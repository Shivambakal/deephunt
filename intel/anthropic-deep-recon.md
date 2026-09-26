# Anthropic Public Bug Bounty — Passive Deep Recon

**Date:** 2026-09-26
**Author:** passive-recon subagent
**Program:** https://hackerone.com/anthropic (product/infrastructure security program — PUBLIC since 2026-05-08; previously invite-only)
**Out of scope for THIS hunt:** model safety / jailbreaks (separate programs: hackerone.com/anthropic-cyber-jailbreak for Fable cyber-jailbreaks; modelbugbounty@anthropic.com for all other models)

> Verdict codes used below: **[LIVE]** = confirmed on hackerone.com/anthropic today; **[SECONDARY]** = claims from hunter GitHub guides citing the H1 scope CSV (May 2026), not directly re-verified; **[UNVERIFIED]** = single-source or inference, needs confirmation before acting.

---

## 1. Live policy (from https://hackerone.com/anthropic, read 2026-09-26)

### Asset scope **[SECONDARY + partial LIVE]**
The live policy page's text render did **not** include the asset table section (HackerOne loads it separately), so the table below is from a secondary hunter source that claims to quote the H1 scope CSV as of May 2026 (ml-ke/ml-ke, `_atlas_backups/2026-06-03/skills/bug-bounty/anthropic-bug-bounty/SKILL.md`). Program stats on the live hacktivity page say **"Assets In Scope: 14"** **[LIVE]**. Treat the secondary table as directionally reliable but re-check the live Scope tab before submitting.

**Core assets (bounty-eligible)** [SECONDARY]:
| Asset | Type | What to test |
|---|---|---|
| `claude.ai` | URL | Web app: XSS, CSRF, auth bypass, IDOR, file upload |
| API & SDKs | AI_MODEL | API auth, API-parameter injection, SDK vulns |
| Official Clients | OTHER | iOS/Android/Desktop — MCP integrations, local storage, IPC |
| **Claude Code** | OTHER | **Hot target** — permission-model boundaries (see §5) |
| `console.anthropic.com` | URL | Developer console — API key mgmt, workspace mgmt |
| `api.anthropic.com` | URL | API endpoint testing |
| Leaked Employee API Keys | OTHER | Publicly leaked keys — authenticate then immediately de-auth |

**Non-core (may still be bounty-eligible)** [SECONDARY]:
| Asset | Notes |
|---|---|
| `github.com/anthropics` | Source code; archived repos/forks excluded unless impact on Anthropic assets shown |
| `docs.anthropic.com` | Docs site |
| `support.anthropic.com` | Support portal |
| `anthropic.atlassian.com` | Jira — 4 queues intentionally accessible externally |
| Infrastructure & Internal Apps | Auth bypass, privesc, exposed internal services |
| Claude Desktop Extensions & Claude.ai MCP servers | Anthropic-developed connectors only (not third-party) |

**Explicitly OUT of scope** [SECONDARY]:
- **`github.com/modelcontextprotocol`** — OSS MCP code goes to MCP maintainers; Anthropic's *implementation* of MCP (in Claude.ai/Desktop) IS in scope under those assets.
- **All customer domains under `*.supabase.co`** — customer projects.

### Bounty table [LIVE — from the hacktivity page reward footer, 2026-09-26]
| Severity | Range | Avg. paid | Share of submissions |
|---|---|---|---|
| Low | $100 – $750 | $186 | 17.87% |
| Medium | $250 – $2,500 | $876 | 41.07% |
| High | $1,000 – $5,000 | $3,384 | 39.68% |
| Critical | $3,000 – $10,000 | $7,200 | 1.39% |

Note: the "$50 minimum" figure from context was **not** found anywhere on the live pages — the live table bottoms at $100 (Low). Special rules pay fixed $100 (doc-update findings; third-party-coordinated fixes) [LIVE]. Only 1.39% of submissions reach Critical — duplicates are the main killer: **5,614 reports received in 90 days, 466 resolved, 532 hackers thanked, $1,070,485 total paid** [LIVE]. Assume heavy competition; pick zones where duplicates are less likely (console business logic, Admin API boundaries, newer features).

