#!/usr/bin/env python3
"""DEEPHUNT news watcher: ongoing ingestion of vulnerability/bug/hack news.

Sources (all free, no auth):
  - Hacker News Algolia API: security-keyword stories from the last 24h
  - CISA Known Exploited Vulnerabilities catalog: newly added entries
  - BleepingComputer RSS: latest security news

Output:
  - intel/news/YYYY-MM-DD.md ............ human-readable daily digest
  - intel/news/seen.json ................ watermark (no duplicates)
  - intel/news/signals.jsonl ............ candidate learning signals for the
                                           knowledge pipeline (one JSON per line:
                                           {date, source, title, url, why})

Usage: python3 news_watcher.py [--days N]
Designed to run on a cron every 6 hours.
"""
from __future__ import annotations

import datetime
import json
import os
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEWS_DIR = os.path.join(BASE, "intel", "news")
SEEN_FILE = os.path.join(NEWS_DIR, "seen.json")
SIGNALS_FILE = os.path.join(NEWS_DIR, "signals.jsonl")

HN_QUERIES = ["vulnerability", "CVE", "data breach", "ransomware",
              "zero-day", "bug bounty", "supply chain attack"]
CISA_KEV = ("https://www.cisa.gov/sites/default/files/feeds/"
            "known_exploited_vulnerabilities.json")
BC_RSS = "https://www.bleepingcomputer.com/feed/"


def _get(url: str, timeout: int = 25) -> bytes | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "DEEPHUNT-news/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except Exception as e:
        print(f"WARN fetch failed {url[:60]}: {e}", file=sys.stderr)
        return None


def _load_seen() -> dict:
    if os.path.exists(SEEN_FILE):
        return json.load(open(SEEN_FILE))
    return {"hn": [], "kev": [], "bc": []}


def _save_seen(seen: dict) -> None:
    os.makedirs(NEWS_DIR, exist_ok=True)
    json.dump(seen, open(SEEN_FILE, "w"), indent=1)


def hn_stories(days: int = 1) -> list[dict]:
    """HN stories matching security queries, created in the last `days`."""
    out, seen_ids = [], set()
    since = (datetime.datetime.now(datetime.timezone.utc)
             - datetime.timedelta(days=days)).timestamp()
    for q in HN_QUERIES:
        # NOTE: build the query string with urlencode — the egress proxy
        # drops requests with a raw '>'/'<' in the URL, so numericFilters
        # must go out as created_at_i%3E<ts> (2026-09-29).
        params = urllib.parse.urlencode({
            "query": q,
            "tags": "story",
            "numericFilters": f"created_at_i>{int(since)}",
        })
        url = "https://hn.algolia.com/api/v1/search?" + params
        raw = _get(url)
        if not raw:
            continue
        try:
            for h in json.loads(raw).get("hits", []):
                hid = str(h.get("objectID"))
                if hid in seen_ids or h.get("points", 0) < 5:
                    continue
                seen_ids.add(hid)
                out.append({"id": "hn-" + hid, "source": "hackernews",
                            "title": h.get("title", ""),
                            "url": h.get("url") or
                            f"https://news.ycombinator.com/item?id={hid}",
                            "points": h.get("points", 0)})
        except Exception as e:
            print(f"WARN hn parse: {e}", file=sys.stderr)
    return sorted(out, key=lambda x: -x["points"])


def kev_new(seen: list) -> list[dict]:
    raw = _get(CISA_KEV)
    if not raw:
        return []
    try:
        vulns = json.loads(raw).get("vulnerabilities", [])
    except Exception as e:
        print(f"WARN kev parse: {e}", file=sys.stderr)
        return []
    out = []
    for v in vulns:
        cve = v.get("cveID", "")
        if cve in seen:
            continue
        out.append({"id": "kev-" + cve, "source": "cisa-kev",
                    "title": f"{cve}: {v.get('vulnerabilityName', '')}",
                    "url": v.get("notes", ""),
                    "vendor": v.get("vendorProject", "")})
    return out


def bc_news(seen: list) -> list[dict]:
    raw = _get(BC_RSS)
    if not raw:
        return []
    out = []
    try:
        root = ET.fromstring(raw)
        for item in list(root.iter("item"))[:25]:
            link = item.findtext("link", "")
            if link in seen:
                continue
            out.append({"id": "bc-" + link[-40:], "source": "bleepingcomputer",
                        "title": item.findtext("title", ""),
                        "url": link})
    except Exception as e:
        print(f"WARN bc parse: {e}", file=sys.stderr)
    return out


def main() -> None:
    days = int(sys.argv[sys.argv.index("--days") + 1]) if "--days" in sys.argv else 1
    seen = _load_seen()
    items: list[dict] = []

    for s in hn_stories(days):
        if s["id"] not in seen["hn"]:
            seen["hn"].append(s["id"])
            items.append(s)
    for v in kev_new(seen["kev"]):
        seen["kev"].append(v["id"].replace("kev-", ""))
        items.append(v)
    for b in bc_news(seen["bc"]):
        seen["bc"].append(b["url"])
        items.append(b)

    # keep watermarks bounded (KEV catalog is >1300 entries; cap must exceed it
    # or old CVEs get re-ingested as "new" every run)
    for k in seen:
        seen[k] = seen[k][-5000:]
    _save_seen(seen)

    os.makedirs(NEWS_DIR, exist_ok=True)
    today = datetime.date.today().isoformat()
    digest = os.path.join(NEWS_DIR, f"{today}.md")
    with open(digest, "a") as f:
        f.write(f"\n# News {today} ({datetime.datetime.now().strftime('%H:%M')})\n\n")
        if not items:
            f.write("No new items.\n")
        for it in items:
            f.write(f"- [{it['title']}]({it['url']}) [{it['source']}]\n")
            sig = {"date": today, "source": it["source"], "title": it["title"],
                   "url": it["url"],
                   "why": "security news candidate for technique learning"}
            with open(SIGNALS_FILE, "a") as sf:
                sf.write(json.dumps(sig) + "\n")

    print(f"news_watcher: {len(items)} new items -> {digest}")


if __name__ == "__main__":
    main()
