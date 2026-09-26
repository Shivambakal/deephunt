# FDJ United — Manual Test Playbooks (NO SCANNERS)

**Program:** FDJ United — Online Betting and Gaming (YesWeHack)
**Bounty (Critical tier):** Low €150 / Medium €1,000 / High €5,000 / Critical €15,000
**Bounty (High tier):** €50 / €150 / €800 / €2,500
**Hard rules:** own test accounts ONLY · NO automated scanners / heavy traffic · no DoS · no social engineering · no touching end users · no disclosure without written permission · same vuln across brands = reported once as systemic
**Explicit focus areas:** RCE, SQLi, PCI-environment access, account takeover (with/without user interaction), stored/blind XSS, subdomain takeover on main brands, CSRF on sensitive actions
**In-scope brands:** unibet.com (+ .it/.se/.co.uk/.be/.nl/.dk/.ro/.ee/.ie/.com.au/.mt), mariacasino.com (+ .se/.ee/.dk), 32red.com, bingo.com (+ se/fi/uk), ottokasino.com, stor spiller/storspelare, casinohuone.com, kolikkopelit.com, vladcazino.ro, pci.kindredgroup.com, mobile apps. `/blog/` endpoints = High tier.

## Account setup (do this first)
1. Create TWO test accounts per brand you touch (A: `progamee1414@gmail.com`, B: `shivambakal@gmail.com`) — two accounts are mandatory for every IDOR/priv-esc test.
2. Verify emails, complete KYC-lite if required. Never use real identity documents beyond what's needed for the test account; never touch another user's account.
3. Note your player IDs / account UUIDs from profile pages and API responses — these are your IDOR swap material.

## Rate discipline
- Manual pace: click through flows like a user. Burp **Repeater only** — no Intruder, no active scan, no spider.
- If a page loads slowly or you hit a CAPTCHA/429, stop that flow for the hour. Heavy traffic = ban.
- One tab, one flow at a time. Parallel-tab tricks are only for the checkout state-mutation tests (2 tabs max).

## What NOT to touch
- Any other player's account, balance, betslip, or PII. If an IDOR returns someone else's data, screenshot + stop + report.
- Real-money flows beyond the minimum: use minimum-stake bets / minimum deposits; never complete an underpriced or manipulated transaction.
- `pci.kindredgroup.com` beyond read-only probing of your own session — PCI env is high-value but also high-scrutiny; report access, don't escalate.
- Live customer support chats as an attack vector (no social engineering).

---

## TARGET 1 — payment.mariacasino.com (deposit / cashier flow)

This is the money page. Betting cashiers are classic business-logic territory.

**Walk the flow:**
1. Log in as Account A on www.mariacasino.com, navigate to cashier/deposit (`payment.mariacasino.com`).
2. Start a minimum deposit. In Repeater, capture the full request sequence: amount selection → payment-method choice → confirmation → callback/return URL.
3. Record every amount-bearing field: `amount`, `currency`, `bonus_code`, `promo_id`, `deposit_id`, `transaction_id`.

**Tamper (one at a time, never completing):**
- **Amount mismatch:** change `amount=10` to `amount=1` at the confirmation step — does the server re-quote or trust the client? The signal is the SERVER returning a lower total. Document, don't pay.
- **Currency swap:** deposit in a weak currency param (`currency=USD` → `currency=TRY`/`VND`) mid-flow; check if the credited amount follows the tampered currency.
- **Parameter pollution:** duplicate `amount` fields (`amount=10&amount=1`) — which one wins server-side?
- **Callback replay:** capture the payment-gateway return/callback URL; replay it with modified `status=success` / `transaction_id`. If the account credits without a real payment → critical. Do NOT loop it.
- **Bonus/coupon stacking:** apply a deposit bonus, remove it mid-flow, re-apply; check for double-credit or bonus applied to a different amount.
- **Negative/zero/decimal:** `amount=0`, `amount=-10`, `amount=10.999` — watch for credit of 0-cost or negative-balance states.

**What a win looks like:** server credits a different amount than paid, bonus double-applies, or callback replay fabricates a deposit. Minimum-deposit stakes only; stop before any real charge settles.

## TARGET 2 — support-qa1.mariacasino.com (QA environment)

QA boxes are where debug flags, test credentials, and disabled auth live.

**Walk the flow:**
1. Open the host directly. Note: does it resolve to a login page, an open dashboard, or a copy of the support portal?
2. Compare every page against production `support.mariacasino.com` — QA often lags on security headers/patches.
3. Check for: `/admin`, `/debug`, `/console`, `?debug=true`, test-user listings, exposed stack traces (trigger a 404/500), `robots.txt`, `/.git/HEAD`.

**Tamper/probe (read-only):**
- **Default/test creds:** try `admin/admin`, `test/test`, `qa/qa` ONCE each — one attempt per pair, never brute-force.
- **Registration on QA:** if QA allows self-registration, register and check whether the QA account has elevated roles (agent/admin flags) or sees other tenants' tickets.
- **Ticket IDOR:** open a support ticket as Account A; as Account B, try `ticket_id` ±1, and your own ticket UUID swapped. QA ticket systems frequently lack the prod authz checks.
- **Attachment access:** upload an attachment to your ticket, then fetch its direct URL logged-out. If it serves without auth → stored file exposure.
- **Error verbosity:** force errors (bad ticket ID, malformed params) and read stack traces for internal hostnames, framework versions, SQL snippets.

**What a win looks like:** unauthenticated access to QA tickets/PII, default creds working, or debug endpoints exposing internal config. Screenshot everything; QA findings still count if the flaw mirrors prod.

