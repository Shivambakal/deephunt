# Deep-Hunt Execution Plan — Easy Bounties (2026-09-26)

**Date:** 2026-09-26 | **Status:** PLANNING ONLY — no tests executed.
**Targets (operator order, REVISED 23:36 IST):** 1. Wolt · 2. Live Nation · 3. Agoda Public (leftovers only, operator-manual).
Backups (A&F, Coupang TW, Chess.com) dropped per operator speed change.
> Operator correction 23:36 IST: Agoda was already hunted — its remaining hypotheses need his manual
> logged-in session. Fresh targets first. Section numbering below still reads 1=Agoda/2=Wolt/3=Live Nation
> from the draft; EXECUTION order is Wolt → Live Nation → Agoda.

---

## 1. Scope verification (read-only, done 2026-09-26)

| Target | Program page | Status |
|---|---|---|
| Agoda Public | https://hackerone.com/agoda-public | **LIVE** — full policy fetched today. Min $50. 0 resolved (directory snapshot). |
| Wolt | https://hackerone.com/wolt | **LIVE** — full policy fetched today. Min $100. 0 resolved on H1 (legacy Intigriti HoF large). |
| Live Nation | https://hackerone.com/live_nation | **LIVE** — handle confirmed via H1 directory search; full policy fetched today. Launch Sept 2026, 5 resolved, min $50. |

> If any policy changes, scope shrinks, or program pauses at execution time, mark that
> target **DEAD** and move to the next. Re-verify the policy page on the day of testing.

## 2. Global rules of engagement (all targets)

- **Enforced loop:** every test below is a plan, not an authorization. Before any
  action, open a `ResearchSession` (brain/session.py) and pass `propose_test()` with
  the 7 fields (hypothesis, expected observation, testing reason, scope_hosts,
  authorization basis, success/failure criteria), clear the 5-question adversarial
  self-check, mint a `TestAuthorization`, and run dry-run + scope gate. No token, no test.
- **Own data only:** accounts self-registered with the HackerOne alias
  `shiva92@wearehackerone.com` (h1 username: **shiva92**). Never touch another
  person's account, order, ticket, or data. Where a policy names test entities, use
  ONLY those.
- **Stop at proof:** confirm the primitive, capture evidence, stop. No data extraction
  beyond minimum, no destructive replay, no persistence of credential-shaped material.
- **Traffic discipline:** manual-paced, single requests. No automated scanning
  (Agoda and Live Nation explicitly prohibit it), no intruder bursts without a
  program-permitted, paced profile.
- **No money:** never complete a real purchase, never add payment methods, never pass
  KYC. Abort every purchase flow before the payment step.
- **Live Nation special:** policy states "Use bots, automated scanning tools, LLMs, or
  generative AI in the discovery of bugs. We only accept bugs found by humans." —
  discovery for Live Nation is human-driven; the agent plans/analyzes, the human
  operates the browser. No public disclosure of any kind, ever.
- **Capability honesty:** browser tasks cannot inject custom HTTP headers and do not
  currently route through the mitmproxy harness. Tests marked `operator-manual` need
  the human (or a brain-gated proxy-routed run via `proxy/repeater.py`, which supports
  header injection) — NOT executable by a plain browser task.

**Test-block legend (every test maps 1:1 to the enforced loop):**

- **H** hypothesis · **EO** expected observation · **TR** testing reason ·
- **SH** scope hosts · **AB** authorization basis · **SC** success criteria ·
- **FC** failure criteria · **PC** preconditions / session principal ·
- **EX** execution mode: `browser-task` (UI-only, no custom headers) or
  `operator-manual` (human browser + devtools, or brain-gated proxy run)

**Thinking traces:** under each attack, the operator-visible reasoning in five pipes —
INTAKE / HYPOTHESIZE / ADVERSARY / DESIGN / VERDICT. 5 lines, no fluff.

**Idea mapping:** `P1–P28` = novel-attacks-playbook.md ideas; `S1–S6` = Shopify
transfer seeds; `U1–U6` = Uber transfer seeds; `SC1–SC7` = Snapchat transfer seeds.

---

## 3. Target 1 — Agoda Public (easiest; already on-site)

**Program:** https://hackerone.com/agoda-public · **Min bounty:** $50
**Testing tag:** `User-Agent: hackerone-shiva92` on every request.
**Self-provisioned accounts:** shiva92's own test accounts (already registered).
**Test-property rules (ycs.agoda.com):** location = Test City, Comoros; name includes
"Test" + "Do not book"; description includes "For security testing".
**Do NOT touch:** booking tokens of any real booking (risk-accepted = ineligible),
other users' accounts/data, automated scanning, high traffic.

### A-1 — Multi-field PII enumeration via account/profile endpoints
**Maps:** P23. **H:** Account/profile lookup endpoints return PII (name, email, phone)
for foreign account IDs instead of 403. **EO:** Requesting a foreign profile/object ID
returns 200 with PII fields. **TR:** Agoda's own table lists "user personal information
enumeration (multiple fields)" as Medium→Critical. **SH:** www.agoda.com, ycs.agoda.com.
**AB:** Public H1 program; own test accounts + UA tag; read-only probes. **SC:** Foreign
(second own account B) profile returns PII to account A. **FC:** Identical minimal/403
responses regardless of account. **PC:** Two self-registered accounts A and B (both owned).
**EX:** browser-task (UI) for discovery; operator-manual for replay.
> **INTAKE:** P23 (wording/existence oracles); Agoda policy table: multi-field PII enumeration = Medium→Critical; recon: HttpOnly cookie auth, no client tokens — profile endpoints are server-driven.
> **HYPOTHESIZE:** Profile/lookup endpoints return PII for foreign account IDs instead of 403.
> **ADVERSARY:** Private program since 2016 already cleaned the obvious IDORs; "0 resolved" on the public launch ≠ untested. Single-field enumeration is None→Low — easy to burn a report on an ineligible variant.
> **DESIGN:** From account A request account B's profile/object IDs (both owned); diff field sets vs own. Expected: PII fields for B. Failure: identical minimal/403.
> **VERDICT:** Keep — multi-field only; count the fields in the report to clear the eligibility bar.

