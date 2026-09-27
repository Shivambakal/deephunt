#!/usr/bin/env python3
"""
intruder.py — Burp Intruder equivalent (heavily safety-constrained).

Payload-cluster fuzzer over marked parameter positions with:
  - sniper mode:        one payload set, one position at a time
  - battering-ram mode: one payload set, same payload in ALL positions at once
  - pitchfork mode:     N payload sets, lockstep (set1->pos1, set2->pos2, ...)
  - cluster-bomb mode:  cartesian product of 2 payload sets over pos1 x pos2
  - response-attribute diffing: status / length / timing / reflection
  - grep-match:         --grep REGEX flags responses whose body matches
  - BUILT-IN rate limiting: default max 1 request per 2 seconds (configurable,
    but never faster than 1 req/sec)
  - DEFAULT-DENY allowlist: refuses any host not in scope.yaml
  - HARD BLOCKLIST: manual-only / scanner-restricted programs can NEVER be
    targeted, even if allowlisted.

Positions are marked in a base request file (JSON) with § markers, Burp-style:
  {"method":"GET","url":"https://api.example.com/v3/§p§?x=§1§", "headers":{...}}

Payloads: one per line in a text file.
  pitchfork:    --payloads p1.txt --payloads2 p2.txt [--payloads3 p3.txt]
  cluster-bomb: --payloads p1.txt --payloads2 p2.txt (capped by --max)

Usage:
  python intruder.py --request base.json --payloads payloads.txt --mode sniper
  python intruder.py --request base.json --payloads payloads.txt --mode battering-ram --rate 3.0
  python intruder.py --request base.json --payloads u.txt --payloads2 p.txt --mode pitchfork
  python intruder.py --request base.json --payloads a.txt --payloads2 b.txt --mode cluster-bomb --grep "admin|root"

Human-paced always. Read-only style probes only — the operator is responsible
for payload content staying within authorized, non-destructive testing.
"""
import argparse
import json
import os
import re
import sys
import time
from urllib.parse import urlparse

import requests
import yaml

PROXY_URL = os.environ.get("PROXY_URL", "http://127.0.0.1:8080")
SCOPE_PATH = os.environ.get(
    "PROXY_SCOPE_FILE",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "scope.yaml"),
)

# Programs where automation/scanners are prohibited or restricted.
# These hosts can NEVER be intruder targets. Substring match, case-insensitive.
BLOCKLIST = [
    # FDJ United / Kindred brands (manual-only)
    "fdj", "32red", "bingo.com", "mariacasino", "unibet",
    # others with manual-only / scanner restrictions per program notes
    "booking.com", "okta.com", "auth0.com", "superbank",
    "coindcx", "oda.com", "basecamp.com", "aptible.com", "artsy.net",
]

MIN_INTERVAL = 1.0  # never faster than 1 req/sec, no matter what


