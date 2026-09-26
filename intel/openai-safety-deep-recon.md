# OpenAI Safety Bug Bounty — Passive Deep Recon

- **Report date:** 2026-09-26
- **Recon type:** PASSIVE ONLY (public web pages, docs, press, GitHub). No scanning, probing, sign-ins, or API testing.
- **Program found via Bugcrowd search (not guessed):** search "Bugcrowd OpenAI bug bounty program" → live engagement page opened and read in full: **https://bugcrowd.com/engagements/openai-safety** ("Safety Bug Bounty"). Note: policies change without notice — re-verify before testing.
- **Program entry per official page:** `openai.com/index/safety-bug-bounty/` → Apply → Bugcrowd engagement. Engagement has "transitioned to public" (no invitation needed).

**Important framing:** This is the **AI-safety-scoped** program (agentic abuse, platform integrity, proprietary-info), launched **2026-03-25/26**. It complements — not replaces — the older **Security Bug Bounty** (`bugcrowd.com/openai`, launched April 2023, 409 vulnerabilities rewarded; classic web/API scope). Submissions are triaged by a joint Safety + Security team and may be **rerouted between the two programs**.

---

## 1. Live Policy (read from the engagement page 2026-09-26)

### In-scope categories (exact wording)

**A. Abuse risks in agentic products** — any product that (1) performs an action on behalf of the user or (2) accesses data as the user. **Named in-scope surfaces: Atlas Browser, Codex, Operator, Connectors, and other agentic ChatGPT tools.** Target label: `Agentic Tools`.
- **IN:** Indirect / third-party prompt injection or untrusted-content attacks that cause an agent to **misuse a Connector or MCP tool** to access, exfiltrate, or transform sensitive data from a bughunter-owned "victim" account, or take a harmful action under it. **For bounty purposes, extracting PII from a user's chat history counts as sensitive private data.** Prompt injections must meet a **realism/feasibility bar; reports relying on victims running clearly malicious or dangerous commands are NOT eligible.** The official launch page sets a **reproducibility bar: ≥50% of the time** for third-party prompt-injection hijacking agents.
- **IN:** Authorization/permission bypasses where an agent accesses Connector/MCP data or performs Connector/MCP actions **beyond what the user, workspace, or app integration permissions should allow (including cross-workspace or cross-tenant exposure).**
- **IN:** Agents performing tool actions **without appropriate user understanding/confirmation**, or where confirmations are **materially misleading** re: what will be accessed/sent/done — especially high-impact actions (sharing/exporting data, changing settings, posting/sending messages).
- **IN:** Misusing an agentic tool to perform a disallowed action: **creating new OpenAI user accounts at scale (≥10 accounts without human interaction).**
- **OUT:** Issues existing **solely in third-party services with no OpenAI-side remediation** (e.g., poorly-annotated third-party MCP servers). The flaw must be in OpenAI systems/config/permissioning/confirmation-UX/integration logic.
- **OUT:** Testing accounts/tenants/data you do not own or lack authorization to test. Any MCP testing must comply with third-party ToS.

**B. Proprietary information** — vulnerabilities or model issues that return OpenAI internal info/IP/confidential data.
- **IN:** Vulnerabilities that return proprietary information related to reasoning — e.g., **full unsummarized Chain of Thought**.
- **IN (belongs to Security Bug Bounty):** vulnerabilities exposing other OpenAI proprietary information (e.g., insider info) — report via Security program.
- **OUT:** Model responses that *appear* to expose proprietary info; **system prompts or any other info present in the model context window at inference time except CoT.**

