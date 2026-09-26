"""DEEPHUNT tool pool — one arsenal for all agent teams.

Wraps the tool registry (hand-built adapters + the tools-100 generics) and
presents it per-team. Built to scale: adapters are data + lazy classes, so
the pool grows from today's ~90 toward the 1000-tool target by adding
registry rows, never rewiring callers.
"""
from __future__ import annotations

try:
    from tools import list_tools
    from tools.t100 import REGISTERED_100
    from tools100 import TOOLS100
except ImportError:  # pragma: no cover
    from .tools import list_tools
    from .tools.t100 import REGISTERED_100
    from .tools100 import TOOLS100

_T100CAT = {t[0]: t[1] for t in TOOLS100}

# team -> which tool categories it draws
TEAM_CATEGORIES = {
    "recon": {"recon", "discovery"},
    "webapi": {"discovery", "vuln", "api", "protocol", "fuzz"},
    "logic": {"vuln", "api", "protocol"},
}


class ToolPool:
    """The shared arsenal. Teams check out tools; the pool tracks the count."""

    def __init__(self):
        self._tools = list_tools()
        self._by_name = {t.name: t for t in self._tools}

    def category_of(self, tool):
        n = tool.name
        if n.startswith("t100-"):
            return _T100CAT.get(n[5:], "t100")
        return "core"

    def for_team(self, team, only_available=True):
        cats = TEAM_CATEGORIES[team]
        out = []
        for t in self._tools:
            if team == "recon" and t.phase != "passive":
                continue
            if team in ("webapi", "logic") and t.phase != "active":
                continue
            if self.category_of(t) not in cats and self.category_of(t) != "core":
                continue
            if only_available:
                try:
                    if not t.available():
                        continue
                except Exception:
                    continue
            out.append(t)
        return out

    def get(self, name):
        return self._by_name.get(name)

    def stats(self):
        by_phase, by_cat, avail = {}, {}, 0
        for t in self._tools:
            by_phase[t.phase] = by_phase.get(t.phase, 0) + 1
            c = self.category_of(t)
            by_cat[c] = by_cat.get(c, 0) + 1
            try:
                if t.available():
                    avail += 1
            except Exception:
                pass
        return {"total": len(self._tools), "available": avail,
                "by_phase": by_phase, "by_category": by_cat,
                "target_capacity": 1000}
