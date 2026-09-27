# CAMPAIGN STATE — Bug Bounty Deep Hunt
Master state file. Read this first in any fresh session to restore full context.
Last updated: 2026-09-26 (late night IST). Owner: Shivam. Operator: Jarvis.

## Mission
Elite authorized bug-bounty operation. Loop: persistent memory → hypothesis →
adversarial self-check → smallest controlled experiment → observation → learning.
No bug submitted yet. Goal: first valid paid submission, then scale.

## Rules of engagement (standing)
- In-scope, paid programs only. Owned/synthetic test data only. Minimum-safe proof only.
- Every security test runs inside brain/ResearchSession: propose_test() must pass
  (hypothesis + expected observation + reason + scope hosts + auth basis + success/failure
  criteria), adversarial 5-question self-check approves, TestAuthorization minted,
  Engine.execute() refuses anything without a valid token. Findings stay unconfirmed
  until competing explanations are disproven.
- Never persist credential-shaped content. Never spend money without a fresh explicit cap.
- No proactive Gmail checks. OTP: newest code only, never mix, never repeat in chat.
- Live Nation: HUMAN-DISCOVERED bugs only (no bots/scanners/LLM-assisted discovery).
  Agent does intel + report drafting; Shivam operates the browser.
- Wolt + Live Nation: `X-HackerOne-Research: shiva92` header on all traffic (managed
  browser cannot add headers — UI-only traffic needs a policy re-check before claiming eligibility).
- Dry wells stay dry: a target that ate time and gave zero bugs goes to the back of the
  line until something changes (new scope/features/program). Do NOT loop on old targets.
- His corrections are final: stop instantly, no rebuttal.

## Architecture
- `~/workspace/hacker-agent/brain/` — gate.py (TestAuthorization), session.py
  (ResearchSession, persistent to data/brain/sessions/<id>.json), engine.py
  (refuses without valid token, dry-run + scope gate), pipes.md (8-stage pipeline:
  INTAKE → HYPOTHESIZE → ADVERSARY → DESIGN → AUTHORIZE → EXECUTE → OBSERVE → LEARN).
- `brain/test_session.py` — 19/19 pass (2026-09-26). Legacy swarm.py/hunter.py have
  direct-execution paths — DO NOT use for security actions until migrated.
- Proxy/Burp-equivalent harness exists (`proxy/`) but NO live browser traffic has ever
  been routed through it. Do not claim traffic is being watched.

## Findings register

### CONFIRMED (behavior verified, not yet submittable)
- Pinterest: Unicode bidi/homoglyph board-name spoofing — reproducible. Impact story
  too thin for submission as-is; needs a sharper exploit narrative.
- Pinterest: public-pin response-shape oracle — real, but public enumeration alone is low impact.
- Pinterest: secret→public board became visible logged-out immediately; after
  re-secreting, logged-out access failed within <1 min. No render-layer cache persistence.

### LEADS (needs validation)
- GitLab (STRONGEST): job-token allowlist NOT enforced on package-registry endpoints.
  Code-confirmed: routes with `skip_job_token_policies: true` fall back to job-user
  abilities; group/project PyPI, group Composer, npm namespace metadata accept job
  tokens without allowlist checks. Container-registry routes with the same flag ARE
  protected by `job_token_scope: :project` — so this is a gap, not design. REST-only
  (GraphQL rejects job tokens). Needs minimum-safe runtime proof on two owned
  projects/accounts. Live brain session: b73b0af59bd7.
- Aiven: application-user token generate/revoke actions NOT in org audit logs
  (no event types exist). Potential Low, needs retest.
- GitLab Low: job-token-scope allowlist target-path existence oracle (unscoped
  find_by_full_path, distinguishable errors).
- GitLab Low: bulk-import cross-user migration metadata IDOR (unscoped
  BulkImport.find(id) on HTML history/failures paths; API equivalent is user-scoped).

### REJECTED (do not retry without new info)
- Pinterest: CSV formula injection inconclusive (stored/rendered verbatim; raw export
  survival unverified — export requested, cannot cancel; do NOT check Gmail unless asked).
- Pinterest: scheduled-pin/deleted-board desync inconclusive (no scheduling UI option).
- Aiven: 7 rejected — token double-submit, back-button resubmission, trial-credit
  arithmetic (zero drift over 8 cycles), UUID case, existence oracle, CSV formula +
  CHAIN B stored payloads (strict allowlists kill the class at input).
- GitLab GraphQL: 5 suspected seams all clean after code tracing.

### INCONCLUSIVE (needs a new angle or access)
- Aiven: Referer leak (mitigation evidence: referrer=strict-origin), quota ceiling
  (no refusal up to 10 projects), session_id substitution (real authorize endpoint not
  observable), CHAIN A realtime-channel auth (no devtools access).

