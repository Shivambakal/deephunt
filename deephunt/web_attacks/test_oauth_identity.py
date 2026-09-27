"""Tests for web_attacks/oauth_identity.py (W1-017 identity confusion).

Mocks only. Run: python3 -m unittest web_attacks.test_oauth_identity -v
"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web_attacks import identity_probes, score_identity  # noqa: E402
from evidence import ContractRegistry, EvidenceContract  # noqa: E402

SURFACE = {"kind": "oauth", "name": "mock-target", "provider": "mock-idp",
           "relying_party": "mock-app"}


class MockOAuthApp:
    def __init__(self, mode="vulnerable"):
        assert mode in ("vulnerable", "patched")
        self.mode = mode

    def observe(self):
        if self.mode == "vulnerable":
            # Attacker session carries the victim's user_id.
            return {"victim_user_id": "u-victim", "victim_sub": "sub-v",
                    "attacker_sub": "sub-a",
                    "attacker_session_user_id": "u-victim",
                    "victim_only_action_succeeded": True, "baselines_ok": True}
        return {"victim_user_id": "u-victim", "victim_sub": "sub-v",
                "attacker_sub": "sub-a",
                "attacker_session_user_id": "u-attacker",
                "victim_only_action_succeeded": False, "baselines_ok": True}


class TestIdentityPlanner(unittest.TestCase):
    def test_probe_cases(self):
        cases = identity_probes(SURFACE)
        self.assertEqual([c["id"] for c in cases],
                         ["OAUTH-ID-001", "OAUTH-ID-002"])
        for c in cases:
            self.assertEqual(c["technique_card"], "W1-017")
            self.assertIn("controls", c)

    def test_oracle_requires_privilege(self):
        c = identity_probes(SURFACE)[0]
        self.assertIn("privilege", c["expected_vulnerable"].lower())


class TestIdentityScorer(unittest.TestCase):
    def test_positive_ato(self):
        case = identity_probes(SURFACE)[0]
        r = score_identity(case, MockOAuthApp("vulnerable").observe())
        self.assertEqual(r["verdict"], "vulnerable")

    def test_negative_subject_binding(self):
        case = identity_probes(SURFACE)[0]
        r = score_identity(case, MockOAuthApp("patched").observe())
        self.assertEqual(r["verdict"], "not_vulnerable")

    def test_unverified_baselines_inconclusive(self):
        case = identity_probes(SURFACE)[0]
        obs = MockOAuthApp("vulnerable").observe()
        obs["baselines_ok"] = False
        r = score_identity(case, obs)
        self.assertEqual(r["verdict"], "inconclusive")

    def test_evidence_contract(self):
        reg = ContractRegistry()
        reg.register(EvidenceContract(
            "W1-017", ["privilege_inheritance_observed",
                       "distinct_accounts_verified",
                       "immutable_subject_control"]))
        case = identity_probes(SURFACE)[0]
        r = score_identity(case, MockOAuthApp("vulnerable").observe())
        ok, missing = reg.validate_evidence("W1-017", r["evidence_artifacts"])
        self.assertTrue(ok, f"missing={missing}")


if __name__ == "__main__":
    unittest.main()
