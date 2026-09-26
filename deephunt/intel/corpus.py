"""DEEPHUNT vulnerability corpus — learn from 1000s of real-world vulns.

Pulls public CVE records from the NVD API (no auth; polite rate limits),
normalizes them into knowledge/corpus.json, and computes CWE class trends
that feed the oracle's "what pays now" reasoning.

Usage:
    python3 intel/corpus.py --pages 3        # ~6000 records
    python3 intel/corpus.py --pages 1 --per-page 500   # quick sample

Safe: read-only public API, no target contact.
"""
import argparse
import json
import os
import time
import urllib.parse
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "knowledge", "corpus.json")
TS = os.path.join(BASE, "state", "corpus_ts.txt")
API = "https://services.nvd.nist.gov/rest/json/cves/2.0"


def _get(params):
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "DEEPHUNT-research"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001
            print(f"  retry {attempt + 1}: {e}")
            time.sleep(10)
    return None


def normalize(item):
    cve = item.get("cve", {})
    descs = cve.get("descriptions", [])
    desc = next((d["value"] for d in descs if d.get("lang") == "en"), "")[:220]
    cwes = []
    for w in cve.get("weaknesses", []):
        for d in w.get("description", []):
            if d.get("value", "").startswith("CWE"):
                cwes.append(d["value"])
    score, sev = "", ""
    for m in cve.get("metrics", {}).get("cvssMetricV31", [])[:1]:
        score, sev = m["cvssData"].get("baseScore", ""), m["cvssData"].get("baseSeverity", "")
    refs = [r.get("url", "")[:120] for r in cve.get("references", [])[:2]]
    return {"id": cve.get("id"), "summary": desc, "cwe": cwes,
            "score": score, "severity": sev,
            "published": (cve.get("published", "") or "")[:10], "refs": refs}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, default=3)
    ap.add_argument("--per-page", type=int, default=2000)
    ap.add_argument("--since", default="2025-01-01",
                    help="pubStartDate; recent CVEs are analyzed (have CWEs)")
    args = ap.parse_args()

    corpus = []
    for p in range(args.pages):
        print(f"[*] page {p + 1}/{args.pages}...")
        data = _get({"resultsPerPage": args.per_page,
                     "startIndex": p * args.per_page,
                     "pubStartDate": args.since + "T00:00:00.000",
                     "noRejected": ""})
        if not data:
            print("  no data; stopping")
            break
        for v in data.get("vulnerabilities", []):
            corpus.append(normalize(v))
        print(f"    corpus at {len(corpus)}")
        if p < args.pages - 1:
            time.sleep(7)  # NVD unauthenticated: 5 req / 30s

    cwe_freq = {}
    for c in corpus:
        for cwe in c["cwe"] or ["CWE-unknown"]:
            cwe_freq[cwe] = cwe_freq.get(cwe, 0) + 1
    trends = sorted(cwe_freq.items(), key=lambda kv: -kv[1])[:15]

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({"records": corpus, "trends": trends, "count": len(corpus)},
              open(OUT, "w"), indent=1)
    open(TS, "w").write(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    print(f"[+] corpus: {len(corpus)} records -> {OUT}")
    print(f"[+] top CWEs: {trends[:10]}")


if __name__ == "__main__":
    main()
