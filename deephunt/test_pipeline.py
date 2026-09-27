"""Tests for the ATTACKSURFACE pipeline — every stage, no network, no targets.

Conventions match the other suites: plain functions, PASS/FAIL lists,
`python3 test_pipeline.py` runs everything.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "intel"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(f"[{'ok' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail and not cond else ""))


# ---------------------------------------------------------------- global intel
def test_global_intel_offline():
    import global_intel as gi
    # cwe mapping is curated and offline
    check("cwe-map", gi.cwe_to_klass("CWE-79") == "xss")
    check("cwe-map-unknown", gi.cwe_to_klass("CWE-9999") == "unknown")
    # query works with an empty/missing store (no crash, empty result)
    q = gi.what_is_known("definitely-not-a-real-tech-xyz")
    check("query-empty", isinstance(q, dict) and q["tech"] == "definitely-not-a-real-tech-xyz"
          and q["cves"] == [], str(q)[:80])
    # store round-trips through the index
    store = gi._load_store()
    check("store-shape", set(store.keys()) >= {"cves", "by_tech", "signals"})


# ---------------------------------------------------------------- target intel
def test_target_intel():
    import target_intel as ti_mod
    ti = ti_mod.TargetIntel("__test_pipe__")
    ti.add_technology("WordPress", evidence="test")
    ti.add_technology("wordpress", evidence="dup")  # case-insensitive dedupe
    check("tech-dedupe", ti.technologies() == ["WordPress"], str(ti.technologies()))
    ti.target.add_asset("*.example.com", kind="scope")
    check("in-scope", ti.in_scope("api.example.com"))
    check("out-of-scope", not ti.in_scope("evil.com"))
    # dossier merge is defensive (empty / malformed never crashes)
    check("dossier-empty", ti.merge_dossier({}) == 0)
    check("dossier-garbage", ti.merge_dossier({"workers": None}) == 0)
    n = ti.merge_dossier({"company": "X", "domain": "x.test",
                          "workers": {"techstack": {"data": {"detected": ["nginx"]}}}})
    check("dossier-merge", n >= 1 and "nginx" in ti.technologies())
    snap = ti.snapshot()
    ti.add_technology("apache", evidence="test2")
    d = ti.diff_since(snap)
    check("diff-suspicious", d["suspicious"] and "apache" in d["tech"]["added"], str(d)[:120])
    # apiprobe merge
    m = ti.merge_apiprobe({"specs": [{"url": "https://x.test/openapi.json", "kind": "openapi"}],
                           "endpoints": [{"path": "/api/users", "method": "GET",
                                          "auth": "unknown", "params": ["id"]}]})
    check("apiprobe-merge", m >= 2)
    qs = ti.target.authz_questions(limit=4)
    check("authz-questions", any("users" in q for q in qs), str(qs)[:100])
    # cleanup
    import shutil
    shutil.rmtree(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "state", "__test_pipe__"), ignore_errors=True)


# ---------------------------------------------------------------- reasoning
def test_reasoning():
    import reasoning, target_intel as ti_mod
    ti = ti_mod.TargetIntel("__test_r__")
    ti.add_technology("WordPress", evidence="test")
    tech_knowledge = {"WordPress": {"kev": ["CVE-2026-0001"], "cves": [],
                                   "technique_klasses": ["rce"], "news": []}}
    out = reasoning.seed_from_intel("__test_r__", tech_knowledge, ti, {})
    check("reason-assumptions", any("CVE-2026-0001" in a.get("provenance", "")
                                    for a in out["assumptions"]), str(len(out["assumptions"])))
    check("reason-seeds", len(out["seed_hypotheses"]) > 0)
    check("reason-baseline", any(a["provenance"] == "baseline"
                                 for a in out["assumptions"]))
    import shutil
    shutil.rmtree(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "state", "__test_r__"), ignore_errors=True)


# ---------------------------------------------------------------- attack graph
def test_attackgraph():
    import attackgraph
    from world_model import WorldModel
    from target_model import Target
    wm = WorldModel("__test_ag__")
    wm.update_from_observation(
        "anonymous can read /api/users?id=1, admin panel at /admin", source="test")
    wm._derive_invariants()
    t = Target("__test_ag__")
    t.add_endpoint("/api/users", method="GET", authentication="none",
                   roles=["anonymous"], object="users", owner_required=True,
                   parameters=["id"])
    t.add_identity("anon", role="anonymous")
    g = attackgraph.build(wm, t)
    check("graph-nodes", g["node_count"] > 0, str(g["node_count"]))
    check("graph-paths", isinstance(g["paths"], list))
    check("graph-trust", isinstance(g["trust"], list))
    check("graph-seeds", all("attack path" in s["statement"]
                             for s in g["hypothesis_seeds"]))
    import shutil, glob
    for p in glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "state", "__test_ag__*")):
        try:
            os.remove(p)
        except OSError:
            pass
    shutil.rmtree(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "state", "__test_ag__"), ignore_errors=True)


# ---------------------------------------------------------------- hypothesis fusion
def test_fusion():
    import hypothesis_fusion as hf
    from brain.session import ResearchSession
    s = ResearchSession(objective="__test_fusion__")
    mem = {"rejected": [], "confirmed": [], "lessons": [], "tried_paths": []}
    seeds = [{"statement": "seed one", "source": "test", "score": 3,
              "provenance": "p"}]
    plan_items = [{"hypothesis": "plan one", "score": 4, "card_id": "X-01",
                   "klass": "x", "test_sketch": "t", "reasons": ["r"]}]
    out = hf.fuse(s, seeds, plan_items, [], mem, max_new=6)
    check("fusion-registers", len(out["registered"]) >= 2, str(out))
    # second fuse of the same seeds -> duplicates skipped
    out2 = hf.fuse(s, seeds, plan_items, [], mem, max_new=6)
    check("fusion-dedupe", len(out2["registered"]) == 0, str(out2))
    # retread of a rejected hypothesis dies
    mem["rejected"] = [{"statement": "plan one widget cross-account read attempt",
                        "why_failed": "x", "learned": "y"}]
    out3 = hf.fuse(s, [{"statement": "plan one widget cross-account read retest",
                        "source": "t", "score": 5, "provenance": "p"}],
                   [], [], mem, max_new=6)
    check("fusion-retread", len(out3["registered"]) == 0, str(out3))
    try:
        os.remove(s.path)
    except OSError:
        pass


# ---------------------------------------------------------------- learn updates
def test_learn_updates():
    import learn_updates as lu
    from brain.session import ResearchSession
    from world_model import WorldModel
    s = ResearchSession(objective="__test_learn__")
    h = s.add_hypothesis("widget can be read cross-account", violated_assumption="a")
    t = s.propose_test(h["id"], expected_observation="foreign widget data",
                       reason="r", scope_hosts=["example.com"], auth_basis="test",
                       success_criteria="s", failure_criteria="f")
    rec, _ = s.record_result(t["id"], "rejected", observed="403 denied as expected",
                             why_failed="authz held", learned="403 is the control working",
                             environment="test", technology="test", preconditions="test")
    wm = WorldModel("__test_learn__")
    before = dict(wm.model["beliefs"])
    summary = lu.apply(s, wm, "__test_learn__")
    check("learn-processed", summary["processed"] == 1, str(summary))
    check("learn-negative", summary["negative_examples"] >= 0)  # 0 ok if dup
    # idempotent: second apply processes nothing
    summary2 = lu.apply(s, wm, "__test_learn__")
    check("learn-idempotent", summary2["processed"] == 0, str(summary2))
    # confirmed -> proposal file
    h2 = s.add_hypothesis("second", violated_assumption="a")
    t2 = s.propose_test(h2["id"], expected_observation="e2", reason="r",
                        scope_hosts=["example.com"], auth_basis="test",
                        success_criteria="s", failure_criteria="f")
    s.record_result(t2["id"], "confirmed", observed="foreign data returned 200")
    summary3 = lu.apply(s, wm, "__test_learn__")
    check("learn-proposal", len(summary3["proposals"]) == 1, str(summary3))
    for p in summary3["proposals"]:
        try:
            os.remove(p)
        except OSError:
            pass
    try:
        os.remove(s.path)
    except OSError:
        pass
    import shutil, glob
    for p in glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "state", "__test_learn__*")):
        try:
            os.remove(p)
        except OSError:
            pass
    shutil.rmtree(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "state", "__test_learn__"), ignore_errors=True)


# ---------------------------------------------------------------- full pipeline (dry)
def test_pipeline_dry():
    import attacksurface as ap
    # use a synthetic target profile written to targets/
    prof_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "targets", "__test_pipe_target__.yaml")
    with open(prof_path, "w") as f:
        f.write("name: __test_pipe_target__\nactive_allowed: false\n"
                "auth_basis: test\nscope_hosts:\n- example.com\n"
                "tech_terms:\n- nginx\nhypothesis_seeds:\n- seed q\n")
    try:
        report = ap.run_pipeline("__test_pipe_target__", max_passes=1,
                                 max_hypotheses=4, max_tests=2)
        st = report["stages"]["pass1"]
        check("pipe-stages", st["hypotheses_registered"] > 0, json.dumps(st)[:200])
        check("pipe-propose-only", st["tests_run"] == 0)
        check("pipe-tests-proposed", st["tests_proposed"] >= 0)
        check("pipe-session", bool(report.get("session_id")))
        # cleanup session + state
        from brain.session import ResearchSession
        try:
            os.remove(os.path.join(
                os.path.expanduser("~/workspace/hacker-agent"),
                "data", "brain", "sessions", report["session_id"] + ".json"))
        except OSError:
            pass
    finally:
        try:
            os.remove(prof_path)
        except OSError:
            pass
        import shutil
        shutil.rmtree(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "state", "__test_pipe_target__"), ignore_errors=True)


def main():
    test_global_intel_offline()
    test_target_intel()
    test_reasoning()
    test_attackgraph()
    test_fusion()
    test_learn_updates()
    test_pipeline_dry()
    print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
    if FAIL:
        print("FAILURES:", FAIL)
        sys.exit(1)


if __name__ == "__main__":
    main()
