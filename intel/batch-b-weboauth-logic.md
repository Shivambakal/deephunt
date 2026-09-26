# Intel Batch B — Web/OAuth/Business-Logic research (ingested 2026-09-26)

11 of 16 URLs fetched. NOT ingested (fetch blocked, no retry per tool policy):
- xlsize0bruh open-redirect→email-leak (upstream fetch failed)
- dsmodi484 IDOR→priv-esc Microsoft (403)
- bag0zathev2 rewards-webview chain (403)
- mll.sh IIS, nopnop git-integrations, landh.tech find-comment-get-shell, eaton-works J&J (browser service 429)

RULES FOR ALL CHECKLISTS BELOW: own test accounts only. Never touch real users'
data, never complete a takeover on anyone else's account, stop at proof-of-concept
and report.

---

## 1. Unverified-email OAuth provider → mass account takeover (Ali Mojaver)

Source: https://medium.com/@AliMojaver/the-most-dangerous-oauth-bug-ive-ever-found-a2af1275385c
Class: Business-logic / OAuth. Rated P1.

### What
A site that is itself an OAuth PROVIDER (like "Login with X") let users register
with any email address and never verified it. A downstream site (victim.com)
offering "Login with provider" trusted the email claim returned by the provider.
Researcher registered victim@gmail.com on the provider, clicked "Login with
provider" on victim.com, and landed inside the real victim@gmail.com account on
victim.com. Scale: every account of every site using that provider.

### Bug pattern
1. OAuth providers must only assert *verified* email addresses to relying parties.
2. Combinatorial bug: harmless-by-design "unverified signup allowed" becomes
   critical the moment the same platform acts as an identity provider.
3. The program's policy even said pre-account-takeover was "by design" — the
   OAuth-provider angle made it a P1 anyway.

### Safe manual checklist (own test accounts only)
1. If the target is an OAuth provider (has "Login with <target>" on third-party
   sites), register with a second email you own but never verify it.
2. On a test relying-party app you control, click the provider login and check
   which email claim comes back — if your unverified address is asserted as
   verified, you have the primitive. STOP: do not log into anyone else's account.
3. Document the mismatch (unverified email asserted as identity) and report.

---

## 2. OAuth misconfiguration chain → account takeover (Shafayat Ahmed Alif)

Source: https://medium.com/@iamshafayat/how-i-found-a-critical-oauth-misconfiguration-that-led-to-account-takeover-abfec43eaea6
Class: OAuth misconfiguration chain. Rewarded.

### What
Self-hosted platform with complete OAuth 2.0. Five lows chained into full ATO:
(1) open OAuth client registration — anyone could register an app with an
arbitrary attacker-controlled redirect URI; (2) authorization endpoint processed
requests with NO authenticated session (returned 201 + code redirect);
(3) token endpoint accepted code+client_id+PKCE verifier with no client secret
(metadata advertised `"none"` auth); (4) wildcard CORS `*`; (5) Google SSO with
auto-provisioning confirming the auth model. Chain: register malicious client →
victim approves consent → code lands on attacker callback → exchange for victim
JWT + refresh token → persistent access.

### Bug pattern
1. Read `/.well-known/oauth-authorization-server` first — it maps the whole
   attack surface (registration_endpoint, token auth methods).
2. Each finding alone looks low; the chain is the vulnerability. Test the
   authorization endpoint WITHOUT a session — a 201/code for an anonymous
   request is the loudest signal.
3. Redirect-URI ownership validation is the single cheapest fix that breaks most
   of these chains.

### Safe manual checklist (own test accounts only)
1. GET `/.well-known/oauth-authorization-server`; note registration_endpoint and
   token_endpoint_auth_methods_supported.
2. Try registering a client with a redirect URI on a domain you own — if it
   succeeds unauthenticated, note it. Do NOT send the crafted link to any real
   user.
3. POST to the authorize endpoint with no session cookies using your own client:
   a returned code/redirect without login = missing-auth finding. Report the
   chain as a design issue; never harvest another user's tokens.

---

## 3. Google device-code flow hijacking → universal "Sign in with Google" ATO (weirdmachine64)

