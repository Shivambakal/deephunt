#!/usr/bin/env python3
"""
HUNTER — Shivam's bug-bounty recon agent (v1).
Passive recon + structured checks against IN-SCOPE targets only.

Usage:
  python hunter.py scope add <domain>        # authorize a target
  python hunter.py scope list
  python hunter.py recon <domain>            # subdomains (crt.sh) + wayback URLs
  python hunter.py takeover <domain>         # subdomain-takeover fingerprints
  python hunter.py expose <domain>           # common exposed files on live hosts
  python hunter.py report <domain>           # compile markdown report

Rules: scope-locked, low-volume, passive-first. It finds CANDIDATES;
you confirm and you submit. Never runs against anything not in scope.yaml.
"""
import argparse, json, os, re, socket, subprocess, sys, time, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
SCOPE_FILE = os.path.join(BASE, "scope.yaml")
DATA_DIR = os.path.join(BASE, "data")
REPORT_DIR = os.path.join(BASE, "reports")
UA = {"User-Agent": "Mozilla/5.0 (hackerone-shiva92)"}
DELAY = 1.0  # seconds between requests — stay quiet

# service -> (cname fragment, unclaimed signature in response body)
TAKEOVER_FPS = {
    "GitHub Pages": (".github.io", "There isn't a GitHub Pages site here"),
    "Heroku": (".herokuapp.com", "No such app"),
    "AWS S3": (".s3.amazonaws.com", "NoSuchBucket"),
    "Netlify": ("netlify.app", "Not Found - Request ID:"),
    "Vercel": ("vercel.app", "The deployment could not be found"),
    "Azure": (".azurewebsites.net", "404 Web Site not found"),
    "Shopify": (".myshopify.com", "Sorry, this shop is currently unavailable"),
    "Tumblr": (".tumblr.com", "There's nothing here."),
    "Fastly": (".fastly.net", "Fastly error: unknown domain"),
    "Pantheon": (".pantheonsite.io", "The gods are not at home"),
}

EXPOSED_PATHS = [
    "/.git/HEAD", "/.env", "/.well-known/security.txt",
    "/server-status", "/.DS_Store", "/wp-config.php.bak",
    "/config.php.bak", "/backup.sql", "/db.sql",
]

# Fingerprint probes: (name, path, match_fn(status, headers, body)->bool/str, severity, manual_next)
def _has(h, needle):
    return any(needle in str(v).lower() for v in h.values())

