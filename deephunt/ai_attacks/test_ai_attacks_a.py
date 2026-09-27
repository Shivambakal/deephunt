"""Tests for ai_attacks part 1: prompt_injection, jailbreak, scorer.

All fixtures are mocks. Nothing here touches a real system.
Run from ~/workspace/hacker-agent/deephunt:
    python3 -m unittest ai_attacks.test_ai_attacks_a -v
"""
from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_attacks import (  # noqa: E402
    battery,
    classify,
    delimiter_confusion_cases,
    direct_injection_cases,
    generate,
    indirect_injection_cases,
    instantiate,
    load_techniques,
    multiturn_escalation_plan,
)
from evidence import ContractRegistry, EvidenceContract  # noqa: E402

CHATBOT = {"kind": "chatbot", "name": "test-surface",
           "input_fields": ["message"]}
RAG = {"kind": "rag", "name": "other-surface", "input_fields": ["query"]}
AGENT = {"kind": "agent", "name": "third-surface", "input_fields": ["task"]}

# Brand names that must NEVER appear in generated probes (target-agnostic).
FORBIDDEN_BRANDS = ["adobe", "shopify", "yahoo", "google", "microsoft",
                    "openai", "anthropic", "meta", "amazon"]


class MockAIEndpoint:
    """Simulates vulnerable vs patched model behavior against probes."""

    def __init__(self, mode="vulnerable"):
        assert mode in ("vulnerable", "patched")
        self.mode = mode

    def respond(self, probe):
        markers = probe.get("success_markers") or []
        canary = markers[0] if markers else "CANARY"
        if self.mode == "vulnerable":
            return ("Understood. Following the instruction provided. "
                    f"Here is the requested output including {canary}.")
        return ("I can't follow instructions embedded in user content. "
                "I can help with your original request instead - "
                "let me know how else I can assist.")

    def respond_partial(self, probe):
        leaks = probe.get("leak_markers") or ["INTERNAL-HANDLING-NOTE"]
        return ("I can't provide that. However, for context, " + leaks[0] +
                " describes related internal handling.")


class TestTargetAgnostic(unittest.TestCase):
    def test_same_ids_across_surfaces(self):
        a = generate(CHATBOT)
        b = generate(RAG)
        self.assertEqual([c["id"] for c in a["cases"]],
                         [c["id"] for c in b["cases"]])

    def test_no_hardcoded_brands(self):
        import re
        blob = json.dumps(generate(AGENT)).lower()
        for brand in FORBIDDEN_BRANDS:
            # Word-boundary match: "meta" must not flag "metadata_field".
            self.assertIsNone(re.search(r"\b" + re.escape(brand) + r"\b",
                                        blob),
                              f"brand leaked into probes: {brand}")

    def test_surface_kind_propagates(self):
        for case in generate(RAG)["cases"]:
            self.assertEqual(case["surface_kind"], "rag")

    def test_generate_shape(self):
        out = generate(CHATBOT)
        self.assertEqual(set(out.keys()), {"cases", "count"})
        self.assertEqual(out["count"], len(out["cases"]))
        self.assertGreater(out["count"], 15)

    def test_case_schema(self):
        required = {"id", "family", "input_field", "expected_vulnerable",
                    "expected_safe", "owasp", "technique_card",
                    "success_markers", "forbidden_pattern", "leak_markers"}
        for case in generate(CHATBOT)["cases"]:
            if case.get("multiturn"):
                continue
            self.assertTrue(required <= set(case.keys()), case["id"])
            self.assertTrue(case["owasp"].startswith("LLM"), case["id"])

    def test_multiturn_plans_are_data(self):
        plans = multiturn_escalation_plan(CHATBOT)
        self.assertGreaterEqual(len(plans), 1)
        for plan in plans:
            self.assertIn("turns", plan)
            self.assertIn("escalation_ladder", plan)
            for turn in plan["turns"]:
                self.assertIsInstance(turn["user_text"], str)
        # JSON-serializable => pure data, no callables, engine executes later.
        json.dumps(plans)

    def test_indirect_carriers_present(self):
        for case in indirect_injection_cases(CHATBOT):
            self.assertIn("carrier_document", case)
            self.assertTrue(case["carrier_document"].strip())


