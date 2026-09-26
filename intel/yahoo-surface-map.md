# Yahoo — Authenticated Attack Surface Map (manual-only VDP)

Passive mapping only. No logins, no testing performed. Prepared 2026-09-26.
Companion to `yahoo-vdp-recon.md` (program rules, scope, disclosed-report
patterns). This file models the *authenticated* surface from public evidence:
OAuth flow, Mail web surface, account security/recovery flows, legacy
remnants. Exact internal webapp API paths require authenticated JS analysis
later — this map marks every such gap explicitly.

**Program rules that constrain all later testing:** manual only (no scanners),
tag requests `X-Bug-Bounty: HackerOne-<username>`, test accounts must use
`<username>+x@wearehackerone.com`, test ONLY owned accounts, no public
disclosure without written permission. (See yahoo-vdp-recon.md.)

---

## [SURFACE MAP]

### 1. Identity & authentication

| Component | What is publicly known |
|---|---|
| `login.yahoo.com` | Central login. Legacy redirect params `.done`, `.src`, `.intl`, `.partner` (the $7k Flickr token-theft bug was prefix-only validation on `.done`). Session cookies historically named `.ys` / `.data` per writeups. |
| `login.yahoo.com/forgot` | Sign-in Helper — the account-recovery entry point (see Flow Models). |
| `account.yahoo.com` | Account Info shell: Personal info · **Account security** · Recent activity · Preferences · Help. The Account security page is the privilege-transition hub (password change, Account Key, 2SV, recovery options). |
| `api.login.yahoo.com/oauth2/request_auth` | OAuth 2.0 authorization endpoint (publicly documented by integrators). |
| `api.login.yahoo.com/oauth2/get_token` | OAuth 2.0 token endpoint. Form-encoded POST: `grant_type=authorization_code`, `redirect_uri`, `code`, `client_id`, `client_secret`. |
| `api.oauth.yahoo.com` | OAuth service host; an unauthenticated `/health` exposure was found there in 2026 (recon). Suggests other service endpoints on the same host. |
| `developer.yahoo.com/apps/` | OAuth app registration (create app → client_id/client_secret, API permissions, Redirect URI(s), Home Page URL). The redirect_uri validation rules of *your own registered apps* are the legal test vector for OAuth destination bugs. |
| `open.login.yahoo.com` (legacy) | Older OpenID-era login host referenced in historical docs; verify current status later. |

### 2. Yahoo OAuth 2.0 — confirmed public facts

