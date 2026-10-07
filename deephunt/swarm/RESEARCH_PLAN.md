# DEEPHUNT Swarm — RESEARCH PLAN
**Agent #100 (research director), 2026-09-27.**
Inputs: `WORLD_MODEL.md`, `synth_recon.md`, `synth_app.md`, `synth_diff.md`, `synth_hyp.md`, `memory_91_build.json`, `memory_91_report.md`, `memory_93_dedupe_hyp.md`, `memory_94_lessons.md`, `memory_95_patterns.md`, `memory_96_invariants.md`, `memory_normalized.jsonl` (413 entries), and the raw JSONL evidence files.

Target: `https://ywh-kw-public.bounty.kiteworks.dev` (Kiteworks YesWeHack, passive/low-rate policy).
Success metric: **confirmed, independently reproducible findings per unit of research time.** Everything else = 0.

---

## 1. What the swarm established with confidence

### Actually established (high confidence, independently verifiable)
1. **Program facts**: the hunting host, `-public-yeswehack` UA requirement, scope (Kiteworks Core + EPG + MFT + Forms + API Playground), exclusions (no automated tools, no DoS, no user-data touching), bounty terms ($25k bonus for new unauth RCE-as-root on Core, $50k at CVSS 10.0). Verified by agent 81–83 against the live YesWeHack page.
2. **The host is a hardened React/webpack SPA login shell**: HTTP 200 on `/`, strict CSP/HSTS/frame-ancestors/no-store. No backend fingerprint.
3. **The sandbox cannot reach the target.** Five agents (5, 35, 36, 40, 42) independently confirm CONNECT timeouts from this network; sandbox DNS returns RFC-2544 blackhole addresses. **Zero live experiments have been executed against the hunting environment from anywhere in this swarm.** Every "test" that references live behavior is speculative.
4. **Docs-grade application model**: three-layer authorization (zero-privilege profiles → two-tier admin roles with documented anti-self-promotion guards → six-rung folder roles), chunked upload sessions, async AV/DLP scanning, per-file AES-256-CTR, OAuth 2.0 with 7 legacy grant types, LDAP/SAML/JIT provisioning paths, recipient-share tiers, ICAP-delegated verdicts. All from vendor docs — ungrounded in the live env.
5. **The only target-touching evidence anyone captured**: agent 50's `/login_config` (200, 1190 bytes — auth config: username_password preferred, captcha on, SSO/OAuth empty; `desanitize()` HTML-decodes and strips backslashes from vue_config) and a 49KB `signin.f7b86212.js` chunk with zero sinks in that chunk. 21 other JS chunks unfetched.
6. **The program's own known-issue boundary**: current build uses numeric internal user IDs (→UUID next release); restricted users/recipients must not be able to message other users. This is a live, vendor-acknowledged seam, not a finding.
7. **CVE boundary map (patched, current env claims 9.5.1)**: CVE-2025-53939 (folder member role validation), CVE-2026-23638/24753-24761 (Forms ownership IDORs), CVE-2026-23514 (Core authz bypass), CVE-2026-29092 (EPG session survival), CVE-2026-23635/23636 (Forms transport/upload). Value = variant-test targets only; priors for variants on a patched build are LOW.

### What this is worth, honestly
The swarm produced an excellent **threat model of a Kiteworks deployment in general** and a 97-claim hypothesis inventory with falsifiers. It produced **zero target-specific vulnerability evidence**. The honest scoreboard: **0 confirmed findings, 0 live tests, ~90 hypotheses with no target contact**. Everything below is a plan to convert the pile into live signal.

---

## 2. The 10 highest-value hypotheses, ranked

Ranking = falsifiability × information value × program eligibility × target fit. Rank 1 is the *only* one with any code evidence from the actual target.

