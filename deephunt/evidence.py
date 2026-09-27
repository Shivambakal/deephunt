"""DEEPHUNT evidence contracts — XBOW's core trick, adapted.

XBOW (Black Hat USA 2025): LLM agents do *discovery*; validation is non-LLM
deterministic code. Per-vuln-class validators demand EXACT evidence artifacts;
no report without them.

This module implements that split for DEEPHUNT:
  - Each technique card may carry an `evidence_contract`: the list of artifact
    names that constitute proof (e.g. ["response_with_foreign_data",
    "control_response_404"]).
  - `validate_evidence(technique_id, artifacts)` returns (ok, missing) —
    deterministic, no LLM involved.
  - `register_contract()` / contracts are also loadable from technique cards.
  - Canary support: `Canary` plants a known-answer check to calibrate whether
    a technique's contract is satisfiable at all (catches impossible
    contracts before they burn hunt budget).

Contracts live with the technique cards (knowledge/techniques/*.yaml) so the
reasoning layer and the validation layer share one source of truth.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# Built-in contracts for core technique classes. Cards may override/extend
# via their `evidence_contract` field.
BUILTIN_CONTRACTS: Dict[str, List[str]] = {
    # IDOR/BOLA: need the foreign object AND a control showing the boundary
    "IDOR": ["foreign_object_returned", "control_denied_or_not_found",
             "auth_context_documented"],
    "BOLA": ["foreign_object_returned", "control_denied_or_not_found",
             "auth_context_documented"],
    "XSS": ["payload_reflected_executed", "context_documented"],
    "SQLI": ["differential_confirmed", "control_baseline_recorded"],
    "SSRF": ["oob_interaction_observed", "control_no_egress"],
    "RCE": ["command_output_observed", "control_baseline_recorded"],
    "AUTH_BYPASS": ["protected_resource_accessed", "unauth_control_denied"],
    "RACE": ["single_packet_evidence", "repeated_n_times"],
}


@dataclass
class EvidenceContract:
    technique_id: str
    required: List[str] = field(default_factory=list)
    notes: str = ""

    def validate(self, artifacts: Dict[str, bool]) -> Tuple[bool, List[str]]:
        missing = [r for r in self.required if not artifacts.get(r)]
        return (len(missing) == 0, missing)


class ContractRegistry:
    def __init__(self):
        self.contracts: Dict[str, EvidenceContract] = {
            tid: EvidenceContract(tid, req)
            for tid, req in BUILTIN_CONTRACTS.items()
        }

    def register(self, contract: EvidenceContract):
        self.contracts[contract.technique_id] = contract

    def for_technique(self, technique_id: str,
                      klass: Optional[str] = None) -> Optional[EvidenceContract]:
        if technique_id in self.contracts:
            return self.contracts[technique_id]
        if klass and klass.upper() in self.contracts:
            return self.contracts[klass.upper()]
        return None

    def validate_evidence(self, technique_id: str, artifacts: Dict[str, bool],
                          klass: Optional[str] = None) -> Tuple[bool, List[str]]:
        contract = self.for_technique(technique_id, klass)
        if contract is None:
            return (False, ["no contract registered — cannot confirm"])
        return contract.validate(artifacts)

    def load_from_cards(self, cards: List[dict]) -> int:
        """Pull `evidence_contract` lists off technique cards. Returns count."""
        n = 0
        for c in cards:
            ec = c.get("evidence_contract")
            if ec:
                req = ec if isinstance(ec, list) else ec.get("required", [])
                self.register(EvidenceContract(
                    c["id"], req, ec.get("notes", "") if isinstance(ec, dict) else ""))
                n += 1
        return n


@dataclass
class Canary:
    """Known-answer calibration check for a technique contract.

    Plant a canary (a synthetic case with a known outcome) and verify the
    contract validates it. If the canary fails, the contract — not the target —
    is broken; fix the contract before spending hunt budget.
    """
    technique_id: str
    expected_artifacts: Dict[str, bool]
    expect_valid: bool = True

    def run(self, registry: ContractRegistry,
            klass: Optional[str] = None) -> Tuple[bool, str]:
        ok, missing = registry.validate_evidence(
            self.technique_id, self.expected_artifacts, klass)
        if ok == self.expect_valid:
            return (True, "canary behaved as expected")
        return (False,
                f"canary mismatch: valid={ok} (missing={missing}), "
                f"expected valid={self.expect_valid}")
