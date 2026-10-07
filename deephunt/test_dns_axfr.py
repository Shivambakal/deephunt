#!/usr/bin/env python3
"""DEEPHUNT daily build 2026-10-07 — tests for the DoH-aware dns_axfr adapter.

The old DnsAxfr resolved NS records with `dig` (system DNS). In the sandbox
that returns SHIMMED answers (198.18.x.x), so every zone-transfer attempt
would either hit a fake nameserver or silently report "refused everywhere" —
a false negative. The new adapter:

  1. resolves authoritative NS -> IP via DoH (deephunt/doh_dns.py, through
     the egress proxy — passive, never touches the target),
  2. probes once whether raw UDP/TCP DNS can leave this network; if not,
     emits explicit 'env' findings instead of a bogus "refused everywhere",
  3. factors the allowed/refused decision into a unit-testable staticmethod.
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from tools.base import egress_profile
from tools.active import DnsAxfr


def test_egress_profile_detects_shim():
    prof = egress_profile(refresh=True)
    assert prof["dns_shimmed"] is True, f"shim not detected: {prof}"
    assert prof["system_answer"].startswith("198.18."), prof
    assert prof["doh_answer"] and prof["doh_answer"] != prof["system_answer"]
    print(f"  shim={prof['system_answer']} real={prof['doh_answer']} "
          f"via={prof['doh_provider']}")


def test_parse_axfr_allowed():
    out = ("example.com. 3600 IN SOA a.iana-servers.net. "
           "hostmaster.example.com. 2026100701 7200 3600 1209600 3600\n"
           "example.com. 3600 IN NS a.iana-servers.net.\n"
           "example.com. 3600 IN NS b.iana-servers.net.\n"
           "www.example.com. 3600 IN A 93.184.216.34\n")
    verdict, why = DnsAxfr.parse_axfr(out)
    assert verdict == "allowed", (verdict, why)
    print(f"  allowed -> {why}")


def test_parse_axfr_refused():
    verdict, _ = DnsAxfr.parse_axfr(";; Transfer failed.\n")
    assert verdict == "refused", verdict
    verdict, _ = DnsAxfr.parse_axfr(";; connection timed out; no servers "
                                    "could be reached\n")
    assert verdict == "refused", verdict
    verdict, _ = DnsAxfr.parse_axfr("")
    assert verdict == "refused", verdict
    print("  refused cases OK")


def test_parse_axfr_inconclusive():
    # non-empty junk without an SOA block must NOT be a false positive
    verdict, _ = DnsAxfr.parse_axfr("some weird banner text\n")
    assert verdict == "inconclusive", verdict
    print("  inconclusive case OK")


def test_ns_ips_live():
    import doh_dns
    pairs, err = DnsAxfr._ns_ips("example.com", doh_dns)
    assert pairs, f"no NS pairs: {err}"
    for ns, ip in pairs:
        assert ip and not ip.startswith("198.18."), (ns, ip)
    print(f"  example.com NS via DoH: {pairs}")


def test_gated_block():
    ctx = {"profile": {}, "authorization": None, "state": {}}
    f = DnsAxfr().run(ctx)
    assert f[0]["kind"] == "gated", f
    print(f"  gated -> {f[0]['title']}")


def test_full_adapter_live():
    # gate passes; this sandbox blocks raw DNS egress, so the adapter must
    # report 'env' (unreachable) rather than a false "refused everywhere".
    ctx = {"profile": {"active_allowed": True, "ct_zones": ["example.com"]},
           "authorization": {"scope_hosts": ["example.com"]}, "state": {}}
    findings = DnsAxfr().run(ctx)
    kinds = {f["kind"] for f in findings}
    titles = [f["title"] for f in findings]
    print(f"  findings: {titles}")
    assert "env" in kinds, findings
    assert any("unreachable" in t for t in titles), titles
    assert not any(t == "dns_axfr: refused everywhere" for t in titles), \
        "false 'refused everywhere' emitted in a blocked-egress env"


if __name__ == "__main__":
    test_egress_profile_detects_shim()
    test_parse_axfr_allowed()
    test_parse_axfr_refused()
    test_parse_axfr_inconclusive()
    test_ns_ips_live()
    test_gated_block()
    test_full_adapter_live()
    print("ALL PASS")
