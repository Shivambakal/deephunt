"""DEEPHUNT advanced hand-built adapters — Burp-grade hunting power.

JwtProbe    (passive): static JWT misconfiguration analysis. Zero traffic:
                     decodes header/payload and flags alg=none, weak algs,
                     kid traversal, jku/x5u exfil URLs, missing exp.
Bypass403   (active): 403/401 bypass automation over the curated authz-403
                     battery. Differential vs a 403 baseline, rate-limited,
                     gated like every other active tool.
"""
from __future__ import annotations
import base64
import json
import os
import time
from urllib.parse import urlparse, urlunparse

from .base import ToolAdapter, register, sh
from .active import _gate

OPS = os.path.expanduser("~/workspace/hacker-agent/ops")
BATTERY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "data", "payloads", "authz-403.txt")

MIN_INTERVAL = 1.5
MAX_REQUESTS = 60


def _b64url_decode(seg: str):
    seg += "=" * (-len(seg) % 4)
    return json.loads(base64.urlsafe_b64decode(seg.encode()).decode("utf-8", "replace"))


@register
class JwtProbe(ToolAdapter):
    name = "jwt_probe"
    phase = "passive"
    description = "Static JWT analysis: alg confusion, kid traversal, jku/x5u, missing exp"

    def run(self, ctx):
        token = (ctx.get("jwt") or "").strip()
        if not token:
            return [self.finding("gated", "jwt_probe: no token",
                                 "pass a JWT via ctx['jwt'] (e.g. from a captured "
                                 "Authorization header or cookie)")]
        parts = token.split(".")
        if len(parts) != 3:
            return [self.finding("error", "jwt_probe: not a JWT",
                                 f"expected 3 segments, got {len(parts)}")]
        try:
            header = _b64url_decode(parts[0])
            payload = _b64url_decode(parts[1])
        except Exception as e:  # noqa: BLE001
            return [self.finding("error", "jwt_probe: undecodable",
                                 str(e)[:200])]
        out = []
        alg = str(header.get("alg", "")).upper()
        if alg == "NONE":
            out.append(self.finding(
                "vuln-candidate", "jwt_probe: alg=none accepted structurally",
                "Token header declares alg:none. If the server honors it, "
                "signature verification is bypassed entirely — test by "
                "re-signing with alg:none.",
                evidence=f"header={json.dumps(header)[:300]}",
                severity_hint="high"))
        elif alg.startswith("HS"):
            out.append(self.finding(
                "sensitive", "jwt_probe: symmetric HMAC algorithm",
                f"alg={alg}. Symmetric keys are brute-forceable offline and "
                "enable RS256->HS256 confusion if the server mixes key types.",
                severity_hint="note"))
        kid = str(header.get("kid", ""))
        if kid and (".." in kid or "/" in kid):
            out.append(self.finding(
                "vuln-candidate", "jwt_probe: kid path traversal shape",
                f"kid={kid!r} looks like a filesystem path — classic key-file "
                "inclusion vector (e.g. kid=../../dev/null).",
                severity_hint="medium"))
        for url_field in ("jku", "x5u"):
            u = str(header.get(url_field, ""))
            if u and u.startswith("http"):
                out.append(self.finding(
                    "sensitive", f"jwt_probe: {url_field} external URL",
                    f"{url_field}={u} — server fetches a remote key set; "
                    "attacker-controlled URL = key confusion / SSRF surface.",
                    severity_hint="note"))
        if "exp" not in payload:
            out.append(self.finding(
                "sensitive", "jwt_probe: no exp claim",
                "Token never expires — stolen tokens stay valid indefinitely.",
                severity_hint="note"))
        if not out:
            out.append(self.finding(
                "clean", "jwt_probe: no static misconfigurations",
                f"alg={alg or '?'} kid={'set' if kid else 'absent'} "
                f"exp={'set' if 'exp' in payload else 'absent'}"))
        return out


