"""DEEPHUNT knowledge-base loader — single entry point for the enriched
technique cards in knowledge/techniques/*.yaml plus the negative-example
gate used BEFORE any finding is promoted.

Usage:
    from kb import load_techniques, get_card, cards_by_klass, negative_check
"""
from __future__ import annotations
import glob
import os
import yaml

BASE = os.path.dirname(os.path.abspath(__file__))
TECH_DIR = os.path.join(BASE, "knowledge", "techniques")
NEG_PATH = os.path.join(BASE, "knowledge", "negative_examples.yaml")

_cache = None
_neg_cache = None

REQUIRED_FIELDS = ("id", "name", "klass", "requires", "signals",
                   "questions", "evidence", "followups", "test", "impact_hint")


def load_techniques():
    """Load every enriched card from knowledge/techniques/*.yaml (cached)."""
    global _cache
    if _cache is not None:
        return _cache
    cards = []
    for path in sorted(glob.glob(os.path.join(TECH_DIR, "*.yaml"))):
        try:
            docs = yaml.safe_load(open(path)) or []
        except (OSError, yaml.YAMLError):
            continue
        for c in docs:
            if not isinstance(c, dict) or "id" not in c:
                continue
            # normalize: guarantee enriched shape even for hand-added cards
            c.setdefault("requires", [])
            c.setdefault("signals", [])
            c.setdefault("questions", [])
            ev = c.get("evidence") or {}
            c["evidence"] = {"positive": list(ev.get("positive", [])),
                             "negative": list(ev.get("negative", []))}
            c.setdefault("followups", [])
            c.setdefault("test", "")
            c.setdefault("impact_hint", "")
            cards.append(c)
    _cache = cards
    return cards


def reload_techniques():
    global _cache
    _cache = None
    return load_techniques()


def get_card(card_id):
    for c in load_techniques():
        if c.get("id") == card_id:
            return c
    return None


def cards_by_klass(klass):
    return [c for c in load_techniques() if c.get("klass") == klass]


def card_ids():
    return [c.get("id") for c in load_techniques()]


def validate_cards():
    """Return (ok, problems): every card unique + enriched."""
    problems = []
    seen = set()
    for c in load_techniques():
        cid = c.get("id")
        if cid in seen:
            problems.append(f"duplicate id: {cid}")
        seen.add(cid)
        for f in REQUIRED_FIELDS:
            if f not in c or c[f] in (None, "", []):
                # impact_hint/test may legitimately be short; flag truly missing
                if f in ("requires", "questions", "followups", "signals"):
                    problems.append(f"{cid}: empty {f}")
        ev = c.get("evidence", {})
        if not ev.get("positive") or not ev.get("negative"):
            problems.append(f"{cid}: evidence missing positive/negative")
    return (not problems), problems


# ---------------- negative-example gate ----------------

def _load_negative():
    global _neg_cache
    if _neg_cache is not None:
        return _neg_cache
    try:
        _neg_cache = yaml.safe_load(open(NEG_PATH)) or []
    except (OSError, yaml.YAMLError):
        _neg_cache = []
    return _neg_cache


def negative_check(observation):
    """Consult negative examples BEFORE promoting an observation to a finding.

    observation: free text (or dict with an 'observation'/'interpretation' key).
    Returns the matching negative entry dict, or None if no negative matches.
    A match means: do NOT promote on this evidence alone — see 'lesson'.
    """
    if isinstance(observation, dict):
        text = " ".join(str(observation.get(k, "")) for k in
                         ("observation", "interpretation", "detail", "title"))
    else:
        text = str(observation or "")
    low = text.lower()
    best, best_hits = None, 0
    for entry in _load_negative():
        signals = entry.get("match_signals") or []
        hits = sum(1 for s in signals if s.lower() in low)
        # require >=2 signal hits: a single shared word (e.g. "user") must
        # not suppress a real finding. Precision over recall for this gate.
        if hits >= 2 and hits > best_hits:
            best, best_hits = entry, hits
    return best
