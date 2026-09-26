"""DEEPHUNT strategy — the CEO's battle plan.

Chooses where to spend the tool budget (recon vs web/api vs logic depth)
from the live world model + episodic memory, not from vibes. Returns a
plan dict the CEO hands to the agent teams.
"""
from __future__ import annotations


class Strategy:
    def choose(self, wm, mem, profile, pool):
        m = getattr(wm, "model", {}) or {}
        n_identities = len(m.get("identities", []) or [])
        n_objects = len(m.get("objects", []) or [])
        n_services = len(m.get("services", []) or [])
        n_anomalies = len(m.get("anomalies", []) or [])
        episodes = mem.count() if hasattr(mem, "count") else 0

        # Heuristic weights: breadth first, then depth where the model is rich.
        w_recon, w_webapi, w_logic = 5, 3, 2
        if n_services >= 5 or n_objects >= 10:
            w_recon, w_webapi, w_logic = 3, 5, 4   # surface mapped -> attack it
        if n_anomalies >= 3 or episodes >= 20:
            w_recon, w_webapi, w_logic = 2, 4, 6   # anomalies -> logic depth
        if n_identities >= 2 and n_objects >= 5:
            w_logic += 2                            # authz graph worth testing
        total = w_recon + w_webapi + w_logic

        stats = pool.stats()
        plan = {
            "focus": {
                "recon": round(w_recon / total, 2),
                "webapi": round(w_webapi / total, 2),
                "logic": round(w_logic / total, 2),
            },
            "depth": "deep" if (n_anomalies >= 3 or episodes >= 20) else "broad",
            "tool_budget": {
                "recon": len(pool.for_team("recon")),
                "webapi": len(pool.for_team("webapi")),
                "logic": len(pool.for_team("logic")),
            },
            "pool": stats,
            "rationale": (
                f"identities={n_identities} objects={n_objects} "
                f"services={n_services} anomalies={n_anomalies} "
                f"episodes={episodes} -> "
                f"recon {w_recon} / webapi {w_webapi} / logic {w_logic}"
            ),
        }
        return plan
