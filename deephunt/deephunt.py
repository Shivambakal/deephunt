#!/usr/bin/env python3
"""DEEPHUNT — give it a target name, it hunts until it learns or wins.

Usage:
  python3 deephunt.py --target adobe [--max-cycles 3] [--passive-only]
  python3 deephunt.py --list-tools [--phase passive|active|operator]
  python3 deephunt.py --learn [--target adobe]
  python3 deephunt.py --target adobe --daemon --interval-hours 6
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator import run_target  # noqa: E402
from tools import list_tools  # noqa: E402
from tools.base import now  # noqa: E402
import learn  # noqa: E402


def run_forever(targets, max_cycles, passive_only, interval_hours):
    """The 100-year mode: rotate across targets, run, learn, sleep, repeat.
    Never stops until state/STOP exists. Every crash is caught, logged,
    and survived. A target that goes dry (no novel hypotheses) is skipped
    for one full rotation, then retried — fresh targets get priority."""
    import time
    import traceback
    if isinstance(targets, str):
        targets = [t.strip() for t in targets.split(",") if t.strip()]
    stop = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "state", "STOP")
    run_no = 0
    dry = {}  # target -> rotations to skip
    print(f"DEEPHUNT daemon: targets={targets} every {interval_hours}h. "
          f"STOP with: touch state/STOP")
    while True:
        if os.path.exists(stop):
            print("STOP file found — daemon halting. Remove it to resume.")
            break
        for target in targets:
            if os.path.exists(stop):
                break
            if dry.get(target, 0) > 0:
                dry[target] -= 1
                print(f"[daemon] {target} dry — skipping this rotation "
                      f"({dry[target]} left)")
                continue
            run_no += 1
            try:
                state = run_target(target, max_cycles=max_cycles,
                                   passive_only=passive_only)
                print(f"[daemon run {run_no}] {target} done: "
                      f"stop={state['stop_reason']} "
                      f"findings={len(state['findings'])}")
                if state.get("stop_reason", "").startswith(
                        "no novel hypotheses"):
                    dry[target] = 1  # skip one rotation, then retry
                    print(f"[daemon] {target} dry — cooling down one rotation")
            except Exception as e:  # noqa: BLE001
                with open(os.path.join(
                        os.path.dirname(os.path.abspath(__file__)),
                        "logs", "daemon_errors.log"), "a") as f:
                    f.write(f"\n=== run {run_no} {target} {now()} ===\n")
                    f.write(traceback.format_exc())
                print(f"[daemon run {run_no}] {target} CRASHED ({e}) — "
                      f"surviving, retrying after sleep")
        for _ in range(int(interval_hours * 3600 / 60)):
            if os.path.exists(stop):
                break
            time.sleep(60)


def main():
    ap = argparse.ArgumentParser(description="DEEPHUNT autonomous hunter")
    ap.add_argument("--target",
                    help="target profile name (targets/<name>.yaml); "
                         "comma-separated for daemon rotation, e.g. "
                         "--target adobe,shopify,yahoo")
    ap.add_argument("--max-cycles", type=int, default=3)
    ap.add_argument("--passive-only", action="store_true",
                    help="mapping only, no active tools, no test proposals")
    ap.add_argument("--list-tools", action="store_true")
    ap.add_argument("--phase", choices=["passive", "active", "operator"])
    ap.add_argument("--learn", action="store_true",
                    help="print what past runs learned (mistakes not to repeat)")
    ap.add_argument("--daemon", action="store_true",
                    help="run forever: rotate targets, repeat until STOP file "
                         "appears")
    ap.add_argument("--interval-hours", type=float, default=6,
                    help="sleep between daemon runs (default 6)")
    args = ap.parse_args()

    if args.list_tools:
        for t in list_tools(args.phase):
            mark = "OK " if t.available() else "MISS"
            print(f"[{mark}] {t.phase:8} {t.name:14} {t.description}")
        return

    if args.learn:
        mem = learn.load_memory(args.target or "")
        print(learn.mistakes_report(mem))
        return

    if not args.target:
        ap.error("--target is required (or use --list-tools / --learn)")
    if args.daemon:
        run_forever(args.target, args.max_cycles, args.passive_only,
                    args.interval_hours)
        return
    state = run_target(args.target, max_cycles=args.max_cycles,
                       passive_only=args.passive_only)
    print("\n== RESULT ==")
    print(f"stop_reason: {state['stop_reason']}")
    print(f"findings: {len(state['findings'])}  "
          f"cycles: {len(state['cycles'])}")
    if state["operator_tasks"]:
        print("operator tasks:")
        for t in state["operator_tasks"]:
            print(f"  - {t}")


if __name__ == "__main__":
    main()
