"""DEEPHUNT persistent learning pulse — endgame #7.

"Updates every second" should mean the LEARNING LOOP runs per observation,
not that data piles up. pulse() is the atomic unit:

    observation -> world-model change -> belief update ->
    new hypothesis -> new experiment -> new evidence -> memory

Call it after every meaningful response. It is cheap (no tools fire),
so it can run hot — this is the tight inner loop; the orchestrator's
cycles are the slow outer loop.
"""
from world_model import WorldModel
from episodic import EpisodicMemory
import experiment as planner
import differential


def pulse(target, observation_text, source="response", mem=None):
    """One learning heartbeat. Returns the next best action."""
    mem = mem or {"rejected": [], "family_counts": {}}
    wm = WorldModel(target)

    # 1-2. observation -> model change -> belief update
    delta = wm.update_from_observation(observation_text, source=source)

    # anomaly? -> feed the heretic
    new_hypotheses = []
    if _looks_anomalous(observation_text, wm):
        wm.record_anomaly(f"{source}: {observation_text[:160]}")
        new_hypotheses.append({
            "statement": f"[pulse/anomaly] '{observation_text[:120]}' fits no "
                         f"known pattern — explain or kill it",
            "family": "novel", "source": "pulse", "score": 5})

    # 3-4. weakest belief -> hypothesis -> planned experiment
    inv, conf = wm.weakest_invariant()
    probe = None
    if inv and conf < 0.75:
        probe = {"statement": f"[pulse/probe] weakest belief (conf {conf}): "
                              f"'{inv[:100]}' — design the cheapest test of it",
                 "family": "inference", "source": "pulse", "score": 4}
        new_hypotheses.append(probe)

    planned = planner.plan(new_hypotheses, mem, max_risk=1)  # passive only
    next_action = planned[0] if planned else None

    # differentials the observation invites
    diffs = differential.design("pulse", wm, limit=3)

    wm.save()
    return {
        "model_delta": delta,
        "weakest_belief": (inv, conf),
        "hypotheses": len(new_hypotheses),
        "next_action": (next_action or {}).get("statement"),
        "suggested_differentials": [d["dimension"] for d in diffs],
        "world": wm.summary(),
    }


def _looks_anomalous(text, wm):
    """An observation is anomalous if it matches no known technique signal
    and no bias marker the brain knows."""
    try:
        import train
        signals = []
        for c in train.load_techniques():
            signals += [s.lower() for s in c.get("signals", [])]
        low = text.lower()
        return not any(s in low for s in signals if len(s) > 3)
    except Exception:  # noqa: BLE001
        return False