### A-2 — Booking-object IDOR between two own accounts
**Maps:** U1. **H:** Booking detail/modify endpoints authorize on booking-token possession
or session without binding bookingId to the session account. **EO:** GET/modify with B's
bookingId from A's session returns B's booking data or accepts changes. **TR:** IDOR is
Medium→Critical on Agoda's table; booking flow is the core asset. **SH:** www.agoda.com.
**AB:** Both bookings owned by researcher; no real guests. **SC:** Cross-account read or
write succeeds. **FC:** 403/redirect to own bookings; write rejected server-side. **PC:**
Accounts A and B; a cancelled/no-payment test booking each (never complete payment).
**EX:** operator-manual.
> **INTAKE:** Uber U1 (capability authorization); Agoda policy: booking tokens are risk-accepted on the manage-booking *page* — the API behind it may enforce differently.
> **HYPOTHESIZE:** The booking detail/modify API doesn't bind bookingId to the session account.
> **ADVERSARY:** If the API treats bookingId as the bearer token, this is by-design and ineligible (risk-accepted). Booking IDOR is the #1 reported class on a 10-year-old private program — duplicate risk is extreme.
> **DESIGN:** Two owned accounts, test bookings, no payment. From A, GET/modify B's bookingId. Expected: B's data or accepted write. Failure: 403/self-scope.
> **VERDICT:** Keep — but kill the variant that merely replays booking tokens on the risk-accepted page; only the API-path variant counts.

### A-3 — OTP verification bypass / rate-limit on own account
**Maps:** P10. **H:** OTP verify endpoint accepts unlimited attempts or accepts a
null/empty/replayed code. **EO:** Wrong codes never lock; or a consumed code re-verifies.
**TR:** "MFA (OTP) bypass" Low→High; "improper rate-limiting on authentication" Low→Medium.
**SH:** www.agoda.com. **AB:** Own account, own OTP channel. **SC:** Authentication completes
with invalid/replayed OTP, or >20 wrong attempts with no throttle. **FC:** Lockout/throttle
after few attempts; replayed codes rejected. **PC:** Own account with OTP enabled. **EX:** operator-manual.
> **INTAKE:** P10 (time-window attacks); Agoda table: OTP bypass Low→High, auth rate-limit Low→Medium.
> **HYPOTHESIZE:** The OTP verify endpoint accepts replayed/null codes or never throttles.
> **ADVERSARY:** Auth rate-limiting is the most-reported, most-duplicated class on every consumer program; Agoda caps it at Medium and triage demands demonstrated impact, not "no rate limit observed."
> **DESIGN:** Own account, own OTP. Try null/empty/replayed/wrong codes; count to 20 attempts. Expected: bypass or no throttle. Failure: lockout after a few.
> **VERDICT:** Keep — 15 minutes, cheap; kill immediately if throttling appears.

### A-4 — Stored payload in property fields → guest-facing render
**Maps:** P1, P26. **H:** Test-property fields (name/description/policy text) on
ycs.agoda.com render unescaped on the guest-facing property page or confirmation email.
**EO:** `<img src=x onerror>` or `{{7*7}}` in a Test property renders as active
markup/template output in a sink. **TR:** Stored XSS is Low→High; second-order sinks
evade scanners. **SH:** ycs.agoda.com, www.agoda.com. **AB:** Own Test property per
program's test-property rules; benign payloads. **SC:** Payload executes/reflects unescaped
in any sink. **FC:** Escaped/encoded in all observed sinks. **PC:** Test property created
per program rules. **EX:** browser-task (create + inspect); operator-manual for email sinks.
> **INTAKE:** P1 (write-in-A, detonate-in-B); P26 (visual/UI spoofing); stored XSS = Low→High on Agoda's table.
> **HYPOTHESIZE:** ycs.agoda.com property fields render unescaped in some guest-facing sink.
> **ADVERSARY:** OTA listing content feeds Google and partners through heavy sanitization pipelines; stored XSS on listing platforms is usually escaped at several layers. Test-property rules constrain what can be published.
> **DESIGN:** Create Test property per program rules; inject benign markup/{{7*7}} into name/description; inspect property page, confirmation, email sinks. Expected: unescaped execution. Failure: encoded everywhere.
> **VERDICT:** Keep — second-order sinks are exactly what scanners miss; delete the property after.

### A-5 — Open redirect on Rocketmiles/Hitrewards assets
**Maps:** —. **H:** Redirect parameters on Rocketmiles/Hitrewards login/click-through
endpoints accept arbitrary external URLs. **EO:** `?next=https://evil.example`
(researcher-controlled) produces a 302 to the external URL. **TR:** Explicitly eligible:
"Open redirect — Rocket Travel, Rocketmiles, Hitrewards assets: None→Medium".
**SH:** rocketmiles.com, hitrewards assets (confirm exact host from policy asset table at
test time). **AB:** Read-only navigation; PoC domain controlled by researcher. **SC:**
External redirect honored. **FC:** Allowlist enforced; external URLs rejected. **PC:** None.
**EX:** browser-task.
> **INTAKE:** Agoda policy table explicitly prices this: Rocket Travel/Rocketmiles/Hitrewards open redirect = None→Medium.
> **HYPOTHESIZE:** Redirect params on Rocketmiles/Hitrewards accept arbitrary external URLs.
> **ADVERSARY:** "Other assets" open redirect is None→Low — test the wrong host and the report is worthless. Redirect params are the first thing every hunter checks; duplicates likely.
> **DESIGN:** Read-only navigation; ?next=/redirect= to researcher-controlled domain. Expected: 302 external. Failure: allowlist.
> **VERDICT:** Keep — 10-minute read-only test; confirm the host is on the Rocket list first.

