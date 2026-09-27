#!/usr/bin/env python3
"""DEEPHUNT Company Hunter orchestrator.

    python3 orchestrator.py --company "Gruve" --domain gruve.ai --mode dossier
    python3 orchestrator.py --company "Example" --domain example.com --mode plan
    python3 orchestrator.py --company X --domain x.com --mode hunt \\
        --authorize-active --scope-hosts x.com,api.x.com --auth-basis "HackerOne ..."

Modes:
  dossier — passive workers -> dossier.md + dossier.json (default, always safe)
  plan    — dossier + ranked attack plan (attack_plan.json)
  hunt    — plan + ResearchSession: hypotheses registered and tests PROPOSED
            through the enforced gate (propose_test). Proposing authorizes;
            nothing is EXECUTED here. Requires --authorize-active and an
            explicit scope + auth basis from the user.

The main hunt daemon (deephunt.py) is untouched by this module.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
HA_ROOT = os.path.dirname(BASE)
sys.path.insert(0, HA_ROOT)

from company import attack_planner, dossier as dossier_mod, snapshot  # noqa: E402
from company.workers import breach_history, domains, employees, news, techstack  # noqa: E402

WORKERS = {
    "domains": lambda c, d: domains.run(d),
    "techstack": lambda c, d: techstack.run(d),
    "employees": lambda c, d: employees.run(c, d),
    "breach_history": lambda c, d: breach_history.run(c, d),
    "news": lambda c, d: news.run(c),
}


def run_workers(company: str, domain: str) -> dict:
    """Fan out to specialists in parallel. Failures are captured per worker."""
    out: dict = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
        futs = {ex.submit(fn, company, domain): name
                for name, fn in WORKERS.items()}
        for fut in concurrent.futures.as_completed(futs):
            name = futs[fut]
            try:
                out[name] = fut.result()
            except Exception as e:  # noqa: BLE001 - one worker never kills the run
                out[name] = {"worker": name, "data": {},
                             "errors": [f"worker crashed: {e}"[:200]],
                             "partial": True}
    return out


def build(company: str, domain: str, mode: str = "dossier",
          top_n: int = 15) -> dict:
    slug = snapshot.slugify(domain or company)
    sdir = snapshot.state_dir(slug)

    workers = run_workers(company, domain)
    dsr = {"workers": workers, "company": company, "domain": domain}

    # adaptive loop: snapshot + diff BEFORE planning, so the plan can re-rank
    snap = snapshot.extract_snapshot(dsr)
    snap_path = snapshot.save_snapshot(slug, dsr)
    changes = snapshot.diff_snapshots(slug, snap)
    followups = snapshot.followups_for_changes(changes)

    plan = attack_planner.build_plan(dsr, top_n=top_n)
    if changes.get("suspicious"):
        plan = attack_planner.rerank(plan, changes)
        followups.append("attack plan re-ranked against changed surface")

    active_handoff = ("passive mode — no active testing authorized. "
                      "Re-run with --mode hunt --authorize-active once a "
                      "bug-bounty scope is confirmed.")
    full = dossier_mod.assemble(company, domain, workers, plan, changes,
                                followups, active_handoff)

    with open(os.path.join(sdir, "dossier.json"), "w") as f:
        json.dump(full, f, indent=1)
    with open(os.path.join(sdir, "dossier.md"), "w") as f:
        f.write(dossier_mod.render_markdown(full))
    with open(os.path.join(sdir, "attack_plan.json"), "w") as f:
        json.dump(plan, f, indent=1)
    full["_paths"] = {"dir": sdir, "snapshot": snap_path}
    return full


def hunt_mode(full: dict, scope_hosts: list[str], auth_basis: str,
              max_tests: int = 5) -> dict:
    """Feed the plan into the enforced ResearchSession loop.

    Creates hypotheses from the top plan items and PROPOSES tests through
    propose_test (adversarial gate + TestAuthorization). Proposing does not
    transmit anything — execution stays with the operator/daemon via run_test.
    """
    from brain.session import ResearchSession
    session = ResearchSession(
        objective=f"Company hunter active phase: {full['company']} "
                  f"({full['domain']}) — authorized scope only")
    proposed = []
    for item in full["attack_plan"][:max_tests]:
        h = session.add_hypothesis(
            statement=item["hypothesis"],
            violated_assumption=f"assumes {item['klass']} controls hold",
            attacker_view=f"card {item['card_id']}: {item['name']}",
            defender_view="assume hardened until a controlled test proves otherwise",
            investigator_test=item["test_sketch"],
            killed_by="control == variant on owned accounts/data",
            impact=4, novelty=3, testability=4)
        try:
            t = session.propose_test(
                hypothesis_id=h["id"],
                expected_observation="variant differs from control in a "
                                     "security-relevant way",
                reason=f"company-hunter plan rank (score {item['score']})",
                scope_hosts=scope_hosts,
                auth_basis=auth_basis,
                success_criteria="unauthorized disclosure/action across the "
                                 "trust boundary, reproduced",
                failure_criteria="control == variant, or demonstrable "
                                 "neutralization",
                single_variable=True)
            proposed.append({"hypothesis": h["id"], "test": t["id"],
                             "authorized": bool(t.get("authorization"))})
        except Exception as e:  # noqa: BLE001 - gate refusals are recorded
            proposed.append({"hypothesis": h["id"], "test": None,
                             "refused": str(e)[:200]})
    return {"session_id": session.id, "proposed": proposed,
            "note": "tests proposed through the enforced gate; execution via "
                    "run_test/Engine only, with TestAuthorization"}


def main() -> None:
    p = argparse.ArgumentParser(description="DEEPHUNT Company Hunter")
    p.add_argument("--company", required=True)
    p.add_argument("--domain", required=True)
    p.add_argument("--mode", choices=["dossier", "plan", "hunt"],
                   default="dossier")
    p.add_argument("--top-n", type=int, default=15)
    p.add_argument("--authorize-active", action="store_true")
    p.add_argument("--scope-hosts", default="")
    p.add_argument("--auth-basis", default="")
    p.add_argument("--max-tests", type=int, default=5)
    args = p.parse_args()

    if args.mode == "hunt":
        if not (args.authorize_active and args.scope_hosts and args.auth_basis):
            p.error("--mode hunt requires --authorize-active, --scope-hosts "
                    "and --auth-basis (explicit user authorization)")
    full = build(args.company, args.domain, args.mode, args.top_n)
    print(f"dossier: {full['_paths']['dir']}/dossier.md")
    print(f"plan items: {len(full['attack_plan'])}")
    ch = full["changes"]
    print(f"suspicious changes: {ch['suspicious']} "
          f"({len(ch['items'])} change notes)")
    if args.mode == "hunt":
        res = hunt_mode(full, [h.strip() for h in args.scope_hosts.split(",")
                               if h.strip()], args.auth_basis, args.max_tests)
        with open(os.path.join(full["_paths"]["dir"],
                               "hunt_handoff.json"), "w") as f:
            json.dump(res, f, indent=1)
        print(f"ResearchSession {res['session_id']}: "
              f"{len(res['proposed'])} tests proposed "
              f"({sum(1 for x in res['proposed'] if x.get('authorized'))} authorized)")


if __name__ == "__main__":
    main()
