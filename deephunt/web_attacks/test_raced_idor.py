"""Tests for web_attacks/raced_idor.py (F1 raced-IDOR combo).

Mocks only. Run: python3 -m unittest web_attacks.test_raced_idor -v
"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web_attacks import raced_idor_plan, score_raced_idor  # noqa: E402
from evidence import ContractRegistry, EvidenceContract  # noqa: E402

SURFACE = {"kind": "idor", "name": "mock-target",
           "object_endpoint": "/objects/{id}",
           "revoke_endpoint": "/objects/{id}/share"}


class MockShareService:
    def __init__(self, mode="vulnerable"):
        assert mode in ("vulnerable", "patched")
        self.mode = mode

    def observe(self):
        reads = [{"sent_at": 1.5, "status": 200, "victim_data": True},
                 {"sent_at": 2.0, "status": 200, "victim_data": True},
                 {"sent_at": 4.0, "status": 200, "victim_data": True}]
        if self.mode == "vulnerable":
            # Revocation completed at t=1.0; later reads still 200 + data.
            return {"revocation_completed_at": 1.0, "raced_reads": reads,
                    "control_victim_ok": True, "control_third_denied": True}
        return {"revocation_completed_at": 1.0,
                "raced_reads": [{"sent_at": 0.5, "status": 200,
                                 "victim_data": True},
                                {"sent_at": 1.5, "status": 403,
                                 "victim_data": False},
                                {"sent_at": 2.0, "status": 403,
                                 "victim_data": False}],
                "control_victim_ok": True, "control_third_denied": True}


class TestRacedIDORPlanner(unittest.TestCase):
    def test_plan_shape(self):
        cases = raced_idor_plan(SURFACE)
        self.assertEqual(len(cases), 1)
        c = cases[0]
        self.assertEqual(c["technique_card"], "F1-001")
        self.assertIn("schedule", c)
        self.assertIn("oracle", c)

    def test_oracle_is_post_revocation(self):
        c = raced_idor_plan(SURFACE)[0]
        self.assertIn("revocation_completed", c["oracle"])


class TestRacedIDORScorer(unittest.TestCase):
    def test_positive_toctou(self):
        case = raced_idor_plan(SURFACE)[0]
        r = score_raced_idor(case, MockShareService("vulnerable").observe())
        self.assertEqual(r["verdict"], "vulnerable")
        self.assertTrue(r["evidence_artifacts"]["revocation_authz_toctou"])

    def test_negative_revocation_effective(self):
        case = raced_idor_plan(SURFACE)[0]
        r = score_raced_idor(case, MockShareService("patched").observe())
        self.assertEqual(r["verdict"], "not_vulnerable")

    def test_pre_revocation_200_not_finding(self):
        # A 200 sent BEFORE revocation completed is plain IDOR timing,
        # not the raced-IDOR oracle.
        case = raced_idor_plan(SURFACE)[0]
        obs = {"revocation_completed_at": 5.0,
               "raced_reads": [{"sent_at": 1.0, "status": 200,
                                "victim_data": True}],
               "control_victim_ok": True, "control_third_denied": True}
        r = score_raced_idor(case, obs)
        self.assertEqual(r["verdict"], "not_vulnerable")

    def test_evidence_contract(self):
        reg = ContractRegistry()
        reg.register(EvidenceContract(
            "F1-001", ["post_revocation_200_with_victim_data",
                       "revocation_authz_toctou",
                       "control_victim_still_ok",
                       "control_third_denied"]))
        case = raced_idor_plan(SURFACE)[0]
        r = score_raced_idor(case, MockShareService("vulnerable").observe())
        ok, missing = reg.validate_evidence("F1-001", r["evidence_artifacts"])
        self.assertTrue(ok, f"missing={missing}")


if __name__ == "__main__":
    unittest.main()
