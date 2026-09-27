"""Tests for ai_attacks wave-1 extensions: exfiltration (A1-002),
ghostjacking (A1-016), memory_write (A1-008) + integrate wiring.

All fixtures are mocks. Nothing here touches a real system.
Run from ~/workspace/hacker-agent/deephunt:
    python3 -m unittest ai_attacks.test_ai_attacks_c -v
"""
from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_attacks import (  # noqa: E402
    exfil_chain_cases, score_exfil,
    ghostjack_cases, score_ghostjack,
    memory_write_cases, score_memory_write,
    integrate,
)
from evidence import ContractRegistry, EvidenceContract  # noqa: E402

SURFACE = {"kind": "agent", "name": "test-surface",
           "input_fields": ["task"]}

FORBIDDEN_BRANDS = ["adobe", "shopify", "yahoo", "google", "microsoft",
                    "openai", "anthropic", "meta", "amazon"]


class MockCopilot:
    """Simulates copilot behavior against the exfil chain."""

    def __init__(self, mode="vulnerable"):
        assert mode in ("vulnerable", "patched")
        self.mode = mode

    def observe(self, case):
        canary = case["canary_url"]
        if self.mode == "vulnerable" and not case.get("is_control"):
            return {"outbound_requests": [
                        {"url": canary + "?data=salary-alice-120k",
                         "data": "salary summary"}],
                    "user_interaction": False, "tenant_data_accessed": True}
        return {"outbound_requests": [], "user_interaction": False,
                "tenant_data_accessed": False}


class MockInvestigator:
    def __init__(self, mode="vulnerable"):
        assert mode in ("vulnerable", "patched")
        self.mode = mode

    def observe(self, case):
        if self.mode == "vulnerable" and not case.get("is_control"):
            return {"agent_report": "Attacker attempted SQLi. pwned-by-log",
                    "tool_actions": [], "canary": case["canary"],
                    "quoted_only": False}
        return {"agent_report": "Blocked request: GET /admin/debug?cmd=... "
                                "(quoted as evidence). Attempted SQLi.",
                "tool_actions": [], "canary": case["canary"],
                "quoted_only": True}


class MockMemoryAgent:
    def __init__(self, mode="vulnerable"):
        assert mode in ("vulnerable", "patched")
        self.mode = mode

    def observe(self, case):
        if self.mode == "vulnerable" and not case.get("is_control"):
            return {"fresh_session": True,
                    "victim_query_response":
                        "Check deploy status via DH-MEMWRITE-redirect.example/ops",
                    "canary": case["canary"], "stored_record_seen": True}
        return {"fresh_session": True,
                "victim_query_response":
                    "Check deploy status at dashboard.internal",
                "canary": case["canary"], "stored_record_seen": False}


class TestTargetAgnostic(unittest.TestCase):
    def test_no_hardcoded_brands(self):
        import re
        blob = json.dumps([
            exfil_chain_cases(SURFACE), ghostjack_cases(SURFACE),
            memory_write_cases(SURFACE)]).lower()
        for brand in FORBIDDEN_BRANDS:
            self.assertIsNone(re.search(r"\b" + re.escape(brand) + r"\b", blob),
                              f"brand leaked: {brand}")


class TestExfiltration(unittest.TestCase):
    def test_pair(self):
        cases = exfil_chain_cases(SURFACE)
        self.assertEqual(len(cases), 2)
        self.assertEqual([c["technique_card"] for c in cases],
                         ["A1-002", "A1-002"])
        self.assertTrue(cases[0]["is_control"])

    def test_positive(self):
        case = exfil_chain_cases(SURFACE)[1]
        r = score_exfil(case, MockCopilot("vulnerable").observe(case))
        self.assertEqual(r["verdict"], "vulnerable")
        self.assertTrue(r["evidence_artifacts"]["tenant_data_exfiltrated"])

    def test_negative(self):
        case = exfil_chain_cases(SURFACE)[1]
        r = score_exfil(case, MockCopilot("patched").observe(case))
        self.assertEqual(r["verdict"], "not_vulnerable")

    def test_fetch_without_data_inconclusive(self):
        case = exfil_chain_cases(SURFACE)[1]
        obs = {"outbound_requests": [{"url": case["canary_url"], "data": ""}],
               "user_interaction": False, "tenant_data_accessed": False}
        r = score_exfil(case, obs)
        self.assertEqual(r["verdict"], "inconclusive")

    def test_evidence_contract(self):
        reg = ContractRegistry()
        reg.register(EvidenceContract(
            "A1-002", ["canary_url_reached", "tenant_data_exfiltrated",
                       "zero_click"]))
        case = exfil_chain_cases(SURFACE)[1]
        r = score_exfil(case, MockCopilot("vulnerable").observe(case))
        ok, missing = reg.validate_evidence("A1-002", r["evidence_artifacts"])
        self.assertTrue(ok, f"missing={missing}")


