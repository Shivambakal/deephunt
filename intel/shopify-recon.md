# Shopify Bug Bounty — Passive Recon

**Date:** 2026-09-26
**Mode:** READ-ONLY. No logins, no form submissions, no testing. Single GETs only.
**Research account note:** Testing (later, manual) must use only stores created with the
`YOURHANDLE@wearehackerone.com` HackerOne alias email. Never touch live merchants.

---

## [SCOPE]

Source: https://hackerone.com/shopify and https://bugbounty.shopify.com/criteria?q=scope
(scope page header: "Last Updated: September 26, 2026 at 2:00 PM UTC").
Program stats shown 2026-09-26: $10,073,261 total paid; $1,459,258 paid this year;
$552,125 paid this month; 1,718 reports in last 90 days; 2,429 resolved to date.
Max bounty: $200,000. Scoring via Shopify's Bug Bounty Calculator; score < 3 → $500.

### In scope (Core = full CVSS weight; Non-Core = CIA requirements forced Low)

| Asset | Coverage |
|---|---|
| `*.pci.shopifyinc.com` | In Scope, **Core** |
| `admin.shopify.com` | In Scope, **Core** |
| `arrive-server.shopifycloud.com` | In Scope, **Core** |
| `shopify.plus` | In Scope, **Core** |
| `shop.app` | In Scope, **Core** |
| `accounts.shopify.com` | In Scope, **Core** |
| `partners.shopify.com` | In Scope, **Core** |
| `your-store.myshopify.com` (own test stores) | In Scope, **Core** |
| `*.shopifycs.com` | In Scope, Non-Core |
| `https://github.com/Shopify/*` | In Scope, Non-Core |
| `shopifyinbox.com` | In Scope, Non-Core |
| `linkpop.com` | In Scope, Non-Core |
| `*.shopifycloud.com` | In Scope, Non-Core |
| `*.shopifykloud.com` | In Scope, Non-Core |
| Shopify Mobile Applications | In Scope, Non-Core |
| Shopify Developed Apps | In Scope, Non-Core |
| Shopify Third Party Store | In Scope, Non-Core |
| Shopify Third Party Apps | In Scope, Non-Core (reports closed "Informative", no bounty) |
| `*.shopify.com` | In Scope, Non-Core |
| `*.shopify.io` | In Scope, Non-Core |

### Explicitly out of scope

`community.shopify.dev`, `academy.shopify.com`, `supplier-portal.shopifycloud.com`,
`community.shopify.com`, `livechat.shopify.com`, `cdn.shopify.com`,
`*.email.shopify.com`, `investors.shopify.com`, "Other" (anything not listed).

### Ineligible issue classes (will be closed N/A / Informative)

- **XSS:** storefront self-XSS (staff JS in own store incl. `*.shopifypreview.com`),
  iframe-in-admin/Theme Editor, legacy Rich Text Editor (Blogs/Pages),
  checkout self-XSS, header-control XSS (Referer/Host), devtools/console XSS,
  self-XSS without a ≤2-step attack scenario.
- **CSRF:** cart modification; login/logout (unless chained with another vuln for impact).
- **CDN:** arbitrary file upload to `cdn.shopify.com` / `static.shopify.com`,
  stored XSS in CDN context, "sensitive data disclosure" (CDN is public by design).
- **Hosted-store false positives (`*.myshopify.com`):** staff access to
  `/admin/settings/{shop,account,users,locations}.json`; `payments/config.json`
  (intended public); password-reset tokens not expiring on email change;
  no email verification on signup; no domain verification on custom-domain add;
  "Edit Permissions" staff removing permissions they lack; user/store name
  enumeration; weak "Opening Soon" password; Stocky permission issues;
  Order Printer template sanitization bypasses.
- **Mobile/POS:** rooted/jailbroken-only, biometrics bypass, missing SSL
  pinning/binary protection/encryption, emulator-only, POS PIN brute force
  (intentionally short — a selector, not a control).
