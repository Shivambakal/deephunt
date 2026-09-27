#!/usr/bin/env python3
"""DEEPHUNT ATTACKSURFACE — the unified hunt pipeline.

One target in, a full reasoning-driven hunt out:

  INTAKE -> GLOBAL INTEL + TARGET INTEL -> REASONING -> WORLD MODEL
      -> ATTACK/TRUST GRAPH -> HYPOTHESIS ENGINE -> EXPERIMENT PLANNER
      -> AUTHORIZED TESTING (gated) -> OBSERVATION -> LEARN + UPDATE
      -> loop back (world model; re-intel on suspicious change)

Every stage has typed inputs/outputs and logs to the ResearchSession.
The enforced rails are structural: AUTHORIZED TESTING only proposes tests
through session.propose_test(); execution happens only with --execute AND
profile active_allowed, and every auto-run is recorded as inconclusive
with full evidence — promotion to confirmed/rejected happens in review
(compete_finding + calibration), never by the pipeline alone.

Usage:
  python3 attacksurface.py --target robinhood            # propose-only (safe default)
  python3 attacksurface.py --target robinhood --execute  # also run gated tests
  python3 attacksurface.py --target example.com --passes 1 --max-hypotheses 6
  python3 attacksurface.py --target acme --dossier path/to/dossier.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "intel"))  # deephunt/intel (not the repo-root intel/)
sys.path.insert(0, os.path.dirname(BASE))

from orchestrator import load_profile  # noqa: E402
from brain.session import ResearchSession  # noqa: E402
from world_model import WorldModel  # noqa: E402
import global_intel  # noqa: E402
import target_intel  # noqa: E402
import reasoning  # noqa: E402
import attackgraph  # noqa: E402
import hypothesis_fusion  # noqa: E402
import experiment as exp_planner  # noqa: E402
from ai_attacks import integrate as ai_integrate  # noqa: E402
import learn as learn_mem  # noqa: E402
import learn_updates  # noqa: E402
from eventbus import EventBus  # noqa: E402


def _ts():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def stage_log(session, stage, summary):
    """Every stage writes a typed record to the session."""
    session.observe(f"[pipeline:{stage}] {summary}", kind=f"stage:{stage}")


def _load_dossier(path):
    if path and os.path.isfile(path):
        try:
            return json.load(open(path))
        except (OSError, ValueError):
            pass
    return None


def _company_plan_items(dossier):
    """Ranked technique items from the company attack planner (guarded)."""
    if not dossier:
        return []
    try:
        from company import attack_planner
        plan = attack_planner.plan(dossier)
        return plan if isinstance(plan, list) else []
    except Exception as e:
        return [{"hypothesis": f"attack planner unavailable: {e}",
                 "source": "error", "score": 0}]


# ---------------------------------------------------------------- stages

def stage_intake(target, dossier_path=None):
    profile = load_profile(target)
    ti = target_intel.TargetIntel.from_profile(profile)
    dossier = _load_dossier(dossier_path)
    if dossier:
        ti.merge_dossier(dossier)
    return {"profile": profile, "target_intel": ti, "dossier": dossier}


def stage_global_intel(ti):
    techs = ti.technologies()
    # profile tech_terms are a second tech source
    for t in (ti.intel.get("profile", {}).get("tech_terms") or []):
        ti.add_technology(str(t), evidence="profile tech_terms")
    techs = ti.technologies()
    knowledge = {}
    for t in techs[:12]:  # bounded: 12 techs max per pass
        try:
            knowledge[t] = global_intel.what_is_known(t)
        except Exception:
            knowledge[t] = {"tech": t, "cves": [], "kev": [],
                            "technique_klasses": [], "news": []}
    ti.save()
    return knowledge


def stage_ai_attacks(session, target, ti):
    """AI/LLM attack planning: detect AI surfaces, generate hypothesis seeds.

    Pure planning — seeds flow into stage_hypotheses; every resulting test
    still passes through propose_test() -> TestAuthorization ->
    Engine.execute(). Propose-only by default.
    """
    try:
        surfaces = ai_integrate.detect_ai_surfaces(ti)
        seeds = ai_integrate.seed_hypotheses(target, ti)
    except Exception as e:
        stage_log(session, "ai-attacks", f"planner error: {e}")
        return {"seeds": [], "surfaces": []}
    stage_log(session, "ai-attacks",
              f"{len(surfaces)} AI surface(s), {len(seeds)} hypothesis seeds")
    return {"seeds": seeds, "surfaces": surfaces}


def stage_reasoning(session, target, tech_knowledge, ti, mem):
    out = reasoning.seed_from_intel(target, tech_knowledge, ti, mem)
    for a in out["assumptions"]:
        session.assume(a["believes"], a["enforcement"], a["violated_if"],
                       a.get("confidence", 0.6),
                       provenance=a.get("provenance", "reasoning"))
    stage_log(session, "reasoning",
              f"{len(out['assumptions'])} assumptions, "
              f"{len(out['seed_hypotheses'])} seeds, "
              f"{len(out['open_questions'])} open questions")
    return out


def stage_world_model(target, ti, session):
    wm = WorldModel(target)
    findings = [{"tool": "target_intel", "title": t,
                 "detail": f"technology {t} on {target}"}
                for t in ti.technologies()[:12]]
    for obs in ti.target.data["observations"][-30:]:
        findings.append({"tool": "target_intel", "title": "observation",
                         "detail": obs})
    wm.ingest(findings)
    stage_log(session, "world-model", wm.summary())
    return wm


def stage_attack_graph(session, wm, ti):
    g = attackgraph.build(wm, ti.target)
    stage_log(session, "attack-graph",
              f"{g['node_count']} nodes, {g['edge_count']} edges, "
              f"{len(g['paths'])} attack paths; weakest boundary: "
              f"{g['weakest_boundary']}")
    return g


def stage_hypotheses(session, seeds, plan_items, agraph, mem, max_new):
    fused = hypothesis_fusion.fuse(
        session, seeds["seed_hypotheses"], plan_items,
        agraph["hypothesis_seeds"], mem, max_new=max_new)
    stage_log(session, "hypotheses",
              f"{fused['candidates']} candidates -> "
              f"{len(fused['registered'])} registered "
              f"({len(fused['skipped'])} skipped)")
    return fused


def stage_plan(session, profile, mem, max_tests=5, ai_surfaces=None):
    """Order live hypotheses by EIG; propose the top-N through the gate.

    AI-attack hypotheses (source ai_attacks:*) are expanded into concrete
    test cases by the ai_attacks planners before proposal; every case still
    goes through propose_test()'s adversarial gate.
    """
    live = [h for h in session.state["hypotheses"] if h["status"] == "live"]
    seeds = [{"statement": h["statement"],
              "reasoning": h.get("investigator_test", ""),
              "family": "hypothesis", "score": h.get("score", 3)}
             for h in live]
    planned = exp_planner.plan(seeds, mem)[:max_tests]
    proposed = []
    scope = profile.get("scope_hosts") or []
    auth_basis = profile.get("auth_basis") or f"profile:{profile.get('name')}"
    # AI-attack expansion: turn ai_attacks hypotheses into concrete cases.
    # (fuse() stores seed origin in `provenance`; session hardcodes source.)
    ai_tests = []
    for h in live:
        if str(h.get("provenance", "")).startswith("ai_attacks"):
            surface = (ai_surfaces or [{}])[0]
            try:
                for c in ai_integrate.expand_tests(h, surface):
                    c["_hypothesis_id"] = h["id"]
                    c["_reason"] = h.get("investigator_test", "")[:240]
                    ai_tests.append(c)
            except Exception as e:
                session.observe(f"[pipeline:plan] ai expand failed "
                                f"{h['id']}: {e}", kind="stage:plan")
    ai_tests = ai_tests[:max_tests]
    for c in ai_tests:
        try:
            t = session.propose_test(
                hypothesis_id=c["_hypothesis_id"],
                expected_observation=(
                    f"AI probe {c.get('id')}: vulnerable -> "
                    f"{str(c.get('expected_vulnerable'))[:120]}; safe -> "
                    f"{str(c.get('expected_safe'))[:120]}"),
                reason=c.get("_reason") or "ai_attacks-planned",
                scope_hosts=scope, auth_basis=auth_basis,
                success_criteria=str(c.get("expected_vulnerable") or
                                     "probe-specific vulnerable behavior")[:240],
                failure_criteria=str(c.get("expected_safe") or
                                     "probe-specific safe behavior")[:240])
            proposed.append(t["id"])
        except Exception as e:
            session.observe(f"[pipeline:plan] gate refused AI test "
                            f"{c.get('id')}: {e}", kind="stage:plan")
    for s in planned:
        h = next((x for x in live if x["statement"] == s["statement"]), None)
        if not h:
            continue
        try:
            t = session.propose_test(
                hypothesis_id=h["id"],
                expected_observation=f"discriminating signal for: {h['statement'][:120]}",
                reason=h.get("investigator_test", "")[:240] or "pipeline-planned",
                scope_hosts=scope, auth_basis=auth_basis,
                success_criteria="observation matches the predicted vulnerable behavior",
                failure_criteria="observation matches the hardened/benign behavior")
            proposed.append(t["id"])
        except Exception as e:
            session.observe(f"[pipeline:plan] gate refused {h['id']}: {e}",
                            kind="stage:plan")
    stage_log(session, "experiment-plan",
              f"{len(planned)} planned, {len(proposed)} proposed through gate")
    return {"planned": planned, "proposed": proposed,
            "scope": scope, "auth_basis": auth_basis}


def stage_authorized_testing(session, plan, profile, execute):
    """Execute ONLY when --execute AND profile active_allowed. Auto-runs are
    ALWAYS recorded inconclusive-with-evidence; promotion happens in review."""
    results = []
    if not (execute and profile.get("active_allowed")):
        stage_log(session, "authorized-testing",
                  "propose-only (no --execute or active not allowed)")
        return results
    for tid in plan["proposed"]:
        try:
            res = session.run_test(tid)
        except Exception as e:
            session.observe(f"[pipeline:testing] {tid} refused/failed: {e}",
                            kind="stage:testing")
            continue
        obs = json.dumps(res)[:1500]
        session.observe(f"[pipeline:testing] {tid} -> {obs}",
                        kind="stage:testing", force_generate=True)
        test = next(t for t in session.state["tests"] if t["id"] == tid)
        rec, _ = session.record_result(
            tid, "inconclusive", observed=obs,
            learned="auto-run: needs human/agent review before promotion; "
                    "see compete_finding + calibration")
        results.append(rec["id"])
        _ = test
    stage_log(session, "authorized-testing",
              f"{len(results)} auto-runs recorded (inconclusive pending review)")
    return results


def stage_observation(session, wm, ti, bus):
    """Fold fresh observations into the world model + target intel + bus."""
    fresh = [o["text"] for o in session.state["observations"][-25:]
             if o.get("kind") == "observation"]
    n = 0
    for text in fresh:
        r = wm.update_from_observation(text, source="pipeline")
        n += r.get("relations", 0)
        ti.add_observation(text[:300])
    wm.save()
    ti.save()
    try:
        from eventbus import Event
        bus.emit(Event(type="OBSERVATION_BATCH", data=f"{len(fresh)} obs",
                       creator="pipeline"))
    except Exception:
        pass
    stage_log(session, "observation",
              f"{len(fresh)} observations -> {n} new relations")
    return {"observations": len(fresh), "relations": n}


def stage_learn(session, wm, target):
    summary = learn_updates.apply(session, wm, target)
    stage_log(session, "learn-update",
              f"processed={summary['processed']} proposals={len(summary['proposals'])} "
              f"negatives={summary['negative_examples']} "
              f"belief_deltas={len(summary['belief_deltas'])}")
    return summary


# ---------------------------------------------------------------- driver

def run_pipeline(target, dossier_path=None, passive_only=True, execute=False,
                 max_passes=2, max_hypotheses=12, max_tests=5,
                 session_id=None) -> dict:
    """Run the full ATTACKSURFACE pipeline for one target."""
    t0 = time.time()
    bus = EventBus()
    session = ResearchSession(objective=f"attacksurface:{target}",
                              session_id=session_id)
    report = {"target": target, "started": _ts(), "stages": {},
              "session_id": session.id}
    mem = learn_mem.load_memory(target)

    # INTAKE
    intake = stage_intake(target, dossier_path)
    profile, ti, dossier = (intake["profile"], intake["target_intel"],
                            intake["dossier"])
    stage_log(session, "intake", ti.summary())
    old_snapshot = ti.snapshot()

    plan_items = _company_plan_items(dossier)

    for p in range(max_passes):
        tag = f"pass{p + 1}"
        # GLOBAL INTEL + TARGET INTEL (parallel branches, merged)
        tech_knowledge = stage_global_intel(ti)
        report["stages"].setdefault(tag, {})["global_intel"] = {
            "techs": list(tech_knowledge.keys())}
        # REASONING
        seeds = stage_reasoning(session, target, tech_knowledge, ti, mem)
        # AI-ATTACK PLANNING (additive; propose-only)
        ai = stage_ai_attacks(session, target, ti)
        seeds["seed_hypotheses"] = list(seeds.get("seed_hypotheses", [])) \
            + ai["seeds"]
        report["stages"].setdefault(tag, {})["ai_attacks"] = {
            "surfaces": len(ai["surfaces"]), "seeds": len(ai["seeds"])}
        # WORLD MODEL
        wm = stage_world_model(target, ti, session)
        # ATTACK/TRUST GRAPH
        agraph = stage_attack_graph(session, wm, ti)
        # HYPOTHESIS ENGINE
        fused = stage_hypotheses(session, seeds, plan_items,
                                 agraph, mem, max_hypotheses)
        # EXPERIMENT PLANNER (+ gate proposals)
        plan = stage_plan(session, profile, mem, max_tests,
                          ai_surfaces=ai["surfaces"])
        # AUTHORIZED TESTING (gated; propose-only unless --execute)
        tested = stage_authorized_testing(session, plan, profile, execute)
        # OBSERVATION
        obs = stage_observation(session, wm, ti, bus)
        # LEARN + UPDATE
        learned = stage_learn(session, wm, target)
        report["stages"][tag] = {
            "seeds": len(seeds["seed_hypotheses"]),
            "hypotheses_registered": len(fused["registered"]),
            "tests_proposed": len(plan["proposed"]),
            "tests_run": len(tested),
            "observations": obs["observations"],
            "learn": learned["processed"],
            "proposals": len(learned["proposals"]),
        }
        # LOOP-BACK: suspicious change? re-intel. Else stop if nothing new.
        diff = ti.diff_since(old_snapshot)
        old_snapshot = ti.snapshot()
        if diff["suspicious"] and p + 1 < max_passes:
            session.observe(f"[pipeline:loop] suspicious change detected: "
                            f"{json.dumps(diff)[:300]} — re-entering at intel",
                            kind="stage:loop")
            continue
        if not fused["registered"] and not learned["processed"]:
            break  # nothing new to think about

    report["finished"] = _ts()
    report["elapsed_s"] = round(time.time() - t0, 1)
    stop, why = session.should_stop()
    report["should_stop"] = stop
    report["stop_reason"] = why
    return report


def main():
    ap = argparse.ArgumentParser(description="DEEPHUNT ATTACKSURFACE pipeline")
    ap.add_argument("--target", required=True,
                    help="target profile name (targets/<name>.yaml)")
    ap.add_argument("--dossier", default=None,
                    help="company dossier JSON to merge into target intel")
    ap.add_argument("--execute", action="store_true",
                    help="also EXECUTE gated tests (needs profile active_allowed; "
                         "default is propose-only)")
    ap.add_argument("--passes", type=int, default=2)
    ap.add_argument("--max-hypotheses", type=int, default=12)
    ap.add_argument("--max-tests", type=int, default=5)
    args = ap.parse_args()

    report = run_pipeline(args.target, dossier_path=args.dossier,
                          passive_only=not args.execute,
                          execute=args.execute,
                          max_passes=args.passes,
                          max_hypotheses=args.max_hypotheses,
                          max_tests=args.max_tests)
    print(json.dumps(report, indent=1)[:6000])
    print(f"\nsession: {report['session_id']}  "
          f"elapsed: {report['elapsed_s']}s")


if __name__ == "__main__":
    main()
