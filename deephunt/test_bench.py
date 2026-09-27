"""Tests for the DEEPHUNT P1 bench — mocks, harness, metrics.

Conventions match the other suites: plain functions, PASS/FAIL lists,
`python3 test_bench.py` runs everything. No network, no real systems:
every target is an in-process mock.

Covers:
  - mock fixtures behave as labeled (vuln exhibits, patched blocks)
  - harness template resolution ($setup/$chain/$test_chain/$disproof)
  - §19 metric computation on synthetic campaigns
  - determinism: two hunts, different run ids -> identical metrics
  - oracle step-awareness (the multi-step transcript fix)
  - verifier contract enforcement + 400-as-denial
  - MockEngine authorization discipline (no token / wrong scope -> refuse)
"""
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(f"[{'ok' if cond else 'FAIL'}] {name}" +
          (f" — {detail}" if detail and not cond else ""))


# ---------------------------------------------------------------- fixtures
def test_shop_labels():
    from bench_targets.shop import ShopMock
    v, p = ShopMock(patched=False), ShopMock(patched=True)
    s, d, _ = v.probe("get_order", {"order_id": "101", "identity": "alice"})
    check("shop-vuln-bola", s == 200 and d.get("owned by") == "bob" and
          "bob@example.com" in d.get("email", ""), f"status={s}")
    s, d, _ = p.probe("get_order", {"order_id": "101", "identity": "alice"})
    check("shop-patched-blocks", s == 403, f"status={s}")
    s, _, _ = v.probe("get_order", {"order_id": "101", "identity": "anonymous"})
    check("shop-anon-401", s == 401, f"status={s}")
    gt = v.ground_truth()
    check("shop-gt", gt["vulnerable"] is True and
          gt["root_cause"] == "bola:get_order")
    check("shop-gt-patched", p.ground_truth()["vulnerable"] is False)


def test_workflow_labels():
    from bench_targets.workflow import WorkflowMock
    v = WorkflowMock(patched=False)
    s, d, _ = v.probe("create_order", {"identity": "alice"})
    oid = d["order_id"]
    s, _, _ = v.probe("pay_order", {"order_id": oid, "identity": "alice"})
    check("workflow-vuln-skip-pay", s == 200, f"status={s}")
    s, d, _ = v.probe("fulfill_order", {"order_id": oid, "identity": "alice"})
    check("workflow-vuln-fulfilled", s == 200 and d["state"] == "FULFILLED")
    p = WorkflowMock(patched=True)
    s, d, _ = p.probe("create_order", {"identity": "alice"})
    oid = d["order_id"]
    s, d, _ = p.probe("pay_order", {"order_id": oid, "identity": "alice"})
    check("workflow-patched-rejects", s == 400 and
          "invalid transition" in d.get("error", ""), f"status={s}")
    s, _, _ = p.probe("approve_order", {"order_id": oid, "identity": "alice",
                                        "role": "buyer"})
    check("workflow-nonmanager-403", s == 403, f"status={s}")


def test_ragbot_labels():
    from bench_targets.ragbot import RagbotMock, CANARY, CANARY_URL, INJECTION
    v, p = RagbotMock(patched=False), RagbotMock(patched=True)
    for m in (v, p):
        m.probe("plant_doc", {"user": "alice", "title": "notes",
                              "content": "draft. " + INJECTION})
    s, d, _ = v.probe("chat", {"user": "alice",
                               "message": "what was Q3 revenue?"})
    check("ragbot-vuln-exfil", s == 200 and CANARY in d["reply"] and
          CANARY_URL in d["reply"])
    s, d, _ = p.probe("chat", {"user": "alice",
                               "message": "what was Q3 revenue?"})
    check("ragbot-patched-no-exfil", s == 200 and CANARY not in d["reply"]
          and CANARY_URL not in d["reply"])
    s, d, _ = v.probe("check_access", {"user": "alice", "doc_id": "doc_fin"})
    check("ragbot-acl-denies", d.get("access") == "denied")


