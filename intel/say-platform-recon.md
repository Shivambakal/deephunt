# Say Technologies Platform — Passive Recon

Date: 2026-09-26. Method: read-only. No logins, no testing, no form submissions.
~20 single GET requests (public pages, JS bundles, crt.sh), standard browser UA, paced.
Evidence: JS bundles from `app.`, `auth.`, `voting.saytechnologies.com`; page HTML; crt.sh CT logs; one public whitepaper.

Scope note: `saytechnologies.com`, `*.say.rocks` are bounty-eligible per the Robinhood brief. `api.robinhood.com` paths discovered below fall under `*.robinhood.com`.

## [SURFACE MAP]

### Consumer app — `app.saytechnologies.com` (Next.js, shareholder Q&A)
Routes (from `_buildManifest.js`): `/`, `/login`, `/signup`, `/logout`, `/forgot-password`,
`/reset-password`, `/verify-email`, `/complete-profile`, `/invite`, `/link`,
`/messages-opt-out`, `/profile`, `/reply`, `/[slug]/[[...questionId]]`.
Sitemap enumerates dozens of public company-event slugs (`/tesla-2020-q2`, `/palantir-2024-q4`, …) — all public Q&A pages.

API clients (from `_app` chunk): everything routes to `https://issuers.saytechnologies.com/`:
- SSO/auth API → `/v1/` (`REACT_APP_SSO_API`)
- Consumer API → `/v3/` (`REACT_APP_CONSUMER_API`)

Auth endpoints (SSO v1, client-declared): `POST auth/registration/`, `POST auth/login/`,
`POST auth/otp/`, `POST auth/otp/verify/`, `POST /auth/refresh-token/`,
`POST /auth/resend-verification/`, `POST auth/update-email/`, `DELETE auth/user/`,
`POST users/magic-link/`.
Consumer v3 (client-declared): `GET holdings/`, `POST holdings/plaid_link_token/`
(`{redirectUri:"https://app.saytechnologies.com/link"}`), `POST holdings/exchange_plaid_token/`
(`{publicToken, metadata}`). Q&A ask flow uses `/ask` and `/askUnverified` routes.

### "Auth with Say" — `auth.saytechnologies.com` (OAuth2 provider for ownership verification)
- `POST oauth/authorize/` with `{clientId, responseType:"code", scope:"ownership_limited", redirectUri, state}`
- `GET oauth/theme/?client_id=` (per-client themed consent screen)
- `?oauth_state_id=` flow for resuming authorization state.
This is Say's "verify share ownership" OAuth product: third parties (issuers, brokers) redirect
shareholders here; Say asserts ownership back via an authorization code with `ownership_limited` scope.

### Proxy voting app — `voting.saytechnologies.com` (CRA SPA, Redux Toolkit Query)
The HTML leaks its full runtime config (`window.config` in page source):
- `REACT_APP_CONSUMER_URL`: `https://consumerapi.saytechnologies.com` → API at `/v3/`
- `REACT_APP_WARRENG_URL`: `https://api.robinhood.com/say-brokers`
- `REACT_APP_SNOOPDOGG_URL`: `https://api.robinhood.com/say-issuers`
- Plus Segment write key, Adobe embed key, `REACT_APP_MAINTENANCE_MODE` flag, assets on `broker-assets.saytechnologies.com`.

Confirmed API bases: `consumerapi.saytechnologies.com/v3/`, `api.robinhood.com/say-brokers`,
`api.robinhood.com/say-issuers`. All three hosts are live (404 on `/` root — Django-style, host up).
RTK Query endpoint fragments observed: `/brokers/`, `short-codes/`, `/messages/record-event/`,
`users/subscription-preferences/`, `/auth/refresh-token/`. Ballot/vote endpoints are in
lazily-loaded route chunks (not extracted passively).

Frontend routes confirm the voting workflow: `/proxy-votes/details`, `/proxy-votes/attend-meeting`,
`/proxy-votes/attend-meeting-confirmation`, `/corporate-action-elections/details|success`,
`/vote-results/`, `/voting-instructions/`, `/voting-instruction-results/`, `/election-results/`,
`/meeting-attendance/`, plus `WithdrawVote`, `EditBallot`, `change-ballot` UI actions.

### Subdomain inventory (crt.sh, 2026-09-26)
`saytechnologies.com` (~45 names): `app`, `auth`, `vote`, `voting` (+`voting-alt`, `voting-prod2`),
`issuer`, `issuer-alt`, `issuerportal`, `brokerportal`, `intermediary`, `intermediaryportal`,
`missioncontrol` (+`-alt`, `-temp`, `-prod2`), `portal`, `preferences`, `privacy`,
`legal-proxy`, `regulated-documents`, `materials`, `viewer`, `pay`, `election-reports`,
`tabulation-reports`, `meeting-attendance`, `share-range-analysis`, `shareholder-assets`,
`mc-profile-pictures`, `broker-assets`, `bulk-uploads`, `go`, `doc`, `docs`, `sso.prod2`,
`api.prod2`, `brokers.prod2`, `nexus.prod2`, `natedogg.prod2`, `shared-assets.prod2`.

