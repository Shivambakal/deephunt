#!/usr/bin/env python3
"""DEEPHUNT daily build 2026-10-07 — tests for the protocol-recon honesty pass.

Before this build, t100-wafw00f and t100-testssl ran through the generic
factory adapter, which reported "completed (rc=0)" with a raw stdout dump —
a near-fake result: no parsing, no proxy awareness, no honesty when the tool
cannot work. Now:
  * Wafw00fTool: proxy-aware, parses wafw00f JSON into real WAF findings,
    honest error/unparseable findings instead of fake cleans.
  * TestsslTool: refuses to run testssl.sh in the shimmed sandbox (it would
    resolve target+proxy to fake 198.18.x.x and CONNECT-timeout — verified
    live), emits explicit env findings; on real networks runs --fast and
    parses VULNERABLE / weak-protocol / cert findings.
  * TlsInfo: no longer silently returns nothing when direct TLS is
    impossible here (shimmed DNS + blocked egress + MITM proxy).

Safe targets only: example.com family. scanme.nmap.org is proxy-blocked in
this sandbox, which is exactly what exercises the error path live.
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from tools.base import egress_profile, REGISTRY
from tools.passive import Wafw00fTool, TestsslTool, TlsInfo


def make_ctx(hosts):
    return {"target": "__test_protocol__",
            "profile": {"scope_hosts": list(hosts)},
            "state": {"all_subdomains": [], "findings": []}}


def test_shim_still_detected():
    prof = egress_profile(refresh=True)
    assert prof["dns_shimmed"] is True, f"shim not detected: {prof}"
    print(f"  shim={prof['system_answer']} real={prof['doh_answer']}")


def test_handbuilt_wins_registry():
    # Generic factory must have skipped both (covered_by set in tools100.py).
    from tools.t100 import REGISTERED_100
    names = [c.name for c in REGISTERED_100]
    assert "t100-wafw00f" not in names, "generic wafw00f still registered"
    assert "t100-testssl" not in names, "generic testssl still registered"
    assert REGISTRY["t100-wafw00f"] is Wafw00fTool
    assert REGISTRY["t100-testssl"] is TestsslTool
    print("  registry: hand-built adapters win, generic factory skips both")


def test_wafw00f_parse_live_json():
    # Real output captured live from `wafw00f https://example.com -o - -f json`
    # (trigger_url attack payloads stripped here — the parser must not need
    # them, and findings must not persist them).
    live = ('[{"detected": true, "firewall": "Cloudflare", '
            '"manufacturer": "Cloudflare Inc.", '
            '"url": "https://example.com"}]')
    rows = Wafw00fTool.parse_report(live)
    assert len(rows) == 1, rows
    r = rows[0]
    assert r["detected"] and r["firewall"] == "Cloudflare", r
    assert r["manufacturer"] == "Cloudflare Inc.", r
    assert r["url"] == "https://example.com", r
    print(f"  parse live json -> {r['firewall']} ({r['manufacturer']})")


def test_wafw00f_parse_not_detected_and_garbage():
    rows = Wafw00fTool.parse_report(
        '[{"detected": false, "url": "https://plain.example", '
        '"firewall": "", "manufacturer": ""}]')
    assert len(rows) == 1 and rows[0]["detected"] is False, rows
    assert Wafw00fTool.parse_report("total garbage\nno json here") == []
    # ANSI-wrapped text fallback
    rows = Wafw00fTool.parse_report(
        "\x1b[1;94m[+]\x1b[0m The site https://x.example is behind "
        "Cloudflare WAF.\n")
    assert rows and rows[0]["firewall"] == "Cloudflare", rows
    print("  parse: not-detected + garbage + ansi-text fallback OK")


def test_wafw00f_live_run_detects_cloudflare():
    tool = Wafw00fTool()
    assert tool.available(), "wafw00f binary missing"
    findings = tool.run(make_ctx(["example.com"]))
    by_kind = {}
    for f in findings:
        by_kind.setdefault(f["kind"], []).append(f["title"])
    det = [t for t in by_kind.get("fingerprint", []) if "WAF detected" in t]
    assert det, f"no WAF-detected finding: {by_kind}"
    assert any("Cloudflare" in t for t in det), det
    # findings must not leak the trigger payload URLs
    blob = " ".join(f.get("detail", "") + f.get("evidence", "")
                    for f in findings)
    assert "UNION+SELECT" not in blob and "%3Cscript%3E" not in blob, \
        "attack payload leaked into findings"
    assert any(f["kind"] == "env" for f in findings), "env finding missing"
    print(f"  live: {det[0]}")


def test_wafw00f_live_error_path():
    # scanme.nmap.org is blocked by the sandbox egress proxy -> wafw00f
    # cannot reach it; adapter must emit an honest error, not a fake clean.
    tool = Wafw00fTool()
    findings = tool.run(make_ctx(["scanme.nmap.org"]))
    kinds = {f["kind"] for f in findings}
    assert "error" in kinds, f"expected error finding, got {kinds}"
    assert not any(f["kind"] == "clean" for f in findings), \
        "fake clean emitted for unreachable host"
    print(f"  live error path: kinds={sorted(kinds)}")


def test_testssl_live_gate_refuses_in_sandbox():
    tool = TestsslTool()
    assert tool.available(), "testssl.sh binary missing"
    findings = tool.run(make_ctx(["example.com"]))
    kinds = [f["kind"] for f in findings]
    assert kinds and all(k == "env" for k in kinds), kinds
    blob = " ".join(f["title"] + f["detail"] for f in findings)
    assert "NOT evidence" in blob, "honesty disclaimer missing"
    assert "198.18." in blob, "shim evidence missing"
    assert not any("VULNERABLE" in f["title"] for f in findings), \
        "testssl must not manufacture TLS verdicts here"
    print("  live gate: refused with env findings, no fake TLS verdict")


def test_testssl_parser_unit():
    # Synthetic but format-faithful testssl.sh --fast excerpt; exercises the
    # real-network parsing path (unreachable from this sandbox).
    sample = """
 Testing protocols via sockets except NPN+ALPN

 SSLv2      not offered (OK)
 SSLv3      not offered (OK)
 TLS1       offered (deprecated)
 TLS1_1     not offered (OK)
 TLS1_2     offered (OK)

 Testing vulnerabilities

 Heartbleed (CVE-2014-0160)                not vulnerable (OK), no heartbeat extension
 ROBOT                                     VULNERABLE (NOT ok), uses RSA key exchange