### A-6 — Price/currency tampering in checkout
**Maps:** P18, Uber $12k lesson. **H:** Checkout submits client-controlled
price/currency/quantity fields that the server trusts. **EO:** Modifying a hidden price
or currency field changes the charged/quoted total. **TR:** Business-logic price bugs are
the classic high-impact booking finding; stop before payment. **SH:** www.agoda.com.
**AB:** Own session, own test booking; abort before any payment step. **SC:** Server accepts
tampered total into the order summary. **FC:** Server recomputes from canonical values;
tampering ignored. **PC:** Test booking flow reachable without payment. **EX:** operator-manual.
> **INTAKE:** P18 (business arithmetic); Uber $12,000 negative-distance lesson — never trust client-submitted money fields.
> **HYPOTHESIZE:** Checkout trusts client-submitted price/currency fields.
> **ADVERSARY:** Booking platforms recompute server-side from inventory; tampered totals are usually ignored. The real payment step is a hard stop — you may never reach the vulnerable code path without paying.
> **DESIGN:** Own test booking; tamper hidden price/currency via proxy; abort before payment. Expected: tampered total in order summary. Failure: server recomputes.
> **VERDICT:** Keep — abort-before-payment variant only; kill any variant requiring a real charge.

### A-7 — Cross-subdomain session/cookie acceptance
**Maps:** U3, SC4. **H:** Session cookies issued by www.agoda.com are accepted by
ycs.agoda.com (or vice versa) with elevated effect. **EO:** Cookie replayed
cross-subdomain yields an authenticated session where it shouldn't. **TR:** Subdomain
trust differentials are a classic auth-boundary break. **SH:** www.agoda.com,
ycs.agoda.com. **AB:** Own sessions only. **SC:** Foreign-subdomain session accepted.
**FC:** Cookies scoped/rejected per-domain. **PC:** Authenticated sessions on both hosts.
**EX:** operator-manual.
> **INTAKE:** Uber U3 (cross-subdomain cookie acceptance); Snapchat SC4 (accounts↔web session confusion).
> **HYPOTHESIZE:** The www.agoda.com session cookie is accepted by ycs.agoda.com with effect.
> **ADVERSARY:** Consumer vs supplier extranet almost certainly use separate session issuers; recon shows HttpOnly server-side sessions — likely properly scoped. Low prior probability.
> **DESIGN:** Authenticate on www; replay cookie to ycs endpoints. Expected: authenticated where unexpected. Failure: rejected/scope-bound.
> **VERDICT:** Keep — 20 minutes; the supplier/consumer boundary is exactly where mistakes hide.

### A-8 — SSO/OAuth redirect_uri normalization
**Maps:** S1, SC1. **H:** "Sign in with Google/Apple" accepts redirect_uri variants
(trailing slash, path traversal, subdomain) not exactly matching registration. **EO:**
Authorization succeeds with a mutated redirect_uri, delivering code/token off-registered-target.
**TR:** Redirect-URI bypass → token theft is the highest-leverage login bug class.
**SH:** www.agoda.com. **AB:** Own OAuth flow; attacker redirect target researcher-controlled.
**SC:** Code/token delivered to unregistered URI. **FC:** Exact-match enforced; all mutations
rejected. **PC:** Social-login button present. **EX:** operator-manual.
> **INTAKE:** Shopify S1 (redirect URI normalization); Snapchat SC1 (Login Kit redirect bypass).
> **HYPOTHESIZE:** Social login accepts redirect_uri variants not exactly registered.
> **ADVERSARY:** If Agoda delegates entirely to Google/Apple's strict exact-match validation, there is no Agoda-side bug — one check decides this. Big-brand login is heavily reviewed.
> **DESIGN:** Initiate social login; mutate redirect_uri (trailing slash, path traversal, subdomain). Expected: code to unregistered URI. Failure: exact-match rejection.
> **VERDICT:** Keep — highest leverage class; first verify Agoda operates its own OAuth client rather than pure IdP delegation.

### A-9 — Cache poisoning via unkeyed headers on search/booking pages
**Maps:** P16, PortSwigger pattern. **H:** CDN cache keys ignore headers like
X-Forwarded-Host/X-Original-URL, letting one request poison cached responses for others.
**EO:** A request with a malicious unkeyed header is cached and served to a second clean
request. **TR:** Cache poisoning scales one request into stored impact; manual single-pair
test only. **SH:** www.agoda.com. **AB:** Two manual requests; benign canary marker only.
**SC:** Poisoned response served to clean request. **FC:** Headers keyed or stripped; no
cache hit. **PC:** Cacheable endpoint identified. **EX:** operator-manual.
> **INTAKE:** PortSwigger unkeyed-header pattern; P16 (Referer/info-flow thinking applied to cache keys).
> **HYPOTHESIZE:** The CDN cache key ignores X-Forwarded-Host/X-Original-URL on search/booking pages.
> **ADVERSARY:** Needs custom headers (operator-manual only); Agoda bans high traffic — this gets exactly ONE request pair. Most large OTAs key on host correctly by now.
> **DESIGN:** One request with canary unkeyed header; one clean request; compare. Expected: poisoned response served. Failure: headers keyed/stripped.
> **VERDICT:** Keep — single-pair manual test; kill if any response shows the header is keyed.

### A-10 — Search/autocomplete existence oracle + timing
**Maps:** P23. **H:** Booking-management or account-recovery endpoints distinguish
"exists" vs "not exists" via response wording or timing. **EO:** Valid vs invalid booking
references/emails produce distinguishable responses. **TR:** Enumeration oracles feed
targeted attacks; single-field is None→Low, multi-field Medium→Critical — document which.
**SH:** www.agoda.com. **AB:** Probes use researcher-owned references plus random invalid
ones. **SC:** Statistically distinguishable oracle. **FC:** Identical responses and timing.
**PC:** None. **EX:** operator-manual.
> **INTAKE:** P23 (wording/timing oracles); Agoda table splits single-field (None→Low) vs multi-field (Medium→Critical) enumeration.
> **HYPOTHESIZE:** Recovery/booking endpoints distinguish valid vs invalid references.
> **ADVERSARY:** A lone oracle is None→Low on Agoda's table — finding one and reporting it alone earns nothing; it only matters chained to multi-field extraction.
> **DESIGN:** Probe owned vs random references; compare wording/timing. Expected: distinguishable. Failure: identical.
> **VERDICT:** Keep as recon feeding A-1 (multi-field chain); never report a lone oracle.

**Order of attack (Agoda):** A-5 (read-only, 10 min) → A-8 → A-1 → A-10 → A-7 →
A-3 → A-4 → A-2 → A-6 → A-9.

