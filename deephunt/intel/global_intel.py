#!/usr/bin/env python3
"""DEEPHUNT global intelligence store — the GLOBAL INTELLIGENCE stage.

Unifies everything the hunt knows about the world's software into ONE
queryable store so the reasoning layer can ask: "what is known about <tech>?"

Sources (all free, no auth, read-only):
  - CISA KEV catalog ............ exploited-in-the-wild CVEs (high priority)
  - NVD CVE API 2.0 ............. recent CVEs (weekly refresh, bounded)
  - OSV.dev API ................. on-demand per-package vulns (cached)
  - news_watcher signals ........ intel/news/signals.jsonl (existing cron)
  - CWE -> technique-klass map ... curated (full CWE XML is 10MB+; we map the
                                    ~50 CWEs that actually show up in bounties)

Store: intel/global_intel.json
  {"updated": ts,
   "cves": {cve_id: {id, summary, cvss, severity, products[], cwes[], refs[], kev: bool}},
   "by_tech": {product: [cve_id, ...]},
   "signals": [{date, source, title, url, why}]}

The existing news_watcher.py + its 6h cron are UNTOUCHED (contract preserved);
this module only READS its outputs. Refresh this store on its own weekly cron.

Usage:
  python3 global_intel.py --refresh          # NVD + KEV + news signals
  python3 global_intel.py --query wordpress  # what is known about <tech>
  python3 global_intel.py --osv requests pypi
"""
from __future__ import annotations

import datetime
import json
import os
import re
import sys
import time
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HA_ROOT = os.path.dirname(BASE)
INTEL_DIR = os.path.join(BASE, "intel")
STORE = os.path.join(INTEL_DIR, "global_intel.json")
SIGNALS = os.path.join(INTEL_DIR, "news", "signals.jsonl")
KEV_URL = ("https://www.cisa.gov/sites/default/files/feeds/"
           "known_exploited_vulnerabilities.json")
NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
OSV_URL = "https://api.osv.dev/v1/query"

