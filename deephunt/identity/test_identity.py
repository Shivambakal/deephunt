"""Tests for the identity engine: gates, state machine, briefs. No network."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from identity import auto_study, driver
from identity.engine import (AuthState, kyc_hit, on_task_report, resume_after_user,
                             start_run)
from identity.manager import email_for, get, list_all, register, set_status


def test_email_convention():
    assert email_for("robinhood") == "attacksurface.alerts+robinhood@gmail.com"


def test_registry_roundtrip():
    register("testtarget", status="planned", notes="unit test")
    ident = get("testtarget")
    assert ident["email"] == "attacksurface.alerts+testtarget@gmail.com"
    assert ident["status"] == "planned"
    # registry must never hold secrets
    assert "password" not in ident and "secret" not in ident and "token" not in ident
    set_status("testtarget", "retired", "test done")
    assert get("testtarget")["status"] == "retired"


def test_gate_rejects_inactive_target():
    run = start_run("adobe", "signup")  # adobe has active_allowed=false
    assert run.state == AuthState.BLOCKED


def test_gate_rejects_unknown_target():
    run = start_run("nosuchtarget", "signup")
    assert run.state == AuthState.BLOCKED


def test_gate_requires_playbook():
    # shopify is active but has no studied playbook -> STUDY state
    run = start_run("shopify", "signup")
    assert run.state == AuthState.STUDY


def test_robinhood_run_prefill():
    run = start_run("robinhood", "signup")
    assert run.state == AuthState.PREFILL
    assert run.email == "attacksurface.alerts+robinhood@gmail.com"


def test_kyc_signal_halts():
    run = start_run("robinhood", "signup")
    on_task_report(run, "page now asks for Social Security Number")
    assert run.state == AuthState.KYC_STOP


def test_password_step_pauses_for_vault():
    run = start_run("robinhood", "signup")
    on_task_report(run, "PASSWORD_STEP reached")
    assert run.state == AuthState.PASSWORD
    assert "vault" in run.pause_reason.lower()


def test_otp_step_pauses_for_user():
    run = start_run("robinhood", "signup")
    on_task_report(run, "OTP_NEEDED")
    assert run.state == AuthState.VERIFY


def test_signin_success():
    run = start_run("robinhood", "signin")
    on_task_report(run, "SIGNED_IN ok")
    assert run.state == AuthState.ACTIVE


def test_resume_after_vault():
    run = start_run("robinhood", "signup")
    on_task_report(run, "PASSWORD_STEP")
    resume_after_user(run, "vault_card_set")
    assert run.state == AuthState.PREFILL


def test_kyc_hit_detector():
    assert kyc_hit("enter your passport number") == "passport"
    assert kyc_hit("what is your email") is None


def test_signup_brief_has_vault_stop():
    brief = driver.render_brief("robinhood")
    assert "Secure Vault" in brief
    assert "attacksurface.alerts+robinhood@gmail.com" in brief
    assert "KYC_STOP" in brief


def test_signin_brief_uses_vault_fill():
    brief = driver.render_signin_brief("robinhood")
    assert "Secure Vault" in brief
    assert "SIGNED_IN" in brief


def test_study_brief_render():
    b = auto_study.render_study_brief("acme", "https://acme.com/signup")
    assert "READ-ONLY" in b and "acme" in b


def test_unstudied_target_brief_refused():
    try:
        driver.render_brief("shopify")
    except FileNotFoundError:
        return
    raise AssertionError("should have refused unstudied target")