Sources: Nylas provider guide
(https://developer.nylas.com/docs/provider-guides/yahoo-authentication/?redirect=reorg),
multiple open-source Yahoo integrations
(e.g. https://github.com/jhastings843/fantasy-hub/blob/HEAD/docs/superpowers/specs/2026-08-30-yahoo-league-source-design.md,
https://github.com/amolrairikar/leagueql-app/blob/HEAD/docs/requirements/backend/BE-022-yahoo-oauth.md).

- **Authorize:** `GET https://api.login.yahoo.com/oauth2/request_auth?client_id=…&redirect_uri=…&response_type=code&scope=…&state=…` (+ PKCE `code_challenge`/`code_challenge_method=S256` supported).
- **Token exchange:** `POST https://api.login.yahoo.com/oauth2/get_token`, `Content-Type: application/x-www-form-urlencoded`.
- **Token response:** `{access_token, token_type: "bearer", expires_in: 3600, refresh_token, xoauth_yahoo_guid}`.
- **Refresh-token lifecycle:** long-lived; **survives password changes** (documented by integrators). Access token ~1 hour.
- **`redirect_uri=oob` is still supported** — out-of-band flow: Yahoo displays the code to the user, who pastes it back. No HTTPS callback needed.
- **Redirect URIs must be HTTPS** (one integrator notes Yahoo rejects plain-http URIs; another registered `http://localhost` — treat as unverified nuance, confirm during app registration).
- **Known scopes:** `mail-r`, `mail-w`, `fspt-r` (fantasy read), `sdct-r`, `openid`, `profile`, `email`. App registration selects API permissions per app.
- **User GUID** (`xoauth_yahoo_guid`) is the stable cross-app user identifier.
- Yahoo Mail scope grants are used by third-party mail-sync products (`mail-r`/`mail-w`).

### 3. Yahoo Mail (`mail.yahoo.com`)

The repeat $10k surface (two stored-XSS payouts on the HTML sanitizer).
Public feature knowledge (help docs, reviews):

- Message list / reading pane / compose editor (rich text).
- **HTML sanitizer** on inbound message rendering — invariant target #1.
- Attachment handling: previewers (docs, images, PDFs), download, virus scan.
- Signatures (stored, rendered into composed mail — the 2016 PoC self-replicated via signature).
- Filters/rules (server-side filtering with user-controlled criteria + actions).
- Vacation responder / auto-reply.
- Calendar invites rendered inside mail.
- Multiple-account management, folders, spam controls.
- **Internal webapp API:** exact paths require authenticated JS-bundle mining
  (mail.yahoo.com JS not fetchable without login). GAP — enumerate during
  authenticated phase.

### 4. Account security pages (privilege-transition hub)

From Yahoo Help + how-to guides (e.g.
https://www.techradar.com/how-to/how-to-change-your-yahoo-mail-account-password-or-reset-it,
https://y.gogonow.de/help.yahoo.com/kb/new-yahoo-mail/reset-yahoo-password-sln27051.html):

- **Ways of signing in:** Password (change), Yahoo Account Key, 2-step verification.
- **Account Key:** push-approval sign-in replacing passwords. **Mutually exclusive with 2SV** — enabling one disables the other. Resend/approve flow; fallback to "Use text or email to sign in" → enter missing phone digits → SMS code → alternate email.
- **2-step verification:** SMS codes, authenticator app (TOTP), security keys (WebAuthn). Authenticator enrollment **requires ≥2 recovery methods on the account** and issues an **emergency recovery code**.
- **Recovery options:** recovery email address, recovery phone number (add/edit/delete).
- **Recent activity:** sign-in history review.
- Notable UX fact: how-to guides describe reaching the Account Security page
  and changing the password **without a fresh password prompt in some paths**
  ("If the Account Security tab appears without prompting for a password…").
  → test-ready: is fresh authentication required for privilege transitions?

### 5. Legacy / adjacent surfaces

| Surface | Status (public evidence) |
|---|---|
| YQL (`query.yahooapis.com`, `weather.yahooapis.com`, `datatables.org`) | **Retired Jan 3, 2019** (YDN announcement). Dead — but old client code/SDKs may still reference endpoints; a still-live remnant would be high value. |
| Yahoo OpenID 2.0 | Obsolete per OpenID Foundation; third parties removed Yahoo OpenID backends (2017–2020). Legacy only. |
| Yahoo Classic Mail | Shut down Jan 31, 2019; users migrated to current Mail / Basic Mail. |
| Third-party login (Google/Facebook IDs on Yahoo) | Removed (Mayer era). Yahoo ID required. |
| `*.yahooapis.com` remnants | `weather-ydn-yql.media.yahoo.com/forecastrss` was the post-YQL weather endpoint — check if still live. |
| AOL / Compuserve / Netscape ISP hosts (`*.aol.com`, `*.compuserve.com`, `*.isp.netscape.com`, `*.lite.aol.com`, wmconnect.com) | In scope per policy; oldest stacks; subdomain-takeover + legacy-auth candidates. |
| Flickr (`flickr.com`) | Separate app, shared Yahoo identity. Precedents: token-redirect ATO ($7k), stored XSS via tagging, help-forum CSP gap. |
| Fantasy Sports API | OAuth `fspt-r` scope; structured IDs (`449.l.12345.t.1`); XML responses. Cross-league/team IDOR candidate. |
| Ad hosts (`rmaitrack.ads.vip.bf1.yahoo.com` — header injection precedent; DSP/ad-manager) | In scope; infra-adjacent. |
| `sb*.geo.sp1.yahoo.com`, `marketing-dam.yahoo.com` | Disclosed-report hosts (RCE/LFI precedents); verify live scope before touching. |
| Deleted Yahoo IDs | **Not recycled** (per Yahoo Help) — no re-registration takeover vector there. |

---

## [FLOW MODELS]

### F1. OAuth 2.0 authorization-code flow (third-party "Login with Yahoo")

```
1. RP → GET api.login.yahoo.com/oauth2/request_auth
        ?client_id=C&redirect_uri=R&response_type=code&scope=S&state=T[&code_challenge=…]
2. Yahoo: user authenticates (session) → consent screen (app name, scopes)
3. Yahoo → 302 R?code=AUTH_CODE&state=T
4. RP backend → POST api.login.yahoo.com/oauth2/get_token
        {grant_type=authorization_code, code, redirect_uri=R, client_id, client_secret}
5. Yahoo → {access_token (1h), refresh_token (long-lived), xoauth_yahoo_guid}
6. RP → API calls with Bearer access_token; refresh via grant_type=refresh_token
```

**Trust boundaries:** Yahoo must deliver `code` ONLY to the exact registered
`R`; `code` must be single-use and bound to `C`; RP must validate `state`.
Known Yahoo quirks: `redirect_uri=oob` bypasses R entirely (user-pasted code);
refresh tokens survive password change.

### F2. Account recovery (Sign-in Helper) — `login.yahoo.com/forgot`

```
1. Enter identifier (Yahoo email / phone / recovery email) → Continue
2. Human-verification check (CAPTCHA-style)
3. Account located → offered recovery methods (subset, based on what's registered):
   a. SMS code to recovery phone (may require entering missing digits first)
   b. Email code to recovery address
   c. Account Key push approval (if enabled)
   d. "Try another way to sign in" → alternate method / security questions (if set)
4. Enter code / approve → authenticated → forced password reset
5. Post-reset: prompted to review recovery info
```

**State of interest:** which methods are offered is server-decided; each step
is a state machine transition. Rate limit: SMS resends capped per day
(24h lockout documented).

### F3. In-session password change

```
1. Authenticated → Account Info → Account security
2. "Ways of signing in" → Password → enter new password → Continue
3. Success → prompted to review recovery info
```

**Open question:** is fresh authentication (re-enter password) required at
step 2? Public how-tos suggest not always. If not, session theft = silent
password change.

### F4. Account Key enrollment / 2SV enrollment

```
Account Key: Account security → enable → approve push on mobile → passwordless.
             Disables 2SV. Disable path: turn off Account Key → back to password.
2SV:         Account security → 2-step verification → choose method
             (SMS / authenticator app / security key) → verify → Done.
             Authenticator requires ≥2 recovery methods; emergency code issued.
```

**Transitions to probe:** Key↔2SV switching races, 2SV *disable* without fresh
auth, recovery-code reuse, adding attacker recovery email in-session.

### F5. Mail operations (web)

```
List → open (sanitize+render) → compose (editor) → send
Attachments: upload → scan → store → preview/download
Filters: create {criteria, action} → server applies to inbound mail
Signatures: stored per-identity, injected into composed mail
```

**Trust boundaries:** sanitizer between untrusted MIME and victim DOM;
attachment previewers between file bytes and renderer; filter actions must not
cross accounts.

---

## [HYPOTHESES] — ranked, test-ready

Each states the invariant, the concrete probe, and the expected payout band
(per Yahoo's published table). All require two owned test accounts
(`<user>+x@wearehackerone.com` aliases) and manual, low-volume requests with
the `X-Bug-Bounty` header.

### H1. OAuth `redirect_uri` / `.done` destination validation → token theft / ATO
- **Invariant:** authorization codes and session redirects are delivered ONLY
  to the exact registered endpoint.
- **Probe:** register your own app at developer.yahoo.com/apps; test
  `redirect_uri` validation on `request_auth` — path traversal (`/cb/../../evil`),
  encoded slashes, subdomain confusion, scheme tricks, `redirect_uri=oob`
  misuse; separately probe `.done`/`.src` on login.yahoo.com flows the way
  the $7k Flickr bug did. Record exact 302 destinations.
- **Why now:** prefix-only validation paid $7k on a sibling property; `oob`
  still supported is a documented oddity.
- **Expected:** High–Critical.

### H2. Refresh-token / session lifecycle vs password change and "sign out everywhere"
- **Invariant:** a credential rotation or explicit global sign-out must
  invalidate all derived sessions and tokens.
- **Probe:** with your own account, mint OAuth tokens (own app), change the
  password, then test whether access tokens (until expiry) and refresh tokens
  still work; check what "sign out of all devices" actually kills (web
  session? mobile app sessions? OAuth grants listed under "connected apps"?).
  Public evidence says refresh tokens survive password change — verify and
  map the exact boundary.
- **Expected:** Medium–High (High if global sign-out is ineffective).

### H3. Recovery state-machine: skip, reorder, replay
- **Invariant:** each recovery step requires its predecessor; codes are
  single-use, time-bound, and bound to the account under recovery.
- **Probe (own account):** request an SMS/email code, then (a) replay the
  same code twice; (b) use a code issued for account A on account B's flow;
  (c) skip steps by POSTing directly to later recovery endpoints observed in
  browser devtools; (d) test whether the "enter missing digits" gate can be
  bypassed to enumerate which phone is registered. Single attempts, own
  account only.
- **Expected:** High–Critical if a skip/replay yields ATO.

### H4. Privilege transitions without fresh authentication
- **Invariant:** password change, recovery-email/phone change, 2SV disable,
  and Account Key disable require fresh authentication.
- **Probe:** in a normally-authenticated session (own account), attempt each
  transition and record whether a password re-prompt occurs; try the same
  transitions via direct API calls replayed from devtools.
- **Why now:** public how-tos describe password change without a password
  prompt in some paths.
- **Expected:** Medium–High (session theft → account takeover chain).

### H5. Cross-account IDOR on mail/account objects
- **Invariant:** every object ID stays bound to its owning principal.
- **Probe (two owned accounts):** mail filters/rules, contacts, signatures,
  vacation responder, folders, fantasy rosters/teams — swap IDs between
  accounts on read, write, and **delete** endpoints (contact-deletion IDOR
  paid $2.5k; mass comment deletion paid). Record only the access decision.
- **Expected:** Medium–High.

### H6. Mail sanitizer bypass → stored XSS
- **Invariant:** untrusted message content never executes script in a
  victim's session.
- **Probe:** send crafted HTML between your two owned accounts; focus on
  surfaces added since the 2016 payouts — attachment previewers, calendar
  invites, new compose editor, quoted-printable/encoding edge cases,
  `srcdoc`/`data:`/SVG vectors, mutation-XSS (DOMPurify-style differential
  between server filter and client render).
- **Expected:** High (two $10k precedents on this exact surface).

### H7. SSRF in URL-fetching features
- **Invariant:** the server never fetches attacker-influenced internal URLs.
- **Probe:** link unfurling/previews, image proxies, RSS/feed import, "fetch
  from URL" uploads, calendar subscription URLs, webhook/test-URL buttons —
  point each at your own collaborator (webhook.site / Burp Collaborator) and
  observe what the server fetches; only then consider internal targets
  (169.254.169.254, localhost, Redis/gopher per the $15k precedent).
- **Expected:** High–Critical.

### H8. Web vs mobile/API differential authorization
- **Invariant:** authorization must not depend on the client.
- **Probe:** replay webapp API calls (captured from your own session) as the
  mobile-app API shape and vice versa; compare authz decisions on the same
  objects; test OAuth-scope enforcement (`mail-r` token used on write
  endpoints, `fspt-r` token on mail endpoints).
- **Expected:** Medium–High.

### H9. OAuth scope / app confusion
- **Invariant:** a token is valid only for its issued scopes and its issuing
  app's registered redirect surface.
- **Probe:** mint tokens under different scopes on your own apps; cross-use
  them (mail token → fantasy API; fantasy token → mail API); test whether
  `xoauth_yahoo_guid` binding is enforced server-side when a token is
  replayed with a tampered GUID parameter.
- **Expected:** Medium–High.

### H10. `redirect_uri=oob` flow abuse surface
- **Invariant:** out-of-band codes are bound to the authorizing user and the
  requesting client, with the same single-use/expiry rules.
- **Probe:** document the exact oob UX (code format, lifetime, whether it
  shows the app name/scopes clearly — phishing-relevant); test code replay
  and cross-client redemption with your own apps.
- **Expected:** Low–Medium standalone; chain primitive for social engineering
  (Yahoo won't pay for phishing alone — informational).

### H11. Account Key approval binding
- **Invariant:** a push approval authorizes exactly the session that
  requested it, shown with matching context.
- **Probe (own devices):** trigger two concurrent Account Key requests;
  check whether the approval screen distinguishes them (request context,
  location, time); test whether approving request A completes session B.
- **Expected:** Medium–High if cross-request approval works.

### H12. Legacy-remnant sweep (cheap, passive-first)
- **Invariant:** retired endpoints stay retired; DNS doesn't point at
  claimable resources.
- **Probe:** single GETs to `query.yahooapis.com`, `weather.yahooapis.com`,
  `weather-ydn-yql.media.yahoo.com/forecastrss`; passive CNAME review of
  legacy AOL/Compuserve/Netscape hosts for takeover (program explicitly
  values SDTO up to Medium).
- **Expected:** Low–Medium; near-zero cost.

### Explicitly deprioritized
- Open redirect alone (program rates Low/Low — chain primitive only, feeds H1).
- Account/email enumeration (program won't pay).
- Missing cookie flags / clickjacking / self-XSS (program won't pay).
- Deleted-Yahoo-ID re-registration (Yahoo Help confirms IDs are never recycled).
- YQL injection (service retired 2019).

---

## Gaps to close in the authenticated phase
1. Exact `mail.yahoo.com` internal webapp API paths (authenticated JS-bundle mining).
2. `login.yahoo.com` current param surface (`.done`/`.src` still honored?).
3. Whether `api.oauth.yahoo.com` exposes more than `/health`.
4. Redirect-URI validation rules in the current app-registration UI
   (developer.yahoo.com was unreachable from this research environment —
   verify from the test environment).

## Sources
- OAuth flow mechanics: https://developer.nylas.com/docs/provider-guides/yahoo-authentication/?redirect=reorg
- OOB + token-lifecycle details: https://github.com/jhastings843/fantasy-hub/blob/HEAD/docs/superpowers/specs/2026-08-30-yahoo-league-source-design.md
- PKCE/server-side flow: https://github.com/amolrairikar/leagueql-app/blob/HEAD/docs/requirements/backend/BE-022-yahoo-oauth.md
- Recovery/2SV/Account Key steps: https://y.gogonow.de/help.yahoo.com/kb/account/fix-issues-yahoo-account-key-sln25921.html,
  https://y.gogonow.de/help.yahoo.com/kb/account/learn-two-step-verification-sln5013.html,
  https://y.gogonow.de/help.yahoo.com/kb/new-yahoo-mail/reset-yahoo-password-sln27051.html
- Password-change UX: https://www.techradar.com/how-to/how-to-change-your-yahoo-mail-account-password-or-reset-it
- YQL retirement: https://www.valuewalk.com/yahoo-retires-yql-services/
- OpenID 2.0 obsolescence: https://meta.discourse.org/t/removing-yahoo-login-from-core-and-deprecating-openid-2-0/113249/1
- Deleted IDs never recycled: https://y.gogonow.de/help.yahoo.com/kb/SLN3060.html
- Disclosed-report patterns: yahoo-vdp-recon.md (same directory)