| # | Hypothesis | Why it ranks | Confirm/kill | Evidence grade |
|---|---|---|---|---|
| 1 | **`desanitize()` config pipeline → cross-user stored XSS** (agent 50, invariant-adjacent). HTML-decodes and backslash-strips `vue_config` fields (serviceName, labels, disclaimer, link.*, info.*). If any tenant-controlled value lands there and any sink renders it unescaped in *another* user's DOM, that is a real finding with real impact (XSS with PoC required by program). | Only real code captured from the target; tenant-label configurability is designed; sink check is cheap grep work. | Confirm: markup token in a vue_config field renders live in a second account's DOM under the CSP. Kill: all renderers use textContent/React-escaping (inspect remaining 21 chunks). | LOW→MEDIUM (code captured, sink unconfirmed) |
| 2 | **Member-role grant lacks privilege clamping** (H1; CVE-2025-53939 variant class). POST `/rest/folders/{id}/members` roleId not clamped to inviter's role; Manager self-promotes to Owner. | Program-focus privilege escalation; the exact seam that was buggy 9.1.0; cheap 2-account test. | Confirm: GET members shows elevated role + effective owner-only action. Kill: 403/clamp to ≤caller's role. | LOW (docs-grounded; variant-of-patched, L8 discount applied) |
| 3 | **Direct byte endpoints skip Viewer-vs-Downloader split** (H5). Viewer-only identity GETs `/rest/files/{id}/content` → raw bytes. | Program-focus authz; the role ladder's entire purpose is this split; UI enforces it but backend may not. | Confirm: 200 with file bytes for Viewer on a Viewer-scoped file. Kill: 403 or render-only redirect for Viewers. | LOW (docs-grounded) |
| 4 | **"Recipient Only" readable by non-recipient** (H7). Download endpoint validates token but not caller identity vs recipient list (validation is admin-configurable — seam). | The program names this as its own validity line ("you must be able to bypass Recipient Only"); bypass ≠ enumeration. | Confirm: authenticated non-recipient B downloads via token URL. Kill: B rejected while recipient succeeds. | LOW (env default unknown) |
| 5 | **Version-object actions skip per-object write checks** (H6). initiateUpload on another's file_id or versions promote by a Viewer/Downloader. | Upload/authz is Kiteworks' historically buggiest seam; same-name re-upload = new-version design is permissive by nature. | Confirm: B (Downloader) creates a new version on A's file attributable to B. Kill: 403 for non-edit callers on both actions. | LOW (docs-grounded) |
| 6 | **X-Accellion-Version pinning reaches legacy enforcement paths** (H41). Old pinned versions enforce weaker checks; no deprecation schedule published. | If the env honors low version values, every newer check is re-testable under the old pin — a force multiplier across all authz tests. | Confirm: same operation denied on v28 but allowed on an older pin (byte-level response diff). Kill: identical behavior across pins. | LOW (header behavior unobserved) |
| 7 | **JIT/LDAP provisioning skips the create_user admin-strip** (H3). Documented guard covers create_user only; IdP/directory attributes drive role assignment. | If the env uses SSO/LDAP at all, this is a first-login elevation path; single cheap test per path. | Confirm: test account provisioned via JIT/LDAP with privileged mapped attribute lands privileged. Kill: identical strip on all three paths. | LOW (dies if env is local-accounts-only) |
| 8 | **Token classes survive disable/password-change** (H17; CVE-2026-29092 variant class). OAuth refresh, custom-app API, remember-device tokens keep authorizing post-disable. | Precedent exists in this codebase (EPG sessions survived disable pre-9.2.1); cheap per-class matrix with admin control of the test account. | Confirm: any class still authorizes API/download post-disable. Kill: every class fails 401/403 immediately. | LOW (variant-of-patched; needs admin-controlled account) |
| 9 | **Expired/exhausted share link serves via alternate path** (H8). Expiry/download-budget enforced in share-page controller but not direct-download URL, preview, thumbnail, or API path. | Cheap falsifier (create 1-download/1-minute link, re-request all paths); cross-path enforcement gaps are the swarm's most novel reusable pattern. | Confirm: any path returns 200 bytes after expiry/exhaustion. Kill: uniform deny on all paths. | LOW (docs-grounded) |
| 10 | **Login username alters LDAP filter semantics** (H10). Metachar probes vs benign-invalid baseline of equal length; reproducible differential = filter injection. | Program-focus (LDAP injection explicitly listed); single best-armed family in the pool. | Confirm: wildcard/multi-entry effect correlated with filter semantics (not just timing). Kill: identical response class across trials; env uses local accounts. | LOW→MEDIUM IF LDAP is the env auth mode; LOW and dead otherwise |

Deliberately excluded from top-10: all XXE families (zero live contact, untestable), CSRF (one passive cookie inspection kills/advances it first), SQLi (no endpoints mapped), 2FA families (unobserved flows), open-redirect (low impact), EPG mail paths (no inbound path to env), MCP localhost interception (needs shared test host), ICAP fail-open (needs infrastructure control).

---

## 3. Human vs passive testability

