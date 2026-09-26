"""DEEPHUNT information-gain planner — update #5.

The old ranker scored seeds by static value/cost. This planner asks the
real question: WHICH ACTION, IF TAKEN NOW, WOULD MOST REDUCE UNCERTAINTY?

For each candidate it estimates:
  EIG    = expected information gain = sum over possible outcomes of
           P(outcome) * belief-shift(outcome)
  cost   = experiment cost (1-5)
  risk   = authorization/safety risk (1-5; active > passive, authn > anon)

Plans are ordered by EIG / (cost * risk). The planner never selects an
action whose risk exceeds the session's authorization — that gate stays
structural, not advisory.
"""
import math
import re

_COST_PATTERNS = [
    (re.compile(r"passive|observe|read|map|enumerate|review", re.I), 1),
    (re.compile(r"single request|one request|replay|curl", re.I), 2),
    (re.compile(r"two owned|owned accounts|control vs|variant", re.I), 3),
    (re.compile(r"fuzz|intruder|brute|crawl|katana", re.I), 4),
]
_RISK_PATTERNS = [
    (re.compile(r"passive|observe|read-only", re.I), 1),
    (re.compile(r"single|replay|owned account", re.I), 2),
    (re.compile(r"active|nuclei|ffuf|intruder", re.I), 3),
    (re.compile(r"brute|fuzz|dos|destruct", re.I), 5),
]
_VALUE = {"novel": 1.8, "inference": 1.6, "logic": 1.4, "auth": 1.5,
          "api": 1.2, "injection": 1.2, "xss": 1.0, "cors": 0.9,
          "default": 1.0}


def estimate_cost(seed):
    text = seed.get("statement", "") + " " + seed.get("reasoning", "")
    for pat, cost in _COST_PATTERNS:
        if pat.search(text):
            return cost
    return 2


def estimate_risk(seed):
    text = seed.get("statement", "") + " " + seed.get("reasoning", "")
    for pat, risk in _RISK_PATTERNS:
        if pat.search(text):
            return risk
    return 2


def expected_info_gain(seed, mem):
    """Heuristic EIG: novelty x uncertainty x discriminating power.

    - novelty: unseen shapes teach more (memory rejection count lowers it)
    - uncertainty: seeds near the weakest invariant teach more
    - discriminating power: control-vs-variant designs resolve cleanly
    """
    text = (seed.get("statement", "") + " " + seed.get("reasoning", "")).lower()
    base = seed.get("score", 3) * _VALUE.get(seed.get("family", "default"),
                                            _VALUE["default"])
    rej = mem.get("rejected", 0)
    rej_n = len(rej) if isinstance(rej, list) else rej
    novelty = 1.0
    if rej_n > 20:
        novelty = 0.8  # well-trodden ground teaches less
    uncertainty = 1.2 if any(k in text for k in
                              ("unknown", "unexplained", "weakest", "why")) else 1.0
    discriminating = 1.3 if any(k in text for k in
                                ("control", "vs", "two owned", "compare")) else 1.0
    # entropy-flavored: diminishing returns on the same family
    fam_count = mem.get("family_counts", {}).get(seed.get("family"), 0)
    diversity = 1.0 / (1 + 0.15 * fam_count)
    eig = base * novelty * uncertainty * discriminating * diversity
    return round(eig, 2)


def plan(seeds, mem, max_risk=3):
    """Order candidates by EIG/(cost*risk). Drops anything above max_risk.
    Annotates each seed with _eig, _cost, _risk, _roi."""
    planned = []
    for s in seeds:
        risk = estimate_risk(s)
        if risk > max_risk:
            continue
        cost = estimate_cost(s)
        eig = expected_info_gain(s, mem)
        s["_eig"], s["_cost"], s["_risk"] = eig, cost, risk
        s["_roi"] = round(eig / (cost * risk), 3)
        planned.append(s)
    planned.sort(key=lambda s: -s["_roi"])
    return planned


# backward-compatible alias for the old rank() callers
def rank(seeds):
    return plan(seeds, {"rejected": 0, "family_counts": {}})
