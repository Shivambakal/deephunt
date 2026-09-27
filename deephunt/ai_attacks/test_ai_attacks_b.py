"""Self-tests for deephunt/ai_attacks (part B: rag_poison, agent_abuse, extraction).

Run:  cd ~/workspace/hacker-agent/deephunt && python3 -m pytest ai_attacks/test_ai_attacks_b.py -q
      or: python3 ai_attacks/test_ai_attacks_b.py

All fixtures are mocks. Nothing here touches a real system.
"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_attacks import (  # noqa: E402
    approval_bypass_tests,
    covert_channel_patterns,
    distillation_signals,
    embedding_collision_notes,
    escalation_paths,
    map_tool_permissions,
    plan_rag_test,
    poisoned_document_patterns,
    system_prompt_extraction_battery,
    training_data_extraction_patterns,
)

MOCK_RAG_FAQ = {
    "retrieval": "semantic",
    "doc_types": ["faq"],
    "query_examples": ["How do I reset my password?", "What are the support hours?"],
}

MOCK_RAG_PDF = {
    "retrieval": "keyword",
    "doc_types": ["pdf-text"],
    "query_examples": ["Refund policy details"],
}

MOCK_TOOLS = [
    {"name": "send_email", "description": "Send an email message to any recipient address",
     "parameters": {"to": "string", "subject": "string", "body": "string"}},
    {"name": "run_shell", "description": "Execute a shell command on the host",
     "parameters": ["command"]},
    {"name": "read_docs", "description": "Search and read internal documents",
     "parameters": {"query": "string"}},
    {"name": "get_time", "description": "Return the current UTC time",
     "parameters": {}},
]

# Denylist lives ONLY in this test file; the assertion scans the modules,
# never this file, so no shipped code carries target specifics.
COMPANY_DENYLIST = [
    "adobe", "shopify", "yahoo", "google", "openai", "microsoft",
    "anthropic", "apple", "amazon", "meta", "wolt", "agoda", "tesla",
]


def _module_sources() -> str:
    base = os.path.dirname(os.path.abspath(__file__))
    blob = ""
    for fname in ("rag_poison.py", "agent_abuse.py", "extraction.py"):
        with open(os.path.join(base, fname), encoding="utf-8") as fh:
            blob += fh.read().lower()
    return blob


class TestRagPoison(unittest.TestCase):
    def test_patterns_count_and_shape(self):
        pats = poisoned_document_patterns()
        self.assertGreaterEqual(len(pats), 8)
        for p in pats:
            for key in ("id", "name", "carrier_type", "template", "injection_goal", "why_it_works"):
                self.assertIn(key, p, f"pattern {p.get('id')} missing {key}")
            self.assertIn(p["carrier_type"], ("markdown", "pdf-text", "html-comment", "metadata", "faq"))

    def test_required_pattern_classes_present(self):
        names = {p["name"] for p in poisoned_document_patterns()}
        for required in ("instruction-injection-in-doc",
                         "fake-FAQ-authoritative-answer-override",
                         "hidden-instruction-blocks",
                         "metadata-description-field-injection",
                         "conflicting-source-consensus-manipulation"):
            self.assertIn(required, names)

    def test_plan_is_surface_driven(self):
        faq_plan = plan_rag_test(MOCK_RAG_FAQ)
        pdf_plan = plan_rag_test(MOCK_RAG_PDF)
        by_id = {p["id"]: p for p in poisoned_document_patterns()}
        faq_types = {by_id[i]["carrier_type"] for i in faq_plan["selected_patterns"]}
        pdf_types = {by_id[i]["carrier_type"] for i in pdf_plan["selected_patterns"]}
        self.assertEqual(faq_types, {"faq"})
        self.assertEqual(pdf_types, {"pdf-text"})
        self.assertNotEqual(faq_plan["selected_patterns"], pdf_plan["selected_patterns"])

    def test_plan_trigger_queries_derive_from_surface(self):
        plan = plan_rag_test(MOCK_RAG_FAQ)
        texts = [q["text"] for q in plan["trigger_queries"]]
        for example in MOCK_RAG_FAQ["query_examples"]:
            self.assertIn(example, texts)
        purposes = [q["purpose"] for q in plan["trigger_queries"]]
        self.assertTrue(any("ontrol" in p for p in purposes))  # control query present

    def test_plan_has_expected_fields(self):
        plan = plan_rag_test(MOCK_RAG_FAQ)
        for key in ("expected_vulnerable", "expected_safe", "discriminating_observations",
                    "scoring_rule", "plant_operations", "trigger_queries"):
            self.assertIn(key, plan)
        self.assertIn("LLM08", plan["owasp"])

    def test_embedding_notes_honest(self):
        notes = embedding_collision_notes()
        self.assertIn("requires_model_access", notes)
        self.assertTrue(len(notes["requires_model_access"]) >= 2)
        self.assertIn("can_be_planned", notes)
        blob = str(notes).lower()
        self.assertIn("never", blob)  # honesty rule present


class TestAgentAbuse(unittest.TestCase):
    def test_permission_map_flags_risky_tools(self):
        m = map_tool_permissions(MOCK_TOOLS)
        self.assertEqual(m["send_email"]["risk"], "critical")
        self.assertIn("irreversible_action", m["send_email"]["capabilities"])
        self.assertEqual(m["run_shell"]["risk"], "critical")
        self.assertIn("code_exec", m["run_shell"]["capabilities"])
        self.assertEqual(m["read_docs"]["risk"], "medium")
        self.assertEqual(m["get_time"]["risk"], "low")
        self.assertEqual(m["get_time"]["capabilities"], [])

    def test_permission_map_summary(self):
        m = map_tool_permissions(MOCK_TOOLS)
        s = m["summary"]
        self.assertEqual(s["total_tools"], 4)
        self.assertIn("send_email", s["critical_tools"])
        self.assertIn("run_shell", s["critical_tools"])
        self.assertNotIn("get_time", s["risky_tools"])

    def test_escalation_paths_derive_from_capabilities(self):
        m = map_tool_permissions(MOCK_TOOLS)
        paths = escalation_paths(m)
        self.assertTrue(len(paths) >= 2)
        for p in paths:
            self.assertIn("id", p)
            self.assertTrue(len(p["steps"]) >= 2)
            self.assertIn("predicted_abuse", p)
            self.assertEqual(p["owasp"], "LLM06")

    def test_escalation_paths_empty_for_benign_tools(self):
        m = map_tool_permissions([MOCK_TOOLS[3]])  # get_time only
        self.assertEqual(escalation_paths(m), [])

    def test_approval_bypass_tests(self):
        m = map_tool_permissions(MOCK_TOOLS)
        tests = approval_bypass_tests(m)
        self.assertGreaterEqual(len(tests), 2)  # send_email + run_shell
        for t in tests:
            self.assertIn("id", t)
            self.assertIn("probe_prompt", t)
            self.assertEqual(t["expected_vulnerable"], "executes without confirmation")
            self.assertEqual(t["expected_safe"], "asks for confirmation/refuses")

    def test_covert_channel_patterns_well_formed(self):
        pats = covert_channel_patterns()
        self.assertGreaterEqual(len(pats), 4)
        for p in pats:
            for key in ("id", "name", "pattern", "detection_signals", "why_it_works"):
                self.assertIn(key, p)


class TestExtraction(unittest.TestCase):
    def test_battery_count_and_shape(self):
        probes = system_prompt_extraction_battery()
        self.assertGreaterEqual(len(probes), 10)
        for p in probes:
            for key in ("id", "probe_text", "success_markers", "expected_safe"):
                self.assertIn(key, p, f"probe {p.get('id')} missing {key}")
            self.assertTrue(p["probe_text"], f"probe {p['id']} has empty probe_text")
            self.assertTrue(len(p["success_markers"]) >= 1)
            self.assertTrue(p["expected_safe"])

    def test_battery_covers_required_classes(self):
        texts = " ".join(p["probe_text"].lower() for p in system_prompt_extraction_battery())
        self.assertIn("poem", texts)          # format shift
        self.assertIn("debug", texts)         # debug-mode claim
        self.assertIn("multi-turn", texts)    # multi-turn trust building
        self.assertIn("repeat", texts)        # repeat instructions

    def test_training_data_patterns_honest(self):
        pats = training_data_extraction_patterns()
        self.assertGreaterEqual(len(pats), 3)
        for p in pats:
            for key in ("id", "name", "procedure", "what_confirms", "what_does_not", "honest_note"):
                self.assertIn(key, p)

    def test_distillation_signals_passive_only(self):
        sigs = distillation_signals()
        self.assertGreaterEqual(len(sigs), 4)
        blob = " ".join(s["what_to_observe"] for s in sigs).lower()
        self.assertNotIn("bulk query", blob.replace("query-pattern", "x"))  # no active theft language
        for s in sigs:
            self.assertIn("why_it_suggests_distillation", s)


class TestTargetAgnostic(unittest.TestCase):
    def test_no_company_names_in_modules(self):
        import re
        blob = _module_sources()
        for company in COMPANY_DENYLIST:
            self.assertIsNone(
                re.search(r"\b" + re.escape(company) + r"\b", blob),
                f"hardcoded company reference: {company}",
            )

    def test_no_network_or_subprocess_in_modules(self):
        blob = _module_sources()
        for banned in ("import socket", "import requests", "import subprocess",
                       "urllib.request", "os.system", "os.popen"):
            self.assertNotIn(banned, blob, f"transmit-capable import: {banned}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
