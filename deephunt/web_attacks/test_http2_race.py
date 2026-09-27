"""Tests for web_attacks/http2_race.py (W1-031 single-packet race).

Mocks only. Run: python3 -m unittest web_attacks.test_http2_race -v
"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web_attacks import race_plan, score_race  # noqa: E402
from evidence import ContractRegistry, EvidenceContract  # noqa: E402

SURFACE = {"kind": "http2", "name": "mock-target",
           "endpoint": "/api/redeem", "requests": 20,
           "state_read": "GET /api/coupon-count",
           "state_unit": "coupon redemptions"}


class MockRaceEndpoint:
    def __init__(self, mode="vulnerable"):
        assert mode in ("vulnerable", "patched")
        self.mode = mode

    def observe(self, case, runs=2):
        n = case["request_count"]
        if self.mode == "vulnerable":
            return {"requests_sent": n, "state_before": 100.0,
                    "state_after": 100.0 + n, "responses_2xx": n, "runs": runs}
        # Patched: idempotency holds; also N x 200 to test the oracle.
        return {"requests_sent": n, "state_before": 100.0,
                "state_after": 101.0, "responses_2xx": n, "runs": runs}


class TestRacePlanner(unittest.TestCase):
    def test_plan_shape(self):
        cases = race_plan(SURFACE)
        self.assertEqual(len(cases), 1)
        c = cases[0]
        self.assertEqual(c["technique_card"], "W1-031")
        self.assertEqual(c["request_count"], 20)
        self.assertIn("release_schedule", c)
        self.assertIn("state_check", c)

    def test_oracle_is_state_not_status(self):
        c = race_plan(SURFACE)[0]
        self.assertIn("state", c["expected_vulnerable"].lower())
        self.assertNotIn("200", c["expected_vulnerable"])


class TestRaceScorer(unittest.TestCase):
    def test_positive_nfold_state(self):
        case = race_plan(SURFACE)[0]
        r = score_race(case, MockRaceEndpoint("vulnerable").observe(case))
        self.assertEqual(r["verdict"], "vulnerable")
        self.assertTrue(r["evidence_artifacts"]["server_state_diff"])

    def test_negative_patched_ignores_200s(self):
        # N x 200 responses but state advanced once: NOT a finding.
        case = race_plan(SURFACE)[0]
        r = score_race(case, MockRaceEndpoint("patched").observe(case))
        self.assertEqual(r["verdict"], "not_vulnerable")

    def test_single_run_lower_confidence(self):
        case = race_plan(SURFACE)[0]
        r = score_race(case, MockRaceEndpoint("vulnerable").observe(case, runs=1))
        self.assertEqual(r["verdict"], "vulnerable")
        self.assertLess(r["confidence"], 0.85)

    def test_evidence_contract(self):
        reg = ContractRegistry()
        reg.register(EvidenceContract(
            "W1-031", ["server_state_diff", "repeated_n_times",
                       "not_response_codes"]))
        case = race_plan(SURFACE)[0]
        r = score_race(case, MockRaceEndpoint("vulnerable").observe(case))
        ok, missing = reg.validate_evidence("W1-031", r["evidence_artifacts"])
        self.assertTrue(ok, f"missing={missing}")


if __name__ == "__main__":
    unittest.main()
