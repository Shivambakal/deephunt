"""DEEPHUNT ai_attacks — AI/LLM attack planners (propose-only).

Every module here is a *planner*: it generates test-case dictionaries —
what to plant or send, which queries to issue, what observations would prove
or refute the hypothesis, and how to score the result. Nothing in this
package transmits anything, opens sockets, spawns subprocesses, or touches a
real system. The pipeline feeds these test cases through
ResearchSession.propose_test() -> TestAuthorization -> Engine.execute().

Target-agnostic: all target specifics arrive as function parameters.
Mocks/fixtures exist only inside the test file for self-verification.
"""
from __future__ import annotations

from .agent_abuse import (
    approval_bypass_tests,
    covert_channel_patterns,
    escalation_paths,
    map_tool_permissions,
)
from .extraction import (
    distillation_signals,
    system_prompt_extraction_battery,
    training_data_extraction_patterns,
)
from .rag_poison import (
    embedding_collision_notes,
    plan_rag_test,
    poisoned_document_patterns,
)
from .prompt_injection import (
    direct_injection_cases,
    indirect_injection_cases,
    multiturn_escalation_plan,
    delimiter_confusion_cases,
    generate,
)
from .jailbreak import load_techniques, instantiate, battery
from .scorer import classify, REFUSAL_PATTERNS, ALTERNATIVE_PATTERNS

__all__ = [
    "poisoned_document_patterns",
    "plan_rag_test",
    "embedding_collision_notes",
    "map_tool_permissions",
    "escalation_paths",
    "approval_bypass_tests",
    "covert_channel_patterns",
    "system_prompt_extraction_battery",
    "training_data_extraction_patterns",
    "distillation_signals",
    # ai_attacks part 1 (prompt_injection / jailbreak / scorer)
    "direct_injection_cases",
    "indirect_injection_cases",
    "multiturn_escalation_plan",
    "delimiter_confusion_cases",
    "generate",
    "load_techniques",
    "instantiate",
    "battery",
    "classify",
    "REFUSAL_PATTERNS",
    "ALTERNATIVE_PATTERNS",
]