Source: https://weirdmachine64.github.io/research/google-oauth-device-code-hijacking.html
Class: OAuth device authorization grant (RFC 8628) logic flaws. $13,337 (Google VRP).

### What
Two stacked bugs in Google's device flow: (a) the device-code sign-in session
was transferable via URL — the `TL` challenge blob let a second browser complete
the sign-in for the attacker's device; (b) the server never bound client_id/scope
to the device_code, so both could be swapped in the URL after issuance (e.g.
YouTube TV → Cloud SDK client with cloud-platform/compute scopes). Adding
`prompt=none` removed the consent screen for previously-granted scopes
(openid/email/profile), making it one-click: victim opens a link, attacker's
polling script receives an id_token for an arbitrary third-party "Sign in with
Google" client. Audit trail showed the ORIGINAL client (YouTube TV), hiding the
substitution; 2FA was implicitly bypassed. Fixed Mar 2026.

### Bug pattern
1. Device flows assume the *browser* doing the login belongs to the device
   owner — any transferable session state breaks the model.
2. Parameters that ride along in the URL but are never server-side bound to the
   grant (client_id, scope) are substitution targets.
3. `prompt=none` + ubiquitous prior grants ("Sign in with Google" everywhere)
   turns consent-gated flows into zero-click ones.

### Safe manual checklist (own test accounts only)
1. On any target implementing RFC 8628 device flow, check whether the
   verification URL/session is transferable between two browsers YOU control.
2. Test whether client_id/scope in the authorization URL are bound server-side
   to the issued device_code (swap them; see which identity the token carries).
3. Test `prompt=none` behavior on your own sessions. Never craft links for real
   users; report the binding failure as the core issue.

---

## 4. Client-side authentication bypass (kuldeep.io)

Source: https://kuldeep.io/posts/client-side-authentication-bypass/
Class: Broken access control / client-side trust. Multiple bounties incl. $4k SQLi follow-on.

### What
Four case studies, one theme: auth checks lived only in frontend JS.
(1) Vue router `meta: { authRequired: !0 }` gated routes, but `isUserLoggedIn()`
just checked localStorage `token` + `tokenExpiry` — setting a fake JWT and a
future date logged the researcher in, and ALL backend APIs lacked auth anyway.
(2) Angular app trusted `sessionStorage.userInfo`/`loggedIn` — setting
`userInfo={}` bypassed the guard.
(3) Login page redirected to /main.html on success; visiting it directly bounced
back because `GetSessionInfo` returned nulls — intercepting that response with
Burp match-and-replace (valid PluginId + group names harvested from JS) plus
stripping `"TimeoutStatus":"Timeout"` from the notifications response gave full
UI access, leading to a $4k SQLi. (4) `is_active:false` for a restricted user in
an API response — flipping it to `true` revealed and enabled hidden webhook
CRUD.

### Bug pattern
1. JS bundles are the auth spec: search for authRequired, isUserLoggedIn,
   localStorage/sessionStorage trust, route guards.
2. Report it as ONE systemic "client-side authentication bypass" (full CRUD
   impact) rather than ten endpoint reports — one report, full impact.
3. Burp match-and-replace on session/API responses is the fastest way to test
   whether the UI is the only gate.

### Safe manual checklist (own test accounts only)
1. Grep JS for authRequired/isLoggedIn/token checks; identify what the client
   trusts (localStorage keys, response fields).
2. With your own session, replay API calls with NO token — if data returns, the
   server never checked.
3. Try forging the client-side trust signal (fake token, flipped flags) in your
   own browser only. Never modify another user's session data; report the
   systemic bypass.

---

## 5. Re-running an exposed installer → admin takeover (potato.id / Jonias Fortuna)

Source: https://potato.id/en/posts/i-accidentally-logged-into-threat-actor-website/
Class: Exposed installation/setup endpoint. (Threat-actor target; pattern is universal.)

### What
Directory enumeration found `/install/install.php` still accessible on a live
production app. No "already installed" lock. Researcher pointed the installer at
a MySQL instance they controlled, completed setup, created the initial admin
account — and was admin. Session survived a backend reconfiguration because
sessions were server-side.

