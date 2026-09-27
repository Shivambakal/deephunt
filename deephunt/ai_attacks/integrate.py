"""DEEPHUNT ai_attacks integration — hypothesis seeds + experiment expansion.

This module bridges the ai_attacks planners into the ATTACKSURFACE pipeline:
  - detect_ai_surfaces(ti): find AI/LLM surfaces from target intel (technologies,
    observations, dossier text). Target-agnostic.
  - seed_hypotheses(target, ti): produce hypothesis seeds in the exact shape
    hypothesis_fusion.fuse() expects (statement/source/score/...
    provenance). Pure data — no transmission.
  - expand_tests(hypothesis, surface): turn one AI hypothesis into concrete
    test-case dicts for the experiment planner. Pure data — the pipeline still
    routes every test through propose_test() -> TestAuthorization ->
    Engine.execute().
  - score_observation(probe, response_text): scorer.classify wrapper whose
    evidence_artifacts feed evidence.py contracts.

Nothing here transmits. Mocks exist only in tests.
"""
from __future__ import annotations

import re
from typing import Dict, List

from . import prompt_injection as pi
from . import jailbreak as jb
from . import scorer
from . import rag_poison as rp
from . import agent_abuse as aa
from . import extraction as ex

# Signals that a target exposes an AI/LLM surface. Matched (case-insensitive)
# against technology names and observation/dossier text.
AI_SIGNALS = [
    "llm", "gpt", "openai", "anthropic", "claude", "gemini", "llama",
    "chatbot", "copilot", "assistant", "rag", "langchain", "llamaindex",
    "agent", "mcp", "huggingface", "dialogflow", "rasa", "watsonx",
    "mistral", "cohere", "bedrock", "vertex ai", "azure openai",
    "semantic kernel", "autogen", "crewai",
]

_KIND_HINTS = [
    (("rag", "retrieval", "knowledge base", "vector", "embedding"), "rag"),
    (("agent", "tool", "mcp", "function calling", "autonomous"), "agent"),
]


def detect_ai_surfaces(ti) -> List[dict]:
    """Infer AI surfaces from a TargetIntel-like object. Returns surface dicts
    shaped for the planner modules: {"kind", "name", "input_fields", "signals"}.
    """
    texts: List[str] = []
    try:
        texts.extend(ti.technologies())
    except Exception:
        pass
    try:
        texts.extend(str(o) for o in (ti.target.data.get("observations") or [])[-40:])
    except Exception:
        pass
    blob = " ".join(texts).lower()
    hits = sorted({s for s in AI_SIGNALS if s in blob})
    if not hits:
        return []
    kind = "chatbot"
    for hints, k in _KIND_HINTS:
        if any(h in blob for h in hints):
            kind = k
            break
    target_name = getattr(getattr(ti, "target", None), "name", None) or "target"
    return [{
        "kind": kind,
        "name": f"{target_name} AI surface",
        "input_fields": ["user_message"],
        "signals": hits,
    }]


def _seed(statement: str, source: str, score: float, provenance: str,
          investigator_test: str, violated: str = "",
          impact: int = 4, novelty: int = 4) -> dict:
    return {
        "statement": statement,
        "source": source,
        "score": score,
        "investigator_test": investigator_test[:300],
        "violated_assumption": violated,
        "attacker_view": "",
        "devil_view": "",
        "impact": impact,
        "novelty": novelty,
        "provenance": provenance,
    }


