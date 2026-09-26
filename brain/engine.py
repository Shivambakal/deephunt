"""The full loop, orchestrated:

OBSERVE -> model assumptions -> GENERATE 10+ hypotheses -> adversarial COMPETITION
-> RANK -> select ONE minimum experiment -> run (via proxy repeater spec)
-> OBSERVE result -> CONTRADICTION check -> LEARN into ledger -> new hypotheses -> REPEAT

Five loops mapped:
  discovery    = WorldModel updates from observations
  hypothesis   = hypotheses.generate
  adversarial  = hypotheses.compete
  experiment   = experiments.select_experiment -> proxy repeater
  learning     = Ledger.record + derive_followups
"""
from __future__ import annotations
from . import hypotheses as H
from . import experiments as X
from .ledger import Ledger


class Engine:
    def __init__(self, model):
        self.model = model
        self.ledger = Ledger()

    def run(self, observation, context=None, verbose=True):
        m = self.model
        ctx = context or {}
        hyps = H.generate(m)
        self._adversarial_kill(hyps, ctx.get("known_facts", []))
        survivors, killed = H.compete(hyps)
        ranked = H.rank(survivors)
        exp = X.select_experiment(ranked, ctx.get("experiment"))
        report = {
            "observation": observation,
            "model": m.name,
            "assumptions": [(a.id, a.believes) for a in m.assumptions],
            "hypotheses_generated": len(hyps),
            "killed_in_competition": [h.id for h in killed],
            "ranked_top5": [(h.id, h.score, h.statement[:80]) for h in ranked[:5]],
            "selected_experiment": {
                "id": exp.id, "goal": exp.goal,
                "variant_a": exp.variant_a, "variant_b": exp.variant_b,
                "expect_if_true": exp.expect_if_true,
                "expect_if_false": exp.expect_if_false,
            } if exp else None,
            "best_hypothesis_full": self._full(ranked[0]) if ranked else None,
        }
        if verbose:
            self._print(report, ranked)
        return report

    @staticmethod
    def _adversarial_kill(hyps, known_facts):
        """The DEVIL gets evidence: any hypothesis whose own kill-condition is
        already established by a known fact dies before ranking."""
        for h in hyps:
            hay = (h.killed_by + " " + h.defender_view).lower()
            for fact in known_facts:
                if fact.lower() in hay:
                    h.defender_view = "CONFIRMED: " + h.defender_view
                    break

    def _full(self, h):
        return {"id": h.id, "score": h.score, "statement": h.statement,
                "attacker": h.attacker_view, "defender": h.defender_view,
                "devil": h.devil_view, "investigator": h.investigator_test,
                "killed_by": h.killed_by}

    def _print(self, r, ranked):
        print(f"=== OBSERVE: {r['observation']}")
        print(f"=== MODEL: {r['model']} | assumptions: {len(r['assumptions'])}")
        for aid, b in r["assumptions"]:
            print(f"    [{aid}] believes: {b}")
        print(f"=== GENERATED {r['hypotheses_generated']} hypotheses | "
              f"killed in competition: {r['killed_in_competition'] or 'none'}")
        print("=== RANKED (top 5):")
        for hid, score, stmt in r["ranked_top5"]:
            print(f"    {hid} score={score}: {stmt}...")
        e = r["selected_experiment"]
        print(f"=== SELECT ONE EXPERIMENT: {e['id']}")
        print(f"    goal: {e['goal']}")
        print(f"    A (control): {e['variant_a']}")
        print(f"    B (one change): {e['variant_b']}")
        print(f"    if TRUE : {e['expect_if_true']}")
        print(f"    if FALSE: {e['expect_if_false']}")
        h = r["best_hypothesis_full"]
        print(f"=== PERSONAS on {h['id']}:")
        print(f"    ATTACKER: {h['attacker']}")
        print(f"    DEFENDER: {h['defender']}")
        print(f"    DEVIL   : {h['devil']}")
        print(f"    INVESTIGATOR: {h['investigator']}")

    def learn(self, hypothesis_id, ranked, result, observation, why_failed=""):
        """Close the loop: record the outcome, derive new hypotheses from failure."""
        h = next((x for x in ranked if x.id == hypothesis_id), None)
        exp = X.discriminate(h) if h else None
        entry = self.ledger.record(h, exp, result, observation, why_failed)
        followups = self.ledger.derive_followups(entry) if result == "rejected" else []
        print(f"=== LEARN: {hypothesis_id} -> {result}")
        print(f"    observation: {observation}")
        if why_failed:
            print(f"    why: {why_failed}")
        for f in followups:
            print(f"=== NEW HYPOTHESIS from {f['from']}: {f['statement']}")
            print(f"    test: {f['investigator_test']}")
        return entry, followups

    def execute(self, exp, scope_hosts=(), authorization=None):
        """Close the experimentation loop: run the experiment through the proxy
        repeater. ENFORCED: refuses unless `authorization` is a valid
        TestAuthorization minted by ResearchSession.propose_test() — the
        hypothesis gate is structural, not advisory. Safety gate: ALWAYS
        dry-runs first, parses the resolved target, and refuses to transmit
        unless the host is in scope_hosts."""
        import subprocess, os
        from urllib.parse import urlparse
        from .gate import TestAuthorization
        if not isinstance(authorization, TestAuthorization) or not authorization.is_valid():
            return {"refused": True,
                    "reason": "no valid hypothesis-gated authorization: produce hypothesis, "
                              "expected observation, reason, scope check, and success/failure "
                              "criteria via ResearchSession.propose_test() first"}
        if not authorization.covers(scope_hosts):
            return {"refused": True,
                    "reason": f"requested hosts {list(scope_hosts)} exceed authorized scope "
                              f"{authorization.scope_hosts}"}
        proxy = os.path.expanduser("~/workspace/hacker-agent/proxy/repeater.py")
        if exp.repeater_spec.get("base_seq") is None:
            return {"error": "no base_seq: experiment is plan-only, capture a logged request first"}

        def run(send):
            args = ["python3", proxy] + exp.to_repeater_args(include_send=send)
            p = subprocess.run(args, capture_output=True, text=True, timeout=60)
            return (p.stdout or "") + (p.stderr or "")

        dry = run(False)
        target = ""
        for line in dry.splitlines():
            if line.startswith(">>> ") and " " in line[4:]:
                target = line[4:].split(" ", 1)[1].strip()
                break
        if not target:
            return {"error": "dry run produced no target", "dry_output": dry[:500]}
        host = urlparse(target).hostname or ""
        if host not in scope_hosts:
            return {"refused": True,
                    "reason": f"host '{host}' not in scope {list(scope_hosts)}; no packet sent"}
        live = run(True)
        return {"refused": False, "target": target, "observation": live[:2000]}

    def on_contradiction(self, expected, observed):
        c = X.contradiction(expected, observed)
        print(f"=== CONTRADICTION: expected '{expected}' but observed '{observed}'")
        for a in c["alternatives"]:
            print(f"    {a['order']}. {a['rung']}: {a['distinguishing_test']}")
        return c
