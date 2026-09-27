# DEEPHUNT P1 Bench — iteration log

Goal: prove the hunt pipeline operates at P1 level on mock targets —
4 vulnerable mocks (BOLA, workflow bypass, RAG indirect-injection exfil,
agent tool hijack) must each yield a confirmed, reproduced finding;
4 patched twins must yield zero findings; the verifier must demonstrably
reject (rejection rate > 0).

Real pipeline stages under test: `world_model`, `attackgraph`,
`hypothesis_fusion` (+ brain violation templates), `experiment` (EIG),
`difficulty` (UTILITY rank), `ResearchSession.propose_test` (the real
adversarial gate — every probe authorized through it), `differential`,
`oracle`, `verifier`, `regression`, `benchmarks.Campaign` (§19 metrics).

Run: `python3 bench_run.py [--mock shop|workflow|ragbot|agent]
[--variant vuln|patched]`. Tests: `python3 test_bench.py` (41 checks).

## Baseline (run-id `baseline`)

| target | recall | precision | proof | chain | verifier_rej |
|---|---|---|---|---|---|
| shop:vuln | 1.0 | 1.0 | 1.0 | 1.0 | 0.5 |
| shop:patched | 0.0 | — (no reports) | — | 1.0 | 1.0 |
| workflow:vuln | **0.0** | — | — | 1.0 | 0.5 |
| workflow:patched | 0.0 | — | — | 1.0 | 0.5 |
| ragbot:vuln | 1.0 | 1.0 | 1.0 | 1.0 | 0.5 |
| ragbot:patched | 0.0 | — | — | 1.0 | 1.0 |
| agent:vuln | **0.0** | — | — | 1.0 | 1.0 |
| agent:patched | 0.0 | — | — | 1.0 | 1.0 |

Two misses. Diagnoses below — both were harness bugs, and the pipeline's
own safeguards caught one of them before I did.

## Iteration 1 — template resolution (harness bug)

**Symptom:** `agent:vuln` differential reported "identical after noise
stripping"; oracle HELD.

**Root cause:** `$setup.<i>.<key>` templates resolved against the probe
*result envelope* instead of its `data` dict, so `$setup.0.ticket_id`
resolved to `{}`. Both control and test ran `run_agent({})` → 404 →
identical observations. (Same latent bug existed for `$chain.*`, which
additionally resolved against a binding populated only *after* the chain
finished.)

**Fix:** `bench_run.py` — unified `_resolve_value()` digging into
`results[i]["data"]`; chain results bound *live* so later steps can
reference earlier ones; `$chain` inside disproofs resolves against the
chain the alternative is about (`chain_ref`, default `test_chain`);
`$disproof.<i>` namespace for sequential disproof probes.

**Result:** `agent:vuln` → recall 1.0, precision 1.0, proof 1.0.

## Iteration 2 — poisoned control caught by the verifier (harness bug, pipeline win)

**Symptom:** `workflow:vuln` oracle said VIOLATED and both alternatives
were killed, yet the verifier returned NEEDS_MORE: "control shows an
error status — precondition suspect".

**Root cause:** same template bug as iteration 1, but in the *control*
chain: `$chain.0.order_id` resolved to `{}` mid-chain, so approve/pay/
fulfill all returned 404. The oracle still said VIOLATED (the 201 from
`create` made `_granted` true — see iteration 3). The verifier's
precondition audit correctly refused to bless a comparison built on a
poisoned control. The safeguard worked as designed.

**Fix:** same `_resolve_value`/live-binding fix as iteration 1.

**Result:** `workflow:vuln` → oracle VIOLATED on a *valid* control,
alternatives killed, verifier VERIFIED, reproduction confirmed.

## Iteration 3 — FALSE POSITIVE on the patched twin (real oracle bug)

**Symptom:** after iterations 1–2, `workflow:patched` *confirmed a
finding* (precision 0.0 = 1 false report / 0 confirmed — I initially
misread it as "no findings").

**Root cause (two parts):**
1. `oracle.state_transition_oracle` matched *any* 2xx in the whole
   observation text. On the multi-step transcript, the `create` step's
   `HTTP 201` made `_granted(test)` true even though the `pay` step was
   rejected with 400 → false VIOLATED. Additionally, the "rejection
   notice" carve-out required `len(test) < 300`, which never holds for
   chained transcripts.
2. Neither alternative discriminated "the pay step was actually
   rejected": both were killable on the patched mock too, so the
   verifier could not save it.

**Fixes:**
- `oracle.py`: `state_transition_oracle` now judges the *last step* of a
  step-separated transcript (`_final_step()`); single-step observations
  are evaluated exactly as before. `denied`/`_denied()` now recognizes
  HTTP 400 and "invalid transition"/"bad request" as rejections — a 400
  rejection is a genuine denial for transition oracles.
