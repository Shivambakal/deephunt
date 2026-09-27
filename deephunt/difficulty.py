"""DEEPHUNT difficulty-aware planner — the UTILITY formula (blueprint P0-7).

    UTILITY = alpha*InfoGain + beta*Impact + gamma*Novelty + delta*HistSuccess
              - lam*Cost - mu*Risk - nu*Redundancy - rho*Difficulty

Difficulty dimensions (each 0..1):
  horizon            actions required (1 request vs 5-step workflow)
  evidence_confidence strength of the premise (observed vs guessed)
  context_load       state that must be remembered
  historical_success have similar experiments worked (from learning.py)
  state_complexity   transitions required
  oracle_clarity     can the violation actually be measured

The experiment planner (experiment.py) calls rank() — this module is the
scoring brain behind it. learning.py feeds historical_success so the
planner gets smarter every campaign.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional

# Default weights. Tunable per campaign via set_weights().
WEIGHTS = {
    "alpha": 1.0,   # expected information gain
    "beta": 1.2,    # security impact potential
    "gamma": 0.6,   # novelty
    "delta": 0.8,   # historical success
    "lam": 0.5,     # cost
    "mu": 0.9,      # risk
    "nu": 0.7,      # redundancy
    "rho": 0.6,     # difficulty
}

_HORIZON_PATTERNS = [
    (re.compile(r"5-step|multi-step|workflow|chain|sequence", re.I), 0.9),
    (re.compile(r"two|pair|control.*variant|compare", re.I), 0.4),
    (re.compile(r"single|one request|replay", re.I), 0.15),
]
_IMPACT = {"critical": 1.0, "high": 0.8, "medium": 0.5, "low": 0.25}


def set_weights(**kw):
    WEIGHTS.update({k: v for k, v in kw.items() if k in WEIGHTS})


def estimate_difficulty(candidate: Dict, lessons=None) -> Dict[str, float]:
    """Estimate the six difficulty dimensions for a candidate experiment."""
    text = (candidate.get("statement", "") + " " +
            candidate.get("reasoning", "") + " " +
            candidate.get("investigator_test", "")).lower()
    dims: Dict[str, float] = {}

    horizon = 0.3
    for pat, val in _HORIZON_PATTERNS:
        if pat.search(text):
            horizon = max(horizon, val)
    dims["horizon"] = horizon

    # evidence confidence: observed relationships >> guessed ones
    if any(k in text for k in ("observed", "confirmed", "measured", "reproduced")):
        dims["evidence_confidence"] = 0.85
    elif any(k in text for k in ("unknown", "maybe", "possibly", "guessed", "hypothesized")):
        dims["evidence_confidence"] = 0.3
    else:
        dims["evidence_confidence"] = 0.55

    # context load: identities/objects/states the test must juggle
    entities = len(re.findall(r"\b(identity|object|token|session|state|role|tenant)\b", text))
    dims["context_load"] = min(1.0, 0.2 + entities * 0.12)

    # historical success from the causal lesson store
    dims["historical_success"] = 0.5
    if lessons is not None:
        try:
            dims["historical_success"] = lessons.historical_success(
                candidate.get("technique_id", ""), candidate.get("technology", ""))
        except Exception:
            pass

    # state complexity: transitions the experiment must drive
    dims["state_complexity"] = 0.8 if "transition" in text or "state" in text and "workflow" in text else (
        0.4 if "state" in text else 0.15)

    # oracle clarity: can the violation be measured deterministically?
    if candidate.get("oracle") or "differential" in text or "control" in text:
        dims["oracle_clarity"] = 0.85
    elif "fuzz" in text:
        dims["oracle_clarity"] = 0.45
    else:
        dims["oracle_clarity"] = 0.6

    # aggregate difficulty: high horizon/complexity hurt; high evidence
    # confidence and oracle clarity help
    dims["aggregate"] = round(
        0.25 * dims["horizon"] + 0.20 * dims["state_complexity"] +
        0.15 * dims["context_load"] + 0.15 * (1 - dims["evidence_confidence"]) +
        0.15 * (1 - dims["oracle_clarity"]) +
        0.10 * (1 - dims["historical_success"]), 3)
    return dims


def _impact_score(candidate: Dict) -> float:
    sev = str(candidate.get("severity", candidate.get("impact", "medium"))).lower()
    for k, v in _IMPACT.items():
        if k in sev:
            return v
    return 0.5


def _novelty(candidate: Dict, memory: Dict) -> float:
    fam = candidate.get("family", candidate.get("klass", ""))
    fam_count = (memory or {}).get("family_counts", {}).get(fam, 0)
    tried = str(candidate.get("statement", ""))[:80] in \
        {str(t)[:80] for t in (memory or {}).get("tried_paths", [])}
    base = 1.0 / (1 + 0.25 * fam_count)
    return base * 0.3 if tried else base


def _redundancy(candidate: Dict, planned: List[Dict]) -> float:
    stmt = candidate.get("statement", "")[:60]
    return 1.0 if any(p.get("statement", "")[:60] == stmt for p in planned) else 0.0


def utility(candidate: Dict, memory: Optional[Dict] = None,
            lessons=None, planned: Optional[List[Dict]] = None,
            info_gain: float = 0.5, cost: float = 0.4,
            risk: float = 0.3) -> Dict:
    """Score one candidate with the full UTILITY formula. Returns the
    candidate annotated with _utility and a _breakdown."""
    dims = estimate_difficulty(candidate, lessons)
    novelty = _novelty(candidate, memory or {})
    hist = dims["historical_success"]
    redun = _redundancy(candidate, planned or [])
    w = WEIGHTS
    u = (w["alpha"] * info_gain + w["beta"] * _impact_score(candidate) +
         w["gamma"] * novelty + w["delta"] * hist -
         w["lam"] * cost - w["mu"] * risk -
         w["nu"] * redun - w["rho"] * dims["aggregate"])
    candidate["_utility"] = round(u, 3)
    candidate["_breakdown"] = {
        "info_gain": round(info_gain, 3), "impact": _impact_score(candidate),
        "novelty": round(novelty, 3), "hist_success": round(hist, 3),
        "cost": round(cost, 3), "risk": round(risk, 3),
        "redundancy": redun, "difficulty": dims["aggregate"],
        "difficulty_dims": dims,
    }
    return candidate


def rank(candidates: List[Dict], memory: Optional[Dict] = None,
         lessons=None, info_gains: Optional[Dict] = None,
         costs: Optional[Dict] = None, risks: Optional[Dict] = None,
         max_risk: float = 0.6) -> List[Dict]:
    """Rank candidates by UTILITY. Drops anything above max_risk."""
    planned: List[Dict] = []
    for c in candidates:
        risk = (risks or {}).get(id(c), c.get("_risk_norm", 0.3))
        if risk > max_risk:
            continue
        cid = id(c)
        utility(c, memory, lessons, planned,
                info_gain=(info_gains or {}).get(cid, 0.5),
                cost=(costs or {}).get(cid, 0.4), risk=risk)
        planned.append(c)
    planned.sort(key=lambda c: -c["_utility"])
    return planned
