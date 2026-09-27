"""Tests for web_attacks/graphql_alias.py (W1-021).

Mocks only. Run: python3 -m unittest web_attacks.test_graphql_alias -v
"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web_attacks import alias_battery, score_alias  # noqa: E402
from evidence import ContractRegistry, EvidenceContract  # noqa: E402

SURFACE = {"kind": "graphql", "name": "mock-target", "endpoint": "/graphql",
           "mutation": "updateBio", "mutation_arg": "bio"}


class MockGraphQLEndpoint:
    def __init__(self, mode="vulnerable"):
        assert mode in ("vulnerable", "patched")
        self.mode = mode

    def observe(self, case):
        n = case["alias_count"]
        if self.mode == "vulnerable":
            # Limiter counts the HTTP request; all N ops execute.
            return {"alias_count": n, "http_requests": 1,
                    "side_effects_observed": n, "rate_limited": False,
                    "control_single_ok": True}
        # Patched: limiter counts operations, rejects the batch.
        return {"alias_count": n, "http_requests": 1,
                "side_effects_observed": 0, "rate_limited": True,
                "control_single_ok": True}

    def observe_partial(self, case):
        # 200 returned but only some effects executed: NOT full bypass.
        return {"alias_count": case["alias_count"], "http_requests": 1,
                "side_effects_observed": 3, "rate_limited": False,
                "control_single_ok": True}


class TestAliasPlanner(unittest.TestCase):
    def test_battery_sizes(self):
        cases = alias_battery(SURFACE)
        self.assertEqual([c["alias_count"] for c in cases], [10, 100, 500])

    def test_document_alias_count(self):
        for c in alias_battery(SURFACE):
            n = c["alias_count"]
            doc = c["graphql_document"]
            self.assertEqual(doc.count("dh_alias"), n * 2)  # alias + echo arg
            self.assertTrue(c["expected_vulnerable"])

    def test_side_effect_probe_present(self):
        for c in alias_battery(SURFACE):
            self.assertIn("side_effect_probe", c)


class TestAliasScorer(unittest.TestCase):
    def test_positive_full_bypass(self):
        case = alias_battery(SURFACE)[1]  # n=100
        r = score_alias(case, MockGraphQLEndpoint("vulnerable").observe(case))
        self.assertEqual(r["verdict"], "vulnerable")

    def test_negative_patched(self):
        case = alias_battery(SURFACE)[1]
        r = score_alias(case, MockGraphQLEndpoint("patched").observe(case))
        self.assertEqual(r["verdict"], "not_vulnerable")

    def test_partial_execution_not_vulnerable(self):
        # Card FP rule: 200 with partial execution is not full bypass.
        case = alias_battery(SURFACE)[1]
        r = score_alias(case, MockGraphQLEndpoint("patched").observe_partial(case))
        self.assertNotEqual(r["verdict"], "vulnerable")

    def test_evidence_contract(self):
        reg = ContractRegistry()
        reg.register(EvidenceContract(
            "W1-021", ["side_effects_counted", "single_request",
                       "control_single_mutation_ok"]))
        case = alias_battery(SURFACE)[0]
        r = score_alias(case, MockGraphQLEndpoint("vulnerable").observe(case))
        ok, missing = reg.validate_evidence("W1-021", r["evidence_artifacts"])
        self.assertTrue(ok, f"missing={missing}")


if __name__ == "__main__":
    unittest.main()
