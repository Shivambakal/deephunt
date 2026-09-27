"""Attack planner: dossier -> ranked technique shortlist.

Maps what we learned about THIS company (tech stack, domain footprint, breach
history, news) onto DEEPHUNT's 129 technique cards and ranks by expected value:

  score = klass_weight
        + 2 * (# card signals matching dossier tokens)
        + impact bonus (from impact_hint)
        + news/breach situational boosts
        - negative-example penalty (card klass in negative klass list)

Output: ordered plan items, each with rationale, preconditions, the hypothesis
statement for the ResearchSession loop, and a controlled test sketch. The
planner never authorizes anything — it only proposes.

Re-ranking: when the adaptive loop reports suspicious changes, call
rerank(plan, changes) to boost items tied to the changed surface.
"""
from __future__ import annotations

import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
from kb import load_techniques  # noqa: E402

KLASS_WEIGHTS = {
    # empirically high-yield families first
    "authorization": 5, "authentication": 5, "api": 4, "business_logic": 4,
    "graphql": 4, "oauth": 4, "idor": 4, "saml": 3, "smuggling": 3,
    "cache": 3, "race": 3, "proto": 3, "ws": 3, "jwt": 3, "redirect": 2,
    "xss": 2, "sqli": 2, "ssrf": 3, "cloud": 3, "mobile": 2, "ai-llm": 2,
    "survey_2026": 2,
}
NEGATIVE_KLASSES = {"fp-noise", "expected-behaviour"}  # from negative examples

IMPACT_BONUS = {"critical": 4, "high": 3, "medium-high": 2.5, "medium": 2,
                "low-medium": 1, "low": 0.5}


def dossier_tokens(dossier: dict) -> set[str]:
    toks: set[str] = set()
    w = dossier.get("workers", {})
    tech = (w.get("techstack", {}).get("data", {}) or {})
    for t in tech.get("detected", []):
        toks.update(re.findall(r"[a-z0-9]+", t.lower()))
    toks.update(re.findall(r"[a-z0-9]+", " ".join(tech.get("third_party_hosts", [])).lower()))
    dom = (w.get("domains", {}).get("data", {}) or {})
    for s in dom.get("subdomains", []):
        toks.update(p for p in s.split(".") if p not in ("com", "net", "org", "io"))
    news = (w.get("news", {}).get("data", {}) or {})
    for it in news.get("items", [])[:10]:
        toks.update(re.findall(r"[a-z0-9]+", it.get("title", "").lower()))
    return {t for t in toks if len(t) > 2}


def impact_bonus(card: dict) -> float:
    hint = (card.get("impact_hint") or "").lower()
    for k, v in IMPACT_BONUS.items():
        if k in hint:
            return v
    return 1.0


def score_card(card: dict, tokens: set[str], situ: dict) -> tuple[float, list[str]]:
    reasons = []
    score = KLASS_WEIGHTS.get(card.get("klass", ""), 1.0)
    reasons.append(f"klass {card.get('klass')} base {score}")
    hits = [s for s in (card.get("signals") or [])
            if any(tok in s.lower() or s.lower() in tok for tok in tokens)]
    if hits:
        score += 2 * len(hits)
        reasons.append(f"signal hits: {', '.join(hits[:4])}")
    ib = impact_bonus(card)
    score += ib
    reasons.append(f"impact bonus {ib}")
    if card.get("klass") in NEGATIVE_KLASSES:
        score -= 5
        reasons.append("negative-example klass penalty")
    # situational boosts from news/breach history
    cats = situ.get("news_categories", {})
    if cats.get("acquisition") and card.get("klass") in ("api", "authorization", "cloud"):
        score += 2
        reasons.append("acquisition news: new/merged surface")
    if cats.get("launch") and card.get("klass") in ("api", "business_logic", "graphql"):
        score += 1.5
        reasons.append("recent launch: fresh endpoints")
    if cats.get("incident") and card.get("klass") in ("authentication", "authorization"):
        score += 1.5
        reasons.append("past incident: auth weaknesses plausible")
    if situ.get("breach_count") and card.get("klass") in ("authentication", "api"):
        score += 1
        reasons.append("breach history present")
    if situ.get("subdomain_count", 0) > 50 and card.get("klass") in ("api", "cloud"):
        score += 1
        reasons.append("large subdomain footprint")
    return round(score, 2), reasons


def hypothesis_for(card: dict, dossier: dict) -> str:
    target = dossier.get("company", "the target")
    return (f"{target}: {card['name']} — the dossier shows a matching surface "
            f"({card.get('klass')}); a controlled test with owned accounts/data "
            f"would distinguish vulnerable from hardened.")


def test_sketch(card: dict) -> str:
    t = (card.get("test") or "").strip().split("\n")[0]
    return t[:300] if t else "see card questions/followups"


def build_plan(dossier: dict, top_n: int = 15) -> list[dict]:
    tokens = dossier_tokens(dossier)
    w = dossier.get("workers", {})
    situ = {
        "news_categories": (w.get("news", {}).get("data", {}) or {}).get("category_counts", {}),
        "breach_count": (w.get("breach_history", {}).get("data", {}) or {}).get("breach_count", 0),
        "subdomain_count": (w.get("domains", {}).get("data", {}) or {}).get("subdomain_count", 0),
    }
    ranked = []
    for card in load_techniques():
        score, reasons = score_card(card, tokens, situ)
        ranked.append({
            "card_id": card["id"], "name": card["name"], "klass": card["klass"],
            "score": score, "reasons": reasons,
            "requires": card.get("requires", []),
            "hypothesis": hypothesis_for(card, dossier),
            "test_sketch": test_sketch(card),
            "impact_hint": card.get("impact_hint", ""),
        })
    ranked.sort(key=lambda r: r["score"], reverse=True)
    return ranked[:top_n]


def rerank(plan: list[dict], changes: dict) -> list[dict]:
    """Boost plan items tied to suspicious changes from the adaptive loop."""
    changed_text = " ".join(changes.get("items", [])).lower()
    tech_words = set(re.findall(r"[a-z][a-z0-9+]+", changed_text))
    out = []
    for item in plan:
        boost, why = 0.0, []
        hay = f"{item['name']} {item['klass']} {' '.join(item['reasons'])}".lower()
        if any(t in hay for t in tech_words if len(t) > 3):
            boost += 3
            why.append("tied to changed surface")
        if "new subdomain" in changed_text and item["klass"] in ("api", "cloud", "authorization"):
            boost += 2
            why.append("new subdomain: re-probe API/auth surface")
        out.append({**item, "score": round(item["score"] + boost, 2),
                    "rerank_boost": boost, "rerank_why": why})
    out.sort(key=lambda r: r["score"], reverse=True)
    return out
