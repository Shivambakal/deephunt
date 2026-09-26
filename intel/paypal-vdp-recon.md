# PayPal HackerOne — Passive Reconnaissance Report

**Date:** 2026-09-26 · **Type:** Passive only — no testing, no logins, no requests to PayPal.
**Purpose:** Preparation for precise authenticated hunting later.
**Methodology:** `~/workspace/hacker-agent/deep-vuln-methodology.md` §§1, 2, 5.

> Note: PayPal's HackerOne program is a **paid** bounty program ($50–$30,000),
> not a pure VDP. Do not publicly disclose findings without PayPal's prior
> written approval (program terms).

---

## [SCOPE SUMMARY]

Source: live program page https://hackerone.com/paypal (read 2026-09-26).

### In-scope brands
| Brand | Asset |
|---|---|
| PayPal | www.paypal.com |
| Venmo | www.venmo.com |
| Xoom | www.xoom.com |
| Braintree Payments | www.braintreepayments.com |
| Swift Financial / Loanbuilder | my.loanbuilder.com |
| Hyperwallet | www.hyperwallet.com |

### Explicitly out of scope
- **Brands:** Chargehound, Honey, Paidy, Simility, Zettle.
- **Assets/products:** www.paypal-support.com, braintree-web-drop-in SDK, Payflow Gateway (Payflow Pro, Payflow Link, PayPal Manager + pilot/test endpoints).
- **Vuln classes (will be closed):** username enumeration on customer-facing systems, scanner output, open redirect (except: immediate redirect from a PayPal URL, or redirect causing sensitive-data loss), self-XSS, login/logout CSRF, content spoofing without external link/JS, infra issues with no demonstrated impact, sandbox-only issues (except Braintree), **PayPal merchant integrations**, MCP dynamic-client-registration issues, reports limited to secondary business accounts with impact only on the parent account.

### Bounty table (from live page)
| Severity | Reward |
|---|---|
| Critical | $20,000 – $30,000 |
| High | $10,000 – $20,000 |
| Medium | $1,000 – $10,000 |
| Low | $50 – $1,000 |
| Subdomain takeover | $200 / $200 / $3,000 / $5,000 (Low/Med/High/Crit) |
| XSS (set payout) | $50–500 / $500–3k / $3k–6k / $6k |

Modifiers: Braintree **Sandbox** findings pay **50%**; `www.paypal-*.com` partner sites pay **10%**; unsupported old SDKs pay **10%**. Rewards are impact-based, not CVSS-based. PayPal's team explicitly values **chained low-risk issues with demonstrated impact** and clear impact statements over clever-but-impactless PoCs (https://www.HackerOne.com/blog/program-insights-paypal-security-team).

### Mandatory test hygiene (for the later active phase)
- Register test accounts as `<username>+pp@wearehackerone.com`.
- Send header `X-PP-BB: HackerOne-<username>` on all test traffic.
- Include the test IP address in the report (private, for activity review).
- RCE PoC limits: benign commands only (`whoami`, `hostname`, `id`, `pwd`); read via `cat /proc/1/maps`, write via `touch /root/<username>`; no webshells, no persistence, no data beyond proof.
- **DoS: sandbox only, never production.** No automated scanning that degrades availability. Theoretical production-DoS reports accepted with reasoning (no PoC required).
- Delete any inadvertently accessed data after report closure.

---

## [DISCLOSED-REPORT PATTERNS]

What has historically paid at PayPal, and the recurring root-cause patterns.
All references are public writeups/news coverage, not HackerOne disclosed
reports (PayPal requires written approval for disclosure, so few H1 reports
are public).

### 1. Auth-token / session logic flaws → credential exposure — $15,300 (High, CVSS 8.0)
- **Researcher:** Alex Birsan (Nov 2019). Writeup: https://medium.com/@alex.birsan/the-bug-that-exposed-your-paypal-password-539fc2896da9
- **Root cause (chain):** (a) XSSI leaked session tokens from a JS file used by the reCAPTCHA implementation; (b) the reCAPTCHA token was **not bound to the session** — any valid token, e.g. from a captcha-solving service, was accepted; (c) `/auth/validatecaptcha` then returned the victim's **plaintext credentials** server-side.
- **Pattern:** security tokens not bound to the principal/session they protect + sensitive data returned to whoever presents the tokens. Also affected unauthenticated checkout pages → plaintext card data.
- **Lesson for hunting:** any PayPal flow where a token stands in for authentication — check whether the token is bound to session, principal, and intended operation.

