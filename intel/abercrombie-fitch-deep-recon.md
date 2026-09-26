# Abercrombie & Fitch — Passive Recon Deep-Hunt Report
**Research date:** 2026-09-26 (all findings dated; policies change without notice)
**Program handle (verified from HackerOne directory search):** https://hackerone.com/abercrombie_fitch_bbp
**Program name:** "Abercrombie & Fitch Bug Bounty" — Managed by HackerOne, offers bounties, min bounty $50.
**Company:** Abercrombie & Fitch Management Co. (ANF), New Albany, Ohio. Brands: Abercrombie & Fitch, abercrombie kids, Hollister, Gilly Hicks (Social Tourist folded into Hollister per company filings).
**Status of this report:** PASSIVE ONLY. No scanning, no probing, no logins, no traffic beyond loading public pages. Sections marked UNVERIFIED could not be confirmed passively.

---

## 1. Live Policy (from https://hackerone.com/abercrombie_fitch_bbp, fetched 2026-09-26)

### Bounty table (90-day average bounty per severity, per the page)
| Severity | 90-day avg |
|---|---|
| Low | $250 |
| Medium | $750 |
| High | $2,500 |
| Critical | $4,000 |
Bounties are CVSS-based guidelines; award decisions are at ANF's discretion. Min bounty $50.

### SLA / velocity stats (page data)
- Avg time to first response: 2 days, 1 hour
- Avg time to triage: 3 days, 9 hours
- Avg time to bounty: 2 days, 13 hours
- Avg submission→bounty: 5 days, 22 hours
- Avg time to resolution: 2 months, 1 week
- Platform Standards: fully compliant. Managed, collaboration enabled, includes retesting.
- BugBountyHunter mirror shows **0 disclosed reports, $0 paid publicly** (as of 2026-09-26 crawl) — triage is fast but there is no public report history to pattern-match.

### In-scope assets — UNVERIFIED (scope table not retrievable passively)
The scope asset table is rendered via JS on the policy page; the fetched page text did not include it, and the `/policy` sub-URL returned 403. Mark as **unverified until confirmed on the live page while logged in**. The policy text strongly implies the following (see "same architecture" note), but this is inference, not confirmation:
- `*.abercrombie.com` (incl. abercrombiekids.com presumably)
- `*.hollisterco.com`
- Mobile apps: Abercrombie (`com.abercrombie.abercrombie`) and Hollister (`com.abercrombie.hollister`) — likely in scope but NOT confirmed.
- Non-prod environments: explicitly mentioned as eligible ("The same rule can be applied to exposed non-prod environments if found").

### Explicit exclusions (verbatim from policy)
- Core Ineligible Findings (HackerOne platform standard).
- Clickjacking on pages with no sensitive actions.
- CSRF on unauthenticated forms / forms with no sensitive actions.
- MITM / physical access attacks.
- Known vulnerable libraries without a working PoC.
- CSV injection without demonstrating a vulnerability.
- SSL/TLS config best practices; CSP best practices; email best practices (SPF/DKIM/DMARC).
- DoS of any kind.
- Content spoofing / text injection without an attack vector / without HTML/CSS modification.
- **Rate limiting, bruteforce or enumeration issues on non-authentication endpoints** — (implies auth endpoints ARE fair game; account lockout / credential stuffing defenses are testable).
- Outdated browsers (<2 stable versions behind).
- Version disclosure / banner / descriptive error messages without PoC → informational.
- Zero-days with official patch <1 month → case-by-case.
- Tabnabbing, typosquatting.
- Open redirect unless additional security impact demonstrated.
- Issues requiring unlikely user interaction (incl. phishing).
- **Promotional code abuse** ← explicit retail-logic exclusion.
- Social engineering of customer service agents via voice or chat.

