# Integration Plan — ranked by (value × feasibility) for a bug-bounty hunter
**Date:** 2026-09-27 · Source: intel/project-survey-2026-09-27.md

## Ranking

### TIER 1 — implement now (high value, safely implementable)
1. **BBOT-pattern event bus** (`deephunt/eventbus.py`) — HIGH value / MEDIUM effort.
   *Why first:* single highest-leverage architectural change. Turns the flat adapter
   list into recursive, correlated recon: every new DNS_NAME/IP/URL fans into all
   recon adapters; one dedup registry with scope tags. Clean-room (AGPL — do not
   import BBOT). Pure-Python, fully testable offline.
2. **RESTler-core stateful API sequence engine** (`deephunt/apiseq.py`) — HIGH / MEDIUM.
   *Why:* the biggest *capability* gap — zero multi-step state testing today, and
   state bugs are what scanners miss and bounties pay for. Clean-room ideas only:
   PRODUCES/CONSUMES inference, BFS-Fast planner, dynamic-object pool, feedback
   pruning, checkers (use-after-delete, cross-user replay) mapped onto the
   enforced test loop. Sequence-level safety gates mandatory.
3. **Per-technique evidence contracts** (XBOW pattern; card schema + `deephunt/evidence.py`) — HIGH / EASY.
   *Why:* XBOW's #1 trick is deterministic validation with explicit evidence
   contracts. DEEPHUNT's loop already splits discovery/validation; adding
   `evidence_contract` to cards + a validator closes the FP loop at near-zero cost.
4. **Semgrep bounty ruleset** (`intel/semgrep-rules/`) — HIGH / EASY.
   *Why:* runs over client JS DEEPHUNT already extracts; converts black-box
   observations into structured hypotheses. Adapter absorbs the binary when
   installed; rules ship with `--test` cases.
5. **Payload corpus** (`data/payloads/`) — HIGH / EASY.
   *Why:* fills the stated payload gap overnight: PATT Intruder files vendored per
   class, tagged detect/bypass/exploit. Zero new binaries.
6. **GraphQL introspection prober + OpenAPI spec discovery** — HIGH / EASY-MEDIUM.
   *Why:* feeds the ROLE×OBJECT×ACTION×STATE matrix with schema-derived
   objects/actions. Small Python, testable against a local fake server.

### TIER 2 — implement next (high value, more effort or needs keys)
7. **Nuclei custom template pack** (logic/authz-adjacent: 403-battery, JWT battery,
   CORS, header audit) + finding→template authoring pipeline — HIGH / EASY-MEDIUM.
8. **403/401-battery + JWT-battery + HPP primitive cards** (HackTricks curation) —
   HIGH / MEDIUM (curation is manual).
9. **WSTG-ID coverage map** over 117 cards; add CONF/CLNT/APIT-01 cards — HIGH / EASY-MEDIUM.
10. **Specialist teams over technique cards** (HPTSA pattern: class-specific tool
    chains dispatched by scheduler + shared blackboard) — HIGH / MEDIUM.
11. **Experience manager** (AutoAttacker pattern: index successful tool chains as
    reusable playbooks from episodic memory) — HIGH / MEDIUM.
12. **Shodan/Censys pivot dork packs** — HIGH / EASY but **needs API key** (blocked
    until key available).
13. **ZAP automation adapter** (authenticated SPA crawl, automation plans) — HIGH / MEDIUM.
14. **Response-novelty guidance** (AFL++ lesson: response bitmap + power schedules) —
    MEDIUM / EASY.

### TIER 3 — valuable but deferred
- Bearer/Gitleaks secrets stage (needs binary; easy win when installed) — MED-HIGH / EASY.
- LLM taint-spec extraction → Semgrep (SemTaint pattern) — HIGH / MEDIUM, needs LLM budget.
- ProjectDiscovery pipeline grammar (declarative recon DAGs) — HIGH / MEDIUM.
- Adversarial verification inside compete_finding() + Vul-RAG card fields — MED-HIGH / EASY-MEDIUM.
- Reflection passes over failed attempts (HackingBuddyGPT) — MED-HIGH / EASY.
- PTT-style task-tree plan state — MEDIUM / EASY-MEDIUM.
- Amass-pattern persistent asset graph + run diffing — MED-HIGH / HARD.
- apisn1p3r-style native probe cards — HIGH / EASY (CLI wrap).
- WPScan tech-gated lane — conditional value / EASY.
- theHarvester email/OSINT lane — MEDIUM / EASY.