"""
    parsed = TestsslTool.parse_findings(sample, "example.com")
    titles = [t for _, t, _, _ in parsed]
    assert any("ROBOT" in t and "VULNERABLE" not in t.split(":")[0]
               or "ROBOT" in t for t in titles), titles
    assert any("weak TLS protocols" in t and "TLS1" in t for t in titles), \
        titles
    assert all(sev in ("high", "medium") for *_, sev in parsed), parsed
    # clean sample -> no findings
    clean = " TLS1_2     offered (OK)\n Heartbleed (CVE-2014-0160)  not vulnerable (OK)\n"
    assert TestsslTool.parse_findings(clean, "example.com") == []
    print(f"  parser: {len(parsed)} findings from synthetic --fast output")


def test_tlsinfo_honest_in_sandbox():
    tool = TlsInfo()
    findings = tool.run(make_ctx(["example.com"]))
    assert findings, "TlsInfo returned nothing at all"
    assert findings[0]["kind"] == "env", findings[0]
    blob = findings[0]["title"] + findings[0]["detail"]
    assert "MITM" in blob and "NOT evidence" in blob, blob
    print("  tls_info: explicit env finding instead of silent nothing")


def main():
    tests = [test_shim_still_detected,
             test_handbuilt_wins_registry,
             test_wafw00f_parse_live_json,
             test_wafw00f_parse_not_detected_and_garbage,
             test_wafw00f_live_run_detects_cloudflare,
             test_wafw00f_live_error_path,
             test_testssl_live_gate_refuses_in_sandbox,
             test_testssl_parser_unit,
             test_tlsinfo_honest_in_sandbox]
    failed = 0
    for t in tests:
        try:
            print(f"[{t.__name__}]")
            t()
        except AssertionError as e:
            failed += 1
            print(f"  FAIL: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  ERROR: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} PASS")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