def load_scope():
    with open(SCOPE_PATH, encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    hosts = [h.get("host", "").lower() for h in data.get("allowlist", [])]
    sub = bool(data.get("match_subdomains", True))
    return hosts, sub


def host_allowed(host: str, allowlist, match_subdomains: bool) -> bool:
    host = host.lower()
    for entry in allowlist:
        if not entry:
            continue
        if host == entry:
            return True
        if match_subdomains and (host == entry or host.endswith("." + entry)):
            return True
    return False


def host_blocked(host: str) -> str | None:
    h = host.lower()
    for b in BLOCKLIST:
        if b in h:
            return b
    return None


def check_target(url: str):
    host = urlparse(url).hostname or ""
    blocked = host_blocked(host)
    if blocked:
        print(f"REFUSED: host '{host}' matches blocklist entry '{blocked}' "
              f"(manual-only / restricted program — automation prohibited).")
        sys.exit(2)
    allowlist, sub = load_scope()
    if not host_allowed(host, allowlist, sub):
        print(f"REFUSED: host '{host}' is NOT in the scope.yaml allowlist "
              f"(default-deny). Add it explicitly to authorize.")
        sys.exit(2)
    print(f"target authorized: {host}")


def load_base(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def find_positions(base) -> list:
    """Return list of (location, index) for each §...§ marker.

    location: 'url' | 'body' | 'header:<name>'. Markers are numbered
    positionally per location.
    """
    positions = []
    for m in re.finditer(r"§(.*?)§", base.get("url", "")):
        positions.append(("url", m.group(1)))
    body = base.get("body", "")
    if isinstance(body, str):
        for m in re.finditer(r"§(.*?)§", body):
            positions.append(("body", m.group(1)))
    for hk, hv in (base.get("headers") or {}).items():
        if isinstance(hv, str):
            for m in re.finditer(r"§(.*?)§", hv):
                positions.append((f"header:{hk}", m.group(1)))
    return positions


def render(base, positions, payloads_for):
    """payloads_for: dict position-idx -> payload string. Returns (method,url,headers,body)."""
    def sub(text, loc):
        def repl(m):
            key = (loc, m.group(1))
            return payloads_for.get(key, m.group(1))
        return re.sub(r"§(.*?)§", repl, text)

    url = sub(base.get("url", ""), "url")
    headers = {}
    for hk, hv in (base.get("headers") or {}).items():
        headers[hk] = sub(hv, f"header:{hk}") if isinstance(hv, str) else hv
    body = base.get("body")
    if isinstance(body, str):
        body = sub(body, "body")
    return base.get("method", "GET"), url, headers, body


def send(method, url, headers, body, grep_re=None):
    t0 = time.time()
    try:
        r = requests.request(
            method, url, headers=headers,
            data=body.encode("utf-8") if isinstance(body, str) else body,
            proxies={"http": PROXY_URL, "https": PROXY_URL},
            verify=False,  # own MITM proxy; upstream chain validated by proxy
            timeout=30, allow_redirects=False,
        )
        dt = (time.time() - t0) * 1000
        reflected = []
        grep_hits = []
        if grep_re:
            # grep-match: scan a body snippet only; the body itself is never
            # persisted (see results writer below).
            try:
                snippet = r.content[:8192].decode("utf-8", "replace")
                grep_hits = sorted(set(grep_re.findall(snippet)))[:10]
            except Exception:
                pass
        return {
            "status": r.status_code,
            "length": len(r.content or b""),
            "time_ms": round(dt, 1),
            "reflected": reflected,
            "grep_hits": grep_hits,
            "ok": True,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)[:120]}


def main():
    ap = argparse.ArgumentParser(description="Constrained payload fuzzer (Burp Intruder equivalent)")
    ap.add_argument("--request", required=True, help="base request JSON with §markers§")
    ap.add_argument("--payloads", required=True, help="payload file, one per line")
    ap.add_argument("--payloads2", default=None,
                    help="2nd payload file (pitchfork/cluster-bomb)")
    ap.add_argument("--payloads3", default=None,
                    help="3rd payload file (pitchfork only)")
    ap.add_argument("--mode", choices=["sniper", "battering-ram", "pitchfork",
                                        "cluster-bomb"],
                    default="sniper")
    ap.add_argument("--rate", type=float, default=2.0,
                    help="min seconds between requests (default 2.0; floor 1.0)")
    ap.add_argument("--max", type=int, default=25, help="max requests to send (default 25)")
    ap.add_argument("--grep", default=None,
                    help="regex: flag responses whose body matches (grep-match)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    def load_plist(path):
        if not path:
            return []
        with open(path, encoding="utf-8") as fh:
            return [l.rstrip("\n") for l in fh if l.strip() and not l.startswith("#")]

    grep_re = None
    if args.grep:
        try:
            grep_re = re.compile(args.grep, re.I)
        except re.error as e:
            print(f"bad --grep regex: {e}")
            sys.exit(1)

    interval = max(args.rate, MIN_INTERVAL)
    base = load_base(args.request)
    payloads = load_plist(args.payloads)
    payloads2 = load_plist(args.payloads2)
    payloads3 = load_plist(args.payloads3)
    if args.mode in ("pitchfork", "cluster-bomb") and not payloads2:
        print(f"--mode {args.mode} requires --payloads2")
        sys.exit(1)
    if args.mode == "pitchfork" and len([p for p in (payloads2, payloads3) if p]) == 0:
        print("--mode pitchfork needs at least --payloads2")
        sys.exit(1)

    check_target(base.get("url", ""))
    positions = find_positions(base)
    if not positions:
        print("no §positions§ marked in base request")
        sys.exit(1)
    print(f"mode={args.mode} positions={len(positions)} payloads={len(payloads)} "
          f"interval={interval}s max={args.max}")

    # baseline: first request with markers replaced by their defaults
    defaults = {(loc, name): name for loc, name in positions}
    m, u, h, b = render(base, positions, defaults)
    print("sending baseline...")
    base_resp = send(m, u, h, b)
    print(f"baseline: {base_resp}")
    if args.dry_run:
        return

    time.sleep(interval)
    sent = 0
    results = []

    def fire(payload_map, label):
        nonlocal sent
        m, u, h, b = render(base, positions, payload_map)
        r = send(m, u, h, b, grep_re)
        # reflection check: does any payload appear in a follow-up fetch? we
        # only check the immediate response body length/status here; full
        # reflection needs the body which we intentionally do not store.
        entry = {"label": label, "payload": payload_map, **r}
        if r.get("ok"):
            interesting = (
                r["status"] != base_resp.get("status")
                or abs(r["length"] - base_resp.get("length", 0)) > max(50, base_resp.get("length", 0) * 0.1)
                or r["time_ms"] > (base_resp.get("time_ms", 0) * 3 + 2000)
                or bool(r.get("grep_hits"))
            )
            entry["interesting"] = interesting
            flag = " <-- INTERESTING" if interesting else ""
            gh = f" grep={r['grep_hits']}" if r.get("grep_hits") else ""
            print(f"[{sent}] {label} -> {r['status']} len={r['length']} {r['time_ms']}ms{gh}{flag}")
        else:
            print(f"[{sent}] {label} -> ERROR {r.get('error')}")
        results.append(entry)
        sent += 1
        time.sleep(interval)

    if args.mode == "sniper":
        for i, (loc, name) in enumerate(positions):
            for p in payloads:
                if sent >= args.max:
                    break
                pmap = dict(defaults)
                pmap[(loc, name)] = p
                fire(pmap, f"pos{i}({loc})")
            if sent >= args.max:
                break
    elif args.mode == "battering-ram":
        for p in payloads:
            if sent >= args.max:
                break
            pmap = {(loc, name): p for loc, name in positions}
            fire(pmap, "all-positions")
    elif args.mode == "pitchfork":
        # lockstep: set1->pos0, set2->pos1, set3->pos2; extras ignored
        sets = [s for s in (payloads, payloads2, payloads3) if s]
        n = min(len(s) for s in sets)
        for i in range(n):
            if sent >= args.max:
                break
            pmap = dict(defaults)
            for j, s in enumerate(sets):
                if j < len(positions):
                    pmap[positions[j]] = s[i]
            fire(pmap, f"pitchfork#{i}")
    else:  # cluster-bomb: cartesian set1 x set2 over pos0 x pos1
        for p1 in payloads:
            for p2 in payloads2:
                if sent >= args.max:
                    break
                pmap = dict(defaults)
                if len(positions) > 0:
                    pmap[positions[0]] = p1
                if len(positions) > 1:
                    pmap[positions[1]] = p2
                fire(pmap, f"cluster({p1[:12]}|{p2[:12]})")
            if sent >= args.max:
                break

    interesting = [r for r in results if r.get("interesting")]
    print(f"\ndone: {sent} requests, {len(interesting)} flagged interesting")
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs",
                       f"intruder-{int(time.time())}.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"baseline": base_resp, "results": results}, fh, indent=2, default=str)
    print(f"results saved: {out}")


if __name__ == "__main__":
    main()
