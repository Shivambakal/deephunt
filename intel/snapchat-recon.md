# Snapchat Bug Bounty — Passive Recon

**Date:** 2026-09-26
**Method:** READ-ONLY passive recon. No logins, no form submissions, no testing. Low-volume single GETs only (HackerOne program pages, crt.sh, public pages, public developer docs, one web search).
**Program:** https://hackerone.com/snapchat (public, launched Apr 2015, 92% response efficiency)

---

## [SCOPE]

Source: https://hackerone.com/snapchat/policy_scopes (46 assets, last scope update Dec 18, 2024) and https://hackerone.com/snapchat (policy text).

### In-scope (bounty-eligible), by severity cap

**Critical cap — Tier A core:**
| Asset | Notes | Resolved reports |
|---|---|---|
| `web.snapchat.com` | Snapchat for Web | 24 (3%) |
| `accounts.snapchat.com` | [Core] account management website | 66 (9%) — hottest auth surface |
| `app.snapchat.com` | [Core] main server-side app on Google App Engine (`feelinsonice-hrd.appspot.com`) | 51 (7%) |
| `business.snapchat.com` | Business Manager | 16 (2%) |
| `store.snapchat.com` | Bitmoji merch store | 1 |
| `https://lensstudio.snapchat.com/api/` | JS source-code scope | 1 |
| `com.snapchat.android` | Android app | 71 (10%) — most reported |
| `*.sc-corp.net`, `*.sc-core.net` | Internal services (wildcards) | 3 + 7 |
| Tier A - Core Assets (other) | — | 44 (6%) |

**High cap:**
| Asset | Notes | Resolved |
|---|---|---|
| `kit.snapchat.com` | [Core] Snap Kit web app + SDKs | 23 (3%) |
| `ads.snapchat.com` | Ads | 30 (4%) |
| `snappublisher.snapchat.com` | [Core] publisher tool | 22 (3%) |
| `geofilters.snapchat.com` | [Core] on-demand geofilters purchase | 6 |
| `create.snapchat.com` | Geofilter creation tool | 0 |
| `my.snapchat.com` | Spotlight on the web | 2 |
| `businesshelp.snapchat.com` | Salesforce instance | 4 |
| `com.toyopagroup.picaboo` | iOS app | 25 (3%) |

**Medium cap — Tier B non-core (Bitmoji, PlayCanvas):** `www.bitmoji.com` (22 reports), `www.bitstrips.com` (11), `playcanvas.com` (21), `login.playcanvas.com` (3), `forum.playcanvas.com`, `launch.playcanvas.com`, `store/relay/rt/msg/code/blog.playcanvas.com`, `playcanv.as`, `com.bitstrips.imoji` (iOS + Android), Lens Studio (executable, 11).

**Low cap:** `story.snapchat.com` (5), `spectacles.com` (2), `scan.snapchat.com` (2), `map.snapchat.com` (1).

### Out-of-scope (explicit)
- `support.snapchat.com` (static support site) — ineligible
- Spectacles hardware + Spectacles charging case — ineligible
- `returns.spectacles.com` (owned by NetSuite — report to them)
- `http://dev*.playcanvas.com`, `dev.playcanv.as` — ineligible

