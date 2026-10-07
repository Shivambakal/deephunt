"""Tests for deephunt.technique_forge — the permutation/combination engine."""

import os
import subprocess
import sys
import tempfile
import unittest

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import technique_forge as forge

V2_FIELDS = {
    "id", "name", "klass", "requires", "signals", "questions", "evidence",
    "followups", "test", "impact_hint", "preconditions", "required_state",
    "hypothesis_generator", "request_strategy", "mutation_strategy",
    "expected_signal", "positive_oracle", "negative_evidence",
    "false_positive_rules", "followup_experiment", "regression_test",
    "difficulty_estimate",
}


class TestForge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = forge.load_corpus()

    def test_corpus_loads(self):
        self.assertGreater(len(self.corpus), 50, "corpus should hold dozens of cards")
        ids = [c.get("id") for c in self.corpus]
        self.assertEqual(len(ids), len(set(ids)), "corpus ids must be unique")
        for c in self.corpus[:10]:
            for f in ("id", "name", "klass", "preconditions", "positive_oracle"):
                self.assertIn(f, c, f"card {c.get('id')} missing v2 field {f}")

    def test_combo_rules_produce_combos(self):
        combos, dropped = forge.forge(self.corpus, seed=42, max_n=60)
        self.assertGreaterEqual(len(combos), 40, "should forge 40+ combos")
        self.assertLessEqual(len(combos), 60, "should respect --max")
        self.assertGreaterEqual(len(forge.COMBO_RULES), 20, "need 20+ combo families")

    def test_dedupe_no_duplicate_parent_sets(self):
        combos, _ = forge.forge(self.corpus, seed=7, max_n=200, per_rule_cap=50)
        keys = [frozenset(c["parents"]) for c in combos]
        self.assertEqual(len(keys), len(set(keys)), "duplicate parent sets slipped through")

    def test_every_combo_has_oracle_preconditions_why(self):
        combos, _ = forge.forge(self.corpus, seed=42, max_n=60)
        for c in combos:
            self.assertTrue(c["combined_oracle"] and c["combined_oracle"].strip(),
                            f"{c['id']} missing combined_oracle")
            self.assertTrue(c["preconditions"], f"{c['id']} missing preconditions")
            self.assertTrue(c["why_non_obvious"] and c["why_non_obvious"].strip(),
                            f"{c['id']} missing why_non_obvious")
            self.assertTrue(c["expected_signal"] and c["expected_signal"].strip(),
                            f"{c['id']} missing expected_signal")

    def test_determinism_with_seed(self):
        a, _ = forge.forge(self.corpus, seed=123, max_n=60)
        b, _ = forge.forge(self.corpus, seed=123, max_n=60)
        self.assertEqual([c["id"] for c in a], [c["id"] for c in b])
        self.assertEqual([c["name"] for c in a], [c["name"] for c in b])
        self.assertEqual([c["combined_oracle"] for c in a], [c["combined_oracle"] for c in b])
        c, _ = forge.forge(self.corpus, seed=999, max_n=60)
        self.assertNotEqual([x["parents"] for x in a], [x["parents"] for x in c],
                            "different seeds should (almost surely) shuffle differently")

    def test_emit_cards_writes_valid_yaml(self):
        combos, _ = forge.forge(self.corpus, seed=42, max_n=20)
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "cards_forge.yaml")
            out = forge.emit_cards(combos, path)
            self.assertEqual(out, path)
            with open(path, encoding="utf-8") as fh:
                cards = yaml.safe_load(fh)
        self.assertEqual(len(cards), len(combos))
        for card in cards:
            missing = V2_FIELDS - set(card.keys())
            self.assertFalse(missing, f"card {card.get('id')} missing v2 fields {missing}")
            self.assertEqual(card["klass"], "forged")
            self.assertTrue(str(card["id"]).startswith("F1-"))

    def test_no_combo_reuses_same_card_twice(self):
        combos, _ = forge.forge(self.corpus, seed=42, max_n=200, per_rule_cap=50)
        for c in combos:
            self.assertEqual(len(c["parents"]), len(set(c["parents"])),
                             f"{c['id']} uses the same card as both parents: {c['parents']}")

    def test_difficulty_within_1_to_5(self):
        combos, _ = forge.forge(self.corpus, seed=42, max_n=200, per_rule_cap=50)
        for c in combos:
            self.assertGreaterEqual(c["difficulty_estimate"], 1, c["id"])
            self.assertLessEqual(c["difficulty_estimate"], 5, c["id"])

    def test_parents_exist_in_corpus(self):
        corpus_ids = {c.get("id") for c in self.corpus}
        combos, _ = forge.forge(self.corpus, seed=42, max_n=60)
        for c in combos:
            for pid in c["parents"]:
                self.assertIn(pid, corpus_ids, f"{c['id']} references unknown parent {pid}")

    def test_oracle_is_combined_not_just_both_parents(self):
        combos, _ = forge.forge(self.corpus, seed=42, max_n=60)
        for c in combos:
            oracle = c["combined_oracle"]
            parents = [p for p in self.corpus if p.get("id") in c["parents"]]
            for p in parents:
                parent_oracle = str(p.get("positive_oracle", ""))
                # the combo oracle must not be a verbatim copy of a parent's oracle
                self.assertNotEqual(oracle.strip(), parent_oracle.strip(),
                                    f"{c['id']} oracle is just parent {p.get('id')}'s oracle")
            self.assertIn("COMBO-", oracle, f"{c['id']} oracle lacks a combo oracle marker")

    def test_cli_runs_with_seed_flag(self):
        with tempfile.TemporaryDirectory() as td:
            out = os.path.join(td, "out.yaml")
            r1 = subprocess.run(
                [sys.executable, "technique_forge.py", "--max", "25", "--seed", "5", "--out", out],
                cwd=os.path.dirname(os.path.abspath(__file__)),
                capture_output=True, text=True, timeout=120)
            self.assertEqual(r1.returncode, 0, r1.stderr)
            with open(out, encoding="utf-8") as fh:
                first = yaml.safe_load(fh)
            r2 = subprocess.run(
                [sys.executable, "technique_forge.py", "--max", "25", "--seed", "5", "--out", out],
                cwd=os.path.dirname(os.path.abspath(__file__)),
                capture_output=True, text=True, timeout=120)
            self.assertEqual(r2.returncode, 0, r2.stderr)
            with open(out, encoding="utf-8") as fh:
                second = yaml.safe_load(fh)
            self.assertEqual(
                [c["positive_oracle"] for c in first],
                [c["positive_oracle"] for c in second],
                "CLI --seed must be deterministic")


if __name__ == "__main__":
    unittest.main(verbosity=2)