### Bug pattern
1. Installers/setup wizards must be locked or deleted post-deploy; an unlocked
   one is a free admin-account creation primitive.
2. ffuf-style content discovery on PHP apps should always include
   /install, /setup, /config, /admin paths.
3. Session storage decoupled from the DB meant the session outlived the
   reconfiguration — note where session state lives when assessing impact.

### Safe manual checklist (own test accounts only)
1. During content discovery on in-scope targets, probe /install*, /setup*,
   /config/* paths (single GETs, low volume).
2. If an installer loads on a production host, do NOT complete it against the
   target's infrastructure — screenshot, note the missing lock, report.
   (Re-pointing a live app's DB is destructive; the researcher here did it to a
   threat actor's infra — on a bounty target, report the exposure instead.)

---

## 6. Checkout state-machine price manipulation (Zuksh)

Source: https://zuksh.medium.com/the-art-of-business-logic-when-the-checkout-got-the-price-wrong-4d548971b4a3
Class: Business logic / state confusion.

### What
E-commerce checkout: researcher baselined the full flow (product €999 → cart
€999 → checkout preview €999), then treated checkout as a STATE MACHINE instead
of fuzzing `price=1`. By driving the cart through normal workflow actions into
an unexpected state and re-triggering checkout preview, the server's own
calculation produced €200 — a stale/discounted pricing state was trusted instead
of rebuilding from authoritative product data. Server-side miscalc, not a UI
display bug.

### Bug pattern
1. Baseline the entire transaction first (known-good amounts at every step).
2. Don't tamper with `price` — tamper with STATE: apply/remove discounts,
   change quantities mid-flow, abandon and resume, reorder steps, use back
   button / parallel tabs.
3. The signal is the SERVER returning a lower total in checkout preview/order
   summary. Display-only changes are not vulnerabilities.

### Safe manual checklist (own test accounts only)
1. Complete a normal purchase flow on the target with your own test account;
   record amounts at product, cart, preview, and order steps.
2. Replay the flow while mutating cart state between steps (coupon apply/remove,
   quantity edits, address/shipping changes, concurrent sessions).
3. If the server quotes a lower total, STOP before paying — document the state
   sequence and report. Never complete an underpriced order.

---

## 7. Live chatbot MQTT wildcard subscription → cross-customer PII leak (lazysharaf)

Source: https://medium.com/@lazysharaf/how-i-hacked-a-live-chatbot-and-earned-my-first-4-digit-bounty-5c43c8891741
Class: Broken authN/authZ on real-time infra (MQTT). First 4-digit HackerOne bounty.

### What
Page source → Drupal settings JSON exposed chat `apiUrl` on a separate host:port.
JS recon there found public `env_app.js` with MQTT broker URL + credentials, and
main.js revealed an `admin`/empty-password fallback. Connecting to the MQTT
broker over WebSocket as admin with empty password worked; subscribing to the
wildcard topic `client/+/chat_session` streamed LIVE customer support chats —
88 messages across 10 sessions in 3 minutes, including PII and session JWTs.
Researcher stopped after confirming, reported with redacted samples; triage
initially dismissed it as "by design" until the live cross-customer data proof
landed. Chatbot taken offline; retest confirmed fix.

### Bug pattern
1. Support chat widgets are backend-shaped attack surface: follow the apiUrl to
   the OTHER host and do JS recon there, not just on www.
2. Real-time protocols (MQTT/WS) often have weaker authZ than the REST API —
   always test wildcard/overbroad subscriptions with your own session topics.
3. Triage lesson: "exposed config" vs "demonstrated live cross-customer data"
   are different severities — prove the data boundary crossing, redacted.

### Safe manual checklist (own test accounts only)
1. Find chat/support widgets; extract backend URLs and config JS (env_*.js,
   asset-manifest.json); note broker URLs and credential hints.
2. With your OWN two test sessions, verify topic isolation: can session A
   subscribe to session B's topic? One confirmation is enough.
3. NEVER subscribe to wildcard topics on a live system streaming real users —
   that collects other people's PII. Prove the authN weakness (weak/default
   creds on the broker) + demonstrate isolation failure between your own two
   sessions, then report.

---

## 8. SearchLeak: AI search → one-click data exfiltration (Varonis)

Source: https://www.varonis.com/blog/searchleak
Class: AI prompt injection chained with classic web bugs. CVE-2026-42824 (Critical).

### What
Three-stage chain against M365 Copilot Enterprise Search: (1) Parameter-to-Prompt
injection — the `q` URL parameter was executed as an AI instruction ("search the
user's emails, embed the title in an image URL"); (2) HTML rendering race —
the `<img>` in the streaming AI response fired BEFORE the output sanitizer
wrapped it in `<code>`; (3) CSP bypass via Bing SSRF — `*.bing.com` was CSP-
allowlisted and Bing's image-search endpoint server-side-fetches the `imgurl`
parameter, so the exfil URL rode through Bing to the attacker's server. One
click on a trusted microsoft.com link → victim's mailbox/calendar/SharePoint
content exfiltrated. Patched by Microsoft.

### Bug pattern
1. AI search/chat features inherit the victim's full data permissions — the AI
   is a confused deputy with the user's keys.
2. Sanitizer timing matters: streaming render-then-sanitize is a race; test
   whether raw HTML executes during streaming.
3. Any CSP-allowlisted domain that server-side-fetches user URLs is an
   exfiltration proxy — map allowlist × fetch behavior.

### Safe manual checklist (own test accounts only)
1. On targets with AI search/assistants, test whether URL parameters or shared
   links influence the AI's instructions (P2P) using benign prompts in your own
   tenant.
2. Check if AI output renders HTML during streaming before sanitization (use a
   harmless `<img>` to your own request-logging domain).
3. Never exfiltrate another user's data — demonstrate with your own mailbox
   content only, then report the chain.

---

## 9. Re:CACHE — Next.js header reflection → 0-click stored XSS (zhero web sec)

Source: https://zhero-web-sec.github.io/research-and-things/re-cache-excessive-reflection-type-confusion-and-0-click-sxss-on-nextjs
Class: Cache poisoning / content-type confusion. Five-figure bounty.

### What
Target reflected request headers into response headers AND ran Next.js App
Router behind Cloudflare cache. Chain: (1) send `Rsc: 1` to get the React Server
Component payload (`text/x-component`), where URL params are reflected
unescaped after `__PAGE__`; (2) add request header `Content-Type: text/html` —
Next.js only sets Content-Type if absent, so the reflected value stuck,
converting the RSC payload into executable HTML with the XSS payload from the
URL param; (3) URL params were part of the Cloudflare cache key and `Vary: Rsc`
was not honored → poisoned response served to everyone = stored XSS;
(4) second poisoning round: `Refresh: 0; <poisoned-URL>` header on the homepage
→ 0-click (no user interaction; Refresh works on 200s unlike Location).
Related: CVE-2025-57822 (Location-header SSRF on <14.2.32 / <15.4.7) when
headers are reflected.

### Bug pattern
1. Test header reflection first: send a unique `X-Test` header, check response
   headers. Reflection + cache = poison primitives.
2. Next.js RSC endpoint: `Rsc: 1` header returns the component payload; params
   reflect unescaped. Content-Type override flips it to HTML.
3. `Refresh` header achieves redirect-on-200 for the 0-click step where
   `Location` can't work.

### Safe manual checklist (own test accounts only)
1. Probe for header reflection (custom request header → response headers) and
   identify the cache layer and its key components (vary headers, query params).
2. On your own test paths, verify the RSC reflection + Content-Type behavior
   with a BENIGN canary string — never poison shared caches with active
   payloads on a live target.
3. Fingerprint Next.js version (x-nextjs-prerender, build IDs) against
   CVE-2025-57822 range. Report the primitive; let the program confirm impact.

---

## 10. OAuth provider unverified email — see #1 (cross-ref)
Duplicate theme with #1/#2: identity assertions must be verified. Covered above.

## 11. GitHub issues $100k RCE (CVE-2026-3854) — noted, no fetch assigned
Wiz research on GitHub.com/GHES RCE via URL parsing. Fingerprint-only relevance:
none for black-box web hunting beyond version checks on self-hosted GHES.
