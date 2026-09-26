#!/usr/bin/env python3
"""
repeater.py — Burp Repeater equivalent.

Take a request captured by the proxy logger (addons/logger.py), tweak it,
resend it, and diff the response against the original.

Usage:
  # list recent logged requests
  python repeater.py --list [--n 20]

  # resend a logged request unchanged (baseline)
  python repeater.py --seq 42 --send

  # tweak and resend: change method, headers, query params, body
  python repeater.py --seq 42 --send \
      --method POST \
      --header "X-Custom: 1" --remove-header "X-Research-Session" \
      --param "debug=1" --remove-param "tracking_id" \
      --body '{"a":1}' --content-type "application/json"

  # diff against a specific logged response (default: the response logged
  # right after the chosen request)
  python repeater.py --seq 42 --send --compare-seq 43

Environment:
  PROXY_URL     proxy to send through, e.g. http://127.0.0.1:8080 (default)
  PROXY_LOG_DIR log dir override (default: proxy/logs)
"""
import argparse
import difflib
import json
import os
import sys
import time
from urllib.parse import urlparse, parse_qsl, urlencode

import requests

PROXY_URL = os.environ.get("PROXY_URL", "http://127.0.0.1:8080")
LOG_DIR = os.environ.get(
    "PROXY_LOG_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs"),
)


def load_records():
    recs = []
    if not os.path.isdir(LOG_DIR):
        return recs
    for day in sorted(os.listdir(LOG_DIR)):
        p = os.path.join(LOG_DIR, day, "traffic.jsonl")
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        try:
                            recs.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
    return recs


def find_request(recs, seq):
    for r in recs:
        if r.get("seq") == seq and r.get("type") == "request":
            return r
    return None


def find_following_response(recs, seq):
    for r in recs:
        if r.get("type") == "response" and r.get("seq", -1) > seq:
            return r
    return None


def apply_tweaks(req, args):
    method = args.method or req["method"]
    url = req["url"]
    headers = dict(req.get("headers", {}))
    # strip redacted placeholders — operator must supply real values if needed
    headers = {k: v for k, v in headers.items() if v != "[REDACTED]"}
    body = None

    for h in args.header or []:
        k, _, v = h.partition(":")
        headers[k.strip()] = v.strip()
    for h in args.remove_header or []:
        headers.pop(h, None)
        # case-insensitive fallback
        for k in list(headers):
            if k.lower() == h.lower():
                headers.pop(k, None)

    parts = urlparse(url)
    pairs = parse_qsl(parts.query, keep_blank_values=True)
    for p in args.param or []:
        k, _, v = p.partition("=")
        pairs = [(a, b) for a, b in pairs if a != k] + [(k, v)]
    for p in args.remove_param or []:
        pairs = [(a, b) for a, b in pairs if a != p]
    url = parts._replace(query=urlencode(pairs)).geturl()

    if args.body is not None:
        body = args.body.encode("utf-8")
        if args.content_type:
            headers["Content-Type"] = args.content_type
    return method, url, headers, body


def send(method, url, headers, body):
    t0 = time.time()
    # verify=False: we route through our own MITM proxy, whose CA is not in
    # the system store. The proxy already validated the upstream chain.
    resp = requests.request(
        method, url, headers=headers, data=body,
        proxies={"http": PROXY_URL, "https": PROXY_URL},
        verify=False,
        timeout=30, allow_redirects=False,
    )
    dt = (time.time() - t0) * 1000
    return resp, dt


def summarize_diff(orig, new):
    """orig/new: dicts with status, headers, body_len, body_preview."""
    out = []
    if orig.get("status") != new.get("status"):
        out.append(f"STATUS {orig.get('status')} -> {new.get('status')}")
    else:
        out.append(f"status unchanged ({new.get('status')})")
    ol, nl = orig.get("body_len"), new.get("body_len")
    if ol != nl:
        out.append(f"LENGTH {ol} -> {nl} (delta {nl - ol:+d})")
    else:
        out.append(f"length unchanged ({nl})")
    oh = {k.lower() for k in (orig.get("headers") or {})}
    nh = {k.lower() for k in (new.get("headers") or {})}
    added = sorted(nh - oh)
    removed = sorted(oh - nh)
    if added:
        out.append("headers added: " + ", ".join(added))
    if removed:
        out.append("headers removed: " + ", ".join(removed))
    for hk in ("content-type", "cache-control", "x-cache", "cf-cache-status", "location"):
        ov = (orig.get("headers") or {}).get(hk) or (orig.get("headers") or {}).get(hk.title())
        nv = (new.get("headers") or {}).get(hk) or (new.get("headers") or {}).get(hk.title())
        if ov != nv and (ov or nv):
            out.append(f"header {hk}: {ov!r} -> {nv!r}")
    ob = (orig.get("body_preview") or "").splitlines()
    nb = (new.get("body_preview") or "").splitlines()
    if ob != nb:
        diff = list(difflib.unified_diff(ob, nb, n=2))
        out.append(f"body diff ({len(diff)} diff lines):")
        out.extend(diff[:40])
        if len(diff) > 40:
            out.append(f"... truncated ({len(diff) - 40} more)")
    else:
        out.append("body identical (preview)")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="Burp-Repeater-equivalent resend + diff")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--seq", type=int, help="logged request seq to resend")
    ap.add_argument("--send", action="store_true")
    ap.add_argument("--compare-seq", type=int, help="logged response seq to diff against")
    ap.add_argument("--method")
    ap.add_argument("--header", action="append")
    ap.add_argument("--remove-header", action="append")
    ap.add_argument("--param", action="append", help="k=v to set")
    ap.add_argument("--remove-param", action="append")
    ap.add_argument("--body")
    ap.add_argument("--content-type")
    args = ap.parse_args()

    recs = load_records()
    if args.list:
        reqs = [r for r in recs if r.get("type") == "request"][-args.n:]
        for r in reqs:
            print(f"[{r['seq']}] {r['method']} {r['url']}")
        return

    if args.seq is None:
        ap.error("--seq required (or use --list)")
    req = find_request(recs, args.seq)
    if not req:
        print(f"no logged request with seq={args.seq}")
        sys.exit(1)

    method, url, headers, body = apply_tweaks(req, args)
    print(f">>> {method} {url}")
    print(f">>> headers: {len(headers)}, body: {len(body) if body else 0} bytes")

    if not args.send:
        print("(dry run — add --send to transmit)")
        return

    # human pacing: single resend only; caller is responsible for pacing
    resp, dt = send(method, url, headers, body)
    new = {
        "status": resp.status_code,
        "headers": dict(resp.headers),
        "body_len": len(resp.content or b""),
        "body_preview": (resp.text or "")[:2048],
    }
    print(f"<<< {resp.status_code} {len(resp.content or b'')} bytes in {dt:.0f}ms")

    if args.compare_seq is not None:
        orig_rec = next((r for r in recs if r.get("seq") == args.compare_seq), None)
        orig = orig_rec
    else:
        orig = find_following_response(recs, args.seq)
    if not orig:
        print("no baseline response found to diff against")
        return
    print("=== DIFF vs baseline ===")
    print(summarize_diff(orig, new))


if __name__ == "__main__":
    main()