---

## 4. Target 2 — Wolt

**Program:** https://hackerone.com/wolt · **Min bounty:** $100
**Mandatory header:** `X-HackerOne-Research: shiva92` on EVERY request — reports without
it can forfeit the bounty. (Browser tasks can't inject headers → nearly everything here
is operator-manual or proxy-routed.)
**Test entities (policy-provided, use ONLY these):**
consumer test account `user_id = 670fa3e9ead6e49d65cc3614`;
venue test account `venue_id = 670e7897e3c56dcc5b5a0989`;
test venue https://wolt.com/en/fin/helsinki/venue/test-670e7897e3c56dcc5b5a0989-sh0p (no real purchase).
**Accounts:** self-register customer accounts with `shiva92@wearehackerone.com` alias.
Courier/merchant accounts are NOT available — do not attempt to obtain them by other means.
**Do NOT touch:** any restaurant/venue or user data you don't own (explicit ⛔),
customer support staff, payment processors, mass entity creation.
**Exclusions to avoid:** CSV injection, homograph, username/email enumeration, impactless
rate-limit/CSRF/clickjacking/CORS findings, API-key disclosure without business impact.

### W-1 — Consumer→merchant/courier API boundary
**Maps:** U1, P15. **H:** Endpoints under merchant/courier API namespaces accept a consumer
session token and return non-public data or accept state changes. **EO:** Consumer-authed
request to a merchant/courier path returns 200 with data (not 401/403). **TR:** Three-role
systems fail open at role checks more often than anywhere else; policy explicitly frames the
roles as the surface. **SH:** wolt.com. **AB:** Own consumer account + mandatory header;
read-only first request. **SC:** Non-public merchant/courier data or state change with
consumer auth. **FC:** Consistent 401/403 across the namespace. **PC:** Consumer account;
candidate endpoints discovered via UI navigation. **EX:** operator-manual (header required).
> **INTAKE:** Uber U1 (capability authorization); P15 (session-token vs API-token scope asymmetry); Wolt policy frames consumer/merchant/courier roles as the testing surface.
> **HYPOTHESIZE:** Merchant/courier API namespaces accept a consumer session token.
> **ADVERSARY:** Role separation is the first thing a food-delivery platform gets audited on; the Intigriti legacy crowd (large HoF) already worked this surface for years. Needs the custom header — a plain browser task can't even run it.
> **DESIGN:** Map candidate merchant/courier paths via UI; replay with consumer session + X-HackerOne-Research header, read-only first. Expected: 200 with non-public data. Failure: consistent 401/403.
> **VERDICT:** Keep — the role boundary is the single most-likely bug location; run the 403/400 diagnosis ladder before concluding.

### W-2 — Venue test-account boundary (cross-venue IDOR) [CONDITIONAL]
**Maps:** P13, U1. **H:** Venue-scoped endpoints (menu, settings, orders) authorize on
venue_id from the request, letting the test venue account reach other venues' objects by
ID substitution. **EO:** Substituting another venue_id returns that venue's data. **TR:**
IDOR on the money side of a 3-sided marketplace. **SH:** wolt.com. **AB:** ONLY the
policy-provided venue test account; substitute IDs, read-only. **SC:** Another venue's
non-public data returned. **FC:** Strict venue binding; 403 on substitution. **PC:** Venue
test account claimable (policy says merchant accounts unavailable — if the venue test
account can't be claimed, mark BLOCKED, don't improvise). **EX:** operator-manual.
> **INTAKE:** P13 (scope boundary declared on one argument not constraining every object touched); U1; policy hands you a venue_id — the intended test is cross-venue reach.
> **HYPOTHESIZE:** Venue-scoped endpoints authorize on request-supplied venue_id, not the session's venue.
> **ADVERSARY:** The venue test account may not be claimable at all (merchant accounts "not available") — this whole test may be stillborn. Even if claimable, venue binding is usually server-side on mature platforms.
> **DESIGN:** Claim venue test account per policy; substitute other venue_ids on menu/order endpoints, read-only. Expected: foreign venue data. Failure: 403/binding.
> **VERDICT:** Keep CONDITIONAL — verify claimability first; if unclaimable, kill and move on, don't improvise access.

### W-3 — Order state-machine: post-lock modification
**Maps:** P7/P8, P18. **H:** After an order is confirmed/priced, item/quantity/address
modifications are still accepted and the price isn't recomputed. **EO:** PATCH/POST to a
confirmed order changes items while the total stays stale. **TR:** Time-of-check/time-of-use
on the money path. **SH:** wolt.com. **AB:** Own orders on the TEST venue only (no real
purchase available there — matches policy). **SC:** Order mutated after price lock with stale
total. **FC:** Immutable after confirmation, or totals recompute. **PC:** Test-venue order
flow. **EX:** browser-task for flow mapping; operator-manual for tamper.
> **INTAKE:** P7/P8 (state-machine desync — validate at schedule time vs fire time); P18 (business arithmetic).
> **HYPOTHESIZE:** A confirmed order still accepts item/quantity/address changes without repricing.
> **ADVERSARY:** The test venue explicitly has "no real purchase available" — the order flow may be stubbed/mocked, making any finding inapplicable to production. State machines on checkout are usually locked.
> **DESIGN:** Build order on test venue; confirm; then PATCH items/quantity/address. Expected: mutation accepted, total stale. Failure: immutable or repriced.
> **VERDICT:** Keep — but weight any finding by whether the test venue behaves like production; a stubbed flow makes it informational.

