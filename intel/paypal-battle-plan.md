# PayPal Authenticated Battle Plan

**Date:** 2026-09-26 · **Status:** PLAN ONLY — no testing performed, no requests sent.
**Source:** `paypal-vdp-recon.md` (read 2026-09-26) + methodology §5 (business-logic/state-machine research).
**Scope:** PayPal HackerOne paid program — `www.paypal.com`, `www.venmo.com`, `www.xoom.com`, `www.braintreepayments.com`, `my.loanbuilder.com`, `www.hyperwallet.com`. Merchant-integration bugs and sandbox-only issues are out of scope (Braintree sandbox excepted at 50%).
**Money rule:** play money only, sandbox first. No real funds moved at any point.

> Program terms reminder (from recon): test accounts as `<username>+pp@wearehackerone.com`;
> header `X-PP-BB: HackerOne-<username>` on all traffic; log the test IP for the report;
> DoS sandbox-only; benign RCE PoCs only; delete inadvertently accessed data after closure;
> no public disclosure without PayPal's prior written approval.

---

## 1. Sandbox setup checklist

Do these in order before any test case runs.

- [ ] **1.1 Developer dashboard access.** Sign in at `developer.paypal.com` with the researcher's PayPal account. (Requires the account holder's login — cannot be delegated.)
- [ ] **1.2 Create three sandbox accounts** (Dashboard → Sandbox → Accounts → Create Account):
  - `merchant-a`: Business (US), clearly labeled test (e.g. `merchant-a-pp-test@…`).
  - `merchant-b`: Business (US), second credential set for cross-merchant tests.
  - `buyer`: Personal (US), the payer principal.
  - Email naming: use clearly synthetic addresses; for any account registered on PayPal systems follow `<username>+pp@wearehackerone.com`.
- [ ] **1.3 Fund the buyer.** In the sandbox account list, open `buyer` → add fake balance (e.g. $10,000 USD play money). Confirm balance via the sandbox `buyer` login or API.
- [ ] **1.4 Create one REST API app per business account** (Dashboard → My Apps & Credentials → Sandbox → Create App, once while "logged in as" each sandbox business account context or via the account switcher). Record each app's `client_id`. Store each `client_secret` in the Secure Vault — never in the plan file, logs, or chat.
- [ ] **1.5 Verify OAuth.** For each app:
  ```
  POST https://api-m.sandbox.paypal.com/v1/oauth2/token
  Authorization: Basic base64(client_id:client_secret)
  Content-Type: application/x-www-form-urlencoded
  Body: grant_type=client_credentials
  X-PP-BB: HackerOne-<username>
  ```
  Expect `200` with `access_token`, `token_type: "Bearer"`, `expires_in`. Save the token per credential set (tokens are short-lived; re-mint as needed).
- [ ] **1.6 Webhook listener.** Create a request catcher (e.g. `webhook.site`) — this is your listener URL. In each app's settings add webhooks subscribing to: `PAYMENT.CAPTURE.COMPLETED`, `PAYMENT.CAPTURE.DENIED`, `PAYMENT.CAPTURE.REFUNDED`, `PAYMENT.CAPTURE.REVERSED`, `BILLING.SUBSCRIPTION.*`, `PAYOUTS.ITEM.*`, `CUSTOMER.DISPUTE.CREATED`. Keep the listener open during test runs.
- [ ] **1.7 Baseline balances.** Record starting sandbox balances for `merchant-a`, `merchant-b`, `buyer` (screenshot or API read). Every money test starts from a recorded baseline.
- [ ] **1.8 Traffic hygiene.** All requests carry `X-PP-BB: HackerOne-<username>`. Generate a fresh `PayPal-Request-Id` (UUID) for each POST that supports idempotency — and deliberately *re-use* one only when a test case calls for it. Log the egress test IP once; reuse it in every report.
- [ ] **1.9 Evidence directory.** `~/workspace/hacker-agent/intel/paypal-evidence/<TEST-ID>/` holding: `request.json`, `response.json`, `state-before.json`, `state-after.json`, `notes.md` per test. Capture PayPal's `debug_id` from every error response — it is the correlation key PayPal's team needs.