**C. Safeguards against abuse / platform integrity** (target: `openai.com`).
- **IN:** Meaningful bypass of rate limits / platform controls enabling **sustained usage at significant scale beyond intended limits.** Policy threshold: **≥1,000 completions from the latest model generation across ≤5 accounts within one day on our "Sol" model (any reasoning level).** ("Sol" is the policy's name for the current flagship; treat as codename.)
- **IN:** Vulnerabilities in account-integrity / platform-integrity signals — automating mass account creation, etc. (same 1,000-completion threshold for conversation rate-limit bypasses).
- **IN (belongs to Security Bug Bounty):** exploits allowing access to features/data/functionality beyond authorized permissions — report via Security program.
- **OUT:** Evading geographic access restrictions. Testing that facilitates genuine fraud or requires social engineering (e.g., fraudulent OpenAI Startup Fund accounts).

**D. Case-by-case** (target: `Other`): flaws facilitating a **direct path to user harm** with actionable, discrete remediation steps may be considered in scope for rewards.

### Explicit exclusions (jailbreak / model-output question — VERIFIED)
- **Jailbreaks are OUT OF SCOPE** for this program (stated on both the engagement page and OpenAI's launch post).
- **"All content/model response issues are out of scope"** — disallowed-content generations are not addressable via traditional security fixes. Target: `OpenAI models`.
- "Jailbreaks that result in the model using rude language or returning information easily findable via search engines" are explicitly out (launch post).
- **Exception / note:** OpenAI **periodically runs private bounty campaigns on specific harm types** (named example: biorisk content in ChatGPT Agent and GPT-5) — researchers can apply when they arise. So jailbreak-class work has a channel, just not this public program.

### Bounty table
| Priority | Reward |
|---|---|
| P1 | $5,500 – $7,500 |
| P2 | $2,500 – $3,500 |
| P3 | $750 – $1,500 |
| P4 | $250 – $500 |
| Exceptional/differentiated critical | up to **$100,000** (headline ceiling; press-covered) |

- Note: the engagement's activity feed shows a "$20,000 → $100,000 maximum bounty" announcement dated **March 26, 2025** — that predates the safety program (March 2026 launch), so it is most likely the sibling **Security** program's feed history mirrored on the page. The safety program's tier table and $100k ceiling are confirmed by March 2026 launch coverage. An IDOR bonus (Mar 26–Apr 30, 2025) also appears in the feed — same caveat, likely security-program history.
- Activity visible on page (2026-08-13 / 2026-08-31): accepted submissions on targets `Agentic Tools` (×2) and `openai.com` — program is actively triaging.

### Test accounts & special rules
- **Use test accounts** — safety/abuse testing may trigger enforcement including bans. **No reimbursement** for upgrades/purchases. If rate-limited/blocked, wait for expiry; OpenAI **cannot manually unblock**.
- **Automated vulnerability scanners may trigger enforcement** — avoid loud scanning.
- Test **only your own** accounts/tenants/data. Attack only your own test accounts; never agents operated by real users.
- Authorized testing does **not** exempt you from all ToS; abuse → rate limit/block/ban.
- Prompt-injection reports need realism/feasibility; **no reliance on victim running malicious/dangerous commands**; third-party-prompt-injection hijacks must reproduce **≥50%** of the time.
- MCP/third-party testing must comply with those parties' ToS.
- Leaked `sk-`/`sess-` API keys: per a third-party researcher launch plan (UNVERIFIED vs. policy), report via a **special form, NOT Bugcrowd** — verify on the policy page before using.

### Disclosure rules
- Follows **Bugcrowd's standard disclosure terms**; vulnerabilities in this engagement require **explicit permission via the disclosure-request option** on your submission (see Bugcrowd Public Disclosure Policy).
- **Safe harbor:** good-faith compliance = no legal action from OpenAI (incl. DMCA circumvention claims for eligible services); research is "authorized" under CFAA (and similar state laws); OpenAI waives ToS/usage-policy restrictions **only for the limited purpose of this policy's research**.
- Third-party caveat: OpenAI authorizes research on its own systems only; it **cannot authorize testing of third-party products** and will not defend/indemnify you if a third party sues.
- If unsure whether research aligns with policy, contact **support@bugcrowd.com** before proceeding.
- Extortion/threats = denial of safe harbor. (The 2023 Security program write-ups also note ~90-day disclosure authorization target; UNVERIFIED whether the safety program keeps that exact number.)

---

## 2. Architecture & Tech Surface (public sources, 2026-09-26)

**Consumer products:** ChatGPT web (`chatgpt.com`, `chat.openai.com`), mobile apps (`android.chat.openai.com`, `ios.chat.openai.com`), desktop (`desktop.chat.openai.com`). **Atlas Browser** — OpenAI's agentic browser (named in-scope surface). **Operator** — web-browsing/automation agent. **ChatGPT Agent / Deep Research** — autonomous research agent with high autonomy (reads inboxes, browses, fetches URLs server-side). **GPT-5** is the default model in ChatGPT (business + consumer); policy references the flagship as **"Sol"** model.

**Developer/API platform:** `api.openai.com` (Responses API + legacy chat/completions), `platform.openai.com` (docs/dashboard), OpenAPI spec published (`openai-openapi` repo). Auth: `auth.openai.com` (OAuth2 Authorization Code + PKCE; also issues tokens with scopes like `api.connectors.read` / `api.connectors.invoke` used by Codex). Billing via Stripe; identity via **Auth0** (`auth0.openai.com`) and **WorkOS** (enterprise SSO).

**Codex:** CLI (Rust, open-source at `github.com/openai/codex`, ~125k stars), IDE extensions, web, SDK. Codex CLI logs in via ChatGPT OAuth (PKCE → `auth.openai.com/oauth/...`, tokens in `~/.codex/auth.json`, refresh grant), then hits `chatgpt.com/backend-api/codex/...` with Responses-API/SSE transport, `chatgpt-account-id` and `originator` headers, and Cloudflare challenge cookies on chatgpt.com hosts. Has **sandboxing + approval modes** (suggest/auto-edit/full-auto), `AGENTS.md`/`codex.md` project instructions, memory. **Codex backend was previously hit by a command-injection** (malicious branch names in PR review containers stole GitHub install tokens; disclosed Dec 2025, patched late Jan 2026 — affected ChatGPT website, Codex CLI, SDK, IDE extensions). This is exactly the class the safety program's agentic track now covers.

**Connectors (in-scope attack surface, core to this program):** Settings → Connectors (aka "Apps & Connectors", `chatgpt.com/apps`). First-party connectors include **Gmail, Google Drive, Google Calendar, Google Contacts, Outlook, Teams, SharePoint, Dropbox, Box, GitHub, Linear, HubSpot, Notion, Canva, Figma, Spotify, Apple Music, Uber/DoorDash/Instacart/Expedia/Booking.com/Zillow/OpenTable** (commerce & productivity apps with write/send/book actions). Availability varies by plan (Plus/Pro/Team/Enterprise/Edu; some not in EEA/CH/UK). **Custom MCP servers:** admins can deploy their own MCP servers inside ChatGPT; OpenAI publishes **`tunnel-client`** (Secure MCP Tunnel — connect private/localhost MCP servers to ChatGPT/Codex/Responses API/AgentKit without public exposure). Enterprise connectors promise to respect existing user/org permissions and keep data in-plan.

**File handling:** user content served via `*.oaiusercontent.com` (e.g., `files.oaiusercontent.com`); static assets on `*.oaistatic.com`; canvas/artifacts, uploads, and Codex sandbox file execution (sandbox escapes explicitly **out of scope for the Security program's classic scope** historically — check current policy before pursuing).

**Sharing/collaboration surfaces:** shared conversations/canvas links, custom GPTs, (Workspace/Agent Builder — note Agent Builder is being **deprecated effective Nov 30, 2026** after the AgentForger finding; see §5). Team/Enterprise **workspaces** — the policy explicitly names **cross-workspace / cross-tenant** exposure as in scope.

---

## 3. Third Parties & Partners (from OpenAI's own Help Center allowlist article + public reporting)

| Role | Vendor / domain (public) |
|---|---|
| Identity | **Auth0** (`auth0.openai.com`, `auth.openai.com`), **WorkOS** (`setup.workos.com`, `forwarder.workos.com`, `cdn.workos.com`, `workos.imgix.net`) — enterprise SSO; Google/Apple/Microsoft social login |
| Payments/billing | **Stripe** (`js.stripe.com`) — subscription + API billing |
| CDN / bot defense / WAF | **Cloudflare** (`challenges.cloudflare.com`; CF challenge cookies gate chatgpt.com traffic); static via `oaistatic.com` |
| Email | **SendGrid** (`ct.sendgrid.net`) — transactional email |
| Support chat | **Intercom** (`*.intercom.io`, `*.intercomcdn.com`) |
| Error reporting / RUM | **Sentry** (`*.ingest.sentry.io`), **Datadog** (`rum.browser-intake-datadoghq.com`) |
| Feature flags / experimentation | **Statsig** (`*.statsig.com`, `statsigapi.net`, `events.statsigapi.net`), `*.featuregates.org`, `featureassets.org` |
| Compute | **Microsoft Azure** (Bugcrowd tag on `*.openai.com` target lists "Azure"; OpenAI's infra partnership is public) — primary cloud; also CoreWeave-era GPU capacity per press (UNVERIFIED in this pass) |
| Data/labeling | Scale AI historically (public partnership, UNVERIFIED current status) |

All third-party-only issues are out of scope for the safety program; OpenAI cannot authorize testing of these vendors and they may pursue legal action independently (see Safe Harbor).

---

## 4. Code & Repos (github.com/openai org — public, verified via GitHub org listing 2026-09-26)

**SDKs / API:** `openai-python`, `openai-node`, `openai-go`, `openai-java`, `openai-dotnet`, `openai-ruby`, `openai-cli` (Go), `openai-openapi` (API spec), `homebrew-tools`.
**Agents:** `codex` (Rust CLI, ~126k stars), `openai-agents-python`, `openai-agents-js`, `codex-security` (vuln-finding CLI+SDK), `swarm` (educational orchestration), `symphony` (Elixir — isolated autonomous implementation runs), `tunnel-client` (Secure MCP Tunnel for private MCP servers), `fence`.
**Evals / safety:** `simple-evals`, `mle-bench`, `human-eval`, `prm800k`, plus (per third-party inventory) `frontier-evals`, `model_spec`. `openai-cookbook` (examples incl. Codex SDK safety patterns — e.g., dropping sudo perms so Codex can't read its own API key in CI).
**Models/media:** `whisper`, `tiktoken`, `CLIP`, `point-e`, `shap-e`, `gym`.
**Trust & safety ops:** OpenAI is its own **CVE Numbering Authority** (openai.com/policies/openai-cve-assignment-policy), coordinated disclosure via **disclosure@openai.com** (PGP at cdn.openai.com/security/disclosure.asc.pub), disclosure policy at `openai.com/security/disclosure/`.

Note: `github.com/openai` is listed in the **Security** program's scope ("OpenAI public repositories"). Repo content is primarily useful for understanding connector/MCP permission models and agent sandboxing.

---

## 5. Videos & Writeups (past disclosures / public research — grounding for hypothesis seeds)

1. **ShadowLeak (Radware, disclosed 2025-09-18)** — zero-click Gmail exfiltration via **ChatGPT Deep Research agent**: hidden instructions in an email (white-on-white text) made the agent collect inbox PII, Base64-encode it, and `browser.open()` an attacker URL with data appended — **100% success after tuning**, invisible to enterprise defenses because fetches are server-side. Reported June 2025, fixed early Aug 2025. *This is the archetypal in-scope sub-case 1 finding for the new program.*
2. **AgentForger (Zenity Labs, published 2026-07-23)** — **one crafted ChatGPT link** silently built, authorized, and deployed an attacker-controlled agent inside a victim org: Agent Builder accepted init state (template, prompts, connector attachment, "Never ask" approvals, recurring schedule) **from URL parameters** — no confirmation. The forged agent inherited the employee's email/calendar/storage/Slack/Teams access for persistent exfiltration and impersonation. **OpenAI fixed 2026-06-08; Agent Builder deprecating 2026-11-30.** Root cause: CSRF-style provisioning flaw — exactly sub-case 2/3 (permission bypass + missing confirmation).
3. **Codex command injection (BeyondTrust, disclosed Dec 2025 → patched late Jan 2026)** — malicious branch names executed in Codex PR-review containers, stealing GitHub installation tokens; hit **ChatGPT website, Codex CLI, Codex SDK, IDE extensions**. Classic untrusted-content → agent-execution-escape.
4. **NVIDIA AI Red Team vs Codex (disclosed 2026-04-20)** — indirect **AGENTS.md injection**: poisoned Go dependency detecting Codex envs wrote/overwrote `AGENTS.md` to make Codex silently alter code and hide it from PR summaries. **OpenAI declined to fix** ("no significant risk elevation beyond compromised dependencies"). *Heads-up: OpenAI has a track record of declining some indirect-injection variants — anchor reports on the policy's exact sub-cases (harm + OpenAI-side remediation).*
5. **"Self-replicating prompt injections" writeup (dev.to, 2026-09-25)** — summarizes OpenAI research on injections that propagate agent→agent (email connector → calendar replies; repo "memory compaction" notes stripping security gates). Useful mental model for multi-hop impact stories.
6. **Third-party researcher launch plan** (`github.com/ahkarl13/security`, updated ~8 days ago) — engagement-board mapping with P1 reward bands; treats Agentic Tools/MCP and Codex as lead lanes. **Third-party, unverified** — useful for scoping, not policy truth.
7. **OpenAI's own channels:** engineering blog (`openai.com/index/`), system cards, and the launch post itself; conference talks on MCP/agent security appear in vendor circuits (no specific talk URLs captured in this pass — gap).

**Bugcrowd disclosure activity (from engagement page):** accepted submissions on `Agentic Tools` (×2, 2026-08-31) and `openai.com` (2026-08-13) — program is live and paying, but no public disclosure text was fetched in this pass.

---

## 6. Asset Inventory — passive only (2026-09-26)

**crt.sh attempt: FAILED.** `browser_open` on `https://crt.sh/?q=%25.openai.com&output=json` timed out (upstream fetch failure, no HTTP status). Not retried per task constraints. Inventory below is compiled from **OpenAI's official Help Center domain allowlist** (help.openai.com) and public recon write-ups — **not a fresh CT pull**. Flagged accordingly.

**First-party / likely in-scope (policy target `*.openai.com`):**
- `openai.com`, `*.openai.com`
- `api.openai.com` — primary API endpoint
- `platform.openai.com` — developer platform
- `chat.openai.com`, `chatgpt.com`, `*.chatgpt.com` — consumer app + backend-api
- `auth.openai.com`, `setup.auth.openai.com`, `auth0.openai.com` — identity
- `status.openai.com` — status page
- `*.oaistatic.com`, `*.oaiusercontent.com` (`files.oaiusercontent.com`) — static assets, user files
- `android.chat.openai.com`, `ios.chat.openai.com`, `desktop.chat.openai.com`, `tcr9i.chat.openai.com` — clients
- `cdn.openaimerge.com` — CDN asset host (per Help Center)
- Third-party recon claim (UNVERIFIED): `gateway.unified-*.api.openai.com`, `*.ace.openai.com` (edge infra), `beta.openai.com`, `beta42.api.openai.com` (staging) — from a public GitHub recon write-up citing ~1,800 CT certs; treat as leads, not confirmed.

**In-scope by label but not a host:** `Agentic Tools` (Atlas Browser, Codex, Operator, Connectors, MCP integrations — the actual test surfaces are the products, not a domain), `OpenAI models` (content-output issues — **out of scope**), `Other` (case-by-case).

**Third-party deps (out of scope, listed in §3)** — do not test.

---

## 7. Hypothesis Seeds (grounded in this recon; jailbreak classes excluded per policy)

**H1 — Connector sends email with read-only understanding (misleading confirmation)**
- *Hypothesis:* The Gmail/Outlook connector's permission screen or confirmation summary understates write scope; the agent can **send/share email as the user** when the user believed only read access was granted, or a confirmation renders "summarize inbox" while the tool call sends.
- *Why:* Commerce/productivity connectors have send/book actions; policy sub-case 3 explicitly covers "materially misleading" confirmations on send/share.
- *Expected observation:* A high-impact action completes without a faithful confirmation; tool-call log vs. confirmation text diverge.
- *Class:* confirmation-UX / permission-model flaw → **in-scope (sub-case 3).**

**H2 — Cross-workspace connector data exposure**
- *Hypothesis:* An agent operating in a personal workspace can read Connector/MCP data attached to a Team/Enterprise workspace (or vice versa), or scheduled agents inherit broader connector permissions than the invoking user.
- *Why:* Policy explicitly names **cross-workspace / cross-tenant** exposure as in scope; AgentForger showed connector attachment as the weak seam.
- *Expected observation:* Connector query returns records from a workspace the current context should not access.
- *Class:* authorization bypass → **in-scope (sub-case 2).**

**H3 — Indirect injection → chat-history PII exfil (ShadowLeak class, retest)**
- *Hypothesis:* A new or changed agent surface (Atlas Browser, ChatGPT Agent, or a specific connector like Google Drive/SharePoint) still allows untrusted content to drive the agent to exfiltrate **planted chat-history PII** (policy counts this as sensitive) to an attacker URL, reproducibly ≥50%.
- *Why:* Sub-case 1 is the program's headline category; ShadowLeak was fixed on Deep Research but the class may persist on newer surfaces.
- *Expected observation:* Agent fetches attacker URL with encoded planted PII after reading poisoned doc/email.
- *Class:* third-party/indirect prompt injection → data exfil → **in-scope (sub-case 1).**

**H4 — First-party connector tool shadowing / mis-selection (OpenAI-side)**
- *Hypothesis:* OpenAI's own connector routing or a first-party MCP integration can be steered by tool metadata so the agent selects a more-privileged tool or fills sensitive arguments (e.g., shares to a wider audience than shown).
- *Why:* Must be **OpenAI-side** logic (third-party MCP servers are out); policy covers misuse via OpenAI config/permissioning/integration logic.
- *Expected observation:* Attacker-influenced-but-OpenAI-hosted metadata causes cross-tool data flow the user didn't approve.
- *Class:* integration-logic flaw → **in-scope (sub-case 1/2).**

**H5 — Zero-click exfil via rendered external resources**
- *Hypothesis:* Atlas Browser or an agent surface fetches attacker-controlled URLs embedded in untrusted content (markdown images, link previews) and leaks context (planted tokens/PII) in the request — server-side, invisible to the user.
- *Why:* ShadowLeak's `browser.open()` primitive; "zero-click" increases harm story; must show OpenAI-side missing control.
- *Expected observation:* Outbound request to attacker host carrying planted data, triggered by untrusted content alone.
- *Class:* untrusted-content → exfil → **in-scope (sub-case 1).**

**H6 — Codex workspace escape via untrusted repo content (retest of declined class)**
- *Hypothesis:* A *new* Codex surface (web/IDE/cloud sandbox) executes attacker-controlled repo content (branch names, `AGENTS.md`, MCP configs) beyond guardrails — e.g., reading the user's API key or crossing sandbox boundaries.
- *Why:* Codex is a named in-scope surface; the Dec 2025 command-injection shows the class is real. **Caution:** OpenAI declined the NVIDIA AGENTS.md variant — anchor on demonstrable OpenAI-side remediation and harm (key exfil, sandbox escape), not just "agent followed bad instructions."
- *Expected observation:* Untrusted repo artifact causes execution outside the declared sandbox/approval boundary.
- *Class:* agent sandbox/permission flaw → **in-scope if OpenAI-side (sub-case 1/2).**

**H7 — Full unsummarized Chain-of-Thought extraction**
- *Hypothesis:* A reliable technique exists to elicit **verbatim, unsummarized CoT** from a current flagship model (policy's "Sol" generation), distinct from the normal summarized reasoning.
- *Why:* Explicitly in scope ("full unsummarized Chain of Thought"); **system prompts are explicitly OUT**, so the technique must target reasoning, not system-prompt leakage.
- *Expected observation:* Reproducible method returning raw reasoning traces.
- *Class:* proprietary-information exposure → **in-scope.**

**H8 — Account creation at scale via agentic tool (policy's named disallowed action)**
- *Hypothesis:* Operator/Atlas Browser flows can be driven to create **≥10 OpenAI accounts without human interaction**, or anti-automation signals (CAPTCHA/phone/device checks) are bypassable at that scale.
- *Why:* Sub-case 4 names this exact threshold; it's a P1-band category ($5.5k–7.5k).
- *Expected observation:* ≥10 accounts created with no human interaction via agent-driven flow. **Test only own test accounts; stop at the threshold — bans are likely and unreversible.**
- *Class:* platform-integrity / disallowed action at scale → **in-scope.**

**H9 — Rate-limit bypass at the policy's stated threshold**
- *Hypothesis:* An inconsistency in metering (e.g., between ChatGPT subscription usage and API, or reasoning-level vs. base) allows **≥1,000 completions from the latest generation across ≤5 accounts in one day on Sol** beyond intended limits.
- *Why:* Policy sets an explicit, testable bar — findings below it are out of scope for reward, so this is high-risk/high-effort; validate the threshold math before deep testing.
- *Expected observation:* Sustained completions beyond plan limits without enforcement.
- *Class:* platform-integrity → **in-scope only if threshold demonstrated.**

**H10 — Sharing/file ACL bypass (filed to the SIBLING program)**
- *Hypothesis:* Shared conversation/canvas links, `files.oaiusercontent.com` URLs, or custom-GPT sharing expose data beyond the intended audience (unauthenticated access, IDOR on shared objects, workspace-boundary leak).
- *Why:* The safety policy explicitly routes "access to features, data, or functionalities beyond authorized permissions" to the **Security Bug Bounty** (`bugcrowd.com/openai`) — the two programs reroute, so this is adjacent in-scope work, just on the other engagement.
- *Expected observation:* Shared/private object accessible outside its permission grant.
- *Class:* broken access control → **in-scope for the Security program, not Safety.**

---

## Gaps & caveats
- **crt.sh pull failed** (timeout); subdomain inventory is from official docs + third-party recon claims — get a fresh CT pull before relying on it.
- Sibling **Security Bug Bounty policy** (`bugcrowd.com/openai`) not fetched (page fetch timed out); cross-file H10 there after reading its current scope.
- Bounty-tier table (P1–P4) and $100k ceiling are confirmed; the March 2025 "$20k→$100k" feed item and IDOR bonus are likely the Security program's history — treat as unverified for the Safety program.
- Leaked-key reporting channel (special form vs. Bugcrowd) is from a third-party launch plan — verify on the policy page.
- No specific conference-talk URLs captured; OpenAI engineering blog and system cards are the primary video/blog sources to mine next.
- **Policies change without notice** — re-read `https://bugcrowd.com/engagements/openai-safety` immediately before any testing (2026-09-26 snapshot above).
