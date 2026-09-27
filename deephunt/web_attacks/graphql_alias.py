"""W1-021 GraphQL alias-batching rate-limit tester.

Oracle discipline from the card: count REAL side effects, not HTTP
responses. A 200 with partial execution is NOT a full bypass.

PROPOSE-ONLY: builds aliased mutation documents; the pipeline routes
them through propose_test() -> TestAuthorization -> Engine.execute().
DoS policy: small N, canary accounts only.
"""
from __future__ import annotations

from typing import Dict, List

from .common import base_case, verdict

CARD = "W1-021"
ALIAS_COUNTS = (10, 100, 500)


def alias_battery(surface: dict) -> List[Dict]:
    """Build alias-batching test cases.

    surface: {"kind": "graphql", "name": str, "endpoint": str,
              "mutation": str, "mutation_arg": str}
    The mutation should be a benign, reversible side effect on an owned
    account (e.g. updateBio). The planner never invents destructive
    mutations — target specifics come from parameters.
    """
    endpoint = surface.get("endpoint", "/graphql")
    mutation = surface.get("mutation", "updateProfile")
    mutation_arg = surface.get("mutation_arg", "bio")
    canary = "dh_alias"
    cases: List[Dict] = []
    for n in ALIAS_COUNTS:
        doc = "mutation { " + " ".join(
            f'{canary}{i}: {mutation}({mutation_arg}: "{canary}-{i}") {{ ok }}'
            for i in range(n)) + " }"
        cases.append(base_case(
            f"GQL-ALIAS-{n:04d}", "graphql_alias", CARD, "send", canary,
            (f"All {n} operations execute: {n} distinct side effects "
             f"observed from ONE HTTP request — the limiter counts "
             "requests, not operations."),
            ("Batch rejected, truncated at a small alias cap, or the "
             "rate limiter counts operations: side effects < aliases "
             "or a rate-limit rejection arrives."),
            endpoint=endpoint, alias_count=n, graphql_document=doc,
            side_effect_probe=(
                f"Read back {mutation_arg} via query; count distinct "
                f"values matching prefix {canary}- across the batch."),
            control="single unbatched mutation first (rate-limit header "
                    "baseline + side-effect mechanism proof)"))
    return cases


def score_alias(case: dict, observation: dict) -> Dict:
    """Score alias-batch observation.

    observation: {"alias_count": int, "http_requests": int,
                  "side_effects_observed": int, "rate_limited": bool,
                  "control_single_ok": bool}
    """
    n = int(case.get("alias_count", observation.get("alias_count", 0)))
    signals: List[str] = []
    reqs = int(observation.get("http_requests", 1))
    effects = int(observation.get("side_effects_observed", 0))
    rate_limited = bool(observation.get("rate_limited", False))
    control_ok = bool(observation.get("control_single_ok", False))
    signals.append(f"side_effects:{effects}/{n}")
    signals.append(f"http_requests:{reqs}")

    artifacts = {
        "side_effects_counted": effects == n and n > 0,
        "single_request": reqs == 1,
        "control_single_mutation_ok": control_ok,
    }

    if effects == n and reqs == 1 and not rate_limited:
        return verdict("vulnerable", 0.9, signals + ["amplification_full"], artifacts)
    if rate_limited and effects < n:
        return verdict("not_vulnerable", 0.8, signals + ["limiter_counts_operations"], artifacts)
    if not control_ok:
        return verdict("inconclusive", 0.35,
                       signals + ["control_mechanism_unproven"], artifacts)
    # Partial execution: a 200 with fewer side effects is NOT full bypass.
    return verdict("inconclusive" if effects else "not_vulnerable",
                   0.55, signals + ["partial_execution"], artifacts)
