"""DEEPHUNT passive adapters — mapping, never attacking."""
from __future__ import annotations
import json
import re
from urllib.parse import urljoin, urlparse

from .base import ToolAdapter, register, fetch, sh


@register
class CrtSh(ToolAdapter):
    name = "crtsh"
    phase = "passive"
    description = "Certificate-transparency subdomain inventory (crt.sh JSON)"

    def run(self, ctx):
        out = []
        for zone in ctx["profile"].get("ct_zones", []):
            status, body = fetch(
                f"https://crt.sh/?q=%25.{zone}&output=json", timeout=40)
            if status != 200 or not body.strip().startswith("["):
                out.append(self.finding("inventory", f"crt.sh failed for {zone}",
                                        f"http={status}"))
                continue
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                continue
            names = set()
            for r in data:
                for n in str(r.get("name_value", "")).split("\n"):
                    n = n.strip().lower()
                    if n and "*" not in n:
                        names.add(n)
            out.append(self.finding(
                "inventory", f"crt.sh: {len(names)} subdomains under {zone}",
                detail="\n".join(sorted(names)[:200]),
                evidence=f"{len(names)} unique names"))
            ctx["state"].setdefault("subdomains", {})[zone] = sorted(names)
        return out


@register
class Headers(ToolAdapter):
    name = "headers"
    phase = "passive"
    description = "Security-header + tech fingerprint via response headers"

    def run(self, ctx):
        out = []
        for host in ctx["profile"].get("scope_hosts", []):
            url = f"https://{host}/"
            rc, head, _ = sh(
                f'curl -sI --max-time 20 "{url}"', timeout=30)
            if rc != 0 or not head:
                continue
            interesting = {}
            for line in head.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    k = k.strip().lower()
                    if k in ("server", "x-powered-by", "x-aspnet-version",
                             "via", "x-cache", "cf-ray", "x-amz-cf-id",
                             "strict-transport-security",
                             "content-security-policy",
                             "x-frame-options", "set-cookie"):
                        interesting[k] = v.strip()[:160]
            missing = [h for h in ("strict-transport-security",
                                   "content-security-policy", "x-frame-options")
                       if h not in interesting]
            out.append(self.finding(
                "fingerprint", f"headers: {host}",
                detail=json.dumps(interesting, indent=1)[:1500],
                evidence=f"missing: {', '.join(missing) or 'none'}"))
        return out


@register
class RobotsSitemap(ToolAdapter):
    name = "robots_sitemap"
    phase = "passive"
    description = "robots.txt + sitemap.xml path disclosure"

    def run(self, ctx):
        out = []
        for host in ctx["profile"].get("scope_hosts", []):
            for path in ("/robots.txt", "/sitemap.xml"):
                status, body = fetch(f"https://{host}{path}", timeout=20)
                if status == 200 and body.strip():
                    paths = re.findall(r"(?:Disallow|Allow|Sitemap):\s*(\S+)",
                                       body)
                    locs = re.findall(r"<loc>([^<]+)</loc>", body)[:50]
                    out.append(self.finding(
                        "paths", f"{host}{path} exposed",
                        detail="\n".join(paths[:40] + locs),
                        evidence=f"{len(paths) + len(locs)} entries"))
        return out


