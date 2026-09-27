"""DEEPHUNT payload corpus loader.

Vendored from PayloadsAllTheThings (MIT) via intel/build_payloads.py, plus
hand-curated high-signal classes. NEVER blind-fire: payloads are consumed by
the enforced test loop (hypothesis gate, adversarial check, rate limits).
"""
from __future__ import annotations

import os
from typing import Dict, List, Optional

CORPUS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "data", "payloads")

CLASSES = {
    "xss": ("cross-site scripting", "vendored"),
    "sqli": ("SQL injection detect/bypass", "vendored"),
    "cmdi": ("command injection", "vendored"),
    "traversal": ("path traversal", "vendored"),
    "xxe": ("XML external entity", "vendored"),
    "openredirect": ("open redirect", "vendored"),
    "jwt": ("JWT test battery shapes", "hand-curated"),
    "ssrf": ("SSRF metadata targets — in-scope only", "hand-curated"),
    "ssti": ("SSTI detect polyglots", "hand-curated"),
    "authz-403": ("403/401 bypass battery", "hand-curated"),
    "hpp": ("HTTP parameter pollution shapes", "hand-curated"),
    # Wave 1 additions (2026-09-27): genuinely new pattern families
    "crlf": ("CRLF/response-splitting variants", "hand-curated"),
    "nosql": ("NoSQL operator injection shapes", "hand-curated"),
    "ldap": ("LDAP filter metachar injection", "hand-curated"),
    "xpath": ("XPath expression injection", "hand-curated"),
    "smuggling": ("HTTP request-smuggling framing shapes", "hand-curated"),
    "prototype_pollution": ("prototype-pollution key paths", "hand-curated"),
    "graphql": ("GraphQL batching/aliasing/introspection shapes", "hand-curated"),
    "mass_assignment": ("mass-assignment field shapes", "hand-curated"),
    "deserialization_markers": ("deserialization format magic bytes", "hand-curated"),
    "host_header": ("Host-header / route-override variants", "hand-curated"),
    "xslt": ("XSLT capability probes", "hand-curated"),
}

_cache: Dict[str, List[str]] = {}


def list_classes() -> List[str]:
    return sorted(CLASSES)


def load(klass: str, limit: Optional[int] = None) -> List[str]:
    """Load payloads for a class. Comments (#) and shape lines with '|' are
    preserved — the caller interprets TYPE|value shapes."""
    if klass not in CLASSES:
        raise KeyError(f"unknown payload class: {klass}")
    if klass not in _cache:
        path = os.path.join(CORPUS_DIR, klass + ".txt")
        with open(path, errors="replace") as f:
            _cache[klass] = [ln.rstrip("\n") for ln in f
                             if ln.strip() and not ln.startswith("#")]
    items = _cache[klass]
    return items[:limit] if limit is not None else items


def provenance(klass: str) -> str:
    return CLASSES.get(klass, ("unknown", "unknown"))[1]