- **Third-party apps:** report to the developer first; Shopify pays nothing
  (closed "Informative") after a 1-week no-response wait.
- **DDoS**, **open redirect** (unless chained), **HTML injection into emails**
  (unless chained), **SSRF** (bare HTTP/DNS interaction = Informative/N/A),
  **race conditions** (only if exploitable AND reaching sensitive data; paid-feature
  bypasses on ineligible plans don't count), **social engineering** (incl.
  contacting Support — also a program-ban offense), **GraphQL introspection**
  (intentionally exposed — use it as a recon resource), **password complexity**,
  **CVV validation** rules.
- **Staff-permission reports** only count if: privilege escalation to a Sensitive
  Permission (Manage Settings / Manage Payment Settings / Themes), direct
  financial impact from the request itself, or Buyer PII access beyond
  authorization. Everything else → N/A.
- **IDOR** judged on identifier predictability + data accessed + impact.
- Reports without a functional PoC demonstrating impact → N/A. Duplicate root
  causes → Duplicate. Leaked-credential reports accepted (authenticate then
  immediately deauthenticate, no functionality exercised, don't share).

---

## [SUBDOMAIN INVENTORY]

**Method note:** direct `crt.sh` JSON fetch timed out twice on 2026-09-26 (not
retried per fetch policy). Inventory below is from the vedbex subdomain
aggregator for `shopify.com` (last crawl 2026-05-10 — treat as stale, re-pull
via crt.sh at test time). Source: https://www.vedbex.com/subdomain-finder/shopify.com

### Tier 1 — authenticated / high-value (all In Scope)

- `admin.shopify.com` — unified admin entry (Core)
- `accounts.shopify.com` — central identity service (Core). Homepage is a JS SPA
  ("Welcome to Shopify / Reconnect or refresh the page to log in" —
  fetched 2026-09-26 via https://accounts.shopify.com).
- `partners.shopify.com` — Partner Dashboard (Core). App registration, client
  IDs/secrets, redirect-URI allowlist, payout data via Partner API.
- `shopify.plus` — Plus surface (Core).
- `shop.app` — consumer Shop app backend surface (Core).
- `arrive-server.shopifycloud.com` — Shop app server (Core).

### Tier 2 — interesting, worth mapping

- `apps.shopify.com` — App Store listing surface
- `pay.shopify.com` — payments-adjacent
- `dev.shopify.com` — developer surface (cf. `shopify.dev` docs)
- `api` — **no `api.shopify.com` in the inventory**; Admin/Storefront APIs are
  served per-shop at `{shop}.myshopify.com/admin/api/...` — the absence of a
  central `api.*` host is itself a finding-shaping fact (token audience =
  the shop domain, not a shared API host).
- `portal.shopify.com`, `data.shopify.com`, `events.shopify.com`,
  `services.shopify.com`, `shell.shopify.com`, `chat.shopify.com`,
  `setup.shopify.com`, `store.shopify.com`, `market.shopify.com`,
  `partner.shopify.com` (singular — distinct from `partners`), `support.shopify.com`
- `*.myshopify.com` — every merchant store; only YOUR OWN test stores are in
  scope (`your-store.myshopify.com`, Core). Live merchants are off-limits.

### Out-of-scope but adjacent (do not test)

`community.shopify.com`, `livechat.shopify.com`, `cdn.shopify.com`,
`static.shopify.com`, `investors.shopify.com`, `community.shopify.dev`,
`academy.shopify.com` — all explicitly excluded.

---

## [API SURFACE]

Source: https://shopify.dev/docs/api (fetched 2026-09-26). All APIs versioned
quarterly (`YYYY-MM`), each version supported 1 year; idempotent-request
support; cursor-based pagination; shared error codes.

| API | Endpoint pattern | Auth | Notes |
|---|---|---|---|
| GraphQL Admin API | `https://{shop}.myshopify.com/admin/api/{YYYY-MM}/graphql.json` | `X-Shopify-Access-Token` (offline/online token) + access scopes | Full merchant data: products, orders, customers, inventory. **Introspection intentionally exposed** (per scope page — free recon). |
| Storefront API | per-shop storefront domain | Separate `StorefrontAccessToken` (public, unauthenticated) | Buyer-facing primitives; powers Hydrogen. Public token by design — abuse = business-logic, not auth. |
| Customer Account API | discovered via `GET /.well-known/customer-account-api` on storefront | OIDC access token (buyer) | **GraphQL only.** Returns `graphql_api` + `mcp_api` endpoints with version baked in. |
| Ajax API | `{shop}/cart.js`, `/cart/add.js`, etc. | buyer session cookie | Cart/product endpoints on the storefront; no full reload. |
| Partner API | via Dev Dashboard | partner token | Orgs, payouts, app configs. |
| Shop API / Shop Minis | `shop.app` surface | buyer auth | Connects storefronts to the Shop consumer app. |
| Multipass | `{shop}/account/login/multipass/{token}` | HMAC-signed token (merchant secret) | Plus-only; legacy, closed to new stores. |
| App Bridge session tokens | embedded app iframe | JWT (HMAC-SHA256) | Verified by the *app backend*, not Shopify — trust boundary lives in third-party code. |

**Checkout auth (new customer accounts):** buyer identity set on cart via
`cartBuyerIdentityUpdate` then `checkoutUrl`; or append `sso=silent` to
`checkoutUrl` for OIDC session verification on the Customer Accounts domain.
Source: https://shopify.dev/docs/api/customer (fetched 2026-09-26).

---

## [AUTH FLOWS]

### F1 — App install OAuth (merchant-facing)

Source: https://shopify.dev/docs/api (auth concepts) + corroborating
implementations (https://github.com/kandr-ryan/kandr-bootstrap/blob/HEAD/global/skills/shopify-auth/SKILL.md,
https://github.com/paulpas/agent-skill-router/blob/HEAD/skills/coding/shopify-api/SKILL.md).

1. App redirects merchant to
   `https://{shop}.myshopify.com/admin/oauth/authorize?client_id=...&scope=...&redirect_uri=...&state={nonce}`
2. Merchant approves; Shopify redirects to `redirect_uri` with
   `?code=...&hmac=...&shop=...&state=...`
3. App validates: HMAC-SHA256 over the query string **minus `hmac`**, params
   sorted alphabetically, keyed with the app secret (`timingSafeEqual`
   compare); verifies `state` nonce.
4. App exchanges: `POST https://{shop}.myshopify.com/admin/oauth/access_token`
   with `client_id`, `client_secret`, `code` → `access_token` (long-lived,
   shop-scoped).
5. `redirect_uri` must be pre-registered in the Partner Dashboard
   (partners.shopify.com) — allowlist enforced server-side.

### F2 — Embedded app session tokens (App Bridge)

Short-lived JWTs minted in the admin iframe, verified by the app's own backend
(HMAC-SHA256 with app secret). Claims include shop (`dest`) and app audience.
Modern installs use **token exchange**: session token → offline access token,
no separate install step. Trust boundary: the app's verification code, which
is why Shopify's docs push the official libraries.

### F3 — Customer Account API (buyer OIDC, new customer accounts)

Source: https://shopify.dev/docs/api/customer (fetched 2026-09-26).

1. Discover: `GET /.well-known/openid-configuration` on the storefront domain →
   `authorization_endpoint`, `token_endpoint`, `end_session_endpoint`, `jwks_uri`.
2. Authorize: `response_type=code`, `client_id` (UUID), `scope=openid email
   customer-account-api:full`, `redirect_uri` (must be registered; mobile
   scheme must be `shop.{shop_id}.*`), `state`, `nonce`.
   Public clients add PKCE `code_challenge` (S256) + `code_challenge_method`.
   `prompt=none` enables silent re-auth (returns `login_required` if no session).
3. Token: `POST` to `token_endpoint` with `grant_type=authorization_code`,
   `code`, `redirect_uri`, `client_id` (+ `code_verifier` for public clients;
   Authorization header `Basic(base64(client_id:client_secret))` for
   confidential clients).
4. **App client IDs get NO refresh token**; shop-configured clients (Hydrogen/
   headless storefronts) do. Apps renew via `prompt=none` top-level navigation
   (authorization endpoint can't load in an iframe).
5. Logout: redirect to `end_session_endpoint` with `id_token_hint` +
   `post_logout_redirect_uri`.

### F4 — Multipass (merchant-owned SSO into the storefront)

Source: https://shopify.dev/docs/api/customer-authentication/multipass
(fetched 2026-09-26). Plus-plan only; closed to new stores.

- Token = AES-128-CBC (random IV) encrypted JSON `{email, created_at
  (ISO8601), …}` + HMAC-SHA256 over the ciphertext; keys derived from the
  merchant secret via SHA-256 (first 128 bits = encryption key, last 128 =
  signature key); base64url-encoded `IV ‖ ciphertext ‖ signature`.
- Redeem once via `/account/login/multipass/{token}` (storefront) or
  `/login/multipass/{token}` (customer-account domain), or exchange via the
  **Multipass grant** for a Customer Account API token. **Single-use is
  enforced across surfaces** (a token redeemed on the storefront can't be
  redeemed again via the grant, and vice versa).
- Validity: 15 minutes. `remote_ip` binding removed (IPv6 migration).
- Backchannel logout exists: form-encoded `logout_token` + `token_type=multipass`
  ends all of the customer's sessions on every device and revokes their
  Customer Account API tokens. A `204` means "request accepted", **not**
  "session revoked" (also returned when no customer matches).
- Account-creation-on-redeem: redeeming for an unknown email **creates the
  customer account** — email is the unique identifier.

### F5 — Central identity (`accounts.shopify.com`, In Scope / Core)

The identity hub fronting merchant/partner sign-in. Served as a JS SPA
(2026-09-26 fetch returned only the app shell). Bundle/API inventory requires
an interactive session — flagged as follow-up, not done in this passive pass.

---

## [HYPOTHESIS SEEDS]

Each is framed as a violated invariant, located precisely, with a minimum-safe
test using **only** researcher-owned assets (own dev store created via the
`@wearehackerone.com` alias + own Partner Dashboard app). None touch live
merchants.

### H1 — OAuth `redirect_uri` allowlist normalization gap

- **Invariant:** authorization codes are issued only to byte-exact
  pre-registered redirect URIs (F1).
- **Where:** `https://{own-shop}.myshopify.com/admin/oauth/authorize`,
  allowlist stored in partners.shopify.com app config.
- **Test:** register `https://own-app.example/auth/callback` on the owned app;
  initiate authorize with owned shop using mutated variants — trailing slash,
  trailing `/.`, case-swapped host, `%2e` path segments, subdomain prefix
  (`https://own-app.example.evil.example/`), and query-string appends. Record
  accept vs `invalid redirect_uri` for each. A single accepted near-miss =
  allowlist confusion worth escalating.
- **Why interesting:** redirect-URI confusion is the classic OAuth account-takeover
  primitive; Shopify's allowlist is the only control standing between a leaked
  `client_id` and code theft.

### H2 — Customer Account API PKCE downgrade on public clients

- **Invariant:** public clients must present the `code_verifier` matching the
  S256 `code_challenge` or the token exchange fails (F3).
- **Where:** the `token_endpoint` discovered from the owned store's
  `/.well-known/openid-configuration`, using a public client registered on
  the owned store.
- **Test:** complete a legitimate authorize step on the owned store, then POST
  the token exchange (a) omitting `code_verifier`, (b) with `code_verifier`
  mismatched, (c) with `code_challenge_method=plain` while the challenge was
  S256. Expect `400 invalid_grant` in all three; anything else is a finding.
- **Why interesting:** PKCE is the *only* secret a public client has; a
  verifier-optional endpoint turns any intercepted code into a buyer session.

### H3 — Multipass single-use enforcement across surfaces

- **Invariant (documented):** a Multipass token is redeemable exactly once,
  and the single-use check is shared across the storefront redirect and the
  Customer Account API Multipass grant (F4).
- **Where:** `{own-shop}/account/login/multipass/{token}` vs the Multipass
  grant on the owned store.
- **Test (requires Plus — dev-store/Plus-trial constraint noted):** mint one
  token with the owned store's secret; redeem via the storefront URL; then
  attempt the same token through the Multipass grant, and the reverse order
  with a second token, racing the two redemptions concurrently. Any double
  redemption = session-creation primitive.
- **Why interesting:** the docs *assert* the cross-surface check — assertions
  in docs are exactly where race conditions hide, and each redemption mints a
  full buyer session (possibly creating the account, F4).

### H4 — Authorization-code binding to the issuing shop

- **Invariant:** a `code` issued for shop A is worthless against shop B's
  token endpoint, and the `shop` parameter in the callback can't be swapped
  to launder a code into a different store's session (F1).
- **Where:** `POST https://{shop}.myshopify.com/admin/oauth/access_token`.
- **Test:** with two owned stores (A, B) and one owned app installed on both,
  run the authorize flow on A, capture the callback, then (a) POST A's `code`
  to B's token endpoint, (b) replay A's callback query string but with
  `shop=B` into the owned app's callback handler and observe what the app —
  and Shopify — accept. All cross-shop exchanges must fail.
- **Why interesting:** multi-store merchants are the norm; a code not bound
  to its issuing shop lets an attacker who can trigger installs (e.g. via an
  app-listing page) pivot a victim merchant's authorization into an
  attacker-controlled store context.

### H5 — OIDC discovery endpoint Host reflection

- **Invariant:** `GET /.well-known/openid-configuration` on a storefront
  returns *that shop's* canonical auth endpoints regardless of request
  shaping (F3).
- **Where:** the owned store's storefront domain.
- **Test (owned store only):** request the discovery endpoint with mutated
  `Host` / `X-Forwarded-Host` headers pointing at an attacker-controlled
  domain you own; check whether `authorization_endpoint` / `token_endpoint`
  in the JSON reflect the supplied host. If they do, a downstream client that
  follows discovery blindly can be steered to a credential-harvesting token
  endpoint — the classic discovery-poisoning chain.
- **Safety note:** Host-header tests stay on the owned store; stop if any
  response suggests cross-tenant influence.

### H6 — Offline-token shop scoping after token exchange

- **Invariant:** an access token minted for shop A authorizes zero API calls
  on shop B, including across the token-exchange path (F2).
- **Where:** `https://{shop}.myshopify.com/admin/api/{version}/graphql.json`
  with `X-Shopify-Access-Token`.
- **Test:** install the owned app on two owned stores; take store A's offline
  token (obtained via legitimate OAuth on A) and call B's GraphQL Admin API
  with it; also try A's token against `admin.shopify.com`-routed endpoints
  if reachable. Expect `401` everywhere outside A.
- **Why interesting:** there is no central `api.shopify.com` — the shop
  domain *is* the audience. Any place the audience check is skipped (a legacy
  route, a `.shopify.com` vs `.myshopify.com` mismatch) converts one store's
  install into a skeleton key.

---

## Gaps / follow-ups (not covered in this passive pass)

1. `crt.sh` JSON fetches for `shopify.com` / `myshopify.com` timed out
   (2026-09-26); subdomain inventory above is from a third-party aggregator
   (crawl 2026-05-10). Re-pull at test time.
2. `accounts.shopify.com` JS bundle / API inventory needs an interactive
   session (SPA shell only via passive GET). In Scope / Core — high priority
   for the manual phase.
3. GraphQL introspection is intentionally open on the Admin API — schema dump
   against the owned store is sanctioned recon, not a finding.
4. Multipass hypotheses require a Plus-capable test store; confirm dev-store
   eligibility before H3.
