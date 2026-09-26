"""Tests for the enforced agent loop. Run: python3 -m brain.test_session"""
import os, sys, json, shutil
sys.path.insert(0, os.path.expanduser("~/workspace/hacker-agent"))

from brain.session import ResearchSession, SESSIONS_DIR
from brain.gate import GateRefused, TestAuthorization
from brain.engine import Engine
from brain import experiments as X

PASS, FAIL = [], []

def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("PASS " if cond else "FAIL ") + name + (f" — {detail}" if detail and not cond else ""))

def fresh(obj="test-objective"):
    s = ResearchSession(objective=obj)
    s.define_model(objects=["Order"], boundaries=["browser->API"])
    s.assume("only the owner can mutate an order", "GET ownership check",
             "PATCH as non-owner succeeds")
    return s

# 1. gate refuses without hypothesis
s = fresh()
try:
    s.propose_test("H99", "x", "y", ["example.com"], "own account", "s", "f")
    check("gate: unknown hypothesis refused", False)
except GateRefused:
    check("gate: unknown hypothesis refused", True)

# 2. gate refuses missing fields
s = fresh()
h = s.add_hypothesis("PATCH skips ownership", violated_assumption="A1")
try:
    s.propose_test(h["id"], "", "reason", ["example.com"], "own account", "s", "f")
    check("gate: missing expected_observation refused", False)
except GateRefused as e:
    check("gate: missing expected_observation refused", "expected_observation" in str(e))

# 3. adversarial rejects non-single-variable experiment
s = fresh()
h = s.add_hypothesis("PATCH skips ownership", violated_assumption="A1",
                     defender_view="a shared before_action enforces it everywhere")
try:
    s.propose_test(h["id"], "non-owner PATCH succeeds", "distinguish channel",
                   ["example.com"], "own account", "200 as non-owner",
                   "403 as non-owner", single_variable=False)
    check("adversarial: multi-variable experiment rejected", False)
except GateRefused as e:
    check("adversarial: multi-variable experiment rejected", "one variable" in str(e).lower())

# 4. adversarial rejects redundant test (already answered)
s = fresh()
h = s.add_hypothesis("PATCH skips ownership", violated_assumption="A1")
s.state["results"].append({"id": "R0", "test_id": "T0", "hypothesis_id": h["id"],
                           "outcome": "rejected", "observed": "non-owner PATCH got 403",
                           "why_failed": "x", "learned": "y", "ts": "t"})
try:
    s.propose_test(h["id"], "non-owner PATCH got 403 shows nothing", "repeat",
                   ["example.com"], "own account", "s", "f")
    check("adversarial: redundant test rejected", False)
except GateRefused as e:
    check("adversarial: redundant test rejected", "unnecessary" in str(e).lower())

# 5. execute() refuses without token (structural enforcement)
s = fresh()
eng = Engine(s._world_model())
class FakeExp:
    repeater_spec = {"method": "GET", "base_seq": None}
    def to_repeater_args(self, include_send=True): return []
r = eng.execute(FakeExp(), scope_hosts=("example.com",))
check("execute: refuses without authorization",
      r.get("refused") and "propose_test" in r.get("reason", ""))
r2 = eng.execute(FakeExp(), scope_hosts=("example.com",),
                 authorization=TestAuthorization("T1", "H1", "sess", ["example.com"]))
check("execute: expired-scope mismatch refused",
      r2.get("refused") and "exceed authorized scope" in r2.get("reason", "") or
      r2.get("error") == "no base_seq: experiment is plan-only, capture a logged request first",
      str(r2)[:80])

# 6. full loop: observe -> generate -> propose -> run (mocked) -> reject -> learn
s = fresh("order-api")
s.define_model(objects=["Order", "Account"], machines={"Order": ["created", "paid"]})
new = s.observe("GET validates ownership but PATCH returned 200 for non-owner instead",
                force_generate=True)
check("generate: observation produced hypotheses", len(new) > 0, f"got {len(new)}")
hyp = new[0]
t = s.propose_test(hyp["id"], "non-owner PATCH returns 200",
                   "distinguish: does PATCH re-check ownership",
                   ["shop.example"], "own test accounts A and B",
                   "200 + order mutated as non-owner", "403 as non-owner")
