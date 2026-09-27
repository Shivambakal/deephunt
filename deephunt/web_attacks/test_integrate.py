"""Tests for web_attacks/integrate.py pipeline wiring.

Mocks only. Run: python3 -m unittest web_attacks.test_integrate -v
"""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web_attacks import (  # noqa: E402
    detect_web_surfaces, seed_hypotheses, expand_tests)


class _FakeTarget:
    name = "mock-target"

    def __init__(self):
        self.data = {"observations": []}


class _FakeTI:
    def __init__(self, techs):
        self.target = _FakeTarget()
        self._techs = techs

    def technologies(self):
        return self._techs


class TestWebIntegrate(unittest.TestCase):
    def test_detect_surfaces(self):
        ti = _FakeTI(["nginx http/2", "graphql api", "oauth jwt"])
        surfaces = detect_web_surfaces(ti)
        kinds = {s["kind"] for s in surfaces}
        self.assertTrue({"graphql", "oauth", "jwt", "http2", "http"} <= kinds)

    def test_no_signals_no_surfaces(self):
        ti = _FakeTI(["embedded firmware blob"])
        self.assertEqual(detect_web_surfaces(ti), [])

    def test_seeds_pure_data(self):
        ti = _FakeTI(["graphql api", "oauth"])
        seeds = seed_hypotheses("mock", ti)
        self.assertTrue(seeds)
        for s in seeds:
            self.assertTrue(s["provenance"].startswith("web_attacks"))
            self.assertIn("investigator_test", s)

    def test_expand_tests(self):
        ti = _FakeTI(["graphql api"])
        surface = {"kind": "graphql", "name": "mock", "endpoint": "/graphql",
                   "mutation": "updateBio", "mutation_arg": "bio"}
        h = {"id": "h1", "source": "web_attacks:graphql_alias",
             "statement": "alias batching probe", "investigator_test": "t",
             "provenance": "web_attacks seed; card W1-021"}
        cases = expand_tests(h, surface)
        self.assertTrue(cases)
        self.assertEqual(cases[0]["technique_card"], "W1-021")

    def test_all_planners_reachable(self):
        from web_attacks import integrate as wi
        self.assertEqual(len(wi._PLANNERS), 8)
        ti = _FakeTI(["http", "graphql", "oauth", "jwt", "http/2"])
        seeds = seed_hypotheses("mock", ti)
        sources = {s["source"] for s in seeds}
        for mod in wi._PLANNERS:
            self.assertIn(f"web_attacks:{mod}", sources, mod)


if __name__ == "__main__":
    unittest.main()
