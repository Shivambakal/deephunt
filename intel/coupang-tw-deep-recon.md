# Coupang Taiwan — Passive Deep Recon
**Date:** 2026-09-26 (all findings dated; policies change without notice)
**Program:** Coupang Taiwan — https://hackerone.com/coupang_tw (verified via HackerOne directory search)
**Type:** Public, HackerOne-managed, offers bounties ($50 minimum), retesting included, collaboration enabled
**Disclosed reports:** 0 (per BugBountyHunter, crawled 2026-09-26) — ambiguous signal: underserved OR fortress. Disclosure policy is strict non-disclosure without consent.

> PASSIVE ONLY. Everything below is from public pages/docs/repos/press. No scanning, probing, fuzzing, or auth attempts were performed.

---

## 1. Live policy (fetched 2026-09-26 from hackerone.com/coupang_tw)

### Bounty table (CVSS-based, "general guidelines; reward decisions at Coupang Corp's discretion")
| Severity | Amount (USD) |
|---|---|
| Critical | $4,000 – $6,000 |
| High | $1,500 – $3,000 |
| Medium | $400 – $600 |
| Low | $50 – $200 |
| Accepted Risk / Informational | $0 |

Program stats on page: ~16h avg first response, ~3d5h avg triage, ~1w5d avg bounty, ~2w1d submission→bounty. Fast Payment badge (payment within 1 month). Gold Standard Safe Harbor. Response efficiency >90%.

### Scope assets — ⚠️ NOT fully confirmed from page render
The policy page render did **not** include the "In Scope" asset table (HackerOne renders structured scope in a tab that did not come through the text fetch). **Do not test any host until the live scope tab is checked in a logged-in browser session.** The policy explicitly says: *"Ask the program team before submitting vulnerabilities on unscoped subdomains"* and *"Vulnerabilities affecting assets not listed as part of Coupang's scope are not eligible for a bounty."*

