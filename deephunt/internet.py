"""DEEPHUNT internet — fresh thinking from the outside world. Builds targeted
queries from the target profile, pulls recent writeups/techniques via web fetch,
and converts them into hypothesis seeds. Graceful when offline: queries are
always saved so the agent can enrich them."""
from __future__ import annotations
import json
import os
import re

from tools.base import fetch, now  # noqa: F401  (run from deephunt/ root)


def build_queries(profile):
    target = profile.get("name", "")
    tech = profile.get("tech_terms", [])
    classes = profile.get("vuln_classes", [])
    qs = []
    for c in classes[:6]:
        qs.append(f"{target} {c} bug bounty writeup")
    for t in tech[:4]:
        qs.append(f"{target} {t} security research 2026")
    qs.append(f"{target} bug bounty disclosed reports")
    # dedupe, keep order
    seen, out = set(), []
    for q in qs:
        if q not in seen:
            seen.add(q)
            out.append(q)
    return out


def ddg_lite_search(query, timeout=25):
    """DuckDuckGo lite endpoint — simpler markup, fewer bot blocks."""
    from urllib.parse import quote_plus
    status, body = fetch(
        f"https://lite.duckduckgo.com/lite/?q={quote_plus(query)}",
        timeout=timeout,
        headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"})
    if status != 200 or not body:
        return []
    hits = []
    for m in re.finditer(
            r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', body, re.S):
        url, title = m.group(1), re.sub(r"<[^>]+>", "", m.group(2)).strip()
        if url.startswith("//"):
            url = "https:" + url
        if url.startswith("http") and "duckduckgo.com" not in url and title:
            hits.append((title[:160], url[:300]))
        if len(hits) >= 8:
            break
    return hits


def bing_rss_search(query, timeout=25):
    """Bing RSS endpoint fallback."""
    from urllib.parse import quote_plus
    status, body = fetch(
        f"https://www.bing.com/search?format=rss&q={quote_plus(query)}",
        timeout=timeout,
        headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"})
    if status != 200 or not body:
        return []
    hits = []
    for m in re.finditer(
            r"<item>.*?<title>(.*?)</title>.*?<link>(.*?)</link>",
            body, re.S):
        import html as _h
        title = _h.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip()
        url = _h.unescape(m.group(2)).strip()
        if title and url.startswith("http"):
            hits.append((title[:160], url[:300]))
        if len(hits) >= 8:
            break
    return hits


def web_search(query, timeout=25):
    """Fallback chain: DDG html -> DDG lite -> Bing RSS."""
    for fn in (ddg_search, ddg_lite_search, bing_rss_search):
        try:
            hits = fn(query, timeout=timeout)
        except Exception:  # noqa: BLE001
            hits = []
        if hits:
            return hits
    return []


def ddg_search(query, timeout=25):
    """DuckDuckGo html endpoint via curl. Returns [(title, url)]."""
    from urllib.parse import quote_plus
    status, body = fetch(
        f"https://html.duckduckgo.com/html/?q={quote_plus(query)}",
        timeout=timeout,
        headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"})
    if status != 200 or not body:
        return []
    hits = []
    for m in re.finditer(
            r'<a[^>]+class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            body, re.S):
        url, title = m.group(1), re.sub(r"<[^>]+>", "", m.group(2)).strip()
        if url.startswith("//"):
            url = "https:" + url
        if "duckduckgo.com" not in url:
            hits.append((title[:160], url[:300]))
        if len(hits) >= 8:
            break
    return hits


def collect(profile, state_dir):
    """Run the internet phase. Returns seeds + path of saved intel."""
    queries = build_queries(profile)
    intel = {"ts": now(), "queries": queries, "hits": {}, "seeds": []}
    for q in queries[:8]:
        try:
            hits = web_search(q)
        except Exception:  # noqa: BLE001
            hits = []
        intel["hits"][q] = hits
        for title, url in hits:
            # technique-shaped titles become seeds
            if re.search(r"bypass|inject|idor|ssrf|rce|xss|takeover|leak|"
                         r"race|smuggl|desync|prototype|account", title, re.I):
                intel["seeds"].append({
                    "technique": title,
                    "source": url,
                    "query": q})
    path = os.path.join(state_dir,
                        f"internet_{profile.get('name', 'x')}.json")
    with open(path, "w") as f:
        json.dump(intel, f, indent=1)
    return intel, path