VULN_FPS = [
    ("Spring Actuator exposed", "/actuator",
     lambda s, h, b: s == 200 and "logfile" in b.lower(),
     "HIGH", "Try /actuator/logfile, /actuator/env MANUALLY (own session). Logfiles leak usernames/tokens."),
    ("Spring logfile readable", "/actuator/logfile",
     lambda s, h, b: s == 200 and len(b) > 500,
     "HIGH", "Read it — harvest usernames, then check auth endpoints for identifier-only login (Tyrion404 pattern)."),
    ("Swagger/OpenAPI exposed", "/v3/api-docs",
     lambda s, h, b: s == 200 and ("openapi" in b.lower() or "swagger" in b.lower()),
     "MEDIUM", "Enumerate every endpoint; auth endpoints are your targets."),
    ("Swagger UI exposed", "/swagger-ui.html",
     lambda s, h, b: s == 200 and "swagger" in b.lower(),
     "MEDIUM", "Same as above — map the API surface."),
    ("config.js with secrets", "/config.js",
     lambda s, h, b: s == 200 and any(k in b.lower() for k in ("apikey", "api_key", "sas", "client_secret")),
     "HIGH", "Extract keys/tokens; check what they unlock (read-only first)."),
    ("WordPress detected", "/wp-json/",
     lambda s, h, b: s == 200 and "wp" in b.lower(),
     "INFO", "Fingerprint version; check theme-preview / customizer endpoints (Click2Shell class)."),
    ("SharePoint detected", "/_layouts/15/",
     lambda s, h, b: s in (200, 401, 403),
     "INFO", "SharePoint present — check patch level vs CVE-2026-65660 class (SafeControls bypass). Manual only."),
    ("Google API key in page", "/",
     lambda s, h, b: bool(re.search(r"AIza[0-9A-Za-z_-]{35}", b)),
     "MEDIUM", "Key pattern in HTML/JS — check what APIs it enables. Do NOT validate keys that could incur charges."),
    ("n8n instance", "/",
     lambda s, h, b: _has(h, "n8n") or "n8n" in b.lower()[:2000],
     "INFO", "n8n detected — check version vs CVE-2026-21858 (<1.121.0). Fingerprint only; manual follow-up."),
    ("GeoNetwork instance", "/srv/api/info",
     lambda s, h, b: s == 200 and ("geonetwork" in b.lower() or "applicationversion" in b.lower()),
     "INFO", "GeoNetwork detected — grab version; >=4.0.6 flag CVE-2026-63219/58400 pre-auth RCE chain. Detect only, never upload formatters."),
    ("GeoNetwork instance (context path)", "/geonetwork/srv/api/info",
     lambda s, h, b: s == 200 and ("geonetwork" in b.lower() or "applicationversion" in b.lower()),
     "INFO", "Same as above — /geonetwork is the common context path."),
    ("GeoNetwork catalog UI", "/srv/eng/catalog.search",
     lambda s, h, b: s == 200 and "geonetwork" in b.lower(),
     "INFO", "Catalog UI confirms GeoNetwork — verify version via /srv/api/info; check SSRF/XSS endpoint existence only."),
    ("WordPress wp2shell-vulnerable version", "/",
     lambda s, h, b: s == 200 and "wp-content" in b and bool(
         re.search(r"(?:ver=|WordPress )(6\.9\.[0-4]|7\.0\.[01])\b", b)),
     "HIGH", "WordPress 6.9.0-6.9.4 / 7.0.0-7.0.1 — flag wp2shell pre-auth RCE class (/wp-json/batch/v1). Fingerprint only; NEVER send payloads."),
    ("FreePBX endpoint module reachable", "/admin/ajax.php",
     lambda s, h, b: s in (200, 401) and ("freepbx" in b.lower() or "endpoint" in b.lower()),
     "HIGH", "FreePBX — flag CVE-2025-57819 class (endpoint module SQLi->RCE). Check ?module=endpoint error shape (401 vs 500) only; NEVER inject."),
    ("AEM querybuilder/packmgr reachable", "/bin/querybuilder.json",
     lambda s, h, b: s == 200 and ('"hits"' in b or '"results"' in b or "querybuilder" in b.lower()),
     "MEDIUM", "Adobe AEM dispatcher bypass class — also probe /crx/packmgr/ and /adobe/dynamicmedia/deliver/ for direct-to-origin behavior."),
    ("Proxmox VE detected", "/api2/json/version",
     lambda s, h, b: s == 200 and '"version"' in b,
     "INFO", "Proxmox VE — banner-grab version; 7.x/EOL or 8.0-8.0.3 flag CVE-2023-54391 class. NEVER test the tfa-challenge bypass automatically."),
]