---

## 2. Payment state machines (explicit)

Derived from public developer docs (recon §Payment State Machine). Attacker-reachable transitions are marked **[A]**.

### 2.1 Orders v2 — intent=CAPTURE (one-time payment)

```
CREATE  POST /v2/checkout/orders  {intent:"CAPTURE", purchase_units:[{amount, payee?}]}
  │
  ▼
CREATED ──[A] buyer approves via approve-link (HATEOAS "approve")──▶ APPROVED
  │                                                                     │
  │ abandon / never approve                                             │ [A] POST /v2/checkout/orders/{id}/capture
  ▼                                                                     ▼
 (terminal: order expires unapproved)                              COMPLETED ──[A] POST /v2/payments/captures/{id}/refund──▶ REFUNDED
                                                                                                              (full) │
                                                                                                              (partial) ▼
                                                                                                              PARTIALLY_REFUNDED ──[A] further refunds──▶ REFUNDED
```

Key properties to attack: the approval binds (amount, payee, currency) at approve-time; capture must honor the *approved* values, not the *current* order values (see T-3).

### 2.2 Orders v2 — intent=AUTHORIZE (auth/capture split)

```
CREATED ──[A] approve──▶ APPROVED ──[A] POST .../orders/{id}/authorize──▶ authorization object (status CREATED)

Authorization object:
CREATED ──[A] POST /v2/payments/authorizations/{id}/capture {amount?}──▶ CAPTURED | PARTIALLY_CAPTURED
   │            └─(more captures, Σ ≤ authorized)──▶ CAPTURED
   ├──[A] POST .../void──▶ VOIDED  (funds released; terminal for this auth)
   ├──(3 days pass, uncaptured)──▶ EXPIRED ──[A] POST .../reauthorize──▶ CREATED (fresh 3-day window; allowed ≤ day 29)
   ├──(day 29+ with no reauthorize)──▶ terminal, no further capture
   └──(processor)──▶ DENIED | PENDING

Captured funds ──[A] POST /v2/payments/captures/{id}/refund──▶ REFUNDED | PARTIALLY_REFUNDED
```

Invariants under test: Σ captures ≤ authorized amount (T-1); void/expired auths can never be captured or refunded (T-7); reauthorize only inside the 3–29-day window (T-13).

### 2.3 Subscriptions v1 (recurring)

```
Product:  POST /v1/catalogs/products ──▶ product
Plan:     POST /v1/billing/plans {pricing_schemes} ──▶ CREATED ──[A] activate──▶ ACTIVE ⇄ [A] deactivate
Subscription: POST /v1/billing/subscriptions {plan_id}
  APPROVAL_PENDING ──[A] buyer approves──▶ APPROVED ──▶ ACTIVE
  ACTIVE ⇄ [A] suspend / [A] activate ──[A] cancel──▶ CANCELLED ; (billing cycles exhausted)──▶ EXPIRED
  ACTIVE ──[A] POST .../revise {plan/quantity}──▶ APPROVAL_PENDING (buyer must re-approve via link)
  ACTIVE ──[A] PATCH .../subscriptions/{id}──▶ (update; ACTIVE or SUSPENDED only)
```

### 2.4 Payouts v1 (mass disbursement — highest blast radius)

```
POST /v1/payments/payouts
  sender_batch_header: {sender_batch_id  ← caller-chosen idempotency key,
                        recipient_type: EMAIL|PHONE|PAYPAL_ID}
  items[]: {receiver, amount{currency_code, value}, sender_item_id ← per-item idempotency key}

Batch:   PENDING ──▶ PROCESSING ──▶ SUCCESS | DENIED
Item:    PENDING ──▶ SUCCESS | FAILED | UNCLAIMED | RETURNED | ONHOLD | BLOCKED | DENIED | REFUNDED | REVERSED
[A] cancel an UNCLAIMED item ──▶ funds return to sender exactly once
```

