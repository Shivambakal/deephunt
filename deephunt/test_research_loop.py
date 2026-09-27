"""Tests for the DEEPHUNT 2.x research loop — every new module, no network,
no real targets. Synthetic fixtures only.

    python3 test_research_loop.py
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "intel"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS, FAIL = [], []

_TMP = tempfile.mkdtemp(prefix="deephunt_loop_")


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(f"[{'ok' if cond else 'FAIL'}] {name}" + (f" -- {detail}" if detail and not cond else ""))


# isolate on-disk state
import learning as causal_mod
import regression as regression_mod
import object_pool as object_pool_mod

causal_mod.STATE_DIR = os.path.join(_TMP, "causal")
regression_mod._orig_target_dir = regression_mod._target_dir
regression_mod._target_dir = lambda t: os.path.join(
    _TMP, "regressions", t) if os.makedirs(
    os.path.join(_TMP, "regressions", t), exist_ok=True) is None else None
object_pool_mod.STATE_DIR = os.path.join(_TMP, "pool")

import identity_matrix
import object_pool
import oracle
import verifier
import difficulty
import regression
import learning
import fuzz as fuzz_mod
import semantic
import intel_compiler
import report
import differential
from benchmarks import MockTarget


# ---------------- identity_matrix ----------------

class _FakeWM:
    def __init__(self):
        self.model = {
            "identities": [
                {"name": "alice", "roles": ["user"], "tenant": "t1"},
                {"name": "bob", "roles": ["user"], "tenant": "t1"},
                {"name": "admin", "roles": ["admin"], "tenant": "t1"},
            ],
            "objects": [{"name": "order:1", "owner": "alice", "states": ["draft", "paid"]}],
        }


def t_matrix():
    cells = identity_matrix.generate(_FakeWM())
    check("matrix_cells", len(cells) > 0, f"{len(cells)} cells")
    check("matrix_cell_shape", all(
        {"role_control", "role_variant", "object", "action"} <= set(c) for c in cells))
    high = [c for c in cells if c.get("priority") == "high"]
    check("matrix_high_priority", len(high) > 0)
    pair = identity_matrix.to_differential(cells[0])
    check("matrix_pair", pair["single_variable"] and "control" in pair
          and "test" in pair and pair["dimension"])
    rep = identity_matrix.coverage_report(cells)
    check("matrix_coverage", rep["cells"] == len(cells))


# ---------------- object_pool ----------------

def t_pool():
    pool = object_pool.ObjectPool("unittest")
    pool.observe("ORD-48291", param_name="order_id", context="created order")
    pool.observe("sk_live_9f8e7d6c5b4a", param_name="api_key", context="config")
    check("pool_get", pool.get("order_id") == "ORD-48291")
    sens = [r for r in pool.items.values() if r["param_name"] == "api_key"][0]
    check("pool_secret_suppressed", sens["value"] is None and sens["sensitive"])
    check("pool_secret_prefix", sens["value_prefix"] == "sk_live_")
    pool.transition("ORD-48291", "paid", actor="alice")
    check("pool_transition", pool.get_for("order_id", state="paid") == "ORD-48291")
    pool.save()
    pool2 = object_pool.ObjectPool("unittest")
    check("pool_persist", pool2.get("order_id") == "ORD-48291")


# ---------------- oracle ----------------

def t_oracle():
    control = "GET /api/orders/1 as alice -> 200 {\"id\":1,\"owner\":\"alice\"}"
    test_idor = "GET /api/orders/1 as bob -> 200 {\"id\":1,\"owner\":\"alice\"}"
    v = oracle.ownership_oracle(control, test_idor, {})
    check("oracle_idor_violated", v.verdict == oracle.VIOLATED, v.verdict)
    test_held = "GET /api/orders/1 as bob -> 403 forbidden"
    v2 = oracle.ownership_oracle(control, test_held, {})
    check("oracle_held", v2.verdict == oracle.HELD, v2.verdict)
    v3 = oracle.auth_boundary_oracle("alice -> 200 dashboard",
                                     "anon -> 200 dashboard data", {})
    check("oracle_auth_boundary", v3.verdict == oracle.VIOLATED, v3.verdict)
    v3b = oracle.auth_boundary_oracle("alice -> 200 dashboard",
                                      "anon -> 401 unauthorized", {})
    check("oracle_auth_held", v3b.verdict == oracle.HELD, v3b.verdict)
    v4 = oracle.tenant_isolation_oracle(
        "t1 user -> 200 {\"id\": 7, \"tenant\": \"t1\", \"secret\": \"t1-customer-data\"}",
        "t2 user -> 200 {\"id\": 7, \"tenant\": \"t1\", \"secret\": \"t1-customer-data\"}", {})
    check("oracle_tenant", v4.verdict == oracle.VIOLATED, v4.verdict)
    summ = oracle.summarize([v, v2])
    check("oracle_summarize", summ[0] == oracle.VIOLATED)


# ---------------- differential ----------------

def t_differential():
    dims = [d for d, _ in differential.DIMENSIONS]
    for want in ("tenant-vs-tenant", "method-vs-method", "client-vs-client",
                 "state-vs-state", "version-vs-version", "before-vs-after"):
        check(f"diff_dim_{want}", want in dims)
    verdict, reasons = differential.compare(
        "200 {\"id\":1,\"owner\":\"alice\"}",
        "200 {\"id\":1,\"owner\":\"alice\"}")
    check("diff_identical", verdict == "identical")
    verdict2, _ = differential.compare(
        "GET as alice -> 200 {\"id\":1,\"owner\":\"alice\"}",
        "GET as bob -> 403 forbidden")
    check("diff_interesting", verdict2 == "interesting", verdict2)
    pair = differential.make_pair(
        "user-a-vs-b", {"method": "GET", "path": "/api/orders/1"},
        {"identity": "alice"}, {"identity": "bob"})
    check("diff_pair", pair["single_variable"] and pair["control"]["identity"] == "alice")


# ---------------- verifier ----------------

def _good_evidence():
    return {
        "control_observation": "GET /api/orders/1 as alice -> 200 owner alice",
        "test_observation": "GET /api/orders/1 as bob -> 403 forbidden",
        "artifacts": {"request_log": "...", "response_pair": "..."},
        "killed_alternatives": {"caching artifact": "replayed, asymmetry persists"},
    }


def t_verifier():
    rep = verifier.verify_finding("IDOR on /api/orders/1",
                                  {"control_observation": "x", "test_observation": "y",
                                   "artifacts": {}},
                                  technique_id="IDOR-01")
    check("verifier_contract_reject", rep.verdict == verifier.REJECTED, rep.verdict)
    rep2 = verifier.verify_finding("IDOR on /api/orders/1", _good_evidence(),
                                   technique_id="IDOR-01",
                                   alternatives=["caching artifact"])
    check("verifier_verified", rep2.verdict == verifier.VERIFIED, rep2.verdict)
    rep3 = verifier.verify_finding("IDOR on /api/orders/1", _good_evidence(),
                                   technique_id="IDOR-01",
                                   alternatives=["unexplained alternative"])
    check("verifier_needs_more", rep3.verdict == verifier.NEEDS_MORE, rep3.verdict)
    finding = {"claim": "IDOR", "technique_id": "IDOR-01",
               "control_observation": _good_evidence()["control_observation"],
               "test_observation": _good_evidence()["test_observation"],
               "artifacts": _good_evidence()["artifacts"],
               "competition": {"disproven": [
                   {"explanation": "caching artifact",
                    "disproven_by": "replayed, asymmetry persists"}],
                   "surviving": []}}
    rep4 = verifier.verify_for_compete(finding)
    check("verifier_for_compete", rep4.verdict == verifier.VERIFIED, rep4.verdict)


# ---------------- difficulty ----------------

def t_difficulty():
    store = learning.CausalStore("unittest-diff")
    store.record_trial("IDOR-01", "web", "confirmed", hypothesis="idor on orders")
    store.record_trial("XSS-01", "web", "rejected", failure_reason="encoded output",
                       hypothesis="xss on search")
    dims = difficulty.estimate_difficulty({"statement": "idor?", "technique_id": "IDOR-01"},
                                          store)
    check("difficulty_dims", dims["historical_success"] > 0.5, dims)
    cands = [{"statement": "idor on orders", "technique_id": "IDOR-01",
              "severity": "high"},
             {"statement": "xss on search", "technique_id": "XSS-01",
              "severity": "low"}]
    ranked = difficulty.rank(cands, memory={}, lessons=store)
    check("difficulty_rank", ranked[0]["technique_id"] == "IDOR-01",
          [c.get("_utility") for c in ranked])
    risky = [{"statement": "x", "_risk_norm": 0.9}]
    check("difficulty_risk_gate", difficulty.rank(risky) == [])


# ---------------- learning ----------------

def t_learning():
    store = learning.CausalStore("unittest-learn")
    store.record_trial("IDOR-01", "web", "confirmed",
                       evidence_seen=["privilege_differs_by_identity"],
                       hypothesis="idor")
    store.record_trial("IDOR-01", "web", "confirmed",
                       evidence_seen=["privilege_differs_by_identity"],
                       hypothesis="idor again")
    store.record_trial("IDOR-01", "web", "rejected", failure_reason="ownership checked",
                       evidence_seen=["explicit_denial"], hypothesis="idor")
    check("learning_hist", 0 < store.historical_success("IDOR-01", "web") < 1)
    pred = store.predictive_evidence(top_n=5)
    check("learning_predictive",
          any(p["evidence"] == "privilege_differs_by_identity" for p in pred), pred[:2])
    wrong = store.consistently_wrong(min_count=1)
    check("learning_wrong", isinstance(wrong, list))


# ---------------- regression ----------------

def t_regression():
    finding = {"claim": "IDOR on /api/orders/1", "technique_id": "IDOR-01",
               "control_observation": "alice -> 200", "test_observation": "bob -> 403",
               "control_request": {"identity": "alice"},
               "test_request": {"identity": "bob"},
               "oracle": "ownership_must_match_actor",
               "scope_hosts": ["mockshop"], "auth_basis": "synthetic"}
    spec = regression.from_finding(finding, "unittest-target")
    check("regression_created", spec["expected"] == "HELD" and spec["id"].startswith("REG-"))
    check("regression_listed", any(s["id"] == spec["id"]
                                  for s in regression.list_all("unittest-target")))
    ev = regression.evaluate(spec, "alice -> 200", "bob -> 403")
    check("regression_held", ev["passed"] and ev["oracle_verdict"] == "HELD", ev)
    ev2 = regression.evaluate(spec, "alice -> 200", "bob -> 200 alice data")
    check("regression_regressed", not ev2["passed"], ev2)
    dry = regression.run("unittest-target", spec["id"])
    check("regression_dryrun", dry["dry_run"] and dry["ok"]
          and "transmitted" not in dry)


# ---------------- intel_compiler ----------------

def t_intel_compiler():
    tech_knowledge = {
        "wordpress": {"kev": [{"cve": "CVE-2024-1234", "name": "WP plugin RCE"}],
                      "news": [{"title": "mass exploitation of WP plugin"}]},
    }
    out = intel_compiler.compile("mockshop", tech_knowledge, ["wordpress"],
                                 cards=[], max_hypotheses=4)
    check("intel_compile", len(out["hypotheses"]) > 0, out)
    check("intel_no_dump", all("preconditions" in h for h in out["hypotheses"]))
    check("intel_bounded", len(out["hypotheses"]) <= 4)


# ---------------- report ----------------

def t_report():
    finding = {"claim": "IDOR", "technique_id": "IDOR-01", "severity": "high",
               "control_observation": "alice -> 200",
               "test_observation": "bob -> 200 token=sk_live_abcdef123456",
               "scope_hosts": ["mockshop"], "auth_basis": "synthetic",
               "confidence": 0.85}
    rep = report.build_finding_report(finding, regression_id="REG-0001")
    check("report_redact", "sk_live_abcdef123456" not in rep["test"], rep["test"][:80])
    check("report_fields", rep["regression_test"] == "REG-0001"
          and rep["claim"] == "IDOR")
    md = report.to_markdown(rep)
    check("report_markdown", "# Finding" in md or "IDOR" in md)


# ---------------- semantic ----------------

def t_semantic():
    import textwrap
    src = textwrap.dedent('''
        from flask import Flask, request
        app = Flask(__name__)
        @app.route("/api/orders/<int:oid>")
        def get_order(oid):
            q = "SELECT * FROM orders WHERE id = %s" % request.args.get("oid")
            return db.execute(q)
    ''')
    d = tempfile.mkdtemp(prefix="sem_")
    open(os.path.join(d, "app.py"), "w").write(src)
    arch = semantic.analyze_repo(d, use_semgrep=False)
    check("semantic_endpoints", any("/api/orders" in e.get("path", "")
                                   for e in arch.get("endpoints", [])),
          arch.get("endpoints"))
    check("semantic_flows", len(arch.get("flows", [])) > 0, arch.get("flows"))
    hyps = semantic.to_hypotheses(arch, target="mockshop")
    check("semantic_hyps", len(hyps) > 0)


# ---------------- fuzz ----------------

def t_fuzz():
    seen = []

    def executor(case):
        seen.append(case)
        inj = case.get("params", {}).get("q", "")
        if "'" in str(inj):
            return {"status": 500, "body": "SQL syntax error near '''", "novel": True}
        return {"status": 200, "body": "ok", "novel": False}

    def oracle_fn(case, obs):
        return "VIOLATED" if "SQL" in str(obs.get("body", "")) else "HELD"

    seeds = [{"method": "GET", "path": "/search", "params": {"q": "x"}},
             {"method": "GET", "path": "/search", "params": {"q": "'"}}]
    res = fuzz_mod.run_campaign(seeds, executor, budget=12, seed=7,
                                oracle_fn=oracle_fn)
    check("fuzz_runs", res.total > 0 and res.total <= 12)
    check("fuzz_signal", len(res.interesting) > 0,
          f"interesting={len(res.interesting)} total={res.total}")
    mini = fuzz_mod.minimize(seeds[1], executor, oracle_fn)
    check("fuzz_minimize", isinstance(mini, dict))


# ---------------- synthetic E2E ----------------

def t_e2e():
    """Full loop on a synthetic mock target: observe -> model -> hypothesize
    -> rank -> authorize (dry-run) -> differential -> oracle -> verifier ->
    learn -> regression."""
    target = MockTarget("mockshop", {
        "/api/orders/1": {"auth_required": True, "owner": "alice", "vuln": "idor"},
        "/api/orders/2": {"auth_required": True, "owner": "alice"},
    })
    # observe -> model
    from world_model import WorldModel
    wm = WorldModel("mockshop")
    wm.add_endpoint("GET", "/api/orders/1", params=["order_id"])
    wm.add_identity("alice", roles=["user"])
    wm.add_identity("bob", roles=["user"])
    pool = object_pool.ObjectPool("e2e")
    pool.observe("1", param_name="order_id", context="order endpoint",
                 object_type="order", owner="alice")
    # hypothesize
    hyp = {"statement": "BOLA: bob can read alice's order via /api/orders/1",
           "technique_id": "IDOR-01", "severity": "high",
           "investigator_test": "GET /api/orders/1 as bob"}
    # rank (difficulty-aware)
    store = learning.CausalStore("e2e")
    ranked = difficulty.rank([dict(hyp)], memory={}, lessons=store)
    check("e2e_rank", ranked[0]["_utility"] is not None)
    # authorize (dry-run): propose_test gate only — no transmission
    from brain.session import ResearchSession
    sess = ResearchSession(objective="e2e:mockshop")
    hid = sess.add_hypothesis(hyp["statement"], provenance="e2e",
                              investigator_test=hyp["investigator_test"])["id"]
    test = sess.propose_test(
        hypothesis_id=hid,
        expected_observation="bob receives alice's order data (200)",
        reason="differential pair: alice vs bob on same object",
        scope_hosts=["mockshop"], auth_basis="synthetic-fixture",
        success_criteria="bob gets 200 with alice's data",
        failure_criteria="bob gets 403/404")
    check("e2e_gate", test.get("dry_run") or "id" in test, test.get("id"))
    # differential on the SYNTHETIC target
    pair = differential.make_pair(
        "user-a-vs-b", {"method": "GET", "path": "/api/orders/1"},
        {"identity": "alice"}, {"identity": "bob"})
    c_obs = target.request("/api/orders/1", "alice")
    t_obs = target.request("/api/orders/1", "bob")
    c_text = f"{c_obs['status']} {c_obs['body']}"
    t_text = f"{t_obs['status']} {t_obs['body']}"
    verdict, reasons = differential.compare(c_text, t_text)
    check("e2e_diff", verdict in ("interesting", "differs"), (verdict, reasons))
    # oracle
    ov = oracle.ownership_oracle(c_text, t_text, {})
    check("e2e_oracle", ov.verdict == oracle.VIOLATED, ov.verdict)
    sess.record_result(test["id"], "confirmed", observed=t_text,
                       learned="synthetic IDOR reproduced on mock target")
    # verifier (independent falsification attempt)
    rep = verifier.verify_finding(
        hyp["statement"],
        {"control_observation": c_text, "test_observation": t_text,
         "artifacts": {"request_log": "mock", "response_pair": "mock"},
         "killed_alternatives": {"shared cache": "mock: replayed, persists"}},
        technique_id="IDOR-01", alternatives=["shared cache"])
    check("e2e_verifier", rep.verdict == verifier.VERIFIED, rep.verdict)
    # learn
    trial = store.record_trial("IDOR-01", "mockshop", "confirmed",
                               hypothesis=hyp["statement"],
                               evidence_seen=["privilege_differs_by_identity"])
    check("e2e_learn", trial["outcome"] == "confirmed")
    # regression
    finding = {"claim": hyp["statement"], "technique_id": "IDOR-01",
               "control_observation": c_text, "test_observation": t_text,
               "control_request": pair["control"], "test_request": pair["test"],
               "oracle": "ownership_must_match_actor",
               "scope_hosts": ["mockshop"], "auth_basis": "synthetic-fixture"}
    spec = regression.from_finding(finding, "mockshop")
    check("e2e_regression", spec["expected"] == "HELD")
    ev = regression.evaluate(spec, c_text, "bob -> 403 forbidden")
    check("e2e_regression_held", ev["passed"] and ev["oracle_verdict"] == "HELD")
    # report
    rpt = report.build_finding_report(finding, regression_id=spec["id"])
    check("e2e_report", rpt["regression_test"] == spec["id"])


def main():
    for fn in [t_matrix, t_pool, t_oracle, t_differential, t_verifier,
               t_difficulty, t_learning, t_regression, t_intel_compiler,
               t_report, t_semantic, t_fuzz, t_e2e]:
        try:
            fn()
        except Exception as e:
            import traceback
            FAIL.append(fn.__name__)
            print(f"[FAIL] {fn.__name__} raised {e!r}")
            traceback.print_exc(limit=3)
    print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
    if FAIL:
        print("FAILURES:", FAIL)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