@register
class JsExtract(ToolAdapter):
    name = "js_extract"
    phase = "passive"
    description = "Fetch pages + JS bundles, extract API endpoints/params/flags"

    API_RE = re.compile(
        r'["\'`](/(?:api|v\d|graphql|rest)[A-Za-z0-9_\-./{}]*)["\'`]')
    PARAM_RE = re.compile(
        r'["\'`]([a-zA-Z][a-zA-Z0-9_]{2,30})["\'`]\s*:\s*(?:["\'`{[]|true|false|null|\d)')
    URL_RE = re.compile(
        r'https?://[A-Za-z0-9_\-.]+(?:\.[a-z]{2,})(?::\d+)?(?:/[A-Za-z0-9_\-./?=&%{}]*)?')

    def run(self, ctx):
        out = []
        prof = ctx["profile"]
        seeds = [f"https://{h}/" for h in prof.get("scope_hosts", [])]
        seeds += prof.get("seed_urls", [])
        bundles, endpoints, params, urls = set(), set(), set(), set()
        for seed in seeds[:8]:
            status, body = fetch(seed, timeout=25)
            if status != 200:
                continue
            for m in re.finditer(r'<script[^>]+src=["\']([^"\']+)["\']', body):
                bundles.add(urljoin(seed, m.group(1)))
        for b in list(bundles)[:12]:
            _, js = fetch(b, timeout=30)
            if not js:
                continue
            endpoints.update(self.API_RE.findall(js))
            params.update(p for p in self.PARAM_RE.findall(js)
                          if len(p) < 32)
            for u in self.URL_RE.findall(js):
                if urlparse(u).netloc:
                    urls.add(u.split("?")[0])
        interesting = sorted(urls)[:120]
        ctx["state"].setdefault("endpoints", []).extend(sorted(endpoints))
        ctx["state"].setdefault("params", []).extend(sorted(params)[:200])
        out.append(self.finding(
            "inventory", f"JS mining: {len(bundles)} bundles, "
                        f"{len(endpoints)} api paths, {len(params)} params, "
                        f"{len(urls)} urls",
            detail="ENDPOINTS:\n" + "\n".join(sorted(endpoints)[:120]) +
                   "\n\nURLS:\n" + "\n".join(interesting),
            evidence=f"{len(bundles)} bundles fetched"))
        # flag security-sensitive shapes for the funnel
        hot = [e for e in endpoints
               if re.search(r"token|session|auth|share|invit|admin|debug|"
                            r"internal|test|export|upload", e, re.I)]
        if hot:
            out.append(self.finding(
                "sensitive", f"{len(hot)} security-sensitive endpoint shapes",
                detail="\n".join(sorted(set(hot))[:60]),
                severity_hint="note"))
        return out


@register
class Wayback(ToolAdapter):
    name = "wayback"
    phase = "passive"
    description = "Wayback CDX: historic URLs of scope hosts (passive URL collection)"

    def run(self, ctx):
        out = []
        for host in ctx["profile"].get("scope_hosts", [])[:4]:
            status, body = fetch(
                f"https://web.archive.org/cdx/search/cdx?url={host}/*"
                f"&output=text&fl=original&collapse=urlkey&limit=4000",
                timeout=40)
            if status != 200:
                continue
            urls = [l.strip() for l in body.splitlines() if l.strip()]
            apiish = [u for u in urls
                      if re.search(r"/api|/v\d/|graphql|\.json|\?",
                                   u, re.I)][:120]
            out.append(self.finding(
                "inventory", f"wayback: {len(urls)} historic urls for {host}",
                detail="\n".join(apiish),
                evidence=f"{len(apiish)} api-shaped"))
            ctx["state"].setdefault("wayback_urls", {})[host] = len(urls)
        return out


@register
class GithubRecon(ToolAdapter):
    name = "github_recon"
    phase = "passive"
    description = "Official GitHub org repos (unauth API) — SDKs, docs, samples"

    def run(self, ctx):
        out = []
        for org in ctx["profile"].get("github_orgs", []):
            status, body = fetch(
                f"https://api.github.com/orgs/{org}/repos?per_page=100",
                timeout=25,
                headers={"Accept": "application/vnd.github+json",
                         "User-Agent": "deephunt-research"})
            if status != 200:
                out.append(self.finding("inventory",
                                        f"github org {org}: http={status}"))
                continue
            try:
                repos = json.loads(body)
            except json.JSONDecodeError:
                continue
            names = [r.get("full_name", "") for r in repos
                     if isinstance(r, dict)]
            kw = ctx["profile"].get("repo_keywords",
                                    ["sdk", "api", "sample", "docs"])
            hits = [n for n in names
                    if any(k in n.lower() for k in kw)]
            out.append(self.finding(
                "inventory", f"github {org}: {len(names)} repos",
                detail="\n".join(hits[:60]),
                evidence=f"{len(hits)} keyword hits"))
        return out


@register
class TechDetect(ToolAdapter):
    name = "tech_detect"
    phase = "passive"
    description = "Lightweight stack fingerprint (meta tags, js libs, headers)"

    def run(self, ctx):
        out = []
        for host in ctx["profile"].get("scope_hosts", [])[:4]:
            status, body = fetch(f"https://{host}/", timeout=25)
            if status != 200:
                continue
            sigs = []
            for pat, label in [
                (r"react|_react|react-dom", "react"),
                (r"vue(\.min)?\.js|__vue__", "vue"),
                (r"angular", "angular"),
                (r"next\.js|__NEXT_DATA__", "nextjs"),
                (r"graphql", "graphql"),
                (r"akamai|akamaized", "akamai-cdn"),
                (r"cloudflare", "cloudflare"),
                (r"adobe-ims|ims-na1", "adobe-ims"),
            ]:
                if re.search(pat, body, re.I):
                    sigs.append(label)
            out.append(self.finding(
                "fingerprint", f"stack: {host}",
                detail=", ".join(sigs) or "no signatures",
                evidence=f"{len(sigs)} signals"))
        return out


