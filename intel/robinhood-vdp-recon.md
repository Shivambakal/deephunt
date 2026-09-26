# Robinhood VDP Recon — passive only (2026-09-26)

No testing, no logins. Scope pulled live from HackerOne public GraphQL on 2026-09-26.

## [SCOPE SUMMARY]

**Program:** "Robinhood Markets Bounty" — hackerone.com/robinhood (paid program).
A second handle, `robinhood_markets`, was observed in third-party program trackers as VDP-only (unverified — confirm before use).

**Bounty-eligible (live scope):**
- `https://*.saytechnologies.com` (wildcard)
- `api.robinhood.com`, `cashier.robinhood.com`, `minerva.robinhood.com`, `nummus.robinhood.com`, `identi.robinhood.com`
- `www.bitstamp.net` (subdomains = Tier 3)
- `*.rhinternal.net`, `*.robinhood.com`, `*.robinhood.net`, `*.say.rocks`, `*.saytechnologies.com`, "Tier 3"
- Mobile: `com.robinhood.android`, `com.robinhood.gateway`, `com.robinhood.money`, `net.bitstamp.app`, `com.robinhood.global` (Android); Apple app IDs 1634080733, 6462308655, 938003185, Id1406825640 (Bitstamp iOS)

**Explicitly NOT bounty-eligible:** tradepmr.com hosts, bitstamp.net mail/infra subdomains, shop.robinhood.com, fleet.infra.robinhood.net, content.research.robinhood.com, events.robinhood.com, affiliates.robinhood.com, vgs-api.robinhood.com, share.robinhood.com, saytechnologies.com/contact/sales.

**Bounty model:** sliding CVSSv3 scale calculated by HackerOne; final severity/bounty at the sole discretion of the Robinhood Security Team (per program policy mirror). Live per-severity table not exposed via public GraphQL — verify on the brief before the active phase.

**Program posture (HackerOne Q&A with Ian Carroll, Robinhood security):** "we accept almost any security issue that could impact Robinhood, regardless of what technical asset has the problem" — all domains and applications in scope, including third-party vendor products and misconfigurations. Customers regularly submit complex trading-flow business-logic issues that "don't look like normal security issues at all, but are highly impactful." This program PAYS for business logic.

**Test hygiene (third-party testing guides, unverified against live brief):** researchers report using `X-Bug-Bounty: <h1_username>` header. Confirm on the brief.

## [DISCLOSED-REPORT PATTERNS]

Robinhood discloses ~zero HackerOne reports publicly — no disclosed report pages were found via search or public GraphQL (hacktivity_items requires auth). Duplication risk is therefore hidden; assume the obvious is taken. Public incidents are the pattern source instead:

1. **"Infinite money glitch" (Nov 2019)** — the canonical Robinhood bug. Robinhood Gold margin (2:1) + selling covered calls: the app added the sold calls' premium to the user's cash pile, raising buying power, which bought more shares, which collateralized more covered calls — recursive, no limit. $3,000 deposits became $1.7M positions (WallStreetBets, Bloomberg/CNBC coverage). Fixed; traders faced potential fraud liability. **Pattern:** in-flight/settlement value double-counted toward buying power. Every input valid, every API call legitimate — the composition violated the business invariant. Sources: securityboulevard.com business-logic writeup (2026-04), pennystocks.com timeline, pws.io.
2. **Account-creation HTML injection → authenticated phishing (Apr 2026).** Attackers injected HTML into the device-metadata field during signup; Robinhood's "recent login" notification emails rendered it unsanitized, sent from noreply@robinhood.com, passing SPF/DKIM. Combined with Gmail dot-aliasing to target victims. Fixed; field removed. **Pattern:** user-controlled fields reflected into transactional email/SMS/push. Sources: BleepingComputer via cloudfront mirror, techrepublic.com, sqmagazine.co.uk.
3. **Nov 2021 breach:** ~7M customer records (emails, names) via social engineering of a customer-support employee + extortion demand. Not a software vuln, but it marks support tooling as attack surface.
4. **Say platform subdomain takeovers (2026-05):** a researcher drafted a HackerOne submission for three claimable Vercel deployments under *.say.rocks (preferences, preferences-test, missioncontrol-pa) — shareholder-phishing impact, estimated $300–$2,000. Shows the Say acquisition surface is soft. Source: github.com/msellpower/lictor-ai (draft submission doc).

