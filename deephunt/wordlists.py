"""DEEPHUNT wordlist resolution — one place for every adapter's wordlists.

Priority: target-mined (state/wordlists/<target>_*.txt) > SecLists minimal
(ops/wordlists/) > built-in fallback.
"""
from __future__ import annotations
import os

HA = os.path.expanduser("~/workspace/hacker-agent")
OPS_WL = os.path.join(HA, "ops", "wordlists")
STATE_WL = os.path.join(HA, "deephunt", "state", "wordlists")

WORDLISTS = {
    # name -> filename under ops/wordlists (SecLists minimal, fetched 2026-09-27)
    "web-common": "common.txt",                       # 4.7k web paths
    "dns-5000": "subdomains-top1million-5000.txt",    # 5k subdomains
}

_FALLBACK_PATHS = [
    "admin", "api", "graphql", "debug", "internal", "console", "actuator",
    "metrics", "health", "config", ".env", "server-status", "v2", "v3",
    "beta", "staging", "test", "login", "auth", "oauth", "callback",
]


def resolve(name: str, target: str = "") -> str:
    """Return a usable wordlist path for `name`, preferring target-mined."""
    if target:
        for suffix in ("paths", "subs", "params"):
            p = os.path.join(STATE_WL, f"{target}_{suffix}.txt")
            if os.path.isfile(p) and os.path.getsize(p) > 0:
                return p
    fname = WORDLISTS.get(name)
    if fname:
        p = os.path.join(OPS_WL, fname)
        if os.path.isfile(p) and os.path.getsize(p) > 0:
            return p
    fb = "/tmp/dh_wordlist_fallback.txt"
    if not os.path.isfile(fb):
        with open(fb, "w", encoding="utf-8") as fh:
            fh.write("\n".join(_FALLBACK_PATHS))
    return fb


def available_names():
    return [n for n, f in WORDLISTS.items()
            if os.path.isfile(os.path.join(OPS_WL, f))]