### W-4 — Delivery/address boundary vs the consumer test account
**Maps:** U1. **H:** Address-book or order-history endpoints keyed by user_id accept the
policy's consumer test `user_id` from a different account's session. **EO:** Requesting
user_id 670fa3e9ead6e49d65cc3614's addresses/orders from own session returns data. **TR:**
The policy hands you a second user_id — the intended test is whether its data is reachable
cross-account. **SH:** wolt.com. **AB:** Policy-provided test user_id; own session; read-only.
**SC:** Test account's data readable cross-account. **FC:** 403/self-only. **PC:** Own consumer
account. **EX:** operator-manual.
> **INTAKE:** U1; Wolt policy: "if you need to test any sort of access to user data, do it only against this specific consumer test account" — it exists to be probed cross-account.
> **HYPOTHESIZE:** Address/order endpoints keyed by user_id don't verify the session owns that user_id.
> **ADVERSARY:** The test account exists precisely so researchers hammer it — the program team surely hardened exactly this path. Also: accessing even a test account's data beyond the minimum is against the spirit; keep probes minimal.
> **DESIGN:** From own session, request the test user_id's addresses/orders, read-only. Expected: data returned. Failure: 403/self-only.
> **VERDICT:** Keep — this is the policy-invited test; minimum-necessary reads only.

### W-5 — Promo/voucher stacking and reuse [CONDITIONAL]
**Maps:** P18, Shopify discount-stacking lesson. **H:** Multiple promos stack without
server-side combinability checks, or a single-use voucher is reusable (replay/double-apply).
**EO:** Two promos apply to one order, or the same code discounts twice. **TR:** Promo logic
is the softest retail surface; policy doesn't exclude it. **SH:** wolt.com. **AB:** Own
account, test venue, promo codes issued to researcher only. **SC:** Stacked/reused discount
accepted server-side. **FC:** Combinability enforced; single-use enforced. **PC:** Valid promo
code(s) for own account. **EX:** browser-task (UI); operator-manual for replay.
> **INTAKE:** P18; Shopify $10,000 discount-stacking lesson — "test discount/coupon stacking."
> **HYPOTHESIZE:** Wolt promos stack or single-use codes replay.
> **ADVERSARY:** No promo codes may be available to a fresh test account — the entire test depends on obtaining one legitimately. Promo engines at scale usually enforce combinability server-side; the legacy Intigriti crowd likely tried.
> **DESIGN:** Apply two promos to one test-venue order; attempt code reuse via replay. Expected: stacked/reused discount. Failure: enforced.
> **VERDICT:** Keep CONDITIONAL — only if legitimate promo codes land in the test account; never manufacture or guess codes.

### W-6 — Price/fee arithmetic: zero/negative/precision
**Maps:** P18, Uber $12k lesson. **H:** Quantity, tip, or fee fields accept zero/negative/
high-precision values that survive to the total. **EO:** Negative quantity or negative tip
reduces the order total. **TR:** Arithmetic trust in client-submitted money fields.
**SH:** wolt.com. **AB:** Own test-venue order; never submit payment. **SC:** Total decreases
or goes negative server-side. **FC:** Server-side validation/clamping. **PC:** Test-venue
checkout. **EX:** operator-manual.
> **INTAKE:** P18; Uber $12,000 negative-distance fare lesson — "test negative values in all fields."
> **HYPOTHESIZE:** Quantity/tip/fee fields accept zero/negative/high-precision values into the total.
> **ADVERSARY:** Money fields are the most fuzzed inputs on any delivery app; server-side clamping is standard. Test venue may be stubbed (see W-3).
> **DESIGN:** Tamper quantity/tip/fee to zero/negative/high-precision on test-venue checkout; abort before payment. Expected: total decreases or goes negative. Failure: clamped/validated.
> **VERDICT:** Keep — 20 minutes; the Uber precedent says this class pays when it hits.

### W-7 — GraphQL capability-token authorization and stale revocation
**Maps:** U1, P10. **H:** Wolt's API issues capability/purpose-scoped tokens (order tracking
links, share links) that remain valid after the granting context is revoked/cancelled.
**EO:** A token minted for order X works after order X is cancelled, or works on order Y.
**TR:** Direct transfer of the Uber trip-share seed; stale capabilities are under-tested.
**SH:** wolt.com. **AB:** Own orders/tokens only. **SC:** Revoked-context token still
authorizes. **FC:** Tokens die with their context. **PC:** Order flow producing tokens/links.
**EX:** operator-manual.
> **INTAKE:** Uber U1 (trip-share GraphQL capability authorization + stale revocation) — the exact seed, transplanted.
> **HYPOTHESIZE:** Order tracking/share tokens survive cancellation or work cross-order.
> **ADVERSARY:** Requires an order flow that mints such tokens — on the test venue with no real purchase, these may not exist. Speculative until the token surface is confirmed.
> **DESIGN:** Complete test-venue order actions; capture any tracking/share tokens; cancel/expire the context; replay. Expected: still authorizes. Failure: dead with context.
> **VERDICT:** Keep — but first confirm a token surface exists; kill if the flow mints nothing replayable.

### W-8 — Consumer session accepted on merchant/courier web surfaces
**Maps:** U3, SC4. **H:** Session/token issued to the consumer app is accepted by
merchant-portal or courier web endpoints. **EO:** Consumer cookie/token yields authenticated
responses on a merchant/courier host or path. **TR:** Cross-surface session confusion across
the three roles. **SH:** wolt.com and any merchant/courier subdomains listed in scope.
**AB:** Own consumer session only. **SC:** Authenticated cross-surface access. **FC:**
Audience-bound rejection. **PC:** Consumer session; merchant/courier surface URLs.
**EX:** operator-manual.
> **INTAKE:** Uber U3 (cross-subdomain cookie acceptance); Snapchat SC4 (accounts↔web session confusion).
> **HYPOTHESIZE:** The consumer session is accepted on merchant/courier surfaces.
> **ADVERSARY:** Separate apps usually mean separate token issuers/audiences; consumer JWTs rejected elsewhere is the default correct behavior. Finding the merchant/courier surface URLs may itself be the hard part.
> **DESIGN:** Capture consumer session; present it to merchant/courier hosts/paths. Expected: authenticated responses. Failure: audience-bound rejection.
> **VERDICT:** Keep — cheap to test once W-1's endpoint map exists; run it as an extension of W-1.