### Special rules [LIVE — verbatim from policy]
- Must use `@wearehackerone.com` email for test accounts + `X-HackerOne-Handle: <handle>` header on requests.
- One vuln per report (chain to show impact when needed). Duplicates: first reproducible report wins. One underlying issue = one bounty.
- **AI-written/scanner slop closed as Not Applicable** at Anthropic's discretion — must validate + provide working PoC.
- Research Preview/Beta features treated as **non-core for 1 month** after initial release.
- GitHub Action vulns in in-scope repos = **non-core** unless impact on core assets shown.
- Public 0-days patched <7 days: case-by-case.
- **Permission-modal bypass in Claude Code is under active remediation** — reports welcome but "likely closed as duplicates if fixed by this effort."
- Auto-accept-edits modifying CWD files that other software then executes = **user's responsibility, not a vuln**.

### Explicitly out-of-scope classes [LIVE]
General/TLS best-practice without PoC; physical; rate-limit/brute-force on **non-authenticated** endpoints; insider; social engineering; reflected file downloads; account takeovers/brute-force on others' accounts; DoS; clickjacking without sensitive actions; missing HttpOnly/Secure flags; dependency hijacking; publicized 0-days with no patch or patched <30 days. **Model content/jailbreaks/hallucinations out of scope for this program** [LIVE].

### Disclosure [LIVE]
HackerOne disclosure guidelines; researchers' right to public disclosure supported, but coordinate timing and get **written confirmation** before disclosing; may report similar vulns in other orgs freely. Contact: bugbounty@anthropic.com. Acknowledge within 3 business days.

---

## 2. Architecture & tech stack

**Consumer web (`claude.ai`)** [SECONDARY/source: hunter guide]: Next.js SPA. Auth via Google SSO + email magic link [UNVERIFIED — general knowledge, not re-checked this session; auth flows are historically magic-link/Google OAuth].

**Anthropic API (`api.anthropic.com`)** [SECONDARY, from mirrored docs 2026-07/08]:
- Required headers: `x-api-key` (Console key) **or** `Authorization: Bearer <token>` (short-lived, from `POST /v1/oauth/token` via **Workload Identity Federation**), plus `anthropic-version` (e.g. `2023-06-01`) and `content-type: application/json`.
- Keys are long-lived (`sk-ant-api03-...`), user-chosen expiration at creation, managed at Console → Settings → API keys.
- **Workspaces** segment keys; multi-workspace keys require `anthropic-workspace-id` header per request — a real trust-boundary surface.
- **Admin API** (`/v1/organizations/...`, e.g. `GET /v1/organizations/cost_report`) takes Admin API keys, OAuth `org:admin` tokens, or personal/service keys *not* workspace-scoped; never returns secret values (redacted hints only). Roles: organization admins vs members — key management is admin-only.
- Cloud-platform access (AWS Bedrock / GCP Vertex / Azure) is IAM-integrated, not API-key — separate surface.
- MCP: Claude supports MCP servers on claude.ai/Desktop; only **Anthropic-developed** connectors are in scope (third-party connectors and `github.com/modelcontextprotocol` are out).

