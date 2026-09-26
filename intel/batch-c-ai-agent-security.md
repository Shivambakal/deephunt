# Batch C — AI-agent security intel (ingested 2026-09-26)

16 URLs assigned; 13 fetched successfully. Skipped (browser service 429, not retried):
catonetworks.com/blog/duneslide-two-critical-rce-vulnerabilities,
aisle.com/blog/aisle-discovers-1-click-rce-vulnerability-in-cursor-vs-code-and-google-antigravity,
github.com/Metnew/write-ups (claude-code-worktree-sandbox-escape),
blog.ammaraskar.com/github-token-stealing.

---

## 1. Hacking Google with AI for $500,000 — brutecat.com
**What:** Researcher used Claude to auto-fuzz Google's APIs at scale. Pipeline: harvested API keys (60k+ Android APKs unpacked + grepped, Chrome extension intercepting traffic across 2.8k+ Google domains), filtered Google-owned GCP projects via a Cloud Marketplace project-info endpoint, enumerated API domains via cert-transparency + `Server: ESF/GSE` header fingerprinting, mass-scanned for discovery documents (Swagger equivalents) — bypassing Google's removal of `/$discovery/rest` and brute-forcing visibility labels (`?labels=GOOGLE_INTERNAL` revealed hidden endpoints) — then AI-fuzzed 1,500+ APIs.
**Pattern:** Machine-readable API specs + key harvesting + automated AI fuzzing = scale. Note Google's First-Party Auth (SAPISIDHASH from cookies + origin whitelist) as the auth layer to understand.
**Hunter action:** For any target with public API docs (Swagger/OpenAPI/discovery): feed the whole spec to an LLM to generate per-endpoint fuzz variations instead of hand-testing. Harvest API keys from the target's APKs and JS bundles; try hidden-doc variants (`?labels=`-style params); fingerprint infra via `Server` headers. Tooling: geminiHunter-style key grepping + subfinder/httpx for API-domain enumeration.

## 2. Visa Vulnerability Agentic Harness (VVAH) — github.com/visa/visa-vulnerability-agentic-harness
**What:** Open-source 12-stage pipeline: S0 static seed → S1–S3 threat modeling/discovery → S4–S6 multi-lens analysis + adversarial verification + exploit verification over real HTTP (S6, localhost-only, opt-in) → S7–S9 dedup/chaining/SARIF reporting → S10–S11 remediation/validation. Multi-model, per-role model config. Design bets: threat-model before analysis, multi-agent voting to cut false positives, adversarial validation.
**Pattern:** Pipeline discipline beats model choice. Triage speed (Mean Time to Adapt) is the bottleneck, not discovery.
**Hunter action:** Steal the pipeline shape for the hunter agent: recon → threat-model → multi-lens analysis → adversarial validator → structured report. Clone VVAH for source-available targets — but only code you own or are authorized to scan.

## 3. MCP Client OAuth Refresh-Token Support Matrix — redcaller.com
**What:** July 2026 survey: only Gemini CLI has full `refresh_token` grant support; 10 clients partial/broken (Claude Code, Cursor, Cline, Continue, Open WebUI, Goose, LibreChat, Zed, Copilot CLI, Claude Desktop), 2 not implemented. SEP-2207 (Final) standardizes `offline_access` scope augmentation. Known bugs: Claude Code metadata-discovery fails on non-root-path URLs; MCP Python SDK discards stored refresh tokens; mcp-remote double-401 re-auth loop.
**Pattern:** OAuth token-refresh is the weak seam across MCP clients; token-handling bugs break sessions silently.
**Hunter action:** When testing MCP servers or agent products: probe refresh behavior, non-root-path discovery URLs, and refresh-token omission; check logs/config for leaked tokens. Defensive: prefer short-lived access tokens + rotation on the server side since clients are unreliable.