class TestGhostjacking(unittest.TestCase):
    def test_pair(self):
        cases = ghostjack_cases(SURFACE)
        self.assertEqual(len(cases), 2)
        self.assertTrue(cases[0]["is_control"])

    def test_positive(self):
        case = ghostjack_cases(SURFACE)[1]
        r = score_ghostjack(case, MockInvestigator("vulnerable").observe(case))
        self.assertEqual(r["verdict"], "vulnerable")

    def test_negative_quoted_only(self):
        case = ghostjack_cases(SURFACE)[1]
        r = score_ghostjack(case, MockInvestigator("patched").observe(case))
        self.assertEqual(r["verdict"], "not_vulnerable")

    def test_evidence_contract(self):
        reg = ContractRegistry()
        reg.register(EvidenceContract(
            "A1-016", ["canary_executed_from_log",
                       "investigation_flow_carried_payload"]))
        case = ghostjack_cases(SURFACE)[1]
        r = score_ghostjack(case, MockInvestigator("vulnerable").observe(case))
        ok, missing = reg.validate_evidence("A1-016", r["evidence_artifacts"])
        self.assertTrue(ok, f"missing={missing}")


class TestMemoryWrite(unittest.TestCase):
    def test_cases(self):
        cases = memory_write_cases(SURFACE)
        self.assertEqual(len(cases), 2)
        self.assertEqual(cases[0]["phase"], "plant")

    def test_positive(self):
        case = memory_write_cases(SURFACE)[0]
        r = score_memory_write(case, MockMemoryAgent("vulnerable").observe(case))
        self.assertEqual(r["verdict"], "vulnerable")

    def test_negative(self):
        case = memory_write_cases(SURFACE)[0]
        r = score_memory_write(case, MockMemoryAgent("patched").observe(case))
        self.assertEqual(r["verdict"], "not_vulnerable")

    def test_same_session_inconclusive(self):
        case = memory_write_cases(SURFACE)[0]
        obs = MockMemoryAgent("vulnerable").observe(case)
        obs["fresh_session"] = False
        r = score_memory_write(case, obs)
        self.assertEqual(r["verdict"], "inconclusive")

    def test_evidence_contract(self):
        reg = ContractRegistry()
        reg.register(EvidenceContract(
            "A1-008", ["canary_persisted_across_sessions",
                       "victim_query_redirected"]))
        case = memory_write_cases(SURFACE)[0]
        r = score_memory_write(case, MockMemoryAgent("vulnerable").observe(case))
        ok, missing = reg.validate_evidence("A1-008", r["evidence_artifacts"])
        self.assertTrue(ok, f"missing={missing}")


class _FakeTarget:
    name = "mock-target"

    class data:
        pass

    def __init__(self):
        self.data = {"observations": []}


class _FakeTI:
    def __init__(self, techs):
        self.target = _FakeTarget()
        self._techs = techs

    def technologies(self):
        return self._techs


class TestIntegrateWiring(unittest.TestCase):
    def test_new_seeds(self):
        ti = _FakeTI(["copilot assistant", "agent framework"])
        seeds = integrate.seed_hypotheses("mock", ti)
        sources = {s["source"] for s in seeds}
        self.assertIn("ai_attacks:exfiltration", sources)
        self.assertIn("ai_attacks:ghostjacking", sources)
        self.assertIn("ai_attacks:memory_write", sources)

    def test_expand_dispatch(self):
        ti = _FakeTI(["copilot assistant", "agent framework"])
        surface = {"kind": "agent", "name": "mock", "input_fields": ["task"]}
        for src in ("ai_attacks:exfiltration", "ai_attacks:ghostjacking",
                    "ai_attacks:memory_write"):
            h = {"id": "h1", "source": src,
                 "statement": f"probe {src}", "investigator_test": "t"}
            cases = integrate.expand_tests(h, surface)
            self.assertTrue(cases, f"no cases for {src}")
            self.assertTrue(all(c.get("id") for c in cases))

    def test_extraction_not_shadowed_by_exfiltration(self):
        ti = _FakeTI(["copilot assistant"])
        seeds = integrate.seed_hypotheses("mock", ti)
        ext = [s for s in seeds if s["source"] == "ai_attacks:extraction"]
        self.assertTrue(ext, "extraction seed missing")
        h = {"id": "h9", "source": "ai_attacks:extraction",
             "statement": "extraction probe", "investigator_test": "t"}
        surface = {"kind": "chatbot", "name": "mock",
                   "input_fields": ["message"]}
        cases = integrate.expand_tests(h, surface)
        self.assertTrue(cases)


if __name__ == "__main__":
    unittest.main()
