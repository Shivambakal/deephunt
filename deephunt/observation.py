"""DEEPHUNT structured experiment observations.

Every experiment produces an ExperimentObservation — not a log line, but a
structured record the reasoning engine can query:

    experiment_id, hypothesis, preconditions{identity, object_owner, ...},
    action{type, target}, observation{status_changed, response_changed,
    object_changed}, interpretation, confidence, next_question

Appended to state/<target>/observations.jsonl. world_model.update_from_observation
accepts these dict records as well as free text.
"""
from __future__ import annotations
import json
import os
import time
import uuid

BASE = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.join(BASE, "state")


class ExperimentObservation:
    def __init__(self, hypothesis, preconditions=None, action=None,
                 observation=None, interpretation="", confidence=0.5,
                 next_question="", experiment_id=None):
        self.experiment_id = experiment_id or f"EXP-{uuid.uuid4().hex[:6].upper()}"
        self.hypothesis = hypothesis
        self.preconditions = dict(preconditions or {})
        self.action = dict(action or {})
        self.observation = dict(observation or {})
        self.interpretation = interpretation
        self.confidence = float(confidence)
        self.next_question = next_question
        self.ts = time.time()

    def to_dict(self):
        return {
            "experiment_id": self.experiment_id,
            "hypothesis": self.hypothesis,
            "preconditions": self.preconditions,
            "action": self.action,
            "observation": self.observation,
            "interpretation": self.interpretation,
            "confidence": self.confidence,
            "next_question": self.next_question,
            "ts": self.ts,
        }

    @classmethod
    def from_dict(cls, d):
        o = cls(hypothesis=d.get("hypothesis", ""),
                preconditions=d.get("preconditions"),
                action=d.get("action"),
                observation=d.get("observation"),
                interpretation=d.get("interpretation", ""),
                confidence=d.get("confidence", 0.5),
                next_question=d.get("next_question", ""),
                experiment_id=d.get("experiment_id"))
        o.ts = d.get("ts", o.ts)
        return o

    def __repr__(self):
        return (f"<ExperimentObservation {self.experiment_id} "
                f"conf={self.confidence:.2f} {self.interpretation[:60]}>")


def append_observation(target, obs):
    """Append one observation to state/<target>/observations.jsonl."""
    if isinstance(obs, ExperimentObservation):
        rec = obs.to_dict()
    else:
        rec = dict(obs)
    path = os.path.join(STATE_DIR, target, "observations.jsonl")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(rec) + "\n")
    return rec.get("experiment_id")


def read_observations(target, limit=200):
    """Read back structured observations (most recent last)."""
    path = os.path.join(STATE_DIR, target, "observations.jsonl")
    if not os.path.isfile(path):
        return []
    recs = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                recs.append(json.loads(line))
            except ValueError:
                continue
    return recs[-limit:]