## 4. AutoJack: single page → RCE on the AI agent's host — microsoft.com/security/blog
**What:** AutoGen Studio chain, three weaknesses: (1) MCP WebSocket origin allowlist trusted localhost, but the agent's own headless browser IS localhost (confused deputy); (2) auth middleware explicitly skipped `/api/mcp/*`; (3) `server_params` query param was base64-decoded into StdioServerParams and executed as an OS command. One malicious page rendered by the browsing agent = RCE. Fixed pre-release on main.
**Pattern:** Localhost stops being a trust boundary the moment an agent browses untrusted content. Control planes must be authenticated, authorized, isolated.
**Hunter action:** When hunting AI-agent products: enumerate loopback services the agent can reach (scan localhost ports from the agent's context if you control it); test whether agent-rendered content can reach control-plane endpoints (WebSockets, unauthenticated `/api/*`). Defensive: never run a browsing agent on the same host as privileged local services; detect on agent processes opening loopback WebSocket connections to dev-tool ports.

## 5. The Bug Bounty Singularity: Our Hackbot — josephthacker.com
**What:** Thacker + JD (xssdoctor) built a Claude Code hackbot: 126 bugs in 5 months. Three rules: **#1 Keep logs** (stream full sessions to Discord — observability is what separates a hacker from a hallucination machine); **#2 Keep hacking** (Ralph loops for persistence + an orchestrator that judges target richness and cuts thin targets loose); **#3 Validate** (a dedicated validator bot rewarded for KILLING findings, not finding them — FP rate 80%→60%). Auth insight: 80% of tokens were burned fighting anti-bot logins; fix was a real machine + real Chrome keeping sessions alive for the cloud bot.
**Pattern:** Persistence + observability + adversarial validation > model smarts. Auth/session management is the budget killer.
**Hunter action:** Adopt the 3 rules as workflow law: log every agent run, loop with an orchestrator judging whether the target deserves more time, always run an adversarial validator pass before trusting a finding. Post-auth is where the money is — solve sessions with real browsers, not headless retries.

## 6. Harnessing Harnesses — blog.zsec.uk
**What:** The harness (orchestration layer: inputs, tools, prompts, models, state, validation gates, outputs) matters more than the model. Reviewed: RAPTOR (6-stage validation incl. Z3/SMT), Anthropic's defending-code-reference-harness (ASAN-instrumented Docker, binary PoC per finding), baby-naptime (single-agent runtime loop), evilsocket/audit (8-stage; trace stage must show attacker input → sink), VVAH. Build advice: per-stage prompts (never one system prompt for everything), context window as a budget (single-function analysis ~8K tokens; summarize tool output), Scrutineer's `revalidate` skill re-checks findings against git history.
**Pattern:** Verification stages + context budgeting = the leverage. Raw model output without a harness is unverifiable.
**Hunter action:** Structure all AI usage into stages with tight, job-specific prompts; add a revalidate step (re-check each finding against current behavior before reporting); budget context aggressively — feed one file/one endpoint at a time, never whole codebases.

## 7. ZeroQuarry: vuln chains in AI-reviewed code — zeroquarry.com
**What:** Found 13 high + 33 medium in iShortn (URL shortener) that CodeRabbit AI review missed: (a) cross-tenant BOLA — API accepted a `domain` param without checking the API-key owner's ownership, plus mass assignment via PATCH (TypeScript types don't validate at runtime); (b) blind SSRF in link-preview/iframe check — no DNS-resolution validation, followed redirects; (c) cross-workspace custom-domain takeover — confused Vercel project-wide verification with workspace ownership. Lesson: AI review sees diffs, not products; it misses cross-tenant, BOLA, and SSRF chains.
**Pattern:** Authenticated ≠ authorized. Every URL-fetching feature is an SSRF candidate. Mass assignment hides behind typed handlers.
**Hunter action:** For any multi-tenant target with your two test accounts: swap tenant-scoped params (domain, org_id, workspace) between accounts; stuff extra JSON fields into PATCH/PUT bodies; point every URL field at an OOB collector (incl. via redirects). Add tenant-confusion + mass-assignment to the standard playbook.

## 8. Promptfoo LM Security Database — promptfoo.dev/lm-security-db
**What:** 985 research findings across 1,123 evaluated models — searchable primary-source DB of LLM/agent attacks: prompt injection, memory injection (InjecMEM), context privilege escalation, SkillBloat (token amplification via skills), visual prompt injection (Repeat-After-Me), unlearning gaps, embedding leakage.
**Pattern:** Reference library mapping attack classes to architectures (memory systems, skills, RAG, vision).
**Hunter action:** Add "search the LM Security DB for the target's stack" to the recon workflow for any AI-agent target — pick attack classes that match its architecture (memory → memory-injection tests; skills → skill-injection; RAG → retrieval leakage) instead of generic prompt-injection spraying.

