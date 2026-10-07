"""Tests for error_intel + advanced adapters. Hermetic: no network, no targets."""
import base64
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import error_intel as ei


def _b64(d):
    return base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=").decode()


def _jwt(header, payload):
    return f"{_b64(header)}.{_b64(payload)}.fakesig"


# ---------- classification: benign (4+) ----------
def test_benign_rate_limit():
    assert ei.classify("HTTP 429 Too Many Requests") == "benign"
    assert ei.classify("ERROR: rate limit exceeded, slow down") == "benign"


def test_benign_timeout():
    assert ei.classify("curl: (28) Connection timed out after 10001 ms") == "benign"
    assert ei.classify("deadline exceeded while dialing") == "benign"


def test_benign_dns():
    assert ei.classify("curl: (6) Could not resolve host: xyz.example.com") == "benign"
    assert ei.classify("DNS problem: NXDOMAIN looking up A") == "benign"


def test_benign_conn():
    assert ei.classify("Connection refused on port 443") == "benign"
    assert ei.classify("Connection reset by peer") == "benign"
    assert ei.classify("no subdomains found") == "benign"


# ---------- classification: informative (4+) ----------
def test_informative_sqli():
    assert ei.classify("You have an error in your SQL syntax near ''1'''") == "informative"
    assert ei.classify("ERROR: ORA-01756: quoted string not properly terminated") == "informative"
    assert ei.classify("Unclosed quotation mark after the character string 'abc'") == "informative"
    assert ei.classify('Warning: pg_query(): Query failed: ERROR: unterminated quoted string') == "informative"


def test_informative_waf():
    assert ei.classify("<title>Attention Required! | Cloudflare</title> cf-ray: abc") == "informative"
    assert ei.classify("Request blocked by AWS WAF, request id 123") == "informative"
    assert ei.classify("Incapsula incident ID 12345") == "informative"
    assert ei.classify("ModSecurity: Access denied with code 403 (CRS/932100)") == "informative"


def test_informative_traces():
    assert ei.classify("Traceback (most recent call last):\n  File \"/app/views.py\"") == "informative"
    assert ei.classify("java.lang.NullPointerException at com.shop.CartServlet(doGet:42)") == "informative"
    assert ei.classify("Server Error in '/' Application. System.Data.SqlClient") == "informative"
    assert ei.classify("Fatal error: Uncaught Error in /var/www/html/index.php on line 12") == "informative"


def test_informative_versions_cloud():
    assert ei.classify("Server: nginx/1.18.0 (Ubuntu)") == "informative"
    assert ei.classify("X-Powered-By: PHP/7.4.3") == "informative"
    assert ei.classify("169.254.169.254/latest/meta-data/iam") == "informative"
    assert ei.classify('{"errors":[{"message":"Cannot query field \\"admin\\" on type \\"Query\\""}]}') == "informative"


# ---------- classification: unknown ----------
def test_unknown():
    assert ei.classify("Frobnicator failed with code ZX-9912: quantum flux unstable in the hyperdrive manifold") == "unknown"
    assert ei.classify("") == "unknown"


# ---------- extraction ----------
def test_extract_intel():
    blob = ("Server: nginx/1.18.0\r\nX-Powered-By: Express\r\n"
            "Traceback (most recent call last):\n  File \"/var/www/app.py\", line 3\n"
            "You have an error in your SQL syntax")
    intel = ei.extract_intel(blob)
    assert intel.get("server_header") == "nginx/1.18.0 (Ubuntu)".replace(" (Ubuntu)", "") or "nginx" in intel.get("server_header", "")
    assert intel.get("x_powered_by") == "Express"
    assert intel.get("sql_dialect") == "MySQL"
    assert any("/var/www" in p for p in intel.get("internal_paths", []))


def test_extract_waf():
    intel = ei.extract_intel("Attention Required! Cloudflare Ray ID: abc")
    assert intel.get("waf") == "Cloudflare"


