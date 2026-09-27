"""DEEPHUNT web_attacks integration — hypothesis seeds + experiment expansion.

Bridges the web_attacks planners into the ATTACKSURFACE pipeline:
  - detect_web_surfaces(ti): find web/API surfaces from target intel.
    Target-agnostic.
  - seed_hypotheses(target, ti): hypothesis seeds in the exact shape
    hypothesis_fusion.fuse() expects. Pure data — no transmission.
  - expand_tests(hypothesis, surface): turn one web hypothesis into
    concrete test-case dicts. Pure data — the pipeline still routes every
    test through propose_test() -> TestAuthorization -> Engine.execute().

Nothing here transmits. Mocks exist only in tests.
"""
from __future__ import annotations

from typing import Dict, List

from . import desync
from . import graphql_alias
from . import http2_race
from . import jwt_jku
from . import desync_timing
from . import proto_pollution
from . import oauth_identity
from . import raced_idor

# Signals that a target exposes testable web/API surfaces, matched
# case-insensitively against technology names and observation text.
WEB_SIGNALS = [
    "http", "https", "rest", "api", "graphql", "oauth", "jwt", "web",
    "frontend", "backend", "proxy", "cdn", "load balancer", "http/2",
    "h2", "nginx", "apache", "haproxy", "varnish", "cloudfront",
]

_KIND_HINTS = [
    (("graphql",), "graphql"),
    (("oauth", "oidc", "sso"), "oauth"),
    (("jwt", "jwk", "jku"), "jwt"),
    (("http/2", "h2"), "http2"),
]

_PLANNERS = {
    "desync": (desync.desync_battery, "web_attacks:desync",
               "W1-001", "CL.0/0.CL request-desync probes"),
    "graphql_alias": (graphql_alias.alias_battery, "web_attacks:graphql_alias",
                      "W1-021", "GraphQL alias-batching rate-limit probes"),
    "http2_race": (http2_race.race_plan, "web_attacks:http2_race",
                   "W1-031", "single-packet HTTP/2 race plans"),
    "jwt_jku": (jwt_jku.jku_battery, "web_attacks:jwt_jku",
                "C1-007", "JWT jku/x5u two-stage probes"),
    "desync_timing": (desync_timing.timing_probes, "web_attacks:desync_timing",
                      "C1-016", "CL.TE/TE.CL timing-differential probes"),
    "proto_pollution": (proto_pollution.pollution_probe,
                        "web_attacks:proto_pollution",
                        "C1-014", "prototype-pollution json-spaces probe"),
    "oauth_identity": (oauth_identity.identity_probes,
                       "web_attacks:oauth_identity",
                       "W1-017", "OAuth identity-resolution probes"),
    "raced_idor": (raced_idor.raced_idor_plan, "web_attacks:raced_idor",
                   "F1-001", "raced-IDOR revocation-window plans"),
}


def detect_web_surfaces(ti) -> List[dict]:
    """Infer web/API surfaces from a TargetIntel-like object."""
    texts: List[str] = []
    try:
        texts.extend(ti.technologies())
    except Exception:
        pass
    try:
        texts.extend(str(o) for o in (ti.target.data.get("observations") or [])[-40:])
    except Exception:
        pass
    blob = " ".join(texts).lower()
    hits = sorted({s for s in WEB_SIGNALS if s in blob})
    if not hits:
        return []
    kinds = set()
    for hints, k in _KIND_HINTS:
        if any(h in blob for h in hints):
            kinds.add(k)
    kinds.add("http")
    target_name = getattr(getattr(ti, "target", None), "name", None) or "target"
    surfaces = []
    for kind in sorted(kinds):
        surfaces.append({
            "kind": kind,
            "name": f"{target_name} web surface",
            "paths": ["/"],
            "signals": hits,
        })
    return surfaces


def _seed(statement: str, source: str, score: float, provenance: str,
          investigator_test: str, violated: str = "",
          impact: int = 4, novelty: int = 4) -> dict:
    return {
        "statement": statement,
        "source": source,
        "score": score,
        "investigator_test": investigator_test[:300],
        "violated_assumption": violated,
        "attacker_view": "",
        "devil_view": "",
        "impact": impact,
        "novelty": novelty,
        "provenance": provenance,
    }


def seed_hypotheses(target: str, ti) -> List[dict]:
    """Generate web-attack hypothesis seeds for the pipeline. Pure data."""
    surfaces = detect_web_surfaces(ti)
    if not surfaces:
        return []
    seeds: List[dict] = []
    for s in surfaces:
        kind, sigs = s["kind"], ", ".join(s["signals"][:6])
        base = f"[{target}] web surface ({kind}; signals: {sigs})"
        for mod, (planner, source, card, desc) in _PLANNERS.items():
            if mod == "graphql_alias" and kind != "graphql":
                continue
            if mod == "oauth_identity" and kind != "oauth":
                continue
            if mod == "jwt_jku" and kind != "jwt":
                continue
            if mod == "http2_race" and kind != "http2":
                continue
            try:
                n = len(planner(s))
            except Exception:
                n = 0
            seeds.append(_seed(
                f"{base}: {desc} — {n} probe case(s) generated",
                source, 4.0,
                f"web_attacks seed; {n} cases; card {card}",
                f"Propose {mod} cases through authorized proposals; "
                f"vulnerable only if the card's deterministic oracle holds.",
                violated=_violated(mod)))
    return seeds


def _violated(mod: str) -> str:
    return {
        "desync": "front-end and back-end agree on request framing",
        "graphql_alias": "rate limits count operations, not HTTP requests",
        "http2_race": "single-use operations cannot be applied twice",
        "jwt_jku": "key URLs are not attacker-controlled",
        "desync_timing": "ambiguous framing is rejected, not parsed",
        "proto_pollution": "client JSON cannot alter server-wide behavior",
        "oauth_identity": "identity resolves by immutable subject",
        "raced_idor": "revocation takes effect before further reads",
    }.get(mod, "")


def expand_tests(hypothesis: dict, surface: dict) -> List[dict]:
    """Expand one web hypothesis into concrete test-case dicts."""
    src = (hypothesis.get("source") or "")
    stmt = hypothesis.get("statement") or ""
    low = (src + " " + stmt).lower()
    cases: List[dict] = []
    for mod, (planner, source, card, _desc) in _PLANNERS.items():
        if mod in low or card.lower() in low:
            try:
                for c in planner(surface):
                    c["hypothesis_id"] = hypothesis.get("id")
                    c["technique_card"] = card
                    cases.append(c)
            except Exception:
                continue
    return cases[:25]
