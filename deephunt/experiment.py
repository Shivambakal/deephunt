"""DEEPHUNT experiment designer — capability #3.

The agent never asks "what attack should I try?" It asks:
"What observation would most reduce my uncertainty — at the lowest cost?"

rank(seeds) orders hypothesis seeds by expected information gain per unit
of experiment cost, so the orchestrator always fires the cheapest
discriminating experiment first.
"""

import re

# cost signals in seed text -> experiment cost (1=passive read, 5=heavy active)
_COST_PATTERNS = [
    (re.compile(r"passive|observe|read|map|enumerate|review", re.I), 1),
    (re.compile(r"single request|one request|replay|curl", re.I), 2),
    (re.compile(r"two owned|owned accounts|control vs|variant", re.I), 3),
    (re.compile(r"fuzz|intruder|brute|crawl|katana", re.I), 4),
]

# family -> information value multiplier (how much a result teaches us)
_VALUE = {"inference": 1.6, "logic": 1.4, "auth": 1.5, "api": 1.2,
          "injection": 1.2, "xss": 1.0, "cors": 0.9, "default": 1.0}


def estimate_cost(seed):
    text = seed.get("statement", "") + " " + seed.get("reasoning", "")
    for pat, cost in _COST_PATTERNS:
        if pat.search(text):
            return cost
    return 2


def estimate_value(seed):
    base = seed.get("score", 3)
    fam = seed.get("family", "default")
    return base * _VALUE.get(fam, _VALUE["default"])


def rank(seeds):
    """Sort seeds by information-gain-per-cost, descending. Annotates each
    seed with _cost, _value, _roi for the run log."""
    for s in seeds:
        s["_cost"] = estimate_cost(s)
        s["_value"] = round(estimate_value(s), 2)
        s["_roi"] = round(s["_value"] / s["_cost"], 2)
    return sorted(seeds, key=lambda s: -s["_roi"])
