"""Test identity registry — metadata only, never credentials.

Email convention: attacksurface.alerts+<target>@gmail.com (plus-addressing on
the dedicated research mailbox keeps every target's mail separable).
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

REGISTRY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "state", "identities.json")
RESEARCH_MAILBOX = "attacksurface.alerts@gmail.com"

# Statuses: planned -> signing_up -> verifying -> active -> blocked -> retired
VALID_STATUSES = {"planned", "signing_up", "verifying", "active", "blocked", "retired"}


def email_for(target: str) -> str:
    local, _, domain = RESEARCH_MAILBOX.partition("@")
    return f"{local}+{target}@{domain}"


def _load() -> dict:
    if os.path.exists(REGISTRY):
        with open(REGISTRY) as f:
            return json.load(f)
    return {"identities": {}}


def _save(data: dict) -> None:
    os.makedirs(os.path.dirname(REGISTRY), exist_ok=True)
    tmp = REGISTRY + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, REGISTRY)


def register(target: str, status: str = "planned", notes: str = "") -> dict:
    """Register (or update) a test identity's metadata. No secrets accepted."""
    if status not in VALID_STATUSES:
        raise ValueError(f"bad status {status!r}")
    data = _load()
    ident = data["identities"].get(target, {})
    ident.update({
        "target": target,
        "email": email_for(target),
        "mailbox": RESEARCH_MAILBOX,
        "status": status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "notes": notes or ident.get("notes", ""),
        "created_at": ident.get("created_at",
                                datetime.now(timezone.utc).isoformat()),
        # Explicit: the password lives ONLY in the Secure Vault.
        "credential_location": "Secure Vault (vault domain: see playbook)",
    })
    data["identities"][target] = ident
    _save(data)
    return ident


def get(target: str) -> dict | None:
    return _load()["identities"].get(target)


def set_status(target: str, status: str, notes: str = "") -> dict:
    if status not in VALID_STATUSES:
        raise ValueError(f"bad status {status!r}")
    data = _load()
    if target not in data["identities"]:
        raise KeyError(f"no identity registered for {target!r}")
    data["identities"][target]["status"] = status
    data["identities"][target]["updated_at"] = datetime.now(timezone.utc).isoformat()
    if notes:
        data["identities"][target]["notes"] = notes
    _save(data)
    return data["identities"][target]


def list_all() -> dict:
    return _load()["identities"]


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        for t, i in list_all().items():
            print(f"{t}: {i['email']} [{i['status']}]")
    else:
        print("usage: manager.py list")
