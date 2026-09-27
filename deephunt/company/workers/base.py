"""Shared passive-recon helpers. Stdlib only. Every call is a plain HTTPS GET
to a PUBLIC third-party API or the company's public homepage — no scanning,
no auth, no state-changing requests. All failures are captured, never raised.
"""
from __future__ import annotations

import json
import socket
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36 "
      "DEEPHUNT-passive-recon/1.0")
TIMEOUT = 20


def _req(url: str, headers: dict | None = None) -> urllib.request.Request:
    h = {"User-Agent": UA, "Accept": "*/*"}
    if headers:
        h.update(headers)
    return urllib.request.Request(url, headers=h)


def http_get_text(url: str, timeout: int = TIMEOUT) -> tuple[str | None, dict, str]:
    """Return (body, response_headers, error). error == '' on success."""
    try:
        with urllib.request.urlopen(_req(url), timeout=timeout) as r:
            raw = r.read()
            ctype = r.headers.get("Content-Type", "")
            charset = "utf-8"
            if "charset=" in ctype:
                charset = ctype.split("charset=")[-1].split(";")[0].strip()
            return raw.decode(charset, errors="replace"), dict(r.headers), ""
    except Exception as e:  # noqa: BLE001 - passive recon must never crash
        return None, {}, f"{type(e).__name__}: {e}"[:200]


def http_get_json(url: str, timeout: int = TIMEOUT) -> tuple[object, str]:
    body, _, err = http_get_text(url, timeout=timeout)
    if err:
        return None, err
    try:
        return json.loads(body), ""
    except Exception as e:  # noqa: BLE001
        return None, f"JSON parse failed: {e}"[:200]


def dns_doh(name: str, rtype: str = "A") -> tuple[list[str], str]:
    """Passive DNS via Google DNS-over-HTTPS (public API, no auth)."""
    q = urllib.parse.urlencode({"name": name, "type": rtype})
    data, err = http_get_json(f"https://dns.google/resolve?{q}")
    if err or not isinstance(data, dict):
        return [], err or "bad response"
    out = []
    for ans in data.get("Answer", []) or []:
        if ans.get("type") in (1, 28):  # A / AAAA
            out.append(ans.get("data", ""))
        elif rtype != "A" and ans.get("type") == {"MX": 15, "TXT": 16,
                                                 "NS": 2, "CNAME": 5,
                                                 "SOA": 6}.get(rtype, -1):
            out.append(ans.get("data", ""))
    return sorted(set(out)), ""


def resolve_a(name: str) -> list[str]:
    try:
        return sorted({r[4][0] for r in socket.getaddrinfo(name, 443)})
    except OSError:
        return []


def result(worker: str, data: dict, errors: list[str] | None = None) -> dict:
    return {"worker": worker, "data": data,
            "errors": errors or [], "partial": bool(errors)}
