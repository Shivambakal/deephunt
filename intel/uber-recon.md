# Uber — Passive Recon (HackerOne public program)
**Date:** 2026-09-26
**Method:** READ-ONLY. No logins, no form submissions, no testing. Low-volume single GETs (program policy page, developer docs auth guide, m.uber.com, auth.uber.com homepages) + web search for public evidence. No authenticated session was created.

---

## [SCOPE]

Source: https://hackerone.com/uber (program terms, fetched 2026-09-26). Uber runs an **impact-based** program: reports are judged on "specific security impact for users (versus domain + vulnerability class)". Issues with no infosec impact are closed.

**Security-impact buckets (bounty ranges):**
- Exposure of User Data — $0–$10,000
- Unauthorized Requests on Behalf of User/Employee — $0–$10,000
- Monetary Impact — $0–$10,000
- Phishing — $0–$5,000
- Safety — $0–$10,000
- Historical severity ranges: IDOR Low–Critical, Information disclosure Low–Critical, SSRF Medium–Critical, XSS Medium–High.
- Fixed-price items (no CVSS): **Subdomain Takeover $500** (must demonstrate takeover with a non-offensive message, e.g. your username); **Broken URL links on \*.uber.com $100 or $0** (case by case); 3rd-party info disclosures (Prezi, Trello, Google Doc) case by case.
- Hybrid payout model: minimum bounty at triage, full bounty at resolution once impact is understood. Pay-at-triage target ~14 days.

**Ground rules (must-follow):**
- Test ONLY with your own accounts. Reports should reference your `@wearehackerone.com` email.
- 18+ if testing with an Uber account. No Uber employees/affiliates/immediate family. No sanctioned countries. No duplicate HackerOne accounts.
- No brute-forcing credentials, no password changes on accounts you didn't register, no DoS, no social engineering, no targeting specific employees/customers/partners, minimal data access for PoC, stop when unsure and ask.
- No public disclosure without explicit review/consent. Safe harbor applies for good-faith research.

**Explicit OUT-OF-SCOPE (do not waste time here):**
- LLM-token consumption / API-cost inflation via repetitive prompting (unless significant, scalable, immediate availability impact).
- Anything relying on stolen/compromised credentials, credential stuffing, ATO.
- Phishing in a DNS domain that is not a primary service domain.
- Sandbox/lab/staging/non-production runtime contexts (mostly).
- **Open redirect with low impact** (chainable ones — token theft, SSRF — are welcome, say so).
- Vulnerabilities needing significant unlikely victim interaction (e.g. disabling browser controls).
- **Account enumeration / account oracles**: submitting phone, email, or UUID and getting back an "account exists" signal — explicitly out.
- **Invite/promo code enumeration** — explicitly out.
- Push/SMS/email sending without content control.
- Version-number-only reports without PoC. Outdated-client-only issues. Stack traces/path disclosure/directory listing. **CSV injection**. Best-practice-only with no demonstrable issue. Social-media page takeover. Self-XSS / paste-into-console. Automated scanner output without analysis. **Rate-limiting issues / DoS**. Content injection/spoofing. **CSRF with minimal impact (e.g. logout CSRF)**. Missing cookie flags on non-auth cookies. Physical access. TLS-scan reports. Banner grabbing. Open ports without PoC. Exposed login panels without PoC. Dangling IPs. Third-party products not owned by Uber. Out-of-scope domains (see scoping section).

**Account & Financial Fraud — IN SCOPE when technical:** exploits requiring multi-account collusion + a technical product/service vulnerability get a bonus tied to financial impact. Identity fraud (stolen/hijacked/synthetic identities, incl. safety-impacting) reviewed case by case. Credential-stuffing/brute-force/breach-password fraud stays out.

**SSRF Sheriff (official test harness):** if you believe you have SSRF in production, test ONLY against:
- `http://dca11-pra.prod.uber.internal:31084/<handle>@wearehackerone.com`
Accepts HTTP requests to any endpoint, any method, returns a secret token in headers + body. Valid response types for extensions: xml, json, gif, png, jpg/jpeg, html, txt, mp4, csv (append extension to path, e.g. `/foobar.json`).

**Asset Recon:** Uber publishes endpoints to check whether an asset belongs to Uber (support offset/limit params). Endpoints exist for recon; a hit does not guarantee bounty eligibility. (Exact URLs were link-elements not captured in text fetch — verify on the live policy page before use.)

