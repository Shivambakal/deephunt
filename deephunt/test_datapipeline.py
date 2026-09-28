"""DEEPHUNT data-pipeline tests — the data-first reasoning upgrade.

Covers: target model (build/authz matrix/workflow gaps), technique dir
loading (all cards enriched), negative-example gate, observation round-trip,
frontend parsing, scholar reasoning wiring, and graph regeneration.
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import kb
import target_model
import observation
import frontend

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("PASS " if cond else "FAIL ") + name + (f" — {detail}" if detail and not cond else ""))


# ---------- 1. target model ----------
def test_target_model():
    t = target_model.Target("__test_target__")
    t.data = {k: ([] if isinstance(v, list) else v) for k, v in t.data.items()}
    t.add_endpoint("/api/orders/{id}", method="GET", authentication="required",
                   roles=["user", "admin"], object="order", owner_required=True,
                   parameters=["id"], observed_states=["pending", "paid"])
    t.add_endpoint("/api/admin/users", method="GET", authentication="required",
                   roles=["admin"], object="user", owner_required=False)
    t.add_endpoint("/api/public/status", method="GET", authentication="none",
                   object="status")
    t.add_identity("user_A", role="user", owns=["order_1"])
    t.add_identity("user_B", role="user", owns=["order_2"])
    t.add_identity("admin", role="admin")
    t.add_workflow("order", ["created", "confirmed", "paid", "shipped"],
                   [["created", "confirmed"], ["confirmed", "paid"], ["paid", "shipped"]])
    # observed transitions: one valid, one invalid, one repeated
    t.record_transition("order", "created", "confirmed", actor="user_A")
    t.record_transition("order", "created", "paid", actor="user_A")  # invalid skip
    for _ in range(3):
        t.record_transition("order", "confirmed", "paid", actor="user_A")  # repeated

    matrix = t.authz_matrix()
    check("authz_matrix_rows", len(matrix) == 4, f"got {len(matrix)}")
    risky = [r for r in matrix if r["risk"] == "test"]
    check("authz_matrix_flags_owner_endpoints", any(
        r["owner_required"] and r["object"] == "order" for r in risky))
    check("authz_matrix_flags_unauth", any(
        r["authentication"] == "none" for r in risky))

    qs = t.authz_questions()
    check("authz_questions_nonempty", len(qs) > 0, f"got {len(qs)}")
    check("authz_questions_mention_bola", any("someone else" in q for q in qs))

    gaps = t.workflow_gaps()
    kinds = {g["kind"] for g in gaps}
    check("workflow_gap_invalid", "invalid" in kinds, f"kinds={kinds}")
    check("workflow_gap_repeated", "repeated" in kinds, f"kinds={kinds}")
    check("workflow_gap_missing", "missing" in kinds, f"kinds={kinds}")
    anom = t.workflow_anomalies()
    check("workflow_anomalies_subset", all(a["kind"] in ("invalid", "unexpected") for a in anom)
          and len(anom) > 0)

    # persistence round-trip
    t.save()
    t2 = target_model.Target("__test_target__")
    check("target_save_load", len(t2.data["endpoints"]) == 3 and
          len(t2.data["workflows"]) == 1)
    # cleanup
    try:
        os.remove(t.path)
        os.rmdir(os.path.dirname(t.path))
    except OSError:
        pass


# ---------- 2. technique dir loading ----------
def test_technique_loading():
    cards = kb.load_techniques()
    check("cards_count_311", len(cards) == 311, f"got {len(cards)}")
    ids = [c["id"] for c in cards]
    check("cards_unique_ids", len(set(ids)) == len(ids))
    required = ("id", "name", "klass", "requires", "signals", "questions",
                "evidence", "followups", "test", "impact_hint")
    missing = [c["id"] for c in cards
               if not all(c.get(f) for f in required)]
    check("cards_all_enriched", not missing, f"missing={missing[:5]}")
    bad_ev = [c["id"] for c in cards
              if not c["evidence"].get("positive") or not c["evidence"].get("negative")]
    check("cards_evidence_both_sides", not bad_ev, f"bad={bad_ev[:5]}")
    ok, problems = kb.validate_cards()
    check("kb_validate", ok, f"problems={problems[:3]}")
    # original 71 preserved (incl. dedup renames)
    for must in ("IDOR-01", "AUTHZ-01", "JWT-01", "GQL-04", "OAUTH-02",
                 "SSRF-03", "CACHE-02", "WS-02", "AI-04", "AI-05"):
        check(f"card_preserved_{must}", kb.get_card(must) is not None)
    # new cards present (round 1 enrichment + 2026-09-27 ingestion)
    for must in ("BLO-02", "WS-05", "MOB-01", "CLD-02", "GQL-03",
                 "AUTHN-03", "OAUTH-03", "OAUTH-04", "OAUTH-05", "OAUTH-06",
                 "SAML-01", "IDOR-03", "GQL-05", "GQL-06", "API-04",
                 "WS-06", "WS-07", "SMUG-02", "SMUG-03", "SMUG-04",
                 "CACHE-03", "PROTO-02", "PROTO-03", "REDIR-02",
                 "AI-06", "AI-07", "AI-08", "AI-09", "AI-10", "AI-11", "AI-12",
                 "RACE-03", "BLO-05"):
        check(f"card_new_{must}", kb.get_card(must) is not None)
    # survey-2026 cards (2026-09-27 open-source survey)
    for must in ("AUTHB-01", "JWT-02", "HPP-01", "API-05", "API-06",
                 "GQL-07", "SEMGREP-01", "EV-01", "SEQ-01", "SEQ-02",
                 "SEQ-03", "PAYLOAD-01"):
        check(f"card_survey_{must}", kb.get_card(must) is not None)
    # wave1 cards (2026-09-27 hunt-wave ingestion: web, ai, corpora, forged)
    for must in ("W1-001", "W1-017", "W1-021", "W1-031", "A1-002", "A1-008",
                 "A1-016", "C1-001", "C1-007", "C1-014", "C1-016",
                 "F1-001"):
        check(f"card_wave1_{must}", kb.get_card(must) is not None)
    # sweep-2026-09-28 cards (daily intel sweep: A2M, auth-laundering, SalesBleed,
    # MCP exposure/supply-chain, GitLab 85706, MikroTrick, WP 87902, TrueBooker,
    # containerd checkpoint, register_argc_argv)
    for must in ("S28-AI-01", "S28-AI-02", "S28-AI-03", "S28-AI-04",
                 "S28-AI-05", "S28-AI-06", "S28-AI-07", "S28-AI-08",
                 "S28-AUTH-01", "S28-AUTH-02", "S28-AUTH-03", "S28-AUTH-04",
                 "S28-INJ-01", "S28-CLD-01", "S28-WEB-01"):
        check(f"card_sweep_{must}", kb.get_card(must) is not None)
    import train
    tcards = train.load_techniques()
    check("train_loads_311", len(tcards) == 311, f"got {len(tcards)}")
    seeds = train.recommend(
        [{"title": "/api/orders/{id}", "detail": "user_id param order invoice", "evidence": ""}],
        {"tech_terms": [], "vuln_classes": []}, {"rejected": [], "seen": []}, limit=5)
    check("train_recommend", len(seeds) > 0 and any("IDOR" in s["source"] for s in seeds),
          f"got {[s['source'] for s in seeds][:3]}")


# ---------- 3. negative examples ----------
def test_negative_gate():
    m = kb.negative_check("got HTTP 403 after changing the object id")
    check("negative_match_403", m is not None and
          m["classification"] == "expected_behavior", f"got {m}")
    check("negative_lesson_bola", m is not None and "BOLA" in m["lesson"])
    m2 = kb.negative_check("reflected input properly html-encoded, no execution")
    check("negative_match_xss_encoded", m2 is not None)
    m3 = kb.negative_check("200 with another user's private order data")
    check("negative_no_match_real_signal", m3 is None, f"got {m3}")
    m4 = kb.negative_check({"observation": "server header discloses nginx version",
                            "interpretation": "banner"})
    check("negative_dict_input", m4 is not None and
          m4["classification"] == "false_positive")


# ---------- 4. observation round-trip ----------
def test_observation():
    obs = observation.ExperimentObservation(
        hypothesis="object authorization depends on ownership",
        preconditions={"identity": "user_A", "object_owner": "user_B"},
        action={"type": "authorized_test", "target": "owned_test_environment"},
        observation={"status_changed": True, "response_changed": True,
                     "object_changed": False},
        interpretation="authorization behavior differs",
        confidence=0.71,
        next_question="Does the difference persist across another object?")
    d = obs.to_dict()
    check("obs_fields", all(k in d for k in (
        "experiment_id", "hypothesis", "preconditions", "action",
        "observation", "interpretation", "confidence", "next_question")))
    eid = observation.append_observation("__test_obs__", obs)
    recs = observation.read_observations("__test_obs__")
    check("obs_jsonl_roundtrip", len(recs) == 1 and recs[0]["experiment_id"] == eid)
    back = observation.ExperimentObservation.from_dict(recs[0])
    check("obs_from_dict", back.confidence == 0.71 and
          back.preconditions["identity"] == "user_A")
    # world model accepts the record
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import world_model
    wm = world_model.WorldModel("__test_obs__")
    wm.model = {k: ([] if isinstance(v, list) else {}) for k, v in wm.model.items()}
    res = wm.update_from_observation(d, source="test")
    check("world_accepts_record", isinstance(res, dict) and "relations" in res)
    check("world_identity_from_precondition", any(
        i["name"] == "user_A" for i in wm.model["identities"]))
    # cleanup
    import shutil
    for p in (os.path.join("state", "__test_obs__"),
              os.path.join("state", "__test_obs___world.json")):
        try:
            if os.path.isdir(p):
                shutil.rmtree(p)
            else:
                os.remove(p)
        except OSError:
            pass


# ---------- 5. frontend parsing ----------
SAMPLE_HTML = """
<html><head><script src="/static/js/main.abc.js"></script></head>
<body>
<nav><a href="/dashboard">dash</a></nav>
<script>
const API = "https://api.example.com";
fetch("/api/v2/orders/{id}?verbose=true").then(r=>r.json());
axios.post("/api/v2/orders", {item: 1});
const GQL = "/graphql";
</script>
<form action="/api/v2/checkout" method="POST">
<input name="coupon" /><input name="qty" /><input type="submit"/>
</form>
<script>query GetUser { user { email } } mutation PlaceOrder { placeOrder }</script>
<!-- swagger: "/openapi.json" -->
<div class="error">Error: unauthorized - token expired</div>
<a href="/login">login</a> <a href="/oauth/authorize">oauth</a>
<script>var r = { path: "/settings/profile", route: "/orders/:id" };</script>
</body></html>
"""


def test_frontend():
    p = frontend.parse_frontend(SAMPLE_HTML, source="test")
    check("fe_api_calls", "/api/v2/orders/{id}?verbose=true" in p["api_calls"] and
          "/graphql" in p["api_calls"], f"got {p['api_calls']}")
    check("fe_forms", len(p["forms"]) == 1 and
          p["forms"][0]["action"] == "/api/v2/checkout" and
          "coupon" in p["forms"][0]["inputs"])
    check("fe_gql_ops", "GetUser" in p["graphql_ops"] and
          "PlaceOrder" in p["graphql_ops"])
    check("fe_api_specs", "/openapi.json" in p["api_specs"])
    check("fe_auth_markers", "login" in p["auth_markers"] and
          "oauth" in p["auth_markers"], f"got {p['auth_markers']}")
    check("fe_params", "coupon" in p["parameters"] and
          "id" in p["parameters"] and "verbose" in p["parameters"],
          f"got {p['parameters']}")
    check("fe_routes", "/settings/profile" in p["routes"], f"got {p['routes']}")
    check("fe_errors", len(p["error_messages"]) > 0)
    # feed into target model
    t = target_model.Target("__test_fe__")
    t.data = {k: ([] if isinstance(v, list) else v) for k, v in t.data.items()}
    counts = frontend.feed_target_model(p, t)
    check("fe_feed_endpoints", counts["endpoints"] >= 3, f"got {counts}")
    check("fe_feed_specs", counts["api_specs"] == 1)
    check("fe_feed_routes", counts["frontend_routes"] >= 1)
    try:
        os.remove(t.path)
        os.rmdir(os.path.dirname(t.path))
    except OSError:
        pass


# ---------- 6. reasoning wiring ----------
def test_reasoning_wiring():
    import think
    import learn
    mem = {}
    seeds = think.scholar(
        [{"title": "/api/orders/{id}", "detail": "user_id order", "evidence": ""}],
        {"tech_terms": [], "vuln_classes": []}, {"rejected": [], "seen": []}, [])
    q_seeds = [s for s in seeds if "] Q:" in s["statement"]]
    f_seeds = [s for s in seeds if "] next:" in s["statement"]]
    check("scholar_uses_questions", len(q_seeds) > 0, f"total={len(seeds)}")
    check("scholar_uses_followups", len(f_seeds) > 0)
    # world_model.ingest builds the target model
    import world_model
    wm = world_model.WorldModel("__test_ingest__")
    wm.model = {k: ([] if isinstance(v, list) else {}) for k, v in wm.model.items()}
    wm.ingest([{"tool": "httpx", "title": "https://x.example.com",
                "detail": "/api/orders/{id} x200\nuser_id param", "evidence": ""}])
    tpath = os.path.join("state", "__test_ingest__", "target.json")
    check("ingest_builds_target", os.path.isfile(tpath))
    import shutil
    for p in (os.path.join("state", "__test_ingest__"),):
        try:
            shutil.rmtree(p)
        except OSError:
            pass
    try:
        os.remove(os.path.join("state", "__test_ingest___world.json"))
    except OSError:
        pass


def main():
    test_target_model()
    test_technique_loading()
    test_negative_gate()
    test_observation()
    test_frontend()
    test_reasoning_wiring()
    print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
    if FAIL:
        print("FAILURES:", FAIL)
        sys.exit(1)


if __name__ == "__main__":
    main()
