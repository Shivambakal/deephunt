"""DEEPHUNT active adapters — gated: run ONLY with a minted TestAuthorization
and an explicit active_allowed flag in the target profile. Dry-run first."""
from __future__ import annotations
import json
import os

from .base import ToolAdapter, register, sh, now

OPS_BIN = os.path.expanduser("~/workspace/hacker-agent/ops/bin")
NUCLEI = os.path.join(OPS_BIN, "nuclei")


def _gate(ctx):
    """Returns (ok, reason). Active tools need: profile flag + session token."""
    prof = ctx["profile"]
    if not prof.get("active_allowed", False):
        return False, "target profile active_allowed=false (read the test plan first)"
    if not ctx.get("authorization"):
        return False, "no TestAuthorization minted for the current test"
    hosts = ctx.get("authorization", {}).get("scope_hosts", [])
    if not hosts:
        return False, "authorization carries no scope_hosts"
    return True, ""


@register
class NucleiTool(ToolAdapter):
    name = "nuclei"
    phase = "active"
    description = "Nuclei template scan (gated) — misconfig/CVE/exposure classes"
    needs_bins = ()

    def available(self):
        return os.path.isfile(NUCLEI) and os.access(NUCLEI, os.X_OK)

    def run(self, ctx):
        ok, reason = _gate(ctx)
        if not ok:
            return [self.finding("gated", "nuclei BLOCKED", reason)]
        out = []
        hosts = ctx["authorization"]["scope_hosts"]
        sev = ctx["profile"].get("nuclei_severity",
                                 "critical,high,medium")
        tags = ctx["profile"].get("nuclei_tags", "")
        tagflag = f"-tags '{tags}'" if tags else ""
        for host in hosts[:6]:
            target = f"https://{host}"
            rc, so, se = sh(
                f"{NUCLEI} -u '{target}' -severity '{sev}' {tagflag} "
                f"-silent -jsonl -o /tmp/dh_nuclei.jsonl -timeout 10 "
                f"-rate-limit 20 -retries 1", timeout=600)
            hits = []
            try:
                with open("/tmp/dh_nuclei.jsonl") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            hits.append(json.loads(line))
            except OSError:
                pass
            for h in hits[:40]:
                info = h.get("info", {})
                out.append(self.finding(
                    "vuln-candidate", f"nuclei: {info.get('name')}",
                    detail=f"severity={info.get('severity')} "
                           f"template={h.get('template-id')} "
                           f"url={h.get('host', '')}{h.get('path', '')}",
                    evidence=(h.get("extracted-results") or [""])[:1][0],
                    severity_hint=info.get("severity", "unknown")))
            if not hits:
                out.append(self.finding("clean",
                                        f"nuclei: no hits on {target}",
                                        f"rc={rc} severities={sev}"))
        return out


@register
class NmapTool(ToolAdapter):
    name = "nmap"
    phase = "active"
    description = "nmap service inventory (gated) — no DoS flags, top ports only"
    needs_bins = ("nmap",)

    def run(self, ctx):
        ok, reason = _gate(ctx)
        if not ok:
            return [self.finding("gated", "nmap BLOCKED", reason)]
        out = []
        for host in ctx["authorization"]["scope_hosts"][:6]:
            rc, so, _ = sh(
                f"nmap -sV --top-ports 100 -T3 --max-retries 2 "
                f"--host-timeout 120s {host}", timeout=400)
            open_ports = [l.strip() for l in so.splitlines()
                          if "/tcp" in l and "open" in l][:30]
            out.append(self.finding(
                "inventory", f"nmap: {host}",
                detail="\n".join(open_ports) or "no open ports in top-100",
                evidence=f"{len(open_ports)} open"))
        return out


@register
class RepeaterTool(ToolAdapter):
    name = "repeater"
    phase = "active"
    description = "Burp-Repeater: resend a logged proxy request with tweaks (gated)"

    def run(self, ctx):
        ok, reason = _gate(ctx)
        if not ok:
            return [self.finding("gated", "repeater BLOCKED", reason)]
        spec = ctx.get("repeater_spec") or {}
        if not spec.get("seq"):
            return [self.finding("gated", "repeater needs repeater_spec.seq",
                                 "no logged request selected")]
        rep = os.path.expanduser("~/workspace/hacker-agent/proxy/repeater.py")
        mods = " ".join(f"--set {k}={v}"
                        for k, v in spec.get("mods", {}).items())
        rc, so, se = sh(f"python3 {rep} --seq {int(spec['seq'])} {mods}",
                        timeout=90)
        return [self.finding("probe", f"repeater seq={spec['seq']}",
                             detail=(so or se)[:1500],
                             evidence=f"rc={rc}")]


