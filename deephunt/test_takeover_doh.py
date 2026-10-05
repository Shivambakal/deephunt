#!/usr/bin/env python3
"""DEEPHUNT daily build 2026-10-05 — tests for the proxy-aware takeover adapter.

The old TakeoverCheck resolved CNAMEs with `dig` (direct system DNS). In the
sandbox that returns SHIMMED answers (example.com -> 198.18.15.159), so every
fingerprint check ran against fake DNS. The new adapter resolves via DoH
(deephunt/doh_dns.py, through the egress proxy) and detects the shim.
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from tools.base import egress_profile
from tools.passive import TakeoverCheck


def make_ctx(subs):
    return {"target": "__test_takeover__", "profile": {"scope_hosts": []},
            "state": {"all_subdomains": list(subs), "findings": []}}


def test_egress_profile_detects_shim():
    prof = egress_profile(refresh=True)
    assert prof["dns_shimmed"] is True, f"shim not detected: {prof}"
    assert prof["system_answer"].startswith("198.18."), prof
    assert prof["doh_answer"] and prof["doh_answer"] != prof["system_answer"]
    assert prof["doh_provider"] in ("google", "cloudflare")
    print(f"  shim={prof['system_answer']} real={prof['doh_answer']} "
          f"via={prof['doh_provider']}")


def test_fingerprint_hit_positive():
    hit = TakeoverCheck.fingerprint_hit(
        "<Error><Code>NoSuchBucket</Code></Error>", "x.s3.amazonaws.com")
    assert hit == ("s3.amazonaws.com", "NoSuchBucket"), hit
    hit = TakeoverCheck.fingerprint_hit(
        "There isn't a GitHub Pages site here.", "x.github.io")
    assert hit is not None and hit[0] == "github.io"
    print("  fingerprint positives OK")


def test_fingerprint_hit_negative():
    assert TakeoverCheck.fingerprint_hit(
        "<html>hello world</html>", "x.s3.amazonaws.com") is None
    assert TakeoverCheck.fingerprint_hit("", "x.github.io") is None
    # wrong service in cname -> no hit even with matching body text
    assert TakeoverCheck.fingerprint_hit(
        "NoSuchBucket", "x.azureedge.net") is None
    print("  fingerprint negatives OK")


def test_adapter_empty_subs():
    findings = TakeoverCheck().run(make_ctx([]))
    kinds = {f["kind"] for f in findings}
    assert "inventory" in kinds, findings
    print(f"  empty-subs findings: {[f['title'] for f in findings]}")


def test_adapter_live_safe_hosts():
    # Safe targets only. DoH queries are passive (public resolvers, never the
    # targets). cdn.jsdelivr.net exercises the multi-hop CNAME-chain path.
    hosts = ["example.com", "www.example.com", "scanme.nmap.org",
             "testphp.vulnweb.com", "cdn.jsdelivr.net"]
    findings = TakeoverCheck().run(make_ctx(hosts))
    assert findings, "adapter returned nothing"
    for f in findings:
        for k in ("tool", "phase", "kind", "title", "ts"):
            assert k in f, f"missing key {k} in {f}"
    assert all(f["tool"] == "takeover" for f in findings)
    kinds = {f["kind"] for f in findings}
    assert "env" in kinds, f"no shim-env finding in {kinds}"
    assert "broken" not in kinds, f"adapter broken: {findings}"
    print("  live findings:")
    for f in findings:
        print(f"   [{f['kind']}] {f['title']}")
        if f.get("detail"):
            print("    " + f["detail"][:160].replace("\n", " | "))
    return findings


def test_chain_follows_multihop():
    import doh_dns
    r = doh_dns.resolve_cname_chain("cdn.jsdelivr.net")
    assert r["error"] is None, r
    assert len(r["chain"]) >= 2, r["chain"]
    assert r["A"], r
    print(f"  chain: {' -> '.join(r['chain'])} A={r['A'][:2]}")


if __name__ == "__main__":
    tests = [test_egress_profile_detects_shim, test_fingerprint_hit_positive,
             test_fingerprint_hit_negative, test_adapter_empty_subs,
             test_adapter_live_safe_hosts, test_chain_follows_multihop]
    for t in tests:
        print(f"RUN {t.__name__}")
        t()
    print("ALL TAKEOVER-DOH TESTS PASSED")
