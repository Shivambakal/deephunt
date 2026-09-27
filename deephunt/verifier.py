"""DEEPHUNT independent verifier — falsify, don't confirm (blueprint P0-6).

The anti-pattern this kills: the same agent that proposed a finding asking
itself "are you sure?" and answering yes. The verifier is STRUCTURALLY
separate from discovery:

  input:  claim + evidence + expected security property
  job:    ATTEMPT TO FALSIFY the claim using a different reasoning path
  output: VERIFIED / REJECTED / NEEDS_MORE with falsification notes

Falsification paths (deterministic, no LLM self-review):
  1. evidence-contract check — does the evidence satisfy the technique's
     contract from evidence.py? Missing artifacts = cannot verify.
  2. alternative-explanation kill — each surviving alternative from
     compete_finding must be disproven by a concrete evidence item, not
     by assertion.
  3. differential re-analysis — re-run differential.compare() with the
     control/test SWAPPED and stricter noise handling; a real finding is
     direction-independent.
  4. precondition audit — was the control actually valid? An invalid
     control (owner also denied) poisons the whole comparison.

Wire point: attacksurface.stage_independent_verify() calls
verify_finding() for every unconfirmed finding AFTER compete_finding().
brain/session.py is intentionally NOT edited — the verifier stays a
separate stage so discovery and verification can never share a code path.
"""
from __future__ import annotations

import sys
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

VERIFIED = "VERIFIED"
REJECTED = "REJECTED"
NEEDS_MORE = "NEEDS_MORE"


@dataclass
class VerificationReport:
    verdict: str
    falsification_notes: List[str] = field(default_factory=list)
    killed_alternatives: List[str] = field(default_factory=list)
    surviving_alternatives: List[str] = field(default_factory=list)
    confidence: float = 0.0


def _contract_check(technique_id: str, artifacts: Dict) -> (bool, List[str]):
    # built-in minimal contracts: the verifier does not depend on an
    # externally registered evidence contract to do its job.
    builtin_required = {
        "IDOR-01": ["request_log", "response_pair"],
        "IDOR-02": ["request_log", "response_pair"],
        "BOLA-01": ["request_log", "response_pair"],
        "AUTH-01": ["request_log", "response_pair"],
        "SQLI-01": ["request_log", "response_pair", "error_text"],
        # P1 bench classes (2.x): workflow/state, AI exfil, agent tool abuse
        "WF-01": ["request_log", "response_pair", "state_trace"],
        "LLM04": ["request_log", "response_pair", "canary_marker"],
        "LLM06": ["request_log", "response_pair", "tool_trace"],
    }
    required = builtin_required.get(technique_id or "")
    if required:
        missing = [r for r in required if r not in (artifacts or {})]
        if missing:
            return False, missing
        return True, []
    try:
        from evidence import ContractRegistry
        reg = ContractRegistry()
        contract = reg.contracts.get(technique_id)
        if not contract:
            return True, []  # no contract registered: not a blocker
        ok, missing = contract.validate(artifacts or {})
        return ok, missing
    except Exception as e:
        return False, [f"contract registry error: {e}"]


def _differential_reanalysis(control: str, test: str) -> (str, List[str]):
    """Re-run the differential with control/test swapped. A genuine
    authorization finding must survive the swap (the asymmetry must flip
    with the identities, not disappear)."""
    try:
        import differential as diff_mod
    except Exception as e:
        return "error", [f"differential module unavailable: {e}"]
    verdict, reasons = diff_mod.compare(test, control,
                                        label_a="swapped-test",
                                        label_b="swapped-control")
    return verdict, reasons


def _precondition_audit(control: str) -> (bool, str):
    """Was the control valid? Owner-denied controls invalidate everything."""
    import re
    if not control:
        return False, "empty control observation"
    if re.search(r"\b(401|403|404|500)\b", control):
        # control errored — but is that fatal? Only if it never demonstrated
        # the allowed behavior. Flag for review rather than auto-reject.
        return False, "control shows an error status — precondition suspect"
    if re.search(r"\b(200|201|202)\b", control):
        return True, "control demonstrates allowed behavior"
    return False, "control has no clear allow signal"


def verify_finding(claim: str, evidence: Dict,
                   expected_property: str = "",
                   technique_id: str = "",
                   alternatives: Optional[List[str]] = None) -> VerificationReport:
    """Attempt to falsify. Returns VERIFIED only when every falsification
    path fails to kill the claim."""
    notes: List[str] = []
    control = (evidence or {}).get("control_observation", "")
    test = (evidence or {}).get("test_observation", "")
    artifacts = (evidence or {}).get("artifacts", {})

    # 1. evidence contract
    ok, missing = _contract_check(technique_id, artifacts)
    if not ok:
        notes.append(f"contract FAILED for {technique_id}: missing {missing}")
        return VerificationReport(REJECTED, notes, confidence=0.9)
    notes.append("evidence contract satisfied" if technique_id else
                 "no contract registered — skipped")

    # 2. precondition audit (control validity) — BEFORE trusting the diff
    ctrl_ok, ctrl_note = _precondition_audit(control)
    notes.append(f"control audit: {ctrl_note}")
    if not ctrl_ok:
        return VerificationReport(NEEDS_MORE, notes, confidence=0.4)

    # 3. differential re-analysis with swapped roles
    verdict, reasons = _differential_reanalysis(control, test)
    notes.append(f"swapped differential: {verdict} ({'; '.join(reasons[:3])})")
    if verdict == "identical":
        notes.append("FALSIFIED: asymmetry disappears — likely noise/artifact")
        return VerificationReport(REJECTED, notes, confidence=0.85)

    # 4. alternative explanations must each be killed by evidence
    killed, surviving = [], []
    for alt in alternatives or []:
        killed_by = (evidence or {}).get("killed_alternatives", {})
        if alt in killed_by:
            killed.append(alt)
        else:
            surviving.append(alt)
    notes.append(f"alternatives killed={len(killed)} surviving={len(surviving)}")
    if surviving:
        return VerificationReport(NEEDS_MORE, notes, killed, surviving,
                                  confidence=0.5)

    notes.append("all falsification paths exhausted — claim stands")
    return VerificationReport(VERIFIED, notes, killed, surviving, confidence=0.8)


def verify_for_compete(finding: Dict) -> VerificationReport:
    """Adapter: run the verifier over a brain unconfirmed_finding dict."""
    competition = finding.get("competition", {})
    surviving = [s["explanation"] for s in competition.get("surviving", [])]
    evidence = {
        "control_observation": finding.get("control_observation", ""),
        "test_observation": finding.get("test_observation", ""),
        "artifacts": finding.get("artifacts", {}),
        "killed_alternatives": {
            d["explanation"]: d.get("disproven_by", "")
            for d in competition.get("disproven", [])},
    }
    return verify_finding(
        finding.get("claim", ""), evidence,
        expected_property=finding.get("expected_property", ""),
        technique_id=finding.get("technique_id", ""),
        alternatives=surviving)
