"""DEEPHUNT evidence-first validation pipeline — endgame #6.

Never: interesting response -> vulnerability.

Instead every candidate walks a staged pipeline and CANNOT skip stages:

    INTERESTING -> HYPOTHESIZED -> EXPERIMENTED -> REPRODUCED ->
    IMPACT_SHOWN -> RETESTED -> READY_FOR_HUMAN

Each transition requires evidence attached. The pipeline ends at
READY_FOR_HUMAN — it never auto-submits. A human validates and submits;
the machine only earns the right to ask.
"""
import time

STAGES = ["INTERESTING", "HYPOTHESIZED", "EXPERIMENTED", "REPRODUCED",
          "IMPACT_SHOWN", "RETESTED", "READY_FOR_HUMAN"]

def _requirements():
    return {
        ("INTERESTING", "HYPOTHESIZED"): "hypothesis statement + violated assumption",
        ("HYPOTHESIZED", "EXPERIMENTED"): "controlled experiment spec (control, variant, single variable)",
        ("EXPERIMENTED", "REPRODUCED"): "observation where variant differs from control",
        ("REPRODUCED", "IMPACT_SHOWN"): "demonstrated impact: data/capability beyond own account",
        ("IMPACT_SHOWN", "RETESTED"): "independent re-test (fresh session, second identity) reproducing it",
        ("RETESTED", "READY_FOR_HUMAN"): "anti-hallucination checklist passed",
    }


class ValidationPipeline:
    def __init__(self):
        self.cases = {}

    def open(self, case_id, interesting_response):
        if case_id in self.cases:
            raise ValueError(f"case {case_id} already open")
        self.cases[case_id] = {"stage": "INTERESTING", "history": [
            {"stage": "INTERESTING", "evidence": interesting_response[:300],
             "ts": time.time()}]}
        return "INTERESTING"

    def stage_of(self, case_id):
        return self.cases[case_id]["stage"]

    def advance(self, case_id, evidence):
        """Move exactly one stage forward. Evidence is mandatory and
        checked for emptiness. Skipping stages raises."""
        case = self.cases[case_id]
        cur = case["stage"]
        if cur == "READY_FOR_HUMAN":
            raise ValueError("pipeline complete — human owns it from here")
        nxt = STAGES[STAGES.index(cur) + 1]
        need = _requirements()[(cur, nxt)]
        if not (evidence or "").strip():
            raise ValueError(f"cannot advance {cur}->{nxt}: missing evidence "
                             f"({need})")
        if nxt == "READY_FOR_HUMAN":
            from report_gate import clear_for_report
            ok, reasons = clear_for_report(case)
            if not ok:
                raise ValueError("report gate failed: " + "; ".join(reasons))
        case["stage"] = nxt
        case["history"].append({"stage": nxt, "evidence": evidence[:500],
                                "ts": time.time(), "required": need})
        return nxt

    def kill(self, case_id, reason):
        """A failed stage kills the case — recorded, never silently dropped."""
        self.cases[case_id]["stage"] = "KILLED"
        self.cases[case_id]["history"].append(
            {"stage": "KILLED", "evidence": reason[:300], "ts": time.time()})