@register
class IntruderTool(ToolAdapter):
    name = "intruder"
    phase = "active"
    description = "Burp-Intruder: constrained payload fuzz (gated, rate-limited)"

    def run(self, ctx):
        ok, reason = _gate(ctx)
        if not ok:
            return [self.finding("gated", "intruder BLOCKED", reason)]
        spec = ctx.get("intruder_spec") or {}
        if not (spec.get("seq") and spec.get("payloads")):
            return [self.finding("gated", "intruder needs seq+payloads",
                                 "no fuzz spec provided")]
        intr = os.path.expanduser("~/workspace/hacker-agent/proxy/intruder.py")
        pl = ",".join(str(p) for p in spec["payloads"][:25])
        rc, so, se = sh(
            f"python3 {intr} --seq {int(spec['seq'])} "
            f"--payloads '{pl}' --delay 1.5", timeout=600)
        return [self.finding("probe", f"intruder seq={spec['seq']}",
                             detail=(so or se)[:2000],
                             evidence=f"rc={rc}")]


@register
class ProxyRoute(ToolAdapter):
    name = "proxy_route"
    phase = "passive"
    description = "Ensure intercept proxy is up; export env for tool traffic"

    def run(self, ctx):
        rc, _, _ = sh("curl -s --max-time 5 http://127.0.0.1:8080 -o /dev/null",
                      timeout=10)
        if rc == 0:
            return [self.finding("ready", "intercept proxy already on :8080")]
        sh("nohup ~/workspace/hacker-agent/proxy/start.sh 8080 "
           "> /tmp/dh_proxy.log 2>&1 &", timeout=10)
        import time as _t
        _t.sleep(4)
        rc2, _, _ = sh("curl -s --max-time 5 http://127.0.0.1:8080 "
                       "-o /dev/null", timeout=10)
        ok = rc2 == 0
        return [self.finding("ready" if ok else "failed",
                             f"intercept proxy start: {'up' if ok else 'down'}",
                             evidence="proxy/start.sh 8080")]


# ---------------------------------------------------------------------------
# Wave 2 — deeper active arsenal (all gated)
# ---------------------------------------------------------------------------

@register
class FfufTool(ToolAdapter):
    name = "ffuf"
    phase = "active"
    description = "Content discovery with mined wordlist (gated, rate-limited)"

    def available(self):
        import os as _o
        return _o.path.isfile(_o.path.join(OPS_BIN, "ffuf"))

    def run(self, ctx):
        ok, reason = _gate(ctx)
        if not ok:
            return [self.finding("gated", "ffuf BLOCKED", reason)]
        import os as _o
        wl = _o.path.join(_o.path.expanduser("~/workspace/hacker-agent"),
                          "deephunt", "state", "wordlists",
                          f"{ctx['target']}_paths.txt")
        if not _o.path.isfile(wl) or _o.path.getsize(wl) == 0:
            # small built-in fallback
            wl = "/tmp/dh_fallback.txt"
            open(wl, "w").write("\n".join([
                "admin", "api", "graphql", "debug", "internal", "console",
                "actuator", "metrics", "health", "config", ".env",
                "server-status", "v2", "v3", "beta", "staging", "test"]))
        out = []
        for host in ctx["authorization"]["scope_hosts"][:4]:
            rc, so, _ = sh(
                f"{OPS_BIN}/ffuf -u 'https://{host}/FUZZ' -w '{wl}' "
                f"-mc 200,204,301,302,307,401,403 -rate 20 -t 10 "
                f"-o /tmp/dh_ffuf.json -of json -s", timeout=600)
            hits = []
            try:
                data = json.load(open("/tmp/dh_ffuf.json"))
                hits = data.get("results", [])
            except (OSError, json.JSONDecodeError):
                pass
            for h in hits[:30]:
                out.append(self.finding(
                    "sensitive", f"ffuf: {host}/{h.get('input', {}).get('FUZZ')}"
                                 f" -> {h.get('status')}",
                    detail=f"url={h.get('url')} status={h.get('status')} "
                           f"len={h.get('length')}",
                    severity_hint="note"))
            if not hits:
                out.append(self.finding("clean", f"ffuf: nothing on {host}",
                                         f"rc={rc}"))
        return out