### 2. CSRF-auth bypass → full account takeover — $10,000
- **Researcher:** Yasser H. Ali. Coverage: https://www.itnews.com.au/news/paypal-patches-account-hijacking-flaw-398496
- **Root cause:** the CSRF/auth token was **reusable per username/email** — intercepting the pre-login POST's auth token let an attacker impersonate the user (single malicious link + victim's email). Post-takeover: change payment methods, addresses, security questions, add privileged business-account users.
- **Pattern:** anti-CSRF token doubles as an authentication bearer; token not single-use / not bound to the login ceremony.

### 3. 2FA fallback trusts client-controlled state — bounty paid (amount undisclosed)
- **Researcher:** Henry Hoggard. Coverage: https://www.silicon.co.uk/security/researcher-breaches-paypal-two-factor-authentication-199458
- **Root cause:** when SMS 2FA was unavailable, PayPal fell back to security questions; **removing `securityQuestion0`/`securityQuestion1` from the POST body** made the server accept any answer. Missing field ⇒ treated as correct.
- **Pattern (methodology §5):** server treats *absence* of a client-controlled parameter as success. Prime differential probe: omit, empty, and duplicate security-step parameters.

### 4. Cross-feature: account linking bypasses 2FA — no bounty (disclosed after no-fix)
- **Researcher:** Joshua Rogers (2014). Coverage: https://cioafrica.co/paypals-two-factor-authentication-is-easily-beaten-researcher-says/
- **Root cause:** linking eBay↔PayPal accounts set a cookie that made PayPal treat the session as authenticated **without the 2FA step ever executing**.
- **Pattern (methodology §3):** authentication + account-linking interaction — a second feature's session artifact satisfies the first feature's auth invariant.

### 5. Token-type confusion + missing frame protection → one-click money theft — reported Oct 2021, publicly claimed unpatched at time of writing, no bounty paid
- **Researcher:** h4x0r_dz. Coverage: http://thehackernews.com/2022/05/paypal-pays-hacker-200000-for.html
- **Root cause:** `www.paypal.com/agreements/approve` was designed to accept only `billingAgreementToken`, but **accepted other token types**, and the endpoint was frameable → clickjacking that moves real money / subscribes services (Steam balance, Netflix) on one victim click.
- **Pattern:** endpoint accepts a *different object type's token* than designed (object substitution, §5) × missing X-Frame-Options on a money-moving endpoint.

### 6. Race condition in payment processing — $15,000 (secondhand)
- Source: community knowledge base, not a primary report — https://github.com/gabson0x/bountyforge/blob/HEAD/skills/bug-bounty/knowledge.md ("PayPal | Race in payment processing | Double-submit race | $15,000").
- **Pattern:** TOCTOU on financial operations (capture/refund/payout double-submit). Treat as a lead, not a confirmed precedent.

### Meta-patterns across all six
1. **Money moves on tokens** — every high-payout bug is about a token/parameter that the server fails to bind to (session, principal, operation, object type).
2. **Fallback paths are weaker than primary paths** (2FA fallback, reCAPTCHA fallback).
3. **Cross-feature interactions** (eBay linking × PayPal auth; agreements × checkout tokens) beat single-endpoint bugs.
4. PayPal pays for **demonstrated financial impact**; merchant-integration bugs are explicitly out of scope, so the target must be PayPal's own systems.

---

## [PAYMENT STATE MACHINE]

Derived from public developer documentation (no authenticated access).
API hosts: `https://api-m.paypal.com` (live), `https://api-m.sandbox.paypal.com` (sandbox). Auth: OAuth2 client credentials, `POST /v1/oauth2/token`. Idempotency: `PayPal-Request-Id` header on supported POSTs.

### A. Orders v2 — one-time payments
Refs: https://developer.paypal.com/docs/api/orders/v2/, https://developer.paypal.com/docs/api/payments/v2/

```
CREATE  POST /v2/checkout/orders   intent=CAPTURE|AUTHORIZE
  → CREATED ──(buyer approves via approve link)──→ APPROVED
  → (intent=CAPTURE)  POST /v2/checkout/orders/{id}/capture      → COMPLETED
  → (intent=AUTHORIZE) POST /v2/checkout/orders/{id}/authorize   → authorization object
```

**Authorization object lifecycle** (`/v2/payments/authorizations/{id}`):
```
CREATED ──capture──→ CAPTURED | PARTIALLY_CAPTURED ──(more captures)──→ CAPTURED
   ├──void──→ VOIDED
   ├──(3 days, uncaptured)──→ EXPIRED ──reauthorize──→ CREATED (new 3-day window, up to day 29)
   └──(day 29+)──→ terminal, cannot capture
DENIED / PENDING are processor-driven states.
```
- `POST .../authorizations/{id}/capture` — full or **partial** capture (amount in body).
- `POST .../authorizations/{id}/reauthorize` — extends validity; only within 3–29 day window.
- `POST .../authorizations/{id}/void` — releases held funds.
- `POST .../captures/{id}/refund` — full or partial refund of a capture.
- `PATCH /v2/checkout/orders/{id}` — update amount/shipping/items **after** buyer approval; documented behavior forces `PAYER_ACTION_REQUIRED` (buyer must re-approve) when the amount changes — this is the seam to probe.
- Zero-decimal currencies: HUF, JPY, TWD (amount `"100"` = 100 units, not 100.00). All others are 2-decimal.

