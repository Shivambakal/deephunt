#!/usr/bin/env python3
"""DEEPHUNT CLI — think, see, execute from the terminal.

Usage (from the deephunt/ directory):
  python3 cli.py status
  python3 cli.py start "robinhood,shopify,yahoo" 0
  python3 cli.py stop
  python3 cli.py targets
  python3 cli.py identities
  python3 cli.py sessions
  python3 cli.py findings
  python3 cli.py log 40
  python3 cli.py signup robinhood
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys
import time

import yaml

BASE = os.path.dirname(os.path.abspath(__file__))
PIDFILE = os.path.join(BASE, "state", "daemon.pid")
DAEMON_LOG = os.path.join(BASE, "logs", "daemon.out")


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def daemon_status() -> dict:
    if not os.path.exists(PIDFILE):
        return {"running": False}
    try:
        pid = int(open(PIDFILE).read().strip())
    except ValueError:
        return {"running": False}
    if not _alive(pid):
        return {"running": False, "stale_pid": pid}
    return {"running": True, "pid": pid,
            "uptime_s": int(time.time() - os.path.getmtime(PIDFILE))}


def current_activity() -> dict:
    """Parse the daemon log tail for what it's doing right now."""
    info = {"target": "?", "phase": "?", "last_line": ""}
    if not os.path.exists(DAEMON_LOG):
        return info
    with open(DAEMON_LOG, errors="replace") as f:
        lines = f.readlines()[-60:]
    for line in reversed(lines):
        if "DEEPHUNT starting: target=" in line:
            info["target"] = line.split("target=")[1].split(" ")[0]
        if "PHASE:" in line:
            info["phase"] = line.split("PHASE:")[1].strip()
            break
    if lines:
        info["last_line"] = lines[-1].strip()[-160:]
    return info


def cmd_status(_):
    s = daemon_status()
    a = current_activity()
    if not s["running"]:
        print("daemon: STOPPED")
        return
    up = s["uptime_s"]
    print(f"daemon: RUNNING (pid {s['pid']}, up {up // 3600}h {(up % 3600) // 60}m)")
    print(f"target: {a['target']} | phase: {a['phase']}")
    print(f"last: {a['last_line']}")


def cmd_start(args):
    subprocess.run([os.path.join(BASE, "deephunt.sh"), "start",
                    args.targets, str(args.hours)], check=False)


def cmd_stop(_):
    subprocess.run([os.path.join(BASE, "deephunt.sh"), "stop"], check=False)


def cmd_targets(_):
    for path in sorted(glob.glob(os.path.join(BASE, "targets", "*.yaml"))):
        name = os.path.basename(path)
        if name.startswith("_"):
            continue
        d = yaml.safe_load(open(path))
        hosts = d.get("scope_hosts", [])
        print(f"{d.get('name')}: {len(hosts)} scope hosts | "
              f"active={d.get('active_allowed')} | {d.get('program', '')[:70]}")


def cmd_identities(_):
    sys.path.insert(0, BASE)
    from identity.manager import list_all
    idents = list_all()
    if not idents:
        print("no test identities registered yet")
        return
    for t, i in idents.items():
        print(f"{t}: {i['email']} [{i['status']}] updated {i['updated_at'][:16]}")


def cmd_sessions(_):
    sess_dir = os.path.join(BASE, "..", "data", "brain", "sessions")
    files = sorted(glob.glob(os.path.join(sess_dir, "*.json")),
                   key=os.path.getmtime, reverse=True)[:10]
    if not files:
        print("no sessions found")
        return
    for f in files:
        try:
            d = json.load(open(f))
            obj = d.get("objective", "?")[:60]
            hyps = len(d.get("hypotheses", []))
            print(f"{os.path.basename(f)[:8]}: {obj} | {hyps} hypotheses")
        except Exception:
            print(f"{os.path.basename(f)}: unreadable")


def cmd_findings(_):
    found = []
    for pat in ("state/*finding*.json", "state/*finding*.md",
                "../intel/*finding*.md"):
        found += glob.glob(os.path.join(BASE, pat))
    if not found:
        print("no findings recorded yet")
        return
    for f in sorted(found, key=os.path.getmtime, reverse=True)[:10]:
        print(f)


def cmd_log(args):
    if not os.path.exists(DAEMON_LOG):
        print("no daemon log")
        return
    with open(DAEMON_LOG, errors="replace") as f:
        print("".join(f.readlines()[-args.n]), end="")


def cmd_signup(args):
    sys.path.insert(0, BASE)
    from identity import driver
    from identity.engine import start_run
    run = start_run(args.target, "signup")
    print(f"engine state: {run.state.value}")
    if run.state.value not in ("prefill",):
        print("run refused:", run.log[-1] if run.log else run.state.value)
        return
    print("=== PREFLIGHT ===")
    for c in driver.preflight(args.target):
        print(" -", c)
    print("\n=== BROWSER TASK BRIEF (feed to a live browser task) ===")
    print(driver.render_brief(args.target))


def cmd_signin(args):
    sys.path.insert(0, BASE)
    from identity import driver
    from identity.engine import start_run
    run = start_run(args.target, "signin")
    print(f"engine state: {run.state.value}")
    if run.state.value not in ("prefill",):
        print("run refused:", run.log[-1] if run.log else run.state.value)
        return
    print(driver.render_signin_brief(args.target))


def cmd_study(args):
    sys.path.insert(0, BASE)
    from identity import auto_study
    print(auto_study.render_study_brief(args.target, args.url))
    print("\n# After the study returns, save it with:")
    print(f"# python3 -c \"from identity.auto_study import save_playbook; ...\"")


def main():
    p = argparse.ArgumentParser(prog="deephunt", description="DEEPHUNT CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status")
    s = sub.add_parser("start")
    s.add_argument("targets", nargs="?", default="robinhood")
    s.add_argument("hours", nargs="?", type=float, default=0)
    sub.add_parser("stop")
    sub.add_parser("targets")
    sub.add_parser("identities")
    sub.add_parser("sessions")
    sub.add_parser("findings")
    l = sub.add_parser("log")
    l.add_argument("n", nargs="?", type=int, default=30)
    g = sub.add_parser("signup")
    g.add_argument("target")
    si = sub.add_parser("signin")
    si.add_argument("target")
    st = sub.add_parser("study")
    st.add_argument("target")
    st.add_argument("url")

    args = p.parse_args()
    {"status": cmd_status, "start": cmd_start, "stop": cmd_stop,
     "targets": cmd_targets, "identities": cmd_identities,
     "sessions": cmd_sessions, "findings": cmd_findings,
     "log": cmd_log, "signup": cmd_signup, "signin": cmd_signin,
     "study": cmd_study}[args.cmd](args)


if __name__ == "__main__":
    main()
