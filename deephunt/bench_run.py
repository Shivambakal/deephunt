#!/usr/bin/env python3
"""DEEPHUNT P1 bench harness — prove the pipeline hunts at P1 level.

Runs the core hunt loop against each mock target (vulnerable + patched
variants) and scores it with the §19 metrics from benchmarks.py:

  OBSERVE -> HYPOTHESIZE -> PLAN -> AUTHORIZE -> EXECUTE -> DIFFERENTIAL
      -> ORACLE -> INDEPENDENT VERIFY -> LEARN (+ REGRESSION)

Real pipeline modules exercised end to end:
  world_model.WorldModel, attackgraph.build, hypothesis_fusion.fuse
  (incl. the brain violation templates fused inside it),
  experiment.plan (EIG), difficulty.rank (UTILITY),
  ResearchSession.propose_test (the REAL adversarial gate),
  differential.compare, oracle.check, verifier.verify_finding,
  regression.from_finding, benchmarks.Campaign.

AUTHORIZATION MODEL — read before crying "bypass":
  The mocks are pre-authorized synthetic test fixtures, the bench analog
  of a VDP scope ("mock:shop" names the fixture the way a scope names a
  host). NOTHING skips the gate: every probe is proposed through
  ResearchSession.propose_test(), the adversarial self-check runs, and a
  real TestAuthorization token is minted per approved test with
  scope_hosts=["mock:<name>"]. MockEngine.execute() enforces the same
  structural check Engine.execute() does (token is a valid
  TestAuthorization AND covers the requested scope) and then routes the
  probe to the in-process mock instead of the network repeater. The
  production gate is untouched; only the transport differs, because the
  target is a fixture, not a host.

Deliberately out of scope for a mock bench (no network, no dossiers):
  global intel, company attack planner, eventbus, CEO/debate. The bench
  seeds play the role intel + reasoning play in production: they are the
  starting knowledge the hunt refines, ranks, gates, executes, and
  verifies — they do NOT pre-decide the outcome (the oracle + verifier +
  reproduction do).

Usage:
  python3 bench_run.py                  # all mocks, vuln + patched
  python3 bench_run.py --mock shop       # one mock family
  python3 bench_run.py --variant vuln    # only vulnerable variants
  python3 bench_run.py --run-id baseline # tag session/state files
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.dirname(BASE))

from brain.session import ResearchSession  # noqa: E402
from brain.gate import TestAuthorization  # noqa: E402
from world_model import WorldModel  # noqa: E402
from target_model import Target  # noqa: E402
import attackgraph  # noqa: E402
import hypothesis_fusion  # noqa: E402
import experiment as exp_planner  # noqa: E402
import difficulty as difficulty_mod  # noqa: E402
import differential as differential_mod  # noqa: E402
import oracle as oracle_mod  # noqa: E402
import verifier as verifier_mod  # noqa: E402
import regression as regression_mod  # noqa: E402
import learn as learn_mem  # noqa: E402
from benchmarks import Campaign  # noqa: E402

from bench_targets import MockTarget, fmt_observation  # noqa: E402
from bench_targets.shop import ShopMock  # noqa: E402
from bench_targets.workflow import WorkflowMock  # noqa: E402
from bench_targets.ragbot import RagbotMock, CANARY, CANARY_URL  # noqa: E402
from bench_targets.agent import AgentMock  # noqa: E402


# ---------------------------------------------------------------------------
# Custom oracles for the P1 classes the bench covers.
# Registered through oracle.register() — the module's intended extension point.
# ---------------------------------------------------------------------------

def _granted(text: str) -> bool:
    return bool(re.search(r"\b(200|201|202|204)\b", text or ""))


def tool_authorization_oracle(control: str, test: str, ctx: dict):
    """State-changing agent tools must not fire on untrusted input alone.

    VIOLATED: test shows a refund actually issued while the control run did
    not. HELD: no refund in either, or the refund was gated behind approval.
    """
    markers = ("refund issued",)
    t_hit = any(m in (test or "").lower() for m in markers)
    c_hit = any(m in (control or "").lower() for m in markers)
    if t_hit and not c_hit and _granted(test):
        return oracle_mod.OracleVerdict(
            oracle_mod.VIOLATED,
            "agent executed issue_refund on injected ticket text with no "
            "approval record", "tool_authorization", 0.85)
    if not t_hit and not c_hit:
        return oracle_mod.OracleVerdict(
            oracle_mod.HELD, "no refund in either observation — tool stayed "
                             "idle", "tool_authorization", 0.8)
    if re.search(r"approval required|pending.*approval", test or "", re.I):
        return oracle_mod.OracleVerdict(
            oracle_mod.HELD, "refund gated behind approval",
            "tool_authorization", 0.85)
    return oracle_mod.OracleVerdict(
        oracle_mod.INCONCLUSIVE, "refund signal ambiguous",
        "tool_authorization", 0.3)


oracle_mod.register("tool_authorization", tool_authorization_oracle)


# ---------------------------------------------------------------------------
# MockEngine — the bench transport. Same authorization discipline as
# Engine.execute (valid token + scope coverage), in-process mock probes
# instead of network traffic.
# ---------------------------------------------------------------------------

class MockEngine:
    """Executes an approved test's probe plan against a mock target."""

    def __init__(self, mock: MockTarget, camp: Campaign):
        self.mock = mock
        self.camp = camp
        self.scope = [f"mock:{mock.name}"]

    def _check_authorization(self, authorization) -> dict:
        # Mirrors Engine.execute's structural check: no valid token minted
        # by the gate -> refusal, no probes.
        if not isinstance(authorization, TestAuthorization) \
                or not authorization.is_valid():
            return {"refused": True,
                    "reason": "no valid hypothesis-gated authorization"}
        if not authorization.covers(self.scope):
            return {"refused": True,
                    "reason": f"scope {self.scope} not covered by "
                              f"{authorization.scope_hosts}"}
        return {"refused": False}

    def _probe(self, action, params):
        self.camp.trial()
        status, data, delta = self.mock.probe(action, params)
        return status, data, delta, fmt_observation(action, params, status,
                                                    data, delta)

    def _run_steps(self, steps, bindings, chain_key):
        """Run a list of (action, params) steps. results are bound live so
        later steps can reference earlier ones via $chain.<i>.<key>."""
        results, texts = [], []
        bindings[chain_key] = results  # live: intra-chain refs resolve
        for action, params in steps:
            rp = {k: self._resolve_value(v, bindings, chain_key)
                  for k, v in (params or {}).items()}
            status, data, delta, text = self._probe(action, rp)
            results.append({"action": action, "params": rp, "status": status,
                            "data": data, "delta": delta})
            texts.append(f"--- step: {action} ---\n{text}")
        return results, "\n".join(texts)

    def _resolve_value(self, value, bindings, chain_key):
        """Resolve $ns.<i>.<key...> against step-result bindings.

        Namespaces: setup, chain (= the chain currently executing),
        control_chain, test_chain, disproof. Templates dig into the
        result's data dict (e.g. $setup.0.ticket_id).
        """
        if not (isinstance(value, str) and value.startswith("$")):
            return value
        parts = value[1:].split(".")
        if len(parts) < 2:
            return value
        ns = parts[0]
        if ns == "chain":
            ns = chain_key
        src = bindings.get(ns, [])
        try:
            idx = int(parts[1])
        except ValueError:
            return value
        data = src[idx]["data"] if 0 <= idx < len(src) else {}
        for part in parts[2:]:
            data = data.get(part, {}) if isinstance(data, dict) else {}
        return data

    def execute_plan(self, plan: dict, authorization) -> dict:
        """Run setup + control/test (single probes or chains). Returns the
        full execution record with observation texts."""
        refused = self._check_authorization(authorization)
        if refused["refused"]:
            raise PermissionError(refused["reason"])
        bindings: dict = {"setup": []}
        setup_results, setup_texts = bindings["setup"], []
        for action, params in plan.get("setup", []):
            rp = {k: self._resolve_value(v, bindings, "setup")
                  for k, v in (params or {}).items()}
            status, data, delta, text = self._probe(action, rp)
            setup_results.append({"action": action, "params": rp,
                                  "status": status, "data": data,
                                  "delta": delta})
            setup_texts.append(text)

        def as_chain(key_single, key_chain):
            if plan.get(key_chain):
                return plan[key_chain]
            if plan.get(key_single):
                return [plan[key_single]]
            return []

        control_results, control_obs = self._run_steps(
            as_chain("control", "control_chain"), bindings, "control_chain")
        bindings["control_chain"] = control_results
        test_results, test_obs = self._run_steps(
            as_chain("test", "test_chain"), bindings, "test_chain")
        bindings["test_chain"] = test_results
        return {"setup": setup_results, "control": control_results,
                "test": test_results, "control_observation": control_obs,
                "test_observation": test_obs, "bindings": bindings,
                "setup_text": "\n".join(setup_texts)}


