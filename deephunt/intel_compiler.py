"""DEEPHUNT intel compiler — ATTACKSURFACE -> target-specific hypotheses.

The anti-pattern (report §25): dumping thousands of CVEs/articles into the
model. This compiler does the opposite:

  relevant intel only -> precondition extraction -> ranked hypotheses

Rules:
  - NEVER emit raw CVE dumps. KEV/NVD hits are summarized into preconditions
    ("wordpress < 6.4 observed -> precondition: fingerprint exact version,
    then test CVE-2024-XXXX class").
  - Every hypothesis carries preconditions, required state, and the intel
    items that justify it (provenance).
  - Bounded output: max_hypotheses cap, deduped.
"""
from __future__ import annotations

from typing import Dict, List, Optional

MAX_ITEMS = 40  # hard cap on intel items consulted per compile


def _summarize_kev(kev_hits: List[Dict]) -> List[Dict]:
    """Compress KEV hits into precondition-style intel chips."""
    chips = []
    for hit in kev_hits[:10]:
        cve = hit.get("cveID") or hit.get("cve", "?")
        vendor = hit.get("vendorProject", "")
        product = hit.get("product", "")
        chips.append({
            "kind": "kev",
            "title": f"KEV {cve} ({vendor} {product})".strip(),
            "precondition": f"target runs {product or vendor} at a vulnerable version",
            "next": "fingerprint exact version; only then test the vuln class",
            "provenance": "CISA KEV",
        })
    return chips


def _summarize_news(news: List[Dict]) -> List[Dict]:
    chips = []
    for n in news[:10]:
        chips.append({
            "kind": "news",
            "title": str(n.get("title", ""))[:120],
            "precondition": "target shares the named technology/pattern",
            "next": "check whether the target's stack matches; adapt the technique",
            "provenance": n.get("source", "news"),
        })
    return chips


def _technique_chips(cards: List[Dict], techs: List[str]) -> List[Dict]:
    """Match technique cards to observed technologies via their signals."""
    techblob = " ".join(techs).lower()
    chips = []
    for c in cards:
        sigs = [s.lower() for s in (c.get("signals") or [])]
        if any(s and s in techblob for s in sigs):
            chips.append({
                "kind": "technique",
                "title": c.get("name", c.get("id")),
                "technique_id": c.get("id"),
                "precondition": "; ".join(c.get("preconditions", c.get("requires", [])) or
                                          ["observe the surface first"]),
                "next": (c.get("hypothesis_generator") or c.get("test", ""))[:200],
                "oracle": c.get("positive_oracle", ""),
                "difficulty": c.get("difficulty_estimate", 0.5),
                "provenance": f"card {c.get('id')}",
            })
        if len(chips) >= MAX_ITEMS:
            break
    return chips


def compile(target: str, tech_knowledge: Dict, technologies: List[str],
            cards: Optional[List[Dict]] = None,
            max_hypotheses: int = 12) -> Dict:
    """Compile relevant intel into target-specific hypotheses."""
    chips: List[Dict] = []
    for tech, know in (tech_knowledge or {}).items():
        if not isinstance(know, dict):
            continue
        chips.extend(_summarize_kev(know.get("kev", []) or know.get("cves", [])))
        chips.extend(_summarize_news(know.get("news", [])))
    if cards:
        chips.extend(_technique_chips(cards, technologies))

    # dedupe by title
    seen, uniq = set(), []
    for ch in chips:
        if ch["title"] not in seen:
            seen.add(ch["title"])
            uniq.append(ch)

    hypotheses = []
    for ch in uniq[:max_hypotheses]:
        hypotheses.append({
            "statement": f"[{ch['kind']}] {ch['title']}",
            "preconditions": [ch["precondition"]],
            "required_state": [],
            "investigator_test": ch["next"],
            "oracle": ch.get("oracle", ""),
            "technique_id": ch.get("technique_id", ""),
            "source": "intel_compiler",
            "provenance": ch["provenance"],
            "difficulty_hint": ch.get("difficulty", 0.5),
            "status": "candidate",
        })
    return {"target": target,
            "intel_chips_considered": len(uniq),
            "intel_chips_dropped_as_noise": max(0, len(chips) - len(uniq)),
            "hypotheses": hypotheses,
            "note": "summarized, never dumped: KEV->preconditions, news->adaptations, "
                    "cards->matched techniques"}