### Passive-ready NOW (no accounts, ≤10 spaced requests from an *eligible network* — the sandbox cannot reach the target)
- **P1 — Finish agent 50's JS sink hunt.** Grep the remaining 21 `/static/js` chunks for innerHTML/v-html/dangerouslySetInnerHTML/href-assignment sinks consuming vue_config fields through `desanitize()`. Rank-1 hypothesis lives or dies here. (~2 hours of grep, zero requests beyond chunk fetches.)
- **P2 — Set-Cookie SameSite/HttpOnly inspection** on one unauthenticated GET. Kills or advances the CSRF family instantly. (1 request.)
- **P3 — `/login_config` + `/rest/index.html` live reachability and diff vs docs.** Answers env auth integrations, live API surface. (2–3 requests.)
- **P4 — robots.txt / security.txt existence** (conflict: dossier claims exist, agents saw timeouts — unresolved). (2 requests.)
- **P5 — X-Accellion-Version behavior probe**: one benign read with v28 vs a low pin, diff status/headers. If byte-identical, H6 and the legacy-shim family die cheaply. (2 requests.)
- **P6 — Canary reflection probes** (single safe requests): 404 path echo, login error username echo, `?next=` param echo — all passive reads, no payload beyond a benign marker. These feed the reflected-XSS ranks without touching any account.
- **P7 — Feature-existence sweep**: `/sp/module.php/saml/...`, `/simplesaml/*`, comment endpoints, forms endpoints, `123formbuilder` legacy paths, upload config — one request each, answered 200/404/30x decides which ~30 hypotheses live or die. **Run P7 before any human testing.**

