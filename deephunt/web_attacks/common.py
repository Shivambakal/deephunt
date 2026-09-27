"""Shared helpers for web_attacks planners/scorers (pure data, no I/O)."""
from __future__ import annotations

from typing import Dict, List, Sequence


def median(values: Sequence[float]) -> float:
    vals = sorted(float(v) for v in values)
    n = len(vals)
    if n == 0:
        return 0.0
    mid = n // 2
    return vals[mid] if n % 2 else (vals[mid - 1] + vals[mid]) / 2.0


def verdict(v: str, confidence: float, signals: List[str],
            evidence_artifacts: Dict[str, bool]) -> Dict:
    assert v in ("vulnerable", "not_vulnerable", "inconclusive")
    return {
        "verdict": v,
        "confidence": round(confidence, 3),
        "signals": signals,
        "evidence_artifacts": evidence_artifacts,
    }


def base_case(case_id: str, module: str, technique_card: str, action: str,
              canary: str, expected_vulnerable: str, expected_safe: str,
              **extra) -> Dict:
    case = {
        "id": case_id,
        "module": module,
        "technique_card": technique_card,
        "action": action,
        "canary": canary,
        "expected_vulnerable": expected_vulnerable,
        "expected_safe": expected_safe,
        "propose_only": True,
    }
    case.update(extra)
    return case


def surface_paths(surface: dict) -> List[str]:
    return list(surface.get("paths") or ["/"])