### 2.5 Invoicing (secondary)

```
DRAFT ──[A] send──▶ SENT ──[A] pay──▶ PAID | PARTIALLY_PAID ; ──[A] cancel──▶ CANCELLED ; paid──[A] refund──▶ REFUNDED
Merchant setting (opt-in): "block multiple payments per invoice ID" — enforcement seam (T-14).
```

### 2.6 Webhook/IPN trust boundary

PayPal → merchant listener: signed event POSTs. Integrator verifies via
`POST /v1/notifications/verify-webhook-signature` (`transmission_id`, `transmission_time`,
`cert_url`, `auth_algo`, `transmission_sig`, `webhook_id`). Legacy IPN: listener echoes the
message with `cmd=_notify-validate` → `VERIFIED`/`INVALID`. Only PayPal's *own*
signing/verification endpoints are in scope (T-10); merchant-side verification bugs are not.

---

## 3. Test cases — Phase 1: money-movement invariants (run first)

### T-1 — Capture exceeds authorization (maps to H1)
- **Invariant:** Σ captures on one authorization ≤ authorized amount, in the authorized currency. Partial captures may never sum past 100%.
- **Setup:** `merchant-a` app credentials. `buyer` approves.
- **Steps:**
  1. `POST /v2/checkout/orders` `{intent:"AUTHORIZE", purchase_units:[{amount:{currency_code:"USD", value:"10.00"}}]}` → `order_id` (status CREATED). Fresh `PayPal-Request-Id`.
  2. Buyer approves via the `approve` HATEOAS link (sandbox buyer login). Confirm order status APPROVED.
  3. `POST /v2/checkout/orders/{order_id}/authorize` → `authorization_id` (status CREATED).
  4. `POST /v2/payments/authorizations/{authorization_id}/capture` `{amount:{currency_code:"USD", value:"6.00"}}` → expect PARTIALLY_CAPTURED.
  5. `POST /v2/payments/authorizations/{authorization_id}/capture` `{amount:{currency_code:"USD", value:"6.00"}}` → Σ would be 12.00 > 10.00.
  6. Variants (separate authorizations, fresh idempotency keys): capture with `value:"10.01"`; capture with `currency_code:"JPY", value:"100"` (zero-decimal confusion: 100 JPY ≠ 100 USD); partial 6.00 → reauthorize → capture 6.00 again.
- **VULNERABLE:** step 5 returns 2xx and the second capture completes (Σ > authorized), or a currency-mutated capture settles at the wrong value, or reauthorize+recapture double-spends the hold.
- **SECURE:** step 5 returns `4xx` (`AMOUNT_MISMATCH` / `AUTHORIZATION_AMOUNT_EXCEEDED` class) with no funds moved; currency mutation rejected; reauthorized amount still capped at original.
- **Evidence:** both capture responses, `GET /v2/payments/authorizations/{id}` before/after each capture, buyer + merchant sandbox balances, `debug_id`s.
- **Stop rule:** stop at the first over-capture that settles; do not chain further captures. One settled over-capture = complete proof.

### T-2 — Double state transition / idempotency race (maps to H2)
- **Invariant:** each order authorizes/captures/refunds exactly once; `PayPal-Request-Id` is enforced; replaying a transition on a terminal object fails.
- **Setup:** `merchant-a`, `buyer`.
- **Steps:**
  1. Create + approve + capture a $5.00 order (intent=CAPTURE) → COMPLETED. Record capture id.
  2. Replay `POST /v2/checkout/orders/{order_id}/capture` with the *same* `PayPal-Request-Id` → expect idempotent replay (same result, no double charge).
  3. Replay with a *fresh* `PayPal-Request-Id` → expect 4xx (order already COMPLETED).
  4. Race: fire two identical capture requests in parallel (fresh keys each) against a newly APPROVED order; check whether two capture objects exist.
  5. Race the refund: two parallel `POST /v2/payments/captures/{capture_id}/refund` `{amount: full}` → check Σ refunds ≤ capture.