def _parse_battery():
    """Parse authz-403.txt TYPE|spec lines into actionable ops."""
    ops = []
    try:
        with open(BATTERY, encoding="utf-8") as fh:
            lines = fh.readlines()
    except OSError:
            return ops
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "|" not in line:
            continue
        typ, spec = line.split("|", 1)
        typ, spec = typ.strip(), spec.strip()
        if typ == "PATH":
            # "/admin -> /./admin"  (left side is the doc example, right is the mutation)
            mutated = spec.split("->", 1)[1].strip() if "->" in spec else spec
            mutated = mutated.split(" (")[0].strip()
            ops.append(("path", mutated, None))
        elif typ == "HEADER":
            # "X-Original-URL: /admin (request /)" — header + path-to-request
            req_path = "/"
            if "(request " in spec:
                req_path = spec.split("(request ", 1)[1].rstrip(")").strip()
                spec = spec.split(" (request ", 1)[0].strip()
            if ":" in spec:
                hk, hv = spec.split(":", 1)
                ops.append(("header", req_path, (hk.strip(), hv.strip())))
        elif typ == "METHOD":
            ops.append(("method", spec.split(" (")[0].strip(), None))
        elif typ == "QUERY":
            ops.append(("query", spec.split(" (")[0].strip(), None))
        elif typ == "UA":
            ua = spec.split(" (")[0].strip()
            ops.append(("header", None, ("User-Agent", ua)))
    return ops


def _curl_status(url, method="GET", headers=None, timeout=20):
    hdr = " ".join(f'-H "{k}: {v}"' for k, v in (headers or {}).items())
    rc, out, _ = sh(
        f'curl -sk -o /dev/null -w "%{{http_code}} %{{size_download}}" '
        f'-X {method} {hdr} --max-time {timeout} "{url}"', timeout=timeout + 5)
    try:
        status, size = out.strip().split()
        return int(status), int(size)
    except (ValueError, AttributeError):
        return 0, 0


@register
class Bypass403(ToolAdapter):
    name = "bypass403"
    phase = "active"
    description = ("403/401 bypass battery: path/header/method/query/UA mutations, "
                   "differential vs baseline (gated, rate-limited)")

    def run(self, ctx):
        ok, reason = _gate(ctx)
        if not ok:
            return [self.finding("gated", "bypass403 BLOCKED", reason)]
        targets = ctx.get("bypass403") or []
        if isinstance(targets, str):
            targets = [targets]
        if not targets:
            return [self.finding("gated", "bypass403: no target",
                                 "pass the 403 URL via ctx['bypass403'] "
                                 "(e.g. ['https://host/admin'])")]
        battery = _parse_battery()
        out = []
        for target in targets[:3]:
            pr = urlparse(target)
            base = urlunparse((pr.scheme, pr.netloc, "", "", "", ""))
            orig_path = pr.path or "/"
            b_status, b_len = _curl_status(target)
            if b_status not in (401, 403):
                out.append(self.finding(
                    "clean", f"bypass403: {target} is {b_status}, not 401/403",
                    "nothing to bypass — baseline is not a denial"))
                continue
            out.append(self.finding(
                "inventory", f"bypass403: baseline {b_status} on {orig_path}",
                f"testing {len(battery)} mutations, {MIN_INTERVAL}s apart"))
            n = 0
            for op, val, extra in battery:
                if n >= MAX_REQUESTS:
                    break
                url, method, headers = target, "GET", {}
                if op == "path":
                    url = base + (val if val.startswith("/") else "/" + val)
                elif op == "header":
                    url = base + (val or orig_path)
                    hk, hv = extra
                    headers[hk] = hv
                elif op == "method":
                    method = val
                elif op == "query":
                    url = target + ("&" if "?" in target else "?") + val
                status, size = _curl_status(url, method, headers)
                n += 1
                time.sleep(MIN_INTERVAL)
                if status in (200, 201, 206) or (
                        status in (301, 302, 307, 308) and status != b_status):
                    out.append(self.finding(
                        "vuln-candidate",
                        f"bypass403: {b_status}->{status} via {op}:{val[:40]}",
                        detail=f"url={url} method={method} "
                               f"headers={headers} len={size} (baseline {b_len})",
                        severity_hint="high"))
                elif status not in (b_status, 0) and abs(size - b_len) > 500:
                    out.append(self.finding(
                        "sensitive",
                        f"bypass403: differential {b_status}->{status} "
                        f"via {op}:{val[:40]}",
                        detail=f"url={url} len={size} (baseline {b_len}) — "
                               "different handler reached; inspect manually",
                        severity_hint="note"))
            if not [f for f in out if f["kind"] == "vuln-candidate"
                    and target in f.get("detail", "")]:
                out.append(self.finding(
                    "clean", f"bypass403: no bypass on {orig_path}",
                    f"{n} mutations tested, baseline {b_status} held"))
        return out
