# DEEPHUNT ATTACKSURFACE — Architecture (as implemented, 2026-09-27)

Target-agnostic vulnerability-hunting pipeline. Entry point:
`deephunt/attacksurface.py`. One complete pass:

```bash
cd ~/workspace/hacker-agent/deephunt
python3 attacksurface.py --target <name> --passes 1 --max-hypotheses 6 --max-tests 3
```

The engine is a closed research loop, not a scanner orchestrator:

```
ATTACKSURFACE -> intelligence -> event bus -> persistent world model ->
attack graph -> hypotheses -> difficulty-aware planning -> authorization
gate -> execution -> differential -> oracle -> independent verification ->
finding/reject -> causal learning -> regression -> new hypotheses
```

Daemon integration: `python3 deephunt.py --daemon --target a,b --pipeline`
(routes each rotation slot through the pipeline instead of the classic
orchestrator loop; dry-skip/rotation behavior unchanged).

## Stages (implemented)

| # | Stage | Module | What it does |
|---|-------|--------|--------------|
| 1 | INTAKE | `attacksurface.py` | loads `targets/<name>.yaml` (+ optional `--dossier` JSON), opens `ResearchSession`, stages gated on profile |
| 2 | GLOBAL INTELLIGENCE | `intel/global_intel.py` | unified store `intel/global_intel.json`: CISA KEV (1,726), bounded recent NVD, OSV on-demand, news signals from `news_watcher` signals.jsonl, curated CWE→technique-class map. Query: `what_is_known(<technology>)` |
| 3 | TARGET INTELLIGENCE | `intel/target_intel.py` | normalizes target YAML + Company Hunter dossiers + apiprobe output + semantic target model + observations → `state/<target>/target_intel.json`; tech queries, scope checks, snapshot diffs (suspicious-change trigger) |
| 4 | DEEPHUNT REASONING | `reasoning.py` | intel → explicit assumptions (with provenance), hypothesis seeds, open questions; uses inference engine + KEV/CVE + news |
| 5 | INTEL COMPILE | `intel_compiler.py` | relevant intel only → target-specific hypotheses with preconditions + oracle hints. KEV becomes preconditions, never CVE dumps |
| 6 | WORLD MODEL | `world_model.py` | dynamic beliefs, invariants (structured, with invariant_ids the oracle keys off), contradictions, endpoints, identities, object lifecycles, trust boundaries |
| 7 | ATTACK / TRUST GRAPH | `attackgraph.py` | attack graph = reachability (low-priv → endpoint → object); trust graph = claimed enforcement + belief confidence. Built together, separate views |
| 8 | HYPOTHESIS ENGINE | `hypothesis_fusion.py` | fuses brain-generated + Company Hunter plan + reasoning seeds + intel-compiled + attack-graph path seeds; dedupes; checks rejection memory; registers survivors via `session.add_hypothesis()` with provenance |
| 9 | DIFFICULTY-AWARE PLANNING | `difficulty.py` + `stage_plan` | UTILITY = α·info_gain + β·impact + γ·novelty + δ·historical_success − λ·cost − μ·risk − ν·redundancy − ρ·difficulty. EIG from `experiment.py` feeds the info-gain term. Identity-matrix cells turn authz hypotheses into control/test differential pairs |
| 10 | AUTHORIZED TESTING | `brain/engine.py` (existing) + `stage_authorized_testing` | **propose-only by default**; executes only with `--execute` AND `profile.active_allowed` AND session `TestAuthorization`. Auto-runs record `inconclusive`+evidence — never auto-confirm |
| 11 | DIFFERENTIAL | `differential.py` | tri-state compare (identical / differs / interesting); 11 structured dimensions: identity, role, tenant, state, method, version, client, before/after, object, request-mutation, auth-vs-anon; `make_pair()` builds single-variable control/test specs |
| 12 | ORACLE | `oracle.py` | deterministic verdicts VIOLATED / HELD / INCONCLUSIVE keyed to world-model invariant_ids: ownership, auth_boundary, state_transition, no_leak, tenant_isolation. The oracle decides; the LLM never does |
| 13 | INDEPENDENT VERIFICATION | `verifier.py` + `stage_independent_verify` | structurally separate from discovery; runs AFTER `compete_finding()`: evidence-contract check → control-precondition audit → swapped differential re-analysis → surviving-alternative check. VERIFIED only when every falsification path fails |
| 14 | OBSERVATION | session + `object_pool.py` | observations → world-model beliefs; observed IDs/tokens/cursors → persistent per-target object pool (kind/owner/state/lifecycle; credential-shaped values suppressed, never persisted). `apiseq.ObjectPool` subclasses it for producer→consumer dependency resolution |
| 15 | LEARN + UPDATE ↺ | `learn_updates.py` + `learning.py` | confirmed → world-model belief update + **pending-review** technique-card proposal; rejected → deduplicated negative examples; inconclusive → lessons. Causal store records every trial (outcome, failure taxonomy, evidence predictiveness, wrong patterns, per-technique/per-technology rates) → feeds difficulty's historical-success term |
| 16 | REGRESSION | `regression.py` | every CONFIRMED finding becomes a permanent control/test replay spec under `deephunt/regressions/<target>/`; dry-run by default; live replay needs an externally supplied executor |
| 17 | REPORT | `report.py` | evidence-backed finding reports: control/test, oracle verdicts, verifier result, assumptions, scope, authorization basis, confidence, regression ID; credential-shaped content redacted |
| ↺ | LOOP-BACK | `attacksurface` | suspicious target-intel diffs re-trigger reasoning/planning |
| — | IDENTITY MATRIX | `identity_matrix.py` | Role × Object × Action × State enumeration → ranked authorization cells → differential pair specs |
| — | SEMANTIC (white-box) | `semantic.py` | repo → architecture map → AST/regex endpoint + source/sink extraction → intra-procedural taint → hypotheses with preconditions + oracle hints; semgrep seed rules when the binary exists, built-in fallback otherwise |
| — | SEMANTIC FUZZING | `fuzz.py` | deterministic feedback-guided mutation (seeded RNG; optional LLM proposal hook); scores response/state/oracle/differential/chain novelty; delta-minimization; never transmits — executor supplied externally |
| — | BENCHMARKS | `benchmarks.py` | synthetic harness: discovery recall, precision, proof rate, chain completion, verifier rejection rate, time-to-first-valid, duplicate rate, endpoint coverage, cost-to-valid; deterministic MockTarget with planted IDOR/auth-bypass/SQLi |

