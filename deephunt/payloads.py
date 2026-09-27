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
