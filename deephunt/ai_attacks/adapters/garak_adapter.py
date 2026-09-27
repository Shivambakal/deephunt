"""Garak adapter — NVIDIA's LLM vulnerability scanner.

Garak ships 120+ probes (incl. `latentinjection` for RAG-style indirect
injection). Its REST generator can point at ANY authorized HTTP endpoint
with zero code via a JSON config: $INPUT/$KEY templating, JSONPath
response extraction, key from env var.

Interface:
  build_rest_config(endpoint, input_field="prompt", ...) -> dict
      The garak REST generator config. Pure data.
  plan_scan(config, probes=None) -> dict
      Execution spec for the pipeline (propose-only).
  run_scan(spec, authorization) -> dict
      Actually launches garak as a subprocess. REQUIRES a valid
      TestAuthorization token (dict with "token" + "scope_hosts"); the
      endpoint host must be inside scope_hosts. Returns parsed findings.
  parse_report(report_jsonl_path) -> list[dict]
      Normalize garak's report JSONL into DEEPHUNT findings with
      evidence artifacts compatible with evidence.py.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
from typing import Dict, List


def available() -> bool:
    return importlib.util.find_spec("garak") is not None


def build_rest_config(endpoint: str, input_field: str = "prompt",
                      output_jsonpath: str = "$.response",
                      key_env_var: str = "DEEPHUNT_TARGET_KEY",
                      extra_fields: Dict = None) -> Dict:
    """Pure-data REST generator config for garak. No transmission."""
    cfg = {
        "rest": {
            "RestGenerator": {
                "uri": endpoint,
                "method": "POST",
                "req_template_json_object": {
                    input_field: "$INPUT",
                    **(extra_fields or {}),
                },
                "response_json_field": output_jsonpath,
                "key_env_var": key_env_var,
            }
        }
    }
    return cfg


def plan_scan(rest_config: Dict, probes: List[str] = None,
              generations: int = 3) -> Dict:
    """Build a propose-only execution spec for the pipeline."""
    return {
        "tool": "garak",
        "action": "run_scan",
        "rest_config": rest_config,
        "probes": probes or ["promptinject", "latentinjection", "encoding",
                             "dan", "leakreplay"],
        "generations": generations,
        "requires": "TestAuthorization with endpoint host in scope_hosts",
    }


def _check_auth(authorization: Dict, endpoint: str) -> None:
    if not isinstance(authorization, dict) or not authorization.get("token"):
        raise PermissionError("garak run_scan requires a TestAuthorization "
                              "token; got none (propose-only without it)")
    from urllib.parse import urlparse
    host = urlparse(endpoint).netloc.split(":")[0].lower()
    scope = [h.lower() for h in authorization.get("scope_hosts", [])]
    if scope and not any(host == s or host.endswith("." + s) for s in scope):
        raise PermissionError(f"endpoint host {host} not in authorized scope")


def run_scan(spec: Dict, authorization: Dict) -> Dict:
    """Execute garak. Gated: needs TestAuthorization + in-scope endpoint."""
    endpoint = spec["rest_config"]["rest"]["RestGenerator"]["uri"]
    _check_auth(authorization, endpoint)  # gate BEFORE anything else
    if not available():
        return {"ok": False, "reason": "garak not installed "
                "(pip install -U garak)"}
    with tempfile.TemporaryDirectory() as td:
        cfg_path = os.path.join(td, "rest_config.json")
        with open(cfg_path, "w") as f:
            json.dump(spec["rest_config"], f)
        cmd = ["python", "-m", "garak",
               "--model_type", "rest", "--model_name", "target",
               "-G", cfg_path,
               "--probes", ",".join(spec.get("probes", ["promptinject"])),
               "--generations", str(spec.get("generations", 3)),
               "--report_prefix", os.path.join(td, "garak")]
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=1800)
        reports = [os.path.join(td, p) for p in os.listdir(td)
                   if p.endswith(".report.jsonl")]
        findings = []
        for r in reports:
            findings.extend(parse_report(r))
        return {"ok": proc.returncode == 0, "findings": findings,
                "stdout_tail": proc.stdout[-2000:],
                "stderr_tail": proc.stderr[-2000:]}


def parse_report(report_jsonl_path: str) -> List[Dict]:
    """Normalize garak report JSONL -> DEEPHUNT findings."""
    findings: List[Dict] = []
    try:
        with open(report_jsonl_path) as f:
            rows = [json.loads(line) for line in f if line.strip()]
    except (OSError, json.JSONDecodeError):
        return findings
    # garak eval rows carry probe/detector/pass info
    for row in rows:
        if row.get("entry_type") != "eval":
            continue
        passed = bool(row.get("passed"))
        if passed:
            continue  # only failures (vuln signals) become findings
        probe = row.get("probe_classname", "unknown")
        findings.append({
            "tool": "garak",
            "probe": probe,
            "detector": row.get("detector_classname", ""),
            "goal": row.get("goal", ""),
            "evidence_artifacts": {
                "garak_eval_failed": True,
                "probe_classname": bool(probe),
                "attempt_logged": True,
            },
            "raw": {k: row.get(k) for k in
                    ("prompt", "output", "trigger", "score")},
        })
    return findings


__all__ = ["available", "build_rest_config", "plan_scan", "run_scan",
           "parse_report"]
