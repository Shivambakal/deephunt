#!/usr/bin/env python3
"""DEEPHUNT hypothesis engine — the HYPOTHESIS ENGINE stage.

Fuses every hypothesis source into ONE ranked, deduplicated list and
registers them in the ResearchSession (where the adversarial self-check
and gate live — this module never bypasses them):

  1. brain hypotheses.generate() — violation-template hypotheses from the
     session's world model (attacker/defender/devil views included)
  2. company attack-planner items — technique cards ranked for THIS target
  3. reasoning seeds — intel-derived (inference, KEV, authz matrix)
  4. attack-graph path seeds — chains that cross trust boundaries

Dedup: exact-statement match against live session hypotheses, then
learn.is_novel() against the rejection memory (retreads die here, with
the reason recorded). Survivors are registered via session.add_hypothesis()
with provenance in the investigator_test field.
"""
from __future__ import annotations

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.dirname(BASE))

import learn  # noqa: E402


def _brain_hypotheses(session, mem):
    """Violation-template hypotheses from the session's world model."""
    out = []
    try:
        from brain import hypotheses as H
        wm = session._world_model()
        for h in H.rank(H.generate(wm))[:12]:
            novel, _ = learn.is_novel(h.statement, mem)
            if novel:
                out.append({"statement": h.statement,
                            "violated_assumption": h.violated_assumption,
                            "attacker_view": h.attacker_view,
                            "devil_view": h.devil_view,
                            "investigator_test": h.investigator_test,
                            "impact": h.impact, "novelty": h.novelty,
                            "testability": h.testability,
                            "source": "brain-templates",
                            "score": h.score,
                            "provenance": f"violated: {h.violated_assumption}"})
    except Exception as e:
        out.append({"statement": f"brain hypothesis generation failed: {e}",
                    "source": "error", "score": 0, "provenance": ""})
    return out


def fuse(session, seed_hypotheses, plan_items, attackgraph_seeds,
         mem, max_new: int = 14) -> dict:
    """Merge all sources, dedupe, register survivors in the session."""
    candidates = []

    # reasoning seeds (already scored)
    for s in seed_hypotheses:
        candidates.append({**s, "investigator_test": s.get("provenance", "")})

    # attack-graph path seeds
    for s in attackgraph_seeds:
        candidates.append({**s, "investigator_test": s.get("provenance", "")})

    # company attack plan -> hypotheses
    for item in plan_items or []:
        stmt = item.get("hypothesis", "")
        if not stmt:
            continue
        candidates.append({
            "statement": stmt,
            "source": "attack-planner",
            "score": item.get("score", 3),
            "investigator_test": item.get("test_sketch", "")[:300],
            "impact": 4,
            "provenance": f"card {item.get('card_id')} "
                          f"({item.get('klass')}): "
                          f"{'; '.join(item.get('reasons', [])[:2])}",
        })

    # brain violation templates
    candidates.extend(_brain_hypotheses(session, mem))

    # sort: score desc, then dedupe
    candidates.sort(key=lambda c: -c.get("score", 0))
    live_stmts = {h["statement"] for h in session.state["hypotheses"]
                  if h["status"] == "live"}
    registered, skipped = [], []
    for c in candidates:
        stmt = c.get("statement", "")
        if not stmt or stmt in live_stmts:
            skipped.append({"statement": stmt[:80], "reason": "duplicate-live"})
            continue
        novel, retread = learn.is_novel(stmt, mem)
        if not novel:
            skipped.append({"statement": stmt[:80],
                            "reason": f"retread of rejected: "
                                      f"{retread.get('statement','')[:60]}"})
            continue
        rec = session.add_hypothesis(
            statement=stmt,
            violated_assumption=c.get("violated_assumption", ""),
            attacker_view=c.get("attacker_view", ""),
            devil_view=c.get("devil_view", ""),
            investigator_test=f"[{c.get('source')}] {c.get('investigator_test','')[:240]}",
            impact=c.get("impact", 3), novelty=c.get("novelty", 3),
            testability=c.get("testability", 3),
            provenance=c.get("provenance", c.get("source", "")))
        registered.append(rec["id"])
        live_stmts.add(stmt)
        if len(registered) >= max_new:
            break

    return {"registered": registered, "skipped": skipped,
            "candidates": len(candidates)}
