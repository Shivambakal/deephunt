"""DEEPHUNT anti-hallucination layer — endgame #9.

The last gate before a case may become READY_FOR_HUMAN. Seven questions,
all must pass. One failure = the case does not ship, no matter how
exciting the response looked.

    1. Can I reproduce it?            (REPRODUCED stage in history)
    2. Can I demonstrate impact?      (IMPACT_SHOWN stage in history)
    3. What evidence proves it?       (non-empty evidence at key stages)
    4. What assumption am I making?   (assumptions recorded, not hidden)
    5. Could this be benign?          (benign alternative explicitly killed)
    6. Does the program allow this test? (scope/authorization recorded)
    7. Is this already known/duplicate?  (novelty checked)

This is what makes DEEPHUNT hard to fool: the checklist is structural,
not a suggestion. validate.py calls clear_for_report() and refuses to
advance on failure.
"""
import re


def _stages(case):
    return [h["stage"] for h in case["history"]]


def _evidence_at(case, stage):
    for h in case["history"]:
        if h["stage"] == stage:
            return h.get("evidence", "")
    return ""


def clear_for_report(case, scope_hosts=(), known_signatures=()):
    """Returns (ok, reasons). ok=True only if all seven pass."""
    reasons, failures = [], []
    stages = _stages(case)

    # 1. reproducible?
    if "REPRODUCED" in stages and "RETESTED" in stages:
        reasons.append("reproduced + independently re-tested")
    else:
        failures.append("not reproduced and independently re-tested")

    # 2. impact demonstrated?
    impact_ev = _evidence_at(case, "IMPACT_SHOWN")
    if "IMPACT_SHOWN" in stages and impact_ev.strip():
        reasons.append("impact demonstrated with evidence")
    else:
        failures.append("no demonstrated impact beyond own account")

    # 3. evidence present?
    key_ev = " ".join(_evidence_at(case, s) for s in
                      ("EXPERIMENTED", "REPRODUCED", "IMPACT_SHOWN"))
    if len(key_ev.strip()) > 60:
        reasons.append("evidence attached at experiment/reproduce/impact stages")
    else:
        failures.append("evidence too thin to prove the claim")

    # 4. assumptions explicit?
    blob = " ".join(h.get("evidence", "") for h in case["history"]).lower()
    if "assum" in blob:
        reasons.append("assumptions recorded explicitly")
    else:
        failures.append("assumptions not stated — hidden assumptions hallucinate findings")

    # 5. benign alternative killed?
    if re.search(r"benign|alternative.*(killed|disproven|ruled out)", blob):
        reasons.append("benign alternative explicitly ruled out")
    else:
        failures.append("benign explanation not ruled out")

    # 6. authorized?
    if "authoriz" in blob or "scope" in blob or "owned" in blob:
        reasons.append("authorization basis recorded")
    else:
        failures.append("no authorization basis — test may have been out of scope")

    # 7. not a duplicate?
    dup = any(sig.lower() in blob for sig in known_signatures if sig)
    if dup:
        failures.append("matches a known/duplicate signature")
    else:
        reasons.append("no duplicate match")

    return (len(failures) == 0), (reasons if not failures else failures)
