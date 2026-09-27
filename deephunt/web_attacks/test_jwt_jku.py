"""Tests for web_attacks/jwt_jku.py (C1-007 two-stage jku/x5u).

Mocks only. Run: python3 -m unittest web_attacks.test_jwt_jku -v
"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web_attacks import (  # noqa: E402
    jku_battery, score_jku_stage1, score_jku_stage2)
from evidence import ContractRegistry, EvidenceContract  # noqa: E402

SURFACE = {"kind": "jwt", "name": "mock-target",
           "token_param": "Authorization",
           "collaborator": "mock-collab.example", "header_param": "jku"}


class MockJWTServer:
    def __init__(self, mode="vulnerable"):
        assert mode in ("vulnerable", "patched")
        self.mode = mode

    def stage1(self, case):
        if self.mode == "vulnerable":
            return {"collaborator_hits": [case["unique_url"] + "?k=1"]}
        return {"collaborator_hits": []}

    def stage2(self, case):
        if self.mode == "vulnerable":
            return {"stage1_callback": True, "token_accepted": True,
                    "forged_claims_reflected": True}
        return {"stage1_callback": True, "token_accepted": False,
                "forged_claims_reflected": False}


class TestJKUPlanner(unittest.TestCase):
    def test_two_stages(self):
        cases = jku_battery(SURFACE)
        self.assertEqual(len(cases), 2)
        self.assertEqual([c["stage"] for c in cases], [1, 2])
        self.assertEqual(cases[1]["depends_on"], "JKU-STAGE1-001")

    def test_unique_url_per_case(self):
        a = jku_battery({**SURFACE, "collaborator": "c1.example"})[0]
        b = jku_battery({**SURFACE, "collaborator": "c2.example"})[0]
        self.assertNotEqual(a["unique_url"], b["unique_url"])


class TestJKUScorer(unittest.TestCase):
    def test_stage1_callback_is_ssrf_shaped(self):
        case = jku_battery(SURFACE)[0]
        r = score_jku_stage1(case, MockJWTServer("vulnerable").stage1(case))
        self.assertEqual(r["verdict"], "vulnerable")
        # Stage 1 alone must NOT claim forgery.
        self.assertFalse(r["evidence_artifacts"]["forgery_proven"])

    def test_stage1_negative(self):
        case = jku_battery(SURFACE)[0]
        r = score_jku_stage1(case, MockJWTServer("patched").stage1(case))
        self.assertEqual(r["verdict"], "not_vulnerable")

    def test_stage2_forgery(self):
        case = jku_battery(SURFACE)[1]
        r = score_jku_stage2(case, MockJWTServer("vulnerable").stage2(case))
        self.assertEqual(r["verdict"], "vulnerable")
        self.assertTrue(r["evidence_artifacts"]["forgery_proven"])

    def test_stage2_callback_but_rejected(self):
        # Card FP rule: callback alone is not forgery.
        case = jku_battery(SURFACE)[1]
        r = score_jku_stage2(case, MockJWTServer("patched").stage2(case))
        self.assertEqual(r["verdict"], "not_vulnerable")
        self.assertFalse(r["evidence_artifacts"]["forgery_proven"])

    def test_stage2_without_stage1_inconclusive(self):
        case = jku_battery(SURFACE)[1]
        obs = {"stage1_callback": False, "token_accepted": True,
               "forged_claims_reflected": True}
        r = score_jku_stage2(case, obs)
        self.assertEqual(r["verdict"], "inconclusive")

    def test_evidence_contract(self):
        reg = ContractRegistry()
        reg.register(EvidenceContract(
            "C1-007", ["callback_observed", "unique_url_used",
                       "forgery_proven"]))
        case = jku_battery(SURFACE)[1]
        r = score_jku_stage2(case, MockJWTServer("vulnerable").stage2(case))
        ok, missing = reg.validate_evidence("C1-007", r["evidence_artifacts"])
        self.assertTrue(ok, f"missing={missing}")


if __name__ == "__main__":
    unittest.main()