PLAYBOOKS = {
    "idor": """IDOR / BOLA checklist (your Phase 1 — own accounts only):
1. Map every object reference: /user/123, /api/orders?id=, /invoice/456.
2. Swap IDs between your two test accounts (progamee1414 <-> shivambakal).
3. Try: sequential IDs, UUIDs from other responses, negative/zero IDs, no ID at all.
4. Watch for: 200 with someone else's data, different error messages for valid vs invalid IDs.
5. Escalate: user -> other user -> low IDs (1, 2 — often admin/test/service accounts).
6. THE CHAIN (pankaj $4.5k pattern): if a profile-update endpoint takes user_id in the body,
   try changing the EMAIL on another (test) account -> if it sticks without verification,
   that's password-reset account takeover. Report it, don't complete the takeover on real users.
7. BLIND SEARCH ORACLE (kymu.dev pattern): if the app has global search, check whether it
   indexes fields hidden from your role (notes, emails, attachment names). With your LOW-priv
   account, search a substring that should be invisible to you — if result presence (200 vs
   empty) correlates with the hidden value, that's an oracle. One probe to confirm, then
   report. No mass-extraction loops on other people's data.""",
    "sso": """SSO / auth-bypass test (Tyrion404 pattern — own accounts only):
1. Find the login/SSO endpoint in JS or swagger.
2. Does it accept identifier-only JSON like {"username":"..."} or {"email":"..."}?
3. If it returns a token/session without password/MFA -> verify with YOUR OWN second account only.
4. Check: actuator/logfile or config.js for leaked usernames or API keys first.""",
    "ssti": """SSTI quick tests (HariHax pattern — only on fields you own, e.g. your profile/template):
1. Try {{7*7}} then ${7*7} then <%= 7*7 %> — see what renders as 49.
2. Email/preview/name fields are classic sinks.
3. If it renders: dump _context / config to map impact, then STOP and report.""",
    "2fa": """2FA bypass notes (whoareme CSPT pattern):
1. Try replaying the 2FA request with modified params; try __proto__ pollution in JSON bodies.
2. Test: does /verify accept any code? Does omitting the code field still pass?
3. Never brute-force codes — that's rate-limit territory and burns the account.""",
    "oauth-misconfig": """OAuth misconfiguration hunt (Mojaver/shafayat pattern — own accounts only):
1. GET /.well-known/oauth-authorization-server first — maps registration/token endpoints and auth methods.
2. If target is an OAuth PROVIDER: register with an unverified email you own; check whether the email claim is asserted as verified to relying parties.
3. POST the authorize endpoint with zero session cookies — a returned code/redirect without login is the loudest missing-auth signal.
4. Check redirect_uri validation: exact-match vs prefix vs regex — one loose validator = token theft. Never send crafted links to real users.""",
    "client-side-auth": """Client-side auth bypass (kuldeep.io pattern — your browser only):
1. Grep JS bundles for authRequired, isUserLoggedIn, localStorage/sessionStorage trust — the bundle IS the auth spec.
2. Replay 5-10 API calls with no token at all; data without auth = systemic server-side miss, report as ONE systemic bypass.
3. Match-and-replace session-response fields (null -> valid group/flag values) tests whether the UI is the only gate.""",
    "checkout-logic": """Checkout/business-logic (Zuksh pattern — own test account, stop before payment):
1. Baseline the full transaction: product -> cart -> preview -> order amounts, no mutations.
2. Mutate STATE not price: coupon apply/remove, quantity edits mid-flow, back-button/resume, parallel tabs.
3. The signal is the SERVER quoting a lower total. Document the state sequence, never complete an underpriced order.""",
    "ssrf": """SSRF hunt (XBOW Bing-RCE lesson — own test accounts, OOB to YOUR burp collaborator only):
1. Never close SSRF as informational — probe one parser layer deeper: upload/SVG/XML/avatar/thumbnail fields.
2. Differentials: SVG vs PNG content-type handling, XML error-shape changes, timing on internal vs external URLs.
3. Blind check: your collaborator/Interactsh domain as the callback — a hit = server-side fetch confirmed. Then map what internal targets are reachable, report, stop.""",
}


def load_scope():
    targets = []
    if os.path.exists(SCOPE_FILE):
        with open(SCOPE_FILE) as f:
            for line in f:
                line = line.strip()
                if line.startswith("- "):
                    targets.append(line[2:].strip())
                elif line and not line.startswith("#") and ":" in line:
                    targets.append(line.split(":", 1)[1].strip())
    return targets


def require_scope(domain):
    if domain not in load_scope():
        print(f"[!] '{domain}' is NOT in scope. Add it first:")
        print(f"    python hunter.py scope add {domain}")
        print("    Only hunt what you're authorized to hunt.")
        sys.exit(2)


def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # do not follow


def fetch_nr(url, timeout=15):
    """Fetch without following redirects. Returns (status, headers, body, redirect_target)."""
    opener = urllib.request.build_opener(_NoRedirect)
    req = urllib.request.Request(url, headers=UA)
    try:
        with opener.open(req, timeout=timeout) as r:
            return r.status, dict(r.headers), r.read(200000), None
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read(200000), e.headers.get("Location")


def crtsh_subdomains(domain):
    url = f"https://crt.sh/?q=%25.{domain}&output=json"
    try:
        _, raw = fetch(url)
        data = json.loads(raw)
    except Exception as e:
        print(f"[!] crt.sh failed: {e}")
        return []
    names = set()
    for e in data:
        for n in e.get("name_value", "").split("\n"):
            n = n.strip().lower().rstrip(".")
            if n and "*" not in n and n.endswith(domain):
                names.add(n)
    return sorted(names)


