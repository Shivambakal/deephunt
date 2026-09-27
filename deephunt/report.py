"""DEEPHUNT report builder — evidence-backed output (blueprint wire-up).

A report is not "LLM says vulnerable". It is the evidence contract,
rendered: claim, preconditions, control/test, observation, differential,
oracle verdict, independent-verifier verdict, confidence, false-positive
rules checked, and the regression test id.

Secret hygiene: credential-shaped content is redacted before rendering.
"""
from __future__ import annotations

import re
import time
from typing import Dict, List, Optional

_SECRET_PAT = re.compile(
    r"(?i)(password|passwd|secret|api[_-]?key|token)\s*[:=]\s*\S+|"
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----|"
    r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")


def redact(text: str) -> str:
    return _SECRET_PAT.sub("[REDACTED]", text or "")


def build_finding_report(finding: Dict,
                         oracle_verdicts: Optional[List[Dict]] = None,
                         verifier_report=None,
                         regression_id: str = "") -> Dict:
    ev = finding.get("evidence", {}) if isinstance(finding.get("evidence"), dict) else {}
    report = {
        "claim": finding.get("claim", ""),
        "technique_id": finding.get("technique_id", ""),
        "severity": finding.get("severity", "unknown"),
        "preconditions": finding.get("preconditions", []),
        "control": redact(str(finding.get("control_observation") or
                              ev.get("control_observation", ""))[:800]),
        "test": redact(str(finding.get("test_observation") or
                            ev.get("test_observation", ""))[:800]),
        "differential": finding.get("differential", {}),
        "oracle": oracle_verdicts or [],
        "independent_verification": (
            {"verdict": verifier_report.verdict,
             "notes": verifier_report.falsification_notes,
             "confidence": verifier_report.confidence}
            if verifier_report else {"verdict": "NOT_RUN"}),
        "false_positive_rules_checked": finding.get("false_positive_rules_checked", []),
        "assumptions": finding.get("assumptions", []),
        "scope_hosts": finding.get("scope_hosts", []),
        "auth_basis": finding.get("auth_basis", ""),
        "regression_test": regression_id,
        "confidence": finding.get("confidence", 0.0),
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    return report


def to_markdown(report: Dict) -> str:
    lines = [
        f"# Finding: {report['claim']}",
        "",
        f"- Technique: {report['technique_id']} | Severity: {report['severity']} "
        f"| Confidence: {report['confidence']}",
        f"- Scope: {', '.join(report['scope_hosts'])} | Basis: {report['auth_basis']}",
        "",
        "## Preconditions",
    ]
    lines += [f"- {p}" for p in report["preconditions"]] or ["- (none recorded)"]
    lines += ["", "## Control vs Test",
              f"Control: {report['control']}", f"Test: {report['test']}", ""]
    lines.append("## Oracle verdicts")
    for v in report["oracle"]:
        lines.append(f"- {v.get('invariant_id')}: **{v.get('verdict')}** — {v.get('reason')}")
    iv = report["independent_verification"]
    lines += ["", f"## Independent verification: {iv['verdict']}"]
    lines += [f"- {n}" for n in iv.get("notes", [])]
    if report["regression_test"]:
        lines += ["", f"Regression: `{report['regression_test']}`"]
    return "\n".join(lines)


def build_run_summary(target: str, counts: Dict, metrics: Optional[Dict] = None) -> Dict:
    return {"target": target,
            "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "counts": counts, "metrics": metrics or {},
            "note": "Every finding above carries its evidence contract; "
                    "nothing is reported on assertion alone."}
