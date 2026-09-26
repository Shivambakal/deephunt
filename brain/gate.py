"""Hypothesis-gated tool authorization.

A TestAuthorization is minted ONLY by ResearchSession.propose_test(), after the
hypothesis gate and the adversarial self-check both pass. The execution layer
(Engine.execute) refuses anything that doesn't carry a valid one. This is what
makes the loop enforced rather than documented.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import time


class GateRefused(Exception):
    """Raised when a test is proposed without meeting the gate requirements."""


@dataclass
class TestAuthorization:
    test_id: str
    hypothesis_id: str
    session_id: str
    scope_hosts: list
    issued_at: float = field(default_factory=time.time)
    minted_by: str = "ResearchSession"
    revoked: bool = False
    ttl_seconds: int = 86400

    def is_valid(self) -> bool:
        return (not self.revoked
                and self.minted_by == "ResearchSession"
                and bool(self.test_id and self.hypothesis_id and self.session_id)
                and bool(self.scope_hosts)
                and (time.time() - self.issued_at) < self.ttl_seconds)

    def covers(self, hosts) -> bool:
        return set(hosts or ()) <= set(self.scope_hosts)
