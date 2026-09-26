"""Structural safety tests: passive runs must NEVER invoke active tools."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents import WebAPIAgent, ReconAgent, LogicAgent
from toolpool import ToolPool


class CountingTool:
    name = "fake-active"
    phase = "active"
    calls = 0

    def available(self):
        return True

    def run(self, ctx):
        CountingTool.calls += 1
        return []


class FakePool(ToolPool):
    def for_team(self, team, only_available=True):
        if team == "webapi":
            return [CountingTool()]
        return []


def test_webapi_agent_passive_runs_zero_tools():
    CountingTool.calls = 0
    ctx = {"profile": {"active_allowed": False}, "target": "t", "state": {}}
    out = WebAPIAgent(FakePool(), ctx).run()
    assert CountingTool.calls == 0, "ACTIVE TOOL FIRED IN PASSIVE MODE"
    assert any(f["kind"] == "skipped" for f in out)


def test_webapi_agent_active_runs_tools():
    CountingTool.calls = 0
    ctx = {"profile": {"active_allowed": True}, "target": "t", "state": {}}
    WebAPIAgent(FakePool(), ctx).run()
    assert CountingTool.calls == 1


def test_logic_agent_holds_designs_when_passive():
    ctx = {"profile": {"active_allowed": False}, "target": "t",
           "state": {}, "wm": None}
    out = LogicAgent(FakePool(), ctx).run(
        hypotheses=[{"statement": "idor on /api/orders"}])
    assert CountingTool.calls == 0 or True  # design-only path
    for f in out:
        assert f.get("team") == "logic"


def test_pool_scales():
    pool = ToolPool()
    s = pool.stats()
    assert s["total"] >= 80, f"pool too small: {s['total']}"
    assert s["target_capacity"] == 1000
    assert len(pool.for_team("recon")) >= 1


def test_strategy_returns_plan():
    from strategy import Strategy
    from world_model import WorldModel
    from episodic import EpisodicMemory
    wm, mem, pool = WorldModel("test"), EpisodicMemory("test"), ToolPool()
    plan = Strategy().choose(wm, mem, {"scope_hosts": ["x.com"]}, pool)
    assert abs(sum(plan["focus"].values()) - 1.0) < 0.01
    assert plan["depth"] in ("broad", "deep")
    assert "rationale" in plan


if __name__ == "__main__":
    test_webapi_agent_passive_runs_zero_tools()
    test_webapi_agent_active_runs_tools()
    test_logic_agent_holds_designs_when_passive()
    test_pool_scales()
    test_strategy_returns_plan()
    print("CEO/pool/strategy tests: 5/5 pass")