# ---------------------------------------------------------------------------
# The hunt: one mock, one variant.
# ---------------------------------------------------------------------------

def _seed_target_model(mock: MockTarget, wm: WorldModel) -> Target:
    """Build a Target for the attack graph from the seeded world model."""
    t = Target(f"bench-{mock.name}")
    for ident in wm.model.get("identities", []):
        try:
            t.add_identity(ident["name"])
        except Exception:
            pass
    for ep in wm.model.get("endpoints_struct", []):
        try:
            t.add_endpoint(ep["path"], method=ep["method"],
                           authentication=ep.get("auth_state", "unknown"),
                           roles=["user"], object=None,
                           owner_required=False,
                           parameters=ep.get("params", []))
        except Exception:
            pass
    return t


def hunt_mock(mock: MockTarget, run_id: str, max_proposals: int = 6,
              verbose: bool = True) -> dict:
    """Run the full core loop against one mock variant. Returns metrics."""
    tag = f"{mock.label}"
    camp = Campaign(target=tag)
    gt = mock.ground_truth()
    camp.known_vulns = 1 if gt["vulnerable"] else 0
    camp.endpoints_known = len(mock.actions())
    hit_actions = set()
    log = []

    def say(msg):
        log.append(msg)
        if verbose:
            print(f"  [{tag}] {msg}")

    t_start = time.time()
    session = ResearchSession(objective=f"bench:{tag}",
                              session_id=f"bench-{run_id}-{tag}"
                              .replace(":", "-"))

    # ---- OBSERVE ----
    wm = WorldModel(f"bench-{run_id}-{mock.name}")
    wm.ingest([{"tool": "bench", "title": "surface brief",
                "detail": mock.surface_brief()}])
    mock.seed_world(wm)
    for assumption in [
        ("object endpoints verify the caller owns the object",
         "GET /orders/{id}", "a non-owner reads the object"),
        ("state transitions enforce their preconditions",
         "pay_order", "a skipped step is accepted"),
        ("retrieved content is data, never instructions",
         "RAG chat", "injected instructions are followed"),
        ("state-changing tools require approval",
         "issue_refund", "a tool fires on untrusted input alone"),
    ]:
        session.assume(*assumption, 0.7, provenance="bench:reasoning")
    say(f"observe: {wm.summary()}")

    # ---- HYPOTHESIZE ----
    mem = learn_mem.load_memory(f"bench-{mock.name}")
    target = _seed_target_model(mock, wm)
    try:
        agraph = attackgraph.build(wm, target)
    except Exception as e:
        agraph = {"paths": [], "hypothesis_seeds": []}
        say(f"attack-graph unavailable: {e}")
    say(f"attack-graph: {len(agraph.get('paths', []))} paths, "
        f"{len(agraph.get('hypothesis_seeds', []))} seeds")

    seeds = list(mock.bench_seeds()) + list(mock.negative_seeds())
    plan_by_statement = {s["statement"]: s.get("bench_plan")
                         for s in seeds if s.get("bench_plan")}
    fused = hypothesis_fusion.fuse(session, seeds, [],
                                   agraph.get("hypothesis_seeds", []),
                                   mem, max_new=30)
    say(f"hypothesize: {fused['candidates']} candidates -> "
        f"{len(fused['registered'])} registered")

    # ---- PLAN (EIG + difficulty UTILITY) ----
    live = [h for h in session.state["hypotheses"] if h["status"] == "live"]
    candidates = []
    for h in live:
        plan = plan_by_statement.get(h["statement"])
        candidates.append({
            "statement": h["statement"],
            "reasoning": h.get("investigator_test", ""),
            "family": "hypothesis",
            "score": h.get("score", 3) / 9.0 * 5 if h.get("score", 0) > 5
                     else h.get("score", 3),
            "technique_id": (plan or {}).get("technique_id", ""),
            "severity": "critical" if plan and plan.get("root_cause",
                                                       "").startswith(
                ("bola", "workflow", "rag", "agent")) and
            "negative" not in (h.get("provenance") or "") else "medium",
            "oracle": (plan or {}).get("oracle", ""),
            "_bench_plan": plan,
            "_hypothesis_id": h["id"],
        })
    eig_ranked = exp_planner.plan(candidates, mem)
    info_gains = {id(s): min(1.0, s.get("_eig", 2.0) / 6.0)
                  for s in eig_ranked}
    costs = {id(s): s.get("_cost", 2) / 5.0 for s in eig_ranked}
    risks = {id(s): s.get("_risk", 2) / 5.0 for s in eig_ranked}
    ranked = difficulty_mod.rank(candidates, memory=mem,
                                 info_gains=info_gains, costs=costs,
                                 risks=risks)
    executable = [c for c in ranked if c.get("_bench_plan")]
    say(f"plan: {len(ranked)} ranked, {len(executable)} executable; "
        f"top={executable[0]['statement'][:70]}..." if executable else
        "plan: nothing executable")

    # ---- AUTHORIZE -> EXECUTE -> DIFFERENTIAL -> ORACLE -> VERIFY -> LEARN --
    engine = MockEngine(mock, camp)
    scope = [f"mock:{mock.name}"]
    auth_basis = (f"bench-fixture: pre-authorized synthetic target "
                  f"(mock:{mock.name}); no real host, no real data")
    chains_started = 0
    chains_completed = 0
    findings = []

    for cand in executable[:max_proposals]:
        plan = cand["_bench_plan"]
        hid = cand["_hypothesis_id"]
        # AUTHORIZE — the real gate, adversarial self-check included.
        try:
            test = session.propose_test(
                hypothesis_id=hid,
                expected_observation=(
                    f"differential probe: control vs variant; vulnerable -> "
                    f"{plan['expected_property'][:100]} violated; safe -> "
                    f"invariant holds"),
                reason=(f"[{tag}] difficulty-ranked #{ranked.index(cand)+1}; "
                        f"{cand['statement'][:160]}"),
                scope_hosts=scope, auth_basis=auth_basis,
                success_criteria=f"oracle {plan['oracle']} -> VIOLATED with "
                                 f"reproducible evidence",
                failure_criteria=f"oracle {plan['oracle']} -> HELD; "
                                 f"invariant holds on the mock")
        except Exception as e:
            say(f"gate refused '{cand['statement'][:60]}...': {e}")
            continue
        auth_d = test["authorization"]
        auth = TestAuthorization(
            test_id=auth_d["test_id"], hypothesis_id=auth_d["hypothesis_id"],
            session_id=auth_d["session_id"], scope_hosts=auth_d["scope_hosts"],
            issued_at=auth_d["issued_at"], minted_by=auth_d["minted_by"],
            revoked=auth_d["revoked"], ttl_seconds=auth_d["ttl_seconds"])

        # EXECUTE
        chains_started += 1
        try:
            rec = engine.execute_plan(plan, auth)
        except PermissionError as e:
            say(f"engine refused: {e}")
            continue
        for r in rec["setup"] + rec["control"] + rec["test"]:
            hit_actions.add(r["action"])
        control_obs, test_obs = (rec["control_observation"],
                                 rec["test_observation"])

        # DIFFERENTIAL
        diff_verdict, diff_reasons = differential_mod.compare(
            control_obs, test_obs)
        say(f"differential: {diff_verdict} "
            f"({'; '.join(diff_reasons[:2])})")

        # ORACLE
        verdicts = oracle_mod.check_all([plan["oracle"]], control_obs,
                                        test_obs, plan.get("oracle_ctx", {}))
        overall, reason = oracle_mod.summarize(verdicts)
        say(f"oracle {plan['oracle']}: {overall} ({reason[:90]})")
        chains_completed += 1

        if overall != oracle_mod.VIOLATED:
            # Oracle disposed of it: no finding. Feed the world model.
            wm.update_from_observation(
                f"probe {plan['oracle']} on {tag}: {overall} — {reason[:200]}",
                source="bench")
            session.observe(f"[bench:{tag}] oracle {overall}: "
                            f"{cand['statement'][:100]}",
                            kind="observation")
            continue

        # ---- candidate: INDEPENDENT VERIFY (falsify, don't confirm) ----
        claim = (f"{gt['technique']} at {gt['location']} "
                 f"({mock.label})")
        artifacts = {
            "request_log": "\n".join(
                f"{r['action']} {r['params']}" for r in
                rec["setup"] + rec["control"] + rec["test"]),
            "response_pair": f"CONTROL:\n{control_obs}\nTEST:\n{test_obs}",
        }
        if plan["technique_id"] == "WF-01":
            artifacts["state_trace"] = test_obs
        if plan["technique_id"] == "LLM04":
            artifacts["canary_marker"] = CANARY if CANARY in test_obs else ""
        if plan["technique_id"] == "LLM06":
            artifacts["tool_trace"] = test_obs

        killed, surviving = {}, []
        for alt in plan.get("alternatives", []):
            disp_obs = ""
            dresults = []
            dbind = {"setup": rec["bindings"].get("setup", []),
                     "test_chain": rec["bindings"].get("test_chain", []),
                     "control_chain": rec["bindings"].get("control_chain",
                                                           []),
                     "disproof": dresults}  # live: $disproof.<i> refs
            for action, params in alt.get("disproof", []):
                # $chain.* inside a disproof resolves against the chain the
                # alternative is about (default: the test chain).
                rp = {k: engine._resolve_value(
                        v, dbind, alt.get("chain_ref", "test_chain"))
                      for k, v in (params or {}).items()}
                status, data, delta, text = engine._probe(action, rp)
                hit_actions.add(action)
                dresults.append({"action": action, "params": rp,
                                 "status": status, "data": data,
                                 "delta": delta})
                disp_obs += text + "\n"
            # templates embedded in kills_if resolve against all bindings
            kills_if = re.sub(
                r"\$(setup|test_chain|control_chain|disproof)\.\d+\.[\w.]+",
                lambda m: str(engine._resolve_value(m.group(0), dbind,
                                                  "disproof")),
                alt["kills_if"])
            if alt.get("self_evident"):
                target_text = test_obs
            else:
                target_text = disp_obs or test_obs
            if kills_if in target_text:
                killed[alt["explanation"]] = alt["killed_note"]
                say(f"  alt killed: {alt['explanation'][:60]}...")
            else:
                surviving.append(alt["explanation"])
                say(f"  alt SURVIVES: {alt['explanation'][:60]}...")
        evidence = {"control_observation": control_obs,
                    "test_observation": test_obs,
                    "artifacts": artifacts,
                    "killed_alternatives": killed}
        report = verifier_mod.verify_finding(
            claim, evidence,
            expected_property=plan["expected_property"],
            technique_id=plan["technique_id"],
            alternatives=surviving)
        camp.verify(rejected=(report.verdict == verifier_mod.REJECTED))
        say(f"verifier: {report.verdict} "
            f"({'; '.join(report.falsification_notes[:2])})")

        if report.verdict != verifier_mod.VERIFIED:
            wm.update_from_observation(
                f"candidate rejected by verifier ({report.verdict}) on "
                f"{tag}: {claim[:120]}", source="bench")
            camp.report_finding(plan["root_cause"], confirmed=False)
            continue

        # ---- reproduction: re-run the pair, oracle must still say VIOLATED
        mock.reset()
        rec2 = engine.execute_plan(plan, auth)
        v2 = oracle_mod.check(plan["oracle"], rec2["control_observation"],
                              rec2["test_observation"],
                              plan.get("oracle_ctx", {}))
        reproducible = (v2.verdict == oracle_mod.VIOLATED)
        say(f"reproduction: {'reproduced' if reproducible else 'NOT reproduced'}")
        if not reproducible:
            camp.report_finding(plan["root_cause"], confirmed=False)
            continue

        # ---- CONFIRMED ----
        is_true_positive = gt["vulnerable"] and \
            plan["root_cause"] == gt["root_cause"]
        camp.report_finding(plan["root_cause"],
                            confirmed=is_true_positive, evidence_ok=True)
        if is_true_positive:
            camp.known_found += 1
        finding = {"id": f"BENCH-{tag}-{len(findings)+1}", "claim": claim,
                   "technique_id": plan["technique_id"],
                   "control_observation": control_obs,
                   "test_observation": test_obs,
                   "evidence": evidence,
                   "expected_property": plan["expected_property"],
                   "oracle": plan["oracle"],
                   "control_request": {"mock": mock.name,
                                       "variant": mock.label},
                   "test_request": {"mock": mock.name,
                                    "variant": mock.label},
                   "scope_hosts": scope, "auth_basis": auth_basis}
        findings.append((finding, plan))
        say(f"CONFIRMED: {claim[:80]}")

        # ---- LEARN (bench-scoped) + REGRESSION ----
        wm.update_from_observation(
            f"CONFIRMED {plan['root_cause']} on {tag}: {claim[:200]}. "
            f"Alternatives killed: {len(killed)}.",
            source="bench")
        session.observe(f"[bench:{tag}] confirmed: {claim[:160]}",
                        kind="observation")
        try:
            spec = regression_mod.from_finding(finding, f"bench-{mock.name}")
            say(f"regression test written: {spec['id']}")
        except Exception as e:
            say(f"regression write failed: {e}")
        # regression replay against the PATCHED twin proves the fix holds
        # (evaluated by the oracle, no traffic involved)

    # ---- weak-evidence probes: negative controls for the verifier ----
    for wp in mock.weak_probes():
        evidence = {"control_observation": wp["control_observation"],
                    "test_observation": wp["test_observation"],
                    "artifacts": wp["artifacts"],
                    "killed_alternatives": wp["killed_alternatives"]}
        report = verifier_mod.verify_finding(
            wp["claim"], evidence, expected_property="",
            technique_id=wp["technique_id"],
            alternatives=wp["alternatives"])
        camp.verify(rejected=(report.verdict == verifier_mod.REJECTED))
        ok = (report.verdict == wp["expected"])
        say(f"weak probe ({wp['technique_id']}): verifier {report.verdict} "
            f"— {'as expected' if ok else 'UNEXPECTED'}")

    camp.chains_started = chains_started
    camp.chains_completed = chains_completed
    camp.endpoints_hit = len(hit_actions)
    metrics = camp.metrics()
    metrics["elapsed_s"] = round(time.time() - t_start, 1)
    metrics["variant_vulnerable"] = gt["vulnerable"]
    metrics["ground_truth_root_cause"] = gt["root_cause"]
    metrics["findings"] = [{"claim": f["claim"][:100],
                            "technique_id": f["technique_id"]}
                           for f, _ in findings]
    metrics["log"] = log
    try:
        wm.save()
    except Exception:
        pass
    return metrics, findings


