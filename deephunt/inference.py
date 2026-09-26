"""DEEPHUNT security inference engine — capability #2.

Instead of hardcoded `if endpoint contains "user": test IDOR`, the engine
asks, for every object/API in the world model:

    Who owns this object?  Who can read it?  Who can modify it?
    Who can transition its state?  What evidence establishes that authority?
    What happens if the authority assumption is wrong?

Each unanswered question becomes a hypothesis seed with a proposed
discriminating experiment. This is how DEEPHUNT finds bugs outside its
explicit vulnerability catalogue.
"""
from world_model import WorldModel


def _mk(statement, reasoning):
    return {"statement": statement, "family": "inference",
            "source": "inquisitor", "reasoning": reasoning,
            "score": 4}


def infer(findings, profile, mem):
    """Generate invariant-question seeds from the world model."""
    wm = WorldModel(profile.get("name", "unknown"))
    wm.ingest(findings)
    seeds = []
    target = profile.get("name", "")

    # 1. open questions in the model itself
    for q in wm.open_questions()[:6]:
        seeds.append(_mk(
            f"[world-model] {q} (target: {target})",
            "Unmapped territory in the system model is where "
            "authorization assumptions hide."))

    # 2. invariant-violation probes: state each invariant, ask for the
    #    cheapest observation that would violate it
    for inv in wm.model["invariants"][:4]:
        seeds.append(_mk(
            f"[invariant] Design a minimum-safe experiment that would "
            f"VIOLATE this invariant on {target}: '{inv['statement']}'. "
            f"If no experiment can violate it, the invariant holds.",
            "Invariant reasoning finds logic flaws payload-spraying misses."))

    # 3. per-object authority questions
    for o in wm.model["objects"][:5]:
        seeds.append(_mk(
            f"[authority] For object '{o['name']}' on {target}: prove the "
            f"reader set and writer set using two owned identities "
            f"(owner vs non-owner). Any overlap beyond policy is a finding.",
            "Authorization is a set-membership question; answer it "
            "empirically with owned accounts."))

    # 4. trust-boundary questions
    if wm.model["services"]:
        hosts = ", ".join(s["host"] for s in wm.model["services"][:4])
        seeds.append(_mk(
            f"[boundary] Map data flow across trust boundaries for: {hosts}. "
            f"Where does user-controlled input cross into a higher-privilege "
            f"context without re-validation?",
            "Trust-boundary crossings are where SSRF/XSS/injection live."))

    return seeds, wm.summary()