@register
class GraphqlProbe(ToolAdapter):
    name = "graphql_probe"
    phase = "active"
    description = "GraphQL introspection + schema mapping (gated)"

    def run(self, ctx):
        ok, reason = _gate(ctx)
        if not ok:
            return [self.finding("gated", "graphql_probe BLOCKED", reason)]
        out = []
        paths = ["/graphql", "/gql", "/api/graphql", "/v1/graphql"]
        intro = '{"query":"{__schema{queryType{name}}}"}'
        for host in ctx["authorization"]["scope_hosts"][:4]:
            for p in paths:
                rc, so, _ = sh(
                    f'curl -sk -m 20 -X POST "https://{host}{p}" '
                    f'-H "Content-Type: application/json" '
                    f'-d \'{intro}\'', timeout=30)
                if "__schema" in so or "queryType" in so:
                    out.append(self.finding(
                        "vuln-candidate",
                        f"GraphQL introspection OPEN at {host}{p}",
                        detail=so[:800],
                        severity_hint="medium"))
                    break
                if "errors" in so and "suggest" in so.lower():
                    out.append(self.finding(
                        "sensitive",
                        f"GraphQL at {host}{p} leaks field suggestions",
                        detail=so[:600], severity_hint="note"))
                    break
        if not out:
            out.append(self.finding("clean", "graphql_probe: no endpoint"))
        return out


@register
class DnsAxfr(ToolAdapter):
    name = "dns_axfr"
    phase = "active"
    description = "DNS zone-transfer attempt (gated, read-only)"

    def run(self, ctx):
        ok, reason = _gate(ctx)
        if not ok:
            return [self.finding("gated", "dns_axfr BLOCKED", reason)]
        out = []
        for zone in ctx["profile"].get("ct_zones", [])[:3]:
            rc, so, _ = sh(f"dig +short {zone} NS", timeout=20)
            for ns in [l.strip() for l in so.splitlines() if l.strip()][:3]:
                rc2, so2, _ = sh(f"dig @{ns} {zone} AXFR +short +time=10",
                                  timeout=30)
                if so2.strip() and "failed" not in so2.lower() \
                        and "timed out" not in so2.lower():
                    out.append(self.finding(
                        "vuln-candidate",
                        f"Zone transfer ALLOWED: {zone} via {ns}",
                        detail=so2[:1500], severity_hint="high"))
        if not out:
            out.append(self.finding("clean", "dns_axfr: refused everywhere"))
        return out


@register
class KatanaTool(ToolAdapter):
    name = "katana"
    phase = "active"
    description = "Crawl JS-heavy surface for endpoints (gated, polite)"

    def available(self):
        import os as _o
        return _o.path.isfile(_o.path.join(OPS_BIN, "katana"))

    def run(self, ctx):
        ok, reason = _gate(ctx)
        if not ok:
            return [self.finding("gated", "katana BLOCKED", reason)]
        out = []
        for host in ctx["authorization"]["scope_hosts"][:3]:
            rc, _, _ = sh(
                f"{OPS_BIN}/katana -u 'https://{host}' -silent "
                f"-o /tmp/dh_katana.txt -d 2 -c 5 -rate 10 "
                f"-timeout 10 -retries 1", timeout=900)
            try:
                urls = [l.strip() for l in open("/tmp/dh_katana.txt")
                        if l.strip()]
            except OSError:
                urls = []
            apiish = [u for u in urls if "?" in u or "/api" in u][:80]
            out.append(self.finding(
                "inventory", f"katana: {len(urls)} urls crawled on {host}",
                detail="\n".join(apiish), evidence=f"{len(urls)} urls"))
            ctx["state"].setdefault("katana_urls", {})[host] = len(urls)
        return out
