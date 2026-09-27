"""Tests for company hunter: workers (mocked network), planner, snapshots, dossier."""
import json
import os
import sys
from unittest import mock

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from company import attack_planner, dossier as dossier_mod, snapshot  # noqa: E402
from company.workers import breach_history, domains, employees, news, techstack  # noqa: E402

PASS = []
FAIL = []


def check(name, fn):
    try:
        fn()
        PASS.append(name)
    except Exception as e:  # noqa: BLE001
        FAIL.append((name, f"{type(e).__name__}: {e}"))


# ---------- workers with mocked network ----------

def test_domains_worker():
    crt = [{"name_value": "a.example.com\nb.example.com",
            "issuer_name": "Test CA", "not_before": "2026-01-01",
            "not_after": "2027-01-01"}]
    with mock.patch("company.workers.domains.http_get_json",
                    return_value=(crt, "")), \
         mock.patch("company.workers.domains.dns_doh",
                    return_value=(["1.2.3.4"], "")), \
         mock.patch("company.workers.domains.ip_asn_org",
                    return_value={"ip": "1.2.3.4", "asn": "AS1"}), \
         mock.patch("company.workers.domains.resolve_a", return_value=[]):
        r = domains.run("example.com")
    assert r["worker"] == "domains"
    assert "a.example.com" in r["data"]["subdomains"]
    assert r["data"]["subdomain_count"] == 2


def test_techstack_worker():
    html = ('<html><head><meta name="generator" content="WordPress 6.1">'
            '<script src="https://cdn.example.com/jquery-3.6.0.min.js"></script>'
            '</head><body data-next></body></html>')
    hdrs = {"Server": "nginx", "X-Powered-By": "PHP/8.1"}
    with mock.patch("company.workers.techstack.http_get_text") as m:
        # order: homepage, security.txt, robots.txt, sitemap.xml
        m.side_effect = [(html, hdrs, ""),
                         ("", {}, ""),
                         ("User-agent: *\nDisallow: /admin", {}, ""),
                         ("", {}, "")]
        r = techstack.run("example.com")
    det = r["data"]["detected"]
    assert any("WordPress" in d for d in det), det
    assert "nginx" in det
    assert r["data"]["versions"].get("jQuery") == "3.6.0"
    assert "/.well-known/security.txt" not in r["data"]["public_files"]


def test_employees_boundary():
    # boundary string must exist; worker must not attempt contact
    repos = {"items": [{"full_name": "acme/web", "description": "d",
                        "stargazers_count": 1, "language": "Go",
                        "html_url": "https://github.com/acme/web"}]}
    contribs = [{"login": "alice"}, {"login": "ci-bot[bot]"}]
    prof = {"login": "alice", "name": "Alice", "bio": "dev", "company": "Acme",
            "location": "X", "blog": "", "twitter_username": None,
            "public_repos": 3, "html_url": "https://github.com/alice"}
    with mock.patch("company.workers.employees._gh") as m:
        m.side_effect = [(repos, ""), (contribs, ""), (prof, "")]
        r = employees.run("Acme Corp", "acme.com")
    assert "no contact" in r["data"]["boundary"].lower() or \
           "NO CONTACT" in r["data"]["boundary"]
    assert r["data"]["person_count"] == 1
    assert r["data"]["people"][0]["github"] == "alice"
    # no private fields collected
    assert "email" not in r["data"]["people"][0]


def test_news_worker():
    rss = ('<rss><channel><item><title>Acme raises funding - TechCrunch</title>'
           '<link>http://x</link><pubDate>Mon, 01 Jan 2026</pubDate></item>'
           '<item><title>Acme launches new API - Blog</title><link>http://y</link>'
           '<pubDate>Tue, 02 Jan 2026</pubDate></item></channel></rss>')
    with mock.patch("company.workers.news.http_get_text",
                    return_value=(rss, {}, "")):
        r = news.run("Acme")
    assert len(r["data"]["items"]) == 2
    assert r["data"]["category_counts"]["funding"] == 1
    assert "launch" in r["data"]["surface_signals"]


def test_breach_worker():
    bl = [{"Name": "AcmeBreach", "Title": "Acme", "Domain": "acme.com",
           "BreachDate": "2024-01-01", "PwnCount": 100,
           "DataClasses": ["Emails"], "IsVerified": True}]
    with mock.patch("company.workers.breach_history.http_get_json",
                    return_value=(bl, "")), \
         mock.patch("company.workers.breach_history.http_get_text",
                    return_value=(None, {}, "404")):
        r = breach_history.run("Acme", "acme.com")
    assert r["data"]["breach_count"] == 1
    assert "never store" in r["data"]["leak_hunting_note"].lower() or \
           "Never store" in r["data"]["leak_hunting_note"]


