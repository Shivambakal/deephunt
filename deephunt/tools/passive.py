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
    description = ("Probe discovered hosts: alive, title, tech, status "
                   "(proxy-aware)")

    def available(self):
        return _os.path.isfile(_os.path.join(OPS, "httpx"))

    def _proxy_env_ready(self):
        """Make sure the egress-proxy env reaches the httpx child process.

        httpx honors HTTP_PROXY/HTTPS_PROXY/NO_PROXY (and falls back to the
        lowercase forms), so traffic routes through the authenticated egress
        proxy WITHOUT putting proxy credentials on a command line. We only
        mirror lowercase -> uppercase for the in-process env; nothing new is
        persisted anywhere.
        """
        env = _os.environ
        for low, up in (("http_proxy", "HTTP_PROXY"),
                        ("https_proxy", "HTTPS_PROXY"),
                        ("all_proxy", "ALL_PROXY")):
            if env.get(low) and not env.get(up):
                env[up] = env[low]
        return bool(env.get("HTTPS_PROXY") or env.get("https_proxy")
                    or env.get("ALL_PROXY") or env.get("all_proxy"))

    def run(self, ctx):
        from .base import egress_profile
        out = []
        env = egress_profile()
        shimmed = bool(env.get("dns_shimmed"))
        if shimmed:
            out.append(self.finding(
                "env", "system DNS shimmed -> httpx via egress proxy",
                detail=(f"system resolver said example.com = "
                        f"{env.get('system_answer')}; DoH "
                        f"({env.get('doh_provider')}) said "
                        f"{env.get('doh_answer')}. httpx's own DNS fields "
                        f"(a/cname) are shim garbage here, so -cname is "
                        f"dropped; HTTP itself routes through the egress "
                        f"proxy. TLS certs seen through the proxy are "
                        f"sandbox-MITM forged — fingerprints are not "
                        f"target-attributable."),
                evidence="dns-shim-detected"))
            if not self._proxy_env_ready():
                return out + [self.finding(
                    "broken", "httpx: no egress-proxy env in shimmed sandbox",
                    "https_proxy/HTTPS_PROXY missing — running httpx would "
                    "dial the shimmed resolver and silently produce nothing; "
                    "refusing to run",
                    evidence="no-proxy-env")]
        subs = ctx["state"].get("all_subdomains", [])
        hosts = ctx["profile"].get("scope_hosts", [])
        targets = sorted(set(subs) | set(hosts))[:150]
        if not targets:
            return out + [self.finding("inventory", "httpx: no targets yet",
                                       "run crtsh/subfinder first")]
        with open("/tmp/dh_targets.txt", "w") as f:
            f.write("\n".join(targets))
        # -cname needs real DNS; in the shim it returns 198.18.x.x garbage.
        cname_flag = "" if shimmed else "-cname"
        rc, _, _ = sh(
            f"{OPS}/httpx -l /tmp/dh_targets.txt -silent -json "
            f"-o /tmp/dh_httpx.jsonl -title -tech-detect -status-code "
            f"-tls-probe {cname_flag} -retries 1 -timeout 8 -threads 40 "
            f"< /dev/null",  # httpx also ingests stdin; close it or it hangs
            timeout=420)
        live, techs = [], {}
        try:
            import json as _j
            for line in open("/tmp/dh_httpx.jsonl"):
                line = line.strip()
                if not line:
                    continue
                d = _j.loads(line)
                if d.get("failed"):
                    continue
                url = d.get("url", "")
                live.append(url)
                for t in d.get("tech", []) or []:
                    techs[t] = techs.get(t, 0) + 1
        except OSError:
            pass
        ctx["state"]["live_hosts"] = live[:150]
        return out + [self.finding(
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
    description = "Dangling-CNAME subdomain takeover screen (proxy-aware DoH DNS + fingerprints)"

    FINGERPRINTS = [
        ("github.io", "There isn't a GitHub Pages site here"),
        ("herokuapp.com", "No such app"),
        ("s3.amazonaws.com", "NoSuchBucket"),
        ("azureedge.net", "The resource you are looking for has been removed"),
        ("cloudfront.net", "Bad Request"),
        ("myshopify.com", "Sorry, this shop is currently unavailable"),
    ]

    @staticmethod
    def fingerprint_hit(body, cname):
        """Return (service, phrase) if a takeover fingerprint matches the
        fetched body for this CNAME, else None. Pure logic: unit-testable."""
        bl = (body or "").lower()
        for svc, fp in TakeoverCheck.FINGERPRINTS:
            if svc in cname and fp.lower() in bl:
                return svc, fp
        return None

    def run(self, ctx):
        from .base import egress_profile
        try:
            import doh_dns
        except ImportError:
            return [self.finding(
                "broken", "takeover: doh_dns module unavailable",
                "proxy-aware DNS resolver not importable; DNS path would be "
                "shimmed garbage — refusing to run", evidence="doh_dns-missing")]
        out = []
        env = egress_profile()
        if env.get("dns_shimmed"):
            out.append(self.finding(
                "env", "system DNS shimmed -> using DoH via egress proxy",
                detail=f"system resolver said example.com = "
                       f"{env.get('system_answer')}; DoH ({env.get('doh_provider')}) "
                       f"said {env.get('doh_answer')}",
                evidence="dns-shim-detected"))
        subs = ctx["state"].get("all_subdomains", [])[:150]
        if not subs:
            return out + [self.finding("inventory",
                                       "takeover: no subdomains yet")]
        # passive only: DoH queries hit public resolvers, never the targets
        results = doh_dns.resolve_bulk(subs, qtype="CNAME", delay=0.5)
        failed = [r["name"] for r in results if r["error"]]
        if len(failed) == len(results):
            return out + [self.finding(
                "broken", "takeover: all DoH queries failed",
                detail=results[0].get("error") or "unknown",
                evidence="doh-all-failed")]
        cnames = {}
        for r in results:
            if r["error"]:
                continue
            for a in r["answers"]:
                if a["type"] == "CNAME":
                    cnames[r["name"]] = a["data"].rstrip(".")
                    break
        cands, checked = [], []
        for sub, cname in cnames.items():
            svc = next((s for s, _ in self.FINGERPRINTS if s in cname), None)
            if not svc:
                continue
            chain = doh_dns.resolve_cname_chain(sub)
            chain_txt = " -> ".join(chain["chain"])
            st, body = fetch(f"https://{sub}/", timeout=15)
            hit = self.fingerprint_hit(body, cname)
            if hit:
                svc, fp = hit
                cands.append(
                    f"{sub} -> {cname} [{svc} FINGERPRINT HIT: {fp!r}] "
                    f"(chain: {chain_txt}; http={st})")
            else:
                checked.append(f"{sub} -> {cname} [{svc} no fingerprint "
                               f"(http={st})]")
        if failed:
            out.append(self.finding(
                "env", f"takeover: {len(failed)}/{len(subs)} DoH lookups failed",
                detail="\n".join(failed[:20]),
                evidence="partial-doh-failure"))
        if cands:
            return out + [self.finding(
                "vuln-candidate", f"{len(cands)} possible dangling CNAMEs",
                detail="\n".join(cands[:40]) +
                       "\nCLAIM ONLY with program permission.",
                severity_hint="high")]
        return out + [self.finding(
            "clean", "takeover: no dangling CNAMEs found",
            f"{len(cnames)} cnames resolved of {len(subs)} subs checked; "
            f"{len(checked)} fingerprinted services re-verified clean")]


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


# ---------------------------------------------------------------------------
# 2026-10-07 daily build — protocol-recon honesty pass.
# t100-wafw00f and t100-testssl graduate from the generic "completed (rc=0)"
# stdout-dump factory to hand-built, proxy-aware adapters with structured
# findings. TlsInfo stops silently producing nothing when direct TLS is
# impossible (this sandbox: shimmed DNS + blocked egress + MITM proxy, so
# cert data is never target-attributable here).
# ---------------------------------------------------------------------------

def _mirror_proxy_env():
    """Mirror lowercase proxy env -> uppercase so child tools see it.

    Mirrors in-process env only; never on a command line, never persisted.
    Returns True when some proxy env is present.
    """
    env = _os.environ
    for low, up in (("http_proxy", "HTTP_PROXY"),
                    ("https_proxy", "HTTPS_PROXY"),
                    ("all_proxy", "ALL_PROXY")):
        if env.get(low) and not env.get(up):
            env[up] = env[low]
    return bool(env.get("HTTPS_PROXY") or env.get("https_proxy")
                or env.get("ALL_PROXY") or env.get("all_proxy"))


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(text):
    return _ANSI_RE.sub("", text or "")


@register
class Wafw00fTool(ToolAdapter):
    name = "t100-wafw00f"
    phase = "passive"
    description = ("WAF fingerprinting via wafw00f (proxy-aware, parsed "
                   "JSON findings)")

    def available(self):
        return _os.path.isfile(_os.path.join(OPS, "wafw00f"))

    @staticmethod
    def parse_report(text):
        """Parse wafw00f output -> [{url, detected, firewall, manufacturer}].

        Prefers the machine JSON (`-o - -f json`); falls back to the human
        text lines. The trigger_url field (attack payloads) is deliberately
        dropped — firewall/manufacturer/url is the finding, the payload
        is not evidence we need to persist.
        """
        out, seen = [], set()
        clean = _strip_ansi(text)
        try:
            data = json.loads(clean[clean.index("["):clean.rindex("]") + 1])
        except (ValueError, IndexError):
            data = []
        for row in data if isinstance(data, list) else []:
            url = str(row.get("url", "")).strip()
            if not url or url in seen:
                continue
            seen.add(url)
            out.append({"url": url,
                        "detected": bool(row.get("detected")),
                        "firewall": str(row.get("firewall") or "").strip(),
                        "manufacturer": str(row.get("manufacturer") or "").strip()})
        if out:
            return out
        # text fallback: "[+] The site <url> is behind <name> WAF."
        for line in clean.splitlines():
            m = re.search(
                r"The site (\S+) is behind (.+?) WAF\.?", line)
            if m and m.group(1) not in seen:
                seen.add(m.group(1))
                out.append({"url": m.group(1), "detected": True,
                            "firewall": m.group(2).strip(),
                            "manufacturer": ""})
            m2 = re.search(r"The site (\S+) is not behind (?:a|any) WAF", line)
            if m2 and m2.group(1) not in seen:
                seen.add(m2.group(1))
                out.append({"url": m2.group(1), "detected": False,
                            "firewall": "", "manufacturer": ""})
        return out

    def run(self, ctx):
        from .base import egress_profile
        out = []
        shimmed = bool(egress_profile().get("dns_shimmed"))
        proxy_ok = _mirror_proxy_env()
        if shimmed:
            out.append(self.finding(
                "env", "wafw00f via egress proxy (TLS MITM'd here)",
                detail=("System DNS is shimmed and direct egress is blocked, "
                        "so wafw00f's HTTP requests ride the egress proxy. "
                        "WAF verdicts come from real HTTP responses behind "
                        "the proxy; certificate-layer data here is sandbox-"
                        "MITM forged and is NOT used for attribution."),
                evidence="dns-shimmed-proxy-mode"))
            if not proxy_ok:
                return out + [self.finding(
                    "broken", "wafw00f: no proxy env in shimmed sandbox",
                    "https_proxy/HTTPS_PROXY missing — refusing to run",
                    evidence="no-proxy-env")]
        hosts = [h for h in ctx["profile"].get("scope_hosts", []) if h][:8]
        if not hosts:
            return out + [self.finding("error", "wafw00f: no scope_hosts",
                                       "profile has no usable scope_hosts")]
        for host in hosts:
            url = host if host.startswith("http") else f"https://{host}"
            rc, so, se = sh(
                f"{OPS}/wafw00f {url} -o - -f json < /dev/null",
                timeout=120)
            rows = self.parse_report(so or "")
            if rows:
                for r in rows:
                    if r["detected"] and r["firewall"]:
                        out.append(self.finding(
                            "fingerprint",
                            f"WAF detected on {r['url']}: {r['firewall']}"
                            + (f" ({r['manufacturer']})"
                               if r["manufacturer"] else ""),
                            detail=(f"firewall={r['firewall']} "
                                    f"manufacturer={r['manufacturer'] or 'n/a'} "
                                    f"url={r['url']}"),
                            evidence=f"wafw00f:{r['firewall']}"))
                    else:
                        out.append(self.finding(
                            "clean", f"no WAF detected on {r['url']}",
                            evidence="wafw00f:detected=false"))
            elif rc != 0:
                out.append(self.finding(
                    "error", f"wafw00f failed on {url} (rc={rc})",
                    detail=_strip_ansi((se or so or ""))[:500],
                    evidence=f"rc={rc}"))
            else:
                out.append(self.finding(
                    "error", f"wafw00f unparseable output on {url}",
                    "rc=0 but no JSON rows and no text verdict parsed — "
                    "NOT counted as a clean result",
                    evidence="unparseable"))
        return out


@register
class TestsslTool(ToolAdapter):
    name = "t100-testssl"
    phase = "passive"
    description = ("TLS/SSL configuration testing via testssl.sh "
                   "(honest env-gate in sandbox, parsed findings)")

    def available(self):
        return _os.path.isfile(_os.path.join(OPS, "testssl.sh"))

    @staticmethod
    def parse_findings(text, host):
        """Parse testssl.sh --fast output into structured findings.

        Unit-testable; runs only on real networks (the sandbox path refuses
        to execute the binary — see run()).
        """
        clean = _strip_ansi(text)
        findings = []
        weak_protos = []
        for line in clean.splitlines():
            s = line.strip()
            if "VULNERABLE" in s and "not " not in s.lower().split(
                    "VULNERABLE")[0][-12:]:
                # conservative: the literal token VULNERABLE on a result line
                name = re.sub(r"\s+", " ",
                              re.split(r"VULNERABLE", s, 1)[0]).strip(" -")
                findings.append(("vuln", f"TLS vuln on {host}: {name}",
                                 s[:300], "high"))
            m = re.match(r"(SSLv2|SSLv3|TLS1|TLS1_1)\s+offered", s)
            if m:
                weak_protos.append(m.group(1))
            if re.search(r"certificate.*(expired|not yet valid)", s,
                         re.IGNORECASE):
                findings.append(("vuln", f"TLS cert problem on {host}",
                                 s[:300], "medium"))
        if weak_protos:
            findings.append(
                ("vuln", f"weak TLS protocols offered on {host}: "
                         f"{', '.join(sorted(set(weak_protos)))}",
                 "deprecated protocol versions accepted", "medium"))
        return findings

    def run(self, ctx):
        from .base import egress_profile
        env = egress_profile()
        if env.get("dns_shimmed"):
            # PROVEN 2026-10-07 live: testssl.sh cannot work from this
            # sandbox. It resolves the target AND the proxy through the
            # shimmed system DNS (example.com -> 198.18.53.129, proxy ->
            # 198.18.53.128), then "Proxy timed out. Unable to CONNECT via
            # proxy" — the shimmed proxy IP is unreachable. --proxy auto
            # additionally fatals on the proxy URL userinfo
            # ("Proxy IP cannot be determined"). And even a working CONNECT
            # would only see the sandbox-MITM cert (issuer "Hatch Sandbox
            # Egress CA"), never the target's real TLS config. Running it
            # anyway would manufacture false negatives — so we refuse.
            return [self.finding(
                "env", "testssl.sh cannot run from this sandbox",
                detail=(f"system DNS shimmed (example.com -> "
                        f"{env.get('system_answer')}); testssl.sh resolves "
                        f"target+proxy via system DNS -> fake 198.18.x.x, "
                        f"CONNECT times out (verified live 2026-10-07). "
                        f"--proxy auto also fatals on proxy-URL userinfo. "
                        f"Direct TCP 443 is blocked, and TLS through the "
                        f"egress proxy is MITM'd (issuer 'Hatch Sandbox "
                        f"Egress CA'), so no target-attributable TLS data "
                        f"is obtainable from here."),
                evidence="shimmed-dns-no-direct-tcp-mitm-proxy"),
                self.finding(
                "env", "testssl.sh: no TLS verdict from here — NOT evidence "
                       "the target's TLS is safe",
                detail=("On a real (non-shimmed) network this adapter runs "
                        "`testssl.sh --fast <host>` and parses VULNERABLE / "
                        "weak-protocol / cert-expiry findings. From the "
                        "sandbox the correct result is no data, stated "
                        "plainly, never a fake clean bill of health."),
                evidence="no-attempt-made")]
        hosts = [h for h in ctx["profile"].get("scope_hosts", []) if h][:3]
        if not hosts:
            return [self.finding("error", "testssl: no scope_hosts",
                                 "profile has no usable scope_hosts")]
        out = []
        for host in hosts:
            rc, so, se = sh(f"{OPS}/testssl.sh --fast {host} < /dev/null",
                            timeout=600)
            parsed = self.parse_findings(so or "", host)
            for kind, title, detail, sev in parsed:
                out.append(self.finding(kind, title, detail=detail,
                                        evidence=f"testssl:{host}",
                                        severity_hint=sev))
            if not parsed:
                out.append(self.finding(
                    "clean" if rc == 0 else "error",
                    f"testssl.sh --fast {host}: "
                    f"{'no issues parsed' if rc == 0 else f'failed (rc={rc})'}",
                    detail=_strip_ansi((se or "")[-400:])))
        return out


# TlsInfo honesty fix (same file, same build): direct openssl s_client dials
# the shimmed resolver and blocked egress, so it silently returned nothing.
# Now it says so explicitly instead of manufacturing an empty result.
_orig_tlsinfo_run = TlsInfo.run


def _tlsinfo_run_honest(self, ctx):
    from .base import egress_profile
    env = egress_profile()
    if env.get("dns_shimmed"):
        return [self.finding(
            "env", "tls_info: direct TLS fingerprinting unavailable here",
            detail=(f"openssl s_client -connect dials the shimmed system "
                    f"resolver (example.com -> {env.get('system_answer')}) "
                    f"and direct TCP is blocked; via the egress proxy the "
                    f"sandbox CA MITMs TLS (issuer 'Hatch Sandbox Egress "
                    f"CA'), so certificate data is not target-attributable. "
                    f"Skipping — NOT evidence of TLS health."),
            evidence="shimmed-dns-mitm-proxy")]
    return _orig_tlsinfo_run(self, ctx)


TlsInfo.run = _tlsinfo_run_honest
