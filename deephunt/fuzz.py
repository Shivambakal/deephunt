"""DEEPHUNT feedback-guided semantic fuzzing (blueprint P0-P1 #9, report §8-9).

Architecture (the report's key insistence):

    LLM -> semantic mutation proposal
           v
    DETERMINISTIC fuzzer -> execution -> instrumentation -> feedback -> oracle

The LLM never fuzzes directly. It proposes *semantic* mutations
("try a state transition here", "this parameter looks like an object id —
swap identities"). The deterministic engine generates, executes,
measures, minimizes, and reproduces.

Feedback signals: response novelty, state novelty, oracle activation,
differential behavior, chain novelty.

Execution goes through an `executor` callable — in production this is the
session-gated Engine path; in tests it is a mock. The fuzzer itself never
touches the network.
"""
from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

# ---------- semantic mutation operators (deterministic) ----------

def _mut_swap_identity(case: Dict, pool) -> Dict:
    c = dict(case)
    c["identity"] = "variant" if case.get("identity") == "control" else "control"
    c["mutation"] = "swap_identity"
    return c

def _mut_param_inject(case: Dict, pool) -> Dict:
    c = dict(case)
    params = dict(c.get("params", {}))
    for k in list(params):
        if k.endswith("_id") and pool is not None:
            other = pool.get_for(k)
            if other and str(other) != str(params[k]):
                params[k] = other
                break
    else:
        # no pool value: boundary-value injection on first param
        for k in list(params)[:1]:
            params[k] = "0"
    c["params"] = params
    c["mutation"] = "param_inject"
    return c

def _mut_state_skip(case: Dict, pool) -> Dict:
    c = dict(case)
    c["skip_state_validation"] = True
    c["mutation"] = "state_skip"
    return c

def _mut_method_override(case: Dict, pool) -> Dict:
    c = dict(case)
    c["method"] = {"GET": "POST", "POST": "PUT"}.get(case.get("method", "GET"), "GET")
    c["mutation"] = "method_override"
    return c

def _mut_type_confusion(case: Dict, pool) -> Dict:
    c = dict(case)
    params = dict(c.get("params", {}))
    for k, v in list(params.items())[:1]:
        params[k] = ["__array__", v] if not isinstance(v, list) else v[0]
    c["params"] = params
    c["mutation"] = "type_confusion"
    return c

MUTATORS = [_mut_swap_identity, _mut_param_inject, _mut_state_skip,
            _mut_method_override, _mut_type_confusion]


def llm_propose_mutations(context: Dict, llm_fn: Optional[Callable] = None) -> List[str]:
    """LLM hook: propose semantic mutation *names*. The deterministic
    engine still decides what actually runs. Without an LLM, built-in
    heuristics propose from context."""
    if llm_fn is not None:
        try:
            out = llm_fn(context)
            if isinstance(out, list):
                return [str(x) for x in out]
        except Exception:
            pass
    # deterministic fallback: propose from context signals
    proposals = []
    if context.get("has_object_id"):
        proposals += ["swap_identity", "param_inject"]
    if context.get("has_workflow"):
        proposals += ["state_skip"]
    if context.get("has_method_semantics"):
        proposals += ["method_override", "type_confusion"]
    return proposals or ["param_inject"]


# ---------- feedback ----------

def _fingerprint(text: str) -> str:
    norm = "".join(sorted(set((text or "").lower().split())))
    return hashlib.sha256(norm.encode()).hexdigest()[:16]


@dataclass
class Feedback:
    response_novelty: float = 0.0
    state_novelty: float = 0.0
    oracle_activation: float = 0.0
    differential_behavior: float = 0.0
    chain_novelty: float = 0.0

    def score(self) -> float:
        return round(0.3 * self.response_novelty + 0.25 * self.state_novelty +
                     0.25 * self.oracle_activation + 0.1 * self.differential_behavior +
                     0.1 * self.chain_novelty, 3)


