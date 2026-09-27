"""DEEPHUNT causal learning — WHY things worked or failed (blueprint P0 wire-up).

learn.py loads raw memory (rejected/confirmed/lessons). learn_updates.py
closes the loop per pass. THIS module is the causal layer between them:

  what was tried?            -> trials[]
  what happened?             -> outcome per trial
  why did it fail?           -> failure_reason taxonomy
  which evidence was predictive? -> evidence co-occurring with confirmations
  which hypotheses are consistently wrong? -> wrong_patterns[]
  which techniques work on this technology? -> per (technique, tech) rates

Persistence: deephunt/state/<target>_causal.json (also a GLOBAL store at
deephunt/state/_global_causal.json so difficulty.py's historical-success
term improves across targets).

learning.py feeds difficulty.estimate_difficulty() via historical_success()
— the planner literally gets smarter every campaign.
"""
from __future__ import annotations

import json
import os
import time
from typing import Dict, List, Optional

BASE = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.join(BASE, "state")

FAILURE_TAXONOMY = [
    "precondition_unmet",      # control itself failed; test was meaningless
    "oracle_unclear",          # no measurable violation signal
    "wrong_identity_model",    # assumed roles/ownership incorrectly
    "wrong_state_model",       # workflow state assumption wrong
    "hardened_target",         # defense actually present and working
    "insufficient_evidence",   # signal seen but not provable
    "scope_blocked",           # authorization/scope stopped the test
    "flaky_observation",       # non-reproducible signal
    "duplicate",               # same root cause as an existing finding
]


class CausalStore:
    def __init__(self, target: str = "_global"):
        self.target = target
        self.path = os.path.join(STATE_DIR, f"{target}_causal.json")
        self.data = {"trials": [], "tech_rates": {}, "evidence_predictive": {},
                     "wrong_patterns": {}, "updated": None}
        self._load()

    def _load(self):
        if os.path.isfile(self.path):
            try:
                self.data.update(json.load(open(self.path)))
            except (OSError, ValueError):
                pass

    def save(self):
        os.makedirs(STATE_DIR, exist_ok=True)
        self.data["updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        json.dump(self.data, open(self.path, "w"), indent=1)

    # ---------- recording ----------
    def record_trial(self, technique_id: str, technology: str, outcome: str,
                     failure_reason: str = "", evidence_seen: Optional[List[str]] = None,
                     hypothesis: str = "", cost: float = 0.4) -> Dict:
        """outcome: confirmed | rejected | inconclusive."""
        trial = {"ts": time.time(), "technique_id": technique_id,
                 "technology": technology or "unknown", "outcome": outcome,
                 "failure_reason": failure_reason, "hypothesis": hypothesis[:200],
                 "evidence_seen": evidence_seen or [], "cost": cost}
        self.data["trials"].append(trial)
        key = f"{technique_id}||{trial['technology']}"
        rates = self.data["tech_rates"].setdefault(
            key, {"tried": 0, "confirmed": 0, "rejected": 0})
        rates["tried"] += 1
        if outcome == "confirmed":
            rates["confirmed"] += 1
            for ev in trial["evidence_seen"]:
                ep = self.data["evidence_predictive"].setdefault(
                    ev, {"confirmed_with": 0, "seen": 0})
                ep["confirmed_with"] += 1
                ep["seen"] += 1
        elif outcome == "rejected":
            rates["rejected"] += 1
            for ev in trial["evidence_seen"]:
                ep = self.data["evidence_predictive"].setdefault(
                    ev, {"confirmed_with": 0, "seen": 0})
                ep["seen"] += 1
            if hypothesis:
                wp = self.data["wrong_patterns"]
                wp[hypothesis[:120]] = wp.get(hypothesis[:120], 0) + 1
        self.save()
        return trial

    # ---------- queries (feed the planner) ----------
    def historical_success(self, technique_id: str, technology: str = "") -> float:
        """Laplace-smoothed success rate for (technique, technology).
        Falls back to technique-global, then 0.5 (unknown)."""
        tech = technology or "unknown"
        for key in (f"{technique_id}||{tech}",):
            r = self.data["tech_rates"].get(key)
            if r and r["tried"]:
                return round((r["confirmed"] + 1) / (r["tried"] + 2), 3)
        # technique-global fallback
        tried = conf = 0
        for k, r in self.data["tech_rates"].items():
            if k.startswith(technique_id + "||"):
                tried += r["tried"]
                conf += r["confirmed"]
        if tried:
            return round((conf + 1) / (tried + 2), 3)
        return 0.5

    def predictive_evidence(self, top_n: int = 10) -> List[Dict]:
        scored = []
        for ev, d in self.data["evidence_predictive"].items():
            if d["seen"] >= 2:
                precision = d["confirmed_with"] / d["seen"]
                scored.append({"evidence": ev, "precision": round(precision, 3),
                               "seen": d["seen"]})
        scored.sort(key=lambda x: (-x["precision"], -x["seen"]))
        return scored[:top_n]

    def consistently_wrong(self, min_count: int = 2) -> List[Dict]:
        return [{"pattern": p, "times_wrong": n}
                for p, n in sorted(self.data["wrong_patterns"].items(),
                                   key=lambda x: -x[1]) if n >= min_count]

    def failure_breakdown(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for t in self.data["trials"]:
            if t["outcome"] == "rejected" and t.get("failure_reason"):
                out[t["failure_reason"]] = out.get(t["failure_reason"], 0) + 1
        return out

    def summary(self) -> Dict:
        return {"target": self.target, "trials": len(self.data["trials"]),
                "failure_breakdown": self.failure_breakdown(),
                "top_predictive_evidence": self.predictive_evidence(5),
                "consistently_wrong": self.consistently_wrong()[:5]}
