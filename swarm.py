#!/usr/bin/env python3
"""
SWARM — all-directions bug-bounty orchestrator (v1).
Passive recon + gentle active checks across EVERY in-scope target,
with per-program policy modes. Scope-locked: never touches out-of-scope hosts.

Policy modes (from intel/program-rules-matrix.md):
  passive : crt.sh + wayback + DNS only. For scanner-banned / manual-only
            programs, and targets already covered by deep agents.
  light   : passive + gentle single-request HTTP checks (headers, CORS,
            error mining, intel fingerprints, exposed files, redirects).

Usage:
  python3 swarm.py                       # everything
  python3 swarm.py --only aiven.io,agoda.com
  python3 swarm.py --list-modes          # show policy per target
"""
import sys, os, json, time, re, urllib.request, urllib.error, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hunter

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "data", "swarm")
os.makedirs(OUT, exist_ok=True)

DELAY = 1.2
TIMEOUT = 12
EVIL = "https://evil-swarm.example"

# Scanner-banned / manual-only / automation-ban / already-covered-by-deep-agents
PASSIVE_ONLY = {
    "booking.com", "fareharbor.com", "rentalcars.com",          # scanners explicitly banned
    "unibet.com", "mariacasino.com", "32red.com", "bingo.com",  # FDJ manual-only
    "superbank.id", "super-id.net", "coindcx.com",               # scanners banned
    "oda.com", "okta.com", "auth0.com",                         # manual-only / automation bans
    "aiven.io", "pinterest.com", "onetrust.com",                 # deep agents already active
}
UA_OVERRIDE = {"doctolib.com": "BugBounty/42 (YWH)"}  # program-required UA
INTERESTING = ("api", "staging", "stage", "dev", "test", "admin", "beta",
               "demo", "sandbox", "qa", "uat", "preprod", "internal")
EXPOSED_SUBSET = ["/.git/HEAD", "/.env", "/.well-known/security.txt",
                  "/server-status", "/backup.sql"]
REDIRECT_PROBES = ["/redirect?url=", "/login?next=", "/?next=",
                   "/logout?returnTo=", "/r?url="]
ERROR_HINTS = ("traceback", "stack trace", "psql", "postgres", "pg::",
               "syntax error", "exception", "ora-", "at java.",
               "django", "laravel", "whoops")


def log(msg):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def in_scope(host):
    host = host.lower().strip().rstrip(".")
    for root in hunter.load_scope():
        root = root.lower()
        if host == root or host.endswith("." + root):
            return True
    return False


def ua_for(root):
    return {"User-Agent": UA_OVERRIDE.get(root, hunter.UA["User-Agent"])}


def req(url, headers, method="GET", data=None, follow=True, timeout=TIMEOUT):
    h = dict(headers)
    if data is not None:
        h["Content-Type"] = "application/json"
    if follow:
        opener = urllib.request.build_opener()
    else:
        opener = urllib.request.build_opener(hunter._NoRedirect)
    rq = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with opener.open(rq, timeout=timeout) as r:
            return r.status, dict(r.headers), r.read(150000), None
    except urllib.error.HTTPError as e:
        try:
            body = e.read(150000)
        except Exception:
            body = b""
        return e.code, dict(e.headers), body, e.headers.get("Location")
    except Exception as e:
        return 0, {}, ("ERR:%s" % e).encode(), None


def text(b):
    return b.decode("utf-8", errors="ignore") if isinstance(b, bytes) else str(b)


def add_finding(store, target, host, direction, check, severity, evidence, url=""):
    store.append({"target": target, "host": host, "direction": direction,
                  "check": check, "severity": severity,
                  "evidence": evidence[:600], "url": url})
    log(f"  [{severity}] {host} :: {check}")


# ---------------- directions ----------------

def dir_passive(root, store):
    subs = hunter.crtsh_subdomains(root)
    urls = hunter.wayback_urls(root, limit=1500)
    tdir = os.path.join(OUT, root.replace(".", "_"))
    os.makedirs(tdir, exist_ok=True)
    json.dump(subs, open(os.path.join(tdir, "subdomains.json"), "w"), indent=1)
    open(os.path.join(tdir, "wayback.txt"), "w").write("\n".join(urls))
    log(f"{root}: passive -> {len(subs)} subdomains, {len(urls)} wayback URLs")
    leads = [u for u in urls if any(k in u.lower() for k in
             ("api", "admin", "config", "debug", ".json", "swagger", "graphql"))]
    for u in leads[:15]:
        add_finding(store, root, root, "wayback", "interesting archived URL",
                    "INFO", u, u)
    # takeover candidates via DNS only (no HTTP in passive mode)
    for s in subs:
        if not in_scope(s):
            continue
        cname = hunter.cname_of(s)
        if not cname:
            continue
        for svc, (frag, sig) in hunter.TAKEOVER_FPS.items():
            if frag in cname:
                add_finding(store, root, s, "takeover",
                            f"possible {svc} takeover (CNAME {cname})",
                            "MEDIUM",
                            f"CNAME -> {cname}; confirm unclaimed signature manually: '{sig}'")
                break
        time.sleep(0.3)
    return subs