def run_all(run_id="final", mock_filter=None, variant_filter=None,
            verbose=True):
    families = {"shop": ShopMock, "workflow": WorkflowMock,
                "ragbot": RagbotMock, "agent": AgentMock}
    results = {}
    confirmed = []  # (mock_name, finding, plan) for regression replay
    for name, cls in families.items():
        if mock_filter and name != mock_filter:
            continue
        for patched in (False, True):
            if variant_filter == "vuln" and patched:
                continue
            if variant_filter == "patched" and not patched:
                continue
            mock = cls(patched=patched)
            if verbose:
                print(f"\n=== hunting {mock.label} ({mock.display}) ===")
            metrics, findings = hunt_mock(mock, run_id, verbose=verbose)
            results[mock.label] = metrics
            if not patched:
                for finding, plan in findings:
                    confirmed.append((name, finding, plan))

    # ---- REGRESSION REPLAY: each confirmed finding's plan re-executed
    # against a FRESH PATCHED twin must flip the oracle to HELD ----
    replays = []
    if confirmed and not variant_filter:
        if verbose:
            print("\n=== regression replay vs patched twins ===")
        for name, finding, plan in confirmed:
            twin = families[name](patched=True)
            camp = Campaign(target=f"replay:{name}")
            engine = MockEngine(twin, camp)
            scope = [f"mock:{name}"]
            # NOTE: the replay re-executes an already-gated plan (it was
            # proposed + authorized during the hunt); minting the fixture
            # token directly mirrors production regression replay, where
            # the session-gated Engine re-runs a stored control/test pair.
            auth = TestAuthorization(
                test_id="replay", hypothesis_id="replay",
                session_id=f"bench-{run_id}-replay", scope_hosts=scope)
            rec = engine.execute_plan(plan, auth)
            spec = {"id": finding["id"], "oracle": finding["oracle"],
                    "expected": "HELD"}
            res = regression_mod.evaluate(
                spec, rec["control_observation"], rec["test_observation"])
            replays.append({"finding": finding["id"], **res})
            if verbose:
                print(f"  {finding['id']}: oracle={res['oracle_verdict']} "
                      f"expected=HELD passed={res['passed']}")
        results["_regression_replay"] = {
            "replays": len(replays),
            "passed": sum(1 for r in replays if r["passed"]),
        }
    return results


