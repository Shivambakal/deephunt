"""LEARNING LOOP: failure is new information, never just 'move on'.

Every tested hypothesis is recorded with WHY it failed. The ledger derives
follow-up hypotheses from the failure mechanism itself:

  weak agent : IDOR test failed -> move on
  this ledger: IDOR failed -> ownership is validated -> WHERE is it validated?
               -> GET validates it -> PATCH behavior unknown -> new hypothesis
"""
from __future__ import annotations
import json, os, time

LEDGER_PATH = os.path.expanduser("~/workspace/hacker-agent/data/brain/ledger.jsonl")


class Ledger:
    def __init__(self, path=LEDGER_PATH):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)

    def record(self, hypothesis, experiment, result, observation, why_failed=""):
        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "hypothesis_id": hypothesis.id,
            "statement": hypothesis.statement,
            "experiment_id": experiment.id if experiment else None,
            "result": result,                    # confirmed | rejected | inconclusive
            "observation": observation,
            "why_failed": why_failed,
        }
        with open(self.path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        return entry

    def history(self):
        if not os.path.exists(self.path):
            return []
        return [json.loads(l) for l in open(self.path) if l.strip()]

    def derive_followups(self, entry):
        """Turn a rejection into new hypotheses aimed at the enforcement gap."""
        why = (entry.get("why_failed") or "").lower()
        obs = (entry.get("observation") or "").lower()
        text = why + " " + obs
        followups = []

        def add(stmt, test):
            followups.append({"from": entry["hypothesis_id"], "statement": stmt,
                              "investigator_test": test})

        if any(w in text for w in ["get validat", "ownership", "owner check", "authorize"]):
            add("Ownership is enforced on GET but not re-checked on state-changing verbs.",
                "Replay the same object access via PATCH/PUT/DELETE as non-owner; diff against GET.")
            add("Ownership is enforced at the controller but skipped on a nested/member route.",
                "Reach the same object through nested routes (/parent/:id/child) and member actions.")
        if any(w in text for w in ["channel", "verb", "method"]):
            add("The check exists on the primary channel only; an alternate content-type or versioned path skips it.",
                "Replay with different Content-Type, Accept version, and /v1 vs /v2 paths.")
        if any(w in text for w in ["token", "session", "identity"]):
            add("Identity is bound once at login but not re-bound at the sensitive step.",
                "Fixate/swap the token between the check step and the action step.")
        if any(w in text for w in ["time", "window", "race", "stale", "cache"]):
            add("The enforcement reads stale state while the action reads fresh state (or vice versa).",
                "Force the state transition, then act inside the propagation window.")
        if not followups:
            add("The rejection may be channel-specific; the same assumption may fail on a sibling endpoint.",
                "Map sibling endpoints sharing the object and test the cheapest one.")
        return followups