- **VULNERABLE:** two distinct capture ids for one order, or Σ refunds > capture amount, or fresh-key replay re-executes.
- **SECURE:** same-key replay returns the original result; fresh-key replay on terminal object 4xx; parallel races serialize to one execution (second gets idempotent/duplicate error).
- **Evidence:** both parallel responses with timestamps, capture/refund object listings, balances before/after, `debug_id`s.
- **Stop rule:** one demonstrated double-execution is enough; unwind with sandbox refund if needed and note it.

### T-3 — PATCH-after-approval TOCTOU (maps to H3)
- **Invariant:** any amount/payee/currency change after buyer approval must return the order to `PAYER_ACTION_REQUIRED`; capture must settle the *approved* values, never the mutated ones.
- **Setup:** `merchant-a`, `buyer`.
- **Steps:**
  1. `POST /v2/checkout/orders` `{intent:"CAPTURE", purchase_units:[{amount:{currency_code:"USD", value:"1.00"}}]}` → CREATED.
  2. Buyer approves → APPROVED. Record approved amount/payee.
  3. `PATCH /v2/checkout/orders/{order_id}` `[{op:"replace", path:"/purchase_units/@reference_id=='default'/amount", value:{currency_code:"USD", value:"1000.00"}}]` → check status: expect `PAYER_ACTION_REQUIRED`.
  4. Without re-approval, `POST /v2/checkout/orders/{order_id}/capture` → observe: does it 4xx, or capture $1000?
  5. Variants (fresh orders each): PATCH `payee` to `merchant-b`'s email after approval then capture; PATCH `currency_code` USD→JPY after approval then capture; PATCH then immediately capture in a tight loop (race the re-approval flag).
- **VULNERABLE:** capture succeeds at $1000 / to the swapped payee / in the swapped currency without the buyer re-approving; or the order *shows* `PAYER_ACTION_REQUIRED` but capture still executes.
- **SECURE:** PATCH returns the order to `PAYER_ACTION_REQUIRED` and capture attempts 4xx until the buyer re-approves via a fresh approve link; captured values always equal last-approved values.
- **Evidence:** order GET after PATCH (status + amount), capture request/response, webhook `PAYMENT.CAPTURE.COMPLETED` amount, balances. The cosmetic-flag-but-still-captures variant is the critical capture.
- **Stop rule:** stop at first capture of unapproved values. This is the highest-expected-value test in the plan — run it first.

### T-4 — Payout idempotency / double-spend (maps to H4)
- **Invariant:** duplicate `sender_batch_id` / `sender_item_id` never double-pays; cancel of an UNCLAIMED item returns funds exactly once.
- **Setup:** `merchant-a` (sender). Recipient: `buyer`'s sandbox email (or `merchant-b`).
- **Steps:**
  1. `POST /v1/payments/payouts` `{sender_batch_header:{sender_batch_id:"TEST-BATCH-001", recipient_type:"EMAIL"}, items:[{receiver:"<buyer-email>", amount:{currency_code:"USD", value:"5.00"}, sender_item_id:"ITEM-001"}]}` → batch id; poll to SUCCESS.
  2. Replay the identical request (same `sender_batch_id`, same `sender_item_id`) → expect duplicate rejection, no second payment.
  3. Same `sender_batch_id`, *different* `sender_item_id` → expect rejection (batch id already used).
  4. Race: two parallel submissions with identical batch/item ids → exactly one payout must land.
  5. Cancel flow: send payout to an unclaimable address so the item goes UNCLAIMED → cancel it → verify sender balance returns exactly once → replay the cancel.