def seed_hypotheses(target: str, ti) -> List[dict]:
    """Generate AI-attack hypothesis seeds for the pipeline. Pure data."""
    surfaces = detect_ai_surfaces(ti)
    if not surfaces:
        return []
    seeds: List[dict] = []
    for s in surfaces:
        kind, sigs = s["kind"], ", ".join(s["signals"][:6])
        base = f"[{target}] AI surface ({kind}; signals: {sigs})"
        cases = pi.generate(s)
        n = cases.get("count", 0)
        seeds.append(_seed(
            f"{base}: prompt injection possible — {n} probe cases generated "
            f"(direct/indirect/multi-turn/delimiter)",
            "ai_attacks:prompt_injection", 4.0,
            f"ai_attacks seed; {n} cases; cards AI-01/AI-04/AI-08/AI-13",
            f"Run injection battery ({n} cases) through authorized proposals; "
            f"vulnerable if canary markers echoed or instructions overridden.",
            violated="user input is treated as data, never as instructions"))
        jb_battery = jb.battery("BENIGN_TEST_GOAL", s)
        seeds.append(_seed(
            f"{base}: jailbreak resistance unknown — "
            f"{len(jb_battery)} jailbreak techniques available",
            "ai_attacks:jailbreak", 3.5,
            "ai_attacks seed; techniques.yaml JB-01..JB-13; card AI-14",
            "Propose jailbreak battery with synthetic goals; vulnerable if "
            "model complies with disallowed-style synthetic task.",
            violated="safety alignment cannot be bypassed by framing"))
        if kind == "rag":
            seeds.append(_seed(
                f"{base}: RAG pipeline may retrieve poisoned content — "
                f"{len(rp.poisoned_document_patterns())} carrier patterns",
                "ai_attacks:rag_poison", 4.0,
                "ai_attacks seed; cards AI-06/AI-15; LLM04/LLM08",
                "Propose poisoned-document plant + trigger queries in an "
                "authorized test corpus; vulnerable if injected instructions "
                "are followed.",
                violated="retrieved documents are trusted content"))
        if kind == "agent":
            seeds.append(_seed(
                f"{base}: agent may hold excessive tool agency "
                f"(tool-permission mapping + escalation paths)",
                "ai_attacks:agent_abuse", 4.0,
                "ai_attacks seed; card AI-16; LLM06",
                "Map declared tools, propose escalation-path and "
                "approval-bypass tests; vulnerable if irreversible actions "
                "execute without confirmation.",
                violated="agent acts only within least-privilege tools"))
        seeds.append(_seed(
            f"{base}: system prompt / training data extraction untested — "
            f"{len(ex.system_prompt_extraction_battery())} extraction probes",
            "ai_attacks:extraction", 3.0,
            "ai_attacks seed; cards AI-09/AI-10; LLM02/LLM07",
            "Propose extraction battery (synthetic canary prompts only); "
            "vulnerable if system instructions or canary data leak. NOTE: many "
            "programs exclude this class — confirm scope first.",
            violated="system instructions are not disclosable"))
    return seeds


def expand_tests(hypothesis: dict, surface: dict) -> List[dict]:
    """Expand one AI hypothesis into concrete test-case dicts for the
    experiment planner. Each case is proposal data for propose_test()."""
    src = (hypothesis.get("source") or "")
    stmt = hypothesis.get("statement") or ""
    cases: List[dict] = []
    low = (src + " " + stmt).lower()
    if "prompt_injection" in low or "prompt injection" in low:
        for c in pi.generate(surface).get("cases", []):
            cases.append(_case_from_probe(c, hypothesis))
    if "jailbreak" in low:
        for c in jb.battery("SYNTHETIC_BENIGN_GOAL", surface):
            cases.append(_case_from_probe(c, hypothesis))
    if "rag_poison" in low or "rag" in low and "poison" in low:
        plan = rp.plan_rag_test({
            "retrieval": "hybrid",
            "doc_types": ["markdown", "faq"],
            "query_examples": ["how do I reset my password?"],
        })
        for q in plan.get("trigger_queries", [])[:5]:
            cases.append({
                "id": f"rag-{len(cases)}",
                "action": "send",
                "input_text": q,
                "expected_vulnerable": plan.get("expected_vulnerable", ""),
                "expected_safe": plan.get("expected_safe", ""),
                "scoring": plan.get("scoring_rule", ""),
                "hypothesis_id": hypothesis.get("id"),
                "technique_card": "AI-06",
            })
    if "agent_abuse" in low or "agency" in low:
        for t in aa.approval_bypass_tests(
                aa.map_tool_permissions([])):
            cases.append(_case_from_probe(t, hypothesis))
    if "extraction" in low:
        for c in ex.system_prompt_extraction_battery():
            cases.append(_case_from_probe(c, hypothesis))
    return cases[:25]


def _case_from_probe(probe: dict, hypothesis: dict) -> dict:
    return {
        "id": probe.get("id", "probe"),
        "action": "send",
        "input_text": probe.get("input_text") or probe.get("probe_text", ""),
        "turns": probe.get("turns"),
        "expected_vulnerable": probe.get("expected_vulnerable", ""),
        "expected_safe": probe.get("expected_safe", ""),
        "success_markers": probe.get("success_markers", []),
        "forbidden_pattern": probe.get("forbidden_pattern"),
        "leak_markers": probe.get("leak_markers", []),
        "hypothesis_id": hypothesis.get("id"),
        "technique_card": probe.get("technique_card", ""),
        "owasp": probe.get("owasp", ""),
    }


def score_observation(probe: dict, response_text: str) -> dict:
    """Classify one AI-attack observation; evidence_artifacts are
    evidence.py-contract compatible."""
    return scorer.classify(response_text, probe)


__all__ = ["detect_ai_surfaces", "seed_hypotheses", "expand_tests",
           "score_observation", "AI_SIGNALS"]
