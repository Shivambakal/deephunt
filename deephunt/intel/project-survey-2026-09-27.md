# Project Survey — vulnerability-hunting & AI bug-finding landscape
**Date:** 2026-09-27 · **Method:** read-only (repos, docs, papers, writeups). Nothing probed.
**Purpose:** what/how/why per project + gap analysis vs DEEPHUNT.
Full per-track notes: /tmp/survey-{scanners,fuzzers,sast,ai,methodology,recon}.md

DEEPHUNT baseline for gap analysis: Python autonomous bounty hunter; ~100 generic
tool adapters (binary-installed = live); enforced ResearchSession loop
(hypothesis → adversarial check → TestAuthorization → Engine.execute with
dry-run + scope gates → compete_finding alternative rejection); 117 technique
cards / 11 domains; semantic target model + ROLE×OBJECT×ACTION×STATE matrix;
mitmproxy traffic proxy w/ match-replace rules; identity/ test-account module;
CLI + localhost GUI.

---

## A. SCANNERS & HUNTER PLATFORMS

### A1. Nuclei (ProjectDiscovery)
- **What:** Template-driven scanner. YAML templates → requests; matchers (word/regex/status/size/binary/DSL) decide findings. ~9k community templates. v3: `flow` (JS multi-request sequences), multi-protocol templates, global matchers (`-egm` secret sweep over ALL responses), Nuclei SDK.
- **How:** Go; protocols http/dns/network/ssl/file/code/javascript; DSL `contains(body,…)`, `status_code==200`; extractors capture dynamic values into template context; payload attack types clusterbomb/pitchfork.
- **Why it works:** community CVE templates land fast; one finding → reusable check; JSONL composes in pipes.
- **Gap vs DEEPHUNT:** (1) *template-authoring pipeline* — every confirmed finding becomes a re-runnable check; (2) global-matcher secret sweep over captured proxy traffic; (3) flow-style authenticated multi-request sequences.
- **Integration:** EASY (binary auto-detect, JSONL). **Value: HIGH.**

### A2. OWASP ZAP
- **What:** Open-source intercept proxy + active scanner.
- **How:** MITM proxy core; passive scanner (zero extra requests); AJAX spider (headless browser); active scanner with per-rule strength×threshold; Automation Framework YAML plans (env → spider → passiveScan-wait → activeScan → report); api-scan imports OpenAPI/SOAP/GraphQL; ~700-endpoint REST API.
- **Why it works:** only serious OSS active scanner; contexts (include/exclude regex, authenticated users); script add-ons.
- **Gap:** authenticated SPA crawling; passive-scan-as-you-browse; strength/threshold budget knobs; automation-plan YAML execution.
- **Integration:** MEDIUM (REST API; daemon/session lifecycle). **Value: HIGH.**