`say.rocks` (~110 names): full environment sprawl — `app`/`auth`/`vote`/`voting`/`issuer`/`portal`/
`missioncontrol`/`brokerportal`/`intermediaryportal` each in `cloud`, `qa`, `sandbox`, `test`,
`adhoc` variants, plus `consumerapi` (cloud/qa), `api` (cloud/qa), `sso` (cloud/qa),
`notifications`, `postal` (proxy-materials mail?), `trades`, `hoop`, `hub`, `share`,
`waitlist`, `santasworkshop`, `hghiatest`, `tabulation-reports.cloud`, `election-reports`.

Notable: `vote.saytechnologies.com` returns empty replies to plain curl (possible bot filtering);
`docs.`/`doc.saytechnologies.com` and `nexus.prod2` return empty replies. `missioncontrol*` is the
likely admin console. `tabulation-reports` / `election-reports` hold vote count data.

## [AUTH MODEL]

1. **Account auth (SSO API v1):** email+password (`auth/registration/`, `auth/login/`),
   email-OTP login (`auth/otp/` → `auth/otp/verify/` with `{otp, csrf_token}`),
   magic link (`users/magic-link/`), password reset, email verification (`/auth/resend-verification/`),
   email change (`auth/update-email/` with `{newEmail}`), account deletion (`DELETE auth/user/`).
2. **Tokens:** access token kept in memory store; **refresh token persisted in `localStorage`**
   (`window.localStorage.setItem("refresh-token", …)`); `POST /auth/refresh-token/` renews.
   CSRF uses cookie + header (`xsrfCookieName`/`xsrfHeaderName`, `csrf_token`).
   Axios interceptor auto-logs-out on 401s from `users/*` paths.
3. **Share-ownership verification (the core trust primitive):** user links a brokerage via Plaid
   (`holdings/plaid_link_token/` → Plaid Link widget from `cdn.plaid.com` →
   `holdings/exchange_plaid_token/` with `{publicToken, metadata}`); `GET holdings/` lists verified
   positions. The "Verify shares" button routes to `/link`. Verified status gates the "verified
   shareholder" badge; **unverified users can still ask questions** via the `/askUnverified` flow
   (routed there when verified holdings < threshold).
4. **"Auth with Say" OAuth:** third-party `clientId` + `redirectUri` + `state`; user links brokerage,
   Say issues an auth `code` asserting ownership under `ownership_limited` scope.
5. **Registration side-channel:** signup posts `{choice, email, slug}` ("fund position") to a
   third-party endpoint (`bs0na1z` — Airtable-shaped ID) via `sendFundPostionToAirtableApi`, and
   sends a client-controlled `Redirect: https://saytechnologies.com/` header with registration calls.

## [STATE MACHINES]

**M1. Question lifecycle (Q&A):** submit (`/ask`) → if insufficient verified holdings, `/askUnverified`
→ moderation/review (issuer-side, implied) → published → upvoting (`userCanVote`, `userDidUpvote`,
login required; "Verified shareholders of all sizes can ask and upvote") → answered by company.
Privacy rule in UI: "Shares will be shown after 3 shareholders have voted."

**M2. Proxy vote lifecycle:** ballot open → review proposals → cast vote → confirmation →
edit/withdraw (`EditBallot`, `WithdrawVote`, `change-ballot`) → deadline passes → ballot closed
("This ballot closed on … when the vote deadline passed") → tabulation → results
(`/vote-results/`, `/election-results/`, `tabulation-reports`). Also: meeting-attendance
registration (`attend-meeting` → confirmation), corporate-action elections, consent solicitations.

**M3. Brokerage linking:** request link token → Plaid auth → exchange public token → holdings
recorded → verified badge. Unlink path exists (`holdings/` GET implies management).

**M4. Auth lifecycle:** register → verify email → login; OTP: request → verify (must be single-use,
expiring); password reset: request → token → reset (single-use); email change via `auth/update-email/`.

**M5. OAuth ("Auth with Say"):** client initiates → `oauth_state_id` created → user verifies ownership
→ consent → `POST oauth/authorize/` → code → redirect to `redirectUri` with code+state.

## [HYPOTHESES] (ranked)

1. **H1 — Vote weight / ownership confusion (proxy voting).** The ballot API may trust client-side
   share quantities or a stale holdings snapshot when recording votes. Invariant: recorded vote weight
   must equal the verified position at record date, server-side, for every proposal. Highest integrity
   impact on the platform (contested meetings are adversarial).