# ---------------------------------------------------------------------------
# Wave 2 — deeper passive arsenal
# ---------------------------------------------------------------------------
import os as _os

OPS = _os.path.expanduser("~/workspace/hacker-agent/ops/bin")


@register
class SubfinderTool(ToolAdapter):
    name = "subfinder"
    phase = "passive"
    description = "Subdomain enumeration via certificate + API sources"
    needs_bins = ()

    def available(self):
        return _os.path.isfile(_os.path.join(OPS, "subfinder"))

    def run(self, ctx):
        out = []
        zones = ctx["profile"].get("ct_zones", [])
        found = set(ctx["state"].get("subdomains", {}).get(zones[0], [])
                    if zones else [])
        for zone in zones[:3]:
            rc, so, _ = sh(f"{OPS}/subfinder -d {zone} -silent -max-time 5 "
                           f"-o /tmp/dh_subs.txt", timeout=420)
            try:
                subs = [l.strip() for l in open("/tmp/dh_subs.txt")
                        if l.strip()]
            except OSError:
                subs = []
            found.update(subs)
            out.append(self.finding(
                "inventory", f"subfinder: {len(subs)} subs for {zone}",
                detail="\n".join(sorted(subs)[:150]),
                evidence=f"rc={rc}"))
        ctx["state"].setdefault("all_subdomains", []).extend(sorted(found))
        ctx["state"]["all_subdomains"] = sorted(
            set(ctx["state"]["all_subdomains"]))
        return out


@register
class HttpxTool(ToolAdapter):
    name = "httpx"
    phase = "passive"
    description = "Probe discovered hosts: alive, title, tech, status"

    def available(self):
        return _os.path.isfile(_os.path.join(OPS, "httpx"))

    def run(self, ctx):
        subs = ctx["state"].get("all_subdomains", [])
        hosts = ctx["profile"].get("scope_hosts", [])
        targets = sorted(set(subs) | set(hosts))[:150]
        if not targets:
            return [self.finding("inventory", "httpx: no targets yet",
                                 "run crtsh/subfinder first")]
        with open("/tmp/dh_targets.txt", "w") as f:
            f.write("\n".join(targets))
        rc, _, _ = sh(
            f"{OPS}/httpx -l /tmp/dh_targets.txt -silent -json "
            f"-o /tmp/dh_httpx.jsonl -title -tech-detect -status-code "
            f"-tls-probe -cname -retries 1 -timeout 8 -threads 40",
            timeout=420)
        live, techs = [], {}
        try:
            import json as _j
            for line in open("/tmp/dh_httpx.jsonl"):
                line = line.strip()
                if not line:
                    continue
                d = _j.loads(line)
                url = d.get("url", "")
                live.append(url)
                for t in d.get("tech", []) or []:
                    techs[t] = techs.get(t, 0) + 1
        except OSError:
            pass
        ctx["state"]["live_hosts"] = live[:150]
        return [self.finding(
            "inventory", f"httpx: {len(live)} live of {len(targets)} probed",
            detail="TECH:\n" + "\n".join(f"{k} x{v}"
                                         for k, v in sorted(techs.items())),
            evidence=f"{len(live)} live")]


@register
class GauTool(ToolAdapter):
    name = "gau"
    phase = "passive"
    description = "Historic URL collection (wayback/otx/commoncrawl)"

    def available(self):
        return _os.path.isfile(_os.path.join(OPS, "gau"))

    def run(self, ctx):
        out = []
        for host in ctx["profile"].get("scope_hosts", [])[:4]:
            rc, so, _ = sh(f"echo {host} | {OPS}/gau --o /tmp/dh_gau.txt "
                           f"--threads 5", timeout=300)
            try:
                urls = [l.strip() for l in open("/tmp/dh_gau.txt") if l.strip()]
            except OSError:
                urls = []
            apiish = [u for u in urls
                      if "?" in u or "/api" in u][:150]
            out.append(self.finding(
                "inventory", f"gau: {len(urls)} urls for {host}",
                detail="\n".join(apiish),
                evidence=f"{len(apiish)} param/api urls"))
            ctx["state"].setdefault("gau_urls", {})[host] = len(urls)
        return out


