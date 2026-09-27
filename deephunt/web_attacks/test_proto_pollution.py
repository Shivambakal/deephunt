"""Tests for web_attacks/proto_pollution.py (C1-014 json-spaces oracle).

Mocks only. Run: python3 -m unittest web_attacks.test_proto_pollution -v
"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web_attacks import pollution_probe, score_pollution  # noqa: E402
from evidence import ContractRegistry, EvidenceContract  # noqa: E402

SURFACE = {"kind": "http", "name": "mock-target",
           "merge_endpoint": "/api/merge", "read_endpoint": "/api/status"}


class MockJSONServer:
    def __init__(self, mode="vulnerable"):
        assert mode in ("vulnerable", "patched")
        self.mode = mode

    def observe(self):
        if self.mode == "vulnerable":
            return {"baseline_pretty": False, "after_pretty": True,
                    "after_indent": 10, "marker_leaked": False}
        return {"baseline_pretty": False, "after_pretty": False,
                "after_indent": -1, "marker_leaked": False}


class TestPollutionPlanner(unittest.TestCase):
    def test_probe_shape(self):
        cases = pollution_probe(SURFACE)
        self.assertEqual(len(cases), 1)
        c = cases[0]
        self.assertEqual(c["technique_card"], "C1-014")
        self.assertEqual(c["pollution_payload"],
                         {"__proto__": {"json spaces": 10}})
        self.assertIn("baseline", c["control"])


class TestPollutionScorer(unittest.TestCase):
    def test_positive_oracle(self):
        case = pollution_probe(SURFACE)[0]
        r = score_pollution(case, MockJSONServer("vulnerable").observe())
        self.assertEqual(r["verdict"], "vulnerable")
        self.assertTrue(r["evidence_artifacts"]["indent_matches_canary"])

    def test_negative_patched(self):
        case = pollution_probe(SURFACE)[0]
        r = score_pollution(case, MockJSONServer("patched").observe())
        self.assertEqual(r["verdict"], "not_vulnerable")

    def test_baseline_already_pretty_inconclusive(self):
        case = pollution_probe(SURFACE)[0]
        obs = {"baseline_pretty": True, "after_pretty": True,
               "after_indent": 2, "marker_leaked": False}
        r = score_pollution(case, obs)
        self.assertEqual(r["verdict"], "inconclusive")

    def test_evidence_contract(self):
        reg = ContractRegistry()
        reg.register(EvidenceContract(
            "C1-014", ["formatting_changed", "indent_matches_canary",
                       "baseline_recorded"]))
        case = pollution_probe(SURFACE)[0]
        r = score_pollution(case, MockJSONServer("vulnerable").observe())
        ok, missing = reg.validate_evidence("C1-014", r["evidence_artifacts"])
        self.assertTrue(ok, f"missing={missing}")


if __name__ == "__main__":
    unittest.main()