### Program rules (key points)
- Detailed reproducible reports required or ineligible. One vuln per report (chain only to show impact); one underlying issue = one bounty; first report wins duplicates.
- Public PoC/exploit use is fine (cite source); may earn a bonus for lesser-known exploits.
- **PII exfiltration/exposure is expressly prohibited** — use only own test accounts for PoC.
- Found credentials: report source, do NOT use them to access systems without explicit written approval; value at ANF's discretion.
- No social engineering incl. CS/chat agents.
- Only interact with accounts you own; avoid privacy violations, data destruction, service degradation.
- **Employees/contractors (past and current) and connected entities are ineligible.**
- **"Abercrombie's and Hollister Co.'s underlying architecture is the same. The same rule can be applied to exposed non-prod environments if found. Refrain from submitting a duplicate report for the other domain or environment."** ← one architecture, one codebase; dedupe across brands.
- Test plan: use a modified User-Agent (e.g. `h1:<hackerone-username>`) and tag artifacts in PoCs; self-register accounts with `@wearehackerone.com` email; no credentials provided or required.
- Continuous internal scanning: findings already triaged/slated for remediation within SLAs are treated as duplicates; new CVE findings evaluated against existing vuln management.

### Disclosure rules
- Do NOT discuss this program or any vulnerabilities (even resolved ones) outside the program without express written consent from ANF.
- Follow HackerOne disclosure guidelines.
- Corporate disclosure page: https://corporate.abercrombie.com/vulnerability-disclosure/ (points to the HackerOne public program).

---

## 2. Architecture / Tech (public sources: job posts, press, NRF, Retail TouchPoints — 2026-09-26)

- **Custom in-house commerce platform — NOT Salesforce Commerce Cloud.** ANF insourced digital engineering (~125+ hires, product-based model, "insource and build the capability inside the company" — NRF Big Show, Samir Desai, CDTO). Bengaluru Global Capability Centre opened ~April 2026 for data science, AI, engineering, omnichannel ops.
- **Stack from job postings (dice.com, dailyremote.com, wayup.com):** React, Redux, JavaScript, Java Spring Boot APIs, Kafka event streams, Solr, Redis, Elasticsearch, Azure cloud, Kubernetes, Terraform/Bicep, CI/CD (GitLab, Azure DevOps, Jira), Splunk, Dynatrace; iOS in Swift (MVVM/SwiftUI), REST APIs. "API first, headless or composable patterns, event streams." CDN/DNS/global traffic routing experience required — consistent with Akamai infra (see below).
- **Auth model (inferred from public info, UNVERIFIED):** account-based storefronts with loyalty profiles; corporate SSO via NetIQ Access Manager (wamclstr2.anfcorp.com shows NetIQ/nidp SSO for vendor portal — corporate only). No public docs on customer auth (OAuth? session cookies?) — would require logged-in inspection.
- **Mobile apps (verified via APKMirror / Google Play):**
  - Abercrombie: `com.abercrombie.abercrombie`, v10.3.0 (released 2026-09-15), 45 MB, Android 11+.
  - Hollister: `com.abercrombie.hollister`, 4.8★, 110K reviews, 5M+ downloads.
  - App features with security surface: rewards/points accounts, "SHARE2PAY" (Hollister: share a cart, someone else pays — payment-link flow, interesting), barcode scan-and-shop, BOPIS (buy online pickup in store), in-app gift cards, Google Pay / Venmo / PayPal / Klarna.
- **Checkout flow (public info):** card, debit, Amex, PayPal, Venmo (in apps), Klarna BNPL, gift cards, Google Pay. In-store payments via PXP ANYpay (Europe/Canada/Japan). PayPal + Cymbio partnership announced for Perplexity AI-powered checkout (Q3 2025 earnings) — an agentic-commerce surface worth watching.

## 3. Third parties & partners (public sources)
- **CDN/WAF/DNS: Akamai.** anfcorp.com uses Akamai nameservers (a1-58..a26-65.akam.net) and Akamai edge IPs (184.51.146.x); storefronts are very likely behind Akamai too (job posts require CDN/global routing experience). Entrust TLS on corporate.
- **Payments:** PayPal/Braintree family (Venmo in apps), Klarna (BNPL), gift-card processing, Google Pay; PXP for in-store (non-US). Online card processor not publicly confirmed — candidate is PayPal/Braintree given Venmo integration.
- **Fraud/risk:** not publicly named. Retail-standard candidates (Riskified, Signifyd, Forter) — UNVERIFIED.
- **Reviews/UGC:** not confirmed; email program shows Oracle Responsys tags (om_rid/om_mid/RIID in footer links) → **Oracle Responsys** for email marketing (phishing-adjacent, not bounty surface).
- **Personalization/analytics:** Dynatrace (site verification TXT on anfcorp.com), Adobe (adobe-idp site verification TXT), OneTrust (consent), Kochava/MixRank ad-tech footprint (attribution, not app surface).
- **Loyalty:** MyAbercrombie rewards (points for purchases; "Earn points for everything you buy"), Hollister "House" rewards, Club Cali legacy. Points balances + tier status = account-value surface. **Loyalty fraud/abuse is adjacent to "promotional code abuse" exclusion — frame any loyalty hypothesis as technical vuln (IDOR/auth), not abuse.**
- **Inventory/RFID:** Nedap iD Cloud (item-level inventory, global rollout 2025). In-store fulfillment APIs feed BOPIS — inventory APIs are a hypothesis zone.