### B. Subscriptions v1 — recurring billing
Ref: https://developer.paypal.com/docs/api/subscriptions/v1 , https://developer.paypal.com/api/subscriptions/v1

```
Product  POST /v1/catalogs/products
Plan     POST /v1/billing/plans  → CREATED ──activate──→ ACTIVE (⇄ deactivate)
Subscription  POST /v1/billing/subscriptions  (against ACTIVE plan)
  → APPROVAL_PENDING ──(buyer approves)──→ APPROVED ──→ ACTIVE
  ACTIVE ⇄ SUSPENDED (suspend/activate) ──cancel──→ CANCELLED ; ──(cycles end)──→ EXPIRED
```
- `PATCH /v1/billing/subscriptions/{id}` — update (ACTIVE or SUSPENDED only).
- `POST .../revise` — plan/quantity change; buyer must re-approve via returned link.
- `POST .../capture` — capture an authorized subscription payment.
- Webhooks: `BILLING.SUBSCRIPTION.{CREATED,ACTIVATED,UPDATED,EXPIRED,CANCELLED,SUSPENDED,PAYMENT.FAILED}`, `PAYMENT.SALE.COMPLETED`.

### C. Payouts v1 — mass disbursement
Ref: https://developer.paypal.com/api/payments.payouts-batch/v1/payouts-get

```
POST /v1/payments/payouts
  sender_batch_header: sender_batch_id (caller-chosen idempotency), recipient_type EMAIL|PHONE|PAYPAL_ID
  items[]: receiver, amount{currency,value}, sender_item_id (per-item idempotency), note
Batch: PENDING → PROCESSING → SUCCESS | DENIED
Per item: SUCCESS | FAILED | UNCLAIMED | RETURNED | ONHOLD | BLOCKED | DENIED | REFUNDED | REVERSED
GET /v1/payments/payouts/{id} (+ ?fields=, page, page_size) ; cancel unclaimed item
```
- Payouts move money **out of the sender's balance** to arbitrary recipients — the highest-blast-radius primitive in the API set.

### D. Webhooks / IPN — async trust boundary
- Webhooks: app registers URL in developer dashboard; events include `PAYMENT.CAPTURE.{COMPLETED,DENIED,REFUNDED,REVERSED}`, `BILLING.SUBSCRIPTION.*`, `INVOICING.INVOICE.PAID`, `PAYOUTS.ITEM.*`, `MERCHANT.ONBOARDING.COMPLETED`, `CUSTOMER.DISPUTE.*`.
- Verification is the **integrator's** job: `POST /v1/notifications/verify-webhook-signature` with `transmission_id`, `transmission_time`, `cert_url`, `auth_algo`, `transmission_sig`, `webhook_id`. (Merchant-side verification failures are out of scope; PayPal's *own* signing/verification endpoints are in scope.)
- IPN (legacy): listener POSTs the message back with `cmd=_notify-validate` to `ipnpb.paypal.com/cgi-bin/webscr` → `VERIFIED`/`INVALID`.

### E. Invoicing (secondary surface)
- `INVOICING.INVOICE.PAID` webhooks; invoice state machine DRAFT → SENT → PAID / PARTIALLY_PAID / CANCELLED / REFUNDED. `invoice_id` dedup is an **opt-in** merchant setting ("block multiple payments per invoice ID") — the enforcement seam.

---

## [HYPOTHESES] — ranked by expected value

Ranked by (bounty precedent × blast radius × how untested the seam is).
All are **unproven** — they are targets for the authenticated phase, each
requiring a minimal safe reproduction with two sandbox test accounts.

