"""DEEPHUNT error intelligence — every error is studied, not swallowed.

Ingests tool results (stderr text, exit codes, HTTP statuses, exception
strings) and:

  1. CLASSIFIES each error blob as benign / informative / unknown using
     knowledge/error_patterns.yaml.
  2. EXTRACTS intelligence from informative errors (WAF identity, server /
     framework versions, SQL dialect, internal paths) into structured
     findings for the world model.
  3. Creates STUDY task records for unknown errors (state/error_studies.jsonl)
     and searches the technique cards for anything matching, suggesting
     follow-ups the learning pipeline can research later.
  4. Never raises: a classifier failure must never break a hunt cycle.

Hook: orchestrator calls process_tool_result() after every tool run.
Research is read-only — this module never sends traffic.
"""
from __future__ import annotations
import json
import os
import re
import time

BASE = os.path.dirname(os.path.abspath(__file__))
PATTERNS_PATH = os.path.join(BASE, "knowledge", "error_patterns.yaml")
CARDS_PATH = os.path.join(BASE, "knowledge", "techniques.yaml")
STUDY_PATH = os.path.join(BASE, "state", "error_studies.jsonl")

MIN_STUDY_LEN = 40  # ignore trivially short unknown blobs


def _load_patterns():
    try:
        import yaml
        with open(PATTERNS_PATH, encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        out = []
        for p in data.get("patterns", []):
            try:
                p["_re"] = re.compile(p["regex"])
            except re.error:
                continue
            out.append(p)
        return out
    except Exception:  # noqa: BLE001
        return []


def _load_cards():
    try:
        import yaml
        with open(CARDS_PATH, encoding="utf-8") as fh:
            return yaml.safe_load(fh) or []
    except Exception:  # noqa: BLE001
        return []


_PATTERNS = None
_CARDS = None


def patterns():
    global _PATTERNS
    if _PATTERNS is None:
        _PATTERNS = _load_patterns()
    return _PATTERNS


def cards():
    global _CARDS
    if _CARDS is None:
        _CARDS = _load_cards()
    return _CARDS


def match_patterns(text: str):
    """Return list of matched pattern dicts (in file order)."""
    hits = []
    for p in patterns():
        try:
            if p["_re"].search(text or ""):
                hits.append(p)
        except Exception:  # noqa: BLE001
            continue
    return hits


def classify(text: str) -> str:
    """benign | informative | unknown. Informative wins over benign."""
    hits = match_patterns(text)
    cats = {h["category"] for h in hits}
    if "informative" in cats:
        return "informative"
    if "benign" in cats:
        return "benign"
    return "unknown"


def extract_intel(text: str):
    """Pull structured intel out of informative errors.

    Returns dict like {"waf": "Cloudflare", "server_header": "nginx/1.18.0",
    "internal_paths": [...], "sql_dialect": "MySQL", "framework_hint": ...}.
    """
    intel = {}
    hits = match_patterns(text)
    for h in hits:
        for k, v in (h.get("extract") or {}).items():
            intel.setdefault(k, v)
    # generic extractors, independent of patterns
    m = re.search(r"(?im)^Server:\s*([^\r\n]+)", text or "")
    if m:
        intel.setdefault("server_header", m.group(1).strip())
    m = re.search(r"(?im)^X-Powered-By:\s*([^\r\n]+)", text or "")
    if m:
        intel.setdefault("x_powered_by", m.group(1).strip())
    paths = sorted(set(re.findall(r"(/(?:var|etc|home|opt|usr|app|srv)[\w./-]*|"
                                  r"[A-Z]:\\[\w\\.-]+)", text or "")))[:8]
    if paths:
        intel.setdefault("internal_paths", paths)
    return intel


def _card_keywords(card):
    blob = " ".join(str(card.get(k, "")) for k in
                    ("id", "name", "klass", "signals", "questions", "followups"))
    return set(re.findall(r"[a-z0-9]{3,}", blob.lower()))


def search_cards(text: str, top_n: int = 3):
    """Rank technique cards by keyword overlap with the error text."""
    words = set(re.findall(r"[a-z0-9]{3,}", (text or "").lower()))
    if not words:
        return []
    scored = []
    for c in cards():
        kw = _card_keywords(c)
        overlap = words & kw
        if overlap:
            scored.append((len(overlap), c["id"], c.get("name", ""),
                           sorted(overlap)[:8]))
    scored.sort(reverse=True)
    return [{"card": cid, "name": name, "matched": m}
            for _, cid, name, m in scored[:top_n]]


def record_study(tool: str, text: str, context: str = ""):
    """Persist an unknown-error STUDY task for the learning pipeline."""
    rec = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tool": tool,
        "context": context[:200],
        "raw": (text or "")[:1500],
        "suggested_cards": search_cards(text),
        "status": "open",
    }
    try:
        os.makedirs(os.path.dirname(STUDY_PATH), exist_ok=True)
        with open(STUDY_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")
    except OSError:
        pass
    return rec


def process_tool_result(tool_name: str, findings: list, context: str = "") -> list:
    """Hook for the orchestrator: classify every error-ish finding.

    Returns EXTRA findings (never mutates the input list):
      - informative -> kind="error-intel" with extracted intel
      - unknown (substantial, kind=="error") -> kind="error-study" + STUDY record
      - benign -> silence (known noise)
    """
    extra = []
    try:
        for f in findings or []:
            if not isinstance(f, dict):
                continue
            text = " ".join(str(f.get(k, "")) for k in
                            ("title", "detail", "evidence"))
            if not text.strip():
                continue
            hits = match_patterns(text)
            cat = classify(text)
            if cat == "benign":
                continue
            if cat == "informative":
                intel = extract_intel(text)
                techs = sorted({h.get("technique") for h in hits
                                if h.get("technique")})
                extra.append({
                    "tool": "error_intel",
                    "phase": f.get("phase", ""),
                    "kind": "error-intel",
                    "title": f"error-intel: {hits[0]['meaning'][:90]}",
                    "detail": json.dumps(intel)[:1200] if intel else
                              f"source={tool_name} pattern={hits[0]['id']}",
                    "evidence": f"patterns={[h['id'] for h in hits]} "
                                f"techniques={techs} src={tool_name}:"
                                f"{f.get('title', '')[:80]}",
                    "severity_hint": "note",
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                })
            elif f.get("kind") == "error" and len(text.strip()) >= MIN_STUDY_LEN:
                rec = record_study(tool_name, text, context or f.get("title", ""))
                sug = [s["card"] for s in rec["suggested_cards"]]
                extra.append({
                    "tool": "error_intel",
                    "phase": f.get("phase", ""),
                    "kind": "error-study",
                    "title": f"error-study: unknown error from {tool_name} queued",
                    "detail": f"STUDY task recorded ({STUDY_PATH}). "
                              f"Suggested cards: {sug or 'none matched'}",
                    "evidence": text[:600],
                    "severity_hint": "info",
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                })
    except Exception:  # noqa: BLE001
        return []
    return extra