def wayback_urls(domain, limit=2000):
    url = (f"http://web.archive.org/cdx/search/cdx?url=*.{domain}/*"
           f"&output=text&fl=original&collapse=urlkey&limit={limit}")
    try:
        _, raw = fetch(url, timeout=30)
        urls = [u for u in raw.decode(errors="ignore").splitlines() if u.strip()]
        return sorted(set(urls))
    except Exception as e:
        print(f"[!] wayback failed: {e}")
        return []


def cname_of(host):
    try:
        out = subprocess.run(["nslookup", "-type=CNAME", host],
                             capture_output=True, text=True, timeout=10).stdout
        m = re.findall(r"canonical name\s*=\s*(\S+)", out, re.I)
        return m[0].rstrip(".") if m else None
    except Exception:
        return None


def host_alive(host):
    for scheme in ("https", "http"):
        try:
            req = urllib.request.Request(f"{scheme}://{host}", headers=UA,
                                         method="HEAD")
            with urllib.request.urlopen(req, timeout=8) as r:
                return scheme, r.status
        except Exception:
            continue
    return None, 0


def cmd_scope(args):
    if args.action == "add":
        d = args.domain.lower()
        targets = load_scope()
        if d not in targets:
            with open(SCOPE_FILE, "a") as f:
                f.write(f"- {d}\n")
            print(f"[+] {d} added to scope.")
        else:
            print(f"[=] {d} already in scope.")
    elif args.action == "list":
        for t in load_scope():
            print(f"  - {t}")
    elif args.action == "remove":
        targets = [t for t in load_scope() if t != args.domain.lower()]
        with open(SCOPE_FILE, "w") as f:
            for t in targets:
                f.write(f"- {t}\n")
        print(f"[-] {args.domain} removed from scope.")


def cmd_recon(args):
    d = args.domain.lower()
    require_scope(d)
    os.makedirs(DATA_DIR, exist_ok=True)
    print(f"[*] crt.sh subdomains for {d} ...")
    subs = crtsh_subdomains(d)
    time.sleep(DELAY)
    print(f"[*] wayback URLs for {d} ...")
    urls = wayback_urls(d)
    out = {"domain": d, "subdomains": subs, "wayback_urls": urls,
           "counts": {"subdomains": len(subs), "urls": len(urls)}}
    path = os.path.join(DATA_DIR, f"{d}-recon.json")
    json.dump(out, open(path, "w"), indent=1)
    print(f"[+] {len(subs)} subdomains, {len(urls)} wayback URLs -> {path}")


def cmd_takeover(args):
    d = args.domain.lower()
    require_scope(d)
    path = os.path.join(DATA_DIR, f"{d}-recon.json")
    if not os.path.exists(path):
        print("[!] run recon first: python hunter.py recon " + d)
        sys.exit(1)
    subs = json.load(open(path))["subdomains"]
    print(f"[*] checking {len(subs)} subdomains for takeover fingerprints ...")
    hits = []
    for s in subs:
        cn = cname_of(s)
        if not cn:
            continue
        for svc, (frag, sig) in TAKEOVER_FPS.items():
            if frag in cn:
                try:
                    _, body = fetch(f"https://{s}", timeout=10)
                    if sig.lower() in body.decode(errors="ignore").lower():
                        hits.append({"host": s, "cname": cn, "service": svc,
                                     "note": "UNCLAIMED signature found — verify manually, then claim-test per program rules"})
                        print(f"  [!] POSSIBLE TAKEOVER: {s} -> {cn} ({svc})")
                    else:
                        print(f"  [.] {s} -> {cn} ({svc}, claimed)")
                except Exception as e:
                    print(f"  [?] {s} -> {cn} ({svc}, fetch failed: {e})")
                break
        time.sleep(DELAY)
    json.dump(hits, open(os.path.join(DATA_DIR, f"{d}-takeover.json"), "w"), indent=1)
    print(f"[+] {len(hits)} candidates saved.")


