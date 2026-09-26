# Wolt Deep Recon — Passive Intelligence (2026-09-26)

**Target:** Wolt bug bounty program — https://hackerone.com/wolt
**Date:** 2026-09-26 | **Method:** PASSIVE ONLY — public pages, docs, cert logs, search. No scanning, no probing, no auth attempts, no traffic beyond loading public pages.
**Sibling file:** `~/workspace/hacker-agent/intel/deep-hunt-plan.md` holds hypotheses W-1–W-9. This report builds on them; it does not duplicate them.
**Operator:** researcher handle `shiva92`; test alias `shiva92@wearehackerone.com`.

---

## 1. Live policy (fetched 2026-09-26 from https://hackerone.com/wolt)

### Mandatory header (exact)
- Add to requests: `X-HackerOne-Research: [H1 username]` → for this operator: **`X-HackerOne-Research: shiva92`**
- "Reports resulting in testing without headers can result in the forfeiture of the eligible bounty."

### Identity
- Self-register with hacker email alias: `h1username@wearehackerone.com` (→ `shiva92@wearehackerone.com`).
- Customer account: self-register via wolt.com, iOS app, or Android app.
- **Courier account: NOT available. Merchant/business account: NOT available.** Do not improvise access.

### Provided test entities (use ONLY these)
- Consumer test account: `user_id = 670fa3e9ead6e49d65cc3614` — "If you need to test any sort of access to user data, please do it only against this specific consumer test account."
- Venue test account: `venue_id = 670e7897e3c56dcc5b5a0989` — venue-data tests only against this.
- Test venue: https://wolt.com/en/fin/helsinki/venue/test-670e7897e3c56dcc5b5a0989-sh0p — **real purchase is not available** there.

### Hard rules
- ⛔ Don't use or interact with accounts or data you don't own — explicitly including restaurants/venues and merchant data.
- ⛔ Use only your own accounts and data.
- ⛔ No interaction with Customer Support staff (incl. social engineering) — forbidden and out of scope.
- No mass creation of entities (accounts, profiles, applications). **Kills any multi-account seed — single account + test entities only.**
- Reports: one vuln per report; brief, 300–400 words.
- Disclosure: follow HackerOne disclosure guidelines.

### Explicit out-of-scope (abridged — check the live page before testing)
Testing payment processors · spam/social engineering/physical intrusion · network DoS/DDoS · **Web Cache Poisoned DoS** · brute force · attacks needing victim device access · unproven outdated-software claims · leaked-credential-list reports · **`GATEKEEPER_API_KEY` exposure (explicitly "not a secret")**.
Web: API-key disclosure w/o business impact · signup with unverified mobile numbers (**EXCEPTION: "if you took over an existing number, then that's a finding!"**) · verbose messages/listings w/o sensitive data · CORS w/o impact · missing cookie flags · missing security headers · CSRF w/o impact · autocomplete · **rate-limit bypass or missing rate limits** · password best-practice violations · clickjacking w/o impact · **CSV injection** · session invalidation · content injection w/o HTML modification · **username/email enumeration** · email bombing · request smuggling w/o impact · homograph · banner grabbing · subdomain takeover w/o proof · arbitrary file upload w/o proof · host-header injection w/o business impact.
Mobile: clipboard link leaks · malicious-app-required attacks · sensitive data in TLS-protected URLs/bodies · lack of obfuscation · path disclosure · jailbreak/root detection · malformed-URL-scheme crashes · anti-debug/SSL-pinning · snapshot/pasteboard · jailbroken-only runtime exploits.

### Scope / bounty table — GAP
The fetched policy render (2026-09-26) showed the rules above but **no explicit in-scope asset table and no bounty-tier table** in the page text. A follow-up fetch of the program overview tab failed (upstream timeout, not retried). The sibling plan records **min bounty $100, 0 resolved on HackerOne**. **Re-verify the live Scope tab at test time before touching any host** — policies change without notice.

---

## 2. Architecture & tech (public sources)