**Console (`console.anthropic.com`, now also `platform.claude.com`)**:
- Org → Workspaces → API keys hierarchy; roles (admin/member), SSO/SAML for enterprise orgs [SECONDARY/general].
- Billing: usage-based API billing; subscription plans for Claude Code draw from subscription usage limits (per community docs: Anthropic paused the separate Agent SDK credit plan as of June 15, 2026 update) [SECONDARY].
- Subdomain observed in CT logs: `api.console.anthropic.com` (Let's Encrypt) [LIVE/observed 2026-09-26].

**Claude Code** [from Anthropic engineering content + community verification]:
- Agentic coding CLI; **layered permission model**: auto (reads), ask-per-turn (bash/file-write/network), explicit allowlists, deny rules; `--dangerously-skip-permissions` flag; `.claude/settings.json`, CLAUDE.md trust files.
- OS-level sandbox: **Seatbelt (macOS), bubblewrap (Linux)** — reads allowed, writes confined to workspace, **network denied by default**; open-sourced runtime at github.com/anthropic-experimental/sandbox-runtime; sandboxing cut prompts ~84% (per Anthropic engineering article mirrored on GitHub).
- Verified sandbox baselines (community ADR, 2026-05-19, Claude Code 2.1.x): sandbox layer denies `~/.aws/*`, `~/.ssh/*`, `~/.netrc`, `~/.npmrc`, `~/.docker/config.json`, `~/.kube/config`, `~/.config/gh/hosts.yml`; tool-layer baseline denies `.bashrc`, `.bash_profile`, `.gitconfig`, `.gitmodules`, `.idea`, `.mcp.json` — but `.env`/`.envrc`/`*.key`/`*.pem` were **verified absent** from both baselines at that time (user-side enforcement needed).
- Known-patched CVEs to avoid re-finding (from hunter skill, not individually verified): CVE-2025-59536 (settings-file RCE via hooks, v1.0.111), CVE-2026-21852 (API key exfil via env injection, v2.0.65), CVE-2026-33068 (trust dialog bypass via `permissions.defaultMode`, v2.1.53), GHSA-5hhx-v7f6-x7gv (yarn plugin pre-trust exec), `claude-cli://` deep-link RCE (v2.1.118), sandbox symlink escape, git worktree trust bypass, git-config `user.email` RCE, IDE WebSocket origin bypass, SDK-TS world-readable memory files. **All dead ends — do not resubmit.**
- Claude Code SECURITY.md (github.com/anthropics/claude-code, updated 2 days before 2026-09-26) routes vuln reports to this same H1 program [LIVE/observed via search].

**Official clients**: iOS/Android/Desktop apps; Desktop extensions and Anthropic-built MCP servers in scope [SECONDARY].

---

## 3. Third parties & partners

| Party | Role | Evidence level |
|---|---|---|
| **Google Trust Services** | TLS issuance for `*.api.anthropic.com`, `events.certification.anthropic.com`, `api-release-candidate.anthropic.com` (all WR3) — certs terminated at/through Google infra, suggesting GCP load balancing | Observed in CT logs 2026-09-26 |
| **Let's Encrypt** | TLS for `anthropic.com`, `claude.anthropic.com`, `support.anthropic.com`, `assets.anthropic.com`, `api.console.anthropic.com`, `*.tunnel.anthropic.com` | Observed in CT logs 2026-09-26 |
| **Amazon (RSA 2048 M01 CA)** | At least one host (`prod-rudolph.he.anthropic.com`) on Amazon-issued certs — AWS presence | Observed in CT logs 2026-09-26 |
| Stripe | Console billing payment processor | **UNVERIFIED** this session (widely reported; confirm before use) |
| Supabase | Customer-domain hosting excluded from scope (`*.supabase.co` OOS) | Per [SECONDARY] scope table |
| Google SSO | Consumer auth option on claude.ai | **UNVERIFIED** this session |
| Atlassian (Jira) | `anthropic.atlassian.com`, 4 queues intentionally external | Per [SECONDARY] scope table |
| Cloudflare, Mozilla, Microsoft, Linux Foundation | Project Glasswing defensive-cyber partners (defensive use of Claude Mythos) | Press 2026-09 (not a testing surface) |

No CDN/WAF vendor was directly verified this session; Google-issued certs on API infra point to Google Cloud fronting — treat as inference, not fact.

---

## 4. Code & repos

**`github.com/anthropics`** [observed via search; org is real and in scope]:
- `anthropics/claude-code` — main repo (hooks examples, plugins, CHANGELOG); SECURITY.md → this H1 program
- `anthropics/claude-code-action`, `anthropics/claude-code-security-review` — GitHub Actions (**policy: Action vulns = non-core unless core impact shown**)
- `anthropics/anthropic-sdk-python`, `anthropic-sdk-typescript` (assumed; TS SDK named in sources as `anthropic-sdk-typescript` — verify exact name on the org page before citing)
- `anthropics/claude-agent-sdk-python`, `anthropics/claude-agent-sdk-typescript`
- `anthropics/skills` (public skills repo), `anthropics/claude-cookbooks`
- `anthropics/sandbox-runtime` (as `anthropic-experimental/sandbox-runtime` per mirrored article — org naming unverified; check both)
- archived repos/forks excluded from scope unless impact shown

**`github.com/modelcontextprotocol`** — explicitly OUT of scope; report there, not to Anthropic.

**SDK security notes (from hunter deep-audit summary, [SECONDARY])**: June 2026 audit of 80+ source files concluded SDKs were secure and platform endpoints auth-gated; the residual surface was "authenticated multi-account testing." The audit's full conclusions file was **not retrievable** (404 on the mirrored path) — only the SKILL.md summary was visible. A prior submission from that effort (SSRF in MCP Fetch + WebFetchTool) was closed **Informative** because (a) MCP Fetch is under the OOS `modelcontextprotocol` org, and (b) the permission prompt *is* the security boundary — the lesson: **don't submit agent-SSRF to Anthropic; the vuln is bypassing or misrepresenting the prompt, not what happens after approval.**

---

## 5. Videos, talks & writeups

- **Anthropic engineering: "How we contain Claude"** (patterns for sandboxing AI agents; mirrored at github.com/byteflare-co/anthropic-engineering-ja/articles/en/25_how-we-contain-claude.md) — describes the Claude Code human-in-the-loop sandbox (Seatbelt/bubblewrap), the custom-proxy incident, and the 84% prompt-reduction result. **Read this before touching Claude Code targets** — it documents intended boundaries.
- **Anthropic engineering blog** (anthropic.com/engineering): "Making Claude Code more secure and autonomous" (2025-06-15), "Claude Code: Best practices for agentic coding" (2025-02-24), "Code execution with MCP" (2024-11-04) [titles from secondary source list — verify on anthropic.com/engineering].
- **Community security research**: `toku345/dotfiles` ADR-0001 (sandbox deny-baseline verification, 2026-05-19); `freepeak/devagent` 2026-09-11 Claude Code competitor notes (GH Action OIDC workload-identity-federation details: `anthropic_federation_rule_id`, subprocess secret scrubbing, bubblewrap PID isolation).
- **News (Sept 2026)**: Hacktron AI used Claude to chain a heap-overflow + SSO bug into OpenAI's community forum → employee ChatGPT accounts → private GitHub (WSJ, Sept 18, 2026; $6,500 OpenAI bounty). Relevance: forum/community components + SSO token scoping are proven high-value chains at AI labs — and Anthropic's own `support.anthropic.com` (Zendesk-class) and `anthropic.atlassian.com` (Jira, 4 external queues) are in-scope analogues.
- **Disclosed Anthropic H1 reports**: **none found publicly** this session. The live hacktivity page shows ~20 resolved reports in the last 3 weeks (bounties $250–$4,700, frequent reporter `amr_id`, `liamconner10` with two $4,700 payouts, collaborations involving `hacktronresearch` 2 days ago) but titles/details are private [LIVE]. Active hunters are clearly finding Highs ($3,700–$4,700) regularly — the program is alive and paying.
- **June-2026 deep-audit notes**: only the SKILL.md summary visible; conclusions file 404'd — claims (Claude Code hardened, SDKs secure, need multi-account testing) are **single-source, unverified**. Treat as one hunter's opinion, not ground truth.

---

## 6. Asset inventory — passive (crt.sh, 2026-09-26)

Method: read-only `browser_open` on `https://crt.sh/?q=%25.anthropic.com&output=json` (no probing, no auth, no scanning). Result set was large (~8,267 log lines); sampled the newest entries. Notable hosts, grouped:

**Core-adjacent / product:**
- `anthropic.com`, `claude.anthropic.com`, `support.anthropic.com`, `assets.anthropic.com`, `legal.anthropic.com`
- `api.console.anthropic.com` — console backend API surface (correlates with "console team/role management" hypothesis zone)
- `sandbox.api.anthropic.com`, `sandbox.staging.api.anthropic.com` — sandbox API (staging + prod)
- `api-release-candidate.anthropic.com` — RC API environment
- `*.tunnel.anthropic.com` + `tunnel.anthropic.com` (wildcard cert) — tunneling service; interesting but test only via in-scope assets

**Inference/ML infra (service names worth knowing for API shape, not test targets per se):**
- `stt-nova3-s{1,2,3,4,5,7,8}.titanium.api.anthropic.com` (+ `-staging` variants) — speech-to-text service ("nova3" = new model family codename?; "titanium" = internal API infra codename)
- `stt-flux-multi-chs2.titanium.api.anthropic.com` / `-staging`
- `prod-rudolph.he.anthropic.com` (Amazon-issued) — "he" likely human-eval; internal

**Corporate/other:**
- `events.certification.anthropic.com`
- `url8792.mail.anthropic.com` — mail-tracking (Iterable/SFMC-class; not a vuln surface)

**Takeaway:** the `titanium.api.anthropic.com` tree shows a large internal service mesh behind the public API; staging hosts exist under the same namespace (`*-staging.api.anthropic.com`) — scope-wise, confirm with the program whether staging counts as `api.anthropic.com` before touching. `api.console.anthropic.com` is the highest-value named host for console business-logic hypotheses.

---

## 7. Hypothesis seeds (all in-scope classes only; no model-safety/jailbreak content)

**H1. Workspace-boundary confusion on the API (api.anthropic.com).**
*Hypothesis:* Requests carrying `anthropic-workspace-id` with a key valid on multiple workspaces may act on the wrong workspace if the header is ignored or defaulted server-side (e.g., admin endpoints, key listing, cost reports).
*Why:* Multi-workspace keys + a workspace-selection header = classic confused-deputy shape; Admin API is the money/key surface.
*Expected observation:* With two owned workspaces, set header to workspace B while key context is A; observe data/actions attributed to A.
*Class:* IDOR / broken access control (High).

**H2. Console role escalation: member → key/admin operations (api.console.anthropic.com / console.anthropic.com).**
*Hypothesis:* Org-member-scoped sessions may reach admin-only console API routes (key create/revoke, member invite/role change, SSO config) via direct API calls even if the UI hides them.
*Why:* Console is the key-management trust boundary; Atlassian/Jira queues are externally reachable, suggesting broad internal exposure.
*Expected observation:* As org member, replay admin-only endpoints observed in traffic; 200/201 where UI would forbid.
*Class:* Privilege escalation (High).

**H3. Admin API key-scope confusion: workspace keys on organization endpoints.**
*Hypothesis:* Docs say workspace-scoped keys "don't work" on Admin API — but partial failures (e.g., list works, create fails; or error messages leak org metadata) are a common seam.
*Why:* Explicitly documented boundary = high signal; any deviation is a finding.
*Expected observation:* Workspace-scoped key against `/v1/organizations/*` endpoints returns data instead of clean 401/403, or verbose errors disclosing org IDs, member emails, key hints.
*Class:* Broken access control / info disclosure (Medium–High).

**H4. Artifact/file-handling stored XSS via conversation file render (claude.ai).**
*Hypothesis:* Files uploaded to conversations (docs, images, HTML/SVG) may be rendered or offered for download with unsafe `Content-Type`/`Content-Disposition`, giving stored XSS in the victim's session when a shared conversation or artifact link is opened.
*Why:* claude.ai is a Next.js SPA rendering rich model output; file upload/download is explicitly named in scope; sharing features widen the victim set.
*Expected observation:* Upload HTML/SVG; download or preview URL serves it inline as `text/html` without `Content-Disposition: attachment` or sandboxing.
*Class:* Stored XSS (High).

**H5. Claude.ai conversation/project sharing IDOR.**
*Hypothesis:* Share links, shared projects, or published artifacts may be enumerable or accessible cross-account (unguessable-token bypass via IDOR on the underlying object ID, or shared-with-me list leakage).
*Why:* Object-level sharing is the #1 historical IDOR zone in collaboration apps; Anthropic's surface is share-heavy.
*Expected observation:* As account B, request account A's conversation/artifact by numeric/UUID ID without the share token; data returned.
*Class:* IDOR (High).

**H6. OAuth/SSO account-linking takeover on claude.ai / console.**
*Hypothesis:* The Google-SSO/email-magic-link account linking flow may allow pre-hijacking: creating an account with a victim's email via one method, then the victim's SSO login merges into (or fails to reclaim) the attacker-created account.
*Why:* Multi-method auth (SSO + magic link) on the same identifier is the classic account-linking vuln shape. Note policy excludes "brute-force ATO on others' accounts" — this must be demonstrated strictly on owned test accounts with `@wearehackerone.com` emails.
*Expected observation:* Controlled A/B test: attacker creates account via magic link for victim-email (owned), victim SSO-login behavior differs from clean baseline (merge vs. new account vs. takeover).
*Class:* Authentication bypass / account linking flaw (High–Critical). **Caution:** stay within owned accounts only.

**H7. Claude Code: permission-prompt *misrepresentation* via URL-parser differential (not prompt bypass).**
*Hypothesis:* WebFetch or a tool prompt may *display* a normalized URL while *fetching* a different one (redirect handling, unicode/credential-info in authority, DNS-rebinding between display and fetch) — i.e., the prompt lies about what it does.
*Why:* In-scope per program: "misrepresenting parameters or tools in permission prompts" is explicitly bounty-eligible; raw prompt bypass is under active remediation (dup risk) — misrepresentation is the fresher angle.
*Expected observation:* Prompt shows URL X, network fetch goes to Y (own controlled domains for both ends); user approval was for X.
*Class:* Security boundary bypass (High). **Do not submit plain WebFetch SSRF — closed as Informative.**

**H8. Claude Code: plugin/MCP `canUseTool` bypass.**
*Hypothesis:* Plugin-installed MCP servers may skip the permission callback chain entirely (referenced as a 6+ month open issue in hunter notes) — a tool executing with zero prompt.
*Why:* Third-party MCP servers are the least-trusted code running inside the trusted CLI; any gap in the callback chain = silent execution.
*Expected observation:* Install a test MCP server (own code) exposing a sensitive tool; invoke via prompt; no permission dialog appears and the tool runs.
*Class:* Permission bypass (High–Critical). **Verify it's not the documented auto-accept/preapproved behavior first.**

**H9. Usage/billing metering manipulation (console.anthropic.com).**
*Hypothesis:* Usage metering or spend-limit enforcement may be client-computed or eventually-consistent in a way that lets spend limits be bypassed (e.g., workspace spend caps not enforced on streaming or on specific endpoints like batch/files).
*Why:* Money logic is in scope; only 1.39% of reports are Critical — billing bypass is a known Critical-shaped finding at API companies.
*Expected observation:* With a $0/low spend cap on an owned workspace, run metered calls; observe whether enforcement blocks or bills.
*Class:* Business logic (High–Critical). **Keep spend at $0; document without incurring charges.**

**H10. Anthropic-built MCP connector / Desktop extension token handling.**
*Hypothesis:* First-party connectors (e.g., Google Drive/GitHub connectors on claude.ai, Desktop extensions) may store or transmit OAuth tokens insecurely, or the connector auth callback may be hijackable (redirect_uri manipulation, `state` reuse) to bind a victim's third-party account to the attacker's Claude session.
*Why:* "Claude Desktop Extensions & Claude.ai MCP servers (Anthropic-developed)" are explicitly in scope; OAuth callback flaws are evergreen.
*Expected observation:* Intercept own connector OAuth flow; mutate `redirect_uri`/`state`; observe whether the flow completes bound to the wrong session.
*Class:* OAuth flaw (High).

---

## Caveats & next steps
- **Policy freshness:** hackerone.com/anthropic policy text verified 2026-09-26; Anthropic can change it without notice — re-read the live Scope tab before testing/submitting. The 14-asset table could not be rendered from the live page today; the table in §1 is secondary-source.
- **Highest-value / lowest-dup zones:** console/Admin API trust boundaries (H1–H3, H9), prompt *misrepresentation* (H7), plugin MCP permission chain (H8), OAuth connector flows (H10). Avoid: raw permission-modal bypass (active remediation → dup risk), any modelcontent/jailbreak angle, scanner slop.
- **Program hygiene for any live work:** `@wearehackerone.com` test accounts only, `X-HackerOne-Handle` header on requests, owned accounts only, working PoC required, no data retention, coordinate disclosure with written confirmation.
