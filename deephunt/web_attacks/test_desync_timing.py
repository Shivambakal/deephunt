"""Tests for web_attacks/desync_timing.py (C1-016 timing differential).

Mocks only. Run: python3 -m unittest web_attacks.test_desync_timing -v
"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web_attacks import timing_probes, score_timing  # noqa: E402
from evidence import ContractRegistry, EvidenceContract  # noqa: E402

SURFACE = {"kind": "http", "name": "mock-target", "host": "mock",
           "paths": ["/"]}


def _obs(probe, control, repeats=3):
    return {"probe_delays": probe, "control_delays": control,
            "repeats": repeats}


class TestTimingPlanner(unittest.TestCase):
    def test_probes_plus_control(self):
        cases = timing_probes(SURFACE)
        ids = [c["id"] for c in cases]
        self.assertIn("TIMING-CLTE-001", ids)
        self.assertIn("TIMING-TECL-001", ids)
        self.assertIn("TIMING-CONTROL-001", ids)
        for c in cases:
            self.assertEqual(c["repeats"], 3)
            self.assertEqual(c["technique_card"], "C1-016")


class TestTimingScorer(unittest.TestCase):
    def test_positive_repeated_differential(self):
        case = timing_probes(SURFACE)[0]
        r = score_timing(case, _obs([3.1, 3.3, 3.0], [0.1, 0.12, 0.09]))
        self.assertEqual(r["verdict"], "vulnerable")
        self.assertTrue(r["evidence_artifacts"]["delay_reproduced"])

    def test_negative_no_delta(self):
        case = timing_probes(SURFACE)[0]
        r = score_timing(case, _obs([0.11, 0.13, 0.1], [0.1, 0.12, 0.09]))
        self.assertEqual(r["verdict"], "not_vulnerable")

    def test_single_slow_not_enough(self):
        # Card FP rule: one slow response is noise — require repeats.
        case = timing_probes(SURFACE)[0]
        r = score_timing(case, _obs([3.1], [0.1], repeats=1))
        self.assertEqual(r["verdict"], "inconclusive")

    def test_noisy_controls_inconclusive(self):
        case = timing_probes(SURFACE)[1]
        r = score_timing(case, _obs([3.1, 3.0, 3.2], [2.8, 3.1, 2.9]))
        self.assertEqual(r["verdict"], "inconclusive")

    def test_evidence_contract(self):
        reg = ContractRegistry()
        reg.register(EvidenceContract(
            "C1-016", ["delay_reproduced", "control_clean", "repeats_met"]))
        case = timing_probes(SURFACE)[0]
        r = score_timing(case, _obs([3.1, 3.3, 3.0], [0.1, 0.12, 0.09]))
        ok, missing = reg.validate_evidence("C1-016", r["evidence_artifacts"])
        self.assertTrue(ok, f"missing={missing}")


if __name__ == "__main__":
    unittest.main()