# Curated CWE -> DEEPHUNT technique klass. These ~50 cover the CWEs behind
# the vast majority of bounty findings; the full CWE corpus is noise here.
CWE_KLASS = {
    "CWE-22": "path-traversal", "CWE-23": "path-traversal", "CWE-24": "path-traversal",
    "CWE-36": "path-traversal", "CWE-73": "path-traversal",
    "CWE-78": "rce", "CWE-77": "rce", "CWE-88": "rce", "CWE-94": "rce",
    "CWE-95": "rce", "CWE-96": "rce",
    "CWE-79": "xss", "CWE-80": "xss", "CWE-83": "xss", "CWE-87": "xss",
    "CWE-89": "sqli", "CWE-90": "sqli", "CWE-564": "sqli",
    "CWE-91": "xxe", "CWE-611": "xxe",
    "CWE-918": "ssrf", "CWE-919": "ssrf",
    "CWE-200": "info-disclosure", "CWE-201": "info-disclosure", "CWE-209": "info-disclosure",
    "CWE-215": "info-disclosure", "CWE-532": "info-disclosure", "CWE-538": "info-disclosure",
    "CWE-287": "authentication", "CWE-288": "authentication", "CWE-290": "authentication",
    "CWE-291": "authentication", "CWE-302": "authentication", "CWE-304": "authentication",
    "CWE-306": "authentication", "CWE-307": "authentication", "CWE-308": "authentication",
    "CWE-521": "authentication", "CWE-522": "authentication", "CWE-620": "authentication",
    "CWE-640": "authentication", "CWE-798": "authentication", "CWE-1208": "authentication",
    "CWE-1216": "authentication",
    "CWE-276": "authorization", "CWE-281": "authorization", "CWE-282": "authorization",
    "CWE-283": "authorization", "CWE-285": "authorization", "CWE-286": "authorization",
    "CWE-639": "authorization", "CWE-862": "authorization", "CWE-863": "authorization",
    "CWE-1220": "authorization", "CWE-1297": "authorization",
    "CWE-352": "csrf", "CWE-1275": "csrf",
    "CWE-601": "redirect", "CWE-178": "redirect",
    "CWE-20": "input-validation", "CWE-74": "injection", "CWE-75": "injection",
    "CWE-76": "injection", "CWE-470": "injection",
    "CWE-1321": "prototype-pollution", "CWE-915": "prototype-pollution",
    "CWE-1333": "regex-dos", "CWE-400": "dos", "CWE-401": "dos", "CWE-402": "dos",
    "CWE-404": "dos", "CWE-405": "dos", "CWE-772": "dos",
    "CWE-119": "memory", "CWE-120": "memory", "CWE-121": "memory", "CWE-122": "memory",
    "CWE-125": "memory", "CWE-190": "memory", "CWE-191": "memory",
    "CWE-416": "memory", "CWE-476": "memory", "CWE-787": "memory", "CWE-788": "memory",
    "CWE-1254": "memory",
    "CWE-319": "crypto", "CWE-320": "crypto", "CWE-321": "crypto", "CWE-322": "crypto",
    "CWE-323": "crypto", "CWE-324": "crypto", "CWE-325": "crypto", "CWE-326": "crypto",
    "CWE-327": "crypto", "CWE-328": "crypto", "CWE-329": "crypto", "CWE-330": "crypto",
    "CWE-331": "crypto", "CWE-335": "crypto", "CWE-338": "crypto", "CWE-340": "crypto",
    "CWE-1240": "crypto",
    "CWE-269": "privilege-escalation", "CWE-270": "privilege-escalation",
    "CWE-271": "privilege-escalation", "CWE-272": "privilege-escalation",
    "CWE-250": "privilege-escalation",
    "CWE-502": "deserialization", "CWE-913": "deserialization",
    "CWE-829": "file-inclusion", "CWE-98": "file-inclusion",
    "CWE-434": "file-upload", "CWE-494": "file-upload",
    "CWE-367": "race", "CWE-362": "race",
    "CWE-441": "logic", "CWE-840": "business_logic",
    "CWE-602": "server-side-template", "CWE-1336": "ssti",
    "CWE-918": "ssrf",
    "CWE-1385": "ai-llm", "CWE-1427": "ai-llm", "CWE-1428": "ai-llm",
    "CWE-693": "protection-mechanism", "CWE-696": "protection-mechanism",
    "CWE-703": "exception-handling", "CWE-707": "neutralization",
    "CWE-754": "state-machine", "CWE-841": "workflow",
    "CWE-346": "origin-validation", "CWE-345": "origin-validation",
    "CWE-441": "logic",
}


def _get(url, timeout=30, data=None, headers=None):
    try:
        h = {"User-Agent": "DEEPHUNT-global-intel/1.0"}
        h.update(headers or {})
        req = urllib.request.Request(url, data=data, headers=h)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except Exception as e:
        print(f"WARN fetch failed {url[:70]}: {e}", file=sys.stderr)
        return None


def _load_store():
    if os.path.isfile(STORE):
        try:
            return json.load(open(STORE))
        except (OSError, ValueError):
            pass
    return {"updated": None, "cves": {}, "by_tech": {}, "signals": []}


def _save_store(store):
    os.makedirs(INTEL_DIR, exist_ok=True)
    tmp = STORE + ".tmp"
    json.dump(store, open(tmp, "w"), indent=1)
    os.replace(tmp, STORE)


def _cve_products(cve):
    """Product names from CPE configs + description fallback."""
    prods = set()
    for conf in cve.get("configurations", []) or []:
        for node in conf.get("nodes", []) or []:
            for m in node.get("cpeMatch", []) or []:
                crit = m.get("criteria", "")
                parts = crit.split(":")
                if len(parts) > 4 and parts[2] == "a":
                    prods.add(parts[4].lower().replace("_", " "))
    return sorted(p for p in prods if p and p != "*")


