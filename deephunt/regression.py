"""DEEPHUNT regression engine — confirmed findings become permanent tests.

Every CONFIRMED finding is converted into a regression test: the exact
control/test pair that proved the violation, replayable after remediation
to prove the fix held (or catch the regression).

Storage: deephunt/regressions/<target>/<REG-id>.json
CLI: python3 regression.py list --target X
     python3 regression.py run  --target X --dry-run   (default: dry-run)
     python3 regression.py run  --target X --execute  (needs an executor)

Execution NEVER happens inside this module directly: run() requires an
explicit `executor` callable (which in production is the session-gated
Engine path). Without one, run() refuses. This keeps the hard
authorization gate as the single choke point even for replays.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import time
from typing import Callable, Dict, List, Optional

BASE = os.path.dirname(os.path.abspath(__file__))
REG_DIR = os.path.join(BASE, "regressions")


def _target_dir(target: str) -> str:
    d = os.path.join(REG_DIR, target)
    os.makedirs(d, exist_ok=True)
    return d


def _next_id(target: str) -> str:
    existing = glob.glob(os.path.join(_target_dir(target), "REG-*.json"))
    nums = []
    for p in existing:
        try:
            nums.append(int(os.path.basename(p).split("-")[1].split(".")[0]))
        except (IndexError, ValueError):
            pass
    return f"REG-{max(nums, default=0) + 1:04d}"


def from_finding(finding: Dict, target: str) -> Dict:
    """Convert a confirmed finding into a regression test spec."""
    rid = _next_id(target)
    spec = {
        "id": rid,
        "target": target,
        "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "finding_ref": finding.get("id", finding.get("claim", "")[:60]),
        "claim": finding.get("claim", ""),
        "technique_id": finding.get("technique_id", ""),
        "control": finding.get("control_observation")
                   or (finding.get("evidence") or {}).get("control_observation", ""),
        "test": finding.get("test_observation")
                or (finding.get("evidence") or {}).get("test_observation", ""),
        "control_request": finding.get("control_request", {}),
        "test_request": finding.get("test_request", {}),
        "oracle": finding.get("oracle", finding.get("expected_property", "")),
        "expected": "HELD",  # after remediation, the invariant must HOLD
        "scope_hosts": finding.get("scope_hosts", []),
        "auth_basis": finding.get("auth_basis", ""),
        "history": [{"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                     "event": "created from confirmed finding"}],
    }
    path = os.path.join(_target_dir(target), f"{rid}.json")
    json.dump(spec, open(path, "w"), indent=1)
    return spec


def list_all(target: str) -> List[Dict]:
    out = []
    for p in sorted(glob.glob(os.path.join(_target_dir(target), "REG-*.json"))):
        try:
            out.append(json.load(open(p)))
        except (OSError, ValueError):
            pass
    return out


def load(target: str, reg_id: str) -> Optional[Dict]:
    p = os.path.join(_target_dir(target), f"{reg_id}.json")
    if os.path.isfile(p):
        try:
            return json.load(open(p))
        except (OSError, ValueError):
            return None
    return None


def evaluate(spec: Dict, control_obs: str, test_obs: str) -> Dict:
    """Evaluate a replay: run the oracle over the fresh pair and compare
    against the expected post-fix verdict (HELD)."""
    import sys
    sys.path.insert(0, BASE)
    import oracle as oracle_mod
    verdicts = oracle_mod.check_all(
        [spec.get("oracle")] if spec.get("oracle") else ["ownership"],
        control_obs, test_obs)
    overall, reason = oracle_mod.summarize(verdicts)
    passed = (overall == spec.get("expected", "HELD"))
    return {"regression_id": spec["id"], "oracle_verdict": overall,
            "expected": spec.get("expected", "HELD"),
            "passed": passed, "reason": reason,
            "detail": [{"invariant": v.invariant_id, "verdict": v.verdict,
                        "reason": v.reason} for v in verdicts]}


def run(target: str, reg_id: str, executor: Optional[Callable] = None,
        dry_run: bool = True) -> Dict:
    """Replay a regression. DRY-RUN by default. Live replay requires an
    explicit executor callable — the production path passes the
    session-gated Engine here, so authorization is enforced outside this
    module."""
    spec = load(target, reg_id)
    if not spec:
        return {"ok": False, "error": f"unknown regression {reg_id}"}
    if dry_run or executor is None:
        return {"ok": True, "dry_run": True, "regression_id": reg_id,
                "would_replay": {
                    "control_request": spec.get("control_request"),
                    "test_request": spec.get("test_request"),
                    "oracle": spec.get("oracle")},
                "note": "dry-run: no traffic sent; pass executor= to replay"}
    # executor(spec) -> {"control_observation": ..., "test_observation": ...}
    obs = executor(spec)
    result = evaluate(spec,
                      obs.get("control_observation", ""),
                      obs.get("test_observation", ""))
    spec["history"].append(
        {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
         "event": f"replayed: passed={result['passed']}"})
    json.dump(spec, open(os.path.join(_target_dir(target), f"{reg_id}.json"), "w"),
              indent=1)
    return {"ok": True, "dry_run": False, **result}


def main():
    ap = argparse.ArgumentParser(description="DEEPHUNT regression tests")
    ap.add_argument("cmd", choices=["list", "run"])
    ap.add_argument("--target", required=True)
    ap.add_argument("--id", default=None, help="REG id for run")
    ap.add_argument("--execute", action="store_true",
                    help="live replay (needs executor wiring; without it, dry-run)")
    args = ap.parse_args()
    if args.cmd == "list":
        for s in list_all(args.target):
            print(f"{s['id']}  {s['claim'][:70]}  expected={s['expected']}")
    elif args.cmd == "run":
        if not args.id:
            raise SystemExit("--id required for run")
        print(json.dumps(run(args.target, args.id, dry_run=not args.execute),
                         indent=1))


if __name__ == "__main__":
    main()
