"""DEEPHUNT operator adapters — steps that need the agent/browser, emitted as
precise task briefs instead of executed. The loop never silently skips them."""
from __future__ import annotations
import os

from .base import ToolAdapter, register, now


@register
class BrowserProbe(ToolAdapter):
    name = "browser_probe"
    phase = "operator"
    description = "Emit a precise browser-task brief for app-layer probing"

    def run(self, ctx):
        prof = ctx["profile"]
        brief = prof.get("operator_brief")
        if not brief:
            return [self.finding(
                "operator-task", "no operator brief defined",
                "add operator_brief to the target profile")]
        path = os.path.join(ctx["state_dir"],
                            f"operator_task_{now().replace(':','-')}.md")
        with open(path, "w") as f:
            f.write(f"# OPERATOR TASK — {ctx['target']} ({now()})\n\n{brief}\n")
        return [self.finding(
            "operator-task", f"browser brief written: {os.path.basename(path)}",
            detail=brief[:1200], evidence=path)]
