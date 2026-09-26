# THE ADVANCED STUDY — Master Synthesis of the 2026-09-26 Operation

**Date:** 2026-09-26 (all statuses below are as of this date)
**Method:** `~/workspace/hacker-agent/deep-vuln-methodology.md`
**Headline:** **Zero confirmed vulnerabilities above Low.** Ten intel reports banked, three authenticated hunts running, one unauthenticated surface fully clean. Every item below is marked with its evidence status. No lead has been upgraded to a finding.

This is a **living document** — update statuses as probes resolve. Evidence status vocabulary: `CONFIRMED` (reproduced with evidence), `LEAD` (passive evidence only, needs probing), `PROBING` (assigned to a live authenticated session right now), `QUEUED` (defined, awaiting session capacity or a precondition), `BLOCKED` (needs operator action), `REJECTED` (tested and clean — do not re-test).

---

## 1. UNIFIED INVARIANT CATALOG

Every "must never happen" rule derived across all targets, grouped by class. Each invariant names the targets where it is under test.

### 1A. Authorization (object-level)
| # | Invariant | Under test at |
|---|-----------|---------------|
| AZ-1 | User A must never access User B's object (resource ID stays bound to the authorized principal) | Pinterest (secret boards/pins, conversations), Aiven (cross-project substitution), OneTrust (DSR L3/L9, attachment L5, orggroupuser), GitLab (H3), FDJ (affiliate boundaries) |
| AZ-2 | A low-privilege user must never perform an admin-only operation | Aiven (invite at `accounts:read` vs UI admin), OneTrust (Site Admin escalation bar), GitLab (group restrictions H8) |
| AZ-3 | A client-supplied identity parameter must never override the session principal | Pinterest (`orbac_subject_id` — #1 live probe) |
| AZ-4 | Old API generations must enforce the same authorization as current ones | Pinterest (v3 vs v5), OneTrust (v1 vs v2 user-groups, deprecated DSR v1), GitLab (REST vs GraphQL H5) |
| AZ-5 | A download/credential-issuance token must remain bound to the requesting principal | OneTrust (attachment token L5), Aiven (governance credentials AIV-01) |
| AZ-6 | A coarse OAuth scope must never substitute for a fine-grained role check the UI itself enforces | Aiven (invite/delete-invite, AppBuilder writes) |
| AZ-7 | Download/token endpoints must not serve another principal's object on ID substitution | Pinterest (OAuth consumer_id revocation), OneTrust (L5) |

### 1B. State machines
| # | Invariant | Under test at |
|---|-----------|---------------|
| SM-1 | No authentication state transition may be driven without the victim's credentials or an unguessable secret delivered to the victim | GitLab (H2 — the $35k password-reset bug shape), Yahoo (H5), Robinhood (H11) |
| SM-2 | A terminal state must never accept further transitions | Robinhood (H3: cancel-after-fill, exercise-after-expiry), Pinterest (invite accept/decline/revoke replay), PayPal (H2 double capture) |
| SM-3 | A signup/onboarding step must not be skippable or replayable out of order | Pinterest (`progress_token` L7) |
| SM-4 | An invite/approval workflow must not be completable by skipping the approval state | Pinterest (collaborator `status_filters` approval L11), Aiven (invite weblink entropy/expiry) |
| SM-5 | Two concurrent state transitions must never double-apply (race) | PayPal (H2/H4/H7 races), Robinhood (H2 balance TOCTOU, H10 promo stacking), Pinterest (follow/unfollow races) |
| SM-6 | Linking/unlinking an external identity must not leave a stale privileged session | Pinterest (OAuth unlink/relink), GitLab (OmniAuth linking) |

### 1C. Tenant isolation
| # | Invariant | Under test at |
|---|-----------|---------------|
| TI-1 | Tenant X's database role/files/credentials must never reach tenant Y's data | Aiven (SupaPwn pattern: extensions, FDW, file-read functions — needs service-approval) |
| TI-2 | A token minted for tenant/org A must never authorize tenant/org B | OneTrust (L7 tenant/org/role confusion, L8 collection-point cross-use) |
| TI-3 | Requester A must never read requester B's workflow object via a client-chosen key | OneTrust (DSR `requestTraceId` L3, `requestQueueRefId` L9) |
| TI-4 | A server-side proxy must not execute with more database privilege than the caller | Aiven (pg-editor `run-query` principal — needs service) |
| TI-5 | A CI job must act only as its triggering project/user and see only in-scope variables | GitLab (H4: CI_JOB_TOKEN cross-project, protected variables) |

### 1D. Token trust
| # | Invariant | Under test at |
|---|-----------|---------------|
| TT-1 | A token must be bound to session + principal + operation + object type (type confusion = bug) | PayPal (H6 token-type confusion, Birsan/Hoggard precedents), Pinterest (cross-context token replay) |
| TT-2 | Client-declared restrictions must be re-enforced server-side, never trusted | Pinterest (ApiResource `options.url` dispatcher allowlist — #1 web lead), Aiven (MCP `read_only`/`services_scope` query params) |
| TT-3 | A JWT must be unforgeable without the server secret; the algorithm must not be downgradeable | All live sessions (token harvest → alg-confusion battery) |
| TT-4 | Authentication tokens must be delivered only to the exact registered endpoint | Yahoo (H1 — the $7k Flickr `.done` prefix-validation bug shape) |
| TT-5 | The identity in the verified signature must be the identity the session is created for, under every parser the stack uses | OneTrust/Aiven (SAML parser differentials — if SAML exposed) |
| TT-6 | A fallback/secondary auth path must be as strong as the primary path | PayPal (H9: 2FA fallback parameter omission), Pinterest (magic-link/Qr-auth) |
| TT-7 | Anti-CSRF tokens must be single-use and bound to the ceremony, never reusable as bearer tokens | PayPal (H6/Yasser Ali precedent), Pinterest (CSRF enforcement probes) |

### 1E. Cache
| # | Invariant | Under test at |
|---|-----------|---------------|
| CA-1 | The cache key must cover every input reflected in the cached response (no unkeyed inputs) | Aiven (cached homepage + unkeyed headers L1), Pinterest (Fastly black box L2) |
| CA-2 | Private/authenticated content must never be cached or served to another user | Pinterest (secret-board cache deception `;.css` probes) |
| CA-3 | One user's request must never poison a cache entry served to others | All (T1 unkeyed-input battery with unique cache-busters) |

### 1F. Business logic / money movement
| # | Invariant | Under test at |
|---|-----------|---------------|
| BL-1 | Σ captures ≤ authorized amount, in the authorized currency; amounts never client-mutable post-approval | PayPal (H1 capture > auth, H3 PATCH-after-approval TOCTOU, H12 currency confusion) |
| BL-2 | Duplicate idempotency keys must never double-pay; cancelled/unclaimed funds return exactly once | PayPal (H4 payout idempotency/double-spend, H14 invoice dedup TOCTOU) |
| BL-3 | Value in transit must be counted exactly once toward buying power/margin | Robinhood (H1 — the infinite-money-glitch shape on new features) |
| BL-4 | Funds must never leave the platform before settlement except through the defined instant-credit allowance | Robinhood (H4 unsettled-fund withdrawal) |
| BL-5 | The server must re-derive amount/destination from its own state, never trust client-supplied values | Robinhood (H13 cashier tampering), FDJ (payment callback signing) |
| BL-6 | Payment callbacks must be signed and bound to a server-side transaction; replay must not credit | FDJ (callback replay — blocked until Maria Casino account) |
| BL-7 | User-controlled input must never render as executable content in transactional email/SMS/push | Robinhood (H9 notification injection — the Apr-2026 class) |
| BL-8 | A promo/credit must be claimable exactly once per eligible principal | Robinhood (H10 referral stacking) |
| BL-9 | Unsubscribing must never cause the server to fetch an arbitrary URL | OneTrust/Pinterest/Aiven/FDJ (T10 unsubscribe SSRF) |
| BL-10 | Uploaded bytes must be inert wherever stored, rendered, or parsed | GitLab (H7 workhorse/multipart/notebook), Yahoo (H8 Flickr/mail uploads) |
| BL-11 | Server-side requests must never go to attacker-controlled destinations | OneTrust (L1 webhook→FreeMarker→HTTP SSRF), Yahoo (H3), Pinterest (rich-pin validator OBS-2) |
| BL-12 | Template rendering must not execute code | OneTrust (L2 FreeMarker SSTI) |
| BL-13 | Billing/credit state must not be manipulable via client-side values | Aiven (billing/credit endpoint battery) |

---

## 2. RANKED MASTER LEAD BOARD

Scored by expected value = (payout precedent × blast radius × likelihood). Status as of 2026-09-26. **Nothing here is confirmed above Low.**

### Tier S — Critical-shaped, live in sessions NOW
| ID | Lead | Target | Status | Evidence |
|----|------|--------|--------|----------|
| PIN-01 | `orbac_subject_id` client-supplied authz identity on board invites / collaborator removal / pin feeds | Pinterest | PROBING | JS-bundle strings (deep-static C3); fed to live session 2026-09-26 |
| PIN-02 | `ApiResource` dispatcher allowlist — client controls `options.url` | Pinterest | PROBING | py3-pinterest source + bundle (mobile-differential C5); T9 writeup validates the bug shape |
| AIV-01 | Governance credentials endpoint declares `accounts:read` yet returns live Kafka `access_cert`/`access_key`/`password` | Aiven | PROBING | Spec-declared scope vs secret response (deep-static §2); fed to live session 2026-09-26 |
| AIV-02 | Invite/uninvite endpoints at `accounts:read` while console UI demands `organization:users:write`/admin | Aiven | PROBING | Spec vs UI permission table mismatch (deep-static §3) |
| GL-01 | Project/group import → file read / SSRF / RCE / cross-project theft ($29k/$20k×3/$16k/$10k precedents) | GitLab | PROBING | Disclosed-report pattern #1; session launching 2026-09-26 |

### Tier A — High-shaped, live or one step away
| ID | Lead | Target | Status | Evidence |
|----|------|--------|--------|----------|
| AIV-03 | AppBuilder writes (`apply-live-edit-changes`, `publish-preview`) on `projects:read`, undocumented in public spec | Aiven | PROBING | Console-bundle client only (deep-static §4) |
| AIV-04 | MCP server trusts client-controlled `read_only`/`services_scope` query params | Aiven | PROBING | Bundle `Ipe()` URL construction (deep-static §5) |
| PIN-03 | v3 vs v5 authorization divergence on the same objects | Pinterest | PROBING | v3 still routes (`v3_get_user_handler`); 2013 identity-confusion precedent on this plane |
| PIN-04 | `/v3/batch/` sub-request smuggling (non-GET sub-requests, nested `/resource/` URLs) | Pinterest | PROBING | Bundle: `data:{requests: JSON.stringify(s)}` (deep-static C6) |
| PIN-08 | `progress_token` signup step-skipping / replay | Pinterest | PROBING | Bundle state machine (deep-static C10) |
| PIN-09 | Collaborator privilege transitions via `status_filters` approval workflow | Pinterest | PROBING | Bundle strings (`pending_approval`, …) (deep-static L11) |
| PIN-06 | Invite redeem flow fully client-driven (`invite_code` + `board_url` from query string) | Pinterest | PROBING | Bundle (deep-static C4) |
| AIV-08 | Cross-project object substitution across all `/project/{project}/…` endpoints | Aiven | PROBING | In 10-technique battery |
| GL-02 | Password-reset/2FA/session state-machine flaws (the $35k bug shape) | GitLab | QUEUED | Disclosed #2293343; needs two test accounts |
| GL-03 | GraphQL vs REST authorization differentials | GitLab | QUEUED | Disclosed #1122408, CVE-2026-87719 |
| GL-04 | CI job identity escape / protected-variable reads (policy test pipelines) | GitLab | QUEUED | #894569 ($12k), CVE-2026-79708 |
| OT-01 | Webhook → FreeMarker → Generic HTTP action = SSRF primitive | OneTrust | BLOCKED | Docs C3+C4; needs Bugcrowd staging credential |
| OT-02 | FreeMarker SSTI in integration builder | OneTrust | BLOCKED | Docs C4 |
| OT-03 | Client-driven privilege context on OAuth flow (`tenant_id`/`orggroup_id`/`role_id`/`switchRole`) | OneTrust | BLOCKED | Staging bundle query params |
| OT-04 | DSR webforms/workflows IDOR | OneTrust | BLOCKED | Brief's explicit focus area |
| OT-05 | Attachment download-token IDOR | OneTrust | BLOCKED | Docs C6 |
| OT-06 | DSR status oracle via client-chosen `requestTraceId` | OneTrust | BLOCKED | Docs C5 |
| OT-07 | Deprecated v1 DSR Create Request still live with weaker checks | OneTrust | BLOCKED | Deprecated-APIs list |
| OT-08 | v1 vs v2 user-groups differential | OneTrust | BLOCKED | Spec C7 |
| OT-09 | SCIM scope privilege boundary | OneTrust | BLOCKED | Scope table |
| OT-10 | `/api/v1/private/orggroupuser/get` IDOR | OneTrust | BLOCKED | Staging surface map |

### Tier B — Solid mediums, queued
| ID | Lead | Target | Status | Evidence |
|----|------|--------|--------|----------|
| PIN-05 | QR-auth token binding (poll cross-session, entropy, expiry) | Pinterest | QUEUED | Bundle: two chunk implementations (deep-static C5) |
| PIN-07 | OAuth authorization IDOR (`DELETE /v3/oauth/authorizations/{consumer_id}/`) | Pinterest | QUEUED | Bundle (deep-static C7) |
| PIN-10 | `/v3/connect/*` linking CSRF/`state` validation | Pinterest | QUEUED | 10-provider surface (deep-static C13) |
| PIN-11 | `switch_account` id tampering (`{switch_account:<id>}`) | Pinterest | QUEUED | Bundle (deep-static L10) |
| PIN-12 | Debug endpoints gating (`/v3/hf_debug_tool/`, `/v3/pins/debug/`, `/v3/legal/takedowns/test/`) | Pinterest | QUEUED | Route map (deep-static C8) |
| PIN-13 | `ask.pinterest.com` prompt injection / cross-user data | Pinterest | QUEUED | Loads unauth, `/api/` → 401 |
| PIN-14 | Rich-pin validator server-side fetch (SSRF primitive, unconfirmed) | Pinterest | QUEUED | Page exists, fetch endpoint unidentified (unauth-battery OBS-2) |
| AIV-05 | pg-editor `run-query` database principal | Aiven | QUEUED | Scope `services:write`; needs service-creation approval |
| AIV-06 | Kafka REST produce vs native ACL parity | Aiven | QUEUED | Needs service |
| AIV-07 | Query-optimizer / pg-editor LLM prompt injection, error-based schema disclosure | Aiven | QUEUED | `/pg/query/optimize` sinks (deep-static §6) |
| AIV-09 | Weblink invite code entropy/expiry/role | Aiven | QUEUED | Console-only API (deep-static §3) |
| AIV-10 | Billing/credit/invoice endpoint IDOR | Aiven | PROBING | In battery |
| AIV-11 | OAuth2 token-endpoint parameter confusion | Aiven | PROBING | Already leaks raw PG errors (F1) |
| FDJ-01 | JSF ViewState on `/payment-cashier/` (state-saving method, deserialization) | FDJ/Maria | QUEUED | Legacy JSF on money app (deep-static §3) |
| FDJ-02 | Payment callback replay (`status=success` on cancelled transaction) | FDJ/Maria | BLOCKED | Needs authenticated deposit flow; uniform-stub recon confirms opacity |
| FDJ-03 | `/pay-bootstrap/` auth handshake session confusion | FDJ/Maria | QUEUED | `authentication_failed` endpoint (deep-static §3) |
| FDJ-04 | Internal/QA hosts internet-reachable (`int.32red.com`, `www-qa1/si1.*`) | FDJ | QUEUED | Leaked in prod devtools bundle (deep-static §2) |
| FDJ-05 | `affiliateadmin.32red.com` trust-zone boundary | FDJ | QUEUED | CT inventory (deep-static §5) |
| FDJ-06 | Dev subdomains (`secure-dev`, `web-services-dev`, `*.d2-dev.aws.unibet.com`) | FDJ | QUEUED | CT inventory |
| FDJ-07 | Shared bundle-store version pinning / downgrade | FDJ | QUEUED | Versioned immutable bundles (deep-static §1) |
| FDJ-08 | Mobile bridge schemes (`jockey:`, `unibetpro:`) native-method exposure | FDJ | QUEUED | CSP evidence (deep-static §6) |
| FDJ-09 | Legacy bingo cPanel hosts / 32red legacy brand hosts | FDJ | QUEUED | CT inventory; low priority |
| GL-05 | OAuth/token scope confusion across token zoo (PAT/group/project/deploy/job/runner) | GitLab | QUEUED | Recon H6 |
| GL-06 | Upload pipeline bypasses / content injection as victim | GitLab | QUEUED | #850447, pattern #8 |
| PP-01…PP-15 | PayPal Tier 1–4 hypotheses (capture>auth, double-submit, PATCH-after-approval, payout double-spend, cross-merchant IDOR, token confusion, over-refund, subscription authz, 2FA fallback, webhook-sig, OAuth scope, currency, reauthorize window, invoice dedup, framing) | PayPal | BLOCKED | Needs sandbox accounts |
| YH-01…YH-10 | Yahoo H1–H10 (OAuth token-destination, mail sanitizer, SSRF, IDOR, recovery state machine, SDTO, web/mobile differential, upload chains, XSSI, redirect-chains) | Yahoo | QUEUED | Needs test accounts + live-brief verification |
| RH-01…RH-14 | Robinhood H1–H14 money-movement + MCP + Say platform | Robinhood | QUEUED* | *Money-movement subset blocked on KYC; MCP/Say/static testable now |

### Confirmed findings (Low only — reportable, not the "real bug")
| ID | Finding | Target | Status | Evidence |
|----|---------|--------|--------|----------|
| AIV-F1 | Verbose PostgreSQL error disclosure on `POST /v1/oauth2/token` (schema-qualified function names, SQLSTATE) | Aiven | CONFIRMED | Reproduced unauthenticated 2026-09-26 |
| AIV-F2/U1 | User enumeration via `login_options` (`signup` vs `google_oauth` branch) | Aiven | CONFIRMED | Valid-vs-invalid differential reproduced |
| AIV-F3/U2 | User enumeration via `/v1/userauth` message differential ("User does not exist" vs "Authentication failed") | Aiven | CONFIRMED | Reproduced |
| AIV-F4/U3 | CORS origin reflection API-wide (no `Allow-Credentials`) | Aiven | CONFIRMED | Multiple endpoints incl. preflight |
| AIV-F5 | Internal Admin API OAuth `clientSecret` exposed in public Regatta config (suspected — exploitability UNVALIDATED) | Aiven | BLOCKED | Exposure confirmed; `admin-api.aiven.io:4343` out of scope — do not touch |

---

## 3. TECHNIQUE → TARGET MATRIX

Deployed technique types (12, from the 10+ battery + token battery + playbook).

| Technique | Pinterest | Aiven | GitLab | OneTrust | FDJ | PayPal | Yahoo | Robinhood |
|-----------|-----------|-------|--------|----------|-----|--------|-------|-----------|
| 1. Confused deputy / dispatcher tampering | PROBING (ApiResource, orbac_subject_id) | — | — | BLOCKED (L1/L8) | — | — | — | — |
| 2. API version / plane differentials | PROBING (v3 vs v5 vs web) | PROBING | QUEUED (REST vs GraphQL) | BLOCKED (v1 vs v2) | — | — | QUEUED (web vs mobile) | QUEUED (3 planes) |
| 3. HTTP method tampering | PROBING | PROBING | QUEUED | BLOCKED | — | — | — | — |
| 4. Parameter pollution / type juggling | PROBING | PROBING | — | BLOCKED | — | BLOCKED (H9) | — | — |
| 5. Mass assignment | PROBING | PROBING | — | BLOCKED | — | — | — | — |
| 6. IDOR by object substitution | PROBING | PROBING | PROBING | BLOCKED | QUEUED | BLOCKED (H5) | QUEUED | QUEUED |
| 7. CSRF enforcement gaps | PROBING | — | — | out-of-scope per brief | — | BLOCKED (H15) | — | — |
| 8. State-machine violations | PROBING (invites, signup) | PROBING (invites) | QUEUED | BLOCKED | BLOCKED (callback) | BLOCKED (T1–T4) | QUEUED | QUEUED* |
| 9. Cache poisoning / deception | PROBING | PROBING | — | BLOCKED | — | — | — | — |
| 10. Race conditions | PROBING | PROBING | QUEUED | — | — | BLOCKED (H2/H4) | — | QUEUED |
| 11. OAuth unlink/relink / session semantics | PROBING | — | QUEUED | BLOCKED | — | — | QUEUED | — |
| 12. JWT/session token forgery & replay | PROBING | PROBING | QUEUED | BLOCKED | — | BLOCKED (H11) | — | — |
| Passive: JS-bundle mining | DONE | DONE | — | DONE | DONE | — | — | — |
| Passive: OpenAPI/spec mining | DONE | DONE | — | DONE | — | — | — | — |
| Passive: CT/infra recon | DONE | DONE | — | DONE | DONE | — | — | — |
| Passive: disclosed-report pattern mining | DONE | DONE | DONE | DONE | — | DONE | DONE | DONE |
| Passive: writeup technique mining | DONE (all targets mapped) | DONE | DONE | DONE | DONE | DONE | DONE | DONE |

**Uncovered / thin:** SAML parser differentials (no session yet at OneTrust/Aiven — queued); DOM XSS source→sink runtime confirmation (static pass done, runtime queued); React2Shell fingerprinting (queued, cheap); List-Unsubscribe SSRF (queued); anomaly-rank tooling (queued); FDJ beyond recon (account-blocked); PayPal everything (sandbox-blocked); Yahoo everything (account-blocked).

---

## 4. BLOCKER REGISTER — awaiting the operator

| # | Front | Exactly what is needed | Unblocks |
|---|-------|------------------------|----------|
| B1 | FDJ / Maria Casino | Operator types a password making **all 5 indicators green**, clicks CONTINUE (research email already filled) | Maria Casino authenticated phase: JSF ViewState, pay-bootstrap, callback capture, cashier JS |
| B2 | OneTrust | Operator provides **exact Bugcrowd registered email/username** (vault password reset rejected 3×; no more blind retries) | Staging authenticated battery OT-01…OT-10 (SSRF, SSTI, IDOR, tenant confusion) |
| B3 | PayPal | Operator provides PayPal developer login | 2 sandbox business accounts + 1 buyer account → PP-01…PP-15 |
| B4 | Robinhood money movement | **No viable path** — requires US residency + SSN; fake KYC is out of bounds | RH-01…RH-05, RH-12, RH-13 stay blocked; RH-08 (MCP), RH-14 (Say), static analysis proceed without KYC |
| B5 | Aiven | Operator approval to create a **database service** (cost/isolation decision) | pg-editor principal, Kafka REST ACL parity, Flink JAR, tenant-escape DB tests |
| B6 | Aiven | Scope confirmation for `admin-api.aiven.io:4343` | AIV-F5 validation (one token-exchange attempt) |
| B7 | Yahoo | Operator confirms live brief + test-account alias format before any active work | YH-01…YH-10 |
| B8 | GitLab | Verify `@wearehackerone.com` alias requirement on live brief (account currently launching via research Google SSO) | Full H1–H8 battery compliance |
| B9 | Pinterest | Optional: second Google account sign-in | Cross-account IDOR (conversations, board invites between two principals) |

---

## 5. CONFIRMED-CLEAN LIST — tested and rejected, do not re-test

### Pinterest
- P-C1. Public v5 unauth access — 401 everywhere, auth before input validation
- P-C2. Legacy `/v1/`, `/v3/` on `api.pinterest.com` — `API method not found` (note: `www`-plane v3 IS live — different namespace)
- P-C3. Widget embed API over-exposure — 77-key response audited, no sensitive fields
- P-C4. Pin/board/user ID enumeration — 19-digit snowflakes, not enumerable
- P-C5. CORS misconfiguration — no origin reflection on `api.` or `www.`
- P-C6. Open redirect on `/login/?next=` — 200, no server redirect; `next` echoed inside JSON only
- P-C7. Reflected XSS via `next` — payload properly URL-encoded inside JSON string
- P-C8. Subdomain takeover (61 crt.sh hosts) — edge "Not Found" pages / 302s / unresolvable
- P-C9. Secrets in 50 webapp JS bundles — none
- P-C10. `/resource/` webapp API without session — requires `csrftoken` even anonymously, public data only
- P-C11. Security headers — HSTS preload, nonce CSP, SAMEORIGIN, nosniff all present
- P-C12. Mobile uses a separate private API — no evidence; treat as internal plane
- P-C13. postMessage wildcard in LINE OAuth redirect — single-arg call defaults to same-origin
- P-C14. `dangerouslySetInnerHTML` XSS in 70 chunks — all benign (React internals/CSS/skeletons)
- P-C15. `pinterest://` deep-link handlers — none found
- P-C16. Forgot-password oracle — client handles success/failure identically
- P-C17. X-Forwarded-Host affects homepage — disproven (variance was dynamic content noise)
- P-C18. Cache deception via `.css` on `/login/` — 301, no content served

### Aiven
- A-C1. OAuth `redirect_uri` open redirect — 200 error page, no redirect issued
- A-C2. Console bundle secrets — placeholders only
- A-C3. `POST /v1/user/password_reset_request` oracle — uniform `200 {"message":"email sent"}`
- A-C4. `/v1/pg/query/validate` + `/v1/mysql/query/validate` SQL execution — parse-only (nonexistent table → `success`), no schema resolution, no execution
- A-C5. `/v1/pg/database-metadata-query` — returns template only, no data
- A-C6. `POST /v1/account/{id}/invite/{code}` — 410, retired 2026-03-23
- A-C7. SBOM/invoice download cookies — clean 400s on garbage
- A-C8. Credit/referral code oracles — clean 400s
- A-C9. Debug/actuator surface on `api.aiven.io` — all 404 (console returns SPA fallback 200)
- A-C10. Malformed-input battery on `login_options` — clean 400s, no stack traces
- A-C11. Trial-signup client-side bypass — no tamperable parameter; flow is Google-OAuth-based
- A-C12. Admin API OAuth secret in console JS — absent in all 7 bundles (lead lives in Regatta config, out-of-scope destination)
- A-C13. `dangerouslySetInnerHTML` XSS — benign (icons, code snippets)
- A-C14. `postMessage` trust issues — app-internal handlers only
- A-C15. `reset_password` over-permissioning — sanely gated (`accounts:write`, managed users)
- A-C16. Feature flags as vuln class — server-issued, cosmetic gating only
- A-C17. XFH as cache-poisoning vector — reproducibly 403-blocked by Cloudflare
- A-C18. Query-param cache-key anomaly — normal (param is part of key)
- A-C19. Cached personalized content on console/API — `DYNAMIC` + `no-store`

### OneTrust
- O-C1. Debug exposure (`/actuator`, `/debug`, `/graphql`, `/v3/api-docs`, …) — all 401
- O-C2. Verbose errors — empty 401s, generic error JSON, no stack traces
- O-C3. Auth bypass via method tampering on `/api/access/v1/tenants/current` — consistent 401
- O-C4. CORS misconfiguration — no origin reflection
- O-C5. Client secrets in staging bundle — none
- O-C6. `my.onetrust.com` as app target — Salesforce community shell, not the app
- O-C7. `tenant_id` as documented request parameter — not in specs (L7 is a behavioral probe, downgraded)

### FDJ
- F-C1. Path enumeration on `payment.mariacasino.com` — uniform 22-byte stub, no oracle (stopped after 4 requests)
- F-C2. Direct datacenter curl to brand homepages — 503 bot/geo gating, not a vuln
- F-C3. Subdomain takeover via DNS — unverifiable (sandbox DNS intercepted); no claim made
- F-C4. `ww1.admins.dream--bingo.com` — legacy CDN label, not a real admin panel

### Cache differential
- CA-C1…CA-C5 as A-C17…A-C19 and P-C17/P-C18 above.

---

## 6. OPERATION LEDGER (2026-09-26)

| Report | File | Status |
|--------|------|--------|
| Pinterest unauth battery | `intel/pinterest-unauth-battery.md` | Complete — clean |
| Pinterest mobile differential | `intel/pinterest-mobile-differential.md` | Complete — 7 leads |
| Pinterest deep static | `intel/pinterest-deep-static.md` | Complete — 12 leads |
| Aiven deep assessment | `intel/aiven-deep-assessment.md` | Complete — 4 confirmed Lows + battery |
| Aiven unauth battery | `intel/aiven-unauth-battery.md` | Complete — 2 confirmed Lows |
| Aiven deep static | `intel/aiven-deep-static.md` | Complete — 10 leads |
| OneTrust staging | `intel/onetrust-staging.md` | Complete — clean; 4+10 leads blocked |
| OneTrust deep static | `intel/onetrust-deep-static.md` | Complete — 10 leads |
| FDJ payment recon | `intel/fdj-payment-recon.md` | Complete — clean |
| FDJ deep static | `intel/fdj-deep-static.md` | Complete — 10 leads |
| GitLab VDP recon | `intel/gitlab-vdp-recon.md` | Complete — 8 hypotheses |
| Yahoo VDP recon | `intel/yahoo-vdp-recon.md` | Complete — 10 hypotheses |
| PayPal VDP recon | `intel/paypal-vdp-recon.md` | Complete — 15 hypotheses |
| Robinhood VDP recon | `intel/robinhood-vdp-recon.md` | Complete — 14 hypotheses; KYC wall |
| Writeup technique playbook | `intel/writeup-techniques.md` | Complete — 10 techniques mapped |
| Cache differential | `intel/cache-differential.md` | Complete — mostly clean |
| This synthesis | `intel/ADVANCED-STUDY.md` | **Living** |

**Live sessions:** Pinterest (10+token-technique battery), Aiven (10+token-technique battery + 5 spec leads), GitLab (account creation → import seam). **Blocked on operator:** B1 (Maria Casino password), B2 (Bugcrowd email), B3 (PayPal sandbox login). **Dead end:** B4 (Robinhood KYC).

*End of study. Next update when a PROBING lead resolves to CONFIRMED or REJECTED.*