# ---------- study records + card search ----------
def test_study_record_and_cards(tmp_path=None):
    import tempfile
    orig = ei.STUDY_PATH
    ei.STUDY_PATH = os.path.join(tempfile.mkdtemp(), "studies.jsonl")
    try:
        rec = ei.record_study("fuzzx", "weird quantum flux error ZX-9912 in hyperdrive")
        assert rec["status"] == "open"
        assert os.path.isfile(ei.STUDY_PATH)
        # card search returns list (may be empty for nonsense, must not crash)
        sug = ei.search_cards("You have an error in your SQL syntax near 1")
        assert isinstance(sug, list)
        assert any(s["card"] == "SQLI-01" for s in sug)
    finally:
        ei.STUDY_PATH = orig


# ---------- process_tool_result hook ----------
def test_process_tool_result():
    findings = [
        {"tool": "t100-wapiti", "phase": "active", "kind": "probe",
         "title": "wapiti done", "detail": "You have an error in your SQL syntax", "evidence": ""},
        {"tool": "t100-dnsx", "phase": "passive", "kind": "error",
         "title": "dnsx failed", "detail": "Could not resolve host", "evidence": ""},
        {"tool": "t100-xyz", "phase": "active", "kind": "error",
         "title": "xyz crashed", "detail": "Frobnicator ZX-9912 quantum flux unstable hyperdrive manifold failure",
         "evidence": ""},
    ]
    import tempfile
    orig = ei.STUDY_PATH
    ei.STUDY_PATH = os.path.join(tempfile.mkdtemp(), "s.jsonl")
    try:
        extra = ei.process_tool_result("testtool", findings)
    finally:
        ei.STUDY_PATH = orig
    kinds = {f["kind"] for f in extra}
    assert "error-intel" in kinds          # sqli -> informative
    assert "error-study" in kinds          # unknown substantial error -> study
    assert not any("resolve" in f.get("evidence", "") for f in extra)  # benign silenced


# ---------- jwt_probe (static, no network) ----------
def test_jwt_probe_none():
    from tools.advanced import JwtProbe
    t = JwtProbe()
    token = _jwt({"alg": "none", "typ": "JWT"}, {"sub": "1"})
    fs = t.run({"jwt": token})
    assert any(f["kind"] == "vuln-candidate" and "alg=none" in f["title"] for f in fs)


def test_jwt_probe_kid_jku():
    from tools.advanced import JwtProbe
    t = JwtProbe()
    token = _jwt({"alg": "HS256", "kid": "../../dev/null",
                  "jku": "http://evil.test/keys.json"}, {"sub": "1"})
    fs = t.run({"jwt": token})
    titles = " ".join(f["title"] for f in fs)
    assert "symmetric HMAC" in titles
    assert "kid path traversal" in titles
    assert "jku external URL" in titles


def test_jwt_probe_no_token():
    from tools.advanced import JwtProbe
    fs = JwtProbe().run({})
    assert fs[0]["kind"] == "gated"


# ---------- bypass403 battery parsing (no network) ----------
def test_bypass403_battery_parses():
    from tools.advanced import _parse_battery
    ops = _parse_battery()
    types = {o[0] for o in ops}
    assert {"path", "header", "method", "query"} <= types
    assert len(ops) >= 20


def test_bypass403_gated_without_auth():
    from tools.advanced import Bypass403
    fs = Bypass403().run({"profile": {"active_allowed": True},
                          "bypass403": ["https://example.com/admin"]})
    assert fs[0]["kind"] == "gated"  # no TestAuthorization in ctx


# ---------- wordlists ----------
def test_wordlists_resolve():
    from wordlists import resolve, available_names
    p = resolve("web-common")
    assert os.path.isfile(p)
    assert "web-common" in available_names() or os.path.basename(p) == "common.txt"


# ---------- intruder render/positions (no network) ----------
def test_intruder_positions_render():
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", "proxy"))
    import intruder
    base = {"method": "GET", "url": "https://example.com/§p§?x=§1§",
            "headers": {"X-T": "a§b§"}, "body": ""}
    pos = intruder.find_positions(base)
    assert len(pos) == 3
    pmap = {(loc, name): "PAY" for loc, name in pos}
    m, u, h, b = intruder.render(base, pos, pmap)
    assert "PAY" in u and "§" not in u


if __name__ == "__main__":
    import traceback
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except Exception:  # noqa: BLE001
            failed += 1
            print(f"FAIL {fn.__name__}")
            traceback.print_exc()
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
