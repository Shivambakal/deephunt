#!/usr/bin/env python3
"""DEEPHUNT daily build 2026-10-06 — tests for the proxy-aware httpx adapter.

The old HttpxTool shelled out to the httpx binary with no proxy awareness:
in this sandbox direct egress is blocked and system DNS is shimmed
(example.com -> 198.18.x.x), so the binary dialed fake IPs and silently
produced nothing. The new adapter detects the shim via egress_profile(),
routes httpx through the egress proxy (env vars — never on a command line),
drops -cname (httpx's own DNS is shim garbage), and emits an 'env' finding
so the daemon never silently produces nothing. If no proxy env exists in a
shimmed sandbox it emits 'broken' and refuses to run.
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from tools.base import egress_profile
from tools.passive import HttpxTool

# Safe targets only. NOTE: the sandbox egress proxy allowlists; as of this
# run scanme.nmap.org and testphp.vulnweb.com are blocked (curl -> 000),
# so tests use the example.com family + cdn.jsdelivr.net.
SAFE = ["example.com", "www.example.com", "cdn.jsdelivr.net"]


def make_ctx(hosts):
    return {"target": "__test_httpx__",
            "profile": {"scope_hosts": list(hosts)},
            "state": {"all_subdomains": [], "findings": []}}


def test_egress_profile_detects_shim():
    prof = egress_profile(refresh=True)
    assert prof["dns_shimmed"] is True, f"shim not detected: {prof}"
    assert prof["system_answer"].startswith("198.18."), prof
    print(f"  shim={prof['system_answer']} real={prof['doh_answer']}")


def test_proxy_env_mirror():
    tool = HttpxTool()
    saved = {k: os.environ.get(k) for k in
             ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
              "http_proxy", "https_proxy", "all_proxy")}
    try:
        for k in saved:
            os.environ.pop(k, None)
        os.environ["https_proxy"] = "http://proxy.internal:3128"
        assert tool._proxy_env_ready() is True
        assert os.environ.get("HTTPS_PROXY") == "http://proxy.internal:3128"
        for k in ("http_proxy", "https_proxy", "all_proxy",
                  "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
            os.environ.pop(k, None)
        assert tool._proxy_env_ready() is False
        print("  proxy env mirror OK (lowercase->uppercase, absent->False)")
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def test_run_no_targets():
    findings = HttpxTool().run(make_ctx([]))
    kinds = {f["kind"] for f in findings}
    assert "env" in kinds, findings  # shim always detected in this sandbox
    assert any("no targets yet" in f["title"] for f in findings), findings
    print(f"  no-targets findings: {[f['title'] for f in findings]}")


def test_run_live_safe_hosts():
    findings = HttpxTool().run(make_ctx(SAFE))
    kinds = {f["kind"] for f in findings}
    assert "env" in kinds, findings
    inv = next(f for f in findings if f["kind"] == "inventory")
    # example.com + www.example.com are 200 via proxy (verified); jsdelivr 301
    assert "3 live of 3 probed" in inv["title"], inv
    assert "Cloudflare" in inv["detail"], inv
    print(f"  live run: {inv['title']} :: {inv['detail'].replace(chr(10), ' | ')}")


def test_run_no_proxy_env_is_broken_not_silent():
    tool = HttpxTool()
    saved = {k: os.environ.get(k) for k in
             ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
              "http_proxy", "https_proxy", "all_proxy")}
    try:
        for k in saved:
            os.environ.pop(k, None)
        findings = tool.run(make_ctx(SAFE))
        kinds = {f["kind"] for f in findings}
        assert "broken" in kinds, findings
        assert not any(f["kind"] == "inventory" and "live of" in f["title"]
                       for f in findings), findings
        print("  no-proxy-env -> explicit 'broken' finding, no silent run")
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


TESTS = [test_egress_profile_detects_shim,
         test_proxy_env_mirror,
         test_run_no_targets,
         test_run_live_safe_hosts,
         test_run_no_proxy_env_is_broken_not_silent]


if __name__ == "__main__":
    failed = 0
    for t in TESTS:
        try:
            print(f"RUN {t.__name__}")
            t()
            print("  PASS")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  FAIL: {type(e).__name__}: {e}")
    print(f"\n{len(TESTS) - failed}/{len(TESTS)} passed")
    sys.exit(1 if failed else 0)
