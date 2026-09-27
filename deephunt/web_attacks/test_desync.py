"""Tests for web_attacks/desync.py (W1-001 CL.0/0.CL battery).

All fixtures are mocks. Nothing here touches a real system.
Run from ~/workspace/hacker-agent/deephunt:
    python3 -m unittest web_attacks.test_desync -v
"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web_attacks import desync_battery, score_desync  # noqa: E402
from evidence import ContractRegistry, EvidenceContract  # noqa: E402

SURFACE = {"kind": "http", "name": "mock-target", "host": "mock",
           "paths": ["/", "/static/app.js"]}


class MockSocketTarget:
    """Simulates FE/BE framing behavior for desync timing probes."""

    def __init__(self, mode="vulnerable"):
        assert mode in ("vulnerable", "patched")
        self.mode = mode

    def observe(self, case):
        canary = case["canary"]
        if self.mode == "vulnerable":
            # Queue poisoning: follow-up socket gets the smuggled response.
            return {
                "probe_latencies": [3.2, 3.1, 3.4],
                "control_latencies": [0.12, 0.10, 0.11],
                "followup_response": f"HTTP/1.1 200 OK\r\n\r\nadmin panel {canary}",
                "repeats": 3,
            }
        return {
            "probe_latencies": [0.12, 0.13, 0.11],
            "control_latencies": [0.12, 0.10, 0.11],
            "followup_response": "HTTP/1.1 200 OK\r\n\r\nbenign",
            "repeats": 3,
        }

    def observe_noisy(self):
        # Probes delayed AND controls also slow: differential exists but
        # the baseline is dirty — must be inconclusive, not vulnerable.
        return {
            "probe_latencies": [5.0, 5.1, 5.2],
            "control_latencies": [2.9, 3.0, 3.1],
            "followup_response": "HTTP/1.1 200 OK\r\n\r\nbenign",
            "repeats": 3,
        }


class TestDesyncPlanner(unittest.TestCase):
    def test_battery_covers_matrix(self):
        cases = desync_battery(SURFACE)
        cells = {c["matrix_cell"] for c in cases}
        self.assertIn("FE=CL x BE=none (CL.0)", cells)
        self.assertIn("FE=none x BE=CL (0.CL)", cells)

    def test_cases_have_contract(self):
        for c in desync_battery(SURFACE):
            self.assertTrue(c["expected_vulnerable"])
            self.assertTrue(c["expected_safe"])
            self.assertEqual(c["technique_card"], "W1-001")
            self.assertIn("{canary}", c["request_template"])

    def test_target_agnostic(self):
        a = desync_battery({**SURFACE, "host": "h1"})
        b = desync_battery({**SURFACE, "host": "h2"})
        self.assertNotEqual(a[0]["request_template"], b[0]["request_template"])
        self.assertEqual(a[0]["canary"], b[0]["canary"])


class TestDesyncScorer(unittest.TestCase):
    def test_positive_queue_poisoning(self):
        case = desync_battery(SURFACE)[0]
        obs = MockSocketTarget("vulnerable").observe(case)
        r = score_desync(case, obs)
        self.assertEqual(r["verdict"], "vulnerable")
        self.assertTrue(r["evidence_artifacts"]["queue_poisoning_observed"])

    def test_negative_patched(self):
        case = desync_battery(SURFACE)[0]
        obs = MockSocketTarget("patched").observe(case)
        r = score_desync(case, obs)
        self.assertEqual(r["verdict"], "not_vulnerable")

    def test_noisy_controls_inconclusive(self):
        case = desync_battery(SURFACE)[0]
        obs = MockSocketTarget("patched").observe_noisy()
        r = score_desync(case, obs)
        self.assertEqual(r["verdict"], "inconclusive")

    def test_evidence_contract(self):
        reg = ContractRegistry()
        reg.register(EvidenceContract(
            "W1-001",
            ["queue_poisoning_observed", "timing_differential_repeated",
             "control_clean"]))
        case = desync_battery(SURFACE)[0]
        obs = MockSocketTarget("vulnerable").observe(case)
        r = score_desync(case, obs)
        ok, missing = reg.validate_evidence("W1-001",
                                            r["evidence_artifacts"])
        self.assertTrue(ok, f"missing={missing}")


if __name__ == "__main__":
    unittest.main()
