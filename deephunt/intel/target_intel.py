#!/usr/bin/env python3
"""DEEPHUNT target intelligence — the TARGET INTELLIGENCE stage.

One normalized model per target, built from every source we have:

  targets/<name>.yaml   profile (scope, bounty rules, hypothesis seeds)
  company dossier       workers output (domains, techstack, breach, news, people)
                        — consumed defensively; the company hunter may still be
                        building when this runs
  apiprobe results      OpenAPI/Swagger + GraphQL discovery output
  observations          free-text intel accumulated during the hunt
  state/<t>/target.json the persistent semantic model (target_model.Target)

TargetIntel EXTENDS target_model.Target (composition, never edits it):
everything the reasoning layer needs — technologies(), attack surface,
scope check, snapshot diff for suspicious-change detection — lives here.

Persisted: state/<target>/target_intel.json
"""
from __future__ import annotations

import copy
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.dirname(BASE))

from target_model import Target  # noqa: E402

STATE_DIR = os.path.join(BASE, "state")
TARGETS_DIR = os.path.join(BASE, "targets")


class TargetIntel:
    """Normalized intelligence for one target. Wraps Target; never replaces."""

    def __init__(self, name: str):
        self.name = name
        self.path = os.path.join(STATE_DIR, name, "target_intel.json")
        self.target = Target(name)  # the semantic model (persisted separately)
        self.intel = {"profile": {}, "dossier": {}, "apiprobe": {},
                      "tech_extra": [], "notes": []}
        self._load()

    # ---------- persistence ----------
    def _load(self):
        if os.path.isfile(self.path):
            try:
                saved = json.load(open(self.path))
                if isinstance(saved, dict):
                    self.intel.update(saved)
            except (OSError, ValueError):
                pass

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        tmp = self.path + ".tmp"
        json.dump(self.intel, open(tmp, "w"), indent=1)
        os.replace(tmp, self.path)
        self.target.save()

    # ---------- builders ----------
    @classmethod
    def from_profile(cls, profile: dict) -> "TargetIntel":
        """targets/<name>.yaml as loaded by orchestrator.load_profile()."""
        ti = cls(profile.get("name", "unknown"))
        ti.intel["profile"] = {k: v for k, v in profile.items()}
        hosts = profile.get("scope_hosts") or profile.get("scope") or []
        if isinstance(hosts, str):
            hosts = [hosts]
        for h in hosts:
            ti.target.add_asset(str(h).strip(), kind="scope",
                                notes="from target profile")
        for seed in profile.get("hypothesis_seeds", []) or []:
            ti.target.add_observation(f"seed: {seed}")
        for tech in profile.get("technologies", []) or []:
            ti.add_technology(str(tech), evidence="target profile")
        ti.save()
        return ti

    def merge_dossier(self, dossier: dict) -> int:
        """Fold a company-hunter dossier (workers output) into the model.

        Defensive: the company module is being built in parallel, so every
        access is a .get chain. Returns number of new facts absorbed.
        """
        if not isinstance(dossier, dict):
            return 0
        self.intel["dossier"] = {"company": dossier.get("company"),
                                 "domain": dossier.get("domain"),
                                 "generated": dossier.get("generated")}
        n = 0
        w = dossier.get("workers", {}) or {}

        def wdata(name):
            return (w.get(name, {}) or {}).get("data", {}) or {}

        dom = wdata("domains")
        for sub in dom.get("subdomains", []) or []:
            before = len(self.target.data["assets"])
            self.target.add_asset(sub, kind="subdomain", notes="company dossier")
            n += len(self.target.data["assets"]) - before
        for ip in dom.get("ips", []) or []:
            self.target.add_asset(ip, kind="ip", notes="company dossier")

        tech = wdata("techstack")
        for t in tech.get("detected", []) or []:
            self.add_technology(str(t), evidence="company techstack worker")
            n += 1
        for v in tech.get("versions", []) or []:
            self.target.add_observation(f"version: {v}")
            n += 1
        for tp in tech.get("third_party_hosts", []) or []:
            self.target.add_asset(tp, kind="third-party",
                                  notes="company techstack worker")

        br = wdata("breach_history")
        for b in br.get("records", []) or br.get("breaches", []) or []:
            txt = b if isinstance(b, str) else json.dumps(b)[:200]
            self.target.add_observation(f"breach-history: {txt}")
            n += 1

        nw = wdata("news")
        for item in (nw.get("items", []) or [])[:15]:
            title = item.get("title", "") if isinstance(item, dict) else str(item)
            if title:
                self.target.add_observation(f"news: {title[:160]}")
                n += 1

        emp = wdata("employees")
        for p in emp.get("profiles", []) or emp.get("people", []) or []:
            handle = p.get("handle") or p.get("login") or str(p)[:60]
            self.target.add_identity(handle, role="employee-public",
                                     owns=[])
            n += 1
        self.save()
        return n

    def merge_apiprobe(self, result: dict) -> int:
        """Fold apiprobe.py discovery output into endpoints + api_specs."""
        if not isinstance(result, dict):
            return 0
        self.intel["apiprobe"] = result
        n = 0
        for spec in result.get("specs", []) or []:
            url = spec.get("url", "")
            if url:
                self.target.data["api_specs"].append(
                    {"url": url, "kind": spec.get("kind", "openapi")})
                n += 1
        for ep in result.get("endpoints", []) or []:
            self.target.add_endpoint(ep.get("path", "/"),
                                     method=ep.get("method", "GET"),
                                     authentication=ep.get("auth", "unknown"),
                                     parameters=ep.get("params", []))
            n += 1
        for q in result.get("graphql", {}) or {}:
            if isinstance(q, dict) and q.get("introspection"):
                self.target.add_observation(
                    "graphql introspection enabled: full schema enumerable")
                n += 1
        self.save()
        return n

    def add_technology(self, name: str, evidence: str = ""):
        name = (name or "").strip()
        if not name:
            return
        have = {t["name"].lower() for t in self.target.data["technologies"]}
        if name.lower() not in have:
            self.target.data["technologies"].append(
                {"name": name, "evidence": evidence[:120]})
        if name.lower() not in {t.lower() for t in self.intel["tech_extra"]}:
            self.intel["tech_extra"].append(name)

    def add_observation(self, text: str):
        self.target.add_observation(text)

    # ---------- queries the reasoning layer uses ----------
    def technologies(self) -> list:
        techs = [t["name"] for t in self.target.data["technologies"]]
        return sorted(set(techs) | set(self.intel["tech_extra"]))

    def scope_hosts(self) -> list:
        hosts = [a["host"] for a in self.target.data["assets"]
                 if a.get("kind") == "scope"]
        if not hosts:
            hosts = [a["host"] for a in self.target.data["assets"]]
        # strip wildcards for direct use, keep the raw for matching
        return hosts

    def in_scope(self, host: str) -> bool:
        host = (host or "").lower().lstrip("*.")
        for s in self.scope_hosts():
            s = s.lower().lstrip("*.")
            if host == s or host.endswith("." + s):
                return True
        return False

    def attack_surface_summary(self) -> dict:
        d = self.target.data
        return {"assets": len(d["assets"]), "endpoints": len(d["endpoints"]),
                "technologies": self.technologies(),
                "workflows": len(d["workflows"]),
                "observations": len(d["observations"]),
                "authz_questions": self.target.authz_questions(limit=8)}

    def snapshot(self) -> dict:
        """Compact fingerprint for suspicious-change detection."""
        return {"assets": sorted(a["host"] for a in self.target.data["assets"]),
                "tech": sorted(self.technologies()),
                "endpoints": sorted(e["endpoint"] for e in self.target.data["endpoints"])}

    def diff_since(self, old: dict) -> dict:
        """What changed vs a previous snapshot — drives adaptive re-planning."""
        new = self.snapshot()
        old = old or {}
        def _diff(k):
            o, nn = set(old.get(k, [])), set(new.get(k, []))
            return {"added": sorted(nn - o), "removed": sorted(o - nn)}
        d = {k: _diff(k) for k in ("assets", "tech", "endpoints")}
        d["suspicious"] = bool(d["assets"]["added"] or d["tech"]["added"]
                               or d["endpoints"]["added"])
        return d

    def summary(self) -> str:
        s = self.attack_surface_summary()
        return (f"target_intel({self.name}): {s['assets']} assets, "
                f"{s['endpoints']} endpoints, tech=[{', '.join(s['technologies'][:6])}], "
                f"{s['observations']} observations")


def load_target_intel(name: str) -> TargetIntel:
    return TargetIntel(name)
