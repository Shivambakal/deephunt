"""Integration tests for ai_attacks wiring (mock fixtures only).

Verifies: surface detection, seed shape compatibility with
hypothesis_fusion, test expansion, scorer wiring, propose-only rails
(no transmission-capable imports), and adapter gating.
"""
import os
import sys
import unittest

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "intel"))
sys.path.insert(0, os.path.dirname(BASE))

from ai_attacks import integrate
from ai_attacks import scorer
from ai_attacks.adapters import garak_adapter, pyrit_adapter, jbb_corpus


class FakeTarget:
    def __init__(self, name, techs, observations):
        self.name = name
        self.data = {"observations": observations}
        self._techs = techs


class FakeTI:
    def __init__(self, name, techs, observations):
        self.target = FakeTarget(name, techs, observations)
        self._techs = techs

    def technologies(self):
        return self._techs

    def summary(self):
        return "fake"


def ai_ti():
    return FakeTI("demo-ai-co", ["python", "openai", "langchain", "react"],
                  ["site has a support chatbot powered by GPT",
                   "knowledge base uses vector retrieval (RAG)"])


def plain_ti():
    return FakeTI("demo-plain-co", ["nginx", "wordpress"],
                  ["blog site, no AI features observed"])


class TestDetect(unittest.TestCase):
    def test_detects_ai_surface(self):
        surfaces = integrate.detect_ai_surfaces(ai_ti())
        self.assertEqual(len(surfaces), 1)
        self.assertIn(surfaces[0]["kind"], ("chatbot", "rag", "agent"))
        self.assertTrue(surfaces[0]["signals"])

    def test_no_ai_no_surface(self):
        self.assertEqual(integrate.detect_ai_surfaces(plain_ti()), [])

    def test_target_agnostic(self):
        s1 = integrate.detect_ai_surfaces(ai_ti())
        ti2 = FakeTI("other-corp", ["openai"], ["chatbot"])
        s2 = integrate.detect_ai_surfaces(ti2)
        self.assertNotIn("demo-ai-co", str(s2))
        self.assertTrue(s1 and s2)


class TestSeeds(unittest.TestCase):
    def test_seed_shape(self):
        seeds = integrate.seed_hypotheses("demo-ai-co", ai_ti())
        self.assertGreaterEqual(len(seeds), 3)
        for s in seeds:
            for k in ("statement", "source", "score", "investigator_test",
                      "provenance"):
                self.assertIn(k, s, f"seed missing {k}")
            self.assertTrue(s["source"].startswith("ai_attacks:"))
            self.assertNotIn("demo-ai-co".upper() + "-HARDCODED", s["statement"])

    def test_no_seeds_without_surface(self):
        self.assertEqual(integrate.seed_hypotheses("x", plain_ti()), [])


class TestExpand(unittest.TestCase):
    def test_expand_injection(self):
        hyp = {"id": "h1", "source": "ai_attacks:prompt_injection",
               "statement": "prompt injection possible",
               "investigator_test": "run battery"}
        cases = integrate.expand_tests(
            hyp, {"kind": "chatbot", "name": "t", "input_fields": ["msg"]})
        self.assertTrue(len(cases) > 5)
        for c in cases:
            self.assertIn("expected_vulnerable", c)
            self.assertIn("expected_safe", c)

    def test_expand_caps(self):
        hyp = {"id": "h1", "source": "ai_attacks:jailbreak",
               "statement": "jailbreak", "investigator_test": "x"}
        cases = integrate.expand_tests(
            hyp, {"kind": "chatbot", "name": "t", "input_fields": []})
        self.assertLessEqual(len(cases), 25)


class TestScorerWire(unittest.TestCase):
    def test_score_observation(self):
        probe = {"id": "p1", "success_markers": ["BLUEHARE"],
                 "forbidden_pattern": None, "leak_markers": []}
        r = integrate.score_observation(
            probe, "Sure, BLUEHARE is the token you asked about.")
        self.assertEqual(r["verdict"], "compliance")
        self.assertIsInstance(r["evidence_artifacts"], dict)
        r2 = integrate.score_observation(
            probe, "I can't help with that. Is there something else I can do?")
        self.assertEqual(r2["verdict"], "refusal")


class TestProposeOnly(unittest.TestCase):
    BANNED = ("import socket", "import requests", "import subprocess",
              "urllib.request", "http.client")

    def test_no_transmit_imports(self):
        pkg = os.path.join(BASE, "ai_attacks")
        for root, _, files in os.walk(pkg):
            if "adapters" in root:
                continue  # adapters gate execution behind TestAuthorization
            for fn in files:
                if not fn.endswith(".py") or fn.startswith("test_"):
                    continue
                src = open(os.path.join(root, fn)).read()
                for banned in self.BANNED:
                    self.assertNotIn(banned, src,
                                     f"{fn} contains {banned}")

    def test_adapter_gating(self):
        spec = garak_adapter.plan_scan(
            garak_adapter.build_rest_config("https://api.example.com/v1/chat"))
        # no auth -> PermissionError (or not-installed dict)
        try:
            out = garak_adapter.run_scan(spec, authorization={})
            self.assertFalse(out.get("ok", True))
        except PermissionError:
            pass
        # wrong scope -> PermissionError
        try:
            garak_adapter.run_scan(
                spec, {"token": "tok", "scope_hosts": ["other.com"]})
            self.fail("expected PermissionError for out-of-scope host")
        except PermissionError:
            pass

    def test_adapter_specs_pure_data(self):
        cfg = garak_adapter.build_rest_config("https://x.example/chat")
        self.assertIn("$INPUT", str(cfg))
        pspec = pyrit_adapter.plan_redteam("SYNTHETIC objective")
        self.assertEqual(pspec["tool"], "pyrit")
        # jbb offline: returns list (empty if datasets missing)
        self.assertIsInstance(jbb_corpus.load_behaviors(limit=2), list)


class TestPipelineStage(unittest.TestCase):
    def test_stage_registers_ai_hypotheses(self):
        import attacksurface
        from brain.session import ResearchSession
        import learn as learn_mem
        session = ResearchSession(objective="test:ai-wire")
        ti = ai_ti()
        out = attacksurface.stage_ai_attacks(session, "demo-ai-co", ti)
        self.assertTrue(out["seeds"])
        seeds = {"seed_hypotheses": out["seeds"]}
        mem = learn_mem.load_memory("demo-ai-co-wiretest")
        fused = attacksurface.stage_hypotheses(session, seeds, [],
                                               {"hypothesis_seeds": []},
                                               mem, 12)
        srcs = [h.get("provenance", "") for h in
                session.state["hypotheses"]]
        self.assertTrue(any(str(s).startswith("ai_attacks") for s in srcs),
                        f"no ai_attacks hypotheses registered: {srcs}")
        self.assertGreater(len(fused["registered"]), 0)


if __name__ == "__main__":
    unittest.main(verbosity=1)