def test_agent_labels():
    from bench_targets.agent import AgentMock, INJECTED_TICKET, BENIGN_TICKET
    v, p = AgentMock(patched=False), AgentMock(patched=True)
    for mock, label in ((v, "vuln"), (p, "patched")):
        _, d, _ = mock.probe("create_ticket", {"user": "alice",
                                               "text": INJECTED_TICKET})
        tid = d["ticket_id"]
        s, d, dl = mock.probe("run_agent", {"ticket_id": tid})
        fired = bool(dl.get("refund_issued"))
        check(f"agent-{label}-refund",
              (fired and "refund issued" in " ".join(d["transcript"]))
              if label == "vuln" else (not fired and s == 200),
              f"fired={fired}")
    # benign ticket never refunds, even on the vuln mock
    _, d, _ = v.probe("create_ticket", {"user": "alice", "text": BENIGN_TICKET})
    _, d2, dl2 = v.probe("run_agent", {"ticket_id": d["ticket_id"]})
    check("agent-benign-no-refund", not dl2.get("refund_issued"))


# ---------------------------------------------------------------- harness
def test_template_resolution():
    from bench_run import MockEngine
    from bench_targets.shop import ShopMock
    from benchmarks import Campaign
    eng = MockEngine(ShopMock(), Campaign(target="t"))
    bindings = {"setup": [{"data": {"ticket_id": "TCK-9"}}],
                "test_chain": [{"data": {"order_id": "ORD-3"}}],
                "disproof": [{"data": {"x": "1"}}]}
    check("tpl-setup", eng._resolve_value("$setup.0.ticket_id", bindings,
                                          "disproof") == "TCK-9")
    check("tpl-chain-default", eng._resolve_value("$chain.0.order_id",
                                                  bindings,
                                                  "test_chain") == "ORD-3")
    check("tpl-ns", eng._resolve_value("$test_chain.0.order_id", bindings,
                                       "disproof") == "ORD-3")
    check("tpl-disproof", eng._resolve_value("$disproof.0.x", bindings,
                                             "disproof") == "1")
    check("tpl-literal", eng._resolve_value("plain", bindings,
                                            "disproof") == "plain")
    check("tpl-missing", eng._resolve_value("$setup.5.nope", bindings,
                                            "disproof") == {})


def test_engine_authorization():
    from bench_run import MockEngine
    from bench_targets.shop import ShopMock
    from benchmarks import Campaign
    from brain.gate import TestAuthorization
    eng = MockEngine(ShopMock(), Campaign(target="t"))
    plan = {"setup": [], "control": ("list_orders", {"identity": "alice"}),
            "test": ("list_orders", {"identity": "alice"})}
    # no token at all
    try:
        eng.execute_plan(plan, None)
        check("engine-refuses-no-token", False, "no exception raised")
    except PermissionError:
        check("engine-refuses-no-token", True)
    # token for the wrong scope
    bad = TestAuthorization(test_id="T", hypothesis_id="H",
                            session_id="S", scope_hosts=["mock:other"])
    try:
        eng.execute_plan(plan, bad)
        check("engine-refuses-wrong-scope", False, "no exception raised")
    except PermissionError:
        check("engine-refuses-wrong-scope", True)
    # valid token, correct scope -> executes
    good = TestAuthorization(test_id="T", hypothesis_id="H",
                             session_id="S", scope_hosts=["mock:shop"])
    rec = eng.execute_plan(plan, good)
    check("engine-executes-authorized",
          "HTTP 200" in rec["control_observation"])