def pick_hosts(root, subs):
    hosts = [root]
    for s in subs:
        if s != root and any(s.split(".")[0].startswith(p) for p in INTERESTING):
            hosts.append(s)
        if len(hosts) >= 6:
            break
    return [h for h in hosts if in_scope(h)]


def dir_headers(root, host, headers, store):
    s, h, b, _ = req(f"https://{host}/", headers)
    if s == 0:
        return
    missing = [x for x in ("content-security-policy",
                           "strict-transport-security",
                           "x-frame-options",
                           "x-content-type-options")
               if x not in {k.lower() for k in h}]
    if missing:
        add_finding(store, root, host, "headers", "missing security headers",
                    "LOW", "missing: " + ", ".join(missing), f"https://{host}/")
    disc = {k: v for k, v in h.items()
            if k.lower() in ("server", "x-powered-by", "x-aspnet-version")}
    if disc:
        add_finding(store, root, host, "headers", "version disclosure",
                    "INFO", json.dumps(disc), f"https://{host}/")
    time.sleep(DELAY)


def dir_cors(root, host, headers, store):
    h = dict(headers)
    h["Origin"] = EVIL
    s, rh, b, _ = req(f"https://{host}/", h)
    if s == 0:
        return
    acao = ""
    for k, v in rh.items():
        if k.lower() == "access-control-allow-origin":
            acao = v
    if EVIL in acao:
        add_finding(store, root, host, "cors", "arbitrary Origin reflected",
                    "LOW", f"Access-Control-Allow-Origin: {acao}", f"https://{host}/")
    elif acao == "*":
        add_finding(store, root, host, "cors", "wildcard ACAO", "INFO",
                    "Access-Control-Allow-Origin: *", f"https://{host}/")
    time.sleep(DELAY)


def dir_redirect(root, host, headers, store):
    for p in REDIRECT_PROBES:
        param = "url" if "url=" in p else ("next" if "next=" in p else "returnTo")
        url = f"https://{host}{p}{EVIL}"
        s, h, b, loc = req(url, headers, follow=False)
        if loc and "evil-swarm.example" in loc:
            add_finding(store, root, host, "redirect",
                        f"open redirect via {param}", "MEDIUM",
                        f"{s} -> Location: {loc}", url)
        time.sleep(DELAY)


def dir_fingerprints(root, host, headers, store):
    for name, path, match, sev, nxt in hunter.VULN_FPS:
        url = f"https://{host}{path}"
        s, h, b, _ = req(url, headers)
        try:
            if match(s, h, text(b)):
                add_finding(store, root, host, "fingerprint", name, sev,
                            f"{s} {path} :: {nxt}", url)
        except Exception:
            pass
        time.sleep(DELAY)


def dir_exposed(root, host, headers, store):
    for path in EXPOSED_SUBSET:
        url = f"https://{host}{path}"
        s, h, b, _ = req(url, headers)
        t = text(b)
        if path == "/.git/HEAD" and s == 200 and "ref:" in t:
            sev, ev = "HIGH", ".git exposed: " + t.strip()[:120]
        elif path == "/.env" and s == 200 and ("=" in t and len(t) > 20):
            sev, ev = "HIGH", ".env exposed (" + str(len(t)) + " bytes)"
        elif path == "/server-status" and s == 200 and "apache" in t.lower():
            sev, ev = "MEDIUM", "server-status exposed"
        elif s == 200 and len(t) > 100 and "not found" not in t.lower()[:200]:
            sev, ev = "LOW", f"{path} returned 200 ({len(t)} bytes)"
        else:
            time.sleep(DELAY)
            continue
        add_finding(store, root, host, "exposed", f"exposed file {path}",
                    sev, ev, url)
        time.sleep(DELAY)