## 4. Code & repos
- **No official ANF engineering GitHub org found** (searched 2026-09-26; queries "anfcorp github", "Abercrombie Fitch github organization"). No public SDKs identified. Mark as none-found; do not assume a handle.
- Engineering hiring is active (iOS, platform, front-end, supply-chain Java) but no open-source footprint surfaced.

## 5. Videos & writeups
- **Disclosed HackerOne reports:** none public (0 disclosed per BugBountyHunter, 2026-09-26). No hunter writeups found for A&F on the open web or social (social.search stood down with no results).
- **Corporate/public content (architecture context, not vulns):**
  - NRF "Inside the digital transformation of Abercrombie & Fitch" — Samir Desai (CDTO): https://nrf.com/blog/inside-digital-transformation-abercrombie-fitch
  - Retail TouchPoints "How Spotify Helped Abercrombie & Fitch Drive True Digital Transformation": https://www.retailtouchpoints.com/features/abercrombie-fitch-digital-transformation-retail-tech-sprints-organizational-change/113800/
  - Retail Gets Real podcast #337 (Feb 2024): https://www.everand.com/podcast/707310525/337-Inside-the-digital-transformation-of-Abercrombie-Fitch-American-lifestyle-retailer-Abercrombie-Fitch-is-in-the-midst-of-an-enterprise-wide-d
  - eTail Boston 2022 talk (Samir Desai).
  - Vulnerability disclosure page: https://corporate.abercrombie.com/vulnerability-disclosure/

## 6. Asset inventory (passive only)
- **crt.sh:** attempted `https://crt.sh/?q=%25.abercrombie.com&output=json` via browser_open on 2026-09-26 — fetch timed out; not retried per passive discipline. Cert-transparency enumeration is an open follow-up for a session with working crt.sh access.
- **Known domains (verified via company/press sources):**
  - Storefronts: abercrombie.com, abercrombiekids.com, hollisterco.com, gillyhicks.com, socialtourist.com (regional variants e.g. abercrombie.co.uk)
  - Corporate: corporate.abercrombie.com, investor.abercrombie.com, anfcorp.com
- **Subdomains observed in public sources (all anfcorp.com corporate, likely out-of-scope unless listed — verify against live scope table):** my.anfcorp.com, wamclstr2.anfcorp.com (NetIQ SSO), vendorprofile.anfcorp.com, cloudid-ts.anfcorp.com, pshrprdext.anfcorp.com, tprm.anfcorp.com (MX).
- **Registrar:** MarkMonitor; anfcorp.com created 2000-10-20, expires 2027-10-20.
- No scanning performed; no DNS brute-forcing.

## 7. Hypothesis seeds (testable, in-scope-shaped; confirm scope table before testing)
Policy-aware notes: "Promotional code abuse" and "rate limiting on non-auth endpoints" are OUT. "Auth endpoints" are implicitly IN. PII exfiltration prohibited — use own accounts. Same architecture across brands — dedupe across A&F/Hollister.