def cmd_expose(args):
    d = args.domain.lower()
    require_scope(d)
    path = os.path.join(DATA_DIR, f"{d}-recon.json")
    if not os.path.exists(path):
        print("[!] run recon first: python hunter.py recon " + d)
        sys.exit(1)
    subs = json.load(open(path))["subdomains"][:40]  # cap: stay quiet
    print(f"[*] probing {len(subs)} live hosts x {len(EXPOSED_PATHS)} paths (low volume) ...")
    hits = []
    for s in subs:
        scheme, code = host_alive(s)
        if not scheme:
            continue
        try:
            cst, _, cbody, _ = fetch_nr(f"{scheme}://{s}/__hunter_canary_{os.urandom(4).hex()}", timeout=10)
            canary = (cst, cbody[:200])
        except Exception:
            canary = (None, b"")
        for p in EXPOSED_PATHS:
            try:
                st, hdrs, body, redir = fetch_nr(f"{scheme}://{s}{p}", timeout=10)
                if st in (301, 302, 303, 307, 308):
                    continue  # parked/redirect host, not a real hit
                if (st, body[:200]) == canary:
                    continue  # soft-404: identical response to nonexistent path
                txt = body.decode(errors="ignore")
                interesting = st == 200 and len(txt.strip()) > 0 and "not found" not in txt.lower()[:200]
                if interesting and not (p == "/.well-known/security.txt" and st == 200):
                    hits.append({"url": f"{scheme}://{s}{p}", "status": st,
                                 "size": len(body), "preview": txt[:120].replace("\n", " ")})
                    print(f"  [!] {st} {scheme}://{s}{p} ({len(body)}b)")
                elif p == "/.well-known/security.txt" and st == 200:
                    print(f"  [.] security.txt exists on {s} (read it — it names the scope)")
            except Exception:
                pass
            time.sleep(DELAY)
    json.dump(hits, open(os.path.join(DATA_DIR, f"{d}-exposed.json"), "w"), indent=1)
    print(f"[+] {len(hits)} findings saved.")


def notable_subs(subs):
    kw = ("api", "dev", "stg", "stage", "qa", "sandbox", "admin", "partner",
          "pay", "secure", "auth", "candidate", "backoffice")
    return [s for s in subs if any(k in s for k in kw)][:25]


def cmd_fp(args):
    """Fingerprint a single host with VULN_FPS (scope-checked)."""
    s = args.host.lower()
    # scope check: host must end with a scoped root
    require_scope(s if s.count(".") == 1 else ".".join(s.split(".")[-2:]))
    scheme, code = host_alive(s)
    if not scheme:
        print(f"[!] {s} not reachable"); return
    try:
        cst, _, cbody, _ = fetch_nr(f"{scheme}://{s}/__hunter_canary_{os.urandom(4).hex()}", timeout=10)
        canary = (cst, cbody[:200])
    except Exception:
        canary = (None, b"")
    hits = []
    for name, p, match, sev, nxt in VULN_FPS:
        try:
            st, hdrs, body, redir = fetch_nr(f"{scheme}://{s}{p}", timeout=10)
            if st in (301, 302, 303, 307, 308):
                continue
            if (st, body[:200]) == canary:
                continue
            txt = body.decode(errors="ignore")
            if match(st, hdrs, txt):
                hits.append({"host": s, "check": name, "severity": sev,
                             "url": f"{scheme}://{s}{p}", "next": nxt})
                print(f"  [{sev}] {name} on {s}{p}")
        except Exception:
            pass
        time.sleep(DELAY)
    print(f"[+] {len(hits)} fingerprint hits on {s}.")


