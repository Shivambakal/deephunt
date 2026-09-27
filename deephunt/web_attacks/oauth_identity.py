"""W1-017 OAuth identity-resolution probe (mutable-attribute confusion).

Tests whether the relying party resolves identity by IMMUTABLE subject
(sub) or by mutable attributes (display name, email). Two owned
accounts with distinct immutable subjects but colliding display names —
or an email-change rebinding — reveal the confusion.

False-positive discipline: display-name-only UI confusion without
privilege inheritance is NOT account takeover; require the attacker
session to carry the victim's internal user_id / privileges.

PROPOSE-ONLY: account-creation and login steps only, on owned accounts.
"""
from __future__ import annotations

from typing import Dict, List

from .common import base_case, verdict

CARD = "W1-017"


def identity_probes(surface: dict) -> List[Dict]:
    """Build identity-resolution probe cases.

    surface: {"kind": "oauth", "name": str, "provider": str,
              "relying_party": str}
    """
    canary = "dh_idconf"
    mk = lambda cid, desc, vuln, safe, steps: base_case(  # noqa: E731
        cid, "oauth_identity", CARD, "send_sequence", canary, vuln, safe,
        steps=steps, description=desc,
        controls=("record both accounts' immutable subjects and user_ids "
                  "before any collision; accounts must be clearly distinct"))
    return [
        mk("OAUTH-ID-001",
           "display-name collision: victim caches under name N; attacker "
           "registers with display name exactly N and logs in.",
           "Attacker session carries the VICTIM's internal user_id and "
           "privileges (performs a victim-only action).",
           "Name collision creates a separate account, or identity "
           "resolves strictly by immutable subject.",
           ["create victim account; record sub_v, user_id_v",
            "create attacker account; set display name == victim's; record sub_a",
            "log in as attacker; read session user_id and privilege set",
            "attempt a victim-only action with the attacker session"]),
        mk("OAUTH-ID-002",
           "email-change rebinding: attacker changes their account email "
           "to the victim's email, then re-authenticates via the provider.",
           "Post-change session is bound to the victim's account "
           "(victim user_id in attacker session).",
           "Email change re-verifies ownership; sessions stay bound to "
           "the original subject.",
           ["create victim and attacker accounts with distinct emails",
            "attacker changes account email to victim's email",
            "attacker re-authenticates via OAuth provider",
            "read resolved user_id on the attacker session"]),
    ]


def score_identity(case: dict, observation: dict) -> Dict:
    """Score identity-resolution observation.

    observation: {"victim_user_id": str, "attacker_sub": str,
                  "victim_sub": str,
                  "attacker_session_user_id": str,
                  "victim_only_action_succeeded": bool,
                  "baselines_ok": bool}
    """
    signals: List[str] = []
    vid = str(observation.get("victim_user_id", ""))
    sid = str(observation.get("attacker_session_user_id", ""))
    vsub = str(observation.get("victim_sub", ""))
    asub = str(observation.get("attacker_sub", ""))
    acted = bool(observation.get("victim_only_action_succeeded", False))
    baselines = bool(observation.get("baselines_ok", False))
    signals.append(f"session_user_id:{sid or '?'}")
    signals.append(f"distinct_subjects:{bool(vsub and asub and vsub != asub)}")

    artifacts = {
        "privilege_inheritance_observed": (sid == vid and bool(vid)) or acted,
        "distinct_accounts_verified": baselines and vsub != asub,
        "immutable_subject_control": bool(vsub and asub),
    }

    if not baselines or not vsub or not asub:
        return verdict("inconclusive", 0.3,
                       signals + ["baselines_unverified"], artifacts)
    if vsub == asub:
        return verdict("inconclusive", 0.35,
                       signals + ["accounts_not_distinct"], artifacts)
    if (sid == vid and vid) or acted:
        return verdict("vulnerable", 0.9,
                       signals + ["identity_confusion_ato"], artifacts)
    return verdict("not_vulnerable", 0.75,
                   signals + ["identity_resolves_by_subject"], artifacts)
