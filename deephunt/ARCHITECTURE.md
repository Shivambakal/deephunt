# DEEPHUNT ATTACKSURFACE — Architecture (as implemented, 2026-09-27)

Target-agnostic vulnerability-hunting pipeline. Entry point:
`deephunt/attacksurface.py`. One complete pass:

```bash
cd ~/workspace/hacker-agent/deephunt
python3 attacksurface.py --target <name> --passes 1 --max-hypotheses 6 --max-tests 3
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
| 5 | WORLD MODEL | `world_model.py` (existing) | dynamic beliefs, invariants, contradictions from observations |
| 6 | ATTACK / TRUST GRAPH | `attackgraph.py` | attack graph = reachability (low-priv → endpoint → object); trust graph = claimed enforcement + belief confidence. Built together, separate views |
| 7 | HYPOTHESIS ENGINE | `hypothesis_fusion.py` | fuses brain-generated + Company Hunter plan + reasoning seeds + attack-graph path seeds; dedupes; checks rejection memory; registers survivors via `session.add_hypothesis()` with provenance |
| 8 | EXPERIMENT PLANNER | `experiment.py` (existing) + `attacksurface.stage_plan` | plans through `session.propose_test()` (adversarial gate), ranks by expected info gain |
| 9 | AUTHORIZED TESTING | `brain/engine.py` (existing) + `stage_authorized_testing` | **propose-only by default**; executes only with `--execute` AND `profile.active_allowed` AND session `TestAuthorization`. Auto-runs record `inconclusive`+evidence — never auto-confirm |
| 10 | OBSERVATION | session | observations → world model beliefs |
| 11 | LEARN + UPDATE ↺ | `learn_updates.py` | confirmed → world-model belief update + **pending-review** technique-card proposal; rejected → deduplicated negative examples; inconclusive → lessons; error-pattern lessons if `knowledge/error_patterns.yaml` exists; idempotent per result |
| ↺ | LOOP-BACK | `attacksurface` | suspicious target-intel diffs re-trigger reasoning/planning |

## Deviations from the original diagram (authorized; documented)

1. **Reasoning runs before AND after the world model.** The diagram shows
   reasoning → world model as a straight line. Initial intel seeds
   assumptions before any model exists; later observations update the model
   and cause re-planning. Reason: cold-start targets have no model yet.
2. **Attack graph and trust graph are separate views, built together.**
   Diagram shows one box. Attack graph = reachability; trust graph = claimed
   enforcement + belief confidence. Reason: they answer different questions
   (what's reachable vs. what's claimed to be enforced).
3. **Technique updates are proposals, not corpus edits.** Diagram's
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

## Provenance (added to the enforced brain, backward-compatible)

`session.assume(..., provenance=...)` and
`session.add_hypothesis(..., provenance=...)` — optional kwargs, defaults
preserve old behavior. Every assumption and hypothesis in a pipeline session
carries its origin (e.g. `cisa-kev`, `attack-graph path anon→/api/users`).

## Tests

- `deephunt/test_pipeline.py` — 31/31 (every new stage + full dry pass)
- `deephunt/test_datapipeline.py` — 96/96
- `deephunt/test_ceo.py` — 5/5
- `deephunt/identity/test_identity.py` — 16/16
- `brain/test_session.py` — 19/19

## Safety invariants

- Propose-only default; active execution needs `--execute` + profile
  `active_allowed` + session authorization + scope checks.
- Auto-run results are `inconclusive` pending review; findings stay
  unconfirmed until `compete_finding()` + calibration.
- No automatic technique-corpus merges; no automatic submissions.
- Credential-shaped content is refused at the session layer.
