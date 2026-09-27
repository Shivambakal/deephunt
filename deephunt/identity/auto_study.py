"""Auto-study: turn any target's signup page into a studied playbook.

The engine never guesses a signup flow. This module renders the read-only
browser-task brief that observes a signup page and returns structured data,
plus the parser that converts the observation into playbooks/<target>.yaml.

Accuracy comes from observation, not heuristics: every playbook field must be
seen in the live DOM. Anything not observed is marked unknown, never guessed.
"""
from __future__ import annotations

import os

import yaml

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STUDY_BRIEF = """READ-ONLY signup-flow study for {target}. Do NOT create an account,
do NOT submit any form, do NOT enter any personal data. Observe only.

Target signup page: {signup_url} (if it redirects, record the final URL)

Return your findings in EXACTLY this structure:

URLS:
- signup_url_final: <final URL after redirects>
- login_url: <login page URL>

STEP1_FIELDS: (list every field on the first step)
- label: <visible label> | type: <email|password|text|tel|checkbox> | testid/name/autocomplete: <value> | required: <yes|no>

CONSENT:
- type: <checkboxes|clickwrap|none>
- checkboxes: (exact visible label of each, one per line)
- clickwrap_text: <exact text if clickwrap>

CAPTCHA:
- type: <none_visible|recaptcha_v2_checkbox|recaptcha_v3_invisible|recaptcha_enterprise|hcaptcha|turnstile|arkose|other>
- evidence: <DOM/HTML evidence, e.g. script src, iframe, site key>
- fingerprinting: <any device/browser fingerprint endpoints seen, e.g. preconnects>

VERIFICATION_HINTS:
- <anything on the page hinting at email/phone verification later>

SOCIAL_LOGIN:
- <list any Continue with Google/Apple/GitHub buttons, or 'none'>

PASSWORD_POLICY_HINTS:
- <any visible password requirements>

KYC_HINTS:
- <any mention of identity verification, SSN, ID documents in visible text/links>

WIZARD:
- steps_hint: <progressbar values, 'Step X of Y' text, or 'unknown'>

HARD RULE: anything you did not directly observe must be written as 'unknown'.
Do not infer later steps. Do not click Continue/Submit."""

# Maps study output keys to playbook fields. Unknown stays unknown.
PLAYBOOK_DEFAULTS = {
    "captcha": {"type": "unknown", "notes": "", "strategy": "user_handles"},
    "verification": {"method": "unknown"},
    "consent": {"checkboxes": []},
    "stop_conditions": [
        "SSN / national ID number",
        "government ID document upload",
        "real full name / date of birth beyond test persona",
        "payment instrument / bank details",
    ],
    "vault": {"password_via": "secure_card"},
}


def render_study_brief(target: str, signup_url: str) -> str:
    return STUDY_BRIEF.format(target=target, signup_url=signup_url)


def build_playbook_skeleton(target: str, signup_url: str, login_url: str = "") -> dict:
    """Skeleton the agent fills from the study observation. Unobserved = unknown."""
    pb = {
        "target": target,
        "studied_on": "YYYY-MM-DD",
        "studied_by": "auto-study (read-only browser observation)",
        "signup_url": signup_url,
        "login_url": login_url or "unknown",
        "steps": [],
        "consent": {"checkboxes": [], "type": "unknown"},
        "captcha": dict(PLAYBOOK_DEFAULTS["captcha"]),
        "verification": dict(PLAYBOOK_DEFAULTS["verification"]),
        "stop_conditions": list(PLAYBOOK_DEFAULTS["stop_conditions"]),
        "vault": {"domain": target + ".com", "password_via": "secure_card"},
        "notes": "",
    }
    return pb


def save_playbook(target: str, playbook: dict) -> str:
    path = os.path.join(BASE, "identity", "playbooks", f"{target}.yaml")
    with open(path, "w") as f:
        yaml.safe_dump(playbook, f, sort_keys=False, default_flow_style=False)
    return path


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 4 and sys.argv[1] == "brief":
        print(render_study_brief(sys.argv[2], sys.argv[3]))
    else:
        print("usage: auto_study.py brief <target> <signup_url>")