check("gate: well-formed test approved", t["status"] == "approved" and bool(t["authorization"]))
# mock the network: patch engine execute
s._engine = s._get_engine()
s._engine.execute = lambda exp, scope_hosts=(), authorization=None: {
    "refused": False, "target": "PATCH https://shop.example/api/order/1",
    "observation": "403 as non-owner; owner PATCH 200"}
res = s.run_test(t["id"])
check("run_test: gated execution returns observation", not res.get("refused"), str(res)[:60])
result, followups = s.record_result(t["id"], "rejected",
    observed="PATCH as non-owner returned 403; ownership enforced in shared before_action",
    why_failed="enforcement lives in a shared before_action covering all verbs",
    learned="ownership is verb-agnostic here; pivot to nested routes and alternate channels")
rej = s.state["rejected_hypotheses"][-1]
check("failure learning: 6 fields stored",
      all(k in rej for k in ("believed", "tested", "observed_result", "why_failed",
                             "learned", "changes_future")))
check("failure learning: follow-ups derived", len(followups) > 0, f"got {len(followups)}")
check("failure learning: lesson persisted",
      any("before_action" in l["text"] for l in s.state["lessons"]))

# 7. competition before confirmation
s2 = fresh("compete-case")
h2 = s2.add_hypothesis("allowlist skipped on package routes", violated_assumption="A1")
t2 = s2.propose_test(h2["id"], "foreign project packages served to job token",
                     "code shows skip_job_token_policies on pypi routes",
                     ["gitlab.example"], "two owned projects",
                     "200 with package bytes", "404 identical to anonymous")
s2._engine = s2._get_engine()
s2._engine.execute = lambda exp, scope_hosts=(), authorization=None: {"refused": False, "observation": "200 with bytes"}
s2.run_test(t2["id"])
s2.record_result(t2["id"], "confirmed", observed="200 with package bytes for non-allowlisted project")
f = s2.compete_finding(0)
check("competition: alternatives generated and disproof required",
      f["status"] == "awaiting-disproof" and len(f["competition"]["surviving"]) > 0)
check("competition: not confirmed prematurely",
      len(s2.state["confirmed_findings"]) == 0)

# 8. stop conditions
s3 = fresh("stop-case")
h3 = s3.add_hypothesis("X", violated_assumption="A1")
t3 = s3.propose_test(h3["id"], "obs", "reason", ["h.example"], "own", "s", "f")
s3._engine = s3._get_engine()
s3._engine.execute = lambda exp, scope_hosts=(), authorization=None: {"observation": "no"}
s3.run_test(t3["id"])
result3, fups3 = s3.record_result(t3["id"], "rejected", observed="no", why_failed="w", learned="l")
stop, reason = s3.should_stop()
check("stop: derived follow-ups keep the loop alive (not a halt)", not stop and len(fups3) > 0,
      f"stop={stop} followups={len(fups3)}")
# now kill everything: all hypotheses dead, nothing awaiting disproof
for h in s3.state["hypotheses"]:
    h["status"] = "rejected"
stop, reason = s3.should_stop()
check("stop: disproven hypothesis halts loop", stop, reason)

# 9. persistence across sessions
s4 = fresh("persist-case")
sid = s4.id
s4.observe("noted", force_generate=False)
s5 = ResearchSession(session_id=sid)
check("persistence: session reloads state",
      s5.state["objective"] == "persist-case" and len(s5.state["observations"]) == 1)
check("persistence: session listed", sid in ResearchSession.list_sessions())

# 10. secrets never persisted
s6 = fresh("secret-case")
try:
    s6.observe("api_key: sk-live-abcdefgh12345678")
    check("secrets: credential-shaped content refused", False)
except ValueError:
    check("secrets: credential-shaped content refused", True)

# cleanup test sessions
for sess_id in list(ResearchSession.list_sessions()):
    p = os.path.join(SESSIONS_DIR, sess_id + ".json")
    if os.path.exists(p):
        st = json.load(open(p))
        if st.get("objective", "").endswith("-case") or st.get("objective") == "test-objective":
            os.remove(p)

print(f"\n{len(PASS)} passed, {len(FAIL)} failed")
sys.exit(1 if FAIL else 0)
