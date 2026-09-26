# FDJ Group / Kindred — Passive Static Surface Map

**Date:** 2026-09-26 · **Analyst:** subagent (passive only)
**Brands:** unibet.com, 32red.com, bingo.com, mariacasino.com
**Method:** crt.sh enumeration, Wayback CDX + archived JS bundles, single normal-visitor
fetches, one web search. MANUAL-ONLY program: no fuzzing, no parameter tampering,
no repeated requests, no scanners. Methodology: `deep-vuln-methodology.md` §1, §6.

**Environment caveat:** DNS inside this sandbox is intercepted (every test hostname
resolved to 198.18.219.255 / 198.18.220.x), so dangling-CNAME/takeover status could
NOT be verified — candidates below are named on pattern only, marked unverified.
Direct curl to the brand homepages returns `503` from `Server: kindred-loadbalancer`
(datacenter/bot mitigation); JS was recovered from Wayback archives instead.

---

## [CONFIRMED EXPOSURES]

### 1. Shared Kindred micro-frontend bundle store (cross-brand code sharing)
- **What:** All brands serve micro-frontend apps from a versioned bundle store:
  `https://www.<brand>.com/kwp-bundle-store/<app>/<version>/<hash>.min.system.js`
  (SystemJS format).
- **Evidence:** Wayback CDX for `mariacasino.com/kwp-bundle-store*` (2026-09-26 query)
  returned ~2000 collapsed URLs; app names include `analytics-data-collection-fe`
  (130), `deposit-limit-fe` (47), `deposit-limit-modal-fe` (39),
  `channel-verification-fe` (16), `balance-limit-fe` (14), `acquisition-offer-fe`,
  `cashback-fe`, `account-closure-fe`, `cool-off-fe`. The same store path pattern
  serves brand-suffixed bundles (`32red-*.js`, `bingo-*.js`) — one codebase,
  brand-parameterized builds.
- **Security note:** a vulnerability in one shared bundle/app ships to every brand
  simultaneously (blast radius = all four brands + other Kindred properties).
  Version-pinned old bundles remain addressable — worth checking whether outdated
  vulnerable app versions are still served (manual, single fetch).

### 2. Devtools bundle shipped to production
- **What:** `kwp-bundle-store/analytics-data-collection-fe/0.10.120/dev-tools-fee04f40.js`
  and `devtools-kwp-analytics-fabf0158.system-dev.js` archived 2026-05-15 —
  internal developer tooling bundled into the production site.
- **Evidence:** downloaded 370,861-byte bundle from Wayback
  (`web/20260515153742id_/https://www.mariacasino.com/kwp-bundle-store/.../dev-tools-fee04f40.js`);
  imports `@kindred/antd`, `react`, `kaf-client`, `kmf-sitedefinition`, `kwp-csp`.
- **Embedded internal hostnames** (grep of the bundle): `int-qa1.32red.com`,
  `int-si1.32red.com`, `int.32red.com`, `www-qa1.bingo.com`, `www-qa1.mariacasino.com`,
  `www-qa1.unibet.com`, `www-si1.bingo.com`, `www-si1.mariacasino.com`,
  `www-si1.unibet.com`, `ca.unibet.com`. Internal environment naming (qa1/si1/int)
  disclosed to every visitor.

### 3. Payment cashier is a legacy JavaServer Faces application
- **What:** `payment.mariacasino.com/payment-cashier/` serves JSF resources:
  `javax.faces.resource/...faces?ln=web/js...&version=Payment/8.69.0.5462`
  (also seen `Payment/8.72.0.5467`).
- **Evidence:** Wayback CDX for `payment.mariacasino.com*` (2026-09-26): resource
  URLs `Console.js.faces`, `dependencies.js.faces`, `jquery.js.faces`, `load.js.faces`,
  `Progress.js.faces`, `upaymentCommon.js.faces`, CSS `uglobal.css.faces`,
  `upayment.css.faces` (`ln=web/css/uskin1/unibet` — Unibet skin on the Maria host,
  confirming shared cashier), plus `payment-cashier/view/web/errorview.faces` and
  `/pay-bootstrap/authentication_failed` (401, 2020 snapshot).
- **Security note:** JSF `javax.faces.ViewState` is the classic attack surface
  (server-side state, potential deserialization depending on config). This is the
  money-handling app on a legacy stack — highest-value manual target in this
  program. No probing performed; hypothesis only.

