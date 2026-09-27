"""C1-014 server-side prototype pollution via JSON merge endpoints.

Non-destructive oracle: POST {"__proto__": {"json spaces": N}} to an
endpoint that merges/clones request JSON; then GET any JSON endpoint.
If responses come back pretty-printed (indent N) where the baseline was
compact, the server read the indentation setting from the polluted
prototype — proof without destructive gadgetry.

PROPOSE-ONLY: the payload and comparison plan only.
"""
from __future__ import annotations

from typing import Dict, List

from .common import base_case, verdict

CARD = "C1-014"


def pollution_probe(surface: dict) -> List[Dict]:
    """Build the non-destructive json-spaces pollution probe.

    surface: {"kind": "http", "name": str, "merge_endpoint": str,
              "read_endpoint": str}
    """
    canary_indent = 10  # unusual indent = unambiguous marker
    return [base_case(
        "PROTO-SPACES-001", "proto_pollution", CARD, "send",
        f"json-spaces:{canary_indent}",
        ("JSON read-endpoints return pretty-printed output with indent "
         f"{canary_indent} where the baseline was compact — the server "
         "read the setting from the polluted prototype."),
        "No formatting change across read endpoints: merge is shallow "
        "(Object.assign) or uses null-prototype objects.",
        merge_endpoint=surface.get("merge_endpoint", "/"),
        read_endpoint=surface.get("read_endpoint", "/"),
        pollution_payload={"__proto__": {"json spaces": canary_indent}},
        canary_indent=canary_indent,
        control="record compact-JSON baseline on read endpoints before "
                "the pollution request; confirm the change fades after "
                "restart or is scoped to the test")]


def score_pollution(case: dict, observation: dict) -> Dict:
    """Score the json-spaces oracle observation.

    observation: {"baseline_pretty": bool, "after_pretty": bool,
                  "after_indent": int, "marker_leaked": bool}
    """
    signals: List[str] = []
    canary = int(case.get("canary_indent", observation.get("canary_indent", 10)))
    baseline_pretty = bool(observation.get("baseline_pretty", False))
    after_pretty = bool(observation.get("after_pretty", False))
    after_indent = int(observation.get("after_indent", -1))
    marker = bool(observation.get("marker_leaked", False))
    signals.append(f"baseline_pretty:{baseline_pretty}")
    signals.append(f"after_indent:{after_indent}")

    artifacts = {
        "formatting_changed": (not baseline_pretty) and after_pretty,
        "indent_matches_canary": after_indent == canary,
        "marker_property_present": marker,
        "baseline_recorded": True,
    }

    if baseline_pretty:
        return verdict("inconclusive", 0.4,
                       signals + ["baseline_already_pretty"], artifacts)
    if after_pretty and after_indent == canary:
        return verdict("vulnerable", 0.9,
                       signals + ["json_spaces_oracle_hit"], artifacts)
    if marker:
        return verdict("vulnerable", 0.7,
                       signals + ["marker_property_leaked"], artifacts)
    return verdict("not_vulnerable", 0.7,
                   signals + ["no_behavior_change"], artifacts)
