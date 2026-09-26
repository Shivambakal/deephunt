"""DEEPHUNT train — the program's hunter instinct. Matches funnel findings
against the technique knowledge base and produces ranked, targeted hypothesis
seeds. This is what makes DEEPHUNT dangerous on ANY target, not just Adobe."""
from __future__ import annotations
import os
import re

import kb  # noqa: E402  — enriched technique cards from knowledge/techniques/*.yaml

BASE = os.path.dirname(os.path.abspath(__file__))


def load_techniques():
    """Enriched cards via kb (source of truth: knowledge/techniques/*.yaml)."""
    return kb.load_techniques()


def _haystack(findings):
    return " ".join(
        (f.get("title", "") + " " + f.get("detail", "") + " " +
         f.get("evidence", "")) for f in findings).lower()


def recommend(findings, profile, mem, limit=10):
    """Rank technique cards by signal match against funnel findings."""
    hay = _haystack(findings)
    tech_terms = " ".join(profile.get("tech_terms", [])).lower()
    vuln_classes = " ".join(profile.get("vuln_classes", [])).lower()
    scored = []
    for card in load_techniques():
        score = 0
        matched = []
        for sig in card.get("signals", []):
            if sig.lower() in hay:
                score += 2
                matched.append(sig)
        # profile affinity: AI techniques for AI targets, etc.
        klass = card.get("klass", "")
        if klass in ("ai-llm",) and any(
                w in tech_terms for w in ("ai", "assistant", "llm", "prompt")):
            score += 3
        if klass in vuln_classes or any(
                w in vuln_classes for w in klass.split("-")):
            score += 1
        if score > 0:
            scored.append((score, card, matched))
    scored.sort(key=lambda x: -x[0])

    seeds = []
    for score, card, matched in scored[:limit * 2]:
        stmt = (f"[{card['id']}] {card.get('name')}: "
                f"{card.get('test', '')[:280]}")
        ok, _ = __import__("learn").is_novel(stmt, mem)
        if ok:
            seeds.append({"statement": stmt, "family": card.get("klass", "logic"),
                          "source": f"train:{card['id']}",
                          "score": score, "matched": matched,
                          "impact": card.get("impact_hint", "")})
        if len(seeds) >= limit:
            break
    return seeds


def technique_report():
    cards = load_techniques()
    klasses = {}
    for c in cards:
        klasses[c.get("klass", "?")] = klasses.get(c.get("klass", "?"), 0) + 1
    return f"{len(cards)} technique cards across {len(klasses)} classes: " + \
        ", ".join(f"{k}({v})" for k, v in sorted(klasses.items()))
