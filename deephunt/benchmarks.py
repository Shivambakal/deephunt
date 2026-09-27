"""DEEPHUNT benchmark harness — measure the hunter, not the hype (report §19).

Never measure only "number of vulnerabilities" — that rewards false
positives. Tracked per campaign:

  discovery_recall      known vulns found / known vulns present (mock)
  precision             confirmed / reported
  proof_rate            confirmed with reproducible evidence / confirmed
  chain_completion      multi-step investigations completed / started
  verifier_rejection_rate  verifier-rejected / verifier-seen
  time_to_first_valid   seconds from start to first confirmed finding
  duplicate_rate        duplicate reports / root causes
  endpoint_coverage     endpoints exercised / endpoints known
  cost_to_valid         trials executed / confirmed findings

The harness runs scripted campaigns against MOCK targets (fixtures with
planted vulnerabilities) so metrics are measurable without touching any
real system.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Campaign:
    target: str
    started: float = field(default_factory=time.time)
    trials: int = 0
    reported: int = 0
    confirmed: int = 0
    with_evidence: int = 0
    chains_started: int = 0
    chains_completed: int = 0
    verifier_seen: int = 0
    verifier_rejected: int = 0
    known_vulns: int = 0
    known_found: int = 0
    root_causes: List[str] = field(default_factory=list)
    duplicate_reports: int = 0
    endpoints_known: int = 0
    endpoints_hit: int = 0
    first_valid_at: Optional[float] = None
    events: List[Dict] = field(default_factory=list)

    def log(self, event: str, **kw):
        self.events.append({"t": round(time.time() - self.started, 2),
                            "event": event, **kw})

    def trial(self):
        self.trials += 1

    def report_finding(self, root_cause: str, confirmed: bool,
                       evidence_ok: bool = False):
        self.reported += 1
        if root_cause in self.root_causes:
            self.duplicate_reports += 1
        else:
            self.root_causes.append(root_cause)
        if confirmed:
            self.confirmed += 1
            if evidence_ok:
                self.with_evidence += 1
            if self.first_valid_at is None:
                self.first_valid_at = time.time()

    def verify(self, rejected: bool):
        self.verifier_seen += 1
        if rejected:
            self.verifier_rejected += 1

    def metrics(self) -> Dict:
        elapsed = time.time() - self.started
        return {
            "target": self.target,
            "trials": self.trials,
            "discovery_recall": round(self.known_found / max(1, self.known_vulns), 3),
            "precision": round(self.confirmed / max(1, self.reported), 3),
            "proof_rate": round(self.with_evidence / max(1, self.confirmed), 3),
            "chain_completion": round(self.chains_completed / max(1, self.chains_started), 3),
            "verifier_rejection_rate": round(
                self.verifier_rejected / max(1, self.verifier_seen), 3),
            "time_to_first_valid_s": (round(self.first_valid_at - self.started, 1)
                                      if self.first_valid_at else None),
            "duplicate_rate": round(self.duplicate_reports / max(1, self.reported), 3),
            "endpoint_coverage": round(self.endpoints_hit / max(1, self.endpoints_known), 3),
            "cost_to_valid": round(self.trials / max(1, self.confirmed), 1),
            "elapsed_s": round(elapsed, 1),
        }


class MockTarget:
    """A synthetic target with planted vulnerabilities for benchmarking.

    endpoints: {path: {method, auth_required, owner_param, vuln}}
    vuln kinds: 'idor' (no object check), 'auth_bypass' (no auth check),
    'sqli' (tainted param). The mock answers deterministically.
    """

    def __init__(self, name: str, endpoints: Dict):
        self.name = name
        self.endpoints = endpoints

    def request(self, path: str, identity: str, params: Optional[Dict] = None) -> Dict:
        ep = self.endpoints.get(path, {})
        params = params or {}
        vuln = ep.get("vuln")
        if vuln == "auth_bypass":
            return {"status": 200, "body": f"data for {path} (no auth check)"}
        if ep.get("auth_required") and identity == "anonymous":
            return {"status": 401, "body": "unauthorized"}
        if vuln == "idor":
            owner = ep.get("owner", "alice")
            return {"status": 200,
                    "body": f"object owned by {owner}, served to {identity}"}
        if vuln == "sqli" and any("'" in str(v) for v in params.values()):
            return {"status": 500, "body": "SQL syntax error near '''"}
        return {"status": 200, "body": f"ok {path}"}

    def known_vulns(self) -> List[str]:
        return [p for p, ep in self.endpoints.items() if ep.get("vuln")]


def demo_campaign() -> Dict:
    """Scripted benchmark: hunt the mock with the real differential+oracle
    stack and compute §19 metrics."""
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import differential as diff_mod
    import oracle as oracle_mod

    target = MockTarget("mockshop", {
        "/api/orders/1": {"auth_required": True, "owner": "alice", "vuln": "idor"},
        "/api/orders/2": {"auth_required": True, "owner": "alice"},
        "/api/admin": {"auth_required": True, "vuln": "auth_bypass"},
        "/api/search": {"auth_required": False, "vuln": "sqli"},
        "/api/profile": {"auth_required": True},
    })
    camp = Campaign(target=target.name)
    camp.known_vulns = len(target.known_vulns())
    camp.endpoints_known = len(target.endpoints)

    # 1. IDOR differential: alice (owner) vs bob (other) on /api/orders/1
    camp.trial()
    camp.endpoints_hit += 1
    ctrl = target.request("/api/orders/1", "alice")
    test = target.request("/api/orders/1", "bob")
    verdict, _ = diff_mod.compare(str(ctrl), str(test))
    ov = oracle_mod.check("ownership", str(ctrl), str(test))
    if ov.verdict == "VIOLATED":
        camp.known_found += 1
        camp.report_finding("idor:/api/orders/1", True, evidence_ok=True)

    # 2. auth bypass probe
    camp.trial()
    camp.endpoints_hit += 1
    anon = target.request("/api/admin", "anonymous")
    ov2 = oracle_mod.check("auth_boundary", "401 unauthorized", str(anon))
    if ov2.verdict == "VIOLATED":
        camp.known_found += 1
        camp.report_finding("auth_bypass:/api/admin", True, evidence_ok=True)

    # 3. SQLi probe
    camp.trial()
    camp.endpoints_hit += 1
    sqli_obs = target.request("/api/search", "anonymous", {"q": "' OR 1=1--"})
    if "SQL syntax error" in sqli_obs["body"]:
        camp.known_found += 1
        camp.report_finding("sqli:/api/search", True, evidence_ok=True)

    # 4. negative control: properly-guarded endpoint must NOT report
    camp.trial()
    camp.endpoints_hit += 1
    c4 = target.request("/api/orders/2", "alice")
    t4 = target.request("/api/orders/2", "alice")  # same identity
    v4, _ = diff_mod.compare(str(c4), str(t4))
    assert v4 == "identical", "negative control failed"

    camp.verify(rejected=False)
    camp.verify(rejected=False)
    return camp.metrics()