### Human-required (needs accounts, authenticated actions, or infrastructure the program policy reserves for a human researcher)
- **H1–H5, H8 (rank 2–5, 9)**: every confirm test needs **two consenting test identities** (A owner, B low-role) and authenticated API calls. A human registers/provisions them, sets up shares, and holds the admin identity. The agents can *draft* exact request sequences, but the accounts and clicks are human.
- **Rank 7 (JIT/LDAP strip bypass)**: requires **IdP/directory control** (a test IdP feeding attributes) — human-only, and only if the env uses SSO/LDAP at all (P3 answers this first).
- **Rank 8 (token survival)**: requires **admin control of a test account** to trigger disable/password-change, then replay each token class — human orchestrates, agents decode.
- **Rank 10 (LDAP injection)**: needs the env to be LDAP-authenticated (P3 gates it); the metachar probes themselves are low-rate requests a human fires by hand per program rules (no automation allowed by policy).
- **MCP localhost interception (deferred)**: requires a **shared test host** — human infrastructure, out of scope for remote agents.
- **ICAP fail-open / verdict-inheritance families**: need control of or visibility into the env's ICAP/DLP policy — human-only, likely unavailable in a shared hunting env; **defer to wave 2**.
- **NOT allowed, ever**: anything crossing into program-excluded classes (enumeration as a finding, rate-limit "findings", self-XSS, AV-bypass-by-rename, "anyone after authentication" disclosure, DoS, other users' data). Agents must write the non-excluded boundary into each experiment's success criteria before the human runs it.

**Bottom line for the human**: the highest-ROI human investment is not 10 experiments — it is **two test accounts + P1–P7 passive answers**. Until those exist, every confirm test for ranks 2–10 is blocked on unknown preconditions.

---

## 4. What the swarm got wrong or left unexplored

1. **The biggest structural failure: the sandbox has no route to the target, and agents spent request budget anyway.** Agents 35/36/40/42 burned probes on timeouts. Standing rule from here: any agent that cannot complete a TLS handshake in ≤3 attempts must mark its task UNEXECUTABLE and stop — no timeout-sweeping.
2. **Agents 1, 2, 4, 6, 8, 12 (recon) and 24, 27, 29 (app) and 31, 39 (diff) delivered nothing.** 13 of ~80 assigned roles are silent. SQLi stayed weak because nobody mapped listing/report/search endpoints; endpoint mapping was agent 8's job and it never reported. The next wave must re-assign or kill these.
3. **Agent 63 wrote 4 XXE hypotheses with REACHABILITY: NONE** — zero live contact, pure class-prior speculation. It admitted it. Its lesson (L7) is now policy: no hypothesis ships without a reachability label.
4. **~80% of the pool is class-prior-only** (memory_94 L1): "No evidence from this target yet" appears as the honest baseline. The swarm generated breadth, not grounding. The next wave must be forbidden from generating new hypotheses until the P1–P7 passive set converts weak ones to testable ones.
5. **The Airflow claim is unresolved**: agent 23 asserts Airflow-powered MFT from vendor marketing; agent 14 found vendor docs saying proprietary flow engine. Nothing in the swarm should depend on Airflow CVEs — and nothing currently does, good, but the contradiction was never settled. One vendor-page check settles it (passive).
6. **robots.txt / security.txt existence is a direct contradiction** (dossier says exists, GETs timed out). Nobody resolved it. P4 resolves it in 2 requests.
7. **Crypto/protocol internals are untouched**: token format (JWT vs opaque) unknown — one token decode decides the JWT family's fate. TLS config unmeasured (no handshake ever completed from here). Password-reset token mechanics undocumented. Session cookie names/flags unobserved.
8. **The mobile-client differential (agent 43) was never tested**: Viewer no-download on web vs mobile Open-In/offline is a live differential waiting for any reachable network. Nobody ran it because nobody could reach the host.
9. **The `ywh-kw-res-h3.bounty.kiteworks.dev` host is still scope-uncertain.** Same-infra naming is not authorization. Nobody confirmed it in the YesWeHack UI. Do not test it until confirmed.
10. **Over-deduction risk**: 97 "unique testable claims" reads impressive; in reality the set is ~10 seams × variations. The dedupe (agent 93) was good work, but ranks 2–10 above are the honest condensation. The remaining ~85 are not dead — they are gated on P1–P7 — but presenting them as 97 experiment-ready claims would be hype. They are not.

---

## 5. Where the next 100-agent wave should focus

**Do not run another hypothesis-generation wave.** The inventory is complete enough. The next wave must be **evidence-conversion** with a research economy:

**Wave 2A — Passive conversion (agents 1–30), eligible network required, ≤10 spaced requests each, `-public-yeswehack` UA.**
1. P1: finish the 21-chunk JS sink grep (rank-1 hypothesis — this is the single highest-ROI task in the whole swarm).
2. P2–P7 as listed in §3 (cookie attrs, login_config/index.html diff, robots.txt, version-pinning probe, canary reflections, feature-existence sweep).
3. Re-assign the 13 silent roles or close them out with explicit "no data" verdicts.
4. Settle the Airflow contradiction and the robots.txt contradiction; record both in WORLD_MODEL.md.

**Wave 2B — Human gate.**
A human provides: two consenting test accounts, an admin-controlled test account, knowledge of the env's auth mode (LDAP vs local), and confirmation that res-h3 is/​isn't in scope. Without these, Wave 2C cannot start. This is the wave's critical path and it is a person, not agents.

**Wave 2C — Controlled experiments (agents 31–60), only on preconditions cleared by 2A/2B.**
Run rank 2–10 in order, cheapest falsifier first, each through the mandatory ResearchSession workflow (propose_test → adversarial self-check → authorization → dry-run → Engine.execute → rejected/confirmed record). Any hypothesis whose precondition fails is REJECTED with why_failed, not deferred silently.

**Wave 2D — Adversarial verification (agents 61–80).**
Only for confirm-signals from 2C: independent reproduction by a second agent, `compete_finding()` disproof of alternatives, excluded-class boundary check (no user-enumeration/rate-limit/self-XSS/rename-bypass findings), then and only then a human submits via YesWeHack within 24h.

**Wave 2E — Memory/learning (agents 81–100).**
Rejected hypotheses enter rejected-hypothesis memory with the cheap-kill attached (so the next wave inherits the kills, not just the claims). World model gets the live-grounded facts: auth mode, token format, feature inventory, enforced toggles. Technique cards are seeded ONLY from patterns that fired on a live observation (memory_95's 12 seeds are seeds, not cards).

**Resource rule for the director**: 100 agents → but only ~10 agents on ranks 1–10 at any time. The rest are evidence-gatherers for 2A or verifiers for 2D. Breadth without grounding was wave 1's mistake; wave 2 must not repeat it.

---

## Summary

- The swarm built a strong docs-grade threat model and a 97-claim hypothesis inventory with falsifiers, but **zero live tests and zero findings** — the sandbox has no route to the target, and ~80% of hypotheses have no target evidence.
- The top-10 ranked list is led by the only real code evidence captured (`desanitize()` config pipeline → cross-user XSS), followed by nine authz/version/provisioning/token seams; all need a human gate (two test accounts, admin-controlled account, env auth mode) plus a passive conversion pass first.
- Next wave: stop generating hypotheses; run passive conversion (finish the 21-chunk JS grep, feature-existence sweep, cookie/version-pinning probes) → human provides accounts → controlled experiments on ranks 1–10, cheapest falsifier first, rejected paths recorded in memory.

*3-line summary:*
The swarm produced an excellent threat model and 97 hypotheses but zero live evidence — the sandbox cannot reach the target and most claims are class-prior-only. The plan: finish the JS sink hunt on the one real code lead (`desanitize()`), run a cheap passive feature/toggle sweep, then have a human gate provide two test accounts before running the ranked 10 experiments. No new hypotheses until the passive conversion wave turns the pile into grounded, testable claims.