### W-9 — Stored payload in delivery instructions / profile fields
**Maps:** P1. **H:** Free-text fields (delivery instructions, profile name, address notes)
render unescaped in the order-tracking or venue view. **EO:** Benign markup payload reflects
unescaped in a downstream sink. **TR:** Second-order stored sink; courier app unavailable so
test consumer/venue sinks. **SH:** wolt.com. **AB:** Own account, benign payloads, test venue.
**SC:** Unescaped reflection in any sink. **FC:** Escaped everywhere. **PC:** Own account.
**EX:** browser-task.
> **INTAKE:** P1 (second-order stored sinks); the courier app — the highest-risk sink — is unavailable, so consumer/venue sinks only.
> **HYPOTHESIZE:** Free-text fields render unescaped in order-tracking or venue views.
> **ADVERSARY:** Without the courier app you can't reach the most dangerous sink; consumer-side rendering of own instructions is low-impact and likely sanitized. This is the weakest test in the Wolt set.
> **DESIGN:** Inject benign markup into delivery instructions/profile fields on own test-venue order; inspect tracking/venue views. Expected: unescaped reflection. Failure: escaped everywhere.
> **VERDICT:** Keep — browser-task executable, near-zero cost; deprioritize behind W-1/W-4/W-6.

**Order of attack (Wolt):** W-9 (read-only UI, no header needed for pure UI) → W-1 →
W-8 → W-4 → W-2 (conditional) → W-3 → W-6 → W-5 (conditional) → W-7.
Header first: no request without `X-HackerOne-Research: shiva92`.

---

## 5. Target 3 — Live Nation (flagship: explicit test campaigns)

**Program:** https://hackerone.com/live_nation · **Min bounty:** $50 · Launch Sept 2026, 5 resolved.
**Mandatory:** `X-HackerOne-Research: shiva92` header on all traffic; accounts created
with `shiva92@wearehackerone.com`; **human-discovered bugs only** (no bots, scanners, or
LLM/AI-assisted discovery — agent plans, human operates); no public disclosure ever;
test ONLY explicitly listed assets; no excessive traffic; redact PII from reports;
do NOT name artists/events/teams in reports.
**Out-of-scope bug classes:** XSS, missing headers, DoS, social engineering.
**In-scope bug classes:** ATO, priv-esc, IDOR, auth/MFA/OTP/IDV bypass, SQLi, SSRF,
subdomain takeover, impactful CSRF, SafeTix bypass, ticket-transfer bypass, onsale
queue exploitation.
**Two explicit campaigns (rare — treat as the front door):**
- **ASU/Persona verification bypass:** isolated test event at
  https://signup.ticketmaster.com/bugbountytest — test ONLY this URL. Objective:
  complete sign-up / reach post-verification state without a valid Persona check.
- **SafeTix 2.0:** bypass = ticket rendered+scanned on unbound device, duplicated
  tickets scanning, scannable after violating device limits, or scannable via
  legacy/wallet fallback paths. Test tickets provided on request.

### L-1 — Persona/IDV bypass on the ASU test campaign (FLAGSHIP)
**Maps:** — (program-authored campaign). **H:** The Persona identity-verification step on
the isolated ASU flow can be skipped, replayed, or satisfied with invalid input, reaching
post-verification state. **EO:** Sign-up completes or advances past verification without a
valid Persona check. **TR:** The program explicitly invites exactly this test on an isolated
URL — highest signal-to-effort in the whole plan. **SH:** signup.ticketmaster.com/bugbountytest
ONLY. **AB:** Campaign authorization in the live policy; test event isolated from production.
**SC:** Post-verification state without valid verification. **FC:** Every bypass path forces
a valid Persona check. **PC:** None. **EX:** operator-manual (human-driven per program rule).
> **INTAKE:** Live Nation policy itself (2026-09-26 fetch): dedicated ASU campaign with an isolated test URL and a precise bypass definition — the program telling researchers exactly what to break.
> **HYPOTHESIZE:** The Persona verification step can be skipped, replayed, or satisfied with invalid input.
> **ADVERSARY:** 5 reports already resolved — the campaign has been live since the September launch and the obvious bypasses may be taken. Persona is a mature vendor; the bug is more likely in Live Nation's state machine around it than in Persona itself.
> **DESIGN:** Walk the 7-step flow (landing → account → email → phone → redirect → Persona → completion); at the Persona step try skip/replay/param-tamper/back-navigation. Expected: post-verification state without valid check. Failure: every path forces a valid check.
> **VERDICT:** Keep — run FIRST. An explicitly invited, isolated verification-bypass test is the rarest high-value setup in this plan; test ONLY the given URL.

### L-2 — MFA/OTP bypass on own fan account
**Maps:** P10, SC7. **H:** Login or sensitive-action OTP can be bypassed via code replay,
null/empty code, or response tampering. **EO:** Authentication/action completes without a
valid OTP. **TR:** "Authentication, MFA, and OTP bypass" explicitly in scope. **SH:**
ticketmaster.com / livenation.com (confirm listed assets at test time). **AB:** Own account,
own OTP channel. **SC:** Bypass demonstrated. **FC:** OTP strictly enforced. **PC:** Own
account with MFA enabled. **EX:** operator-manual.
> **INTAKE:** P10 (time windows); Snapchat SC7 (login CSRF/state binding); in-scope class per policy.
> **HYPOTHESIZE:** Login or sensitive-action OTP accepts replayed/null codes or is skippable via response tampering.
> **ADVERSARY:** Ticketmaster's auth is a hardened, heavily-attacked surface (credential stuffing capital of the internet); OTP bypass here would likely have been found. Duplicate risk high.
> **DESIGN:** Own account, own OTP. Replay/null/skip variants on login and on sensitive actions (transfer, email change). Expected: bypass. Failure: strict enforcement.
> **VERDICT:** Keep — in-scope and cheap; focus on sensitive-action OTP (transfer/withdraw) where logic is custom, not the commoditized login OTP.

