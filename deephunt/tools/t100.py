"""DEEPHUNT tools-100 generic adapters — data becomes weapons.

For every tools100.py entry that (a) has no hand-built adapter and
(b) is auto-runnable (passive/active phase), this factory builds a real
ToolAdapter: availability is detected from the project bin dirs + PATH,
and run() executes the templated command with the target substituted.

A tool becomes live in the hunt the moment its binary is installed —
no code changes. `available()` keeps uninstalled tools out of every run.
"""
from __future__ import annotations
import os
import re

from .base import ToolAdapter, register, sh
try:
    from tools100 import TOOLS100  # deephunt/ on sys.path
except ImportError:  # pragma: no cover
    from ..tools100 import TOOLS100

BIN_DIRS = [
    os.path.expanduser("~/workspace/hacker-agent/bin"),
    os.path.expanduser("~/workspace/hacker-agent/ops/bin"),
]

PASSIVE_TIMEOUT = 180
ACTIVE_TIMEOUT = 600


def _which(binary):
    for d in BIN_DIRS:
        p = os.path.join(d, binary)
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    rc, out, _ = sh(f"command -v {binary}")
    if rc == 0 and out.strip():
        return out.strip().split("\n")[0]
    return None


def _root_domain(host):
    parts = (host or "").split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def _inputs(ctx):
    profile = ctx.get("profile", {})
    hosts = profile.get("scope_hosts", []) or [profile.get("name", "")]
    host = (hosts[0] if hosts else "").strip()
    zones = profile.get("ct_zones", [])
    domain = zones[0] if zones else _root_domain(host)
    url = f"https://{host}" if host and not host.startswith("http") else host
    return {"domain": domain, "url": url, "host": host}


def _make_adapter(entry):
    name, category, phase, binary, takes, args_t, install, desc = entry[:8]
    covered = entry[8] if len(entry) > 8 else ""

    class Generic100(ToolAdapter):
        pass

    Generic100.name = f"t100-{name}"
    Generic100.phase = phase
    Generic100.description = f"[tools-100/{category}] {desc} :: install: {install}"
    Generic100.needs_bins = ()

    def available(self, _b=binary):
        return _which(_b) is not None

    def run(self, ctx, _e=entry):
        _name, _cat, _phase, _binary, _takes, _args_t, _install, _desc = _e[:8]
        exe = _which(_binary)
        if not exe:
            return []
        inp = _inputs(ctx)
        if _takes in ("domain", "url", "host") and not inp.get(_takes):
            return [self.finding("error", f"t100-{_name}: no {_takes} in scope",
                                 "profile has no usable scope_hosts")]
        cmd = _args_t
        for k, v in inp.items():
            cmd = cmd.replace("{" + k + "}", v or "")
        cmd = re.sub(r"\s+", " ", cmd).strip()
        timeout = ACTIVE_TIMEOUT if _phase == "active" else PASSIVE_TIMEOUT
        rc, out, err = sh(f"{exe} {cmd}", timeout=timeout)
        body = (out or err or "")[:6000]
        if rc == 124:
            return [self.finding("error", f"t100-{_name}: timed out",
                                 f"cmd: {_binary} {cmd[:120]}")]
        lines = [l for l in body.splitlines() if l.strip()][:40]
        kind = "inventory" if _phase == "passive" else "probe"
        return [self.finding(
            kind, f"t100-{_name}: completed (rc={rc})",
            detail="\n".join(lines)[:3000],
            evidence=f"category={_cat} cmd={_binary} {cmd[:160]}")]

    Generic100.available = available
    Generic100.run = run
    Generic100.__name__ = f"T100_{name.replace('-', '_')}"
    register(Generic100)  # register AFTER the name is set
    return Generic100


REGISTERED_100 = []
for _entry in TOOLS100:
    _p, _covered = _entry[2], (_entry[8] if len(_entry) > 8 else "")
    if _covered:      # hand-built adapter already exists — no duplicate
        continue
    if _p in ("manual", "resource"):  # human-driven or not a runner
        continue
    REGISTERED_100.append(_make_adapter(_entry))


def availability_report():
    """Which of the 100 are installed right now."""
    rows = []
    for e in TOOLS100:
        name, cat, phase, binary = e[0], e[1], e[2], e[3]
        rows.append({"name": name, "category": cat, "phase": phase,
                     "installed": _which(binary) is not None,
                     "covered": bool(e[8]) if len(e) > 8 else False})
    return rows