### 4. `payment.*` host exists per brand
- **Evidence:** crt.sh — `payment.mariacasino.com` (12-name cert set),
  `payment.32red.com`, `payment.unibet.com.au`. Prior recon (fdj-payment-recon.md):
  `payment.mariacasino.com`, `payment.unibet.com`, `payment.bingo.com`,
  `payment.32red.com` all returned the same minimal HTML stub — shared cashier
  front door. No path/error oracle found unauthenticated.

### 5. Trust-zone anomalies in certificate transparency
- **32red.com (73 names):** `vpn.32red.com`, `webmail.32red.com`, `affiliateadmin.32red.com`,
  `affiliates.32red.com`, `secure-dev.32red.com`, `web-services-dev.32red.com`,
  `financials.32red.com`, `cantorffo.32red.com` (legacy acquisition naming),
  `f1x2.32red.com`, `jpmgames.32red.com`, `xgames.32red.com`,
  `red-exch01.cms.32red.com`, `red-hcas01.cms.32red.com` (internal hostnames in a
  public cert), `autodiscover.cms.32red.com`, `outlook.cms.32red.com`,
  `support-qa1.32red.com`, `support-si1.32red.com`. Source: crt.sh 2026-09-26.
- **unibet.com (263 names):** `admin.{az,ia,il,in,pa,va}.unibet.com` + matching
  `api.*`/`cdn.*`/`notifyapi.*` per-region sets (US state + country segmentation),
  `lyncadmin.unibet.com`, `lyncdiscoverinternal.unibet.com` (Skype-for-Business
  legacy), `internal-api.bel1.unibet.com`, `internal-innovation.unibet.com`,
  `developer.unibet.com`, `dev-bgc-ssl.unibet.com`, `mobile-scratch.unibet.com`,
  `*.d2-dev.aws.unibet.com`, `*.dev.aws.unibet.com`, `*.qa1.us1.unibet.com`,
  `*.pay.aws.unibet.com`, `*.payp.aws.unibet.com` (wildcard certs covering
  dev/qa/pay AWS environments). Source: crt.sh 2026-09-26.
- **bingo.com (126 names):** legacy shared-hosting footprint —
  `cpanel.`, `webdisk.`, `webmail.`, `mail.`, `autodiscover.`, `cpcalendars.`,
  `cpcontacts.` on `beacon--bingo.com`, `costa--bingo.com`, `mirror--bingo.com`,
  `online--bingo.com`; `ww1.*`/`ww11.*` legacy CDN naming (`ww11.docker.*`,
  `ww11.stage.*`, `ww11.billing.*`, `ww11.forum.*`, `ww1.hwcdn.*`, `ww1.nginx.*`,
  `ww1.private.*`); odd SAN `www.gala--bingo.com.en-zulacasino.com`. Source:
  crt.sh 2026-09-26.
- **mariacasino.com (12 names):** minimal — `payment.`, `support.`, `support-qa1.`,
  `support-si1.`, `welcome.`, `evolivecasino.`, wildcards. Tightest surface of the four.

### 6. Edge/security headers observed (single fetch)
- `Server: kindred-loadbalancer`, `Strict-Transport-Security: max-age=63072000;
  includeSubDomains; preload`, `X-Frame-Options: SAMEORIGIN`,
  `X-Content-Type-Options: nosniff`, `Cross-Origin-Opener-Policy:
  same-origin-allow-popups`, CSP `default-src 'unsafe-inline' 'unsafe-eval'
  http: https: data: wss: blob: jockey: unibetpro: *` — permissive CSP
  (wildcard + unsafe-inline/unsafe-eval; `jockey:`/`unibetpro:` = mobile
  WebView bridge schemes, confirming hybrid mobile apps). Source: response
  headers from `https://www.mariacasino.com/` 2026-09-26 (503 body, headers intact).

### 7. Third-party payment providers (aggregator-reported, not first-party confirmed)
- Visa, Mastercard, PayPal, Skrill, Neteller, Trustly, Paysafecard, EcoPayz, bank
  transfer listed for Unibet across affiliate guides (sistercasinosfinder.com,
  getyourtipsout.co.uk, topbrokeri.com — crawled within the last 60 days).
  Trustly "Pay By Bank" is the instant-deposit rail. Treat as lead-grade, not
  confirmed — first-party confirmation needs the authenticated cashier.