# ---------- planner ----------

def _dossier():
    return {
        "company": "Acme", "domain": "acme.com",
        "workers": {
            "techstack": {"data": {"detected": ["WordPress", "GraphQL"],
                                   "third_party_hosts": ["cdn.acme.com"],
                                   "versions": {}, "headers_of_note": {},
                                   "public_files": {}}},
            "domains": {"data": {"subdomains": ["api.acme.com"] * 60,
                                 "subdomain_count": 60,
                                 "resolved_ips": [], "dns": {},
                                 "live_typo_candidates": []}},
            "news": {"data": {"items": [], "category_counts":
                              {"acquisition": 1}, "surface_signals": []}},
            "breach_history": {"data": {"breach_count": 1, "breaches": []}},
            "employees": {"data": {"people": []}},
        },
    }


def test_planner_ranks_and_reasons():
    plan = attack_planner.build_plan(_dossier(), top_n=10)
    assert len(plan) == 10
    assert plan[0]["score"] >= plan[-1]["score"]
    for p in plan:
        assert p["card_id"] and p["hypothesis"] and p["test_sketch"]
        assert p["reasons"]


def test_planner_signal_matching():
    toks = attack_planner.dossier_tokens(_dossier())
    assert "wordpress" in toks and "graphql" in toks and "api" in toks


def test_rerank_boosts_changed_surface():
    plan = attack_planner.build_plan(_dossier(), top_n=10)
    changes = {"items": ["NEW subdomain: graphql.acme.com",
                         "NEW detected technology: GraphQL"]}
    r = attack_planner.rerank(plan, changes)
    assert r[0]["score"] >= plan[0]["score"] or \
        any(x.get("rerank_boost", 0) > 0 for x in r)


# ---------- snapshots ----------

def test_snapshot_diff():
    import tempfile
    slug = "testco-diff"
    tmpd = tempfile.mkdtemp()
    os.makedirs(os.path.join(tmpd, "snapshots"), exist_ok=True)

    def fake_state_dir(s):
        return tmpd
    d = {"workers": {
        "domains": {"data": {"subdomains": ["a.testco.com"],
                             "resolved_ips": ["1.1.1.1"],
                             "dns": {"MX": []},
                             "certificates_observed": 1,
                             "live_typo_candidates": []}},
        "techstack": {"data": {"detected": ["nginx"], "versions": {},
                                "third_party_hosts": []}}}}
    with mock.patch("company.snapshot.state_dir",
                    side_effect=fake_state_dir):
        s1 = snapshot.extract_snapshot(d)
        snapshot.save_snapshot(slug, d)
        d["workers"]["domains"]["data"]["subdomains"] = ["a.testco.com",
                                                        "b.testco.com"]
        s2 = snapshot.extract_snapshot(d)
        snapshot.save_snapshot(slug, d)
        ch = snapshot.diff_snapshots(slug, s2)
    assert ch["suspicious"] is True
    assert any("b.testco.com" in i for i in ch["items"])
    fups = snapshot.followups_for_changes(ch)
    assert any("b.testco.com" in f for f in fups)


# ---------- dossier ----------

def test_dossier_renders():
    dsr = _dossier()
    plan = attack_planner.build_plan(dsr, top_n=3)
    full = dossier_mod.assemble("Acme", "acme.com",
                               {k: {"data": v["data"], "errors": [],
                                    "worker": k}
                                for k, v in dsr["workers"].items()},
                               plan,
                               {"items": ["first snapshot — baseline established"],
                                "suspicious": False},
                               [], "passive mode")
    md = dossier_mod.render_markdown(full)
    assert "# Company Dossier: Acme (acme.com)" in md
    assert "DO NOT CONTACT" in md
    assert plan[0]["card_id"] in md


if __name__ == "__main__":
    for name, fn in sorted([(k, v) for k, v in globals().items()
                            if k.startswith("test_")]):
        check(name, fn)
    print(f"{len(PASS)}/{len(PASS) + len(FAIL)} passed")
    for n, e in FAIL:
        print(f"FAIL {n}: {e}")
    sys.exit(1 if FAIL else 0)
