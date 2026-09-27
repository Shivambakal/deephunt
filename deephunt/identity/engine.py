"""DEEPHUNT identity engine: autonomous signup/signin state machine.

This is the in-depth auth automation core. It drives test-account creation
and sign-in for in-scope bug bounty targets through live browser tasks,
handling every step up to the verification wall:

  STUDY -> PREFILL -> CONSENT -> CAPTCHA -> PASSWORD -> VERIFY -> ACTIVE
                                              |          |
                                              v          v
                                          KYC_STOP    BLOCKED

Structural gates (enforced, not advisory):
  - target must have active_allowed=true in targets/<target>.yaml
  - target must have a STUDIED playbook (identity/playbooks/<target>.yaml);
    the engine refuses to run signup on an unstudied target.
  - any step matching stop_conditions -> KYC_STOP immediately, hands to user.
  - passwords are never generated, typed, logged, or stored by this engine.
    The PASSWORD state emits a Secure Vault card request for the user.
  - OTP codes are never guessed. The VERIFY state pauses for user input.

Session persistence: authenticated state lives in the live browser's
persistent profile (same profile across tasks). This engine never writes
cookies/tokens to disk — see SESSIONS.md.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from enum import Enum

import yaml

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from identity.manager import email_for, get, register, set_status  # noqa: E402


class AuthState(Enum):
    IDLE = "idle"
    STUDY = "study"            # playbook missing -> auto-study the signup page
    PREFILL = "prefill"        # fill identity fields (email, username, persona)
    CONSENT = "consent"        # click ToC/PP/disclosure checkboxes (or clickwrap note)
    CAPTCHA = "captcha"        # per-playbook strategy; pause on block
    PASSWORD = "password"      # STOP -> Secure Vault card for the user
    VERIFY = "verify"          # STOP -> user provides OTP from research mailbox
    KYC_STOP = "kyc_stop"      # identity/payment/SSN asked -> hand to user
    ACTIVE = "active"          # signed in, session in browser profile
    BLOCKED = "blocked"        # unrecoverable (ban, hard block, repeated captcha)


# Signals that force KYC_STOP. Checked against step descriptions the browser
# task reports back, and baked into every generated brief.
KYC_SIGNALS = (
    "ssn", "social security", "national id", "id document", "passport",
    "driver license", "driving licence", "selfie", "date of birth",
    "bank account", "routing number", "credit card", "debit card",
    "proof of address", "utility bill", "tax id",
)


@dataclass
class AuthRun:
    target: str
    mode: str = "signup"  # signup | signin
    state: AuthState = AuthState.IDLE
    email: str = ""
    playbook: dict = field(default_factory=dict)
    log: list = field(default_factory=list)
    pause_reason: str = ""

    def event(self, msg: str) -> None:
        self.log.append(msg)

    def transition(self, new: AuthState, reason: str = "") -> None:
        self.event(f"{self.state.value} -> {new.value} ({reason})")
        self.state = new
        if new in (AuthState.PASSWORD, AuthState.VERIFY,
                   AuthState.KYC_STOP, AuthState.BLOCKED):
            self.pause_reason = reason


def _target_active(target: str) -> bool:
    path = os.path.join(BASE, "targets", f"{target}.yaml")
    if not os.path.exists(path):
        return False
    with open(path) as f:
        return bool(yaml.safe_load(f).get("active_allowed"))


def _load_playbook(target: str) -> dict | None:
    path = os.path.join(BASE, "identity", "playbooks", f"{target}.yaml")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return yaml.safe_load(f)


def start_run(target: str, mode: str = "signup") -> AuthRun:
    """Begin an auth run. Enforces the structural gates."""
    run = AuthRun(target=target, mode=mode, email=email_for(target))
    if mode not in ("signup", "signin"):
        run.transition(AuthState.BLOCKED, f"unknown mode {mode}")
        return run
    if not _target_active(target):
        run.transition(AuthState.BLOCKED,
                       f"target {target} not active_allowed — refusing")
        return run
    pb = _load_playbook(target)
    if pb is None:
        run.transition(AuthState.STUDY,
                       "no studied playbook — run auto-study first")
        register(target, status="planned",
                 notes="awaiting signup-flow auto-study")
        return run
    run.playbook = pb
    register(target, status="signing_up" if mode == "signup" else "verifying",
             notes=f"{mode} run started via identity engine")
    run.transition(AuthState.PREFILL, "playbook loaded, gates passed")
    return run


def kyc_hit(text: str) -> str | None:
    """Return the matched KYC signal in free text, or None."""
    low = text.lower()
    for sig in KYC_SIGNALS:
        if sig in low:
            return sig
    return None


def on_task_report(run: AuthRun, report: str) -> AuthRun:
    """Advance the state machine from a browser task's status report."""
    sig = kyc_hit(report)
    if sig and run.state not in (AuthState.KYC_STOP, AuthState.ACTIVE,
                                 AuthState.BLOCKED):
        run.transition(AuthState.KYC_STOP, f"KYC signal: {sig!r}")
        set_status(run.target, "blocked", f"KYC stop at: {sig}")
        return run

    r = report.strip().upper()
    if "PASSWORD_STEP" in r:
        run.transition(AuthState.PASSWORD,
                       "issue Secure Vault card (credentials.request_new_password)")
    elif "OTP_NEEDED" in r or "VERIFICATION" in r:
        set_status(run.target, "verifying", "awaiting OTP from user")
        run.transition(AuthState.VERIFY, "user provides code from research mailbox")
    elif "CAPTCHA_BLOCKED" in r:
        run.transition(AuthState.CAPTCHA, "blocked — escalate to user takeover")
    elif "CONSENT_DONE" in r:
        run.transition(AuthState.CONSENT, "checkboxes/clickwrap handled")
    elif "SIGNED_IN" in r or "LOGIN_OK" in r:
        set_status(run.target, "active", "authenticated session in browser profile")
        run.transition(AuthState.ACTIVE, "session established")
    elif "BLOCKED" in r or "BANNED" in r or "DENIED" in r:
        set_status(run.target, "blocked", report[:200])
        run.transition(AuthState.BLOCKED, report[:200])
    else:
        run.event(f"unrecognized report (holding state): {report[:120]}")
    return run


def resume_after_user(run: AuthRun, action: str) -> AuthRun:
    """Continue a paused run after the user acts (vault card set / OTP given)."""
    if run.state == AuthState.PASSWORD and action == "vault_card_set":
        run.transition(AuthState.PREFILL, "password set in vault — continue flow")
    elif run.state == AuthState.VERIFY and action == "otp_provided":
        run.transition(AuthState.PREFILL, "OTP provided — submit verification")
    elif run.state == AuthState.CAPTCHA and action == "user_solved":
        run.transition(AuthState.PREFILL, "user solved CAPTCHA — continue")
    elif run.state == AuthState.KYC_STOP and action == "user_completed_kyc":
        set_status(run.target, "active", "user completed KYC manually")
        run.transition(AuthState.ACTIVE, "user completed KYC")
    else:
        run.event(f"resume ignored: state={run.state.value} action={action}")
    return run


if __name__ == "__main__":
    # quick self-check
    run = start_run("robinhood", "signup")
    print("state:", run.state.value, "| email:", run.email)
    for line in run.log:
        print("  ", line)