@register
class UrlscanTool(ToolAdapter):
    name = "urlscan"
    phase = "passive"
    description = "urlscan.io: historic scans, URLs, tech, cookies of the target"

    def run(self, ctx):
        out = []
        for host in ctx["profile"].get("scope_hosts", [])[:3]:
            status, body = fetch(
                f"https://urlscan.io/api/v1/search/?q=domain:{host}&size=50",
                timeout=30)
            if status != 200:
                continue
            try:
                import json as _j
                data = _j.loads(body)
            except Exception:  # noqa: BLE001
                continue
            results = data.get("results", [])
            techs, urls = set(), []
            for r in results[:50]:
                page = r.get("page", {})
                urls.append(page.get("url", ""))
                for k in ("server", "ip"):
                    if page.get(k):
                        techs.add(f"{k}={page[k]}")
            out.append(self.finding(
                "inventory", f"urlscan: {len(results)} scans for {host}",
                detail="\n".join(u for u in urls[:60] if u) +
                       "\nTECH: " + ", ".join(sorted(techs)[:20]),
                evidence=f"{data.get('total', '?')} total"))
        return out


@register
class JsSecrets(ToolAdapter):
    name = "js_secrets"
    phase = "passive"
    description = "Scan JS bundles for leaked keys/tokens (type-only, never used)"

    PATTERNS = [
        (r"sk_live_[A-Za-z0-9]{16,}", "stripe-live-key"),
        (r"AKIA[0-9A-Z]{16}", "aws-access-key"),
        (r"xox[bap]-[A-Za-z0-9-]{10,}", "slack-token"),
        (r"ghp_[A-Za-z0-9]{20,}", "github-pat"),
        (r"AIza[0-9A-Za-z_-]{30,}", "google-api-key"),
        (r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]",
         "generic-api-key"),
        (r"(?i)(secret|client_secret)\s*[:=]\s*['\"][A-Za-z0-9_\-]{12,}['\"]",
         "generic-secret"),
    ]

    def run(self, ctx):
        import re as _re
        out, hits = [], []
        seeds = [f"https://{h}/"
                 for h in ctx["profile"].get("scope_hosts", [])[:3]]
        bundles = set()
        for seed in seeds:
            status, body = fetch(seed, timeout=25)
            if status != 200:
                continue
            from urllib.parse import urljoin as _uj
            for m in _re.finditer(r'<script[^>]+src=["\']([^"\']+)["\']', body):
                bundles.add(_uj(seed, m.group(1)))
        for b in list(bundles)[:10]:
            _, js = fetch(b, timeout=30)
            if not js:
                continue
            for pat, label in self.PATTERNS:
                if _re.search(pat, js):
                    hits.append(f"{label} in {b[:90]}")
        if hits:
            out.append(self.finding(
                "sensitive", f"{len(hits)} possible secrets in JS bundles",
                detail="\n".join(sorted(set(hits))[:30]) +
                       "\nVALIDATE BY TYPE ONLY — never use a found secret.",
                severity_hint="note"))
        else:
            out.append(self.finding("clean",
                                    f"js_secrets: {len(bundles)} bundles, "
                                    f"no key patterns"))
        return out