class FeedbackTracker:
    def __init__(self):
        self.seen_responses = set()
        self.seen_states = set()
        self.seen_chains = set()

    def evaluate(self, case: Dict, observation: Dict,
                 oracle_verdict: str = "") -> Feedback:
        fb = Feedback()
        fp = _fingerprint(observation.get("body", ""))
        if fp not in self.seen_responses:
            fb.response_novelty = 1.0
            self.seen_responses.add(fp)
        st = observation.get("state_after", "")
        if st and st not in self.seen_states:
            fb.state_novelty = 1.0
            self.seen_states.add(st)
        if oracle_verdict == "VIOLATED":
            fb.oracle_activation = 1.0
        elif oracle_verdict == "INCONCLUSIVE":
            fb.oracle_activation = 0.4
        if observation.get("differs_from_control"):
            fb.differential_behavior = 1.0
        chain = (case.get("mutation", ""), observation.get("state_after", ""))
        if chain not in self.seen_chains:
            fb.chain_novelty = 0.5
            self.seen_chains.add(chain)
        return fb


# ---------- campaign ----------

@dataclass
class FuzzResult:
    interesting: List[Dict] = field(default_factory=list)
    total: int = 0
    feedback_log: List[Dict] = field(default_factory=list)


def run_campaign(seed_cases: List[Dict], executor: Callable,
                 pool=None, budget: int = 50, seed: int = 7,
                 oracle_fn: Optional[Callable] = None,
                 llm_fn: Optional[Callable] = None) -> FuzzResult:
    """Deterministic fuzzing campaign. executor(case) -> observation dict.
    Seeded RNG => reproducible."""
    rng = random.Random(seed)
    tracker = FeedbackTracker()
    result = FuzzResult()
    queue = [dict(c) for c in seed_cases]
    tried = set()

    while queue and result.total < budget:
        case = queue.pop(0)
        key = json.dumps(case, sort_keys=True, default=str)
        if key in tried:
            continue
        tried.add(key)
        result.total += 1

        obs = executor(case) or {}
        oracle_v = ""
        if oracle_fn:
            try:
                oracle_v = oracle_fn(case, obs)
            except Exception:
                oracle_v = ""
        fb = tracker.evaluate(case, obs, oracle_v)
        result.feedback_log.append(
            {"case": case.get("mutation", "seed"), "feedback": fb.score()})

        if fb.score() >= 0.5 or oracle_v == "VIOLATED":
            result.interesting.append(
                {"case": case, "observation": obs,
                 "feedback": fb.score(), "oracle": oracle_v})
            # energy: mutate interesting cases further (feedback-guided)
            mut_names = llm_propose_mutations(
                {"has_object_id": True, "has_workflow": bool(obs.get("state_after"))},
                llm_fn)
            name_to_fn = {f.__name__.replace("_mut_", ""): f for f in MUTATORS}
            for name in mut_names[:2]:
                fn = name_to_fn.get(name)
                if fn:
                    child = fn(case, pool)
                    child["parent"] = case.get("mutation", "seed")
                    queue.append(child)
        # baseline diversity: a couple of blind mutations per seed
        if result.total < budget and rng.random() < 0.3:
            queue.append(rng.choice(MUTATORS)(case, pool))

    return result


def minimize(case: Dict, executor: Callable,
             oracle_fn: Callable) -> Dict:
    """Delta-debugging-lite: try dropping each param; keep the minimal
    case that still triggers the oracle."""
    params = dict(case.get("params", {}))
    best = dict(case)
    for k in list(params):
        trial = dict(best)
        tp = dict(trial.get("params", {}))
        tp.pop(k, None)
        trial["params"] = tp
        try:
            if oracle_fn(trial, executor(trial)) == "VIOLATED":
                best = trial
        except Exception:
            pass
    best["minimized_from"] = len(params)
    best["minimized_to"] = len(best.get("params", {}))
    return best