Candidate assets seen in third-party/public sources (NOT official confirmation — verify against live scope tab):
- `marketplace.tw.coupangcorp.com` — Salesforce Experience Cloud site for the TW marketplace/seller side; referenced as the tested target in two independent public hunter case studies (see §5)
- `tw.coupang.com` / `www.tw.coupang.com` — Taiwan storefront (Play Store listing for the TW app points at https://www.tw.coupang.com/)
- `payment.tw.coupang.com` — appears as a scan target in a public GitHub bug-bounty tooling repo (third-party, not an official scope list)
- `api-gateway.tw.coupang.com` — Taiwan API gateway (HMAC CEA auth, `X-MARKET: TW` header); documented in a public third-party Coupang Partners API spec (seller/affiliate API)
- `partners.tw.coupang.com` — Taiwan Partners (affiliate) portal, with public API docs tab (`#help/open-api`)
- `pages.tw.coupang.com` — used for campaign/landing pages (e.g., breach-compensation coupon lookup `pages.tw.coupang.com/f/3081`)
- `tw.coupangcorp.com` — Coupang Taiwan corporate news/press site
- Mobile apps: `com.coupang.mobile` (global app, switchable TW/KR region) and `com.coupang.mobile.lightspeed` ("Coupang - Next Day Delivery", the Taiwan app)

### Explicit exclusions (from live policy, verbatim categories)
- Core Ineligible Findings: infrastructure attacks/vulns, DoS via application vulns
- Attacks requiring jailbroken/rooted device; MiTM or physical access to a user's device
- Social engineering incl. phishing via redirection (phishing/vishing/smishing **prohibited** as testing activity)
- Other ineligible: CSRF with minor impact (e.g., logout), password-policy improvements, missing security headers, internal IP/domain leakage, error messages/version info, unlikely user interaction (e.g., self-XSS), publicly known vulns, already-known/informational issues

### Special rules (high-impact for hunting strategy)
1. **TW/KR backend overlap dedupe:** *"Coupang's Taiwan and Korea assets might have overlapping backend code… vulnerabilities that require the same fix across Korea, Taiwan, iOS, or Android will be treated as a single vulnerability report, and only the first valid submission (from either host) will receive the bounty."* — duplicates across regions are real; check the Korean program/duplicates first.
2. **IDOR with unpredictable IDs:** program deviates from platform standards — *"Reports without showing how those 'unpredictable IDs' were obtained easily won't be considered valid."* IDOR reports must demonstrate the ID is enumerable/leaked.
3. **Leaked-credential reports accepted** (Coupang API/infra auth material) but must include verifiable evidence (data sources, account samples, account type); duplicates/known leaks ineligible.
4. **LLM vulns:** no intrusive actions against LLM systems (no data poisoning, no unauthorized deletion).
5. **Test plan requirements:** use `X-HackerOne-Researcher: [H1 username]` header on all testing traffic; use hacker email alias `<h1username@wearehackerone.com>`; **a Taiwanese phone number may be required** for account verification — program cannot provide test accounts; researchers obtain their own. Only interact with accounts you own.
6. Disclosure: public program, but **no discussion of the program or vulns (even resolved) outside the program without express consent**; follow HackerOne disclosure guidelines.
7. One vuln per report unless chaining for impact; first reproducible report wins duplicates; multiple vulns from one root cause = one bounty; zero-day with patch <1 month accepted case-by-case; good-faith effort to avoid privacy violations/data destruction/service degradation.

---

## 2. Architecture / tech stack (public sources)

- **Heavy AWS shop** (confirmed across job posts): Spring Boot, JPA, microservices (MSA), Docker, Kafka, Redis, MySQL, Cassandra, Elastic stack; blue-green deploys, ~100–200 microservices/day, 2,000+ new instances/day (Coupang Engineering blog, Medium). Video side uses Golang/Node.js/Java, S3/EC2/ECS/EKS/Lambda/RDS/DynamoDB/CloudFront/Route53, event-driven serverless.
- **ML platform:** hybrid on-prem GPU + AWS multi-region; distributed cache for ML training (Slideshare deck, Coupang staff backend engineer, Apr 2025).
- **Edge/WAF:** a third-party hunter commit references an **Akamai** bypass case against Coupang TW ("Coupang TW … Akamai bypass-exhaustion") — Akamai in front of TW assets is plausible but **unverified** from official sources.
- **Auth model (TW storefront):** email + password registration; real-name required (needed for delivery); Taiwanese mobile number + SMS OTP verification during signup (policy confirms phone requirement). Alternative-auth history is sensitive here: the 2025 breach was an ex-employee abusing a **stolen signing key for an alternative/backup authentication system** he himself built — suggests Coupang runs a custom secondary auth path alongside standard login.
- **APIs:** region-specific API gateways — `api-gateway.tw.coupang.com` (TW) vs `api-gateway.coupang.com` (KR). Seller/affiliate auth is HMAC-SHA256 "CEA" scheme: `Authorization: CEA algorithm=HmacSHA256, access-key=..., signed-date=..., signature=...`, signature over `datetime + METHOD + path [+ query]`, ~5-min expiry; `X-MARKET: TW` header for seller OPEN API. Base path observed: `/v2/providers/affiliate_open_api/apis/openapi/v1/`.
- **Mobile:** two Android apps — `com.coupang.mobile` (one global app, in-app **region switch TW↔KR**, languages KO/ZH/EN) and `com.coupang.mobile.lightspeed` (Taiwan "Next Day Delivery" app, 1M+ downloads, 4.3★, links to tw.coupang.com + LINE @coupangtw + FB CoupangTaiwan). Region-switching in one app = cross-region logic worth probing (price/catalog/session bleed TW↔KR).
- **Marketplace model:** "Rocket Delivery/火箭速配" (Coupang-owned inventory + own logistics, next-day) vs "Marketplace/酷澎商城" (third-party sellers, 50M+ SKUs claimed, seller-fulfilled). Seller onboarding requires business license, ID, bank book; KYC + passport for payouts. WOW membership NT$59/month: free shipping, 30-day returns, member-only coupons.
- **Logistics:** own fulfillment + delivery fleet ("Rocket" network), scheduled delivery slots (up to 7 days out), convenience-store pickup (超商取貨), cash on delivery (貨到付款) exists in TW.

## 3. Third parties & partners

- **Payments (Taiwan) — partially verified:** public promos confirm **credit/debit card checkout** (HSBC, Cathay United bank card promos), **cash on delivery**, **convenience-store pickup payment**; **Edenred (宜睿智慧) e-voucher integration launched 2026-09** — corporate benefit recipients get a serial/redemption code (NT$100/500/1000/2000/3000) entered at Coupang checkout. **Coupang coins (酷澎幣)** as loyalty currency (1% back promos). LINE Pay / JKoPay as Coupang TW checkout options: **NOT confirmed** — Taiwan's popular wallets are LINE Pay/JKoPay/Apple Pay per PPRO, but no source confirms them on Coupang TW checkout. **Do not assert; verify at checkout.**
- **Identity:** no third-party IdP confirmed for TW (email/password + SMS OTP; Korea uses carrier-based identity verification). Salesforce Experience Cloud on the marketplace portal side (§5) with OAuth2/SAML endpoints.
- **CDN/WAF:** likely Akamai per third-party hunter note (unverified).
- **Logistics partners:** primarily Coupang's own Rocket network; convenience-store chains for pickup (unverified which chains).
- **Affiliate/seller ecosystem:** Coupang Partners (affiliate) TW portal + OPEN API; CedCommerce official integration partner; seller tools via `developers.coupang.com` (API Integration Agreement covers PII handling for order-data integrations).

## 4. Code & repos

- **Official:** `github.com/coupang` — legacy/stale (spring-data-requery, hibernate-redis, coupang-metrics, Kafka mirrors; last meaningful updates ~2018–2019). `github.com/Coupang-USA` — no public repos. Nothing Taiwan-specific or current in the open.
- **Third-party (recon-useful, NOT official):**
  - `lunkerchen/skills` — Coupang Partners **Taiwan** API research: gateway discovery, HMAC details, `X-MARKET: TW`, full TW affiliate endpoint list (`/products/search`, `/products/bestcategories/{id}`, `/products/goldbox`, `/products/coupangPL`, `/reports/*` incl. commission/clicks/orders/cancels/ads), rate limits (50/min products, 500/hr reports).
  - `retention-corp/coupang_partners`, `noah3521/coupang-sourcing`, `uju777/coupang-mcp` — community API clients (HMAC logic reusable for understanding auth; **do not use anyone's keys**).
  - `arkadiyt/bounty-targets-data` — hourly HackerOne/Bugcrowd scope dumps (17.2MB `hackerone_data.json` — too large to read via page fetch; use locally if needed; **not fetched here**).
  - `zaaaxx11/hunteros` — Coupang TW Salesforce case study (see §5).
  - `jbwolfflow/huntress` — commits referencing a Coupang TW engagement: Salesforce Aura RPC guest-user enumeration validator and an Akamai bypass case (methodology notes only).
  - `houseofmartynix-debug/god-recon-bot` — recon bot sourcing scope from bounty-targets-data for `coupang_tw`.

## 5. Videos, writeups, engineering content

- **Engineering blog:** `medium.com/coupang-engineering` — backend-at-scale series (microservices, deployment system, ML platform), distributed-cache-for-ML-training talk (Slideshare, Apr 2025, Hyun Jung Baek). Conference presence is real; no TW-specific security talks found.
- **Disclosed HackerOne reports for coupang_tw:** **zero** (BugBountyHunter, 2026-09-26). Strict no-disclosure rule means even resolved bugs stay private.
- **Third-party writeups (unaffiliated hunters, public):**
  - **HunterOS case study (2026-07-25): `marketplace.tw.coupangcorp.com` is a Salesforce Experience Cloud/Community site.** Findings claimed (their testing, not independently verified): unauthenticated `GET /tw/services/data/` enumerates **37 REST API versions (v31.0–v67.0)**; OAuth2/SAML endpoints (`/tw/services/oauth2/token`, `/authorize`, `/tw/_nc_external/identity/sso/ui/*`); internal port **8443 disclosed** in `/tw/services/auth/*` redirects; Aura framework path leakage via Link headers (`/tw/s/sfsites/auraFW/...`); cookies (`CookieConsentPolicy`, `renderCtx`) missing HttpOnly/SameSite; missing CSP/Referrer-Policy/Permissions-Policy; CSP report-only with `unsafe-inline`/`unsafe-eval`. Recommended retest priorities: auth bypass on REST API (SOQL/SOSL vectors are 401-gated), JWT/SAML2 bearer <redacted> testing, LWC/Aura XSS, OAuth parameter pollution, host-header injection.
  - **Huntress repo commits** reference Aura RPC guest-user enumeration methodology validated against the same host and an Akamai bypass-exhaustion case.
- **Breach context (2025–2026, press):** ex-employee (Chinese national) stole an internal signing key for a backup auth system; from Jun–Nov 2025 hit delivery-address page ~148M times and account-edit page ~35M times cycling member IDs; 33.7M KR accounts + ~200K TW accounts exposed (names, emails, phones, delivery addresses, some order history; no payment creds). Korea PIPC fined record amounts; **Taiwan MODA fined Coupang NT$1.5M (~US$47k) on 2026-08-17** (reported 2026-09-21). Coupang paid NT$1,000 coupons to affected TW users (redeemable via `pages.tw.coupang.com/f/3081`). **Takeaway for hunting:** the TW stack demonstrably exposes member-ID-enumerable endpoints (delivery address / account edit) — ID-enumeration + broken object-level authorization is the historically proven bug class here (but see policy: IDOR with unpredictable IDs needs demonstrated ID acquisition).

## 6. Asset inventory (passive only)

⚠️ **crt.sh fetch for `%25.coupang.tw` failed (upstream fetch timeout, 2026-09-26) — subdomain enumeration via CT logs NOT completed.** No active scanning performed. Inventory below is from public sources only; **verify every host against the live HackerOne scope tab before testing.**

| Host / asset | Source | Status |
|---|---|---|
| `tw.coupang.com`, `www.tw.coupang.com` | Play Store listing (TW app), affiliate docs | Unverified vs scope |
| `payment.tw.coupang.com` | Third-party tooling repo scan-target list | Unverified vs scope |
| `api-gateway.tw.coupang.com` | Third-party Partners API research (HMAC OK) | Unverified vs scope |
| `partners.tw.coupang.com` | Public affiliate portal docs | Unverified vs scope |
| `pages.tw.coupang.com` | Coupang TW breach notice (coupon lookup) | Unverified vs scope |
| `marketplace.tw.coupangcorp.com` | Two public hunter case studies | Unverified vs scope |
| `tw.coupangcorp.com` | Coupang TW corporate press site | Unverified vs scope |
| `globalsellers.coupang.com` | Seller signup guide | Likely global, not TW scope |
| `developers.coupang.com` | API Integration Agreement PDF | Docs; likely out of scope |
| Android `com.coupang.mobile`, `com.coupang.mobile.lightspeed` | Google Play | Unverified vs scope |

## 7. Hypothesis seeds (marketplace-logic first, policy-checked)

Policy gates to respect: IDOR-with-unpredictable-ID needs demonstrated ID acquisition (§1 rule 2); TW/KR overlap = one bounty, check KR dups first; `X-HackerOne-Researcher` header required; Taiwanese phone needed for full accounts; no social engineering, no DoS, no infra attacks.

**H1 — Coupon/redemption-code enumeration (Edenred voucher codes at checkout).**
*Hypothesis:* The Edenred e-voucher flow (serial codes NT$100–3,000 entered at checkout, launched 2026-09) has weak rate limiting or predictable code structure, allowing redemption-code guessing or reuse across accounts. *Why this target:* brand-new integration (Sep 2026) = fresh code; voucher flows are classic logic-bug territory. *Expected:* redemption endpoint accepts codes without per-account binding or with high attempt limits. *Class:* business logic / insufficient anti-automation.

**H2 — First-purchase 70%-off coupon abuse via account/SMS verification weakness.**
*Hypothesis:* The 首購7折 (first-purchase 70% off) coupon, scoped to Rocket速配 Taiwan-shipped items, can be re-armed — e.g., SMS OTP verification for TW numbers lacks attempt throttling, or "new device" detection is client-side, allowing repeated new-account coupon harvesting. *Why:* policy itself flags TW phone verification as a friction point researchers must solve — friction points hide logic bugs. *Expected:* OTP endpoint without rate limit, or coupon eligibility keyed on mutable account attribute. *Class:* auth/verification bypass → business logic.

**H3 — Seller↔buyer boundary IDOR on order/settlement APIs.**
*Hypothesis:* Marketplace seller APIs (via `api-gateway.tw.coupang.com`, `X-MARKET: TW`) authorize by seller ID passed client-side; swapping `vendorId`/order IDs yields other sellers' orders, settlements, or buyer PII. *Why:* two-sided marketplaces are the #1 IDOR zone; breach history shows member-ID-enumerable endpoints. *Expected:* order/settlement endpoints return cross-seller data with a substituted ID; must demonstrate ID acquisition per policy rule 2 (IDs may leak in seller dashboard URLs or affiliate `productUrl`s). *Class:* IDOR / BOLA.

**H4 — Salesforce Experience Cloud auth bypass → SOQL data access (marketplace.tw.coupangcorp.com).**
*Hypothesis:* Per the public case study, 37 REST API versions are exposed unauthenticated and all query vectors are 401-gated — but older versions (v31.0–v49.0) or the JWT/SAML2 bearer <redacted> at `/tw/services/oauth2/token` may have weaker validation (alg=none, key confusion, assertion replay). *Why:* third-party recon already mapped it; Salesforce communities are a proven bug class. *Expected:* token endpoint accepts forged/unsigned assertion → authenticated REST/SOQL access. *Class:* auth bypass → SOQL injection/data exfil. **Verify host is in scope first** (policy: ask before unscoped subdomains).

**H5 — Region-confusion in the global app (TW↔KR switch).**
*Hypothesis:* The single app (`com.coupang.mobile`) with in-app TW/KR region switching sends region as a client-controlled parameter; a TW session can invoke KR-only endpoints (or vice versa) — price, coupon, or PII bleed across regions; or TW/KR session tokens are interchangeable on the shared backend (which the policy admits overlaps). *Why:* policy explicitly warns TW/KR backends share code — shared code + client-side region flag = confusion bugs. *Expected:* KR-priced checkout or KR coupon applied on TW account, or TW token accepted by KR API. *Class:* business logic / access control.

**H6 — Rocket Delivery tracking/order-management IDOR.**
*Hypothesis:* Order tracking, address-change-before-dispatch, delivery-photo, and return-pickup endpoints use sequential or guessable order IDs; a buyer can view/modify another buyer's shipment (address reroute = high impact). *Why:* logistics endpoints are historically IDOR-rich; Coupang's own fleet + scheduled slots multiply the state machine. *Expected:* tracking API returns other users' orders with incremented IDs; address-change endpoint lacks ownership check. *Class:* IDOR. (Policy rule 2: demonstrate how IDs are obtained — e.g., leaked in referral URLs or sequential.)

**H7 — Review manipulation APIs.**
*Hypothesis:* Product review endpoints allow posting/editing reviews for orders never purchased, or allow sellers to delete/alter negative reviews via seller-side API; "verified purchase" flag is client-settable. *Why:* marketplace trust systems are logic-bug dense and directly monetizable for sellers. *Expected:* review POST without order linkage, or seller API exposes review-moderation actions beyond own listings. *Class:* business logic.

**H8 — Affiliate reports cross-account data (api-gateway.tw.coupang.com `/reports/*`).**
*Hypothesis:* The affiliate reports endpoints (commission/clicks/orders/cancels, 500/hr limit) scope by affiliate ID from the request rather than the HMAC key identity, leaking other affiliates' earnings/order data. *Why:* documented public API with clear data-sensitivity; HMAC scheme documented by third parties (5-min signature expiry suggests replay protections exist — test scope confusion, not replay). *Expected:* substituting affiliate identifier returns another account's report rows. *Class:* IDOR.

**H9 — WOW membership / 酷澎幣 (Coupang coins) ledger logic.**
*Hypothesis:* Coin accrual (e.g., 1% back promos, 618/中元節 flash coupons) and refund-to-coin flows have race conditions or double-credit paths — cancel/refund after coin redemption re-credits coins without debiting, or coin balance is updated by a client-callable endpoint. *Why:* loyalty-currency double-spend is a classic marketplace bug; frequent promo churn (618, 中元節, bank promos) = frequent new code. *Expected:* refund of a coin-discounted order restores coins AND cash; or concurrent redemption requests both succeed. *Class:* business logic / race condition. (No DoS-style load testing — single paired requests only, per policy.)

**H10 — Akamai edge request smuggling / cache poisoning on storefront.**
*Hypothesis:* If Akamai fronts `tw.coupang.com` (per third-party note), discrepancies between edge and origin parsing (header folding, duplicate Content-Length, cache-key including unvalidated headers) enable cache poisoning of product/promotion pages or session confusion. *Why:* third-party hunter already burned time on Akamai bypass here, suggesting the edge is in play and non-trivial. *Expected:* poisoned cache serves attacker content to other TW users, or `X-Forwarded-Host`-style cache-key injection. *Class:* cache poisoning / HTTP desync. (Passive header observation only to start; any active desync testing must stay within policy's good-faith/degradation limits.)

---

## Gaps & caveats
- **Scope table not retrieved** (policy page render omitted it; crt.sh timed out). **Nothing in §6/§7 may be tested until hosts are confirmed in the live HackerOne scope tab.**
- Taiwan checkout payment methods (LINE Pay/JKoPay on Coupang TW): **unconfirmed** — do not assert.
- Akamai as CDN/WAF: third-party claim only, unverified.
- All §5 third-party writeups are unaffiliated claims; treat as leads, not facts.
- TW/KR overlap dedupe (§1 rule 1) means pre-searching Korean-asset duplicates is mandatory before reporting.