def test_metrics_math():
    from benchmarks import Campaign
    c = Campaign(target="m")
    c.known_vulns = 2
    for _ in range(10):
        c.trial()
    c.report_finding("rc1", confirmed=True, evidence_ok=True)
    c.known_found = 1
    c.report_finding("rc1", confirmed=True, evidence_ok=True)  # dup root cause
    c.report_finding("rc2", confirmed=False)  # reported, not confirmed
    c.verify(rejected=True)
    c.verify(rejected=False)
    c.chains_started, c.chains_completed = 2, 1
    c.endpoints_known, c.endpoints_hit = 4, 3
    m = c.metrics()
    check("m-recall", m["discovery_recall"] == 0.5, m["discovery_recall"])
    check("m-precision", m["precision"] == round(2 / 3, 3), m["precision"])
    check("m-proof", m["proof_rate"] == 1.0)
    check("m-chain", m["chain_completion"] == 0.5)
    check("m-vrr", m["verifier_rejection_rate"] == 0.5)
    check("m-dup", m["duplicate_rate"] == round(1 / 3, 3), m["duplicate_rate"])
    check("m-coverage", m["endpoint_coverage"] == 0.75)
    check("m-cost", m["cost_to_valid"] == 5.0, m["cost_to_valid"])


def test_oracle_step_awareness():
    import oracle as om
    from bench_targets import fmt_observation
    vuln_test = ("--- step: create_order ---\n" +
                 fmt_observation("create_order", {}, 201, {"order_id": "O1"},
                                 {}) +
                 "\n--- step: pay_order ---\n" +
                 fmt_observation("pay_order", {}, 200, {"state": "PAID"},
                                 {"to": "PAID"}))
    patched_test = ("--- step: create_order ---\n" +
                    fmt_observation("create_order", {}, 201,
                                    {"order_id": "O1"}, {}) +
                    "\n--- step: pay_order ---\n" +
                    fmt_observation("pay_order", {}, 400,
                                    {"error": "invalid transition"}, {}))
    ctx = {"attempted_transition": "CREATED->PAID skipping APPROVED"}
    v = om.check("state_transition", "HTTP 200", vuln_test, ctx)
    check("oracle-multistep-violated", v.verdict == "VIOLATED", v.verdict)
    v2 = om.check("state_transition", "HTTP 200", patched_test, ctx)
    check("oracle-multistep-held", v2.verdict == "HELD", v2.verdict)
    # single-step behavior unchanged
    v3 = om.check("state_transition", "HTTP 200",
                  fmt_observation("pay", {}, 200, {}, {}), ctx)
    check("oracle-singlestep-violated", v3.verdict == "VIOLATED")


def test_denied_recognizes_400():
    import oracle as om
    check("denied-400", om._denied("HTTP 400\nbody: invalid transition"))
    check("denied-403", om._denied("HTTP 403"))
    check("not-denied-200", not om._denied("HTTP 200 ok"))


def test_verifier_contract():
    import verifier as vm
    rep = vm.verify_finding(
        "weak claim", {"control_observation": "HTTP 200",
                       "test_observation": "HTTP 200",
                       "artifacts": {"request_log": "x"},
                       "killed_alternatives": {}},
        technique_id="IDOR-01", alternatives=[])
    check("verifier-rejects-weak", rep.verdict == "REJECTED", rep.verdict)


def test_determinism():
    from bench_run import hunt_mock
    from bench_targets.shop import ShopMock
    r1 = uuid.uuid4().hex[:8]
    m1, _ = hunt_mock(ShopMock(patched=False), f"det-{r1}", verbose=False)
    r2 = uuid.uuid4().hex[:8]
    m2, _ = hunt_mock(ShopMock(patched=False), f"det-{r2}", verbose=False)
    drop = {"elapsed_s", "time_to_first_valid_s", "log", "findings"}
    d1 = {k: v for k, v in m1.items() if k not in drop}
    d2 = {k: v for k, v in m2.items() if k not in drop}
    check("deterministic-metrics", d1 == d2,
          str({k: (d1.get(k), d2.get(k)) for k in d1 if d1.get(k) != d2.get(k)}))
    check("deterministic-recall", m1["discovery_recall"] == 1.0)


def main():
    test_shop_labels()
    test_workflow_labels()
    test_ragbot_labels()
    test_agent_labels()
    test_template_resolution()
    test_engine_authorization()
    test_metrics_math()
    test_oracle_step_awareness()
    test_denied_recognizes_400()
    test_verifier_contract()
    test_determinism()
    print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
    if FAIL:
        print("FAILURES:", FAIL)
        sys.exit(1)


if __name__ == "__main__":
    main()
