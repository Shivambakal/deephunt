#!/usr/bin/env python3
"""DEEPHUNT reasoning stage — intel -> assumptions + seed hypotheses.

The architecture diagram shows a "DEEPHUNT REASONING" box between intel and
the world model. This module IS that box, as code rather than a pass-through:

  IntelBundle (global intel slice + target intel)
      -> assumptions: what we believe about this target and how we'd know
                      we're wrong (believes / enforcement / violated_if)
      -> seed hypotheses: first questions worth testing, each traceable to
                      the intel that produced it
      -> open questions: what we still don't know (drives recon priority)

Sources of seeds, in order:
  1. inference.infer() over intel-derived findings (invariant questions)
  2. global intel: KEV CVEs / recent CVEs touching the target's tech stack
  3. dossier/news signals: surface-changing events -> targeted questions
  4. target model authz questions (unauthenticated object access etc.)

Every seed carries `provenance` so a hypothesis can always answer
"why did you think of that?"
"""
from __future__ import annotations

import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import inference  # noqa: E402


def _assumption_from_tech(tech: str, known: dict) -> dict | None:
    """A KEV-listed CVE for this tech -> an assumption to test."""
    kev = known.get("kev", [])
    if not kev:
        return None
    return {
        "believes": f"{tech} deployment is patched against known-exploited CVEs",
        "enforcement": "patch management / version pinning",
        "violated_if": f"target runs a {tech} version affected by {', '.join(kev[:3])}",
        "confidence": 0.4,
        "provenance": f"cisa-kev: {', '.join(kev[:3])}",
    }


def seed_from_intel(target_name: str, tech_knowledge: dict,
                    target_intel, mem: dict | None = None) -> dict:
    """Build the reasoning output for one target.

    target_name: str
    tech_knowledge: {tech: what_is_known(tech)} from global_intel
    target_intel: TargetIntel
    mem: learn.load_memory() output (may be empty dict)
    """
    mem = mem or {}
    assumptions, seeds, questions = [], [], []

    # --- 1. inference engine over intel-derived findings ---
    findings = []
    for t in target_intel.technologies():
        findings.append({"tool": "target_intel", "title": t,
                         "detail": f"technology {t} detected on {target_name}"})
    for obs in target_intel.target.data["observations"][-20:]:
        findings.append({"tool": "target_intel", "title": "observation",
                         "detail": obs})
    profile = {"name": target_name,
               "scope_hosts": target_intel.scope_hosts()}
    try:
        for s in inference.infer(findings, profile, mem)[:10]:
            seeds.append({"statement": s["statement"], "source": "inference",
                          "score": s.get("score", 3),
                          "provenance": s.get("reasoning", "")[:200]})
    except Exception as e:  # inference must never kill the pipeline
        questions.append(f"inference engine failed ({e}); manual seeding needed")

    # --- 2. global intel -> assumptions + CVE-driven seeds ---
    for tech, known in tech_knowledge.items():
        a = _assumption_from_tech(tech, known)
        if a:
            assumptions.append(a)
            for cve in known.get("kev", [])[:2]:
                seeds.append({
                    "statement": f"[{target_name}] {tech} is exposed to {cve} "
                                 f"(CISA KEV): verify running version and exploitability "
                                 f"with owned test data only.",
                    "source": "global-intel", "score": 5,
                    "provenance": f"cisa-kev {cve} affects {tech}"})
        for cve in known.get("cves", [])[:3]:
            if cve.get("severity") in ("CRITICAL", "HIGH") and not known.get("kev"):
                seeds.append({
                    "statement": f"[{target_name}] recent {cve['severity']} {cve['id']} "
                                 f"affects {tech}: check if the target's {tech} "
                                 f"deployment is in the affected range.",
                    "source": "global-intel", "score": 4,
                    "provenance": f"nvd {cve['id']}"})
        for klass in known.get("technique_klasses", [])[:4]:
            seeds.append({
                "statement": f"[{target_name}] {tech} has known {klass} weakness "
                             f"history (CWE-mapped): probe {klass} on {tech}-served "
                             f"surface with owned accounts.",
                "source": "global-intel", "score": 3,
                "provenance": f"cwe->klass {klass} for {tech}"})

    # --- 3. news / dossier signals -> surface-change questions ---
    for obs in target_intel.target.data["observations"]:
        if obs.startswith("news:") and len(questions) < 8:
            questions.append(f"surface change? {obs[5:].strip()[:140]}")

    # --- 4. target model authz questions become seeds ---
    for q in target_intel.target.authz_questions(limit=6):
        seeds.append({"statement": f"[{target_name}] {q}",
                      "source": "target-model", "score": 4,
                      "provenance": "authz matrix cell flagged 'test'"})

    # --- baseline assumptions every target gets ---
    assumptions.extend([
        {"believes": "authentication is enforced on every non-public endpoint",
         "enforcement": "server-side session/token checks",
         "violated_if": "an endpoint returns non-public data without credentials",
         "confidence": 0.6, "provenance": "baseline"},
        {"believes": "object access requires ownership or explicit grant",
         "enforcement": "authorization checks per object",
         "violated_if": "cross-identity read/write succeeds on an owned object",
         "confidence": 0.6, "provenance": "baseline"},
    ])

    # dedupe seeds by statement
    seen, uniq = set(), []
    for s in seeds:
        if s["statement"] not in seen:
            seen.add(s["statement"])
            uniq.append(s)
    return {"assumptions": assumptions, "seed_hypotheses": uniq,
            "open_questions": questions}