**No test accounts provided.** If credentials were needed, they'd be under test plan/instructions — none are, so bring your own.

---

## [SUBDOMAIN INVENTORY]

Note on method: a direct crt.sh JSON query for `%.uber.com` timed out at fetch and was not retried (per fetch-failure policy). The inventory below is built from evidence-backed sources: disclosed HackerOne reports, official developer docs, and the program policy page. Treat as a high-signal shortlist, not an exhaustive zone dump.

| Subdomain | Role / evidence |
|---|---|
| `m.uber.com` | Mobile web app ("Request a Ride with Uber"); universal-link host `m.uber.com/ul/`; trip-share pages `m.uber.com/go/share/*` poll a GraphQL endpoint ~1×/sec (observed by https://github.com/ernanicastro92/trip-guard) |
| `auth.uber.com` | Central OAuth 2.0 / login ("Sign up or Log in with Uber"; phone/WhatsApp verification-code consent text on homepage). Token endpoint `/oauth/v2/token`, authorize endpoint `/oauth/v2/authorize` (see [AUTH FLOWS]) |
| `api.uber.com` | Production API base for Uber Eats Marketplace / Direct APIs (per https://github.com/hrs190/agent-framework/blob/HEAD/.claude/skills/uber-eats-api/SKILL.md) |
| `test-api.uber.com` | Sandbox API base (same source) |
| `sandbox-login.uber.com` | Sandbox auth host (same source) |
| `riders.uber.com` | Rider web surface; invite-code brute-force report hackerone 125505 ($5,000); SSO shared-cookie auth-bypass report 219205 lists it as relying on auth.uber.com |
| `partners.uber.com` | Driver/partner web surface; invite-code report 144616 ($750); listed in 219205 SSO-cookie analysis |
| `developer.uber.com` | Developer dashboard + docs; listed in 219205 SSO-cookie analysis; OAuth app registration happens here |
| `bonjour.uber.com` | Marketplace web surface; **highest-signal historic target**: `bonjour.uber.com/marketplace/_rpc` + `userUuid` parameter disclosed sensitive user info (hackerone.com/reports/542340 — 642 upvotes, most-upvoted Uber info-disclosure report); listed in 219205 |
| `saostatic.uber.com` | Historic subdomain-takeover → session-cookie theft → full auth bypass chain (report 219205, 2017). Fixed, but the *class* (dangling DNS + shared cookie scope) is the thing to re-hunt |
| `ubermovement.com` | Uber Movement site; blind OOB XXE reported (226335, $500). Verify current scope before touching |
| `dca11-pra.prod.uber.internal` | Internal-only SSRF sheriff host (port 31084). Not a target — the sanctioned SSRF test sink |

**Interesting but unverified from this pass:** `drivers.uber.com`, `eats.uber.com` (task-named candidates) — no direct evidence captured; confirm via DNS/asset-recon endpoints before scoping work around them. `*.uber.com` cookie-sharing behavior documented in 219205 ("SSO system using shared session cookies for https://\*.uber.com") — the *current* cookie `Domain` scoping across these hosts is itself a recon target.

---

## [API SURFACE]

### Riders API (public, documented)
Source: https://developer.uber.com/docs/ride-requests/guides/authentication/introduction (fetched 2026-09-26).

Server-token endpoints (note: **server tokens are deprecated** — no new grants; existing tokens work until migration to scopes-based access tokens completes):
- `GET /products`, `GET /products/{product_id}`, `GET /estimates/price`, `GET /estimates/time`

User-access-token endpoints (OAuth 2.0):
- `GET /me`, `PATCH /me` (apply a user promotion), `GET /history` (lifetime activity: pickup/dropoff locations+times, distances, products)
- `GET /places/{place_id}`, `PUT /places/{place_id}` (saved places)
- `POST /requests/estimate`, `POST /requests` (create ride request)
- `GET /requests/{request_id}`, `DELETE /requests/{request_id}` (cancel), `PATCH /requests/{request_id}` (update)
- `GET /requests/{request_id}/map`, `GET /requests/{request_id}/receipts`

### Uber Eats / Direct / Ads APIs (documented, partner-gated)
Sources: https://github.com/hrs190/agent-framework/blob/HEAD/.claude/skills/uber-eats-api/SKILL.md ; https://community.postman.com/t/uber-direct-api-help/75018 ; https://github.com/uber/ads-api-example/blob/HEAD/README.md
- Base: `https://api.uber.com` (prod), `https://test-api.uber.com` (sandbox)
- Eats endpoints seen: `GET /v1/eats/stores/{store_id}/transactions`, `GET /v1/eats/stores/{store_id}/payouts`
- Uber Direct auth example uses scope `eats.deliveries` via client_credentials.
- Uber Ads API: full OAuth 2.0 authorization-code flow, typed client generated from official OpenAPI spec, Ads scopes enabled per-app in dashboard.

### Web-app internals (observed, not from bundles)
- `m.uber.com` and `auth.uber.com` homepages are JS SPAs (text fetch returns only "Loading" / login-consent shell) — no bundle URLs recoverable via text fetch. **Gap:** JS-bundle endpoint mining not completed; do it in a live browser session later.
- Trip-share pages (`m.uber.com/go/share/*`) poll a **GraphQL endpoint ~1×/sec** for driver position + route (per https://github.com/ernanicastro92/trip-guard). Unauthenticated-by-design share surface — prime IDOR/stale-auth target.
- Historic: `bonjour.uber.com/marketplace/_rpc` RPC-style endpoint taking `userUuid` (hackerone.com/reports/542340).

---

## [AUTH FLOWS]

### Central OAuth 2.0 (auth.uber.com)
Sources: https://github.com/hrs190/agent-framework/blob/HEAD/.claude/skills/uber-eats-api/SKILL.md ; https://community.postman.com/t/uber-direct-api-help/75018 ; https://developer.uber.com/docs/ride-requests/guides/authentication/introduction

- **Token endpoint:** `POST https://auth.uber.com/oauth/v2/token` (form-encoded: `client_id`, `client_secret`, `grant_type`, `scope`)
- **Grant types:** `client_credentials` (server-to-server, e.g. `scope=eats.store eats.order`, `scope=eats.deliveries`); `authorization_code` (user consent)
- **Authorize endpoint:** `https://auth.uber.com/oauth/v2/authorize?client_id=…&response_type=code&redirect_uri=…&scope=…`
- **Scopes are space-delimited** (comma-separated scopes are rejected — documented gotcha: https://github.com/stevenmaguire/oauth2-uber/issues/1 citing `developer.uber.com/docs/ride-requests/guides/authentication/introduction#step-one-authorize`)
- **Known scopes:** `profile`, `request` (**privileged — needs Uber approval for production**), `ride_request`, `eats.store`, `eats.store.status.write`, `eats.order`, `eats.store.orders.read`, `eats.report`, `eats.pos_provisioning`, `eats.deliveries`, plus Ads API scopes
- **Default-scope behavior:** "If none are provided the default is the set selected in your application's dashboard. It is invalid to provide no scopes and have none selected in the dashboard." → dashboard-selected scopes are the fallback authorization set; test whether the authorize flow lets a caller *narrow* vs *widen* relative to dashboard.
- **Sandbox:** `https://sandbox-login.uber.com` + `https://test-api.uber.com`
- **SSO (mobile):** recommended via Android/iOS SDK SSO feature (per official docs); web SSO anchored at auth.uber.com with historically shared `*.uber.com` session cookies (report 219205 — verify current `Domain`/`SameSite` scoping, it may have changed since 2017)
- **Login UX:** auth.uber.com homepage shows phone-first login with "verification code by text or Whatsapp" consent — OTP-based primary auth, no password in the observed shell.

### Deep links / universal links
Sources: https://github.com/neteinstein/compareapp/blob/HEAD/docs/DEEP_LINKS.md ; https://developer.uber.com/docs/rides/deep-linking-action-applypromo (referenced therein); https://forum.ionicframework.com/t/uber-integration/18085
- **Native scheme:** `uber://` (e.g. `uber://?action=setPickup&…`); `client_id` documented as required (attribution) but tolerated absent in practice
- **Universal link:** `https://m.uber.com/ul/?action=setPickup&pickup[latitude]=…&client_id=…` → falls back to mobile-web/signup flow if app missing
- **Actions:** `setPickup` (pickup/dropoff params), `applyPromo` (`client_id` + `promo_code`)
- Malware precedent (2018, Symantec via SC Media/Dark Reading) abused the real `uber://` deep link to chain a fake-credential UI into the legitimate app's Ride Request activity — deep-link handling is a historically soft spot.

### Session/token handling (what's observable passively)
- OAuth access tokens + refresh tokens + expiry (standard OAuth 2.0; SDKs persist encrypted per https://github.com/manavgabhawala/UberSDK — old but structurally unsurprising)
- Web SSO: session cookies shared across `*.uber.com` as of 2017 report — **must re-verify**; look for `Domain=.uber.com` vs host-bound, `SameSite`, `__Host-`/`__Secure-` prefixes, and whether auth.uber.com rotates session on login (fixation check)

---

## [HYPOTHESIS SEEDS]

Rules for all of these: **owned accounts only** (`@wearehackerone.com` rider + driver accounts you register yourself), no touching other users' data, stop at PoC. Do NOT do account-oracle or invite/promo-enumeration testing — both are explicitly out of scope.

### H1 — Share-link GraphQL authorization is token-bound, not session-bound (m.uber.com/go/share/*)
- **Violated invariant:** an unauthenticated capability URL (share link) must authorize exactly one trip; the backing GraphQL poll must reject mutated/forged tokens and stop serving data the moment the share is revoked.
- **Where:** `m.uber.com/go/share/*` → backing GraphQL endpoint (polls ~1×/sec per trip-guard repo).
- **How to test (owned accounts only):** from owned rider account A, create a trip share link. (a) Mutate the share token (single-char flips, truncation, swap in a token-shaped value from a *second* share you created on owned account B) and observe whether the GraphQL response leaks trip B's live driver position/route — IDOR across capability URLs. (b) Revoke the share in-app, then keep polling the old token: does the endpoint keep returning live driver GPS (stale authorization)? (c) Replay a captured poll request without cookies entirely — is any session binding present at all?
- **Why it matters:** unauthenticated-by-design + live GPS + 642-upvote precedent class (bonjour `userUuid` disclosure, 542340). Safety bucket ($0–10k).

### H2 — OAuth scope confinement fails on auth.uber.com-issued tokens
- **Violated invariant:** a token minted for scope set S must be rejected on endpoints requiring scope T∉S; the authorize flow must not let a caller widen scopes beyond the dashboard-registered set.
- **Where:** `https://auth.uber.com/oauth/v2/authorize` + `/oauth/v2/token`; Riders API `POST /requests`, `PATCH /requests/{request_id}`, `GET /requests/{request_id}/receipts`.
- **How to test:** register an owned developer app with minimal scopes (e.g. `profile` only). (a) Mint a user token and call privileged endpoints (`POST /requests/estimate`, `GET /history`, `GET …/receipts`) — any 200 is scope-confusion. (b) In the authorize URL, request scopes *not* selected in the dashboard (e.g. add `request`) and see whether the issued token carries them (dashboard-default vs request-widening). (c) Replay an authorization `code` with a *different* `redirect_uri` at the token endpoint. (d) Send comma-separated scopes (`profile,request`) — documented as invalid; confirm it fails closed rather than parsing loosely.
- **Why it matters:** `request` scope is explicitly privileged/production-gated; scope-confusion → ride requests on behalf of users = "Unauthorized Requests" bucket ($0–10k).

### H3 — Cross-subdomain session acceptance without re-auth (post-219205)
- **Violated invariant:** a session established for a low-privilege surface (rider web) must not authenticate the holder on higher-privilege surfaces (partners/developer) without step-up; session cookies must be host- or audience-bound.
- **Where:** `riders.uber.com`, `partners.uber.com`, `developer.uber.com`, `auth.uber.com` cookie layer.
- **How to test:** with owned accounts, sign in on riders.uber.com only; inspect which cookies carry `Domain=.uber.com` vs host-only. (a) Present the rider-session cookies to partners.uber.com / developer.uber.com endpoints — any authenticated response is cross-surface acceptance. (b) Fixation check: capture pre-login session identifier at auth.uber.com, complete login, compare — unchanged value = session fixation. (c) Check `SameSite`/`__Host-`/`__Secure-` attributes; missing flags on *authentication* cookies are in-scope-adjacent (note: missing flags on *non-auth* cookies are explicitly out).
- **Why it matters:** exact class of the historic 219205 auth-bypass (shared cookie + subdomain takeover); even without takeover, cross-surface acceptance is an authn-boundary break.

### H4 — Universal-link actions execute cross-account state changes (m.uber.com/ul/)
- **Violated invariant:** a universal link carrying attacker-chosen parameters (`client_id`, `promo_code`, pickup/dropoff) must not mutate the *victim's* account state; promo application must be bound to the account the promo was issued to.
- **Where:** `https://m.uber.com/ul/?action=applyPromo&client_id=…&promo_code=…`, `action=setPickup`.
- **How to test:** obtain a promo code issued to owned account A (from your own promotions — no enumeration, that's out of scope). (a) As owned account B, open the `applyPromo` universal link with A's promo — does B's account receive the credit (missing promo↔account binding)? (b) `setPickup` with attacker `client_id`: does the resulting session/attribution context leak into the victim session or create bookings under the wrong attribution? (c) Open `applyPromo` with no authenticated session — does it queue the promo to be applied on next login (deferred cross-session state)?
- **Why it matters:** Monetary Impact bucket ($0–10k); promo/account-binding flaws are the classic rideshare logic bug. Stay inside "promos issued to your own accounts" — enumeration is out.

### H5 — Trip state-machine allows wrong-actor transitions (rider token vs driver actions)
- **Violated invariant:** only the legitimate actor may advance a trip's state; a rider credential must never perform driver-side mutations and vice versa; one account's `request_id` must be unusable from another account's token.
- **Where:** Riders API `PATCH /requests/{request_id}`, `DELETE /requests/{request_id}`, `GET /requests/{request_id}/receipts`, `PATCH /me`.
- **How to test:** two owned accounts (A rider, B rider; plus an owned driver account if obtainable). (a) With B's token, `GET /requests/{request_id}` using A's `request_id` — distinguishable success vs error is the IDOR signal (frame as authorization differential, not an existence oracle — oracles are out of scope). (b) With a rider token, attempt driver-semantics fields on `PATCH /requests/{request_id}`. (c) `PATCH /me` (documented as "apply a user promotion") with another account's promotion reference. (d) Cancel-flow: `DELETE` on a request_id belonging to A using B's token.
- **Why it matters:** mirrors the $1,500 trip-rating-change report (724522) and the $10k ride-history IDOR pattern; "Unauthorized Requests on Behalf of User" bucket.

### H6 — Stale OAuth artifacts: refresh-token and code replay across the v2 endpoints
- **Violated invariant:** authorization codes are single-use and bound to (client_id, redirect_uri); refresh tokens rotate; a used/replayed artifact must fail closed.
- **Where:** `https://auth.uber.com/oauth/v2/token` with `grant_type=authorization_code` / `refresh_token`.
- **How to test (owned app + owned accounts):** (a) Exchange the same authorization code twice — second exchange must fail. (b) Use a refresh token, then reuse the *old* refresh token after rotation — acceptance means no rotation. (c) Exchange a code issued for redirect_uri X while presenting redirect_uri Y. (d) Present an authorization code at the token endpoint with a *different* `client_id` than the one that requested it.
- **Why it matters:** token-replay flaws convert any single code/token leak (logs, referers, browser history) into persistent account access; ATO-adjacent without touching anyone else's account.

---

## Method & gaps (honest)
- **crt.sh direct fetch failed** (upstream timeout; not retried per fetch policy) — subdomain list is evidence-backed but not an exhaustive CT dump. Re-run via asset-recon endpoints or a live session before treating any "complete" inventory claim as final.
- **No JS-bundle analysis**: `m.uber.com` / `auth.uber.com` are JS SPAs; text fetch returns only the shell. Bundle URL discovery + endpoint mining needs a live browser session (deferred, not done here).
- **Secondary-source claims flagged**: the $10k `/api/v1/rides/{id}` IDOR and $15k JWT-algorithm-confusion entries come from a third-party knowledge base (https://github.com/gabson0x/bountyforge/blob/HEAD/skills/bug-bounty/knowledge.md), not from primary disclosed-report text — treat as pattern intelligence, not verified precedent.
- **Uber Movement (`ubermovement.com`)**: historic XXE report exists; verify it is still in scope before any contact.
- `drivers.uber.com` / `eats.uber.com` were task-suggested but not evidence-confirmed in this pass — confirm via DNS before scoping.

## Suggested next actions (for parent, not this passive task)
1. Live browser session: harvest `m.uber.com` + `auth.uber.com` JS bundles, mine API/GraphQL endpoints, map cookie `Domain` scoping across riders/partners/developer subdomains.
2. Register owned `@wearehackerone.com` rider + driver test accounts (18+, own accounts only per program terms).
3. Run H1–H6 as gated experiments inside the enforced research loop; SSRF ideas must use only the sheriff endpoint `http://dca11-pra.prod.uber.internal:31084/<handle>@wearehackerone.com`.