## Target-by-target status
- Pinterest: DONE 2026-09-26. Cleanup verified (bidi board, sec-pub-race-8, sec-export-test-3,
  sec-sched-test-7 + pins deleted; 7-day restore grace applies). Report:
  intel/pinterest-novel-attacks.md.
- Aiven: DONE 2026-09-26. All synthetic projects/token/app-user/tags cleaned. Trial left
  $50.00/30 days, $0 spent. Report: intel/aiven-novel-attacks.md.
- GitLab: LEAD OPEN. Runtime proof blocked at phone verification for
  attacksurface.alerts@gmail.com. Reports: intel/gitlab-whitebox-ci.md,
  intel/gitlab-whitebox-import.md, intel/gitlab-whitebox-graphql.md,
  intel/novel-attacks-playbook.md (28 ideas, 13 testable).
- Wolt: PARKED 2026-09-26 (his order: "leave it"). Signup started as shiva92@wearehackerone.com,
  magic link sent, browser task closed. W-9 test designed (benign probe `<b>w9probe</b>w9probe`
  on test venue 670e7897e3c56dcc5b5a0989-sh0p) but NEVER authorized/executed. Re-check
  header-policy question before any UI testing.
- Live Nation: MISSION BRIEFED to Shivam 2026-09-26. L-1 flagship: Persona/IDV bypass at
  https://signup.ticketmaster.com/bugbountytest (isolated campaign, test ONLY that URL).
  He operates; agent assists with analysis + report drafting.
- Agoda: DROPPED / DRY WELL 2026-09-26 (his correction). Private program since 2016,
  hundreds of researchers, past hunt yielded nothing. Do not revisit unless he asks.
- Shopify / Snapchat / Uber: passive recon only (recon reports in intel/). Hypothesis
  seeds banked, never hunted. Lower priority than the 10-target operation.