## Technique-card schema (v2, §26)

All 143 cards upgraded additively (`knowledge/migrate_cards_v2.py`):
`preconditions, required_state, hypothesis_generator, request_strategy,
mutation_strategy, expected_signal, positive_oracle, negative_evidence,
false_positive_rules, followup_experiment, regression_test,
difficulty_estimate`. `kb.py` normalizes with defaults so old/hand-added
cards stay valid. Domain files in `knowledge/techniques/*.yaml` are the
source of truth; `knowledge/techniques.yaml` is regenerated from them.

## Audit log (decision)

No new audit module was built: the enforced root execution engine already
provides an append-only immutable ledger — `brain/ledger.py` (`Ledger`)
writes every tested hypothesis (experiment, result, observation, why_failed)
to `data/brain/ledger.jsonl`, append-only, and derives follow-ups from
failures. Building a second ledger would duplicate the source of truth.

## Deviations from the blueprint (deliberate; documented)

1. **Reasoning runs before AND after the world model.** The blueprint shows
   reasoning → world model as a straight line. Initial intel seeds
   assumptions before any model exists; later observations update the model
   and cause re-planning. Reason: cold-start targets have no model yet.
2. **Attack graph and trust graph are separate views, built together.**
   Blueprint shows one box. Attack graph = reachability; trust graph = claimed
   enforcement + belief confidence. Reason: they answer different questions
   (what's reachable vs. what's claimed to be enforced).