def cmd_vuln(args):
    d = args.domain.lower()
    require_scope(d)
    path = os.path.join(DATA_DIR, f"{d}-recon.json")
    if not os.path.exists(path):
        print("[!] run recon first: python hunter.py recon " + d)
        sys.exit(1)
    subs = json.load(open(path))["subdomains"]
    targets = notable_subs(subs)
    print(f"[*] fingerprinting {len(targets)} notable hosts ...")
    hits = []
    for s in targets:
        scheme, code = host_alive(s)
        if not scheme:
            continue
        try:
            # canary: random nonexistent path — catches gateways that 200 every path
            cst, _, cbody, _ = fetch_nr(f"{scheme}://{s}/__hunter_canary_{os.urandom(4).hex()}", timeout=10)
            canary = (cst, cbody[:200])
        except Exception:
            canary = (None, b"")
        for name, p, match, sev, nxt in VULN_FPS:
            try:
                st, hdrs, body, redir = fetch_nr(f"{scheme}://{s}{p}", timeout=10)
                if st in (301, 302, 303, 307, 308):
                    continue  # redirect = not a real hit; parked host
                if (st, body[:200]) == canary:
                    continue  # soft-404: identical response to nonexistent path
                txt = body.decode(errors="ignore")
                res = match(st, hdrs, txt)
                if res:
                    hits.append({"host": s, "check": name, "severity": sev,
                                 "url": f"{scheme}://{s}{p}", "next": nxt})
                    print(f"  [{sev}] {name} on {s}{p}")
            except Exception:
                pass
            time.sleep(DELAY)
    json.dump(hits, open(os.path.join(DATA_DIR, f"{d}-vuln.json"), "w"), indent=1)
    print(f"[+] {len(hits)} fingerprint hits saved.")


def cmd_ports(args):
    import shutil
    d = args.domain.lower()
    require_scope(d)
    if not shutil.which("nmap"):
        print("[!] nmap not installed yet — install running in background, retry shortly.")
        return
    host = getattr(args, "host", None)
    if host:
        targets = [host]
    else:
        path = os.path.join(DATA_DIR, f"{d}-recon.json")
        if not os.path.exists(path):
            print("[!] run recon first: python hunter.py recon " + d)
            sys.exit(1)
        subs = json.load(open(path))["subdomains"]
        targets = notable_subs(subs)[:12]
    print(f"[*] light port scan (top 100, T2) on {len(targets)} host(s) ...")
    results = []
    for t in targets:
        try:
            out = sp.run(["nmap", "-T2", "--top-ports", "100", "--open", "-oG", "-", t],
                         capture_output=True, text=True, timeout=300).stdout
            ports = [ln for ln in out.splitlines() if "Ports:" in ln]
            info = ports[0].split("Ports:")[1].strip() if ports else "no open ports in top 100"
            results.append({"host": t, "open": info})
            print(f"  {t}: {info[:160]}")
        except Exception as e:
            results.append({"host": t, "open": f"scan failed: {e}"})
    json.dump(results, open(os.path.join(DATA_DIR, f"{d}-ports.json"), "w"), indent=1)
    print(f"[+] port results saved.")


def cmd_playbook(args):
    name = args.name.lower()
    if name == "list":
        print("playbooks: " + ", ".join(PLAYBOOKS))
    elif name in PLAYBOOKS:
        print(PLAYBOOKS[name])
    else:
        print(f"[!] unknown playbook '{name}'. Try: hunter.py playbook list")


def cmd_ai(args):
    """Ask the connected LLM to prioritize recon findings and suggest next tests."""
    import subprocess as sp
    d = args.domain.lower()
    require_scope(d)
    bundle = {}
    for name in ("recon", "takeover", "exposed", "vuln"):
        p = os.path.join(DATA_DIR, f"{d}-{name}.json")
        if os.path.exists(p):
            data = json.load(open(p))
            if name == "recon":
                data = {"counts": data.get("counts"),
                        "notable": notable_subs(data.get("subdomains", [])),
                        "wayback_sample": data.get("wayback_urls", [])[:40]}
            bundle[name] = data
    if not bundle:
        print("[!] no data yet — run recon first")
        sys.exit(1)
    prompt = ("You are a bug-bounty mentor using strict evidence discipline. Given this recon "
              "bundle for an IN-SCOPE authorized target, output at most 5 hypotheses in this "
              "exact structure each:\nHYPOTHESIS: <one line>\nEVIDENCE FOR: <exact data point from the bundle>\n"
              "EVIDENCE AGAINST: <what weakens it>\nFALSIFYING TEST: <one manual test using only the researcher's own test accounts, and what result would kill the hypothesis>\n"
              "STATUS: open\n\nNo theory, no generic advice. Bundle:\n\n" + json.dumps(bundle)[:6000])
    try:
        out = sp.run([sys.executable, os.path.expanduser("~/workspace/skills/openai/bin/ask.py"),
                      "--system", "You are a terse bug-bounty mentor.", prompt],
                     capture_output=True, text=True, timeout=120)
        hyps = out.stdout or out.stderr
        print(hyps)
        # adversarial validator pass: a second instance rewarded for disproof
        critic = sp.run([sys.executable, os.path.expanduser("~/workspace/skills/openai/bin/ask.py"),
                         "--system", ("You are a hostile validator. Your job is to KILL these "
                                      "hypotheses: find the flaw, the false positive, the missing auth "
                                      "context. Keep only what survives. Be brutal and brief."),
                         "Kill or confirm each hypothesis:\n\n" + hyps[:4000]],
                        capture_output=True, text=True, timeout=120)
        print("\n--- ADVERSARIAL VALIDATOR ---")
        print(critic.stdout or critic.stderr)
    except Exception as e:
        print(f"[!] AI call failed: {e}")


