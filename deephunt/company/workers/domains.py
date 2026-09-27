"""Worker: total domain footprint. Passive only.

Sources (all public, no auth):
- crt.sh certificate transparency (subdomains + cert history)
- DNS-over-HTTPS: A/AAAA/MX/TXT/NS/SOA for the root domain
- ipinfo.io for ASN/org of resolved IPs (public endpoint, no token)
- Locally generated typo/fuzzy candidates (reported as candidates, resolved
  passively via DoH — resolution of a public DNS name is not active probing)

Independently runnable: python3 -m company.workers.domains example.com
"""
from __future__ import annotations

import re
import sys

from .base import dns_doh, http_get_json, http_get_text, resolve_a, result

WORKER = "domains"


def crtsh_subdomains(domain: str) -> tuple[set[str], list[dict], str]:
    data, err = http_get_json(
        f"https://crt.sh/?q=%25.{domain}&output=json", timeout=30)
    if err:
        return set(), [], err
    subs, certs = set(), []
    if isinstance(data, list):
        for row in data:
            name = (row.get("name_value") or "")
            for part in name.split("\n"):
                part = part.strip().lower().lstrip("*.")
                if part and (part == domain or part.endswith("." + domain)):
                    subs.add(part)
            certs.append({
                "issuer": (row.get("issuer_name") or "")[:120],
                "not_before": row.get("not_before"),
                "not_after": row.get("not_after"),
            })
    return subs, certs, ""


def ip_asn_org(ip: str) -> dict:
    data, err = http_get_json(f"https://ipinfo.io/{ip}/json", timeout=15)
    if err or not isinstance(data, dict):
        return {"ip": ip, "error": err or "bad response"}
    return {"ip": ip, "asn": data.get("org", ""),
            "city": data.get("city", ""), "country": data.get("country", "")}


def typo_candidates(domain: str) -> list[str]:
    """Common typo/lookalike permutations. Candidates only — passive DoH check."""
    if "." not in domain:
        return []
    label, _, tld = domain.partition(".")
    cands = set()
    # omission / duplication / transposition / substitution neighbours
    for i in range(len(label)):
        cands.add(label[:i] + label[i + 1:])                      # omission
        cands.add(label[:i] + label[i] * 2 + label[i + 1:])       # duplication
        if i < len(label) - 1:
            cands.add(label[:i] + label[i + 1] + label[i] + label[i + 2:])
    for ch in "aioe":
        cands.add(label.replace("o", ch) if "o" in label else label + ch)
    for suffix in ("-app", "-api", "app", "api", "-hq", "hq"):
        cands.add(label + suffix)
    cands.discard(label)
    out = []
    for c in sorted(cands):
        if re.fullmatch(r"[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?", c):
            out.append(f"{c}.{tld}")
    return out[:40]


def run(domain: str) -> dict:
    domain = domain.strip().lower().rstrip(".")
    errors: list[str] = []
    data: dict = {"domain": domain}

    subs, certs, err = crtsh_subdomains(domain)
    if err:
        errors.append(f"crt.sh: {err}")
    data["subdomains"] = sorted(subs)
    data["subdomain_count"] = len(subs)
    data["certificates_observed"] = len(certs)
    # newest certs first — recent issuance can flag new surface
    certs.sort(key=lambda c: c.get("not_before") or "", reverse=True)
    data["recent_certificates"] = certs[:10]

    dns: dict = {}
    for rtype in ("A", "AAAA", "MX", "TXT", "NS", "SOA"):
        vals, err = dns_doh(domain, rtype)
        if err:
            errors.append(f"DoH {rtype}: {err}")
        dns[rtype] = vals
    data["dns"] = dns

    ips = sorted(set(dns.get("A", []) + dns.get("AAAA", []))) or resolve_a(domain)
    data["resolved_ips"] = ips
    data["ip_intel"] = [ip_asn_org(ip) for ip in ips[:10]]

    # passive resolution of typo candidates
    live_typos = []
    for cand in typo_candidates(domain):
        vals, _ = dns_doh(cand, "A")
        if vals:
            live_typos.append({"domain": cand, "a_records": vals})
    data["live_typo_candidates"] = live_typos

    # SPF/DMARC posture from TXT
    txt = " ".join(dns.get("TXT", []))
    data["email_posture"] = {
        "spf": "v=spf1" in txt,
        "dmarc_hint": any("dmarc" in t for t in dns.get("TXT", [])),
    }
    return result(WORKER, data, errors)


if __name__ == "__main__":
    import json
    print(json.dumps(run(sys.argv[1] if len(sys.argv) > 1 else "example.com"),
                     indent=1)[:6000])
