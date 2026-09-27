#!/usr/bin/env python3
"""DEEPHUNT learn + update — the LEARN + UPDATE stage (the loop-closer).

Every pipeline pass ends here, and NOTHING is a dead end. For each new
session result since the last pass:

  confirmed / supported
      -> world model: update_from_observation() + belief votes (REAL update)
      -> technique-card PROPOSAL written to knowledge/research/proposals/
         (status: pending-review — NEVER auto-merged into the generated
         techniques.yaml; a human or a validation run promotes it)
      -> world delta logged to state/<target>/world_deltas.jsonl
  rejected
      -> negative_check() first; if uncovered, append to
         knowledge/negative_examples.yaml (deduped) — failures become armor
      -> lesson already stored by the session; also indexed here
  inconclusive
      -> lesson appended to the session ("what would discriminate this")

Plus:
  - error-pattern consumer: when knowledge/error_patterns.yaml exists
    (built by the error-intel agent), new observations are scanned for
    matches and the suggested technique is attached as a follow-up note.
  - session.export_knowledge() merges facts/lessons/findings to knowledge.json.

Idempotent: processed result ids are tracked in
state/<target>/learned.json — a second pass never double-counts.
"""
from __future__ import annotations

import datetime
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

try:
    import yaml
    _HAVE_YAML = True
except ImportError:
    _HAVE_YAML = False

PROPOSALS_DIR = os.path.join(BASE, "knowledge", "research", "proposals")
NEGATIVE_PATH = os.path.join(BASE, "knowledge", "negative_examples.yaml")
ERROR_PATTERNS = os.path.join(BASE, "knowledge", "error_patterns.yaml")


def _learned_path(target):
    return os.path.join(BASE, "state", target, "learned.json")


def _load_learned(target):
    p = _learned_path(target)
    if os.path.isfile(p):
        try:
            return set(json.load(open(p)))
        except (OSError, ValueError):
            pass
    return set()


def _save_learned(target, done):
    p = _learned_path(target)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(sorted(done), open(p, "w"), indent=1)


def _new_results(session, done):
    return [r for r in session.state.get("results", [])
            if r.get("id") not in done]


