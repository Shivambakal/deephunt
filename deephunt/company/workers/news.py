"""Worker: recent company news. Passive only.

Source: Google News RSS (public, no key). New surface follows news — funding
rounds, launches, acquisitions, and incidents each reshape the attack surface,
so the planner weights recent items.

Independently runnable: python3 -m company.workers.news "Acme Corp"
"""
from __future__ import annotations

import html
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET

from .base import http_get_text, result

WORKER = "news"

CATEGORY_HINTS = {
    "funding": ["funding", "raises", "series a", "series b", "series c",
                "investment", "valued at"],
    "launch": ["launches", "launch", "announces", "unveils", "introduces",
               "new product", "new feature"],
    "acquisition": ["acquires", "acquisition", "merger", "acquired by", "buys"],
    "incident": ["breach", "hack", "leak", "ransomware", "vulnerability",
                 "cve-", "data exposed", "incident", "outage"],
    "hiring": ["hiring", "appoints", "names", "joins as", "layoffs"],
}


def categorize(title: str) -> str:
    t = title.lower()
    for cat, words in CATEGORY_HINTS.items():
        if any(w in t for w in words):
            return cat
    return "general"


def run(company_name: str, max_items: int = 15) -> dict:
    errors: list[str] = []
    data: dict = {"company": company_name, "items": []}
    q = urllib.parse.quote_plus(company_name)
    body, _, err = http_get_text(
        f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en",
        timeout=25)
    if err:
        errors.append(f"news rss: {err}")
        return result(WORKER, data, errors)
    try:
        root = ET.fromstring(body)
    except Exception as e:  # noqa: BLE001
        errors.append(f"rss parse: {e}"[:200])
        return result(WORKER, data, errors)
    for item in root.iter("item"):
        title = html.unescape((item.findtext("title") or "").strip())
        title = re.sub(r"\s*-\s*[^-]+$", "", title)  # strip outlet suffix
        if not title:
            continue
        data["items"].append({
            "title": title[:220],
            "link": (item.findtext("link") or "")[:300],
            "published": (item.findtext("pubDate") or "")[:40],
            "category": categorize(title),
        })
        if len(data["items"]) >= max_items:
            break
    cats: dict[str, int] = {}
    for it in data["items"]:
        cats[it["category"]] = cats.get(it["category"], 0) + 1
    data["category_counts"] = cats
    data["surface_signals"] = [
        c for c in ("acquisition", "launch", "incident")
        if cats.get(c)]
    return result(WORKER, data, errors)


if __name__ == "__main__":
    import json
    print(json.dumps(run(sys.argv[1] if len(sys.argv) > 1 else "Example"),
                     indent=1)[:5000])
