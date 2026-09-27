"""DEEPHUNT semantic analysis — white-box pipeline (blueprint P0-P1 #10, §10-11).

    repo -> architecture map -> endpoint/source-sink extraction
         -> candidate dataflows -> hypotheses -> test generation

Layers:
  1. AST (stdlib `ast` for Python; regex extractors for JS/TS).
  2. Semgrep seed rules: the repo's intel/semgrep-rules/deephunt-bounty.yaml
     rule ids are mapped to checkers. If the semgrep binary is installed it
     is used; otherwise the built-in pattern checkers run (same rule ids,
     best-effort semantics).
  3. Taint: intra-procedural name-flow — a variable assigned from a SOURCE
     that reaches a SINK without a sanitizer in between becomes a candidate
     dataflow.

Output is hypotheses with preconditions + oracle hints, ready for the
hypothesis engine. No network, no execution of target code.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import subprocess
from typing import Dict, List, Optional

BASE = os.path.dirname(os.path.abspath(__file__))
SEMGREP_RULES = os.path.join(BASE, "intel", "semgrep-rules", "deephunt-bounty.yaml")

# ---- source / sink / sanitizer models (report §11 lenses) ----
SOURCES = {
    "http_input": [r"request\.(args|form|json|values|data|cookies|headers)",
                   r"req\.(query|body|params|headers)", r"location\.search",
                   r"URLSearchParams", r"input\("],
    "route_param": [r"<(int|string|uuid|path):\w+>", r"req\.params", r"\{id\}"],
    "file_upload": [r"request\.files", r"multer", r"upload\.single"],
    "websocket_msg": [r"on\(['\"]message['\"]", r"socket\.on"],
    "webhook": [r"webhook", r"callback.*payload"],
}
SINKS = {
    "sqli": [r"execute\s*\(", r"query\s*\(", r"raw\s*\(", r"from_statement"],
    "cmdi": [r"os\.system", r"subprocess\.", r"exec\s*\(", r"spawn\s*\(",
              r"child_process"],
    "ssti": [r"render_template_string", r"Template\s*\("],
    "xss_sink": [r"innerHTML\s*=", r"dangerouslySetInnerHTML", r"document\.write"],
    "ssrf": [r"requests\.(get|post)\s*\(", r"fetch\s*\(", r"urllib.*urlopen",
             r"axios\.(get|post)"],
    "deser": [r"pickle\.loads", r"yaml\.load\s*\(", r"eval\s*\(", r"marshal\.loads"],
    "redirect": [r"redirect\s*\(", r"location\s*="],
    "weak_random": [r"Math\.random\s*\(\)", r"random\.random\s*\(\)"],
    "path": [r"open\s*\(", r"send_file", r"readFile"],
}
SANITIZERS = [r"escape", r"sanitize", r"quote", r"parameteri", r"prepared",
              r"allowlist", r"validate", r"encode"]

# Map of semgrep seed-rule ids -> (lens, sink-family) for the fallback checker.
SEED_RULE_MAP = {
    "deephunt-idor-fetch": ("authorization", "http_input"),
    "deephunt-sqli-concat": ("injection", "sqli"),
    "deephunt-cmdi": ("injection", "cmdi"),
    "deephunt-ssrf": ("ssrf", "ssrf"),
    "deephunt-weak-random": ("crypto", "weak_random"),
    "deephunt-open-redirect": ("redirect", "redirect"),
}


def _read_rules() -> List[str]:
    ids = []
    if os.path.isfile(SEMGREP_RULES):
        try:
            import yaml
            docs = yaml.safe_load(open(SEMGREP_RULES)) or {}
            for r in docs.get("rules", []):
                if isinstance(r, dict) and r.get("id"):
                    ids.append(r["id"])
        except Exception:
            pass
    return ids


def _iter_files(root: str):
    for dp, _, fns in os.walk(root):
        if any(skip in dp for skip in (".git", "node_modules", "venv", "__pycache__",
                                       ".venv", "site-packages")):
            continue
        for fn in fns:
            if fn.endswith((".py", ".js", ".ts", ".tsx", ".jsx")):
                yield os.path.join(dp, fn)


def _py_endpoints(tree: ast.AST) -> List[Dict]:
    eps = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for dec in node.decorator_list:
                src = ast.dump(dec)
                # ast.dump: Call(func=Attribute(attr='route'), args=[Constant(value='/path')])
                m = re.search(r"(get|post|put|delete|patch|route)\W", src)
                if not m:
                    continue
                pm = re.search(r"value='([^']+)'", src[m.start():])
                if pm:
                    eps.append({"method": m.group(1).upper(), "path": pm.group(1),
                                "handler": node.name, "params": [a.arg for a in node.args.args]})
    return eps


def _py_flows(src: str) -> List[Dict]:
    """Intra-procedural taint: source-assigned name reaching a sink."""
    flows = []
    lines = src.splitlines()
    for i, line in enumerate(lines):
        for sname, spats in SOURCES.items():
            if any(re.search(p, line) for p in spats):
                m = re.match(r"\s*(\w+)\s*=", line)
                tainted = m.group(1) if m else None
                # look ahead up to 40 lines for a sink using the tainted name
                window = "\n".join(lines[i:i + 40])
                for sinkname, sinkpats in SINKS.items():
                    if any(re.search(p, window) for p in sinkpats):
                        if tainted and re.search(rf"\b{re.escape(tainted)}\b", window):
                            if not any(re.search(s, window) for s in SANITIZERS):
                                flows.append({
                                    "source": sname, "sink": sinkname,
                                    "tainted_var": tainted, "line": i + 1,
                                    "sanitized": False})
    return flows


def _js_extract(path: str, src: str) -> Dict:
    eps, flows = [], []
    for m in re.finditer(r"(fetch|axios\.(get|post|put|delete)|app\.(get|post|put|delete))"
                         r"\s*\(\s*['\"`]([^'\"`]+)", src):
        eps.append({"method": (m.group(2) or m.group(3) or "GET").upper(),
                    "path": m.group(4), "handler": os.path.basename(path),
                    "params": []})
    for i, line in enumerate(src.splitlines()):
        for sname, spats in SOURCES.items():
            if any(re.search(p, line) for p in spats):
                window = "\n".join(src.splitlines()[i:i + 40])
                for sinkname, sinkpats in SINKS.items():
                    if any(re.search(p, window) for p in sinkpats):
                        if not any(re.search(s, window) for s in SANITIZERS):
                            flows.append({"source": sname, "sink": sinkname,
                                          "tainted_var": "?", "line": i + 1,
                                          "sanitized": False})
    return {"endpoints": eps, "flows": flows}


def _run_semgrep(root: str) -> List[Dict]:
    """Use the real semgrep binary when present; else []."""
    try:
        r = subprocess.run(["semgrep", "--config", SEMGREP_RULES, "--json",
                            "--quiet", root],
                           capture_output=True, text=True, timeout=120)
        data = json.loads(r.stdout or "{}")
        return [{"rule": res.get("check_id", ""), "path": res.get("path", ""),
                 "line": res.get("start", {}).get("line", 0),
                 "message": res.get("extra", {}).get("message", "")}
                for res in data.get("results", [])]
    except Exception:
        return []


def _fallback_rule_scan(src: str, path: str) -> List[Dict]:
    """Best-effort checkers under the seed rule ids (no semgrep binary)."""
    hits = []
    for rule_id, (lens, sinkfam) in SEED_RULE_MAP.items():
        for i, line in enumerate(src.splitlines()):
            hit = False
            if sinkfam == "http_input":
                hit = bool(re.search(r"location\.search|URLSearchParams", line) and
                           re.search(r"fetch\s*\(.*\+", line))
            else:
                hit = any(re.search(p, line) for p in SINKS.get(sinkfam, []))
            if hit:
                hits.append({"rule": rule_id, "path": path, "line": i + 1,
                             "message": f"{lens}: {sinkfam} pattern (fallback scan)",
                             "fallback": True})
                break
    return hits


def analyze_repo(root: str, use_semgrep: bool = True) -> Dict:
    """Full white-box pipeline for a local repo checkout."""
    arch = {"root": root, "endpoints": [], "flows": [],
            "rule_hits": [], "files": 0, "languages": set()}
    semgrep_hits = _run_semgrep(root) if use_semgrep else []
    arch["rule_hits"].extend(semgrep_hits)
    for path in _iter_files(root):
        arch["files"] += 1
        try:
            src = open(path, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        if path.endswith(".py"):
            arch["languages"].add("python")
            try:
                tree = ast.parse(src)
                for ep in _py_endpoints(tree):
                    ep["file"] = path
                    arch["endpoints"].append(ep)
            except SyntaxError:
                pass
            for fl in _py_flows(src):
                fl["file"] = path
                arch["flows"].append(fl)
        else:
            arch["languages"].add("javascript")
            r = _js_extract(path, src)
            for ep in r["endpoints"]:
                ep["file"] = path
                arch["endpoints"].append(ep)
            for fl in r["flows"]:
                fl["file"] = path
                arch["flows"].append(fl)
        if not semgrep_hits:  # fallback only when real semgrep didn't run
            arch["rule_hits"].extend(_fallback_rule_scan(src, path))
    arch["languages"] = sorted(arch["languages"])
    arch["seed_rules"] = _read_rules()
    return arch


_ORACLE_FOR_SINK = {
    "sqli": "differential_confirmed", "cmdi": "command_output_observed",
    "ssti": "template_evaluated", "xss_sink": "payload_reflected_executed",
    "ssrf": "oob_interaction_observed", "deser": "deserialization_confirmed",
    "redirect": "open_redirect_confirmed", "weak_random": "predictable_token",
    "path": "path_traversal_confirmed",
}


def to_hypotheses(arch: Dict, target: str = "") -> List[Dict]:
    """Candidate dataflows -> hypothesis dicts for the hypothesis engine."""
    hyps = []
    for fl in arch.get("flows", []):
        sink = fl["sink"]
        hyps.append({
            "id": f"SEM-{fl['line']:04d}-{sink}",
            "statement": (f"{fl['source']} reaches {sink} sink unsanitized "
                          f"({fl['file']}:{fl['line']})"),
            "family": "injection" if sink in ("sqli", "cmdi", "ssti") else "web",
            "technique_id": {"sqli": "INJ-01", "cmdi": "INJ-02",
                             "ssti": "INJ-03"}.get(sink, "SEM-01"),
            "preconditions": ["white_box_access", "endpoint_reachable"],
            "required_state": [],
            "oracle": _ORACLE_FOR_SINK.get(sink, "differential_confirmed"),
            "severity": "high" if sink in ("sqli", "cmdi", "deser", "ssrf") else "medium",
            "source": "semantic",
            "evidence_for": [f"{fl['file']}:{fl['line']}"],
            "status": "candidate",
        })
    # endpoints without visible auth checks -> authz hypotheses
    for ep in arch.get("endpoints", [])[:50]:
        if re.search(r"\{id\}|:\w+id|/users/|/orders/|/admin", ep["path"]):
            epid = hashlib.md5(ep["path"].encode()).hexdigest()[:8]
            hyps.append({
                "id": f"SEM-EP-{epid}",
                "statement": f"{ep['method']} {ep['path']} takes object id — "
                             f"check object-level authorization",
                "family": "auth", "technique_id": "IDOR-01",
                "preconditions": ["authenticated_identity", "object_identifier"],
                "required_state": [],
                "oracle": "ownership_must_match_actor",
                "severity": "high", "source": "semantic",
                "evidence_for": [f"{ep.get('file', '')}:{ep.get('handler', '')}"],
                "status": "candidate",
            })
    return hyps