## Active operation (2026-09-26 night)
10-target mega recon: COMPLETE. 10/10 dossiers in intel/<slug>-deep-recon.md (~100 hypothesis
seeds). Synthesis: intel/mega-recon-index.md with ranked top-15 cross-target shortlist.
Top 5: (1) Adobe — indirect prompt injection via shared PDF Spaces → victim AI Assistant
discloses unshared docs (Tier 1 AI bonus, up to $15k, program 25 days old); (2) Arc testnet —
mint-precompile confused deputy via Call From msg.sender preservation; (3) common_codes —
RWSCA PIN-retry race (explicitly invited, Extreme $15k–40k); (4) Adobe — AI session-store IDOR;
(5) chess.com — 2FA pre-auth token regression retest. Suggested order: Adobe → Arc →
common_codes → chess.com → Live Nation ASU. Anthropic (fresh pick replacing Agoda) demoted to
secondary — 5,614 reports/90d, heaviest competition. Friction: Coupang TW needs TW phone;
Live Nation human-only; Arc testnet-only; common_codes ≤2 req/s. First front OPEN 2026-09-26 night: Adobe H1 (indirect prompt injection across PDF Spaces share boundary).
ResearchSession 3dd56620321b — H1 (score 80), T1 approved + authorization minted.
Phase 1 (browser): Intigriti signup, test-plan extraction, 2 self-owned Adobe IDs. No payments/trials.
DEEPHUNT (deephunt/): autonomous hunter program — `python3 deephunt.py --target <name>`.
Loop: INTAKE -> INTERNET (fresh techniques) -> FUNNEL -> HYPOTHESIZE (novel only) -> ADVERSARY/DESIGN -> AUTHORIZE -> EXECUTE -> OBSERVE -> LEARN -> repeat until vuln or exhausted.
13 tools wired (8 passive, 4 gated active, 1 operator); learns from data/brain/sessions + intel reports + proxy logs so it never retries killed ideas. Active tools BLOCKED until test plan read.
Arsenal (ops/WEAPONS.md): Burp-equivalent proxy LIVE (mitmproxy 12.2.3, chained, HTTPS validated; proxy/start.sh); nuclei v3.11.1 LIVE (ops/bin/nuclei); nmap installing. ACTIVE scanners holstered until Adobe test-plan rules are read (phase 1) — firing blind risks a program ban.
Phase 1b DONE 2026-09-26: intel/adobe-endpoint-funnel.md (21KB) — 10 in-scope hosts (incl. *.wopi.acrobat.adobe.com), ~60 route/param points, 8 grounded seeds SH1–SH8. SH5 (owner custom-assistant instructions execute in victim's PRIVATE chat — designed channel, no injection needed) now outranks H1's poisoned-document variant. SH1–SH4 rest on dc-api-v2.adobe.io (out-of-scope evidence only until test plan confirms). Seeds fed to deephunt/targets/adobe.yaml + session 3dd56620321b.
Phase 1b (JS bundle recovery queued): passive JS/API endpoint mapping of acrobat.adobe.com -> intel/adobe-endpoint-funnel.md (the funnel: inventory -> interesting -> sensitive -> unusual -> hypotheses).
Standing methodology: brain/methodology.md (Shivam's funnel doctrine, 2026-09-26). Recon wide, hunt deep, one target at a time.

## Attack paths & types catalog (tried or designed to date)
Bidi/homoglyph spoofing, response-shape oracles, cache-timing races, CSV formula
injection, token double-submit, back-button resubmission, credit/quota arithmetic,
UUID case sensitivity, existence oracles, Referer leakage, session substitution,
realtime-channel auth, stored-payload chains, OAuth redirect/PKCE/code-replay,
OIDC reflection, offline-token scoping, share-link GraphQL authz, universal-link
state actions, trip state-machine transitions, OTP/MFA bypass designs, IDOR patterns,
Persona/IDV bypass (planned), SafeTix bypass (planned), job-token scope escapes.

## Blockers / waiting on Shivam
1. Live Nation L-1: his hands on the Persona flow; send screenshots of anything odd.
2. GitLab runtime proof: phone-verified test account (attacksurface.alerts@gmail.com stuck).
3. Wolt: parked by his order — magic link only if he reopens it.
4. Pinterest data export: submitted, cannot cancel — do not check Gmail unless he asks.

## Plans & reports index
- intel/deep-hunt-plan.md — 29 attacks (Wolt W-1..W-9, Live Nation L-1..L-10, Agoda leftovers)
- intel/easy-bounties-shortlist.md — ranked 10 (basis for the mega recon)
- intel/mega-recon-index.md — PENDING (coordinator synthesizes on completion)
- Research identities: hackerone shiva92 / shiva92@wearehackerone.com; research Gmail
  attacksurface.alerts@gmail.com (password transient, never stored — remind to rotate).

## 2026-09-27 — DEEPHUNT upgrade (26 tools, trained brain, daemon mode)
- Arsenal: subfinder v2.16.0, httpx v1.12.0, gau v2.2.4, ffuf v2.3.0, katana
  installed to ops/bin. Adapters now 26: 17 passive (+subfinder, httpx, gau,
  urlscan, js_secrets, takeover, cors_probe, tls_info, param_miner), 8 gated
  active (+ffuf, katana, graphql_probe, dns_axfr), 1 operator.
- Brain: think.py — 7 thinking modes (predator, architect, accountant,
  saboteur, ghost, scholar, oracle) interrogate the same evidence; council
  dedupes vs memory, diversifies, ranks. train.py matches funnel signals
  against knowledge/techniques.yaml (41 cards, 21 classes). knowledge/
  past_attacks.md holds bounty shapes that keep paying.
- Resources fed: intel/*.md reports, internet seeds, proxy tried-paths,
  brain session lessons, target profile — all feed the council.
- Daemon: `deephunt.py --target X --daemon --interval-hours H` runs until
  state/STOP; crashes caught and survived. Every run writes
  state/<target>_postmortem_<ts>.md; gaps accumulate in deephunt/ROADMAP.md.
- Fixed: targets/adobe.yaml YAML scanner error (unquoted `SH1:`-style seeds
  parsed as mappings) — seeds now quoted, 11 parse clean.
- Adobe still passive-only (active_allowed: false) until the Intigriti test
  plan is read.

## 2026-09-27 02:28 IST — Robinhood hunt started
- Official "Robinhood Markets Bounty" policy verified from hackerone.com/robinhood (paid program, >$460k paid; Tier 1 Critical $10k-$25k).
- Scope file: deephunt/targets/robinhood.yaml (14 scope hosts, out-of-scope list, excluded finding types).
- Mandatory X-Bug-Bounty: shiva92 header auto-injected by proxy rule robinhood-bounty-attribution.
- Daemon restarted: targets=robinhood,shopify,yahoo. ResearchSession 9fa7d08c88bf open, INTAKE phase running.
- NOTE: X-Test-Account-Email header pending — Shivam needs to create a Robinhood test account for authenticated testing.

## 2026-09-27 ~08:05 IST — CLI + GUI + identity module built (user: "give him cli and gui let him think see execute")
- deephunt/cli.py: status/start/stop/targets/identities/sessions/findings/log/signup
- deephunt/gui.py: stdlib-only dashboard on 127.0.0.1:5059 (localhost only) — overview/targets/identities/sessions/findings/logs + daemon start/stop + signup brief generator
- deephunt/identity/: manager.py (metadata-only registry, email convention attacksurface.alerts+<target>@gmail.com), driver.py (playbook -> browser-task brief), playbooks/_template.yaml, CAPTCHA.md (honest strategy doc)
- Passwords NEVER stored in code/logs/memory — Secure Vault only via user-set secure cards; browser fills from vault at sign-in.
- Hard stops: KYC/PII (SSN, ID docs, payment) halts automation -> user.
- CAPTCHA: runtime preference (solve/user_handles/ask); paid solvers need explicit cap — NOT enabled.
- Pending: Robinhood signup-flow study (browser task running) -> playbooks/robinhood.yaml
