#!/usr/bin/env python3
"""proxy/search.py — Burp "search in HTTP history" for the mitmproxy traffic logs.

Searches logs/<date>/traffic.jsonl (JSONL request/response records from
addons/logger.py) by host, URL/path regex, status code, header, or body text.

Usage:
  python search.py --host robinhood.com --status 403
  python search.py --url-re "api/.*admin" --body-re "stack trace|Traceback"
  python search.py --header-re "x-powered-by" --days 7 --limit 20
  python search.py --method POST --type response

Read-only. Secrets are already redacted at log time by the logger addon.
"""
from __future__ import annotations
import argparse
import glob
import json
import os
import re
import sys

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")


def iter_records(days):
    paths = sorted(glob.glob(os.path.join(LOG_DIR, "*", "traffic.jsonl")))
    paths = paths[-max(1, days):]
    for p in paths:
        try:
            with open(p, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue
        except OSError:
            continue


def match(rec, args, url_re, body_re, header_re):
    if args.type and rec.get("type") != args.type:
        return False
    if args.method and rec.get("method", "").upper() != args.method.upper():
        return False
    url = rec.get("url", "")
    if args.host and args.host.lower() not in url.lower():
        return False
    if url_re and not url_re.search(url):
        return False
    if args.status is not None and rec.get("status") != args.status:
        return False
    if header_re:
        headers = rec.get("headers") or {}
        blob = "\n".join(f"{k}: {v}" for k, v in headers.items())
        if not header_re.search(blob):
            return False
    if body_re:
        body = rec.get("body_preview") or ""
        if not body_re.search(body):
            return False
    return True


def main():
    ap = argparse.ArgumentParser(description="Search proxy HTTP history")
    ap.add_argument("--host", help="substring match on URL")
    ap.add_argument("--url-re", help="regex on URL")
    ap.add_argument("--body-re", help="regex on body preview")
    ap.add_argument("--header-re", help="regex on headers blob")
    ap.add_argument("--status", type=int, help="response status code")
    ap.add_argument("--method", help="HTTP method")
    ap.add_argument("--type", choices=["request", "response"])
    ap.add_argument("--days", type=int, default=2, help="how many daily logs back")
    ap.add_argument("--limit", type=int, default=20)
    args = ap.parse_args()

    def comp(p):
        try:
            return re.compile(p, re.I) if p else None
        except re.error as e:
            print(f"bad regex: {e}", file=sys.stderr)
            sys.exit(1)

    url_re, body_re, header_re = comp(args.url_re), comp(args.body_re), comp(args.header_re)
    hits = 0
    for rec in iter_records(args.days):
        if not match(rec, args, url_re, body_re, header_re):
            continue
        hits += 1
        hdrs = rec.get("headers") or {}
        interesting = {k: v for k, v in hdrs.items()
                       if any(s in k.lower() for s in
                              ("server", "powered", "via", "cf-", "x-"))}
        print(f"[{rec.get('seq')}] {rec.get('type')} {rec.get('method')} "
              f"{rec.get('url', '')[:110]}"
              + (f" -> {rec.get('status')}" if rec.get("status") else ""))
        if interesting:
            print("    headers: " + "; ".join(f"{k}={v}" for k, v in
                                              list(interesting.items())[:6]))
        bp = (rec.get("body_preview") or "")[:220].replace("\n", " ")
        if bp:
            print(f"    body: {bp}")
        if hits >= args.limit:
            break
    print(f"\n{hits} match(es)")


if __name__ == "__main__":
    main()