- **Backend:** Scala organization. Legacy **Play Framework monolith** (flagged internally as technical debt — complex DB-level logic); active migration to **microservices (ZIO/Cats + Http4s), event-driven architecture**, "hundreds of microservices" per the observability blog. Source: careers.wolt.com engineering blog ("Technical Decisions in Our Scala Organization", "How Wolt Reduced Metric Cardinality" — they built TRIM, a telemetry ingestion policy engine).
- **Web frontend:** wolt.com serves a modern JS app. A third-party YouTube video (The Cyber Eve, crawled ~2026-09-23) claims a **CVE-2025-29927 (Next.js middleware auth bypass) finding on wolt.com paid $3,500** — **unverified third-party claim**, but it is consistent with wolt.com running **Next.js**. If true, the patch state of the Next.js middleware layer is worth one passive version check at test time (do not treat the video as proof).
- **Public consumer API surface (historical, from a public Medium article on the Wolt API):** `restaurant-api.wolt.com` with REST paths like `/v1/pages/delivery?lat=..&lon=..`, `/v1/google/places/autocomplete/json`, `/v1/google/geocode/json` — **no cert-log entries found for `restaurant-api.wolt.com` in 2026-09-26 crt.sh pull** (may have moved behind the wildcard or been retired — verify passively at test time).
- **Wolt Drive (logistics-as-a-service) API:** documented at **developer.wolt.com/docs/wolt-drive**. Endpoints: `/shipment-promises`, `/delivery-fee`, `/available-venues`, `/deliveries`, `/delivery-order`; **webhook service** for order events (`order.received`, `order.delivered`, `dropoff.completed_at`, courier id/vehicle_type, `purchase_rejected_reason`); per-order tracking URLs (SMS'd to customers). Auth is merchant API-key based (creds issued by the local Wolt Drive team — **not available to researchers; do not attempt to obtain**). Merchant dashboard: `merchant.wolt.com` (referenced in community docs; cert-log shows `links.merchant.wolt.com`, `merchant.links.wolt.com`, `merchant-access-control.wolt.com`).
- **webhooks-service.wolt.com** exists in cert logs (Drive webhook infra).
- **Models:** platform model (courier delivery), **self-delivery model** (merchant delivers, no Wolt couriers) in several markets, **Wolt Drive** (fleet for off-platform merchants via API/Shopify/website), **Wolt for Work** (B2B — `links.woltforwork.wolt.com`), **Wolt+** membership (€0 delivery fees + perks), **Double Order** (two venues, one order, one delivery fee), scheduled orders, gift orders.
- **Infra signals:** Amazon-issued certs (ACM → AWS), Google Trust Services certs, Cloudflare-hosted press assets; **DoorDash-owned since 2022** (see §6).

## 3. Third parties & partners (from policy, docs, press)

- **Identity:** `identity.wolt.com` in cert logs (purpose unconfirmed — candidate IdP/SSO surface; verify scope before touching).
- **Maps/places:** Google Maps Platform — proxied through Wolt's own API (`/v1/google/places/autocomplete`, `/v1/google/geocode`) per the public API writeup.
- **Payments:** consumer checkout offers **credit card and Apple Pay** (per app listings). The policy explicitly puts **payment processors out of scope** — the processor's identity is not confirmed in public sources found today (Adyen rumors unverified — do not assert). Treat all processor-touching paths as out of scope.
- **Embedded lending:** `capital.wolt.com` cert covers `capital.finmid.com` → **Finmid** (embedded finance/lending partner) — merchant-facing, out of researcher reach.
- **BI/analytics:** `looker.wolt.com` (Looker); `brand-insights.wolt.com`, `retailreport.wolt.com` (merchant analytics).
- **Comms:** `email.comms.wolt.com` (email infra); link shorteners `l.wolt.com`, `links.wolt.com`-family.
- **Parent:** DoorDash, Inc. (acquisition closed 2022-05-31, ~$8.1B all-stock). DoorDash/Deliveroo/Tazz assets are **not** Wolt scope — do not cross the brand boundary without explicit scope listing.

## 4. Code & repos

Official org: **https://github.com/woltapp** — all public repos are peripheral (no backend):
`mitmproxy-mock` (mock/modify server responses via mitmproxy), `magic-di` (Python DI/FastAPI), `browserbug` (TS lint rules), `blurhash-python`, `wolt_modal_sheet` (Dart UI), `MainActorPublisher`, `DiamondDebounce`, `Locked` (Swift), internship pre-assignments. **No server-side or mobile-app source exposed.**

## 5. Videos & writeups

- YouTube — "I Found a Critical CVE on Wolt.com on Hackerone | CVE-2025-29927 PoC | $3,500 Bug Bounty" (The Cyber Eve; crawled ~2026-09-23): claims Next.js CVE-2025-29927 on wolt.com → $3,500. **Unverified third-party claim**; useful only as a Next.js signal.
- **0 disclosed/resolved reports on the HackerOne program** (per sibling plan's 2026-09-26 check) — but a **large legacy Intigriti Hall of Fame** (~90 handles: `0xcm1k3`, `0xd0m7`, `stok`, `zseano`-era crowd etc. — full list in the policy) means the classic surface was heavily worked before the H1 migration.
- Engineering blog (careers.wolt.com/en/blog/tech): Scala org decisions, observability/TRIM — architecture context only.
- Wolt Security whitepaper (2023, via assets.ctfassets.net): confirms bug bounty program, SIEM, developer-oriented vuln management — no technical detail useful for hunting.
- Medium: "Exploring the API of a website" (analytics-vidhya) documents the old `restaurant-api.wolt.com` endpoints — dated but shows the API shape.

## 6. Asset inventory — passive only (crt.sh `%.wolt.com`, pulled 2026-09-26)

Cert logs are **evidence of existence, not scope and not authorization**. Internal/ops hosts below must not be touched; they are listed so the operator can check the live Scope tab against them.

**Consumer / product:**
- `wolt.com` + `*.wolt.com` (wildcard) — main app
- `l.wolt.com` — short links (capability-URL surface candidate)
- `preferences.wolt.com` — notification/privacy preferences
- `links.woltforwork.wolt.com` — Wolt for Work (B2B)

**Merchant / Drive:**
- `links.merchant.wolt.com`, `merchant.links.wolt.com`, `merchant-access-control.wolt.com` — merchant link/access-control surfaces
- `webhooks-service.wolt.com` — Drive webhook service
- `cal.integrations.wolt.com` — integrations (Cal.com scheduling?)

**Identity / comms:**
- `identity.wolt.com` — identity service (unconfirmed purpose)
- `email.comms.wolt.com` — email infra

**Corporate/internal (do not touch; listed for scope cross-check only):**
- `internal.wolt.com`, `*.internal.wolt.com`, `*.dd-internal.wolt.com`, `*.eu-dd-internal.wolt.com`, `dash-internal.wolt.com`, `argo-flow-testing.internal.wolt.com`, `atlantis-test.prod.fg.wolt.com`, `ops.wolt.com`, `it.wolt.com`, `people.wolt.com`, `looker.wolt.com`, `util.wolt.com`, `status.wolt.com`, `blog.wolt.com`, `brand-insights.wolt.com`, `retailreport.wolt.com`, `capital.wolt.com` (→ Finmid)

**Mobile apps (in policy):** Android `com.wolt.android` (confirmed via Play Store link in policy); iOS app id `943905271` (confirmed via App Store link in policy), seller Wolt Oy, v26.38.0. Auth model: **phone-number + SMS OTP** (corroborated by the prevalence of virtual-number OTP services targeting Wolt).

**Acquisitions / brand perimeter:** DoorDash (parent, 2022); **Tazz** (Romanian delivery platform, acquired Oct 2024, finalized early 2025 — Tazz domains/apps are a plausible scope question; confirm on the live Scope tab, do not assume).

**Notable absences from cert logs:** no `courier.*`, `api.*`, `drive.*`, `partners.*`, `staging.*`, or `restaurant-api.*` names — courier tooling likely lives in mobile apps or behind the wildcard.

---

## 7. Hypothesis seeds (NEW — beyond W-1–W-9 in deep-hunt-plan.md)

All seeds assume: single self-registered consumer account (`shiva92@wearehackerone.com`), `X-HackerOne-Research: shiva92` on every request, test venue / test entities only, no real purchases, no payment methods, no mass account creation. **Promo/referral abuse via multi-accounting is dead on arrival** (mass entity creation is out of scope) — the seeds below avoid it.

### H-1 — Address-text vs geocoordinate desync in delivery-zone/fee validation
- **Hypothesis:** The checkout/fee-quote path validates the delivery zone against either the free-text address or the lat/lon, but not both consistently — submitting an in-zone address string with out-of-zone coordinates (or vice versa) yields a quotable/deliverable order the zone logic should reject, or a mismatched fee.
- **Why this target:** The old public API took raw `lat`/`lon` params (`/v1/pages/delivery?lat=..&lon=..`); fee and zone logic is inherently coordinate-driven while the UI is address-driven — the seam between the two is classic.
- **Expected observation:** Fee quote or order acceptance for a coordinate/address pair that disagrees on zone membership.
- **Vuln class:** Business-logic / validation desync (fee manipulation).

### H-2 — Scheduled-order TOCTOU: price/menu/venue-state changes between scheduling and firing
- **Hypothesis:** A scheduled order captures price, menu availability, and venue open-state at schedule time; if the venue closes, an item is removed, or prices change before the fire time, the order fires with stale data instead of re-validating.
- **Why this target:** Scheduled orders are explicitly advertised; P7/P8 state-machine desync is the highest-yield food-delivery pattern and is not covered by W-3 (which is post-confirmation modification).
- **Expected observation:** Fired order contains items/prices/venue-state that were invalid at fire time.
- **Vuln class:** TOCTOU / state-machine desync.

### H-3 — Double Order cross-venue contamination
- **Hypothesis:** Double Order merges two venues' carts into one order; venue-scoped attributes (delivery fee, promo eligibility, item availability windows, venue-specific taxes/fees) from venue A leak onto venue B's items or vice versa.
- **Why this target:** Multi-principal cart merging is rare logic — exactly where per-venue invariants break. (CONDITIONAL: needs two orderable venues; the test venue is one — if a second venue can't be used without a real purchase, downgrade to cart-level observation only.)
- **Expected observation:** Fee/promo/tax computed with the wrong venue's parameters on the merged order.
- **Vuln class:** Business-logic / broken object-level scoping.

### H-4 — `venue_id` substitution inside the checkout session
- **Hypothesis:** The cart/checkout session stores `venue_id` client-side or in a mutable session field; swapping it mid-checkout (test venue ↔ nonexistent/garbage IDs, never a real venue's data) changes pricing, fees, or availability without re-resolving the cart.
- **Why this target:** Distinct from W-2 (venue test-account boundary) — this is the *consumer* cart session, not the merchant account; session-held identifiers are a known weak point in the Play-monolith-era code.
- **Expected observation:** Checkout totals/availability change (or error differentially) when `venue_id` is swapped mid-flow.
- **Vuln class:** Business-logic / parameter tampering.

### H-5 — Gift-order claim links as bearer capabilities
- **Hypothesis:** Gift orders generate recipient claim links/tokens; the claim endpoint doesn't bind the token to the recipient's phone/account, so anyone with the link claims the gift (or the token is enumerable/guessable).
- **Why this target:** Direct transplant of the Uber trip-share seed family; gift flows are capability-URL designs that routinely skip recipient binding. Single-account testable (send gift to own second number/own email).
- **Expected observation:** Claim succeeds from a session/account that is not the designated recipient.
- **Vuln class:** Broken access control / insecure capability URLs.

### H-6 — `l.wolt.com` short-link open redirect / token oracle
- **Hypothesis:** Short links (`l.wolt.com/...`) used for order tracking/sharing resolve through a redirector that accepts attacker-influenced destinations, or the short-code space is enumerable, leaking other users' tracking pages.
- **Why this target:** Link shorteners on delivery platforms front order-tracking pages; the redirector is a small, rarely-audited service. (Read-only probing; never enumerate real users' links — test with own generated links only.)
- **Expected observation:** `?next=`/`url=`-style parameter honored to an external domain, or own-link codes enumerable by pattern.
- **Vuln class:** Open redirect / insecure direct object reference.

### H-7 — Comms-preference / unsubscribe token strength (`preferences.wolt.com`, `email.comms.wolt.com`)
- **Hypothesis:** Email/SMS preference-center links carry tokens that are predictable, non-expiring, or not bound to the account — allowing preference changes (or email-address confirmation actions) for another user.
- **Why this target:** Marketing-comms token systems are built by different teams than core auth and are chronically under-tested; both hosts exist in cert logs.
- **Expected observation:** Token from account A's email works to modify account B's preferences, or tokens show guessable structure.
- **Vuln class:** IDOR / weak token.

### H-8 — Wolt+ subscription state transitions
- **Hypothesis:** Delivery-fee waivers and perks key off a subscription flag with transition gaps: cancel-then-order in the grace window, order placed as member but delivered after cancellation, or trial re-eligibility checks done client-side.
- **Why this target:** Subscription state machines (trial → active → cancelled → grace) are bug-dense; Wolt+ is the monetization surface. (Abort before any payment step; test state transitions, never complete a paid signup.)
- **Expected observation:** Member pricing/waivers applied while the subscription is in a non-active state.
- **Vuln class:** Business-logic / state-machine desync.

### H-9 — Recycled-number account takeover (policy-blessed, opportunistic)
- **Hypothesis:** Wolt's phone-OTP login means whoever currently holds a recycled number inherits the previous owner's account — including saved payment methods and order history — with no re-verification of email or other factors.
- **Why this target:** The policy **explicitly** carves this out: "Signup with unverified mobile numbers (if you took over an existing number, then that's a finding!)." It is the only auth-adjacent class the policy invites.
- **Expected observation:** (Only if the operator legitimately obtains a recycled number previously tied to a Wolt account — e.g., their own old number.) Logging in with the recycled number yields the prior owner's account data.
- **Vuln class:** Authentication / account takeover via number recycling.
- **Caveat:** Do NOT manufacture this (no buying numbers to hunt strangers' accounts); opportunistic only, minimum-necessary access, stop at proof.

### H-10 — Self-delivery ↔ courier-delivery mode flip mid-checkout
- **Hypothesis:** Venues operating in self-delivery mode vs Wolt-courier mode carry different fee/tip/ETA logic; flipping the fulfillment mode (or the venue toggling it) between cart build and order confirmation leaves a stale fee or a courier-assignment contradiction on the order.
- **Why this target:** Wolt explicitly runs both models; mode is a venue-level attribute that checkout may snapshot inconsistently — a P7/P8 variant not covered by W-3.
- **Expected observation:** Order confirmed with a delivery fee/ETA from the wrong fulfillment mode, or courier assignment attempted on a self-delivery order.
- **Vuln class:** Business-logic / state-machine desync.

---

## 8. Kill-list (do not spend time — policy or evidence says no)

- Rate-limit bypass / missing rate limits — explicitly out of scope.
- Username/email enumeration — explicitly out of scope.
- CSRF / CORS / missing headers / missing cookie flags / clickjacking without proven impact — out of scope.
- CSV injection, host-header injection w/o business impact, subdomain takeover w/o proof — out of scope.
- `GATEKEEPER_API_KEY` exposure — explicitly not a secret.
- Multi-account promo/referral farming — mass entity creation is out of scope.
- Payment-processor testing — out of scope (processor identity unconfirmed; stay off it).
- Courier/merchant account acquisition by any means — not available, do not improvise.
- Customer-support chat interaction — forbidden.
- Internal/ops hosts from cert logs (`*.internal.wolt.com`, `ops`, `looker`, `people`, etc.) — not scope evidence; check the live Scope tab first.

## 9. Open questions for test day

1. The live Scope tab's asset table + bounty tiers did not render in the 2026-09-26 fetch — **re-pull before any test**; confirm whether `*.wolt.com`, mobile apps, `developer.wolt.com`, `merchant.wolt.com`, and `identity.wolt.com` are listed.
2. Is the test venue's order flow production-equivalent or stubbed? (Determines the weight of W-3/W-6/H-2/H-4 findings.)
3. Can the venue test account actually be claimed, given merchant accounts are "not available"? (Gates W-2.)
4. Is Tazz (Romania) in scope post-acquisition?
5. Current Next.js version on wolt.com (re: the CVE-2025-29927 third-party claim).
6. Does `restaurant-api.wolt.com` still exist behind the wildcard?

**Report complete. No active testing performed; all findings above are passive and unverified unless marked confirmed.**
