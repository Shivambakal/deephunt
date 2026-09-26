"""
Intercept-and-modify rules engine for mitmproxy (Burp Match-and-Replace).

Rules live in a YAML file (default: rules.yaml next to the proxy root, or
PROXY_RULES_FILE env). Each rule:

  - name: add-research-tag
    match:
      host: "api.pinterest.com"      # regex, full match against flow host
      path: "^/v3/"                  # regex against request path
      method: "GET"                  # exact, case-insensitive (optional)
      direction: request            # request | response (default: request)
    actions:
      - add_header: ["X-Research-Tag", "differential-probe"]
      - remove_header: "X-Unwanted"
      - replace_header: ["User-Agent", "ResearchBot/1.0"]
      - set_param: ["debug", "1"]          # query param (request) 
      - remove_param: "tracking_id"
      - set_body: '{"a":1}'                # replace whole body (request/response)
      - drop: true                         # kill the flow entirely

Actions apply in order. A rule fires only if ALL match fields match.
"""
import os
import re
from urllib.parse import urlparse, parse_qsl, urlencode

import yaml
from mitmproxy import http

RULES_PATH = os.environ.get(
    "PROXY_RULES_FILE",
    os.path.join(os.path.dirname(__file__), "..", "rules.yaml"),
)


def load_rules(path: str = RULES_PATH) -> list:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    rules = data.get("rules", []) if isinstance(data, dict) else []
    compiled = []
    for r in rules:
        m = r.get("match", {}) or {}
        try:
            compiled.append({
                "name": r.get("name", "<unnamed>"),
                "host": re.compile(m.get("host", ".*")) if m.get("host") else None,
                "path": re.compile(m.get("path", ".*")) if m.get("path") else None,
                "method": (m.get("method") or "").upper() or None,
                "direction": (m.get("direction") or "request").lower(),
                "actions": r.get("actions", []) or [],
            })
        except re.error as e:
            print(f"[modify] bad regex in rule {r.get('name')}: {e}")
    return compiled


class ModifyRules:
    def __init__(self):
        self.rules = load_rules()
        print(f"[modify] loaded {len(self.rules)} rules from {RULES_PATH}")

    def _matches(self, rule, flow: http.HTTPFlow, direction: str) -> bool:
        if rule["direction"] != direction:
            return False
        req = flow.request
        if rule["method"] and req.method.upper() != rule["method"]:
            return False
        host = req.host or ""
        if rule["host"] and not rule["host"].search(host):
            return False
        path = req.path or ""
        if rule["path"] and not rule["path"].search(path):
            return False
        return True

    def _apply_request_actions(self, rule, flow: http.HTTPFlow):
        req = flow.request
        for action in rule["actions"]:
            if not isinstance(action, dict):
                continue
            for kind, val in action.items():
                if kind == "drop" and val:
                    flow.kill()
                    print(f"[modify] rule '{rule['name']}' DROPPED {req.method} {req.pretty_url}")
                    return
                elif kind == "add_header":
                    req.headers.add(val[0], val[1])
                elif kind == "remove_header":
                    req.headers.pop(val, None)
                elif kind == "replace_header":
                    req.headers[val[0]] = val[1]
                elif kind == "set_param":
                    parts = urlparse(req.pretty_url)
                    pairs = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k != val[0]]
                    pairs.append((val[0], val[1]))
                    new_url = parts._replace(query=urlencode(pairs)).geturl()
                    req.scheme, req.host, req.port, req.path = _split_url(new_url)
                elif kind == "remove_param":
                    parts = urlparse(req.pretty_url)
                    pairs = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k != val]
                    new_url = parts._replace(query=urlencode(pairs)).geturl()
                    req.scheme, req.host, req.port, req.path = _split_url(new_url)
                elif kind == "set_body":
                    req.content = val.encode("utf-8") if isinstance(val, str) else val
        print(f"[modify] rule '{rule['name']}' fired on REQUEST {req.method} {req.pretty_url}")

    def _apply_response_actions(self, rule, flow: http.HTTPFlow):
        resp = flow.response
        for action in rule["actions"]:
            if not isinstance(action, dict):
                continue
            for kind, val in action.items():
                if kind == "add_header":
                    resp.headers.add(val[0], val[1])
                elif kind == "remove_header":
                    resp.headers.pop(val, None)
                elif kind == "replace_header":
                    resp.headers[val[0]] = val[1]
                elif kind == "set_body":
                    resp.content = val.encode("utf-8") if isinstance(val, str) else val
        print(f"[modify] rule '{rule['name']}' fired on RESPONSE {resp.status_code} {flow.request.pretty_url}")

    def request(self, flow: http.HTTPFlow):
        for rule in self.rules:
            if self._matches(rule, flow, "request"):
                self._apply_request_actions(rule, flow)
                if flow.error or getattr(flow, "dead", False):
                    return

    def response(self, flow: http.HTTPFlow):
        for rule in self.rules:
            if self._matches(rule, flow, "response"):
                self._apply_response_actions(rule, flow)


def _split_url(url: str):
    parts = urlparse(url)
    port = parts.port or (443 if parts.scheme == "https" else 80)
    path = parts.path or "/"
    if parts.query:
        path += "?" + parts.query
    return parts.scheme, parts.hostname, port, path


addons = [ModifyRules()]