### L-3 — Ticket/order IDOR between two own accounts
**Maps:** U1. **H:** Ticket/order objects are addressable by guessable IDs and readable or
transferable cross-account. **EO:** Account A reads or acts on account B's ticket/order by
ID substitution. **TR:** IDOR explicitly in scope; ticketing objects are the crown jewels.
**SH:** ticketmaster.com. **AB:** Both accounts owned; test tickets only. **SC:** Cross-account
read or state change. **FC:** Strict ownership binding. **PC:** Two own accounts. **EX:** operator-manual.
> **INTAKE:** Uber U1; IDOR explicitly in-scope; tickets are bearer instruments — the object model is the asset.
> **HYPOTHESIZE:** Ticket/order IDs are enumerable and not ownership-bound on all verbs.
> **ADVERSARY:** Ticketing platforms bind tickets to accounts fanatically (fraud is their existential threat); the GET/POST verb asymmetry (P-contradiction rule) is the only realistic seam, and it's a long shot.
> **DESIGN:** Two owned accounts; enumerate own ticket/order ID patterns; substitute B's IDs from A's session across GET/PATCH/POST/DELETE. Expected: cross-account read or mutation. Failure: ownership enforced on all verbs.
> **VERDICT:** Keep — run the full verb matrix; the contradiction (GET checks ownership, PATCH doesn't) is the finding if it exists.

### L-4 — Ticket transfer without MFA (SafeTix)
**Maps:** — (program-authored). **H:** The transfer flow's MFA/OTP step can be skipped or
replayed, moving a ticket between accounts without verification. **EO:** Transfer completes
with no/invalid OTP. **TR:** Program names "ticket transfer bypass: transferring tickets
without MFA" as an in-scope business-logic class. **SH:** ticketmaster.com. **AB:** Own
accounts; request test tickets per policy. **SC:** Transfer without valid MFA. **FC:** MFA
enforced on every transfer path (note: >90-day low-risk account pairs are EXPECTED to
transfer — exclude that case). **PC:** Two own accounts; test tickets. **EX:** operator-manual.
> **INTAKE:** Live Nation policy SafeTix section — "transferring tickets without MFA" named as an in-scope class, with test tickets available on request.
> **HYPOTHESIZE:** The transfer flow's MFA step can be skipped or its OTP replayed.
> **ADVERSARY:** SafeTix is their flagship anti-fraud product — the transfer MFA path is the most-reviewed code they own. The >90-day low-risk carve-out means you must carefully exclude expected behavior or the report dies as N/A.
> **DESIGN:** Request test tickets; initiate transfer A→B; tamper/skip/replay the MFA step. Expected: transfer without valid MFA. Failure: enforced on all paths.
> **VERDICT:** Keep — program-invited; exclude the 90-day low-risk expected-behavior case explicitly in notes.

### L-5 — Onsale queue position manipulation
**Maps:** P18. **H:** Queue position/token is client-influenced (cookie, parameter, or
timing) and can be advanced without waiting. **EO:** Modified queue state reaches the front
without the wait. **TR:** Explicitly in scope: "reaching the front of the queue without
waiting". **SH:** ticketmaster.com. **AB:** Own session; single manual attempts, no
automation, no traffic spikes. **SC:** Front-of-queue without waiting. **FC:** Server-side
fair queueing. **PC:** An onsale/queue flow reachable without buying. **EX:** operator-manual.
> **INTAKE:** P18; policy explicitly scopes "onsale queue exploitation: reaching the front of the queue without waiting."
> **HYPOTHESIZE:** Queue position is client-influenced and advanceable without waiting.
> **ADVERSARY:** "No excessive traffic" + queue systems are built to resist exactly this; a single manual attempt has low odds, and repeated attempts risk looking like abuse. Queue-it-style systems are server-authoritative.
> **DESIGN:** Join a queue with own session; inspect position token/cookie; single careful mutation attempt. Expected: advanced position. Failure: server-side ordering.
> **VERDICT:** Keep — but ONE careful attempt only; this is the test most likely to look like abuse if repeated. Kill on first clean failure.

### L-6 — Password-reset / account-recovery token binding
**Maps:** SC7, U-transfer. **H:** Reset tokens are not bound to the requesting
account/session, or remain valid after use or after email change. **EO:** Token issued for
account A resets account B, or a used token replays. **TR:** ATO-class; explicitly in scope.
**SH:** ticketmaster.com / livenation.com. **AB:** Both accounts owned; own mailbox alias.
**SC:** Cross-account reset or replay. **FC:** Single-use, account-bound tokens. **PC:** Two
own accounts. **EX:** operator-manual.
> **INTAKE:** Snapchat SC7 (login CSRF/state binding); classic ATO primitive, explicitly in-scope as account takeover.
> **HYPOTHESIZE:** Reset tokens aren't bound to the requesting account or survive use/email-change.
> **ADVERSARY:** Password-reset is the most checklist-audited flow in existence; single-use + account-bound + expiring is the industry default, and Ticketmaster has been burned here before.
> **DESIGN:** Request reset for A; try the token on B's reset endpoint; replay a used token; change email then reuse. Expected: cross-account or replay success. Failure: bound, single-use, expired.
> **VERDICT:** Keep — 30 minutes; the email-change-then-reuse variant is the least-audited seam.

### L-7 — OAuth/SSO redirect and session handling at login
**Maps:** S1, SC1, SC4. **H:** Social-login redirect_uri accepts unregistered variants, or
the web session and the accounts-system session confuse (login CSRF / state binding failure).
**EO:** Code/token to unregistered URI, or cross-session auth confusion. **TR:** Login-layer
bugs are ATO-adjacent and in scope. **SH:** ticketmaster.com / livenation.com. **AB:** Own
flows; researcher-controlled redirect target. **SC:** Token misdelivery or session confusion.
**FC:** Exact-match + state binding enforced. **PC:** Social login present. **EX:** operator-manual.
> **INTAKE:** Shopify S1; Snapchat SC1/SC4; Ticketmaster runs a complex multi-brand identity layer (livenation.com ↔ ticketmaster.com) — brand-crossing SSO is the seam.
> **HYPOTHESIZE:** redirect_uri accepts unregistered variants, or sessions confuse across the brand boundary.
> **ADVERSARY:** If login delegates to a hardened IdP, redirect_uri is exact-matched there; the realistic bug is Live Nation's own state/nonce handling, which is custom code — but also custom-reviewed.
> **DESIGN:** Mutate redirect_uri through the brand-crossing login; test state/nonce binding and session confusion. Expected: misdelivery or confusion. Failure: exact-match + binding.
> **VERDICT:** Keep — prioritize the livenation.com↔ticketmaster.com brand-crossing variant over generic redirect_uri fuzzing.

### L-8 — API capability/authorization differential on fan APIs
**Maps:** U1, P15. **H:** Fan-facing API endpoints (favorites, alerts, payment methods,
saved events) authorize inconsistently — GET checks ownership but PATCH/DELETE checks only
authentication. **EO:** A mutating verb on another-owned object succeeds where read fails,
or vice versa. **TR:** The playbook's contradiction rule: method-level authz asymmetry.
**SH:** ticketmaster.com / livenation.com APIs. **AB:** Own accounts A and B; read-only probes
first. **SC:** Authz contradiction demonstrated. **FC:** Consistent ownership checks on all
verbs. **PC:** Two own accounts. **EX:** operator-manual.
> **INTAKE:** U1; P15; the playbook's contradiction rule — "when expected ≠ observed (GET checks ownership, PATCH checks only authentication), that contradiction is the finding."
> **HYPOTHESIZE:** Fan API endpoints enforce ownership inconsistently across HTTP verbs.
> **ADVERSARY:** Requires mapping the fan API surface first, which costs real time; most endpoints may be uniformly guarded. Saved payment methods are the highest-value and best-guarded.
> **DESIGN:** Map fan APIs (favorites, alerts, payment methods); run the verb matrix A→B objects. Expected: verb asymmetry. Failure: uniform enforcement.
> **VERDICT:** Keep — run after L-3; start with low-sensitivity objects (favorites/alerts) before touching payment-method endpoints.

### L-9 — Email-change → verification desync
**Maps:** P7/P8, SC4. **H:** Changing the account email doesn't re-trigger verification, or
the old email retains recovery capability after change. **EO:** Email changed without
verification, or reset links still go to the old address. **TR:** State-machine desync on
the identity anchor. **SH:** ticketmaster.com / livenation.com. **AB:** Own account; own
alias mailbox. **SC:** Unverified email becomes primary, or old email retains recovery.
**FC:** Re-verification enforced; old email fully detached. **PC:** Own account. **EX:** browser-task (UI flow).
> **INTAKE:** P7/P8 (state desync); SC4 (session/identity confusion).
> **HYPOTHESIZE:** Email change doesn't re-trigger verification, or the old email retains recovery.
> **ADVERSARY:** This is standard, well-worn account-management logic; the realistic yield is a UX-level finding, not a bounty. Lowest expected value in the Live Nation set.
> **DESIGN:** Change account email via UI; check whether verification is required and whether the old address still receives resets. Expected: desync. Failure: clean re-verification.
> **VERDICT:** Keep — browser-task executable, near-zero cost; run it as filler while waiting on test tickets for L-4.

### L-10 — Subdomain takeover on listed assets
**Maps:** — (explicitly in scope: "DNS subdomain takeover"). **H:** A listed asset has a
dangling DNS record (CNAME to unclaimed service). **EO:** CNAME resolves to a claimable
service; claim verified with benign proof. **TR:** Explicitly in scope; passive DNS only
until a dangling record is found. **SH:** Only hosts in the program's in-scope asset table.
**AB:** Passive DNS/cert-log inspection; claim only with benign proof. **SC:** Takeover
demonstrated with benign proof. **FC:** No dangling records on listed assets. **PC:** Asset
table from policy. **EX:** operator-manual (passive recon).
> **INTAKE:** Policy explicitly lists "DNS subdomain takeover" as in-scope — unusual and valuable.
> **HYPOTHESIZE:** A listed asset has a dangling CNAME to a claimable service.
> **ADVERSARY:** Takeover-hunting is fully passive and every hunter does it; Live Nation's estate is actively managed post-breach-history. Odds are low, but cost is near zero.
> **DESIGN:** Pull the in-scope asset table; check DNS CNAMEs against claimable-service fingerprints via cert logs; claim only with benign proof file. Expected: dangling record. Failure: clean.
> **VERDICT:** Keep — passive, cheap, runs in parallel with everything else; never touch unlisted hosts.

**Order of attack (Live Nation):** L-1 (explicit invitation, isolated) → L-10 (passive,
parallel) → L-2 → L-4 → L-6 → L-3 → L-8 → L-7 → L-9 → L-5.

---

## 6. Cross-target execution order

1. **Agoda A-5** (10-min read-only) → **A-8** → **A-1/A-10** — fastest possible first signal.
2. **Live Nation L-1** (flagship campaign) + **L-10** (passive, parallel).
3. **Wolt W-9** (UI-only) → **W-1/W-8/W-4** (header-required; batch as one proxy session).
4. Remaining Agoda (A-7, A-3, A-4, A-2, A-6, A-9) interleaved with Live Nation L-2/L-4/L-6/L-3/L-8/L-7.
5. Fillers: L-9, L-5 (single attempt), W-3/W-6, conditionals W-2/W-5.

## 7. Per-test execution checklist (before ANY action)

- [ ] Policy page re-fetched today; target not marked DEAD.
- [ ] `ResearchSession` opened; `propose_test()` passed with the 7 fields from the test block.
- [ ] 5-question adversarial self-check cleared; `TestAuthorization` minted.
- [ ] Dry-run + scope gate passed (hosts ⊆ program scope; no unlisted hosts).
- [ ] Correct identity material: `User-Agent: hackerone-shiva92` (Agoda) /
  `X-HackerOne-Research: shiva92` (Wolt, Live Nation) / `X-HackerOne-Researcher: shiva92` (n/a — Coupang dropped).
- [ ] Accounts: `shiva92@wearehackerone.com` alias only; test entities only where provided.
- [ ] Stop conditions armed: disproven / sufficient evidence / low info value / uncertain scope / unsafe validation → stop and record.

## 8. What stays blocked (do not work around)

- Raw HTTP with custom headers from a plain browser task → use operator-manual or
  brain-gated `proxy/repeater.py` runs.
- Wolt/Live Nation discovery must be human-driven for Live Nation (program rule);
  for Wolt it's a header-delivery constraint, not a discovery ban.
- Live Nation SafeTix device-level tests need test tickets (request per policy) and the
  current mobile app — beyond browser-only reach; L-4 web-path variants come first.
- No second mailbox access, no Gmail checks, no automated scanning, no real payments.