### Tier 1 — money-movement invariants
1. **Capture exceeds authorization (H1).** Invariant: Σ captures ≤ authorized amount, in the authorized currency. Probe: partial captures summing past 100%, partial capture + reauthorize + capture again, capture with mutated `amount`/`currency_code`, zero-decimal currency confusion (JPY `value:"100"` vs USD `"1.00"`). Precedent class: race/payment-manipulation ($15k race; Birsan token-binding).
2. **Double state transition (H2).** Invariant: each order authorizes/captures exactly once; `PayPal-Request-Id` idempotency is enforced. Probe: double-submit capture/authorize/refund in parallel (race), replay with same vs fresh idempotency keys, capture on already-COMPLETED order.
3. **PATCH-after-approval TOCTOU (H3).** Invariant: any amount/payee change after buyer approval must return the order to `PAYER_ACTION_REQUIRED`. Probe: approve $1 → PATCH amount to $1000 / swap `payee` / change `currency_code` → capture; check whether approval is genuinely re-required or only cosmetically flagged. (The WooCommerce `PAYER_ACTION_REQUIRED` incident shows this seam is load-bearing and fragile.)
4. **Payout idempotency / double-spend (H4).** Invariant: duplicate `sender_batch_id` / `sender_item_id` never double-pays; cancel of UNCLAIMED returns funds exactly once. Probe: replay batch with same IDs, race two identical batches, cancel-then-replay. Highest blast radius primitive in the API set.

### Tier 2 — authorization boundaries
5. **Cross-merchant object access (H5).** Invariant: authorization/capture/refund/subscription IDs are bound to the creating credential. Probe: credential A creates, credential B reads/captures/refunds/cancels it (IDOR across `/v2/payments/*`, `/v1/billing/subscriptions/*`).
6. **Token-type confusion (H6).** Invariant (from h4x0r_dz): each endpoint accepts only its designed token type. Probe: feed `billingAgreementToken` where an order token is expected and vice versa; feed subscription IDs to order endpoints; `ba_token` handling on return URLs.
7. **Refund invariants (H7).** Invariant: refund ≤ capture amount; no refund on VOIDED/EXPIRED authorizations; partial refunds sum ≤ capture. Probe: over-refund, refund-then-refund race, refund of voided auth.
8. **Subscription lifecycle authz (H8).** Invariant: only the owning merchant can suspend/cancel/revise/capture; plan pricing changes don't silently alter ACTIVE subscriptions. Probe: cross-account revise/cancel; `update-pricing-schemes` on a plan with live subscribers; revise-quantity without buyer re-approval.

### Tier 3 — authentication & trust boundaries
9. **2FA / step-up fallback parameter handling (H9).** Invariant (from Hoggard): every auth step validates server-side; absent/empty/duplicate step parameters must fail closed. Probe: omit, blank, and duplicate security-challenge fields; reorder steps; replay a completed step's response in a fresh session.
10. **Webhook/IPN spoofing against PayPal's own verifiers (H10).** Invariant: `verify-webhook-signature` genuinely validates the cert chain and `transmission_time` freshness; IPN `_notify-validate` can't be satisfied with a crafted-but-genuine-looking message. Probe: expired cert, wrong `webhook_id`, replayed `transmission_id`, clock-skewed `transmission_time`. (Merchant-side verification bugs are out of scope — this is PayPal's own endpoint only.)
11. **OAuth scope / token binding (H11).** Invariant (from Birsan): tokens bound to session + principal + operation. Probe: scope escalation in `client_credentials`, token reuse across apps, token accepted after secret rotation.
12. **Currency invariant (H12).** Invariant: `currency_code` immutable from create→approve→capture; zero-decimal vs two-decimal never confused server-side. Probe: create in USD, approve, PATCH currency to JPY before capture; multi-currency payout items.

### Tier 4 — lower expected value, cheap to check
13. **Reauthorize window (H13).** Invariant: no reauthorize after day 29; no capture of EXPIRED auth. Probe: backdated/edge-of-window reauthorize, capture immediately after expiry boundary.
14. **invoice_id dedup TOCTOU (H14).** Invariant: with "block duplicates" enabled, two simultaneous payments with the same `invoice_id` can't both complete. Probe: parallel creates with identical `invoice_id`.
15. **Framing of money-moving endpoints (H15).** Invariant (from h4x0r_dz): payment/approval endpoints must not be frameable. Probe: `X-Frame-Options`/CSP `frame-ancestors` on checkout, agreements/approve, payout-approval, and dispute flows.

### Explicitly NOT hypotheses (out of scope — do not spend time)
- Username enumeration (explicitly excluded from bounty).
- Open redirect (except immediate-redirect or data-loss cases).
- Bugs in a merchant's PayPal integration (report to merchant, not the program).
- Scanner output / missing headers / TLS trivia.

---

## Readiness checklist for the authenticated phase
- [ ] Two sandbox business accounts + one buyer account via developer.paypal.com (sandbox balances are play money — safe for invariant probes).
- [ ] Test accounts named `<username>+pp@wearehackerone.com` per program terms.
- [ ] `X-PP-BB: HackerOne-<username>` header on all traffic; log test IP for the report.
- [ ] Start with Tier 1 on **sandbox**; only reproduce a confirmed sandbox finding against production if the program terms require it (Braintree sandbox findings pay 50% — acceptable).
- [ ] Never touch real money, real merchants, or other users' objects; stop at minimum safe proof.