- `bench_targets/workflow.py`: added a discriminating alternative
  ("the pay step was actually rejected") whose `kills_if` (`"to": "PAID"`
  in the pay step's state delta) holds on the vuln mock and fails on the
  patched one — defense in depth even if the oracle regresses.

**Result:** `workflow:patched` oracle → HELD ("invalid transition
denied"), zero candidates, zero findings. `workflow:vuln` still
VIOLATED → confirmed. Verified no behavior change for single-step
observations (`test_bench.py::test_oracle_step_awareness`,
`test_denied_recognizes_400`).

## Final (run-id `final`)

| target | recall | precision | proof_rate | chain_completion | verifier_rej | t_first_valid | dup | coverage | cost_to_valid |
|---|---|---|---|---|---|---|---|---|---|
| shop:vuln | 1.0 | 1.0 | 1.0 | 1.0 | 0.5 | 0.1s | 0.0 | 0.75 | 9.0 |
| shop:patched | — (0 reports) | — | — | 1.0 | 1.0 | — | 0.0 | 0.25 | 4.0 |
| workflow:vuln | 1.0 | 1.0 | 1.0 | 1.0 | 0.5 | 0.2s | 0.0 | 1.0 | 19.0 |
| workflow:patched | — (0 reports) | — | — | 1.0 | 1.0 | — | 0.0 | 0.67 | 10.0 |
| ragbot:vuln | 1.0 | 1.0 | 1.0 | 1.0 | 0.5 | 0.2s | 0.0 | 0.75 | 9.0 |
| ragbot:patched | — (0 reports) | — | — | 1.0 | 1.0 | — | 0.0 | 0.5 | 5.0 |
| agent:vuln | 1.0 | 1.0 | 1.0 | 1.0 | 0.5 | 0.1s | 0.0 | 0.75 | 14.0 |
| agent:patched | — (0 reports) | — | — | 1.0 | 1.0 | — | 0.0 | 0.75 | 7.0 |

Regression replay vs patched twins: **4/4 passed** (every confirmed
finding's plan re-executed against a fresh patched twin flips the oracle
to HELD — the regression tests discriminate the fix).

Test suites: `test_bench.py` 41/41 · `test_datapipeline` 108/108 ·
`test_pipeline` 31/31 · `test_research_loop` 61/61 · ai_attacks a/b/c/wire
OK · web_attacks 9 suites OK · `test_technique_forge` OK ·
`test_apiprobe`/`test_apiseq`/`test_ceo`/`test_error_intel`/`test_eventbus`/
`test_evidence` all pass.

## Verdict

**The pipeline clears the P1 bar on the mocks.** All four planted P1s are
found through the full loop (hypothesize → difficulty-rank → adversarial
gate → authorized execution → differential → oracle → independent
falsifying verifier → reproduction → regression test), with zero false
positives on the patched twins and a verifier that demonstrably rejects
(0.5–1.0 rejection rate, including deliberate weak-evidence probes).

## Honest gap list — what the mocks don't prove about REAL targets

1. **Discovery from zero knowledge.** The bench seeds hand the hunt its
   starting hypotheses (the analog of intel + reasoning). Against a real
   target, the pipeline must *generate* the right hypothesis from passive
   observations — the hardest step — and the bench does not measure that.
   Brain templates + attack-graph seeds fired (2 paths on shop, 0 on the
   others) but were planning noise here, not the discoverers.
2. **Oracle generality.** The oracles are regexes over status codes and
   markers. Real apps return 200-with-error-JSON, localized messages, or
   silent failures; the 400-recognition and last-step fixes help but the
   oracle layer remains the most brittle part of the loop.
3. **Verifier alternative generation.** The alternatives here are
   hand-authored per mock with bespoke disproof probes. In production,
   `compete_finding` must *invent* the alternatives and their disproofs —
   untested by this bench.
4. **Statefulness and time.** Mocks are deterministic and instant. Real
   targets have caching, eventual consistency, rate limits, WAFs, and
   session expiry — all of which poison differentials and controls in
   ways the mocks never simulate.
5. **The attack graph was a passenger.** It produced paths only for shop
   (2) and contributed no executable hypothesis anywhere. Its coverage of
   workflow/AI/agent surfaces is a real gap for chain discovery.
6. **Authorization scope is asserted, not enforced.** The bench trusts
   `scope_hosts=["mock:<name>"]`; against real targets the scope→host
   binding is the actual safety boundary and was not exercised here.
7. **Cost is trivial.** 9–19 in-process probes per finding. Real hunts
   cost orders of magnitude more in time, traffic, and CAPTCHA/waf
   friction — `cost_to_valid` here is a floor, not a forecast.