## 9. Detecting Agentic Threats in Claude — papermtn.co.uk
**What:** Execution-layer detections (Sigma rules + correlation runner on OpenTelemetry tool-call events) in five families: permission/guardrail integrity (`permission_mode_changed` → bypassPermissions; reject-then-near-identical-approve), supply chain (unsanctioned MCP servers/skills/plugins via allow-list), dangerous actions (destructive Bash, secret-path reads, out-of-scope access), indirect injection/exfiltration, memory poisoning. Framed by the "lethal trifecta": private data + untrusted content + exfil path.
**Pattern:** Detect on the action surface, not the prompt surface; correlate sequences on session/prompt IDs.
**Hunter action (defensive):** The Sigma patterns transfer to guarding your own agent ops: alert on permission-mode escalation, non-allow-listed MCP servers/skills, and reject→approve sequences. **(Offensive):** When testing agent products, check for the lethal trifecta — can the agent touch private data AND untrusted content AND an outbound channel? That's the shape of every major agent incident (EchoLeak, Amazon Q wiper).

## 10. Local AI for Penetration Testing — projectblack.io
**What:** Benchmarked 4 approaches against a known PHPIPAM auth LFI (CVE-2026-12194): semgrep auto (missed), cloud agentic pentest (Strix + GLM 5.1, ~60M tokens, missed), cloud SOTA + security-review skill (inconsistent), local model + custom harness walking one source file at a time (found it EVERY run — then found a real myVesta auth RCE, CVE-2026-12195). Conclusion: harness/approach matters more than the model.
**Pattern:** File-at-a-time review with structured per-file reports beats whole-codebase agentic review; cheap, private, reproducible.
**Hunter action:** For source-available targets: walk code file-by-file with tight prompts and collect structured reports, then synthesize — instead of one big "find bugs" prompt. Runs on local hardware (Qwen-class, ~170K context), zero API cost, no data egress.

## 11. Hacking with LLMs, agentic CLIs, MCP servers — yeswehack.com
**What:** Agentic CLI (Claude Code/Gemini CLI/Codex) + MCP (Burp/Caido) puts the model inside your proxy environment: it sees HTTP history, replays requests, suggests payloads. Critical lesson: the LLM found a real DOM XSS but produced a payload the app's filter blocked; manual refinement (event-handler injection reusing the existing tag) made it work. Never submit unvalidated AI findings — platforms ban for AI slop.
**Pattern:** Model as second pair of eyes inside your environment; human owns validation and the PoC.
**Hunter action:** Workflow rule: LLM suggests, human reproduces — every PoC gets manually fired before it goes near a report. Wire Burp's MCP server into the laptop-side agentic CLI. Report discipline: description/repro/PoC/impact from your own testing; LLM polishes, never authors from scratch.

## 12. How to use Claude Code for Bug Bounty — yeswehack.com (llm-series-claude)
**What:** Blind-lab tests (Opus 4.8): excellent at recon/discovery, weak at last-mile exploitation — missed following a redirect in a DOM XSS lab; found H2.TE request smuggling in 34 min but needed human help to finish queue poisoning. Model-per-job split: Opus (reasoning/chaining), Sonnet (recon/mapping), Haiku (high-volume processing). Encode repeated failure patterns as reusable skills.
**Pattern:** LLMs discover, humans deliver. Skills are crystallized lessons.
**Hunter action:** Split model spend by job (cheap for recon summaries, strong for chaining); turn every recurring miss into a playbook step (the hunter's playbooks already do this — keep growing them). Treat the hunter's `ai` command as the Sonnet-class job and manual validation as the human job.

## 13. Bing Images RCEs — xbow.com
**What:** Autonomous AI found 3 Critical RCEs (CVE-2026-32194/32191/21536, CVSS 9.8): a blind SSRF in reverse image search + a suspicious 500 → crafted SVG reached a shell-backed image converter (ImageMagick-style delegates) → SYSTEM on production workers. Method: persistence; hypothesis-driven probing where every payload asked the backend a question; OOB callbacks as the oracle; parser fingerprinting via pseudo-protocols (`label:`, `xc:`, `vid:`) and content-type differentials; validator blind spots on heterogeneous workers. Safe research: benign read-only proof commands only, OOB collector under researcher control.
**Pattern:** "Boring" helpers (image converters, upload handlers) are the vulnerability. Never close a blind SSRF as informational — ask what happens to the bytes after fetch. Chase every anomaly one layer deeper than the trail goes cold.
**Hunter action:** For any target with image/file upload: test SVG/XML content types, look for parser differentials (different content types → different errors = different parsers), and use OOB callbacks (interactsh-style) to detect blind server-side processing. If an upload endpoint exists, map what the backend does with the bytes before declaring it safe.