def _cve_record(c):
    descs = c.get("descriptions", []) or []
    summary = next((d.get("value", "") for d in descs
                    if d.get("lang") == "en"), "")
    cvss, severity = None, ""
    for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        m = c.get("metrics", {}).get(key, [])
        if m:
            cvss = m[0].get("cvssData", {}).get("baseScore")
            severity = m[0].get("cvssData", {}).get("baseSeverity", "")
            break
    cwes = set()
    for w in c.get("weaknesses", []) or []:
        for d in w.get("description", []) or []:
            v = d.get("value", "")
            if v.startswith("CWE-"):
                cwes.add(v)
    refs = [r.get("url", "") for r in c.get("references", []) or []][:5]
    return {"id": c.get("id", ""), "summary": summary[:400], "cvss": cvss,
            "severity": severity, "products": _cve_products(c),
            "cwes": sorted(cwes), "refs": refs, "kev": False}


def refresh_nvd(days=7, cap=400):
    """Pull CVEs modified in the last `days` from NVD (bounded, polite)."""
    store = _load_store()
    now = datetime.datetime.now(datetime.timezone.utc)
    start = (now - datetime.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S.000")
    end = now.strftime("%Y-%m-%dT%H:%M:%S.000")
    fetched, idx, total = 0, 0, None
    while fetched < cap:
        url = (f"{NVD_URL}?lastModStartDate={start}&lastModEndDate={end}"
               f"&resultsPerPage=2000&startIndex={idx}")
        raw = _get(url, timeout=60)
        if not raw:
            break
        try:
            data = json.loads(raw)
        except ValueError as e:
            print(f"WARN nvd parse: {e}", file=sys.stderr)
            break
        total = data.get("totalResults", 0)
        vulns = data.get("vulnerabilities", [])
        if not vulns:
            break
        for v in vulns:
            rec = _cve_record(v.get("cve", {}))
            if not rec["id"]:
                continue
            old = store["cves"].get(rec["id"], {})
            rec["kev"] = old.get("kev", False)
            store["cves"][rec["id"]] = rec
            fetched += 1
            if fetched >= cap:
                break
        idx += len(vulns)
        if idx >= (total or 0):
            break
        time.sleep(6)  # NVD politeness without an API key
    _reindex_tech(store)
    _save_store(store)
    print(f"nvd: +{fetched} CVEs (total in store: {len(store['cves'])})")
    return fetched


def refresh_kev():
    """Mark KEV-listed CVEs (and add any missing) — exploited in the wild."""
    store = _load_store()
    raw = _get(KEV_URL)
    if not raw:
        return 0
    try:
        vulns = json.loads(raw).get("vulnerabilities", [])
    except ValueError as e:
        print(f"WARN kev parse: {e}", file=sys.stderr)
        return 0
    n = 0
    for v in vulns:
        cid = v.get("cveID", "")
        if not cid:
            continue
        rec = store["cves"].get(cid, {"id": cid, "summary": "", "cvss": None,
                                      "severity": "", "products": [], "cwes": [],
                                      "refs": []})
        rec["kev"] = True
        if not rec["summary"]:
            rec["summary"] = v.get("vulnerabilityName", "")
        if not rec["products"] and v.get("vendorProject"):
            rec["products"] = [v["vendorProject"].lower()]
        store["cves"][cid] = rec
        n += 1
    _reindex_tech(store)
    _save_store(store)
    print(f"kev: {n} exploited CVEs marked")
    return n


def _reindex_tech(store):
    by_tech = {}
    for cid, rec in store["cves"].items():
        for p in rec.get("products", []):
            by_tech.setdefault(p, [])
            if cid not in by_tech[p]:
                by_tech[p].append(cid)
    store["by_tech"] = by_tech


def ingest_news_signals(limit=300):
    """Fold news_watcher signals into the store (reads, never modifies)."""
    store = _load_store()
    if not os.path.isfile(SIGNALS):
        return 0
    have = {(s.get("title"), s.get("url")) for s in store["signals"]}
    n = 0
    with open(SIGNALS) as f:
        for line in f:
            try:
                s = json.loads(line)
            except ValueError:
                continue
            key = (s.get("title"), s.get("url"))
            if key in have:
                continue
            store["signals"].append({"date": s.get("date"), "source": s.get("source"),
                                    "title": s.get("title"), "url": s.get("url"),
                                    "why": s.get("why", "")})
            have.add(key)
            n += 1
    store["signals"] = store["signals"][-limit:]
    _save_store(store)
    print(f"signals: +{n} news items")
    return n


def osv_query(package, ecosystem="pypi", use_cache=True):
    """On-demand OSV.dev lookup for one package; results cached in the store."""
    store = _load_store()
    cache_key = f"osv:{ecosystem}:{package}".lower()
    if use_cache:
        for c in store["signals"]:
            if c.get("why") == cache_key:
                return c
    payload = json.dumps({"package": {"name": package, "ecosystem": ecosystem}}).encode()
    raw = _get(OSV_URL, data=payload,
               headers={"Content-Type": "application/json"})
    if not raw:
        return {"package": package, "ecosystem": ecosystem, "vulns": []}
    try:
        vulns = json.loads(raw).get("vulns", [])
    except ValueError:
        vulns = []
    out = {"package": package, "ecosystem": ecosystem,
           "vulns": [{"id": v.get("id"), "summary": (v.get("summary") or "")[:300],
                      "severity": [s.get("score") for s in v.get("severity", [])][:2]}
                     for v in vulns[:20]]}
    store["signals"].append({"date": datetime.date.today().isoformat(),
                            "source": "osv.dev", "title": f"{package} ({ecosystem})",
                            "url": f"https://osv.dev/list?ecosystem={ecosystem}&q={package}",
                            "why": cache_key, "cached": out})
    store["signals"] = store["signals"][-500:]
    _save_store(store)
    return out


def what_is_known(tech):
    """The query the reasoning layer uses: everything known about <tech>.

    Returns {tech, cves[], kev[], cwes[], technique_klasses[], news[]}.
    """
    store = _load_store()
    t = tech.lower().strip()
    cve_ids = []
    for prod, ids in store.get("by_tech", {}).items():
        if t in prod or prod in t:
            cve_ids.extend(ids)
    cve_ids = sorted(set(cve_ids))
    cves, kev, cwes = [], [], set()
    for cid in cve_ids:
        rec = store["cves"].get(cid, {})
        cves.append({"id": cid, "summary": rec.get("summary", "")[:160],
                     "cvss": rec.get("cvss"), "severity": rec.get("severity", "")})
        if rec.get("kev"):
            kev.append(cid)
        cwes.update(rec.get("cwes", []))
    klasses = sorted({CWE_KLASS[c] for c in cwes if c in CWE_KLASS})
    news = [s for s in store.get("signals", [])
            if t in (s.get("title", "") + " " + s.get("url", "")).lower()][:10]
    return {"tech": tech, "cves": cves[:25], "kev": kev,
            "cwes": sorted(cwes), "technique_klasses": klasses, "news": news}


def cwe_to_klass(cwe):
    return CWE_KLASS.get(cwe.upper(), "unknown")


def refresh_all(nvd_days=7):
    n1 = refresh_kev()
    n2 = refresh_nvd(nvd_days)
    n3 = ingest_news_signals()
    store = _load_store()
    store["updated"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    _save_store(store)
    return {"kev": n1, "nvd": n2, "signals": n3,
            "cves_total": len(store["cves"]),
            "techs_total": len(store["by_tech"])}


def main():
    if "--query" in sys.argv:
        q = sys.argv[sys.argv.index("--query") + 1]
        print(json.dumps(what_is_known(q), indent=1)[:4000])
    elif "--osv" in sys.argv:
        i = sys.argv.index("--osv")
        pkg = sys.argv[i + 1]
        eco = sys.argv[i + 2] if len(sys.argv) > i + 2 else "pypi"
        print(json.dumps(osv_query(pkg, eco), indent=1)[:3000])
    else:  # --refresh (default)
        days = 7
        if "--days" in sys.argv:
            days = int(sys.argv[sys.argv.index("--days") + 1])
        print(json.dumps(refresh_all(days), indent=1))


if __name__ == "__main__":
    main()