- **VULNERABLE:** two payouts land for one batch/item id; cancel refunds twice (balance increases by 2×); replayed cancel 2xx instead of 4xx.
- **SECURE:** replays 4xx (`DUPLICATE_BATCH_ID` / `DUPLICATE_ITEM_ID` class); race serializes; cancel is single-execution with exactly-once fund return.
- **Evidence:** both batch responses, `GET /v1/payments/payouts/{batch_id}` item states, sender/recipient balances before/after each step, webhook `PAYOUTS.ITEM.*` events.
- **Stop rule:** one double-pay or double-return = complete proof. Payouts are the highest-blast-radius primitive — keep amounts tiny ($1–5).

---

## 4. Test cases — Phase 2: authorization boundaries

### T-5 — Cross-merchant object access / IDOR (maps to H5)
- **Invariant:** authorization/capture/refund/subscription/order IDs are bound to the creating credential; credential B can never operate on credential A's objects.
- **Setup:** `merchant-a` creates objects; `merchant-b` attempts operations with its own token.
- **Steps:**
  1. A creates order → approves (buyer) → authorizes → `auth_A`.
  2. B: `GET /v2/payments/authorizations/{auth_A}` → expect 403/404.
  3. B: `POST /v2/payments/authorizations/{auth_A}/capture {amount: 1.00}` → expect 403.
  4. B: `POST /v2/payments/authorizations/{auth_A}/void` → expect 403.
  5. Repeat the matrix for: capture ids (B refunds A's capture), subscription ids (B suspends/cancels A's subscription), payout batch ids (B reads A's batch), invoice ids.
- **VULNERABLE:** any 2xx on B's cross-merchant read or state-changing call.
- **SECURE:** consistent 403 (or 404 that doesn't distinguish existence — verify B can't tell A's id exists vs random id).
- **Evidence:** full request/response per cell of the matrix; test that error for "A's real id" vs "random id" is identical (no oracle).
- **Stop rule:** first cross-merchant 2xx on a state-changing call = proof; stop, do not escalate (no refunding A's real objects with B).

### T-6 — Token-type confusion (maps to H6)
- **Invariant:** each endpoint accepts only its designed token/object type (order tokens ≠ billing-agreement tokens ≠ subscription ids).
- **Setup:** `merchant-a`, `buyer`.
- **Steps:**
  1. Create a billing agreement / subscription → obtain its approval token/id.
  2. Feed the subscription id where an order id is expected (`POST /v2/checkout/orders/{subscription_id}/capture`).
  3. Feed an order id to subscription endpoints (`POST /v1/billing/subscriptions/{order_id}/cancel`).
  4. On the buyer approval return URL, swap `token=` to a different object type's token and complete the flow.
  5. Feed a `ba_token` into checkout return-url handling and vice versa.
- **VULNERABLE:** an endpoint acts on the wrong object type (e.g. capture executes against a subscription id, or a billing-agreement token approves an order).
- **SECURE:** 4xx `RESOURCE_NOT_FOUND` / type-validation errors on every mismatch; return-URL token binding verified server-side.
- **Evidence:** request/response per swap; object states before/after proving nothing moved.
- **Stop rule:** first cross-type state change = proof.

### T-7 — Refund invariants (maps to H7)
- **Invariant:** refund ≤ capture amount; Σ partial refunds ≤ capture; no refund on VOIDED/EXPIRED authorizations or uncaptured orders.
- **Setup:** `merchant-a`, `buyer`.
- **Steps:**
  1. Capture $10.00 → `POST /v2/payments/captures/{id}/refund {amount: 10.01}` → expect 4xx.
  2. Partial refund $6.00 → partial refund $6.00 → expect second to 4xx (Σ=12 > 10).
  3. Refund a capture, then void the parent authorization, then attempt refund again → expect 4xx.
  4. Attempt `POST /v2/payments/captures/{id}/refund` against an *authorization* id (type swap with T-6 flavor).
  5. Race two full refunds in parallel (T-2 variant scoped to refunds).
- **VULNERABLE:** over-refund settles; Σ partials exceed capture; refund executes on voided/expired auth.
- **SECURE:** 4xx on every over-refund; race serializes to one refund.
- **Evidence:** refund responses, capture object state, balances, `debug_id`s.

### T-8 — Subscription lifecycle authorization (maps to H8)
- **Invariant:** only the owning merchant can suspend/activate/cancel/revise/capture; plan pricing changes never silently alter ACTIVE subscriptions; revise requires buyer re-approval.
- **Setup:** `merchant-a` owns product+plan+subscription; `merchant-b` attacks; `buyer` approves.
- **Steps:**
  1. A: create product → plan ($10/mo) → subscription → buyer approves → ACTIVE.
  2. B: `POST /v1/billing/subscriptions/{sub_A}/suspend`, `/cancel`, `/revise` → expect 403.
  3. A: `POST /v1/billing/subscriptions/{sub_A}/revise {plan_id: <plan $100/mo>}` → expect `APPROVAL_PENDING` + approve link; capture/activate the revised subscription *without* buyer re-approval → must fail.
  4. A: update the plan's pricing scheme while the subscription is ACTIVE → verify the ACTIVE subscription's next billing does not silently adopt the new price (check via subscription GET + webhook `BILLING.SUBSCRIPTION.UPDATED`).
  5. B: `POST /v1/billing/subscriptions/{sub_A}/capture` (authorized-payment capture) → expect 403.
- **VULNERABLE:** B's lifecycle calls 2xx; revise takes effect without re-approval; plan price change silently reprices ACTIVE subscribers.
- **SECURE:** 403 on cross-merchant calls; revise parks at re-approval; plan changes apply only to new subscriptions.
- **Evidence:** subscription GETs before/after, revise response + approval-link presence, webhook event log.

---

## 5. Test cases — Phase 3: authentication & trust boundaries

### T-9 — 2FA / step-up fallback parameter handling (maps to H9)
- **Invariant:** every auth step validates server-side; absent/empty/duplicated security-challenge parameters fail closed; steps cannot be reordered or replayed across sessions.
- **Setup:** sandbox buyer account with 2FA/security-challenge enabled (configure in sandbox account security settings).
- **Steps:**
  1. Begin a step-up/security-challenge flow; intercept the challenge-response POST.
  2. Omit the challenge-answer field entirely → must fail.
  3. Send it empty / whitespace → must fail.
  4. Duplicate the field with two different values → must fail (or deterministically take one — record which).
  5. Submit steps out of order (answer step 2 before step 1).
  6. Complete the flow once, then replay the exact successful response body in a fresh session → must fail.
- **VULNERABLE:** any omission/empty/reorder/replay yields an authenticated/step-passed response (the Hoggard class: missing field treated as correct).
- **SECURE:** all malformed variants 4xx; replay rejected (single-use challenge nonces).
- **Evidence:** full request/response per variant; session state after each (authenticated? step passed?).
- **Note:** this touches authentication ceremony — keep to the sandbox buyer account only; never probe production login.

### T-10 — Webhook/IPN verification endpoint robustness (maps to H10)
- **Invariant:** `verify-webhook-signature` genuinely validates the cert chain and `transmission_time` freshness; IPN `_notify-validate` cannot be satisfied by crafted messages.
- **Setup:** `merchant-a` app with webhook registered; listener from §1.6.
- **Steps:**
  1. Capture a real sandbox webhook; replay its exact body+headers to *your own* listener (baseline: your listener accepts it — expected, it's your endpoint).
  2. Call `POST /v1/notifications/verify-webhook-signature` with the real transmission fields but `webhook_id` of merchant-b's webhook → expect INVALID/false.
  3. Same call with `transmission_time` backdated 48h → expect rejection (stale).
  4. Replay an old `transmission_id` for a new event → expect rejection.
  5. Tamper one byte of the event body, keep the original `transmission_sig` → expect INVALID.
  6. IPN: craft an IPN-style message for a payment that never happened; POST to your listener with `cmd=_notify-validate` to `ipnpb.sandbox.paypal.com` → expect INVALID.
- **VULNERABLE:** verification returns true on wrong webhook_id / stale time / replayed id / tampered body.
- **SECURE:** false/INVALID on every tamper; freshness window enforced.
- **Evidence:** verification request/response pairs; note the exact freshness window if discoverable (don't brute-force it — 2–3 samples max).
- **Scope guard:** PayPal's own verification endpoints only. Do not test a merchant's listener.

### T-11 — OAuth scope / token binding (maps to H11)
- **Invariant:** tokens are bound to the issuing app, its scopes, and the principal; rotated secrets invalidate old tokens; a token from app A never authorizes app B's objects.
- **Setup:** both business apps.
- **Steps:**
  1. Mint token with app A's credentials → call a merchant-b-owned object read → expect 403.
  2. Request `client_credentials` with a restricted-scope app (if the dashboard allows scope-limited apps) → attempt an out-of-scope call → expect `insufficient_scope`.
  3. Rotate app A's secret in the dashboard → immediately use the old token → expect rejection (record how fast: immediate vs grace window).
  4. Use app A's token against `merchant-b`'s webhook-verification and payout endpoints.
- **VULNERABLE:** cross-app authorization succeeds; old tokens survive rotation indefinitely; scope field ignored.
- **SECURE:** 401/403 with clear `invalid_token`/`insufficient_scope`; rotation kills tokens promptly.
- **Evidence:** token mint responses (redact the token itself in notes; keep a local hash for correlation), call responses, rotation timestamps.

### T-12 — Currency invariant (maps to H12)
- **Invariant:** `currency_code` is immutable from create→approve→capture; zero-decimal currencies (JPY, HUF, TWD) are never confused with two-decimal ones server-side.
- **Setup:** `merchant-a`, `buyer`.
- **Steps:**
  1. Create order USD 10.00 → approve → PATCH currency to JPY → capture → expect 4xx or capture still settles USD 10.00 (record which; only "settles ¥10 as $10 value" is vulnerable).
  2. Create order `JPY value:"100"` (¥100) → capture → verify settled amount is ¥100, not $100.00.
  3. Payout batch mixing `USD 1.00` and `JPY 100` items → verify each settles in its own currency at correct magnitude.
  4. Refund a JPY capture with a USD-denominated refund body → expect rejection.
- **VULNERABLE:** currency mutation changes settled value; zero-decimal amounts interpreted at two-decimal magnitude (100 → 100.00 in the wrong currency).
- **SECURE:** mutation rejected; magnitudes exact per currency's decimal definition.
- **Evidence:** order/capture/payout objects showing currency + value at each stage.

---

## 6. Test cases — Phase 4: cheap checks

### T-13 — Reauthorize window edges (maps to H13)
- **Invariant:** no reauthorize after day 29; no capture of EXPIRED authorizations.
- **Steps:** authorize $5 → void it → attempt `reauthorize` → expect 4xx; attempt `capture` on the VOIDED auth → expect 4xx. (True 29-day edges can't be tested in one session — note as a calendar follow-up, not a blocker.)
- **VULNERABLE:** reauthorize/capture succeeds on VOIDED or EXPIRED auth.
- **SECURE:** 4xx with terminal-state error codes.

### T-14 — invoice_id dedup race (maps to H14)
- **Invariant:** with "block multiple payments per invoice ID" enabled, two simultaneous payments carrying the same `invoice_id` cannot both complete.
- **Steps:** enable the setting on merchant-a → fire two parallel `POST /v2/checkout/orders` with identical `invoice_id` → approve both → capture both → check how many COMPLETED.
- **VULNERABLE:** both complete.
- **SECURE:** second create/capture rejected as duplicate.
- **Evidence:** both order objects + capture results.

### T-15 — Framing of money-moving endpoints (maps to H15)
- **Invariant:** payment/approval endpoints are not frameable (X-Frame-Options DENY/SAMEORIGIN or CSP `frame-ancestors`).
- **Steps:** GET the checkout approve URL, `/agreements/approve`-class URLs, payout-approval and dispute URLs → record `X-Frame-Options` and `Content-Security-Policy` `frame-ancestors`. Attempt to iframe the approve page from your listener origin (sandbox buyer session) and observe.
- **VULNERABLE:** missing/overly broad framing protection on an endpoint that moves money on click (the h4x0r_dz class — needs a chained token-acceptance issue to be reportable; framing alone is weak).
- **SECURE:** DENY/SAMEORIGIN or restrictive `frame-ancestors` everywhere money moves.
- **Evidence:** response headers per endpoint; note: report only if chained with a token/state issue.

---

## 7. Execution order (by expected value)

| Order | Test | Why first |
|---|---|---|
| 1 | T-3 PATCH-after-approval TOCTOU | Direct money-movement bug class with real precedent (PayPal + WooCommerce); single-session test |
| 2 | T-1 Capture exceeds authorization | Core ledger invariant; partial-capture + currency variants are cheap |
| 3 | T-4 Payout idempotency | Highest blast radius primitive; tiny amounts keep it safe |
| 4 | T-2 Double state transition / race | $15k precedent class; parallel-request tooling reusable for T-7/T-14 |
| 5 | T-5 Cross-merchant IDOR matrix | Authorization boundary; two credential sets already in hand |
| 6 | T-6 Token-type confusion | Historical PayPal-specific class (h4x0r_dz) |
| 7 | T-7 Refund invariants | Ledger invariant; shares setup with T-1 |
| 8 | T-8 Subscription lifecycle | Cross-merchant + revise-without-approval |
| 9 | T-12 Currency invariant | Cheap variants piggybacked on T-1/T-3 orders |
| 10 | T-11 OAuth token binding | Session/principal binding (Birsan class) |
| 11 | T-9 2FA fallback params | Auth ceremony; sandbox-only |
| 12 | T-10 Webhook verification | PayPal's own endpoints only |
| 13 | T-13 Reauthorize edges | Terminal-state enforcement |
| 14 | T-14 invoice_id dedup race | Needs the opt-in setting; quick |
| 15 | T-15 Framing headers | Weakest alone; only report chained |

Parallelization: Phase 1 (T-1..T-4) and Phase 2 (T-5..T-8) are independent — they can run concurrently on separate credential sets / operators. Within a phase, run in table order; each test's setup (approved orders, subscriptions) is reusable by later tests in the same phase.

## 8. Evidence & reporting standard

Per methodology §7, every candidate finding needs:
1. **Minimal reproduction** — the fewest requests that demonstrate the violation (strip variants that don't matter).
2. **Baseline** — the same flow executed the "correct" way, showing what secure behavior looks like.
3. **Boundary proof** — the exact security invariant violated, in one sentence.
4. **Impact statement** — who loses money / what an attacker gains per attempt, at what scale. PayPal explicitly rewards demonstrated impact over clever-but-impactless PoCs.
5. **Artifacts** — `request.json` / `response.json` / `state-before.json` / `state-after.json` / `notes.md` per test ID, including `debug_id`s and the test IP.

## 9. Production-confirmation policy

Sandbox-only issues don't pay (Braintree excepted at 50%). If a sandbox finding is confirmed:
- First, check whether the vulnerable code path is shared with production (same API version, same documented behavior) — document the reasoning.
- Any production touch must move **no real money**: create-but-don't-capture orders, void test authorizations, use $1 amounts with immediate void/refund where the flow requires settlement. When in doubt, ask the program (HackerOne) before touching production.
- Never test against real merchants, real buyers, or any object you don't own.

## 10. Explicitly out of scope — do not spend time

Username enumeration · open redirect (except immediate-redirect/data-loss) · merchant-integration bugs · scanner output · missing-headers/TLS trivia · self-XSS · login/logout CSRF · DoS on production · anything involving real funds or real users.