---

## [HIGH-CONFIDENCE LEADS] (manual-test hypotheses — not probed)

1. **JSF ViewState on `/payment-cashier/`** — Determine state-saving method
   (server vs client) and JSF version from a single authenticated cashier page
   load; if client-side state saving is used, ViewState tampering/deserialization
   is the textbook high-impact primitive on a money-handling app. *Why: legacy
   JSF + money movement is historically the richest bug class in gambling cashiers.*
2. **`/pay-bootstrap/` flow** — `authentication_failed` (401) implies a bootstrap
   auth handshake before the cashier loads; map its parameters from one manual
   login and look for session/bootstrap confusion. *Why: custom pre-auth
   handshakes are where auth-bypass logic bugs hide.*
3. **Internal hosts referenced in prod JS** (`int.32red.com`, `www-qa1.*`,
   `www-si1.*`, `int-qa1/si1.32red.com`) — single manual request each to check
   whether staging/QA is internet-reachable and what auth it demands.
   *Why: QA environments routinely lag prod on auth hardening.*
4. **`affiliateadmin.32red.com` / `affiliates.32red.com`** — different trust zone
   (affiliate/partner system); test the auth boundary and whether affiliate
   sessions can pivot toward player or admin functions. *Why: partner portals
   are the classic confused-deputy surface.*
5. **`secure-dev.32red.com`, `web-services-dev.32red.com`, `*.d2-dev.aws.unibet.com`**
   — dev services with public certs; check for exposed debug endpoints or default
   creds with one careful manual look. *Why: "dev" in a public cert usually means
   reachable.*
6. **Legacy bingo.com cPanel hosts** (`cpanel.*`, `webdisk.*`, `webmail.*` per
   brand-skin host) — verify liveness; legacy shared hosting with default panels
   is a common foothold, though likely out-of-scope if dead. *Why: cPanel =
   well-known default-credential and outdated-software surface.*
7. **Legacy brand hosts on 32red** (`cantorffo`, `financials`, `f1x2`, `jpmgames`,
   `xgames`) — old acquisition/vertical hosts often run unmaintained stacks;
   fingerprint manually. *Why: forgotten acquisitions are the standard "open door".*
8. **`red-exch01.cms.32red.com` / `red-hcas01.cms.32red.com`** — internal naming
   leaked in public cert; check if they resolve/serve anything externally.
   *Why: internal hostnames in CT logs frequently map to real internal services.*
9. **Shared bundle store version pinning** — old `kwp-bundle-store` app versions
   remain addressable by URL; diff an old vs current security-sensitive app
   (e.g. `deposit-limit-fe`) for fixed-then-regressed logic, and check whether the
   site can be made to load a pinned old version. *Why: versioned immutable
   bundles + client-side version selection = downgrade risk.*
10. **Mobile bridge schemes** (`jockey:`, `unibetpro:` in CSP) — the hybrid apps'
    JS bridge is reachable from the same WebViews; test bridge-exposed native
    methods from a manual session. *Why: CSP explicitly blesses these schemes,
    and bridge APIs often lack the web's auth checks.*

---

## [REJECTED]

- **Subdomain takeover via DNS** — could not be assessed: sandbox DNS is
  intercepted (all probes returned 198.18.219.255/198.18.220.x), so no
  dangling-CNAME determination was possible. No takeover claimed.
- **Direct homepage/JS fetch** — datacenter curl gets `503` from
  `kindred-loadbalancer`; not a vulnerability, just edge bot mitigation.
  (Real-browser sessions, e.g. the earlier Maria Casino registration flow, load fine.)
- **urlscan.io result API** — now requires login; used only the public search API
  (53 mariacasino.com scans listed, most recent 2026-09-08) and did not pull
  authenticated scan content.
- **Payment callback replay** — still account-gated (see fdj-payment-recon.md);
  the opaque callback/return URL is only revealed inside an authenticated deposit
  flow. No public callback documentation found in passive sources.
- **`ww1.admins.dream--bingo.com`** — name suggests an admin panel, but it sits
  inside bingo.com's legacy `ww1.*` CDN-naming cluster (alongside `ww1.nginx.*`,
  `ww1.hwcdn.*`); most likely a legacy origin label, not a real admin panel.
  Kept as a look-not-touch note, not a lead.
