"""DEEPHUNT P1 bench — mock vulnerable targets (in-process, no network).

Each mock simulates one app surface with a planted P1 vulnerability (plus a
patched variant as the negative control). The pipeline under test probes
them ONLY through probe(action, params); there is no network, no real
system, no real user data anywhere in this package.

Mock contract:
  probe(action, params) -> (status:int, data:dict, state_delta:dict)
  reset()               -> restore initial state (deterministic re-runs)
  ground_truth()        -> {"vulnerable", "technique", "location", "impact",
                            "root_cause"}
  surface_brief()       -> free-text surface description (world-model seeding)
  seed_world(wm)        -> structured world-model seeding
                          (identities/objects/endpoints/lifecycle/boundaries/
                          invariants)
  bench_seeds()         -> attack hypothesis seeds, each carrying a
                           "bench_plan" with setup/control/test probe
                           sequences, the oracle invariant to check, the
                           expected security property, technique id, and
                           alternative explanations with disproof probes.
  negative_seeds()      -> benign/distractor seeds: behaviors that must NOT
                           become findings (false-positive discipline).
  weak_probes()         -> deliberate weak-evidence candidates used as
                           negative controls for the independent verifier
                           (missing evidence artifacts -> must be REJECTED).

Param templating: a param value of "$setup.<i>.<key>" is resolved from the
data dict returned by setup step i (e.g. "$setup.0.order_id").
"""
from __future__ import annotations

import json
from typing import Dict, List, Tuple


def fmt_observation(action: str, params: dict, status: int,
                    data: dict, state_delta: dict) -> str:
    """Render one probe as the observation text the pipeline stages read.

    The "HTTP <status>" line is load-bearing: verifier._precondition_audit
    keys off it, and the oracles parse status classes from it.
    """
    return (
        f"HTTP {status}\n"
        f"action: {action}\n"
        f"params: {json.dumps(params, sort_keys=True)}\n"
        f"body: {json.dumps(data, sort_keys=True)}\n"
        f"state: {json.dumps(state_delta, sort_keys=True)}"
    )


def resolve_params(params: dict, setup_results: List[dict]) -> dict:
    """Resolve "$setup.<i>.<key>" templates against setup step results."""
    out = {}
    for k, v in (params or {}).items():
        if isinstance(v, str) and v.startswith("$setup."):
            _, idx, *rest = v.split(".")
            data = setup_results[int(idx)]
            for part in rest:
                data = data.get(part, {}) if isinstance(data, dict) else {}
            out[k] = data
        else:
            out[k] = v
    return out


class MockTarget:
    """Base class. Subclasses implement the surface; variants flip `patched`."""

    name = "mock"
    display = "mock target"

    def __init__(self, patched: bool = False):
        self.patched = patched
        self.reset()

    # ---- interface ----
    def reset(self):
        raise NotImplementedError

    def probe(self, action: str, params: dict) -> Tuple[int, dict, dict]:
        raise NotImplementedError

    def ground_truth(self) -> dict:
        raise NotImplementedError

    def surface_brief(self) -> str:
        raise NotImplementedError

    def seed_world(self, wm):
        raise NotImplementedError

    def bench_seeds(self) -> List[dict]:
        raise NotImplementedError

    def negative_seeds(self) -> List[dict]:
        return []

    def weak_probes(self) -> List[dict]:
        return []

    # ---- shared helpers ----
    def actions(self) -> List[str]:
        return sorted(self._actions)

    @property
    def label(self) -> str:
        return f"{self.name}:{'patched' if self.patched else 'vuln'}"
