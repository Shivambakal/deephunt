"""DEEPHUNT long-term episodic memory — update #8.

The intel/ markdown pile is write-only knowledge. Episodes are structured,
retrievable experience:

    observation -> technique -> evidence -> result -> lesson

Stored as JSONL per target; retrieved by keyword-overlap ranking (stdlib
only, no embeddings needed at this scale). The council consults episodes
before generating hypotheses, so DEEPHUNT stops rediscovering what it
already learned — including failures.
"""
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.join(BASE, "state")

_WORD = re.compile(r"[a-z0-9]{3,}")


def _tokens(text):
    return set(_WORD.findall(text.lower()))


class EpisodicMemory:
    def __init__(self, target):
        self.target = target
        self.path = os.path.join(STATE_DIR, f"{target}_episodes.jsonl")

    def record(self, observation, technique, evidence, result, lesson):
        """result: confirmed | rejected | inconclusive"""
        ep = {"observation": observation[:300], "technique": technique[:80],
              "evidence": evidence[:300], "result": result,
              "lesson": lesson[:300]}
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(self.path, "a") as f:
            f.write(json.dumps(ep) + "\n")
        return ep

    def _all(self):
        if not os.path.isfile(self.path):
            return []
        eps = []
        for line in open(self.path):
            try:
                eps.append(json.loads(line))
            except ValueError:
                continue
        return eps

    def recall(self, query, limit=5):
        """Rank episodes by token overlap with the query. Returns best first."""
        qtok = _tokens(query)
        if not qtok:
            return []
        scored = []
        for ep in self._all():
            etok = _tokens(ep["observation"] + " " + ep["technique"] + " " + ep["lesson"])
            overlap = len(qtok & etok)
            if overlap:
                # failures are extra valuable — weight them up
                w = 1.3 if ep["result"] == "rejected" else 1.0
                scored.append((overlap * w, ep))
        scored.sort(key=lambda x: -x[0])
        return [ep for _, ep in scored[:limit]]

    def lessons_for(self, technique):
        """Every lesson ever learned about this technique on this target."""
        return [ep["lesson"] for ep in self._all()
                if ep["technique"] == technique and ep["lesson"]]

    def count(self):
        return len(self._all())
