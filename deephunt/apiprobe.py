"""DEEPHUNT apiprobe — API surface discovery (clean-room).

Two probers, both passive-shaped (few requests, read-only):
  1. OpenAPI/Swagger spec discovery: probe well-known spec paths; a found spec
     is a full attack map (routes+params, missing security:, internal routes).
  2. GraphQL endpoint discovery + introspection: try POST, then GET, then
     `__type(name:"Query")` — each bypasses naive blocks (HackTricks pattern).
     Falls back to error-suggestion harvesting.

Both feed the semantic target model (endpoints/objects/actions). They never
send traffic themselves in library form; `probe_url()` uses urllib and is
exercised in tests against a LOCAL fake server only.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Dict, List, Optional

SPEC_PATHS = [
    "/swagger.json", "/openapi.json", "/swagger/v1/swagger.json",
    "/v2/api-docs", "/v3/api-docs", "/api-docs", "/api/swagger.json",
    "/swagger-ui.html", "/docs", "/api/docs", "/redoc",
    "/graphql/schema.json",
]

GQL_PATHS = ["/graphql", "/graphiql", "/api/graphql", "/v1/graphql",
             "/query", "/gql"]

INTROSPECTION_QUERY = "{__schema{queryType{name}mutationType{name}}}"


def _fetch(url: str, data: Optional[bytes] = None,
           timeout: int = 10) -> Optional[Dict]:
    req = urllib.request.Request(
        url, data=data,
        headers={"User-Agent": "DEEPHUNT-apiprobe/1.0",
                 "Content-Type": "application/json"} if data
        else {"User-Agent": "DEEPHUNT-apiprobe/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read(65536)
            return {"status": r.status, "body": body,
                    "content_type": r.headers.get("Content-Type", "")}
    except Exception:
        return None


def _looks_like_spec(body: bytes) -> bool:
    try:
        doc = json.loads(body)
    except Exception:
        return False
    return isinstance(doc, dict) and ("openapi" in doc or "swagger" in doc
                                     or "paths" in doc)


def discover_specs(base_url: str) -> List[Dict]:
    """Probe well-known OpenAPI/Swagger paths. Returns [{url, kind}]."""
    found = []
    base = base_url.rstrip("/")
    for p in SPEC_PATHS:
        url = base + p
        r = _fetch(url)
        if r and r["status"] == 200 and _looks_like_spec(r["body"]):
            doc = json.loads(r["body"])
            kind = "openapi3" if "openapi" in doc else "swagger2"
            found.append({"url": url, "kind": kind,
                          "paths": len(doc.get("paths", {}))})
    return found


def _gql_ok(resp: Optional[Dict]) -> bool:
    if not resp or resp["status"] != 200:
        return False
    try:
        doc = json.loads(resp["body"])
    except Exception:
        return False
    return isinstance(doc, dict) and ("data" in doc or "errors" in doc)


def probe_graphql(base_url: str) -> List[Dict]:
    """Discover GraphQL endpoints + test introspection via POST, GET,
    then __type fallback. Returns [{url, introspection: bool, method}]."""
    results = []
    base = base_url.rstrip("/")
    payload = json.dumps({"query": INTROSPECTION_QUERY}).encode()
    for p in GQL_PATHS:
        url = base + p
        # 1. POST introspection
        r = _fetch(url, data=payload)
        if _gql_ok(r):
            results.append({"url": url, "introspection": True,
                            "method": "POST"})
            continue
        # 2. GET introspection (bypasses POST-only blocks)
        q = urllib.parse.quote(INTROSPECTION_QUERY)
        r = _fetch(url + "?query=" + q)
        if _gql_ok(r):
            results.append({"url": url, "introspection": True,
                            "method": "GET"})
            continue
        # 3. __type probe (bypasses naive __schema blocks)
        tq = urllib.parse.quote('{__type(name:"Query"){fields{name}}}')
        r = _fetch(url + "?query=" + tq)
        if _gql_ok(r):
            results.append({"url": url, "introspection": "partial",
                            "method": "GET __type"})
    return results


def extract_endpoints_from_spec(spec_url: str) -> List[Dict]:
    """Fetch a discovered spec and extract paths+methods+params for the
    target model."""
    r = _fetch(spec_url)
    if not r or not _looks_like_spec(r["body"]):
        return []
    doc = json.loads(r["body"])
    out = []
    for path, ops in (doc.get("paths") or {}).items():
        for method, op in (ops or {}).items():
            params = [p.get("name") for p in (op.get("parameters") or [])
                      if isinstance(p, dict)]
            out.append({"path": path, "method": method.upper(),
                        "params": params,
                        "auth": "security" in op or "security" in doc})
    return out