3. **Technique updates are proposals, not corpus edits.** Blueprint's
   "LEARN + UPDATE" could read as automatic. Confirmed results write
   `pending_review/TECHNIQUE_PROPOSAL-*.md` + negative examples — a human
   reviews before the generated technique corpus changes. Reason: one-off or
   false-positive results must not poison the knowledge base.
4. **Authorized testing is propose-only by default.** Live transmission stays
   behind `ResearchSession` → adversarial gate → `TestAuthorization` →
   `Engine.execute()` dry-run/scope checks, plus an explicit `--execute`
   flag. Reason: safety; passive recon must never authorize active testing.
5. **Company Hunter is one target-intel producer, not the pipeline.**
   Dossiers merge through `TargetIntel.merge_dossier()`; the pipeline works
   identically with a plain target YAML when no dossier exists.
6. **Event bus is supplementary, not the control plane.** The enforced
   `ResearchSession` remains the only authority for active testing.
7. **No automatic vulnerability submission.** Findings produce reports and
   regression tests; submission stays a human decision.
8. **Independent verifier runs on unconfirmed findings only** and never
   weakens the `compete_finding()` calibration gate — it is an additional
   falsification layer, not a replacement.
9. **Causal learning is per-target + global, not per-technique Bayesian
   posteriors.** `learning.CausalStore` tracks Laplace-smoothed
   (technique, technology) rates, evidence predictiveness, and wrong
   patterns — enough to feed the difficulty formula without a full
   probabilistic graphical model.
10. **Fuzzing LLM proposals are a hook, not a dependency.** The deterministic
    mutation engine runs fully offline; an LLM proposer can be injected for
    semantic mutations but is never required.

## Weakest remaining subsystem (honest read)

The **independent verifier's evidence contracts** are the thinnest part:
built-in contracts cover only IDOR-01/02, AUTH-01, SQLI-01; everything else
falls back to the external `evidence.ContractRegistry`, and unknown
technique IDs skip the contract check entirely (not a blocker). A finding
for a technique without a registered contract gets weaker verification.
Next work: generate contracts from the v2 card schema
(`expected_signal` + `positive_oracle` + `false_positive_rules`) so every
card carries its own verification contract.

## Provenance (added to the enforced brain, backward-compatible)

`session.assume(..., provenance=...)` and
`session.add_hypothesis(..., provenance=...)` — optional kwargs, defaults
preserve old behavior. Every assumption and hypothesis in a pipeline session
carries its origin (e.g. `cisa-kev`, `attack-graph path anon→/api/users`).

## Tests

- `deephunt/test_research_loop.py` — 61/61 (all 2.x modules + synthetic E2E:
  observe → model → hypothesize → rank → gate → differential → oracle →
  verifier → learn → regression → report, on a mock target; no network)
- `deephunt/test_pipeline.py` — 31/31 (every stage + full dry pass)
- `deephunt/test_datapipeline.py` — 96/96
- `deephunt/test_ceo.py` — 5/5
- `deephunt/identity/test_identity.py` — 16/16
- `deephunt/company/test_company.py` — 10/10
- `deephunt/test_apiprobe.py` — 4/4, `test_apiseq.py` — 6/6,
  `test_error_intel.py` — 20/20, `test_eventbus.py` — 4/4,
  `test_evidence.py` — 5/5
- `brain/test_session.py` — 19/19

## Safety invariants

- Propose-only default; active execution needs `--execute` + profile
  `active_allowed` + session authorization + scope checks.
- Auto-run results are `inconclusive` pending review; findings stay
  unconfirmed until `compete_finding()` + calibration.
- No automatic technique-corpus merges; no automatic submissions.
- Credential-shaped content is refused at the session layer and never
  persisted (object pool stores prefixes only).
