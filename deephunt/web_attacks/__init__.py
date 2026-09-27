"""DEEPHUNT web_attacks — web/API attack planners (propose-only).

Mirrors the ai_attacks/ package pattern:

- planner: each module exposes a planner function (``battery()`` /
  ``<x>_plan()`` / ``<x>_probes()``) that builds concrete test-case dicts
  from a target-agnostic ``surface`` dict. Every case carries a canary
  marker so a vulnerable target proves itself deterministically.
- scorer: each module exposes ``score(case, observation)`` returning
  {"verdict", "confidence", "signals", "evidence_artifacts"} with verdict
  in {"vulnerable", "not_vulnerable", "inconclusive"}. Scoring is
  deterministic arithmetic on the supplied observation — never on
  response codes alone where the technique card forbids it.

PROPOSE-ONLY: no network, no sockets, no subprocess, no filesystem
writes. The pipeline turns these cases into authorized tests via
propose_test() -> adversarial gate -> TestAuthorization ->
Engine.execute().

Target-agnostic: all target specifics arrive as function parameters.
Mocks/fixtures exist only inside the test files for self-verification.
"""
from __future__ import annotations

from .desync import desync_battery, score_desync
from .graphql_alias import alias_battery, score_alias
from .http2_race import race_plan, score_race
from .jwt_jku import jku_battery, score_jku_stage1, score_jku_stage2
from .desync_timing import timing_probes, score_timing
from .proto_pollution import pollution_probe, score_pollution
from .oauth_identity import identity_probes, score_identity
from .raced_idor import raced_idor_plan, score_raced_idor
from .integrate import (
    detect_web_surfaces,
    seed_hypotheses,
    expand_tests,
)

__all__ = [
    "desync_battery", "score_desync",
    "alias_battery", "score_alias",
    "race_plan", "score_race",
    "jku_battery", "score_jku_stage1", "score_jku_stage2",
    "timing_probes", "score_timing",
    "pollution_probe", "score_pollution",
    "identity_probes", "score_identity",
    "raced_idor_plan", "score_raced_idor",
    "detect_web_surfaces", "seed_hypotheses", "expand_tests",
]