1. **H1 — Order-tracking / order-history IDOR.** Hypothesis: order status endpoints accept a sequential or guessable order ID without an ownership check. Why: custom-built order management (job posts: "order management… microservices"), BOPIS + ship flows. Expected observation: requesting another account's order number returns its details (items, address → stop at confirming own two accounts to avoid PII violation). Vuln class: IDOR / broken object-level authorization.
2. **H2 — Password-reset token weakness / account takeover.** Hypothesis: reset flow uses predictable tokens, leaks validity oracles, or doesn't expire tokens after use/password change. Why: auth-endpoint rate limiting and bruteforce are implicitly in scope (only non-auth excluded); custom auth stack. Expected observation: token reuse across requests, or user-enumeration via timing/response differences on reset request. Vuln class: broken authentication.
3. **H3 — Cart/checkout price-parameter tampering (technical, not coupon abuse).** Hypothesis: client-side cart or payment APIs accept a server-trusted price/quantity/total from the client, or currency/rounding logic allows underpayment. Why: headless/composable checkout, multiple payment methods incl. gift cards + Klarna; CAREFUL: frame strictly as server-side validation failure, never as promo/coupon abuse (excluded). Expected observation: modifying line-item price in API request changes the charged total (test with $0.01 deltas on own order, do not complete payment). Vuln class: parameter tampering / business-logic flaw.
4. **H4 — Loyalty-points ledger manipulation.** Hypothesis: points accrual/redemption endpoints accept client-supplied point values or fail to validate earn events. Why: "earn points for everything you buy" across brands; points = stored value. Expected observation: API accepts arbitrary points credit on own account (verify balance changes only on own test account; do not redeem). Vuln class: business-logic / parameter tampering. (Not "promotional code abuse" — distinct technical surface.)
5. **H5 — SHARE2PAY payment-link authorization gap (Hollister app).** Hypothesis: "share cart, they pay" links are bearer URLs without expiry or payer/payee binding, allowing link tampering or replay. Why: novel app-only feature = less-hardened code path. Expected observation: payment link usable after cart modification, or accessible without the intended recipient session. Vuln class: broken access control / insecure direct object reference.
6. **H6 — Gift-card balance enumeration / redemption race.** Hypothesis: gift-card balance-check endpoint allows enumeration or double-spend via concurrent redemption requests. Why: in-app gift cards + gift-card payment method; balance check is typically unauthenticated. Expected observation: sequential card numbers yield valid balances, or two near-simultaneous redemptions both succeed on own cards. Vuln class: enumeration / race condition. (Keep to own purchased low-value cards.)
7. **H7 — Inventory / store-availability API data exposure.** Hypothesis: BOPIS/store-stock APIs expose internal fields (cost, supplier, employee notes) or allow cross-store queries without auth. Why: Nedap iD Cloud item-level inventory rollout + custom fulfillment APIs. Expected observation: API responses contain fields not rendered in UI, or accept arbitrary store IDs. Vuln class: excessive data exposure.
8. **H8 — Non-prod environment exposure.** Hypothesis: dev/staging/QA hosts for the storefront or APIs are internet-reachable with weaker auth or debug endpoints. Why: policy explicitly blesses testing exposed non-prod ("same rule can be applied to exposed non-prod environments"). Expected observation: staging host serves the app with debug flags, exposed actuator/Swagger, or default creds (do not log in with found creds without approval — report only). Vuln class: information disclosure / misconfiguration.
9. **H9 — Account registration / profile PII overexposure.** Hypothesis: profile or address-book APIs return other users' data, or the "email already registered" oracle enables enumeration at scale. Why: account-centric loyalty platform; rate-limiting exclusion applies only to non-auth endpoints. Expected observation: address-book endpoint accepts foreign profile IDs; or registration endpoint leaks account existence with high fidelity. Vuln class: IDOR / user enumeration (on auth surface).
10. **H10 — Mobile API vs web API parity gap.** Hypothesis: the mobile apps (com.abercrombie.abercrombie / com.abercrombie.hollister) call API versions or endpoints with weaker validation than the web checkout (e.g., promo/price logic enforced only in web UI). Why: apps updated Sept 2026 (v10.3.0), app-exclusive features (SHARE2PAY, app-only promos), historically mobile APIs lag web hardening. Expected observation: replaying a mobile API call with modified parameters succeeds where web rejects it. Vuln class: business-logic / missing server-side validation. (Requires static analysis of the APK — allowed passive-adjacent step; no dynamic instrumentation against prod beyond normal use.)

### Caveats & open follow-ups
- Scope asset table could not be read passively (JS-rendered; /policy 403). **Confirm exact in-scope assets, mobile-app eligibility, and wildcard coverage on the live HackerOne page before testing.**
- crt.sh enumeration failed (timeout) — retry in a later session for subdomain inventory.
- No official GitHub org / SDKs found; no disclosed reports to pattern-match — this is a fresh-surface program with fast triage (2d) and $4k critical ceiling, but "continuously scanning" + duplicate-SLA rule means recon quality matters more than speed.
