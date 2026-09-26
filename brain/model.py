"""World model: what the application believes is trustworthy.

DISCOVERY LOOP input. The model is updated continuously from observations:
every new observation either confirms an assumption or contradicts it.
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Assumption:
    id: str
    believes: str          # what the system believes is trustworthy
    enforcement: str       # where the system enforces it
    violated_if: str       # observable signature if the assumption is wrong
    confidence: float = 0.8


@dataclass
class WorldModel:
    name: str
    users: list = field(default_factory=lambda: ["anonymous", "user_a", "user_b", "admin"])
    objects: list = field(default_factory=list)
    trust_boundaries: list = field(default_factory=list)
    state_machines: dict = field(default_factory=dict)
    assumptions: list = field(default_factory=list)

    def assume(self, aid, believes, enforcement, violated_if, confidence=0.8):
        self.assumptions.append(Assumption(aid, believes, enforcement, violated_if, confidence))
        return self

    def contradict(self, aid, observation):
        """An observation broke an assumption: lower confidence, keep both alive."""
        for a in self.assumptions:
            if a.id == aid:
                a.confidence = max(0.05, a.confidence - 0.4)
                return a
        return None
