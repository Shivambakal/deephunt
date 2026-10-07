"""Scope-tagging addon for mitmproxy (Burp "target scope" equivalent).

Tags every flow's metadata with in_scope=true/false based on scope.yaml.
TAG-ONLY: it never blocks or drops traffic — the daemon's passive tools must
keep flowing. Enforcement (default-deny) lives in intruder.py, which refuses
out-of-scope targets before sending anything.

The logger addon can read flow.metadata["scope_in_scope"] if desired; the
tag is also visible in mitmproxy's own UI via the metadata.
"""
import os
from urllib.parse import urlparse

import yaml

SCOPE_PATH = os.environ.get(
    "PROXY_SCOPE_FILE",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scope.yaml"),
)


def _load():
    try:
        with open(SCOPE_PATH, encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
    except OSError:
        return [], True
    hosts = [h.get("host", "").lower() for h in data.get("allowlist", [])]
    return hosts, bool(data.get("match_subdomains", True))


ALLOWLIST, MATCH_SUB = _load()


def in_scope(host: str) -> bool:
    host = (host or "").lower()
    for entry in ALLOWLIST:
        if not entry:
            continue
        if host == entry:
            return True
        if MATCH_SUB and host.endswith("." + entry):
            return True
    return False


class ScopeTagger:
    def request(self, flow):
        host = urlparse(flow.request.pretty_url).hostname or ""
        flow.metadata["scope_in_scope"] = in_scope(host)
        flow.metadata["scope_host"] = host


addons = [ScopeTagger()]
