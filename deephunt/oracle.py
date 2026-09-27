"""DEEPHUNT oracle engine — security-property validators (blueprint P0-5).

An oracle answers ONE question: given a control observation and a test
observation, does the security property HOLD, was it VIOLATED, or is the
result INCONCLUSIVE? Oracles are deterministic code, not LLM judgment —
the LLM proposes, the oracle disposes.

Verdicts: VIOLATED / HELD / INCONCLUSIVE.

Each oracle is keyed to an invariant id from the world model. The default
invariant set covers the blueprint's core properties; targets can add
their own via register().
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

VIOLATED = "VIOLATED"
HELD = "HELD"
INCONCLUSIVE = "INCONCLUSIVE"

_STATUS = re.compile(r"\b([1-5][0-9]{2})\b")


def _statuses(text: str) -> List[int]:
    return [int(m.group(1)) for m in _STATUS.finditer(text or "")]


def _denied(text: str) -> bool:
    s = _statuses(text)
    return any(x in (400, 401, 403, 404) for x in s) or \
        bool(re.search(r"forbidden|denied|unauthorized|not found|"
                       r"invalid transition|bad request", text or "", re.I))


def _granted(text: str) -> bool:
    s = _statuses(text)
    return any(x in (200, 201, 202, 204) for x in s)


@dataclass
class OracleVerdict:
    verdict: str
    reason: str
    invariant_id: str = ""
    confidence: float = 0.5


OracleFn = Callable[[str, str, Dict], OracleVerdict]


def ownership_oracle(control: str, test: str, ctx: Dict) -> OracleVerdict:
    """Actor B must not access/modify actor A's object.

    VIOLATED when: control (owner) is granted AND test (other actor) is
    granted with equivalent-or-richer content.
    HELD when: test is denied while control is granted.
    """
    c_grant, t_grant = _granted(control), _granted(test)
    c_deny, t_deny = _denied(control), _denied(test)
    if c_grant and t_grant:
        # granted to both — violation only if test saw the object data.
        # strongest signal: the owner's marker from the control observation
        # reappears in the test response (the object content leaked).
        owner = (ctx or {}).get("owner") or ""
        if not owner:
            m = re.search(r"owned by ([A-Za-z0-9_@.+-]+)", control or "", re.I)
            owner = m.group(1) if m else ""
        if owner and owner.lower() in (test or "").lower():
            return OracleVerdict(VIOLATED,
                                 f"non-owner granted; owner's object content "
                                 f"('{owner}') returned to them",
                                 "ownership", 0.9)
        if len((test or "")) >= max(50, int(len(control or "") * 0.5)):
            return OracleVerdict(VIOLATED,
                                 "non-owner granted with object content returned",
                                 "ownership", 0.85)
        return OracleVerdict(INCONCLUSIVE,
                             "both granted but test content unclear — needs body diff",
                             "ownership", 0.4)
    if c_grant and t_deny:
        return OracleVerdict(HELD, "owner granted, non-owner denied", "ownership", 0.9)
    if not c_grant and not t_grant:
        return OracleVerdict(INCONCLUSIVE,
                             "control itself denied — precondition not met", "ownership", 0.3)
    return OracleVerdict(INCONCLUSIVE, "ambiguous status combination", "ownership", 0.3)


def auth_boundary_oracle(control: str, test: str, ctx: Dict) -> OracleVerdict:
    """Authenticated-only resources must deny anonymous access."""
    if _granted(test) and _denied(control) is False:
        # test = anonymous variant granted
        if _granted(control):
            return OracleVerdict(VIOLATED, "anonymous granted on authenticated resource",
                                 "auth_boundary", 0.8)
    if _denied(test):
        return OracleVerdict(HELD, "anonymous denied", "auth_boundary", 0.9)
    return OracleVerdict(INCONCLUSIVE, "cannot determine auth boundary", "auth_boundary", 0.3)


def state_transition_oracle(control: str, test: str, ctx: Dict) -> OracleVerdict:
    """An invalid workflow transition must be rejected.

    ctx may carry allowed_from/allowed_to and attempted transition.

    Multi-step transcripts (segments separated by "--- step:" markers, as
    produced by chained executions) are judged by their LAST step: the
    transition under test is the final attempted action, and an early 2xx
    (e.g. the setup step) must not mask a later rejection. Single-step
    observations are evaluated whole, as before.
    """
    attempted = ctx.get("attempted_transition", "")
    final = _final_step(test)
    if _granted(final) and attempted:
        # the attempted transition was granted — but a short rejection
        # notice inside the same step still counts as rejected
        if re.search(r"error|invalid|reject|fail", final, re.I) and \
                len(final) < 300:
            return OracleVerdict(HELD, "transition rejected with error",
                                 "state_transition", 0.7)
        return OracleVerdict(VIOLATED,
                             f"invalid transition accepted: {attempted}",
                             "state_transition", 0.75)
    if _denied(final):
        return OracleVerdict(HELD, "invalid transition denied",
                             "state_transition", 0.85)
    return OracleVerdict(INCONCLUSIVE, "no clear transition signal",
                         "state_transition", 0.3)


def _final_step(text: str) -> str:
    """Last "--- step:" segment of a chained observation, else the whole."""
    parts = re.split(r"--- step:[^\n]*\n", text or "")
    parts = [p for p in parts if p.strip()]
    return parts[-1] if parts else (text or "")


def no_leak_oracle(control: str, test: str, ctx: Dict) -> OracleVerdict:
    """Sensitive markers visible in test but not control (or vice versa)."""
    pat = re.compile(ctx.get("leak_pattern", r"(password|secret|api[_-]?key|ssn|card)"),
                     re.I)
    in_c, in_t = bool(pat.search(control or "")), bool(pat.search(test or ""))
    if in_t and not in_c:
        return OracleVerdict(VIOLATED, "sensitive marker in test observation only",
                             "no_leak", 0.8)
    if not in_t and not in_c:
        return OracleVerdict(HELD, "no sensitive markers in either", "no_leak", 0.7)
    return OracleVerdict(INCONCLUSIVE, "markers in both — baseline unclear", "no_leak", 0.3)


def tenant_isolation_oracle(control: str, test: str, ctx: Dict) -> OracleVerdict:
    """Tenant A must not see tenant B's objects. Same shape as ownership."""
    v = ownership_oracle(control, test, ctx)
    v.invariant_id = "tenant_isolation"
    return v


