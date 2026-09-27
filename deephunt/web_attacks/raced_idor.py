"""F1 raced-IDOR combo: IDOR probe raced against revocation.

The combination oracle: an attacker request dispatched AFTER the
revocation completed still returns 200 with the victim's data —
proving a TOCTOU gap in the revocation path, not just plain IDOR.

PROPOSE-ONLY: timing schedule and read plan only, on owned accounts.
"""
from __future__ import annotations

from typing import Dict, List

from .common import base_case, verdict

CARD = "F1-001"


def raced_idor_plan(surface: dict) -> List[Dict]:
    """Build the raced-IDOR test plan.

    surface: {"kind": "idor", "name": str, "object_endpoint": str,
              "revoke_endpoint": str}
    """
    canary = "dh_raced"
    return [base_case(
        "RACE-IDOR-001", "raced_idor", CARD, "send_sequence", canary,
        ("Attacker read dispatched after revocation COMPLETED returns 200 "
         "with the victim's object data — revocation authorization is "
         "TOCTOU-broken."),
        ("Post-revocation reads return 403/404, or the raced read only "
         "succeeds when sent before revocation completed."),
        object_endpoint=surface.get("object_endpoint", "/objects/{id}"),
        revoke_endpoint=surface.get("revoke_endpoint", "/objects/{id}/share"),
        schedule=[
            "victim creates object O; shares it with attacker account",
            "attacker confirms baseline read of O (200)",
            "victim revokes the share; record revocation_completed_at",
            "attacker dispatches N parallel reads of O at t0+delta "
            "(delta from 0ms to 5s)",
            "each read: record sent_at, status, and whether victim data returned",
        ],
        controls=("control read by the victim after revocation still 200; "
                  "control read by a never-shared third account is 403"),
        oracle="revocation_authz_toctou: sent_at > revocation_completed_at "
               "AND status == 200 AND victim data present")]


def score_raced_idor(case: dict, observation: dict) -> Dict:
    """Score raced-IDOR observations.

    observation: {"revocation_completed_at": float,
                  "raced_reads": [{"sent_at": float, "status": int,
                                   "victim_data": bool}],
                  "control_victim_ok": bool, "control_third_denied": bool}
    """
    signals: List[str] = []
    t0 = float(observation.get("revocation_completed_at", 0))
    reads = list(observation.get("raced_reads") or [])
    post = [r for r in reads
            if float(r.get("sent_at", 0)) > t0 and int(r.get("status", 0)) == 200
            and bool(r.get("victim_data", False))]
    signals.append(f"post_revocation_200_with_data:{len(post)}/{len(reads)}")

    artifacts = {
        "post_revocation_200_with_victim_data": len(post) > 0,
        "revocation_authz_toctou": len(post) > 0,
        "control_victim_still_ok": bool(observation.get("control_victim_ok", False)),
        "control_third_denied": bool(observation.get("control_third_denied", False)),
    }

    if post:
        return verdict("vulnerable", 0.88,
                       signals + ["revocation_window_exploited"], artifacts)
    if not reads:
        return verdict("inconclusive", 0.3,
                       signals + ["no_reads_recorded"], artifacts)
    return verdict("not_vulnerable", 0.75,
                   signals + ["revocation_effective"], artifacts)