def _log_delta(target, entry):
    p = os.path.join(BASE, "state", target, "world_deltas.jsonl")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    entry["ts"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with open(p, "a") as f:
        f.write(json.dumps(entry) + "\n")


def _beliefs_snapshot(world_model):
    return {k: v.get("confidence") for k, v in
            world_model.model.get("beliefs", {}).items()}


def _propose_card(target, result, session):
    """Write a technique-card proposal (pending review, never auto-merged)."""
    os.makedirs(PROPOSALS_DIR, exist_ok=True)
    hyp = next((h for h in session.state.get("hypotheses", [])
                if h["id"] == result.get("hypothesis_id")), {})
    card = {
        "id": f"PROP-{target.upper()}-{result.get('id', 'R?')}",
        "name": (hyp.get("statement", "") or result.get("observed", ""))[:120],
        "klass": "proposed",
        "status": "pending-review",
        "validated": False,
        "proposed_from": {"session": session.id,
                          "result": result.get("id"),
                          "hypothesis": result.get("hypothesis_id"),
                          "observed": (result.get("observed", "") or "")[:500]},
        "evidence": {"positive": ["observation_recorded"],
                     "negative": []},
        "questions": [f"Reproduce on demand: {result.get('observed','')[:160]}"],
        "note": "Auto-proposed by learn_updates. Promote only after independent "
                "reproduction + evidence contract validation.",
    }
    path = os.path.join(PROPOSALS_DIR, f"{card['id']}.yaml")
    if _HAVE_YAML:
        with open(path, "w") as f:
            yaml.safe_dump([card], f, default_flow_style=False,
                           allow_unicode=True)
    else:
        json.dump(card, open(path + ".json", "w"), indent=1)
        path += ".json"
    return path


def _append_negative_example(result):
    """Rejected results become negative examples (deduped by statement)."""
    if not _HAVE_YAML:
        return None
    try:
        existing = yaml.safe_load(open(NEGATIVE_PATH)) or []
    except (OSError, ValueError):
        existing = []
    stmt = (result.get("observed", "") or "")[:160]
    if any((e.get("observation", "") or "")[:160] == stmt for e in existing):
        return None
    existing.append({
        "observation": stmt,
        "match_signals": sorted({w for w in re.findall(r"[a-z0-9]+", stmt.lower())
                                 if len(w) > 3})[:6],
        "classification": "false_positive",
        "lesson": (f"Hypothesis {result.get('hypothesis_id')} rejected: "
                   f"{result.get('why_failed', '')[:200]} "
                   f"Learned: {result.get('learned', '')[:200]}"),
    })
    with open(NEGATIVE_PATH, "w") as f:
        yaml.safe_dump(existing, f, default_flow_style=False, allow_unicode=True)
    return NEGATIVE_PATH


def _error_intel_scan(session, texts):
    """Scan new observation texts against error_patterns.yaml (if present).

    Returns follow-up notes; never fails the pipeline when the file or
    pyyaml is missing (the error-intel agent may not have landed yet).
    """
    notes = []
    if not (_HAVE_YAML and os.path.isfile(ERROR_PATTERNS)):
        return notes
    try:
        patterns = yaml.safe_load(open(ERROR_PATTERNS)) or []
    except ValueError:
        return notes
    if isinstance(patterns, dict):
        patterns = patterns.get("patterns", [])
    for text in texts:
        for p in patterns:
            if not isinstance(p, dict):
                continue
            rx = p.get("pattern") or p.get("regex", "")
            try:
                if rx and re.search(rx, text, re.I):
                    notes.append(
                        f"error-intel: pattern '{p.get('name', rx)}' matched -> "
                        f"suggested technique: {p.get('technique', p.get('suggest', '?'))}")
                    break
            except re.error:
                continue
    return notes


def apply(session, world_model, target_name) -> dict:
    """Run the learn+update stage. Returns a summary dict."""
    done = _load_learned(target_name)
    results = _new_results(session, done)
    summary = {"processed": 0, "proposals": [], "negative_examples": 0,
               "belief_deltas": [], "error_notes": [], "lessons": 0}

    before = _beliefs_snapshot(world_model)
    new_texts = []

    for r in results:
        outcome = r.get("outcome")
        observed = r.get("observed", "") or ""
        new_texts.append(observed)
        if outcome == "confirmed":
            world_model.update_from_observation(observed, source="learn_updates")
            world_model._belief_vote(
                "Only the owner role may modify an owned object.",
                +1 if "unauthorized" not in observed.lower() else -1)
            path = _propose_card(target_name, r, session)
            summary["proposals"].append(path)
        elif outcome == "rejected":
            world_model.update_from_observation(observed, source="learn_updates")
            if _append_negative_example(r):
                summary["negative_examples"] += 1
        elif outcome == "inconclusive":
            lesson = {"ts": r.get("ts", ""),
                      "text": f"inconclusive {r.get('id')}: {observed[:160]} — "
                              f"needs a discriminating variant"}
            session.state.setdefault("lessons", []).append(lesson)
            summary["lessons"] += 1
        done.add(r.get("id"))
        summary["processed"] += 1

    world_model.recalculate_beliefs()
    world_model.save()
    after = _beliefs_snapshot(world_model)
    for k, v in after.items():
        if before.get(k) != v:
            delta = {"belief": k, "before": before.get(k), "after": v}
            summary["belief_deltas"].append(delta)
            _log_delta(target_name, delta)

    for note in _error_intel_scan(session, new_texts):
        session.observe(note, kind="error-intel")
        summary["error_notes"].append(note)

    if summary["processed"]:
        session._save()
        try:
            session.export_knowledge()
        except Exception:
            pass
    _save_learned(target_name, done)
    return summary
