"""Tests for deephunt/evidence.py — no network, no LLM."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from evidence import Canary, ContractRegistry, EvidenceContract


def test_builtin_idor_contract():
    reg = ContractRegistry()
    ok, missing = reg.validate_evidence(
        "IDOR-99",
        {"foreign_object_returned": True,
         "control_denied_or_not_found": True,
         "auth_context_documented": True},
        klass="IDOR")
    assert ok and not missing, f"full artifacts should validate: {missing}"
    ok2, missing2 = reg.validate_evidence(
        "IDOR-99", {"foreign_object_returned": True}, klass="IDOR")
    assert not ok2 and "control_denied_or_not_found" in missing2, \
        "partial artifacts must fail with named missing items"
    print("PASS test_builtin_idor_contract")


def test_unknown_technique_rejected():
    reg = ContractRegistry()
    ok, missing = reg.validate_evidence("NOPE-01", {"anything": True})
    assert not ok and missing == ["no contract registered — cannot confirm"]
    print("PASS test_unknown_technique_rejected")


def test_card_contract_loading():
    reg = ContractRegistry()
    cards = [{"id": "AUTHB-01",
              "evidence_contract": ["baseline_403_recorded",
                                    "bypass_response_differs",
                                    "control_still_403"]}]
    n = reg.load_from_cards(cards)
    assert n == 1
    ok, missing = reg.validate_evidence("AUTHB-01", {
        "baseline_403_recorded": True, "bypass_response_differs": True,
        "control_still_403": False})
    assert not ok and missing == ["control_still_403"]
    print("PASS test_card_contract_loading")


def test_canary_calibration():
    reg = ContractRegistry()
    # positive canary: known-good evidence must validate
    good = Canary("IDOR-01", {"foreign_object_returned": True,
                              "control_denied_or_not_found": True,
                              "auth_context_documented": True},
                  expect_valid=True)
    ok, _ = good.run(reg, klass="IDOR")
    assert ok, "positive canary failed — contract broken"
    # negative canary: known-bad evidence must NOT validate
    bad = Canary("IDOR-01", {"foreign_object_returned": True},
                 expect_valid=False)
    ok2, _ = bad.run(reg, klass="IDOR")
    assert ok2, "negative canary failed — contract too lax"
    print("PASS test_canary_calibration")


def test_custom_contract_registration():
    reg = ContractRegistry()
    reg.register(EvidenceContract("CUSTOM-01", ["a", "b"], "test"))
    ok, _ = reg.validate_evidence("CUSTOM-01", {"a": True, "b": True})
    assert ok
    print("PASS test_custom_contract_registration")


if __name__ == "__main__":
    test_builtin_idor_contract()
    test_unknown_technique_rejected()
    test_card_contract_loading()
    test_canary_calibration()
    test_custom_contract_registration()
    print("evidence: 5/5 pass")