def cmd_report(args):
    d = args.domain.lower()
    require_scope(d)
    os.makedirs(REPORT_DIR, exist_ok=True)
    recon = json.load(open(os.path.join(DATA_DIR, f"{d}-recon.json"))) if os.path.exists(os.path.join(DATA_DIR, f"{d}-recon.json")) else {}
    lines = [f"# Hunter report — {d}", "", f"_Generated {time.strftime('%Y-%m-%d %H:%M')}_", ""]
    if recon:
        lines += [f"- Subdomains: {recon['counts']['subdomains']}", f"- Wayback URLs: {recon['counts']['urls']}", ""]
        lines += ["## Notable subdomains", ""]
        kw = ("api", "dev", "stg", "stage", "qa", "sandbox", "admin", "partner",
              "pay", "secure", "auth", "candidate", "backoffice")
        for s in recon["subdomains"]:
            if any(k in s for k in kw):
                lines.append(f"- {s}")
        lines += [""]
    for name, title in (("takeover", "Takeover candidates"), ("exposed", "Exposed files"),
                        ("vuln", "Vulnerability fingerprints")):
        p = os.path.join(DATA_DIR, f"{d}-{name}.json")
        if os.path.exists(p):
            items = json.load(open(p))
            lines += [f"## {title} ({len(items)})", ""]
            for it in items:
                lines.append(f"- {json.dumps(it)}")
            lines += [""]
    lines += ["## Next (manual, your part)",
              "- Pick one candidate above, verify by hand in your own session.",
              "- Confirm it's in the program's scope before touching it further.",
              "- Write the report: what you did, what you saw, impact, repro steps."]
    rp = os.path.join(REPORT_DIR, f"{d}-report.md")
    open(rp, "w").write("\n".join(lines))
    print(f"[+] report -> {rp}")


def main():
    ap = argparse.ArgumentParser(prog="hunter", description="Bug-bounty recon agent (scope-locked)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scope"); s.add_argument("action", choices=["add", "list", "remove"])
    s.add_argument("domain", nargs="?"); s.set_defaults(f=cmd_scope)
    for name, fn, h in [("recon", cmd_recon, "passive recon"),
                        ("takeover", cmd_takeover, "takeover fingerprints"),
                        ("expose", cmd_expose, "exposed-file probes"),
                        ("vuln", cmd_vuln, "vulnerability-class fingerprints (intel-driven)"),
                        ("report", cmd_report, "compile report")]:
        p = sub.add_parser(name, help=h); p.add_argument("domain"); p.set_defaults(f=fn)
    fp = sub.add_parser("fp", help="fingerprint a single host (in-scope only)")
    fp.add_argument("host"); fp.set_defaults(f=cmd_fp)
    pt = sub.add_parser("ports", help="light nmap port scan (top 100, T2, in-scope only)")
    pt.add_argument("domain"); pt.add_argument("--host", default=None)
    pt.set_defaults(f=cmd_ports)
    pb = sub.add_parser("playbook", help="manual test checklists"); pb.add_argument("name")
    pb.set_defaults(f=cmd_playbook)
    ai = sub.add_parser("ai", help="LLM prioritization of findings"); ai.add_argument("domain")
    ai.set_defaults(f=cmd_ai)

    args = ap.parse_args()
    if args.cmd == "scope" and args.action in ("add", "remove") and not args.domain:
        ap.error("domain required")
    args.f(args)


if __name__ == "__main__":
    main()