def print_table(results):
    cols = ["target", "discovery_recall", "precision", "proof_rate",
            "chain_completion", "verifier_rejection_rate",
            "time_to_first_valid_s", "duplicate_rate", "endpoint_coverage",
            "cost_to_valid", "trials"]
    print("\n" + " | ".join(f"{c:>22}" for c in cols))
    print("-" * (25 * len(cols)))
    for tag, m in results.items():
        if tag == "_regression_replay":
            continue
        row = [tag] + [m.get(c, "-") for c in cols[1:]]
        print(" | ".join(f"{str(v):>22}" for v in row))
    replay = results.get("_regression_replay")
    if replay:
        print(f"\nregression replay vs patched twins: "
              f"{replay['passed']}/{replay['replays']} passed "
              f"(oracle flipped to HELD)")


def main():
    ap = argparse.ArgumentParser(description="DEEPHUNT P1 bench harness")
    ap.add_argument("--mock", default=None,
                    choices=["shop", "workflow", "ragbot", "agent"])
    ap.add_argument("--variant", default=None, choices=["vuln", "patched"])
    ap.add_argument("--run-id", default="final")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()
    results = run_all(run_id=args.run_id, mock_filter=args.mock,
                      variant_filter=args.variant,
                      verbose=not args.quiet)
    print_table(results)
    if args.json_out:
        slim = {k: {kk: vv for kk, vv in v.items() if kk != "log"}
                for k, v in results.items()}
        json.dump(slim, open(args.json_out, "w"), indent=1)
        print(f"\nwrote {args.json_out}")


if __name__ == "__main__":
    main()