### DELIBERATELY NOT integrated
- **AFL++/libFuzzer/Honggfuzz/Fuzzilli/syzkaller binaries** — cannot execute against
  remote black-box targets (need local binaries/harnesses). Ideas only.
- **CodeQL engine per-target** — needs source code; heavyweight. Port query models only.
- **Burp core / Caido core / Arachni engine / Skipfish / OpenVAS** — closed, dead, or
  wrong layer. Techniques reimplemented instead.
- **Nikto engine** — superseded by nuclei; wordlists only.
- **ShiftLeft** — dead commercial product; concepts only.
- **DeepTeam** — red-teams LLM systems, not a bug finder.
- **Full LLM agent executor (ReAct over terminal/HTTP)** — the one capability that is
  "just call an LLM": high upside but hard (cost, safety, prompt-injection
  surface). Excluded per scope; revisit with explicit budget + sandboxing.
- **Paid solving services / paid API keys** (Shodan, 2Captcha-class) — need explicit
  spend approval.

## Implemented 2026-09-27 (this commit)
- `deephunt/eventbus.py` — typed event bus (Event, EventBus, ingress dedup/scope,
  intercept tagging, fan-out by watched_events) + `test_eventbus.py` (4/4).
- `deephunt/apiseq.py` — RESTler-core: spec/observed-traffic ingestion,
  PRODUCES/CONSUMES inference, BFS-Fast + bounded random-walk planners, object
  pool, feedback pruning, checkers (use-after-delete, cross-identity replay
  hooks) + `test_apiseq.py` (6/6). Plans/renders only; sends no traffic.
- `deephunt/evidence.py` — per-technique evidence contracts: ContractRegistry,
  validate_evidence(), card contract loading, Canary calibration +
  `test_evidence.py` (5/5).
- `intel/semgrep-rules/` — 10 bounty rules (deephunt-bounty.yaml), YAML-validated;
  4 rules ship `--test` positive/negative cases. semgrep binary NOT installed —
  rules run only when it is; documented as limitation.
- `data/payloads/` — 11-class corpus, 4,409 entries: 6 classes vendored from
  PayloadsAllTheThings (MIT, pinned shallow clone /tmp/patt, deduped, mega
  files capped at 600 lines/file), 5 hand-curated (jwt, ssrf, ssti, authz-403,
  hpp) + `deephunt/payloads.py` loader + MANIFEST.txt with provenance.
- `deephunt/apiprobe.py` — OpenAPI/Swagger spec discovery + GraphQL
  introspection prober (POST/GET/`__type` fallbacks) + `test_apiprobe.py`
  (4/4, local fake HTTP server only).
- 12 new technique cards (117 -> 129), in knowledge/techniques/survey_2026.yaml:
  AUTHB-01 (systematic 403/401 bypass battery), JWT-02 (JWT battery), HPP-01
  (parameter pollution differential), API-05 (OpenAPI spec discovery), API-06
  (stateful API sequencing), GQL-07 (GraphQL introspection fallback ladder),
  SEMGREP-01 (Semgrep JS ruleset triage), EV-01 (evidence contracts), SEQ-01
  (producer/consumer inference), SEQ-02 (bounded sequence planning), SEQ-03
  (feedback pruning + checkers), PAYLOAD-01 (curated payload corpus).
  Note: BUSL-10 was proposed but NOT created; no card with that ID exists.
- Merged knowledge/techniques.yaml regenerated (129 cards); knowledge/graph.json
  rebuilt; build_graph.py CLASS_CWE extended with new klasses `recon`
  (CWE-200) and `methodology` (CWE-1059).
- Cards may carry an optional `evidence_contract` field (EV-01, AUTHB-01,
  JWT-02 use it); deephunt/evidence.py ContractRegistry.load_from_cards()
  consumes it. No change to compete_finding() yet — report gating deferred.
- Tests updated 117->129 + card-presence checks for all 12 new IDs.
