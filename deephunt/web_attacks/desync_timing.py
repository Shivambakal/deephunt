"""C1-016 CL.TE / TE.CL desync detection via timing differential.

The anti-false-positive discipline is baked in: >=3 repeats per probe,
clean controls on the same connection class, keep-alive/pipelining
disabled during validation, and a probe is only a finding when the
delay reproduces and the control stays fast.

PROPOSE-ONLY: probe shapes only; execution flows through the
authorized pipeline.
"""
from __future__ import annotations

from typing import Dict, List

from .common import base_case, median, surface_paths, verdict

CARD = "C1-016"
REPEATS = 3
DELAY_THRESHOLD_S = 2.0


def timing_probes(surface: dict) -> List[Dict]:
    """Build CL.TE / TE.CL timing probes plus controls.

    surface: {"kind": "http", "name": str, "host": str, "paths": [str]}
    """
    host = surface.get("host", "target")
    path = surface_paths(surface)[0]
    canary = "dh_timing"
    mk = lambda cid, desc, vuln, safe, shape: base_case(  # noqa: E731
        cid, "desync_timing", CARD, "send_raw", canary, vuln, safe,
        path=path, host=host, repeats=REPEATS,
        delay_threshold_s=DELAY_THRESHOLD_S,
        request_shape=shape, description=desc,
        connection_rules=("single connection per probe; disable "
                          "pipelining and keep-alive reuse during "
                          "validation"))
    return [
        mk("TIMING-CLTE-001",
           "CL.TE: FE honors Content-Length(4), BE honors chunked encoding "
           "— BE waits for chunk data that never arrives.",
           "Consistent multi-second delay on all 3+ runs; control fast.",
           "No repeatable delta; stack rejects ambiguous framing (400).",
           "POST with Content-Length: 4 + Transfer-Encoding: chunked, "
           "body '1\\r\\nA\\r\\n0\\r\\n\\r\\n'"),
        mk("TIMING-TECL-001",
           "TE.CL: FE honors chunked encoding, BE waits for "
           "Content-Length(6) bytes.",
           "Consistent multi-second delay on all 3+ runs; control fast.",
           "No repeatable delta across runs.",
           "POST with Content-Length: 6 + Transfer-Encoding: chunked, "
           "body '0\\r\\n\\r\\nX'"),
        mk("TIMING-CONTROL-001",
           "Clean control: same POST with unambiguous framing.",
           "Control is fast — establishes the noise floor.",
           "Control also slow — environment too noisy; result is "
           "inconclusive, not a finding.",
           "POST with Content-Length only, well-formed body"),
    ]


def score_timing(case: dict, observation: dict) -> Dict:
    """Score timing-differential observations.

    observation: {"probe_delays": [...], "control_delays": [...],
                  "repeats": int, "delay_threshold_s": float}
    """
    signals: List[str] = []
    probes = [float(v) for v in observation.get("probe_delays") or []]
    controls = [float(v) for v in observation.get("control_delays") or []]
    repeats = int(observation.get("repeats", len(probes)))
    threshold = float(observation.get("delay_threshold_s",
                                      case.get("delay_threshold_s",
                                               DELAY_THRESHOLD_S)))
    is_control = case.get("id", "").endswith("CONTROL-001")

    if repeats < REPEATS or len(probes) < REPEATS:
        return verdict("inconclusive", 0.3,
                       signals + ["insufficient_repeats"], {
                           "delay_reproduced": False,
                           "control_clean": False,
                           "repeats_met": False,
                       })
    probe_med = median(probes)
    control_med = median(controls) if controls else 0.0
    slow_runs = sum(1 for v in probes if v >= threshold)
    signals.append(f"probe_median_s:{probe_med:.2f}")
    signals.append(f"control_median_s:{control_med:.2f}")
    signals.append(f"slow_runs:{slow_runs}/{len(probes)}")
    control_clean = control_med < threshold / 2.0

    artifacts = {
        "delay_reproduced": slow_runs == len(probes) and len(probes) > 0,
        "control_clean": control_clean,
        "repeats_met": True,
    }

    if is_control:
        # Scoring the control case itself: fast = healthy baseline.
        if control_clean:
            return verdict("not_vulnerable", 0.8,
                           signals + ["control_fast"], artifacts)
        return verdict("inconclusive", 0.4,
                       signals + ["control_noisy"], artifacts)

    if slow_runs == len(probes) and control_clean:
        return verdict("vulnerable", 0.82,
                       signals + ["differential_repeated"], artifacts)
    if not control_clean:
        return verdict("inconclusive", 0.4,
                       signals + ["controls_also_slow"], artifacts)
    return verdict("not_vulnerable", 0.7,
                   signals + ["no_repeatable_delta"], artifacts)
