"""DEEPHUNT identity matrix — Role x Object x Action x State (blueprint P0-2).

Systematically enumerates the authorization cross-product so the planner
tests *combinations* instead of guessing. Each cell becomes a differential
test proposal: control = the actor that SHOULD be allowed, variant = the
actor that should NOT.

Cells are priority-ranked, not blindly emitted:
  high    cross-role or cross-owner access to the same object+action
          (BOLA/BFLA/tenant-isolation surface)
  medium  state-dependent authorization (action valid in one state only)
  low     same-role sanity / already-covered combos (emitted only on demand)

Nothing here transmits. Output is proposal dicts for the experiment
planner; every proposal still goes through propose_test() + the hard gate.
"""
from __future__ import annotations

from typing import Dict, List, Optional

ACTIONS = ["create", "read", "update", "delete", "list", "transition"]

# Default lifecycle used when the world model has no object-specific states.
DEFAULT_STATES = ["created", "pending", "verified", "approved", "paid", "archived"]

# Actions that are state-sensitive in most business workflows.
STATE_SENSITIVE = {"update", "delete", "transition"}


def _roles(world_model) -> List[Dict]:
    m = world_model.model if world_model else {}
    roles = [{"name": r["name"], "privilege": r.get("privilege", 1)}
             for r in m.get("roles", [])]
    if not roles:
        roles = [{"name": n, "privilege": p} for n, p in
                 [("anonymous", 0), ("user", 1), ("admin", 2)]]
    return sorted(roles, key=lambda r: r["privilege"])


def _objects(world_model) -> List[Dict]:
    m = world_model.model if world_model else {}
    objs = []
    for o in m.get("objects", []):
        objs.append({
            "name": o["name"],
            "owner_role": o.get("owner_role", "unknown"),
            "states": o.get("lifecycle", {}).get("states", DEFAULT_STATES),
        })
    if not objs:
        objs = [{"name": "object", "owner_role": "user", "states": DEFAULT_STATES}]
    return objs


def _priority(role_a, role_b, action, state, owner_role) -> str:
    """Rank a control/variant cell without any network knowledge."""
    if role_a["name"] == role_b["name"]:
        return "low"
    # variant is LOWER privilege than control: the classic authz probe
    if role_b["privilege"] < role_a["privilege"]:
        if action in ("update", "delete") or owner_role not in ("unknown", role_b["name"]):
            return "high"
        return "medium"
    # variant is HIGHER privilege: detects missing function-level checks
    # only interesting for admin-gated actions probed as lower roles, which
    # is covered by the mirrored cell; keep low to avoid duplicates.
    if action in STATE_SENSITIVE:
        return "medium"
    return "low"


def generate(world_model=None, roles: Optional[List[str]] = None,
             min_priority: str = "medium") -> List[Dict]:
    """Enumerate the Role x Object x Action x State matrix.

    Returns proposal dicts, highest priority first. Each proposal carries
    control/variant identities so the differential engine can express it
    as a control/test pair.
    """
    order = {"high": 0, "medium": 1, "low": 2}
    want = order[min_priority]
    role_list = _roles(world_model)
    if roles:
        role_list = [r for r in role_list if r["name"] in roles] or role_list
    cells = []
    for obj in _objects(world_model):
        for action in ACTIONS:
            # bound the state dimension: test the riskiest two states plus
            # the current one when known
            states = obj["states"][:2]
            cur = obj.get("lifecycle", {}).get("current")
            if cur and cur not in states:
                states = [cur] + states[:1]
            for state in states:
                for i, ra in enumerate(role_list):
                    for rb in role_list[i + 1:]:
                        # two directed probes per unordered pair
                        for control, variant in ((ra, rb), (rb, ra)):
                            pri = _priority(control, variant, action, state,
                                            obj["owner_role"])
                            if order[pri] > want:
                                continue
                            cells.append({
                                "kind": "identity-matrix",
                                "priority": pri,
                                "role_control": control["name"],
                                "role_variant": variant["name"],
                                "object": obj["name"],
                                "action": action,
                                "state": state,
                                "dimension": "role-vs-role",
                                "statement": (
                                    f"{variant['name']} must not {action} "
                                    f"{obj['name']} in state {state} when "
                                    f"{control['name']} can"),
                                "oracle": "ownership_must_match_actor",
                                "decides": f"role-vs-role {action} on {obj['name']}",
                            })
    cells.sort(key=lambda c: (order[c["priority"]], c["object"], c["action"]))
    return cells


def to_differential(cell: Dict) -> Dict:
    """Express a matrix cell as a first-class control/test pair."""
    return {
        "dimension": cell["dimension"],
        "control": {
            "identity": cell["role_control"],
            "object": cell["object"],
            "action": cell["action"],
            "state": cell["state"],
            "expect": "allowed-or-denied-per-policy",
        },
        "test": {
            "identity": cell["role_variant"],
            "object": cell["object"],
            "action": cell["action"],
            "state": cell["state"],
            "expect": "denied",
        },
        "oracle": cell["oracle"],
        "decides": cell["decides"],
        "single_variable": True,  # only the identity differs
    }


def coverage_report(cells: List[Dict]) -> Dict:
    by_pri: Dict[str, int] = {}
    for c in cells:
        by_pri[c["priority"]] = by_pri.get(c["priority"], 0) + 1
    return {"cells": len(cells), "by_priority": by_pri,
            "objects": sorted({c["object"] for c in cells}),
            "actions": sorted({c["action"] for c in cells})}