### Policy exclusions that shape testing (https://hackerone.com/snapchat)
- **Test accounts only.** Never touch another person's account/data. Inadvertent access → stop, notify, delete.
- **No automated tooling** that generates significant traffic / impairs the app. (Manual-style, low-volume only.)
- **Device attestation reports are excluded**: anything centered on `x-snapchat-att` header, `req==token`, `device==check_token` params.
- **Lack of email verification during registration** — explicitly not qualifying.
- Social engineering, physical access, vendor vulns, cert-pinning absence, screenshot-detection avoidance, 2FA bypass requiring physical device access, passive mixed content, low-impact open redirect (chainable ones still welcome), generic stack traces, spam-only issues — all excluded.
- Minimum bounty **$250**. Typical: Critical RCE $35k / client RCE $25k; High auth bypass or mass-ATO logic flaw $15k; **IDOR exposing another user's friend list $10k**; Medium $5k; Low XSS/XSRF $4k. Non-core sites pay less at panel discretion.
- Program stats (https://hackerone.com/snapchat/hacktivity): $1,839,731 total paid, 728 resolved, 40 assets in scope, 501 reports/90 days. Recent payouts observed: $25,000, $15,000, $7,500 ×2, $4,000, $500, $150, $250.

---

## [SUBDOMAIN INVENTORY]

Source: `https://crt.sh/?q=%25.snapchat.com&output=json` (queried 2026-09-26; ~5,943 cert rows scanned). Grouped by function; only currently-issued (2026) certs listed.

**Auth / identity (highest value — matches hottest scope assets):**
- `accounts.snapchat.com` — in scope (Critical), 66 resolved reports
- `pro-accounts.snapchat.com` — "pro" accounts surface (Amazon-issued cert, renewed 2026-06-18)

**Web clients:**
- `web.snapchat.com` — in scope (Critical). NOTE: serves `Oops! Something went wrong…` (Snapchat v13.79.0) to non-browser fetches — JS/bot-gated SPA. Static asset host observed: `cf-st.sc-cdn.net`.
- `app.snapchat.com` — in scope (Critical), GAE-hosted main server app
- `my.snapchat.com` — in scope (High), Spotlight web
- `story.snapchat.com`, `map.snapchat.com` / `maps.snapchat.com`, `s.snapchat.com` — in scope (Low)

**Ads / business:**
- `ads.snapchat.com` — in scope (High), 30 resolved reports
- `business.snapchat.com` — in scope (Critical), Business Manager, 16 resolved
- `marketingapi.snapchat.com` — Marketing API host
- `businesshelp.snapchat.com` — in scope (High), Salesforce instance
- `learn.ads.snapchat.com` (+ `cloud/image/click/view.learn.ads.snapchat.com`) — ads learning subdomains (ExactTarget/Salesforce-issued certs)

**Developer / Snap Kit:**
- `kit.snapchat.com` — in scope (High), Snap Kit web app + SDKs, 23 resolved
- `developers.snapchat.com`, `developer.snapchat.com`, `docs.snapchat.com` — dev docs
- `play.snapchat.com`, `create.snapchat.com` (in scope High), `snappublisher.snapchat.com` (in scope High, 22 resolved)

**Content / creators:**
- `creators.snapchat.com`, `snaporiginals.snapchat.com`, `trends.snapchat.com`, `scan.snapchat.com` (in scope Low), `geofilters.snapchat.com` (in scope High), `geofilters-community-api.snapchat.com`, `lens.snapar.com`

**Interesting / test-adjacent (verify scope before touching):**
- `prodsec-test.snapchat.com` (DigiCert, issued 2026-07-30) — name suggests Snap's own product-security test host; NOT on the scope list → treat as out-of-scope unless the Scope tab says otherwise
- `session.snapchat.com` (DigiCert, to 2027-03-03) — session infra
- `app-analytics.snapchat.com`, `app-analytics-v2.snapchat.com`, `staging.app-analytics.snapchat.com`, `app-analytics-dev.snapchat.com` — analytics + staging/dev
- `am-api.snapchat.com`, `amchat.snapchat.com` — messaging API surface
- `iosbeta.snapchat.com` (Let's Encrypt, 2026-09-05) — iOS beta distribution
- `lenstudio.snapchat.com`, `studio-crash.snapchat.com` — Lens Studio
- `click.snapchat.com`, `groove.snapchat.com`, `ds.snapchat.com`, `publish.snapchat.com`, `creator.snapchat.com`
- `lawenforcement.snapchat.com`, `safety.snapchat.com`, `parents.snapchat.com`, `educators.snapchat.com`, `forbusiness.snapchat.com`, `investor(s).snapchat.com`
- `support.snapchat.com`, `help.snapchat.com` — **out of scope** (static support)

**Not observed in CT (note, not proof of absence):** no `web.snapchat.com` cert row in the scanned window (likely served under a wildcard/CDN cert), no `mcp.snapchat.com` cert row (Ads MCP server referenced in third-party docs — verify independently before testing).

---

## [API SURFACE]

All endpoints below from public documentation (no probing performed).

**Login Kit / Snap Kit OAuth2** — source: https://developers.snapchat.com/snap-kit/login-kit/overview
- Authorize: `GET https://accounts.snapchat.com/accounts/oauth2/auth`
- Token: `POST https://accounts.snapchat.com/accounts/oauth2/token` (code exchange + refresh)
- Flows: Authorization Code + PKCE (public clients), server-side auth code (confidential, refresh tokens), **Implicit Grant** (`response_type=token`, token returned in URL fragment `#`)
- Auth code lifetime: **10 minutes**, single-use semantics per `invalid_grant` on reuse ("Expired or already-used authorization code")
- Access token TTL: **3600s**; refresh tokens issued for code/PKCE and server-side flows; implicit flow has **no refresh**
- Scopes: `https://auth.snapchat.com/oauth2/api/user.display_name`, `.../user.external_id` (app-specific stable ID), `.../user.bitmoji.avatar` (user-toggleable), `.../camkit_lens_push_to_device` (Camera Kit apps)
- Userinfo: `GET https://kit.snapchat.com/v1/me` with `Authorization: Bearer <access_token>` (per https://github.com/firebase/firebaseui-web/blob/HEAD/CUSTOM_AUTHENTICATION.md)
- **No OpenID Connect**: no `/.well-known/openid-configuration`, no `id_token`; identity comes from `/me` (per https://github.com/api-evangelist/snapchat/blob/HEAD/skills/snapchat-authenticate.md)
- Developer portal: https://kit.snapchat.com/manage/apps — per-app OAuth client IDs, redirect URIs, Login Kit scope toggles, **Staging vs production, Trusted Origins / Platform Identifiers, Demo Users** for staging (per https://github.com/auth0/docs-v2/blob/HEAD/auth4genai/integrations/snapchat.mdx and Firebase docs above)
- Login Kit SDKs are being **deprecated** in favor of direct OAuth2 integration (docs page, 2026)

**Marketing (Ads) API** — per https://github.com/api-evangelist/snapchat/blob/HEAD/skills/snapchat-launch-campaign.md
- Base: `https://adsapi.snapchat.com/v1`
- Auth: OAuth2 bearer from `accounts.snapchat.com`; token refresh at `https://accounts.snapchat.com/login/oauth2/access_token`
- Hierarchy: Organization → Ad Account → Campaign → Ad Squad → Ad; Media → Creative
- Notable API properties: **no idempotency key** on creates (retry → duplicates), **no sandbox** (production writes)

**Ads MCP server** — `mcp.snapchat.com`, agent-scoped token with `snapads.read` only (per api-evangelist/snapchat-authenticate.md; no CT row observed — verify before testing)

**Web surfaces (page fetches 2026-09-26):**
- `https://web.snapchat.com` → bot/JS gate: "Oops! Something went wrong…" (v13.79.0); real client is a React SPA. No bundle URLs extractable via text fetch.
- `https://accounts.snapchat.com` → "Log in to Snapchat" page: username **or phone number** login ("Use phone number instead"), Sign Up link, standard footer. Web session + OAuth authorization server share this host.

---

## [AUTH FLOWS]

1. **accounts.snapchat.com web login** (source: https://accounts.snapchat.com, fetched 2026-09-26): username-or-phone + password form; "Use phone number instead" toggle; new-user signup path. This host is BOTH the interactive login page AND the OAuth2 authorization/token server — session-cookie and OAuth-token issuance share infrastructure, which is exactly where cross-surface confusion bugs live.
2. **Login Kit OAuth2** (source: https://developers.snapchat.com/snap-kit/login-kit/overview): auth-code + PKCE (recommended), server-side code flow (client_secret, refresh), implicit grant (fragment token, no refresh). `state` required for CSRF. Redirect URI must match registration.
3. **Snap Kit developer app model** (sources: developers.snap.com overview; auth0/docs-v2 snapchat.mdx; firebaseui-web CUSTOM_AUTHENTICATION.md): apps registered at `kit.snapchat.com/manage`; per-app Confidential OAuth2 client ID/secret; redirect URIs per app version; **Staging environment with Demo Users** (Snapchat usernames allowlisted for login) and **Trusted Origins**; Login Kit scopes toggled per app version.
4. **Marketing API auth** (source: api-evangelist skill doc): same `accounts.snapchat.com` OAuth bearer, 3600s TTL, `GET /me/organizations` → org → ad accounts; 403 on insufficient Business Manager role.
5. **web.snapchat.com session**: SPA (v13.79.0); session handling details not observable passively (bot-gated). Device attestation (`x-snapchat-att`, `req==token`, `device==check_token`) exists on API traffic but is **explicitly excluded** from the bounty — do not test it.

---

## [HYPOTHESIS SEEDS]

Each: violated invariant → where → how to test with **owned accounts only** (two test Snapchat accounts + one owned Snap Kit dev app, per program's test-account rule). All require a live browser session; none tested yet.

**H-1 — Login Kit `redirect_uri` validation bypass.**
Invariant violated: authorization codes must be delivered ONLY to byte-exact pre-registered redirect URIs.
Where: `GET https://accounts.snapchat.com/accounts/oauth2/auth` (in scope via `accounts.snapchat.com`, Critical).
How: register an owned Snap Kit app with redirect `https://owned.example/cb`; then request auth with mutated variants owned by you — trailing-slash, path traversal (`/cb/../evil` on your own second domain), query-param append, subdomain swap between two domains you own, `http:` downgrade. Observe whether the code is issued to any non-registered URI. Benign explanation to disprove first: strict string match (expect rejection).

**H-2 — Authorization code replay / PKCE downgrade.**
Invariant violated: codes are single-use; a PKCE-bound code must not exchange without the original `code_verifier`.
Where: `POST https://accounts.snapchat.com/accounts/oauth2/token` (docs: `invalid_grant` = "Expired or already-used authorization code").
How: with an owned app, complete one PKCE flow, exchange the code twice (expect second to fail); then attempt exchange of a PKCE-issued code WITHOUT `code_verifier`, and with a wrong verifier. Any success = finding. Disprove-benign: verify failures are consistent, not flaky.

**H-3 — Implicit-flow token in fragment leaks via redirect chain.**
Invariant violated: fragment-carried access tokens must never be transmitted to any server (fragments stay client-side — unless a redirect or JS forwards them).
Where: Login Kit implicit flow (`response_type=token`) on an owned app.
How: set your owned redirect URI to a page YOU control that logs full request URLs server-side; run the implicit flow; check whether the access_token ever arrives at your server (it shouldn't — fragment isn't sent). Then test with an intermediate redirector hop. Any server-side token arrival = finding.

**H-4 — Cross-subdomain session confusion (accounts ↔ web).**
Invariant violated: a session minted for one surface must not authenticate another surface's privileged actions.
Where: `accounts.snapchat.com` (web login session) vs `web.snapchat.com` (messaging client), both in scope, Critical.
How: sign in on `accounts.snapchat.com` with test account A; capture session cookies; replay them against `web.snapchat.com` API calls (read own data only) and vice versa. Expect rejection / separate session domains. Any cross-acceptance that elevates capability = finding. (Note: 66 resolved reports on accounts.snapchat.com — auth surface is proven soft.)

**H-5 — Marketing API cross-organization IDOR.**
Invariant violated: every object read must be authorized against the caller's organization membership, not just the bearer token's validity.
Where: `https://adsapi.snapchat.com/v1` (via `ads.snapchat.com`, High, 30 resolved reports).
How: create TWO owned ad accounts under TWO owned organizations; with org-1's token, request org-2's `/adaccounts/{id}`, `/organizations/{id}/adaccounts`, campaigns, creatives, and media download URLs. Expect 403/404 uniformly. Distinguishable errors or any data = finding. Also test `business.snapchat.com` role boundaries: two owned users in one org with different roles, attempt admin mutations as the lesser role.

**H-6 — Bitmoji avatar consent revocation doesn't propagate.**
Invariant violated: revoking a user-toggleable scope must stop data flow to the third-party app.
Where: scope `https://auth.snapchat.com/oauth2/api/user.bitmoji.avatar` (documented as user-toggleable) via an owned Snap Kit app.
How: authorize with bitmoji scope on test account; confirm avatar returned from `kit.snapchat.com/v1/me`; revoke the toggle in Snapchat settings; re-call `/v1/me` with the still-valid access token AND after refresh. Avatar still served post-revocation = stale-consent finding.

**H-7 — Login CSRF via `state` validation gap.**
Invariant violated: the `state` parameter must be bound to the user's session and validated on return; an attacker must not be able to complete another user's login on the attacker's app session.
Where: Login Kit auth flow on an owned app.
How: initiate flow as test account A (capture the redirect to accounts.snapchat.com), complete authorization as test account B in a second session, deliver B's `code&state` to A's callback session. If the app links B's Snapchat identity to A's app session (login CSRF), that's the finding — test with owned app + two owned accounts only.

**Out-of-scope reminders for the testing phase:** `support.snapchat.com`, Spectacles hardware, `prodsec-test.snapchat.com` (not on scope list — verify before touching), device-attestation headers/params, automated high-volume tooling, anything touching non-owned accounts.

---
*Recon compiled 2026-09-26 from public sources only. No authentication performed, no requests beyond single page/document GETs and one web search.*
