"""W1-031 single-packet HTTP/2 race tester (last-byte synchronization).

Oracle discipline from the card: SERVER-SIDE STATE DIFF, never response
codes. N x 200 responses without a state diff is NOT a finding.

PROPOSE-ONLY: builds the release schedule and state-check plan; the
pipeline authorizes execution through propose_test() -> TestAuthorization
-> Engine.execute().
"""
from __future__ import annotations

from typing import Dict, List

from .common import base_case, verdict

CARD = "W1-031"


def race_plan(surface: dict) -> List[Dict]:
    """Build single-packet race test plans.

    surface: {"kind": "http2", "name": str, "endpoint": str,
              "requests": int, "state_read": str, "state_unit": str}
    state_read describes how to read business state (e.g. "GET
    /api/balance"); state_unit is what one operation should change
    (e.g. "coupon redemptions"). All target-specific.
    """
    endpoint = surface.get("endpoint", "/")
    n = int(surface.get("requests", 20))
    canary = "dh_race"
    return [base_case(
        "H2-RACE-001", "http2_race", CARD, "send_burst", canary,
        (f"Server-side state advances {n} times: state_after - state_before "
         f"== {n} for an operation that must be single-use."),
        "State advances exactly once regardless of concurrency "
        "(idempotency enforced); repeated run confirms.",
        endpoint=endpoint, request_count=n,
        release_schedule=("Withhold the final byte of all N requests on "
                          "one HTTP/2 connection; release simultaneously."),
        state_check={
            "before": surface.get("state_read", "read business state"),
            "after": surface.get("state_read", "read business state"),
            "unit": surface.get("state_unit", "operation count"),
        },
        repeat_runs=2,
        control="single unraced request establishes the expected "
                "single-use state transition")]


def score_race(case: dict, observation: dict) -> Dict:
    """Score single-packet race observation.

    observation: {"requests_sent": int, "state_before": float,
                  "state_after": float, "responses_2xx": int,
                  "runs": int}
    """
    n = int(case.get("request_count", observation.get("requests_sent", 0)))
    signals: List[str] = []
    before = float(observation.get("state_before", 0))
    after = float(observation.get("state_after", 0))
    ok2xx = int(observation.get("responses_2xx", 0))
    runs = int(observation.get("runs", 1))
    delta = after - before
    signals.append(f"state_delta:{delta} requests:{n} http2xx:{ok2xx}")

    artifacts = {
        "server_state_diff": delta >= n and n > 0,
        "repeated_n_times": runs >= 2,
        "not_response_codes": True,  # scorer never uses status codes
    }

    if delta >= n and n > 0:
        conf = 0.85 if runs >= 2 else 0.65
        return verdict("vulnerable", conf,
                       signals + ["n_fold_state_application"], artifacts)
    if delta <= 1.0:
        return verdict("not_vulnerable", 0.75,
                       signals + ["state_advanced_once"], artifacts)
    return verdict("inconclusive", 0.4,
                   signals + ["partial_state_delta"], artifacts)