@register
class TakeoverCheck(ToolAdapter):
    name = "takeover"
    phase = "passive"
    description = "Dangling-CNAME subdomain takeover screen (passive DNS + fingerprints)"

    FINGERPRINTS = [
        ("github.io", "There isn't a GitHub Pages site here"),
        ("herokuapp.com", "No such app"),
        ("s3.amazonaws.com", "NoSuchBucket"),
        ("azureedge.net", "The resource you are looking for has been removed"),
        ("cloudfront.net", "Bad Request"),
        ("myshopify.com", "Sorry, this shop is currently unavailable"),
    ]

    def run(self, ctx):
        import re as _re
        subs = ctx["state"].get("all_subdomains", [])[:150]
        if not subs:
            return [self.finding("inventory", "takeover: no subdomains yet")]
        # parallel CNAME resolution (xargs -P), one line per sub
        with open("/tmp/dh_tosubs.txt", "w") as f:
            f.write("\n".join(subs))
        rc, so, _ = sh(
            "xargs -a /tmp/dh_tosubs.txt -P 20 -I{} sh -c "
            "'c=$(dig +short {} CNAME +time=5 +tries=1 | head -1); "
            "echo \"{} $c\"'", timeout=300)
        cnames = {}
        for line in so.splitlines():
            parts = line.split()
            if len(parts) == 2 and parts[1]:
                cnames[parts[0]] = parts[1].rstrip(".")
        cands = []
        for sub, cname in cnames.items():
            for svc, fp in self.FINGERPRINTS:
                if svc in cname:
                    st, body = fetch(f"https://{sub}/", timeout=15)
                    if fp.lower() in body.lower():
                        cands.append(f"{sub} -> {cname} [{svc} FINGERPRINT HIT]")
                    else:
                        cands.append(f"{sub} -> {cname} [{svc} check manually]")
        if cands:
            return [self.finding(
                "vuln-candidate", f"{len(cands)} possible dangling CNAMEs",
                detail="\n".join(cands[:40]) +
                       "\nCLAIM ONLY with program permission.",
                severity_hint="high")]
        return [self.finding("clean", "takeover: no dangling CNAMEs found",
                             f"{len(subs)} subs checked")]


@register
class CorsProbe(ToolAdapter):
    name = "cors_probe"
    phase = "passive"
    description = "CORS misconfiguration check (null/reflective origin)"

    def run(self, ctx):
        out = []
        targets = [f"https://{h}/"
                   for h in ctx["profile"].get("scope_hosts", [])[:6]]
        targets += ctx["state"].get("live_hosts", [])[:10]
        for url in targets[:12]:
            for origin in ("https://evil.example.com", "null"):
                rc, head, _ = sh(
                    f'curl -sk -m 15 -D - -o /dev/null -H "Origin: {origin}" '
                    f'"{url}"', timeout=25)
                acao = acc = ""
                for line in head.splitlines():
                    ll = line.lower()
                    if ll.startswith("access-control-allow-origin:"):
                        acao = line.split(":", 1)[1].strip()
                    if ll.startswith("access-control-allow-credentials:"):
                        acc = line.split(":", 1)[1].strip()
                if acao in (origin, "*") and (acc == "true" or acao == origin):
                    out.append(self.finding(
                        "vuln-candidate",
                        f"CORS: {url} reflects {origin} (ACAO={acao} ACAC={acc})",
                        detail=f"url={url} origin={origin}",
                        severity_hint="medium"))
        if not out:
            out.append(self.finding("clean", "cors_probe: no misconfig found",
                                     f"{len(targets)} targets"))
        return out


@register
class TlsInfo(ToolAdapter):
    name = "tls_info"
    phase = "passive"
    description = "TLS/certificate recon (openssl s_client, handshake only)"

    def run(self, ctx):
        out = []
        for host in ctx["profile"].get("scope_hosts", [])[:6]:
            rc, so, _ = sh(
                f"echo | openssl s_client -connect {host}:443 "
                f"-servername {host} 2>/dev/null | openssl x509 -noout "
                f"-subject -issuer -dates 2>/dev/null", timeout=25)
            if rc == 0 and so.strip():
                out.append(self.finding("fingerprint", f"tls cert: {host}",
                                         detail=so.strip()[:600]))
        return out


@register
class ParamMiner(ToolAdapter):
    name = "param_miner"
    phase = "passive"
    description = "Build param/endpoint wordlists from all findings (feeds ffuf)"

    def run(self, ctx):
        import re as _re
        blob = " ".join(f.get("detail", "") for f in ctx["state"]["findings"])
        params = set(_re.findall(r"[?&]([a-zA-Z][a-zA-Z0-9_]{2,24})=", blob))
        paths = set(_re.findall(r'["\'`\s](/[a-zA-Z0-9_\-/]{2,60})["\'`\s]',
                                blob))
        wl_dir = _os.path.join(_os.path.dirname(
            _os.path.abspath(__file__)), "..", "state", "wordlists")
        _os.makedirs(wl_dir, exist_ok=True)
        pp = _os.path.join(wl_dir, f"{ctx['target']}_params.txt")
        ep = _os.path.join(wl_dir, f"{ctx['target']}_paths.txt")
        open(pp, "w").write("\n".join(sorted(params)))
        open(ep, "w").write("\n".join(sorted(paths)))
        return [self.finding(
            "inventory", f"param_miner: {len(params)} params, {len(paths)} paths",
            detail=f"wordlists: {pp}, {ep}")]
