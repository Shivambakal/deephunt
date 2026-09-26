"""DEEPHUNT learn — the loop's memory. Reads every past log and turns
mistakes into armor: rejected hypotheses are never retried, tried paths are
known, lessons steer the next cycle."""
from __future__ import annotations
import glob
import json
import os
import re

BASE = os.path.expanduser("~/workspace/hacker-agent")
SESSIONS = os.path.join(BASE, "data", "brain", "sessions")
INTEL = os.path.join(BASE, "intel")
PROXY_LOGS = os.path.join(BASE, "proxy", "logs")

STOPWORDS = set("the a an and or of to in on for with is are was were be by as "
                "at from that this it its they their we you your our not can".split())


def _words(text):
    return [w for w in re.findall(r"[a-z0-9]+", (text or "").lower())
            if w not in STOPWORDS and len(w) > 3]


def _overlap(a, b, minimum=3):
    return len(set(_words(a)) & set(_words(b))) >= minimum


def load_memory(target=""):
    """Collect everything past runs learned. Returns dict."""
    mem = {"rejected": [], "confirmed": [], "lessons": [],
           "tried_paths": set(), "sessions": 0, "intel_files": []}

    for path in glob.glob(os.path.join(SESSIONS, "*.json")):
        try:
            s = json.load(open(path))
        except (OSError, json.JSONDecodeError):
            continue
        if target and target.lower() not in json.dumps(s)[:4000].lower():
            # still count global lessons, but skip target-specific rejects
            pass
        mem["sessions"] += 1
        for r in s.get("rejected_hypotheses", []):
            if not target or _overlap(target, r.get("statement", ""), 1):
                mem["rejected"].append({
                    "statement": r.get("statement", ""),
                    "why_failed": r.get("why_failed", ""),
                    "learned": r.get("learned", "")})
        for c in s.get("confirmed_findings", []):
            mem["confirmed"].append(c if isinstance(c, str)
                                    else c.get("statement", str(c)))
        for l in s.get("lessons", []):
            mem["lessons"].append(l if isinstance(l, str) else str(l))

    for path in glob.glob(os.path.join(INTEL, "*-novel-attacks.md")):
        mem["intel_files"].append(os.path.basename(path))
    for path in glob.glob(os.path.join(INTEL, "*-endpoint-funnel.md")):
        mem["intel_files"].append(os.path.basename(path))

    for log in glob.glob(os.path.join(PROXY_LOGS, "*", "traffic.jsonl")):
        try:
            with open(log) as f:
                for line in f:
                    try:
                        d = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    url = d.get("url", "")
                    m = re.match(r"https?://[^/]+(/[^? ]*)", url)
                    if m:
                        mem["tried_paths"].add(m.group(1).split("?")[0])
        except OSError:
            continue

    mem["tried_paths"] = sorted(mem["tried_paths"])
    return mem


def is_novel(statement, mem):
    """True if this hypothesis isn't a retread of a past rejection."""
    for r in mem["rejected"]:
        if _overlap(statement, r["statement"]):
            return False, r
    return True, None


def mistakes_report(mem, limit=15):
    lines = [f"# DEEPHUNT memory — {mem['sessions']} sessions, "
             f"{len(mem['rejected'])} rejected hypotheses, "
             f"{len(mem['tried_paths'])} tried paths"]
    lines.append("\n## DO NOT RETRY (rejected with evidence)")
    for r in mem["rejected"][:limit]:
        lines.append(f"- {r['statement'][:160]}")
        if r["why_failed"]:
            lines.append(f"  why: {r['why_failed'][:160]}")
        if r["learned"]:
            lines.append(f"  learned: {r['learned'][:160]}")
    if mem["lessons"]:
        lines.append("\n## LESSONS")
        for l in mem["lessons"][:10]:
            lines.append(f"- {str(l)[:200]}")
    if mem["confirmed"]:
        lines.append("\n## CONFIRMED BEFORE (don't re-prove, extend)")
        for c in mem["confirmed"][:10]:
            lines.append(f"- {str(c)[:200]}")
    return "\n".join(lines)