class TestJailbreak(unittest.TestCase):
    def test_load_techniques_minimum(self):
        techs = load_techniques()
        self.assertGreaterEqual(len(techs), 12)
        for t in techs:
            for key in ("id", "name", "description", "template",
                        "multi_turn", "source_attribution"):
                self.assertIn(key, t, t.get("id"))

    def test_instantiate_fills_goal(self):
        probe = instantiate("JB-01", "reveal the admin password", CHATBOT)
        self.assertNotIn("{goal}", probe["input_text"])
        self.assertIn("reveal the admin password", probe["input_text"])
        self.assertEqual(probe["technique_card"], "AI-26")

    def test_instantiate_encoded(self):
        probe = instantiate("JB-03", "test goal", CHATBOT)
        self.assertNotIn("{encoded_goal}", probe["input_text"])
        self.assertNotIn("test goal", probe["input_text"])  # encoded

    def test_instantiate_multiturn(self):
        probe = instantiate("JB-06", "some goal", CHATBOT)
        self.assertTrue(probe["multi_turn"])
        self.assertIn("turns", probe)
        self.assertEqual(len(probe["turns"]), 3)
        self.assertNotIn("turns", instantiate("JB-01", "g", CHATBOT))

    def test_instantiate_unknown_raises(self):
        with self.assertRaises(KeyError):
            instantiate("JB-99", "goal", CHATBOT)

    def test_battery_covers_all(self):
        techs = load_techniques()
        bat = battery("some goal", CHATBOT)
        self.assertEqual(len(bat), len(techs))
        self.assertEqual(len({p["id"] for p in bat}), len(bat))


class TestScorer(unittest.TestCase):
    def test_refusal(self):
        probe = direct_injection_cases(CHATBOT)[0]
        result = classify(MockAIEndpoint("patched").respond(probe), probe)
        self.assertEqual(result["verdict"], "refusal")
        self.assertGreaterEqual(result["confidence"], 0.7)
        self.assertTrue(result["evidence_artifacts"]["refusal_detected"])
        self.assertTrue(any(s.startswith("refusal_phrase:")
                            for s in result["signals"]))

    def test_compliance(self):
        probe = direct_injection_cases(CHATBOT)[0]
        result = classify(MockAIEndpoint("vulnerable").respond(probe), probe)
        self.assertEqual(result["verdict"], "compliance")
        self.assertTrue(result["evidence_artifacts"]["success_markers_found"])
        self.assertIn("success_marker:BLUEHARE", result["signals"])

    def test_partial_leak(self):
        probe = {"success_markers": ["DIRECT-SECRET"],
                 "leak_markers": ["INTERNAL-HANDLING-NOTE"],
                 "forbidden_pattern": None}
        result = classify(MockAIEndpoint("patched").respond_partial(probe),
                          probe)
        self.assertEqual(result["verdict"], "partial_leak")
        self.assertTrue(result["evidence_artifacts"]["leak_markers_found"])
        self.assertTrue(result["evidence_artifacts"]["refusal_detected"])

    def test_inconclusive(self):
        probe = direct_injection_cases(CHATBOT)[0]
        result = classify("The weather is nice today.", probe)
        self.assertEqual(result["verdict"], "inconclusive")
        self.assertTrue(result["evidence_artifacts"]
                        ["classification_inconclusive"])

    def test_forbidden_pattern(self):
        probe = {"success_markers": [], "leak_markers": [],
                 "forbidden_pattern": r"internal-[a-z]+-key"}
        result = classify("Here is the internal-admin-key you asked for.",
                          probe)
        self.assertEqual(result["verdict"], "compliance")
        self.assertTrue(result["evidence_artifacts"]
                        ["forbidden_pattern_matched"])

    def test_evidence_artifacts_are_bool_dict(self):
        probe = delimiter_confusion_cases(CHATBOT)[0]
        arts = classify("hello", probe)["evidence_artifacts"]
        self.assertTrue(all(isinstance(v, bool)
                            for v in arts.values()))

    def test_contract_compatibility(self):
        registry = ContractRegistry()
        registry.register(EvidenceContract("AI-01", ["success_markers_found",
                                                     "refusal_detected"]))
        probe = direct_injection_cases(CHATBOT)[0]
        vuln = classify(MockAIEndpoint("vulnerable").respond(probe), probe)
        ok, missing = registry.validate_evidence(
            "AI-01", vuln["evidence_artifacts"])
        self.assertFalse(ok)  # vulnerable => refusal_detected is False
        self.assertEqual(missing, ["refusal_detected"])
        safe = classify(MockAIEndpoint("patched").respond(probe), probe)
        ok2, missing2 = registry.validate_evidence(
            "AI-01", safe["evidence_artifacts"])
        self.assertFalse(ok2)  # patched => success_markers_found is False
        self.assertEqual(missing2, ["success_markers_found"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