BUILTIN: Dict[str, OracleFn] = {
    "ownership": ownership_oracle,
    "ownership_must_match_actor": ownership_oracle,
    "auth_boundary": auth_boundary_oracle,
    "authentication": auth_boundary_oracle,
    "state_transition": state_transition_oracle,
    "workflow_integrity": state_transition_oracle,
    "no_leak": no_leak_oracle,
    "confidentiality": no_leak_oracle,
    "tenant_isolation": tenant_isolation_oracle,
}

_CUSTOM: Dict[str, OracleFn] = {}


def register(invariant_id: str, fn: OracleFn):
    _CUSTOM[invariant_id] = fn


def check(invariant_id: str, control: str, test: str,
          ctx: Optional[Dict] = None) -> OracleVerdict:
    fn = _CUSTOM.get(invariant_id) or BUILTIN.get(invariant_id)
    if not fn:
        return OracleVerdict(INCONCLUSIVE, f"no oracle for invariant {invariant_id}",
                             invariant_id, 0.2)
    return fn(control or "", test or "", ctx or {})


def check_all(invariant_ids: List[str], control: str, test: str,
              ctx: Optional[Dict] = None) -> List[OracleVerdict]:
    return [check(i, control, test, ctx) for i in invariant_ids]


def summarize(verdicts: List[OracleVerdict]) -> Tuple[str, str]:
    """Worst-case roll-up: any VIOLATED dominates."""
    if any(v.verdict == VIOLATED for v in verdicts):
        hit = next(v for v in verdicts if v.verdict == VIOLATED)
        return VIOLATED, f"{hit.invariant_id}: {hit.reason}"
    if all(v.verdict == HELD for v in verdicts) and verdicts:
        return HELD, "all invariants held"
    return INCONCLUSIVE, "no violation proven; evidence insufficient"