2. **H2 — Cross-shareholder ballot IDOR.** Ballot / voting-instruction objects keyed by guessable IDs;
   test whether one principal can read or submit against another's ballot ID (record only the
   access-control decision).
3. **H3 — OAuth `redirect_uri` validation on `auth.saytechnologies.com`.** `POST oauth/authorize/`
   takes a client-supplied `redirectUri`; if not strictly allowlisted per `clientId`, auth codes
   (ownership assertions) leak to an attacker. Also test `state` handling and code single-use.
4. **H4 — "Verified shareholder" badge bypass.** Unverified ask flow (`/askUnverified`) vs verified;
   test whether the verified flag on questions/upvotes can be set without a linked brokerage holding
   the relevant shares.
5. **H5 — Upvote fraud / ballot stuffing.** `userCanVote`/`userDidUpvote` are client state; test
   duplicate upvotes (add/remove race), upvoting while logged out, and upvote-count manipulation —
   upvotes decide which questions management answers.
6. **H6 — Email-change account takeover.** `POST auth/update-email/ {newEmail}` — determine whether
   it requires re-verification or OTP; a session-only email change is a takeover primitive.
7. **H7 — Registration `Redirect` header open redirect.** `auth/registration/` accepts a client
   `Redirect` header — check for an allowlist.
8. **H8 — OTP weaknesses.** `auth/otp/` / `auth/otp/verify/`: rate limiting, OTP entropy/lifetime,
   verification without the CSRF token, OTP reuse.
9. **H9 — Magic-link token strength.** `users/magic-link/` token entropy, expiry, single-use.
10. **H10 — Refresh token in `localStorage`.** Any stored-XSS sink on any Say web app becomes full
    account takeover; prioritize DOM XSS source→sink mining on the voting and consumer apps.
11. **H11 — Plaid token-exchange binding.** `holdings/exchange_plaid_token/` with `{publicToken,
    metadata}` — verify the exchanged holdings bind to the authenticated user and the token is
    single-use.
12. **H12 — Unlink/revoke gaps.** After removing a linked brokerage, do "verified" badges on existing
    questions/votes persist? Does the OAuth layer re-check holdings freshness?
13. **H13 — Tabulation/election report exposure.** `tabulation-reports.*` / `election-reports.*` —
    check for unauthenticated access to per-shareholder vote records.
14. **H14 — QA/sandbox/test env weakness.** `*.say.rocks` qa/sandbox/test/adhoc apps may run weaker
    auth, debug endpoints, or production data.
15. **H15 — `missioncontrol` admin surface.** Identify the admin console's auth model and test for
    privilege boundaries (issuer vs Say-staff roles).
16. **H16 — Vote-after-deadline / withdraw-after-tabulation.** Replay vote submission after the
    deadline message; withdraw a vote after results publish — check server enforcement vs UI gating.

## [REJECTED / NOT VERIFIABLE PASSIVELY]
- Exact REST paths for question submit/upvote and ballot cast (in lazy-loaded chunks; need
  authenticated traffic analysis).
- Whether `vote.saytechnologies.com` empty replies are bot-filtering or dead (needs browser).
- `docs.`/`doc.`/`nexus.prod2` hosts (empty replies; likely internal-only).

## Sources
- `https://app.saytechnologies.com/` HTML + `_buildManifest.js` + JS chunks (`_app`, `index`,
  `[slug]/[[...questionId]]`, `link`, `reply`) — fetched 2026-09-26.
- `https://auth.saytechnologies.com/` HTML + `index-662135008abc811f.js` — fetched 2026-09-26.
- `https://voting.saytechnologies.com/` HTML (env config) + `main.039fb5c3.js` — fetched 2026-09-26.
- crt.sh queries for `%25.saytechnologies.com` and `%25.say.rocks` — 2026-09-26.
- `https://app.saytechnologies.com/sitemap.xml`, `/robots.txt` — fetched 2026-09-26.
- Say whitepaper (Governance Professionals): https://higherlogicdownload.s3.amazonaws.com/GOVERNANCEPROFESSIONALS/a8892c7c-6297-4149-b9fc-378577d0b150/UploadedImages/Say.pdf
- Say mobile-integration announcement: https://www.globenewswire.com/en/news-release/2020/01/23/1974477/0/en/Say-Launches-Mobile-Integration-Capability-for-Shareholder-Communication-Platform-with-Fidelity-Investments.html
- Robinhood stock-token voting plans (Say as voting infra): https://blockonomi.com/robinhood-hood-stock-ceo-announces-voting-rights-for-tokenized-stock-products/

Nothing above is a confirmed vulnerability. Every hypothesis needs authenticated reproduction with
synthetic accounts and minimal test cases, within the live program brief.