def dir_errors(root, host, headers, store):
    for ep in ("/api", "/"):
        s, h, b, _ = req(f"https://{host}{ep}", headers, method="POST",
                         data=b'{"swarm":}')
        t = text(b).lower()
        hits = [x for x in ERROR_HINTS if x in t]
        if hits and s not in (0, 404):
            add_finding(store, root, host, "errors",
                        f"verbose error leakage at {ep}", "LOW",
                        f"{s} leaks: {', '.join(hits)}", f"https://{host}{ep}")
        time.sleep(DELAY)


def dir_takeover_light(root, subs, headers, store):
    for s in subs:
        if not in_scope(s):
            continue
        cname = hunter.cname_of(s)
        if not cname:
            continue
        for svc, (frag, sig) in hunter.TAKEOVER_FPS.items():
            if frag in cname:
                st, h, b, _ = req(f"https://{s}/", headers)
                if st and sig.lower() in text(b).lower():
                    add_finding(store, root, s, "takeover",
                                f"LIKELY {svc} takeover", "HIGH",
                                f"CNAME -> {cname}; body shows '{sig}'",
                                f"https://{s}/")
                else:
                    add_finding(store, root, s, "takeover",
                                f"possible {svc} takeover", "MEDIUM",
                                f"CNAME -> {cname} (signature not confirmed)",
                                f"https://{s}/")
                break
        time.sleep(0.5)


# ---------------- report ----------------

SEV_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}


def write_report(all_findings, targets_done):
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    path = os.path.join(BASE, "reports", f"swarm-report-{ts}.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    ordered = sorted(all_findings,
                     key=lambda f: (SEV_ORDER.get(f["severity"], 5), f["target"]))
    counts = {}
    for f in ordered:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1
    L = [f"# SWARM report — {ts}", "",
         f"Targets swept: {len(targets_done)} · "
         + ", ".join(f"{k}:{v}" for k, v in sorted(counts.items(),
                     key=lambda x: SEV_ORDER.get(x[0], 9))),
         "", "Modes: passive = recon only (scanner-banned/manual-only programs); "
         "light = + gentle single-request checks.", ""]
    cur = None
    for f in ordered:
        if f["target"] != cur:
            cur = f["target"]
            L += [f"## {cur}", ""]
        L += [f"- **[{f['severity']}]** `{f['host']}` — {f['check']}",
              f"  - direction: {f['direction']} · evidence: {f['evidence']}",
              f"  - {f['url']}" if f["url"] else "  - (no url)", ""]
    if not ordered:
        L += ["No findings. Targets are quiet at this layer — go manual.", ""]
    L += ["---", "_Candidates only. Confirm manually, then submit._"]
    open(path, "w").write("\n".join(L))
    return path, counts


def main():
    args = sys.argv[1:]
    if "--list-modes" in args:
        for t in sorted(hunter.load_scope()):
            print(f"{'passive' if t in PASSIVE_ONLY else 'light':8}  {t}")
        return
    only = set()
    if "--only" in args:
        i = args.index("--only")
        only = set(x.strip() for x in args[i + 1].split(","))
    targets = [t for t in hunter.load_scope() if t and (not only or t in only)]
    log(f"SWARM starting: {len(targets)} targets")
    all_findings, done = [], []
    for root in targets:
        mode = "passive" if root in PASSIVE_ONLY else "light"
        log(f"== {root} [{mode}] ==")
        store = []
        try:
            subs = dir_passive(root, store)
            if mode == "light":
                headers = ua_for(root)
                hosts = pick_hosts(root, subs)
                log(f"{root}: light probing {len(hosts)} hosts")
                for h in hosts:
                    dir_headers(root, h, headers, store)
                    dir_cors(root, h, headers, store)
                if hosts:
                    dir_redirect(root, hosts[0], headers, store)
                    dir_fingerprints(root, hosts[0], headers, store)
                    dir_exposed(root, hosts[0], headers, store)
                    dir_errors(root, hosts[0], headers, store)
                dir_takeover_light(root, subs, headers, store)
            tdir = os.path.join(OUT, root.replace(".", "_"))
            os.makedirs(tdir, exist_ok=True)
            json.dump(store, open(os.path.join(tdir, "findings.json"), "w"), indent=1)
            all_findings += store
            done.append(f"{root}[{mode}]")
        except KeyboardInterrupt:
            raise
        except Exception as e:
            log(f"{root}: ERROR {e}")
    path, counts = write_report(all_findings, done)
    log(f"SWARM done. Report: {path}")
    log("Counts: " + json.dumps(counts))


if __name__ == "__main__":
    main()
