"""Signup driver: turns a studied playbook into an executable browser-task brief.

The driver itself never touches the browser. It:
  1. loads identity/playbooks/<target>.yaml (must exist = flow was studied),
  2. emits a pre-flight checklist (vault state, CAPTCHA preference, stop conditions),
  3. renders the step-by-step brief the agent feeds to a live browser task,
  4. tracks the run through the identity registry (planned -> signing_up ->
     verifying -> active | blocked).

Password handling: the brief instructs the browser task to STOP at the
password field and request a Secure Vault card (credentials.request_new_password)
so the user sets the password on the secure page. The password is never typed
by the agent, never logged, never stored here.

OTP handling: at email/phone verification the task pauses and asks the user
for the code (research mailbox is not auto-polled; the user reads it).
"""
from __future__ import annotations

import os
import sys

import yaml

from .manager import email_for, get, register, set_status

BASE = os.path.dirname(os.path.abspath(__file__))
PLAYBOOKS = os.path.join(BASE, "playbooks")


def load_playbook(target: str) -> dict:
    path = os.path.join(PLAYBOOKS, f"{target}.yaml")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"no studied playbook for {target!r} — study the signup flow first "
            f"(see playbooks/_template.yaml)")
    with open(path) as f:
        return yaml.safe_load(f)


def preflight(target: str) -> list[str]:
    """Checklist the agent must satisfy before spawning the signup task."""
    pb = load_playbook(target)
    ident = get(target)
    checks = [
        f"playbook studied: {pb.get('studied_on', 'UNKNOWN')} by {pb.get('studied_by', '?')}",
        f"signup URL: {pb.get('signup_url')}",
        f"test email: {email_for(target)}",
        f"identity status: {ident['status'] if ident else 'not registered'}",
        f"CAPTCHA type on site: {pb.get('captcha', {}).get('type', 'unknown')} "
        f"-> strategy: {pb.get('captcha', {}).get('strategy', 'user_handles')}",
        f"ToC/PP checkboxes: {len(pb.get('consent', {}).get('checkboxes', []))} to click",
        "STOP conditions: " + "; ".join(pb.get("stop_conditions", ["none listed"])),
        "password: user sets via Secure Vault card (never typed by agent)",
        "OTP: user reads research mailbox and provides the code when asked",
    ]
    return checks


def render_brief(target: str) -> str:
    """Render the browser-task brief for the signup run."""
    pb = load_playbook(target)
    email = email_for(target)
    lines = [
        f"SIGNUP TASK — {target} (bug bounty TEST account, researcher-owned)",
        "",
        f"1. Go to {pb.get('signup_url')}",
        f"2. Use email: {email}",
        "3. When you reach the PASSWORD field: STOP. Do not invent or type a",
        "   password. Report back 'PASSWORD_STEP' so a Secure Vault card can be",
        "   issued for the user to set the password securely.",
        "",
        "Consent checkboxes (Terms of Service / Privacy Policy / disclosures):",
    ]
    for cb in pb.get("consent", {}).get("checkboxes", []):
        lines.append(f"  - click the checkbox labeled: {cb}")
    lines += [
        "",
        f"CAPTCHA: {pb.get('captcha', {}).get('type', 'unknown')}. "
        f"{pb.get('captcha', {}).get('notes', '')}",
        "If a CAPTCHA blocks progress, follow the task's CAPTCHA preference; "
        "if it cannot be solved, pause and report 'CAPTCHA_BLOCKED'.",
        "",
        "Email verification: when the site sends a code/link to the email,",
        "pause and report 'OTP_NEEDED'. Do NOT guess codes.",
        "",
        "HARD STOPS — halt immediately and report 'KYC_STOP' if the flow asks for:",
    ]
    for s in pb.get("stop_conditions", []):
        lines.append(f"  - {s}")
    lines += [
        "",
        "Do not submit any real personal data, ID documents, or payment details.",
        "This is a security-research test account on an in-scope bug bounty target.",
    ]
    return "\n".join(lines)


def begin(target: str) -> dict:
    register(target, status="signing_up",
             notes="signup run started via identity driver")
    return {"target": target, "email": email_for(target)}


def mark_verifying(target: str) -> dict:
    return set_status(target, "verifying", "awaiting email OTP from user")


def mark_active(target: str) -> dict:
    return set_status(target, "active", "test account ready for authenticated testing")


def mark_blocked(target: str, reason: str) -> dict:
    return set_status(target, "blocked", reason)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: driver.py <preflight|brief|begin> <target>")
        sys.exit(1)
    cmd, target = sys.argv[1], sys.argv[2]
    if cmd == "preflight":
        print("\n".join(" - " + c for c in preflight(target)))
    elif cmd == "brief":
        print(render_brief(target))
    elif cmd == "begin":
        print(begin(target))
    else:
        sys.exit(f"unknown cmd {cmd}")


def render_signin_brief(target: str) -> str:
    """Render the browser-task brief for a sign-in run (vault-filled password)."""
    from .manager import email_for
    pb = load_playbook(target)
    email = email_for(target)
    login_url = pb.get("login_url", "unknown")
    lines = [
        f"SIGN-IN TASK — {target} (researcher-owned TEST account)",
        "",
        f"1. Go to {login_url}",
        "2. If you are already signed in (redirected to the app, not the login",
        "   form), report 'SIGNED_IN' immediately — reuse the live session.",
        f"3. Otherwise fill email: {email}",
        "4. For the PASSWORD field: use the browser's saved-login fill from the",
        "   Secure Vault. NEVER ask the user for the password in chat, NEVER",
        "   type a password from any other source.",
        "5. Handle 'keep me logged in' / 'remember me' by leaving it CHECKED",
        "   (longer sessions = fewer sign-ins).",
        "",
        f"CAPTCHA: {pb.get('captcha', {}).get('type', 'unknown')}.",
        "If blocked, follow the task CAPTCHA preference; on failure report",
        "'CAPTCHA_BLOCKED' — do not loop.",
        "",
        "On success report 'SIGNED_IN'. On credential rejection report",
        "'CREDENTIALS_REJECTED' (the vault entry may be stale — do not retry",
        "more than once). On any MFA/OTP prompt report 'OTP_NEEDED' and pause.",
        "",
        "HARD STOPS (report 'KYC_STOP'): " + "; ".join(pb.get("stop_conditions", [])),
    ]
    return "\n".join(lines)
