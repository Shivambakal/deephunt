"""DEEPHUNT frontend parser — extract target structure from HTML/JS text.

Parses HTML/JS source (fetched pages, bundles) for:
  routes, API calls (fetch/axios/URL strings), forms (action/method/inputs),
  GraphQL operations, OpenAPI/Swagger URLs, error messages, auth-flow markers.

Output feeds target_model endpoints + api_specs + frontend_routes.
Passive analysis only — never executes the JS.
"""
from __future__ import annotations
import re

_ROUTE = re.compile(r'''(?:path|route|to)\s*[:=]\s*["'](/[\w\-/{}$.:]*)["']''')
_API = re.compile(r'''(?:fetch|axios\.(?:get|post|put|patch|delete)|url)\s*\(\s*["'`]([^"'`]+)["'`]''')
_API2 = re.compile(r'''["'`](/(?:api|v\d|graphql)[^"'`\s]*)["'`]''')
_FORM = re.compile(r'''<form\b([^>]*)>(.*?)</form>''', re.I | re.S)
_FORM_ACTION = re.compile(r'''action\s*=\s*["']([^"']+)["']''', re.I)
_FORM_METHOD = re.compile(r'''method\s*=\s*["']([^"']+)["']''', re.I)
_INPUT = re.compile(r'''<input\b([^>]*)>''', re.I)
_INPUT_NAME = re.compile(r'''(?:name|id)\s*=\s*["']([^"']+)["']''', re.I)
_GQL = re.compile(r'''\b(?:query|mutation|subscription)\s+(\w+)''')
_GQL_URL = re.compile(r'''["'`]([^"'`]*graphql[^"'`]*)["'`]''', re.I)
_OPENAPI = re.compile(r'''["'`]([^"'`]*?(?:openapi\.json|swagger\.json|swagger\.yaml|api-docs)[^"'`]*)["'`]''', re.I)
_ERROR = re.compile(r'''(?:error|exception|stack|trace)[\s:]*["']?([^"'<\n]{10,120})''', re.I)
_AUTH = re.compile(r'''\b(login|logout|signin|sign-in|signup|sign-up|oauth|authorize|token|refresh_token|session|mfa|2fa|password|reset)\b''', re.I)
_PARAM = re.compile(r'''\{(\w+)\}''')
_QUERY_PARAM = re.compile(r'''\?([\w\-,=&{}]+)''')


def parse_frontend(text, source=""):
    """Parse HTML/JS text -> dict of extracted structure."""
    text = text or ""
    out = {"routes": [], "api_calls": [], "forms": [],
           "graphql_ops": [], "api_specs": [], "error_messages": [],
           "auth_markers": [], "parameters": []}

    for m in _ROUTE.finditer(text):
        r = m.group(1)
        if r not in out["routes"]:
            out["routes"].append(r)

    apis = set()
    for m in _API.finditer(text):
        apis.add(m.group(1))
    for m in _API2.finditer(text):
        apis.add(m.group(1))
    out["api_calls"] = sorted(a for a in apis if a.startswith(("/", "http")))

    for fm in _FORM.finditer(text):
        attrs, body = fm.group(1), fm.group(2)
        action = (_FORM_ACTION.search(attrs) or [None, ""])[1]
        method = ((_FORM_METHOD.search(attrs) or [None, "GET"])[1] or "GET").upper()
        inputs = []
        for im in _INPUT.finditer(body):
            nm = _INPUT_NAME.search(im.group(1))
            if nm:
                inputs.append(nm.group(1))
        out["forms"].append({"action": action, "method": method,
                             "inputs": inputs, "source": source})

    out["graphql_ops"] = sorted(set(_GQL.findall(text)))
    gql_urls = sorted(set(_GQL_URL.findall(text)))
    out["api_calls"].extend(u for u in gql_urls if u not in out["api_calls"])

    out["api_specs"] = sorted(set(_OPENAPI.findall(text)))

    errs = []
    for m in _ERROR.finditer(text):
        e = m.group(1).strip()
        if e and e not in errs and len(errs) < 20:
            errs.append(e)
    out["error_messages"] = errs

    out["auth_markers"] = sorted(set(m.group(1).lower() for m in _AUTH.finditer(text)))

    params = set()
    for call in out["api_calls"]:
        params.update(_PARAM.findall(call))
        for q in _QUERY_PARAM.findall(call):
            for pair in q.split("&"):
                name = pair.split("=")[0].strip("{}")
                if name:
                    params.add(name)
    for form in out["forms"]:
        params.update(form["inputs"])
    out["parameters"] = sorted(params)

    return out


def feed_target_model(parsed, target):
    """Feed parsed frontend structure into a Target model. Returns counts."""
    counts = {"endpoints": 0, "api_specs": 0, "frontend_routes": 0, "parameters": 0}
    for call in parsed.get("api_calls", []):
        path = call.split("?")[0]
        target.add_endpoint(path, method="GET",
                            authentication="unknown",
                            parameters=parsed.get("parameters", []))
        counts["endpoints"] += 1
    for spec in parsed.get("api_specs", []):
        if spec not in [s["url"] for s in target.data["api_specs"]]:
            target.data["api_specs"].append({"url": spec, "kind": "openapi"})
            counts["api_specs"] += 1
    for route in parsed.get("routes", []):
        if route not in [r["route"] for r in target.data["frontend_routes"]]:
            target.data["frontend_routes"].append(
                {"route": route, "component_hint": ""})
            counts["frontend_routes"] += 1
    for form in parsed.get("forms", []):
        if form["action"]:
            target.add_endpoint(form["action"], method=form["method"],
                                authentication="unknown",
                                parameters=form["inputs"])
            counts["endpoints"] += 1
    for p in parsed.get("parameters", []):
        target.add_parameter(p, seen_in="frontend", user_controlled=True)
        counts["parameters"] += 1
    if parsed.get("graphql_ops"):
        target.add_observation(
            f"GraphQL operations observed: {', '.join(parsed['graphql_ops'][:10])}")
    if parsed.get("auth_markers"):
        target.add_observation(
            f"Auth-flow markers: {', '.join(parsed['auth_markers'][:10])}")
    target.save()
    return counts