### A3. Burp Suite extension ecosystem (technique mine — closed core)
- **What:** Proxy platform; extensions = years of researcher technique.
- **How:** Montoya API hooks traffic; BChecks = native YAML custom checks (headless `--bchecks-dir`); Bambdas; Turbo Intruder (scripted high-rate engine); Collaborator (OAST); REST API.
- **Key extensions → transferable techniques:** Param Miner (hidden param/header brute-force, unkeyed inputs); HTTP Request Smuggler (CL.TE/TE.CL timing differentials); Turbo Intruder single-packet races; **Autorize** (replay-as-low-priv-user → Bypassed/Enforced matrix); Backslash Powered Scanner (behavioral probing for *unknown* injection classes); Collaborator Everywhere (OOB payloads on all traffic); Active Scan++ (host-header, SSTI); JWT Editor (alg-none/key-confusion).
- **Gap:** Autorize-style authz matrix, param mining, OOB interaction server, race engine, behavioral probing, BChecks-style YAML checks. (Techniques transfer; code doesn't.)
- **Integration:** HARD (reimplement). **Value: HIGH** — prioritize Autorize, Param Miner, Collaborator, race logic.

### A4. Caido
- **What:** Modern Rust intercept proxy (Burp alternative).
- **How:** async Rust proxy; SQLite+WAL + full-text index; Workflows = node chains on QuickJS; HTTPQL traffic query language; plugin SDK.
- **Why:** fast, light, great UX. Lacks active scanner and OAST.
- **Gap:** HTTPQL-like query language over captured traffic; per-engagement project isolation. (DEEPHUNT already has match-and-replace.)
- **Integration:** MEDIUM. **Value: MED** — inspiration, not adoption.

### A5. ProjectDiscovery stack (subfinder/httpx/katana/naabu/dnsx/tlsx/alterx)
- **What:** One-stage-per-tool recon pipeline composed via Unix pipes.
- **How:** ~20 Go CLIs; canonical chain subfinder→dnsx→alterx→naabu→httpx→katana→nuclei; everything streams JSONL; rate-limit flags; katana headless + JS parsing; tlsx SAN harvesting feeds back into enum.
- **Why it works:** the one-liner pipe grammar; fingerprint dedupe (title+length+webserver).
- **Gap:** the *pipeline grammar* — declarative recon chains (YAML stdin/stdout DAGs with stage caching/dedupe/resume) vs DEEPHUNT's ad-hoc tool list; httpx/katana/tlsx fingerprint normalization into the feature graph.
- **Integration:** EASY. **Value: HIGH** — recon is the top of every funnel.

### A6. Nikto / Wapiti / Arachni / Skipfish / OpenVAS
- **Nikto:** 7k signature checks; nuclei supersedes. Take legacy wordlists only. EASY / **LOW**.
- **Wapiti:** Python black-box scanner; per-module attack logic (backup files, time-based SQLi) is technique-card seed; engine weaker than ZAP+nuclei. EASY / **MED**.
- **Arachni:** effectively unmaintained; steal *fingerprint-first check selection* (tech → relevant cards before spending budget) and plugin/check/reporter separation. MEDIUM / **MED**.
- **Skipfish:** dead since 2012; philosophy only (learn-normal → anomaly-flag). **LOW**.
- **OpenVAS:** infra VA, not web-DAST; heavy stack. Deprioritize for bounty. **MED** value, later.

---

## B. FUZZERS

### B1. AFL++ / libFuzzer / Honggfuzz — binary-only, ideas only
Coverage-guided mutation; can't instrument remote targets → not runnable on bounties.
Transferable: **response-surface-guided fuzzing** (treat status×schema-shape×headers×timing as a "response bitmap"; keep novelty-producing inputs; power-schedule rare classes); CMPLOG analog = replay tokens/IDs observed in responses; broaden the oracle beyond status codes (timing, reflected payloads, error-text deltas); signature-based finding dedup (Honggfuzz lesson).
Integration: HARD as tools. Value: **LOW** as tools, **MEDIUM** as ideas.

### B2. RESTler (Microsoft Research) — ★ highest-value gap in survey
- **What:** First *stateful* REST API fuzzer. Found 28 GitLab bugs + Azure/O365 bugs.
- **How:** Compile OpenAPI → per-request grammar; **dependency inference**: PRODUCES(req) = dynamic-object types in response schema, CONSUMES(req) = types required by params, matched by name/type — purely static. Sequence kept iff every consumed type was produced earlier. Search: BFS / BFS-Fast / RandomWalk. RENDER concretizes from dictionaries; EXECUTE memoizes dynamic objects, feeds later requests; **dynamic feedback pruning** (400/500 on reuse → discard sequence). Oracles: any 500 = bug; **Checkers** = pluggable security properties (use-after-free: DELETE→GET should 404; cross-user replay = differential testing; resource leaks); bug bucketization + replay logs.
- **Why it works:** multi-step state bugs are exactly what scanners miss; static inference needs no traffic; checkers encode IDOR/BOLA-shaped properties.
- **Gap:** DEEPHUNT has ZERO stateful API sequencing. Reimplementation (clean-room, Python): spec ingestion from OpenAPI *or synthesized from mitmproxy traffic*; PRODUCES/CONSUMES via fuzzy field-name matching (`id`, `*_id`, `uuid`, `slug`, `token`); BFS-Fast + RandomWalk planner (length 2–4); dynamic-object pool; dictionaries from observed values + card payloads; feedback pruning; **checkers as ResearchSession hypotheses** (use-after-delete, cross-user replay via existing differential comparator); sequence-level safety gates (bounded length, throttle, non-destructive default).
- **Integration:** MEDIUM. **Value: HIGH** — top of survey.
- **Safety:** paper warns fuzzing can cause outages → Engine.execute() gates required.

### B3. boofuzz — steal the pattern, not the dependency
Typed request blocks + session graph + dynamic value extraction from prior responses; per-target modeling cost too high to adopt. Use mitmproxy traffic as the auto-model source. MEDIUM / **MEDIUM** (non-HTTP surfaces).

### B4. Fuzzilli — design lesson
FuzzIL IR: mutate typed request structs, never raw bytes → validity by construction. EASY–MEDIUM as pattern / **MEDIUM**.

### B5. syzkaller — upgrades to RESTler reimplementation
Resource-typed dynamic objects (`user_id`, `session_token`) instead of raw name matching; **choice-table sequence prior** learned from traffic + novelty feedback; auto-minimization of anomaly sequences into reproducers. MEDIUM / **MEDIUM**.

---

## C. SAST & SEMANTIC ANALYSIS

### C1. Semgrep OSS — top SAST pick
- **What:** Fast pattern-based static analysis; rules as code-like YAML with metavariables.
- **How:** per-language AST parsing; boolean combinators; **taint mode**: `pattern-sources/sinks/sanitizers/propagators`; `--test` with `# ruleid:`/`# ok:` annotations.
- **Why:** 10–30x faster than classic SAST; trivial rule authoring; deterministic.
- **Gap:** DEEPHUNT's extracted client JS is the perfect input — run Semgrep over extracted bundles with custom bounty rules; converts black-box observations into structured hypotheses. Per-file taint is *sufficient* at bundle scope.
- **Integration:** EASY (pip binary; adapter framework absorbs it; `--json`). **Value: HIGH.**

### C2. CodeQL — port models, don't run the engine
Gold-standard whole-program analysis, but needs source (black-box targets give only extracted JS) and is heavyweight. **Port its open JS query packs' source/sink models** into Semgrep rules + technique cards. HARD as engine / **MED** as model library.

### C3. Bearer — near-free wins
Go CLI; SAST + **secrets scanning (Gitleaks lib)**; privacy/PII-flow rules (PII→JWT/logs/URLs). EASY / **MED-HIGH** (secrets stage alone is high value).

### C4. ShiftLeft — dead commercial; steal concepts
CPG (endpoints × code × dataflow in one graph) is what DEEPHUNT's target model should become; reachability-based prioritization validates the calibration gate. Design input only.

### C5. LLM-based static analysis (LLMVD.js, SemTaint)
- **LLMVD.js (CMU/Google 2026):** LLM agent pipeline (scan→propose→PoC→execute-oracle) on npm: 84% confirmed vs <22% classical; 36 validated exploits on 260 packages.
- **SemTaint:** LLM resolves unresolvable call edges + classifies sources/sinks per CWE → feeds CodeQL: 106/162 previously-undetectable vulns. **Key lesson: LLM's best role = taint-spec extraction, not replacing the engine.**
- Blueprint for DEEPHUNT: LLM extracts taint specs from extracted JS → deterministic Semgrep executes → findings feed hypothesis loop → execution validates. LLM handles auth logic, IDOR-prone patterns, PP gadgets — classes scanners can't express.
- **Integration:** MEDIUM (prompting over existing brain modes; token-gated). **Value: HIGH.**

### Semgrep rule concepts (bounty-focused, for extracted JS)
IDOR-prone fetch (route params → string-concat URL); token mishandling (localStorage → URL/postMessage/cookie/log); GraphQL input interpolation vs `variables:`; prototype pollution (tainted keys → merge/`obj[$K]=$V`); DOM XSS sinks with DOMPurify exclusions; client-side role gates → target model; secrets; SSRF hints; `Math.random()` nonces; postMessage without origin check.

---

## D. AI BUG FINDERS

### D1. XBOW — architecture to emulate (closed source; facts from Black Hat USA 2025 talk)
- **Confirmed:** LLM agents do *discovery*; **validation is non-LLM deterministic code**; canary framing (canaries planted in code/filesystem, agents chase them — fixes LLMs' poor "tried hard enough" judgment); per-vuln-class validators demand exact evidence; human review before submission. Scale: 17k Docker Hub apps × 100 runs → 174 vulns, 22 CVEs; 285 HackerOne reports; #1 on HackerOne leaderboard (June 2025), ~25% above top human.
- **Why it works:** discovery/validation split → near-zero FP at scale; explicit evidence contracts; brute scale.
- **Gap:** DEEPHUNT's loop already mirrors the split. Missing: **per-technique evidence contracts** (what artifact = proof) and canary-style calibration oracles.
- **Integration:** EASY. **Value: HIGH.**

### D2. PentestGPT — PTT transfers without LLM
3 sessions (Reasoning/Generation/Parsing) share a **Pentesting Task Tree** — compressed NL task tree with completion states, fixing context loss. → DEEPHUNT: hierarchical task-tree plan state (target→phase→technique→attempt, done/failed/blocked). EASY-MEDIUM / **MEDIUM**.

### D3. HackingBuddyGPT — reflection passes
Ablations: high-level guidance 33%→66%; LLM-driven **reflection** doubled unaided success 33%→66%. Scaffolding beats model size. → structured reflection passes over failed attempts + tiered guidance before burning attempts. EASY / **MEDIUM-HIGH**.

### D4. AutoAttacker — Experience Manager
Summarizer→Planner→Navigator + **Experience Manager** (RAG over executed tasks to compose complex attacks from basic ones). → index DEEPHUNT's episodic memory of *successful tool chains* as reusable playbooks. MEDIUM / **HIGH**.

### D5. VulnBot — schema-constrained tool calls
LLMs fabricate tool parameters → validate tool-adapter args against schemas across all adapters. EASY / **MEDIUM**.

### D6. Burp AI — "Explore Issue" pattern
On a weak signal, spawn a bounded follow-up investigation (targeted PoC + impact analysis) before promote/discard. → new pipes stage. MEDIUM / **MEDIUM-HIGH**.

### D7. LLM-agent harnesses (HPTSA, Incalmo, one-day agent)
HPTSA: hierarchical planner → team manager → expert agents: 42% zero-day, **4.3× single-agent**; ZAP/Metasploit 0%. One-day agent: 87% *with* CVE description → 7% without (discovery without description is the hard part = VDP reality). → reorganize 117 cards into **specialist teams** with class-specific tool chains, dispatched by scheduler + shared asset blackboard. No LLM needed. MEDIUM / **HIGH**.

### D8. LLM vuln detection research (Vul-RAG, adversarial verification, DeepAudit)
LLMs beat SAST on F-1 via recall but higher FP; **Vul-RAG**: knowledge-level RAG (root cause/CWE/fix/trigger) +16–24%; **adversarial verification** (clean-context challenger: "argue why NOT exploitable") cuts FPs. → (a) formal adversarial step inside `compete_finding()`; (b) enrich cards with root-cause/CWE/trigger/fix fields; (c) validates reason-proposes/deterministic-disposes split. EASY-MEDIUM / **MEDIUM-HIGH**.

---

## E. METHODOLOGY & PAYLOAD CORPORA

### E1. OWASP Testing Guide v4.2 — coverage spine
97 tests; automatable subset classified: INFO-02/03/08, INFO-04, CONF-02..08/10/11, ATHN-02/03/06, ATHZ-01/04, SESS-02/04, INPV-01/02/04/05–13/18/19 (+03/15/16/17 semi-auto), ERRH, CRYP-01/03, BUSL-08/09, CLNT-04/07/09/10/13, APIT-01. Human-only: BUSL-01–07 (the business-logic core — DEEPHUNT's stated weakness), most SESS/ATHN.
→ Map 117 cards → WSTG IDs; expected holes: BUSL-01–07, APIT-01, systematic CONF probes, CLNT header checks. EASY checklist / MEDIUM per-probe. **Value: HIGH.**

### E2. OWASP API Top 10 2023 — executable backlog
No official automation spec; synthesized checks per risk: API1 BOLA (2-account replay, horizontal/vertical/unauth/write); API2 JWT battery + rate probes; API3 mass-assignment + schema diff; API4 pagination/GraphQL-batching abuse; API5 admin-endpoint replay; API6 rate probes w/ XFF rotation; API7 SSRF metadata; API8 header/debug/CORS audit; API9 version sweep + spec exposure + mobile-web diff; API10 webhook SSRF.
→ API1/3/5 as first-class executable modules; API4/6 rate probes; API9 sweeps; API2 JWT battery. MEDIUM (needs 2-account orchestration) / **HIGH**.

### E3. PayloadsAllTheThings — direct fill for the payload gap
81k★; 66 topic dirs; `Intruder/*.txt` = drop-in fuzz dicts. Ranked signal: XSS polyglots > SQLi (per-DBMS + time-based) > CMDi (delay/marker) > SSTI polyglots > SSRF metadata > XXE > traversal > upload matrix > JWT > open-redirect/HPP/mass-assign/GraphQL > CRLF/CSV/type-juggling.
→ Vendor `data/payloads/<class>.txt` from Intruder files + README fenced blocks, tagged detect/bypass/exploit × context. EASY (pinned shallow clone + build script) / **HIGH**.

### E4. SecLists — discovery lists
Hunter-relevant: `Discovery/Web-Content/raft-medium-*`, `directory-list-2.3-medium.txt`, **`api/api-endpoints.txt`, `api/objects.txt`, `api/api-versioning.txt`**, `common.txt`, DNS `subdomains-top1million-5000/20000.txt`, default-passwords. Exclude: rockyou-for-discovery, raft-large, webshells.
→ wire discovery adapters to api/*.txt + raft-medium. EASY / **HIGH** (discovery), MEDIUM (fuzzing).

### E5. HackTricks — bypass primitives → "primitive cards"
Automatable: **403/401 battery** (path mutations `/./admin`, `/%2fadmin`, `/%252fadmin`, `..;/`; headers `X-Original-URL`, `X-Forwarded-For` family, IP encodings; method swaps + `X-HTTP-Method-Override`; Googlebot UA — differential vs 403 baseline); HPP (dup keys, `a[]=1`, query+body+cookie split); smuggling timing probes; **JWT battery**; GraphQL introspection/alias-batching; CORS (null origin, reflection); host-header; CRLF; cache deception; SSRF metadata; WebSocket/CSWSH.
→ convert to primitive cards (request template + differential signal). MEDIUM curation / **HIGH** — bypass logic is where scanners fail.

### E6. API hunter tools
kiterunner (in DEEPHUNT already); Arjun (param discovery); **BOLA-Hunter** (4 techniques: unauthenticated, id-enumeration, horizontal-read, write-bola — template for API1 module); **RESTler**; **schemathesis** (property-based); **apisn1p3r** (single-file Python: path discovery, CORS, method matrix, header audit, auth-bypass, JWT, GraphQL, spec discovery, rate-limit — closest to DEEPHUNT adapter shape → vendor probes as native cards).
EASY (CLI wrap) / **HIGH** for BOLA design + apisn1p3r probes.

---

## F. RECON FRAMEWORKS

### F1. BBOT — ★ highest-leverage architectural change
- **What:** Recursive event-driven attack-surface discovery; 100+ Python modules consume/produce typed events.
- **How:** Everything is an **event** (type, data, parent chain, `scope_distance` = hops from seed, tags). Modules declare `watched_events`, have in/out queues; scan redistributes emitted events. Stages: **ScanIngress** (dedup, blacklist, scope check) → **Intercept** (DNS normalization, cloud tagging) → **ScanEgress** (scope filter, graph mgmt) → fan-out → outputs. **Recursion is emergent**: portscan (DNS_NAME→OPEN_TCP_PORT) ↔ sslcert (OPEN_TCP_PORT→DNS_NAME) feed each other, no central orchestrator. `excavate` parses every HTTP response into URL/WEB_PARAMETER/FILESYSTEM/STORAGE_BUCKET/TECHNOLOGY events (= DEEPHUNT's JS/HTML extraction wired into the bus). `-rf passive` kills active modules in one flag. Hard-won stability: ingress throttling under memory pressure, event refcounting, heavy unit tests.
- **Why it works:** correlated deduped findings with provenance; recursion finds 20–50% more (third-party claim, unverified).
- **Gap:** DEEPHUNT's recon is a flat adapter list — no recursion, no cross-tool correlation, no dedup registry. Event bus adds: new DNS_NAME/IP/URL auto-fans into all recon adapters; single event registry with scope tags; extraction becomes a producer feeding swagger/GraphQL probers.
- **Integration:** MEDIUM — **do NOT import (AGPLv3)**; clean-room the pattern (typed events + queues + ingress/egress is small) or wrap `bbot` CLI (easy).
- **Value: HIGH.**

### F2. Amass — persistent asset graph
~100 data-source plugins → entities+edges in graph DB; re-runs reload old findings and re-verify; intel mode feeds enum scope. → DEEPHUNT: persistent asset graph + run-over-run diffing (campaign mode). EASY as CLI adapter; HARD to port graph. **MEDIUM-HIGH.**

### F3. theHarvester — email/OSINT lane
54+ sources → emails/subdomains/hostnames/people. DEEPHUNT has no people/email lane → breach-lookup path. EASY / **MEDIUM.**

### F4. Shodan/Censys dork packs — passive, high signal
Dork families: exposed DBs/services; panels (`http.title:"Grafana|Jenkins"`); **target pivots** (`ssl.cert.subject.cn:TARGET`, `hostname:`, `org:`, `net:` — finds staging DNS never shows); `vuln:CVE-...`; `http.favicon.hash:` fleet pivoting. → per-target cert/ASN/favicon pivot packs + exposed-service dork pack. EASY (needs API key + scope gating) / **HIGH**.

### F5. WordPress: WPScan lane, tech-gated
Signal: `-e vp,vt` (vuln plugins/themes only), aggressive plugin detection, `-e u` users, `-e cb` backups, xmlrpc.php, debug.log, `/wp-json/wp/v2/users`. Noise: full enumeration, login brute-force. → tech-conditional WP lane (WP detected → WPScan + Nuclei WP + wp-json enum). EASY / **MEDIUM** overall, HIGH on WP targets.

### F6. API recon — spec discovery + GraphQL prober
Swagger/OpenAPI discovery (probe `/swagger.json`, `/openapi.json`, `/v2|v3/api-docs`, `/docs`, `/api/docs` + Wayback for removed specs); spec = full attack map (routes+params, missing `security:`, internal routes); **SIT-vs-PROD spec diff**. GraphQL: endpoint discovery → introspection via POST, then GET, then `__type` (each bypasses naive blocks) → Clairvoyance brute-force → graphql-cop audit, graphql-path-enum, error-suggestion leaks rebuild schema.
→ DEEPHUNT has kiterunner but NO spec-discovery probe list, NO introspection prober, NO schema→endpoint extraction — yet its ROLE×OBJECT×ACTION×STATE matrix needs schema-derived objects/actions as input. EASY-MEDIUM / **HIGH**.

---

## Honest limits of this survey
- XBOW internals beyond the Black Hat 2025 talk facts are inference; AutoAttacker has no public code.
- BBOT "20–50% more subdomains" is a third-party claim, unverified.
- Semgrep OSS taint boundary (per-file vs intra-procedural) to be verified empirically.
- HackTricks pages not opened directly — re-verify trick details at the wiki before card-ification.
- SecLists `api/` filenames from secondary sources.
- PATT per-dir Intruder contents not sampled (structure confirmed).
- Nuclei ~9k template count / ZAP rule IDs are doc-sourced, version-sensitive.
- LLMVD.js / SemTaint figures from arXiv abstracts/summaries, not full papers.
