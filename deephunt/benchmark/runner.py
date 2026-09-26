"""Benchmark runner: drives DEEPHUNT's REAL pipeline against each scenario.

For every scenario:
  1. differential.compare() on each probe pair (noise-stripped)
  2. interesting -> open validation case, walk stages with scenario evidence
  3. report_gate.clear_for_report() at the final stage
  4. verdict vs ground truth

Metrics: TP/FP/TN/FN, precision, recall, time-to-finding, requests used,
chain completion, reproducibility (each scenario runs twice).
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import differential
from validate import ValidationPipeline
from report_gate import clear_for_report
from scenarios import ALL


def run_scenario(scn_cls):
    scn = scn_cls()
    t0 = time.time()
    requests = 0
    verdict = "no-finding"
    pipe = ValidationPipeline()
    try:
        for label, (cprobe, cident), (vprobe, vident) in scn.probe_pairs():
            obs_c = scn.probe(cprobe, cident)
            obs_v = scn.probe(vprobe, vident)
            requests += 2
            level, reasons = differential.compare(obs_c, obs_v)
            if level == "identical":
                continue  # noise only — no case opened, correctly
            case = f"{scn.name}-{label}"
            pipe.open(case, f"{label}: {reasons[0]}")
            try:
                for stage in ["HYPOTHESIZED", "EXPERIMENTED", "REPRODUCED",
                              "IMPACT_SHOWN", "RETESTED"]:
                    pipe.advance(case, scn.evidence_for(stage))
                ok, why = clear_for_report(
                    pipe.cases[case],
                    known_signatures=["deceptive", "intended public"])
                if ok:
                    pipe.advance(case, "report gate passed: " + "; ".join(why))
                    verdict = "finding"
                else:
                    pipe.kill(case, "report gate: " + "; ".join(why))
            except ValueError as e:
                pipe.kill(case, str(e)[:200])
            if verdict == "finding":
                break
    except Exception as e:  # noqa: BLE001
        verdict = f"error: {e}"
    return {"scenario": scn.name, "category": scn.category,
            "truth": scn.ground_truth, "verdict": verdict,
            "requests": requests, "time_s": round(time.time() - t0, 2)}


def run_all(repeat=2):
    """Run every scenario `repeat` times (reproducibility check)."""
    results = []
    for _ in range(repeat):
        for cls in ALL:
            results.append(run_scenario(cls))
    return results


def score(results):
    tp = fp = tn = fn = 0
    times, reqs = [], []
    for r in results:
        found = r["verdict"] == "finding"
        vuln = r["truth"] == "vuln"
        if found and vuln:
            tp += 1
            times.append(r["time_s"])
        elif found and not vuln:
            fp += 1
        elif not found and not vuln:
            tn += 1
        else:
            fn += 1
        reqs.append(r["requests"])
    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0
    # reproducibility: same verdict across repeats per scenario
    by_scn = {}
    for r in results:
        by_scn.setdefault(r["scenario"], set()).add(r["verdict"])
    repro = sum(1 for v in by_scn.values() if len(v) == 1) / len(by_scn)
    return {
        "n": len(results), "TP": tp, "FP": fp, "TN": tn, "FN": fn,
        "precision": round(precision, 3), "recall": round(recall, 3),
        "avg_time_s": round(sum(times) / len(times), 2) if times else 0,
        "avg_requests": round(sum(reqs) / len(reqs), 1),
        "reproducibility": round(repro, 3),
        "chain_completion": "see ResetChain verdict",
    }


if __name__ == "__main__":
    res = run_all()
    import json
    print(json.dumps(score(res), indent=1))
    for r in res[:14]:
        mark = "TP" if r["verdict"] == "finding" and r["truth"] == "vuln" \
            else "FP" if r["verdict"] == "finding" else \
            "TN" if r["truth"] == "fp" else "FN"
        print(f"  [{mark}] {r['scenario']:18s} truth={r['truth']:4s} "
              f"verdict={r['verdict']:10s} req={r['requests']}")
