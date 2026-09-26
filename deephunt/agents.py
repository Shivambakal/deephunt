"""DEEPHUNT agent teams — recon, web/api, logic.

Three specialist teams under the CEO, all drawing from the shared ToolPool.
Each team runs its tools through the recovery wrapper (resilient + circuit
breaker) and returns findings. Web/api and logic teams are structurally
gated: with active_allowed=false they run zero tools and say so.
"""
from __future__ import annotations

try:
    from recovery import resilient, CircuitBreaker
except ImportError:  # pragma: no cover
    from .recovery import resilient, CircuitBreaker


class BaseAgent:
    team = "base"

    def __init__(self, pool, ctx):
        self.pool = pool
        self.ctx = ctx
        self.breaker = CircuitBreaker()

    def tools(self):
        return self.pool.for_team(self.team)

    def _run_tool(self, tool):
        name = tool.name
        if self.breaker.quarantined(name):
            return []
        ok, res = resilient(lambda: tool.run(self.ctx),
                            retries=1, label=name)
        self.breaker.record(name, ok)
        if not ok:
            return [{"tool": name, "phase": tool.phase, "kind": "error",
                     "title": f"{self.team}: {name} failed",
                     "detail": str(res)[:300]}]
        return res or []

    def run(self):
        raise NotImplementedError


class ReconAgent(BaseAgent):
    """Mapping, never attacking. Passive tools only."""
    team = "recon"

    def run(self):
        out = []
        for t in self.tools():
            for f in self._run_tool(t):
                f.setdefault("team", "recon")
                out.append(f)
        return out


class WebAPIAgent(BaseAgent):
    """Active web/API/fuzz tools. Hard-gated by active_allowed."""
    team = "webapi"

    def run(self):
        if not self.ctx.get("profile", {}).get("active_allowed", False):
            return [{"tool": "ceo-gate", "phase": "active", "kind": "skipped",
                     "title": "webapi team stood down",
                     "detail": "active_allowed=false — zero active tools ran"}]
        out = []
        for t in self.tools():
            for f in self._run_tool(t):
                f.setdefault("team", "webapi")
                out.append(f)
        return out


class LogicAgent(BaseAgent):
    """Logic-flaw team: differential designs + chain hypotheses.

    Designs controlled experiments (control vs variant) instead of spraying
    tools. Execution of each design is itself a gated active step.
    """
    team = "logic"

    def run(self, hypotheses=()):
        designs = []
        try:
            try:
                from differential import design as diff_design
            except ImportError:  # pragma: no cover
                from .differential import design as diff_design
            wm = self.ctx.get("wm")
            for h in list(hypotheses)[:6]:
                stmt = h.get("statement") if isinstance(h, dict) else str(h)
                try:
                    ds = diff_design(stmt, wm) if wm else []
                except Exception:
                    ds = []
                for d in ds:
                    designs.append({
                        "tool": "logic-design", "phase": "active",
                        "kind": "experiment_design", "team": "logic",
                        "title": f"logic experiment: {d.get('name', stmt[:60])}",
                        "detail": str(d)[:1500]})
        except Exception as e:  # noqa: BLE001
            designs.append({"tool": "logic-design", "phase": "active",
                            "kind": "error", "team": "logic",
                            "title": "logic design failed", "detail": str(e)[:300]})
        if not self.ctx.get("profile", {}).get("active_allowed", False):
            for d in designs:
                d["detail"] = "[HELD: active_allowed=false] " + d.get("detail", "")
            return designs
        # active allowed: run the logic team's own probe tools too
        out = list(designs)
        for t in self.tools():
            for f in self._run_tool(t):
                f.setdefault("team", "logic")
                out.append(f)
        return out