## TARGET 3 — evolivecasino.bingo.com (live casino)

Live-dealer games have real-time state — game rounds, balances, and bet placement race each other.

**Walk the flow:**
1. Log in as Account A, open a live table (minimum-stake table). Open browser devtools → Network → WS/XHR; watch the game-round lifecycle: `round_id`, `bet_window_open/close`, `balance` updates.
2. Place a minimum bet; capture the bet-placement request and the round-status polling.

**Tamper (minimum stakes, one round at a time):**
- **Late bet:** capture the bet request; replay it AFTER the betting window closes (round result known). If accepted → critical business logic.
- **Race the balance:** place two near-simultaneous minimum bets from two tabs when balance covers only one. If both are accepted → negative-balance / double-spend logic flaw.
- **Round ID swap:** place a bet referencing a previous `round_id` (already resolved). If the server accepts it → round-state confusion.
- **Bet-amount mutation:** `stake=1` → `stake=0.01` or decimal truncation (`1.999`); check what the server records vs. what it displays.
- **Currency/odds param:** look for `odds`, `multiplier`, or `payout` in responses; if any such field is echoed from the request, tamper it.

**What a win looks like:** bet accepted after window close, double-spend on insufficient balance, or server trusting client-side stake/odds. Never exploit beyond a single minimum-stake proof.

## TARGET 4 — online.bingo.com (bingo rooms)

Bingo rooms = ticket purchase + prize-pool logic + chat-adjacent features.

**Walk the flow:**
1. Buy the minimum ticket pack in a low-traffic room. Capture: ticket purchase request, ticket IDs, card numbers, draw results.
2. Map the room API: room list, ticket inventory, prize pool display, winner announcements.

**Tamper:**
- **Ticket IDOR:** your tickets have IDs — try neighboring IDs and Account B's ticket IDs. Can you view/cash out another player's ticket?
- **Free-ticket params:** `price=0`, `quantity` inflation, `promo=trial` on the purchase call — does the server issue tickets without charge?
- **Draw-result timing:** poll the draw-result endpoint early/often (manual refreshes); if results leak before the draw closes, that's an info-disclosure with betting impact.
- **Prize-pool manipulation:** if the client sends `room_id` or `pool_id` with the ticket purchase, swap to a higher-prize room's ID while paying the low room's price.
- **Chat/XSS:** bingo chat is the classic stored-XSS sink. Test with a benign probe (`<img src=x onerror=...>`) ONLY in a private/empty room or against your own second account's view — stored XSS affecting other players = do not persist it; one render to confirm, then delete and report.

**What a win looks like:** viewing another player's tickets, free/extra tickets issued, or pre-draw result leakage.

## TARGET 5 — unibet.com main app (sportsbook + account)

184 subdomains found; the main app is the account-takeover surface.

**Walk the flow:**
1. Register/login both test accounts. Walk: profile edit, password change, 2FA setup, deposit (minimum), bet placement (minimum stake), betslip, cash-out, withdrawal request.
2. In devtools, inventory the API base (likely `api.unibet.com` or similar) and auth scheme (cookie vs. bearer).

**Tamper — account takeover chain (the €5k–€15k zone):**
- **Profile-update IDOR:** if the profile/bank-details update endpoint takes `user_id`/`player_id` in the body, swap in Account B's ID. If it sticks → horizontal takeover primitive.
- **Email-change → reset:** change Account B's email via the IDOR above (or via a direct email-change endpoint). If it changes WITHOUT verification email → full account takeover chain. Verify with YOUR OWN accounts only; stop at proof of email change.
- **Betslip IDOR:** `betslip_id` / `coupon_id` enumeration between your two accounts — can A view/cash out B's open bet? Cash-out is money movement; test view-only, never execute on the other account.
- **2FA:** does `/verify` accept empty/omitted codes? Replay the verify request with Account A's session but Account B's identifier? No brute-forcing codes, ever.
- **OAuth/SSO:** Unibet offers social login — walk the `oauth-misconfig` checklist: `redirect_uri` to your own domain (use `https://your-own-test-domain`, never a third party), `state` omission, code replay.
- **CSRF on sensitive actions:** password change, email change, withdrawal — strip the CSRF token in Repeater and resubmit. If it processes → CSRF on a sensitive action (explicitly in their focus list).

**What a win looks like:** email change without verification (ATO), betslip/cash-out IDOR, 2FA bypass, or CSRF on withdrawal. Any one of these is High–Critical.

---

## Cross-brand note
Same vuln reproduced on unibet.com + mariacasino.com + bingo.com = report ONCE as systemic (their rules say so) — one report, wider impact statement, better payout.

## Tonight's hit list (do these 5, in order)
1. **payment.mariacasino.com — callback replay:** capture the deposit gateway return URL, replay with `status=success` and a tampered transaction ID. If the balance credits → Critical (€15k zone). One replay, minimum amount, stop at the credit screen.
2. **support-qa1.mariacasino.com — ticket IDOR + open dashboard:** open the host; if there's a ticket portal, create a ticket as Account A and read it as Account B via ID enumeration. QA authz gaps are the fastest wins on this program.
3. **evolivecasino.bingo.com — late-bet replay:** place a minimum bet, capture the request, replay it after the betting window closes. Accepted late bet = broken game-state enforcement.
4. **unibet.com — email-change without verification:** in the profile API, try swapping `user_id` to your second account, then change its email. Email change with no verification = account takeover chain.
5. **online.bingo.com — ticket IDOR:** buy minimum tickets as Account A, then fetch neighboring ticket IDs / Account B's ticket IDs. Another player's ticket data = IDOR win.
