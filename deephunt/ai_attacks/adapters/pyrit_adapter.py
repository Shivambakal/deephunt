"""PyRIT adapter — Microsoft's Python Risk Identification Toolkit.

PyRIT gives us multi-turn red-team orchestrators (RedTeamingOrchestrator,
CrescendoOrchestrator) and pluggable scorers. DEEPHUNT drives it against a
custom target by subclassing PromptTarget; scoring reuses our own
scorer.classify via a MarkerScorer bridge.

Same rail as garak_adapter: specs are pure data; run_* requires a
TestAuthorization token.
"""
from __future__ import annotations

import importlib.util
from typing import Dict, List


def available() -> bool:
    return importlib.util.find_spec("pyrit") is not None


def plan_redteam(objective: str, max_turns: int = 5,
                 orchestrator: str = "crescendo") -> Dict:
    """Propose-only red-team execution spec."""
    return {
        "tool": "pyrit",
        "action": "run_redteam",
        "objective": objective,
        "orchestrator": orchestrator,  # "crescendo" | "red_teaming"
        "max_turns": max_turns,
        "requires": "TestAuthorization; target endpoint via DeepHuntTarget",
        "note": "Objective must be a SYNTHETIC benign stand-in (e.g. canary "
                "extraction), never a real disallowed request.",
    }


def drive_code_sketch() -> str:
    """How a pipeline executor drives PyRIT. Kept as documentation; the real
    driver lives in the engine layer and is only invoked post-authorization."""
    return '''
from pyrit.prompt_target import PromptTarget
from pyrit.orchestrator import CrescendoOrchestrator
from pyrit.score import Scorer
from deephunt.ai_attacks import scorer as dh_scorer

class DeepHuntTarget(PromptTarget):
    # implement _send_prompt_to_target_async only; never override
    # send_prompt_async (it is @final in PyRIT).
    async def _send_prompt_to_target_async(self, prompt):
        return await engine_execute_authorized(prompt)  # via Engine.execute()

class MarkerScorer(Scorer):
    async def score_text_async(self, text, *, probe):
        return dh_scorer.classify(text, probe)  # refusal/compliance/partial_leak

# orchestrator = CrescendoOrchestrator(objective=..., adversarial_chat=...,
#                                     chat_target=DeepHuntTarget(), max_turns=5,
#                                     scorer=MarkerScorer())
'''


def normalize_result(pyrit_result: Dict) -> Dict:
    """Normalize one PyRIT conversation result into a DEEPHUNT finding."""
    return {
        "tool": "pyrit",
        "objective": pyrit_result.get("objective", ""),
        "turns": pyrit_result.get("turns", 0),
        "final_verdict": pyrit_result.get("verdict", "inconclusive"),
        "evidence_artifacts": {
            "pyrit_completed": True,
            "verdict_compliance": pyrit_result.get("verdict") == "compliance",
            "verdict_partial_leak":
                pyrit_result.get("verdict") == "partial_leak",
        },
    }


__all__ = ["available", "plan_redteam", "drive_code_sketch",
           "normalize_result"]