**What pays here (from the program's own words + incident history):** business-logic flaws in money movement and trading flows; anything where "in-transit" value is counted twice; transactional-notification injection; vendor/acquisition misconfigurations.

## [MONEY-MOVEMENT STATE MACHINE]

Modeled from public documentation and reverse-engineered API references (no official brokerage docs published; crypto API docs at docs.robinhood.com are official):

```
ACH DEPOSIT:   initiated → pending (3–5d settlement) → settled
               └─ instant buying power granted against unsettled funds (capped)
WITHDRAWAL:    requested → review/hold → processed → settled
ORDER (stock): created → queued → filled | partial → settled (T+1)
ORDER (crypto): created → filled (near-instant, 24/7)
OPTIONS:       bought/sold → exercised | assigned | expired
MARGIN (Gold): subscribed → 2:1 leverage → maintenance check → margin call
```

**Trust boundaries:** client ↔ api.robinhood.com (OAuth2 + device token + MFA) ↔ ledger/clearing; instant-settlement credit sits between "pending" and "settled" — the exact seam of the 2019 glitch. Hostnames map to functions: `cashier` (money movement), `nummus` (Latin: coin — ledger/payments), `minerva` / `identi` (identity/KYC), `dora` (news feed, per community docs).

**API planes (differential surface):**
- Legacy brokerage API `api.robinhood.com` — unofficial, heavily reverse-engineered (pyhood endpoint reference; robinhood-cli-mcp-api route map: /accounts/, /accounts/{n}/buying_power_breakdown, /orders/, /quotes/, /instruments/ UUID-based, /options/, /marketdata/). Auth: OAuth2 password grant (legacy), device tokens, MFA.
- Official Crypto Trading API (docs.robinhood.com, since 2024) — API key + Ed25519-signed JWT.
- **Agentic Trading MCP server** `agent.robinhood.com/mcp/trading` — opened to third-party agents May 2026 (stocks/options), Jul 2026 (crypto). Brand-new, agent-shaped attack surface: prompt injection via market/news content, tool-permission overreach, confused-deputy trade execution.

## [HYPOTHESES] (ranked by expected value)

1. **H1 — In-flight double-counting (the glitch shape).** Invariant: "value in transit must be counted exactly once toward buying power/margin." Probe every new money feature (instant crypto settlement, Bitstamp transfers, fractional-share settlement, dividend reinvestment) for the same composition flaw: operation A credits buying power while operation B hasn't debited yet.
2. **H2 — Race on balance (TOCTOU).** Invariant: "two concurrent debits must never exceed available balance." Concurrent withdrawals, simultaneous orders, or order+withdrawal pairs racing the ledger check.
3. **H3 — State-transition skipping.** Invariant: "a terminal state must never accept further transitions." Cancel-after-fill, modify-after-execution, withdrawal cancel/replay, exercising expired options.
4. **H4 — Unsettled-fund withdrawal.** Invariant: "funds must never leave the platform before settlement except through the defined instant-credit allowance." ACH deposit → instant credit → withdraw/transfer-out before the ACH clears.
5. **H5 — Amount/precision manipulation.** Invariant: "amounts must be positive, correctly rounded, and currency-consistent." Negative quantities, zero-decimal confusion, fractional-share rounding, crypto dust, currency substitution on Bitstamp pairs.
6. **H6 — IDOR on financial objects.** Invariant: "account_number/order IDs must stay bound to the session principal." api.robinhood.com uses numeric account numbers alongside UUIDs — swap across principals; record only the access decision.
7. **H7 — API-plane authz differential.** Invariant: "the same object must have the same authorization decision on every API plane." Legacy api.robinhood.com vs crypto API vs MCP server on identical objects/actions; device-token auth vs API-key auth vs session.
8. **H8 — MCP tool abuse.** Invariant: "an agent must never execute trades outside its granted scope." Prompt-inject via news/market content the agent reads; test whether tool calls validate intent, amounts, and symbols server-side.
9. **H9 — Transactional notification injection.** Invariant: "user-controlled input must never render as HTML in emails/SMS/push." The Apr-2026 class — enumerate every user-controlled field that lands in a notification (device names, nicknames, memo fields, referral messages).
10. **H10 — Referral/promo stacking.** Invariant: "a promo must be claimable exactly once per eligible principal." Free-stock referrals, deposit matches, Bitstamp migration promos — duplicate claims via race, multi-account, or state replay.
11. **H11 — Recovery/KYC state machine (identi/minerva).** Invariant: "identity verification steps must not be skippable or replayable." Document-upload flows, step reordering, reusing another session's verification result.
12. **H12 — Bitstamp↔Robinhood ledger disagreement.** Invariant: "cross-entity transfers must debit exactly what they credit." The acquisition seam — transfers between the two ledgers, currency/pair mapping mismatches, settlement-timing gaps.
13. **H13 — Cashier endpoint tampering.** Invariant: "the server must re-derive amount/destination from its own state." `cashier.robinhood.com` flows that accept client-supplied amounts, account numbers, or rail selection.
14. **H14 — Say platform auth boundary.** Invariant: "shareholder Q&A must not leak non-public company data or allow impersonation." *.say.rocks / *.saytechnologies.com — the softest in-scope web surface.

## Caveats / blockers for the active phase

- **Identity wall:** Robinhood brokerage accounts require US residency + SSN for KYC. No synthetic identity can clear this, and fake KYC is out of bounds. Authenticated money-movement testing is therefore blocked unless the program provides test accounts (it historically has not) — verify on the live brief.
- **What IS testable without KYC:** unauthenticated API surface (rate limits, error oracles, CORS, version differentials), the official Crypto API docs surface, MCP server tool-permission analysis, mobile app static analysis (in-scope app IDs), Say platform web surface, subdomain/infra recon on *.robinhood.com / *.robinhood.net / *.rhinternal.net.
- Bounty table and required researcher headers must be re-verified on the live HackerOne brief before any active work.
- The lucius-secops TESTING_QUICKSTART.md "IDOR on /api/orders?account_id=" PoC is a hypothetical template, NOT a real finding — do not cite it as a disclosed report.
