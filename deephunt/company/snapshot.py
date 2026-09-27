"""Adaptive loop: snapshot diffing for suspicious-change detection.

After every observation phase the orchestrator snapshots the dossier's
volatile parts (subdomains, tech stack, certs, DNS). On the next run the new
snapshot is diffed against the previous one. Any change — new subdomain, new
tech, new cert, DNS move, new typo-squat going live — is a 'suspicious change'
that triggers attack-plan re-ranking and follow-up tasks.

Snapshots live in deephunt/state/company/<slug>/snapshots/<ts>.json.
"""
from __future__ import annotations

import glob
import json
import os
from datetime import datetime, timezone

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def slugify(name: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")


def state_dir(slug: str) -> str:
    d = os.path.join(BASE, "state", "company", slug)
    os.makedirs(os.path.join(d, "snapshots"), exist_ok=True)
    return d


def extract_snapshot(dossier: dict) -> dict:
    dom = (dossier.get("workers", {}).get("domains", {}).get("data", {}) or {})
    tech = (dossier.get("workers", {}).get("techstack", {}).get("data", {}) or {})
    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "subdomains": sorted(dom.get("subdomains", [])),
        "resolved_ips": sorted(dom.get("resolved_ips", [])),
        "dns_mx": sorted((dom.get("dns", {}) or {}).get("MX", [])),
        "tech_detected": sorted(tech.get("detected", [])),
        "tech_versions": tech.get("versions", {}),
        "third_party_hosts": sorted(tech.get("third_party_hosts", [])),
        "recent_cert_count": dom.get("certificates_observed", 0),
        "live_typos": sorted(t["domain"] for t in dom.get("live_typo_candidates", [])),
    }


def save_snapshot(slug: str, dossier: dict) -> str:
    snap = extract_snapshot(dossier)
    path = os.path.join(state_dir(slug), "snapshots",
                        snap["ts"].replace(":", "-") + ".json")
    with open(path, "w") as f:
        json.dump(snap, f, indent=1)
    return path


def _load_latest(slug: str) -> dict | None:
    files = sorted(glob.glob(os.path.join(state_dir(slug), "snapshots", "*.json")))
    # the file we just saved is newest; we want the one before it
    if len(files) < 2:
        return None
    with open(files[-2]) as f:
        return json.load(f)


def _diff_list(old: list, new: list) -> dict:
    o, n = set(old or []), set(new or [])
    return {"added": sorted(n - o), "removed": sorted(o - n)}


def diff_snapshots(slug: str, current: dict) -> dict:
    """Diff current snapshot against the previous run. Returns changes + verdict."""
    prev = _load_latest(slug)
    changes: dict = {"has_previous": prev is not None, "items": [],
                     "suspicious": False}
    if not prev:
        changes["items"].append("first snapshot — baseline established")
        return changes
    checks = [
        ("subdomains", "subdomain"),
        ("resolved_ips", "resolved IP"),
        ("tech_detected", "detected technology"),
        ("third_party_hosts", "third-party host"),
        ("live_typos", "live typo-squat candidate"),
        ("dns_mx", "MX record"),
    ]
    for key, label in checks:
        d = _diff_list(prev.get(key), current.get(key))
        for x in d["added"]:
            changes["items"].append(f"NEW {label}: {x}")
        for x in d["removed"]:
            changes["items"].append(f"REMOVED {label}: {x}")
    old_v, new_v = prev.get("tech_versions", {}), current.get("tech_versions", {})
    for tech, ver in new_v.items():
        if old_v.get(tech) != ver:
            changes["items"].append(
                f"VERSION CHANGE {tech}: {old_v.get(tech, '?')} -> {ver}")
    if current.get("recent_cert_count", 0) > prev.get("recent_cert_count", 0):
        changes["items"].append("new certificates issued since last run")
    changes["suspicious"] = any(
        i.startswith(("NEW", "VERSION CHANGE")) for i in changes["items"])
    return changes


def followups_for_changes(changes: dict) -> list[str]:
    """Turn suspicious changes into concrete follow-up tasks."""
    out = []
    for item in changes.get("items", []):
        if item.startswith("NEW subdomain:"):
            sub = item.split("NEW subdomain:")[1].strip()
            out.append(f"fingerprint {sub} (tech stack, headers, public files)")
            out.append(f"check {sub} against typo/candidates and cert history")
        elif item.startswith("NEW detected technology:"):
            tech = item.split("NEW detected technology:")[1].strip()
            out.append(f"re-rank attack plan for new tech: {tech}")
        elif item.startswith("VERSION CHANGE"):
            out.append(f"review {item} for known CVEs in the new version")
        elif item.startswith("NEW live typo-squat"):
            out.append(f"assess {item} — possible phishing infrastructure")
        elif item.startswith("NEW resolved IP:"):
            out.append(f"verify ASN/org still matches expected hosting for {item}")
    return out
