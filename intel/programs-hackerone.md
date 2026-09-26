# HackerOne Public Programs — In-Depth Research

**Researched:** 2026-09-26 · **Source:** HackerOne program directory + individual policy pages (direct fetch where renderable; search-indexed official policy copies + reputable secondary sources where HackerOne's JS shell blocked text fetch — flagged ⚠️ per item).
**Researcher:** hackerone-shiva92 · **Agoda:** already hunting (Agoda Public, $50 min bounty) — not re-covered here.
**Rule:** re-read the LIVE policy page before submitting to any program. Payout tables and scope change; several programs restructured in 2026.

## Comparison table — 15 paid programs

| Program | Paid? | Critical range (USD) | Scope size | Why |
|---|---|---|---|---|
| GitHub | Paid ($250 min) | $10,000 fixed | github.com + Enterprise/Desktop/Actions | Fixed payouts + VIP ladder to 3–4×; best reputation farm |
| Airbnb | Paid ($250 min) | $18,000–$25,000 (high-impact) | `*.airbnb.com`, `*.airbnb.org`, apps, + low-impact tier | Best-written policy; 2-day triage SLA; tiered scope |
| Shopify | Paid ($500 min) | Calculator, up to $200,000 | Own test stores only (`@wearehackerone.com`) | Spin up test stores, zero risk to others; IDOR focus |
| Dropbox | Paid ($216 min) | RCE $32,768 · auth bypass $17,576 | Web, iOS/Android, desktop, Core SDK | Published payout "menu"; target the $12–17K rows |
| HackerOne (own) | Paid ($200 min) | ~$20,000 (disclosed) | hackerone.com, hackerone.net, hacker101.com | Hack the triage platform; auth/IDOR/host-header pay |
| Basecamp | Paid ($100 min) | up to $10,000 | `*.hey.com`, app.basecamp.com, APIs, 37signals OSS | Auth→access-control→injection syllabus; chaining encouraged |
| Adobe | Paid ⚠️ | $5,000–$15,000 (tiered, secondary) | `*.acrobat/lightroom.adobe.com`, Magento, Firefly AI | Wildcard scope + open-source Magento = white-box hunting |
| Stripe | Paid ($100 min) ⚠️ | $5,000–$25,000 (secondary) | stripe.com, api.stripe.com, Stripe.js, SDKs | API-first; test accounts; payment-logic bugs proven |
| Coinbase | Paid | Extreme to $1M · Critical to $15K | Platform, exchange, wallet, cb-mpc | Money-relevant web layer (2FA/KYC/fee/IDOR) is the sweet spot |
| Airtable | Paid ($50 min) | RCE $10,000 · stored XSS $5,000 | **Staging only:** `staging.airtable.com` | Safest legal environment; enterprise admin = IDOR playground |
| Verizon Media | Paid | $10,000–$15,000 | `*.yahoo.com`, `*.aol.com`, `*.techcrunch.com` | Huge legacy surface; subdomain-takeover goldmine |
| Automattic | Paid ($100 min) | $1,000 (WP.com) / $500 (rest) | WP.com, Jetpack, WooCommerce, Tumblr… | Overlaps his WordPress audit lane; explicit focus guidance |
| GitLab | Paid ⚠️ | $20,000–$35,000 | gitlab.com, registry, source | Fully open source; CVSS→payout calculator; huge ceiling |
| Amazon VRP | Discretionary | No published table | `*.amazon` wildcard + devices + GenAI | Largest public scope; scanning explicitly allowed (≤5 rps) |
| Booking.com | Paid ⚠️ | Not retrieved | `*.booking.com` (provisional) | Same vertical as Agoda — recon tooling transfers directly |
| Affirm | Paid | No amounts published | `sandbox.affirm.com` (sandbox-only) | Frictionless fintech sandbox; most beginner classes out-of-scope though |

---

## 1. GitHub — https://hackerone.com/github
- **Paid:** yes. Public tier + invite-only VIP tier (restructured **2026-07-27** after AI-generated report spam).
- **Bounty table (public tier, fixed):** Critical $10,000 · High $5,000 · Medium $2,000 · Low $250. VIP tier: $30,000+ / $20,000 / $7,500 / $1,000. Qualify for VIP via: 1 accepted critical, 2 highs, 4 mediums, or 7 lows in the public program (prior findings count).
- **Scope:** github.com, GitHub Enterprise, GitHub Desktop; historically GitHub Actions + Mobile. Confirm asset list on the Scope tab.
- **Rules:** **Safe harbor YES** ("we don't want researchers put in fear of legal consequences"). Newcomers limited to **~4 submissions** (HackerOne signal requirement). AI-generated/low-effort reports actively rejected. Standard GitHub accounts for testing.
- **Focus:** core github.com web app, Actions, Enterprise, Desktop.
- **Invite:** public tier open to all; VIP invite-only.
- **WHY:** the reputation farm — published fixed payouts, clear VIP ladder to 3–4× payouts, most-documented web surface alive. The 4-submission newcomer cap forces quality from day one.

## 2. Airbnb — https://hackerone.com/airbnb
- **Paid:** yes. Min $250, max $25,000.
- **Bounty table:** High-impact scope — Critical $18,000–$25,000 · High $10,000–$17,999 · Medium $1,000–$5,000 · Low $250. Low-impact scope — Critical $5,000 · High $3,000 · Medium $500–$1,000 · Low $250. AI Customer Service Assistant feature: High $5,000 · Medium $2,500. Vuln guide: RCE=Critical; SQLi=High–Critical; IDOR=Medium–Critical; sensitive data exposure=Medium–Critical; SSRF=Low–Critical; stored XSS/auth bypass/authz flaw=Medium–High; CSRF/open redirect/reflected XSS/subdomain takeover=Low–Medium.
- **Scope:** high-impact: `*.airbnb.com`, `*.airbnb.org`, `*.musta.ch`, `*.airbnbpayments.com`, all localized sites, iOS+Android apps. Low-impact (reduced payouts): `*.atairbnb.com`, `*.withairbnb.com`, `*.airbnbcitizen.com`, `*.byairbnb.com`, `*.muscache.com`, `*.airbnb-aws.com`, `*.luxuryretreats.com`, `*.airbnbopen.com`, HotelTonight domains.
- **Rules:** **Safe harbor YES.** Tag traffic with `X-HackerOne-Researcher: <username>` + include source IP. No mass account creation; no brute-force rate-limit probing; no social engineering; own accounts only. **Triage SLA: 2 business days; payout 5 business days from triage.** HotelTonight test env with test card 4111111111111111. Out: DoS, phishing, raw scanner output, missing headers/CSP, email enumeration oracles, exposed Google Maps keys, AI-filler reports closed N/A.
- **Focus:** booking + payments flows — auth, IDOR, SSRF, XSS.
- **WHY:** the most precisely written policy in the set — exact what's-in-scope/what-pays/how-fast; tiered scope gives lower-competition assets; 2-day triage = fast feedback loop.

## 3. Shopify — https://hackerone.com/shopify
- **Paid:** yes. Min **$500** (score < 3); score ≥ 3 → calculator amount; max **$200,000**. High-potential zero-score issues: 10% bonus, $500–$5,000.
- **Bounty table:** calculator-based, no fixed severity table.
- **Scope:** assets on the Scope tab only. **Critical mechanic:** test ONLY stores you create yourself with your `@wearehackerone.com` alias — touching live merchants → N/A and/or disqualification.
- **Rules:** no explicit safe-harbor clause; no automated-scanning clause in fetched text. No public disclosure before resolution. Do NOT contact Shopify Support about the bounty. Leaked credentials accepted — auth, de-auth, stop, don't share. IDOR judged on identifier predictability + data + impact. First reporter wins; same root cause = duplicate.
- **Focus:** IDOR with predictable identifiers; leaked credentials; merchant-data PII exposure.
- **Invite:** public; separate invite-only Early Access Program (4+ reports/2yr, 50%+ success rate) not required.
- **WHY:** beginner-friendly onboarding — your own test store means zero legal risk to others; $500 floor; clear calculator math.

## 4. Dropbox — https://hackerone.com/dropbox
- **Paid:** yes. Min $216, **no maximum**.
- **Bounty table (indicative minimums for criticals on core web/server):** RCE on servers $32,768 · significant auth bypass $17,576 · trivial RCE in clients $15,625 · CSRF on critical actions $13,824 · XSS on www.dropbox.com (all browsers) $12,167. Lower for heavy user interaction; bonuses for clever research; charity donations matched.
- **Scope:** web app, iOS/Android apps, desktop client, Core SDK. Out: XSS on `*.dropboxusercontent.com`, forums, non-Dropbox domains; physical-access attacks; login/logout CSRF.
- **Rules:** safe harbor/scanning not explicitly confirmed — verify. No bounty for pre-patch public disclosure. First reporter wins.
- **Focus:** RCE, auth bypass, XSS (browser breadth affects payout), SSRF (disclosed $17,576 "Full Response SSRF via Google Drive" is a study template), CSRF on critical actions.
- **WHY:** a published "menu" of what pays — target the $12K–$17K rows (XSS, auth bypass, SSRF) with classic web skills; sharing-links/file-preview/OAuth surface is rich in IDOR/XSS/SSRF.

## 5. HackerOne (their own program) — https://hackerone.com/hackerone
- **Paid:** yes. $200 minimum. Disclosed range ~$2,500–$20,000 ($20K ATO via session-cookie leak, $12.5K IDOR, $3K password-reset poisoning via Host header).
- **Scope:** hackerone.com, hackerone.net, hacker101.com, hackerone-ext-content.com.
- **Rules:** **Safe harbor YES** (good-faith research protected, incl. bypassing tech measures; pseudonymous submissions encouraged). **Must set a custom HTTP header in all testing traffic** and include it in the report. **Automated scanning restricted** — ask first. No social engineering; own accounts only. Disclosure: public only with agreement; **180-day** non-response disclosure window.
- **Focus:** platform itself — auth/session flows, invitation/submission logic, researcher APIs. Real finds: password-reset poisoning via Host/X-Forwarded-Host, private-invite harvesting.
- **WHY:** hacking the bounty platform teaches you how triage works (making all other reports better); payouts generous; the paying classes — auth bugs, IDORs, host-header injection — are the beginner-intermediate toolkit.
## 6. Basecamp — https://hackerone.com/basecamp
- **Paid:** yes — $100–$10,000 scaled by impact/ingenuity. One bounty per bug, first finder wins. Valid bypasses of fixed vulns: 35–70% of original bounty.
- **Scope:** HEY — `*.hey.com`, hey.com email + HEY-hosted custom domains, native apps (own accounts only); Basecamp — app.basecamp.com, published APIs, launchpad.37signals.com auth, Admin Pro Pack; **open source** — Fizzy, ONCE Campfire, ONCE Writebook, Trix, Stimulus, other 37signals GitHub projects (bounty-eligible only if the bug translates into the paid apps). Out: stats.hey.com etc.; Fizzy SaaS itself; rate-limiting/best-practice/clickjacking/self-XSS/missing-headers/username-enum/DoS/host-header-without-impact gripes.
- **Rules:** **automated scanning PROHIBITED** (no Burp Intruder, no brute-forcing, no mail bombing); scanner output without explanation = N/A. `@wearehackerone.com` in test-account email. Own accounts only; no social engineering; no fuzzing support forms. No explicit safe-harbor clause (cooperative tone). Step-by-step repro + attack scenario required.
- **Focus (explicit):** strong auth (sign-in, sessions, OAuth, recovery, MFA); access control (bypasses, CSRF); injection (SQL, XSS, method args); HEY-specific: privacy leaks where a message makes the recipient's browser contact sender-controlled servers. **Chaining encouraged.**
- **WHY:** the focus list reads like a beginner-intermediate syllabus (auth → access control → injection); chaining explicitly rewarded — perfect for leveling from single bugs to exploit chains.

## 7. Adobe — https://hackerone.com/adobe ⚠️ (page didn't render; secondary-sourced)
- **Paid:** yes. Range $100–$15,000. Tier 1 (Magento, ColdFusion, Firefly) Critical $5,000–$10,000 · Tier 2 (Commerce Web, Behance, Express) Critical $2,500–$5,000 · Tier 3 AI Bonus (Firefly AI, Acrobat AI) Critical $7,500–$15,000.
- **Scope:** wildcards `*.acrobat.adobe.com`, `*.lightroom.adobe.com`; stock.adobe.com, contributor.stock.adobe.com, firefly.adobe.com, photos.adobe.io, photoshop.adobe.com, fonts.adobe.com, account.adobe.com, new.express.adobe.com, portfolio.ccpsx.com, magento.com, account.magento.com, repo.magento.com; mobile: Acrobat Reader, Adobe Scan, Lightroom Mobile, Photoshop Express, Fresco, Workfront, Frame.io.
- **Eligible:** XSS, CSRF, server-side code execution, auth bypass, authorization flaws, SQL/command injection, directory traversal, info disclosure, security misconfiguration. Out: DoS, social engineering, brute force, clickjacking without impact, missing headers, version disclosure, low-impact open redirects.
- **WHY:** wildcard web scope across many products + fully open-source Magento (magento2, ~12k stars) = white-box hunting; tiered payouts reward depth; Magento REST/GraphQL is an IDOR/SSRF playground.

## 8. Stripe — https://hackerone.com/stripe ⚠️ (page didn't render; secondary-sourced)
- **Paid:** yes. $100 minimum. Critical $5,000–$25,000 · Medium $1,000–$5,000 · Low ~$500 (researcher-reported).
- **Scope:** stripe.com incl. payments **API (api.stripe.com)**, Dashboard, **Stripe.js**, public GitHub SDK repos, open-source scopes (smokescreen, munkisrv).
- **Rules:** stop + notify on any service degradation. **Never incur loss of funds that aren't yours.** Own accounts only (self-serve "Creating Accounts for Vulnerability Research" section). First-to-report with actionable info wins.
- **Focus:** Stripe.js iframe sandbox boundary, payment-intent crypto tokens, global API microservices, **business logic** (disclosed fee-discount race condition paid $5,000 at Medium).
- **WHY:** API-first surface maps to Burp/web skills; self-serve test accounts; payment-logic bugs are a proven high-ROI lane.

## 9. Coinbase — https://hackerone.com/coinbase
- **Paid:** yes. ⚠️ **Low/Medium are OUT OF SCOPE ($0)** — policy prices only High+.
- **Bounty table:** Extreme up to **$1,000,000** (unauthorized access to hot/cold wallet assets, funds, private keys) · Critical up to $15,000 (market-moving API abuse, RCE on staking infra, easily-exploitable protocol bugs — signing, DKG, TDH2 in cb-mpc, large-scale money laundering, MNPI exposure) · High up to $6,000 (meaningful PII exposure, fee-structure bypass at scale, KYC bypass, single-product 2FA bypass). Severity on impact × exploitability. cb-mpc: extreme out of scope; hard-to-exploit = medium = $0.
- **Scope:** Coinbase platform, exchange, wallet, cb-mpc open-source library. Out: social engineering, username enumeration, non-critical rate limiting, physical security, non-security UX issues, deprecated OSS, third-party integrations, banking-function abuse (ACH/chargebacks), rotated leaked creds, demo/testnet/staging.
- **Rules:** safe harbor not visible in indexed excerpt — verify. Scanning terms not explicit — stay conservative. Real payouts: $10,000 Critical ("Double Payout via PayPal"), historical $25,000 IDOR in account recovery.
- **Focus:** wallet/private-key security, MPC protocol bugs, staking infra, market-moving API abuse, KYC/2FA bypasses, fee-structure bypasses.
- **WHY:** real-money web surface with a $1M ceiling; the money-relevant web layer (auth flows, 2FA, KYC, fee logic, IDORs) is exactly the beginner-intermediate sweet spot — and $0 for low/medium keeps you aimed at high-impact classes only.

## 10. Airtable — https://hackerone.com/airtable
- **Paid:** yes. Min $50. Critical: RCE $10,000 · file-system access $10,000 · stored XSS $5,000. High: priv-esc/auth issues, CSRF on user data, sensitive data over HTTP. Medium: CSV-upload vulns, TLS fixes, missing secure/HttpOnly. Low: self-XSS, Referer leaks, legacy-browser exploits.
- **Scope:** **STAGING ONLY — `staging.airtable.com`.** Production airtable.com and desktop/mobile apps out. `staging.airtable.com/admin` enterprise surface in scope (test-account guide in policy). Out: scanner-output-only reports, duplicates, user-disclosed API keys on GitHub, MITM/device-access, CSV formula injection, missing headers, DMARC/DKIM/SPF, username enum, single-user DoS.
- **Rules:** automated scanners allowed but copy-pasted scanner output rejected — manual insight required. **Exploit/PoC required** for a bounty. No disclosure without permission. No explicit safe-harbor clause.
- **WHY:** staging-only scope = the safest legal environment to be aggressive; $50 floor with $10K ceiling; enterprise admin surface is a classic IDOR/priv-esc playground.

## 11. Verizon Media — https://hackerone.com/verizonmedia
- **Paid:** yes. Informative $0 · Low $100–$500 · Medium $500–$3,000 · High $3,000–$10,000 · Critical $10,000–$15,000 (CWE-mapped; SQLi/OS command injection up to Critical, stored XSS High).
- **Scope:** `*.yahoo.com`, `*.aol.com`, `*.techcrunch.com`, plus mail/media assets (`*.aolmail.com`, `*.aolcdn.com`). Explicit out-of-scope list in policy — read fully. SSRF testing uses dedicated "bananastand" servers with required PoC format (fetch `http://<hostname>/hackerone-<username>`, attach file + timestamp).
- **Rules:** safe harbor/scanning terms unverified — read the live page. The `hackerone-<username>` SSRF convention shows labeled noisy activity is expected.
- **Focus:** injection classes (SQLi, OS command injection, XSS variants), auth issues, subdomain/DNS takeover.
- **WHY:** enormous scope across dozens of Yahoo/AOL/TechCrunch properties — forgotten subdomains and legacy-app bugs; published severity→payout table; classic beginner-friendly hunting ground. ⚠️ Slug may be legacy; also check **hackerone.com/yahoo** before submitting.

## 12. Automattic — https://hackerone.com/automattic
- **Paid:** yes. Min $100.
- **Bounty table:** Critical $1,000 (WP.com) / $500 (rest) · High $600/$300 · Medium $300/$200 · Low $100/$100.
- **Scope:** WordPress.com, Jetpack, WordPress VIP, Beeper, Texts, Akismet, Gravatar, WooCommerce, Tumblr, Simplenote, "and more". Out: issues needing admin-granted roles (Contributor+, Shop Manager+) unless high-severity escalation shown; DoS-by-missing-rate-limit; "Follow-Ups" WooCommerce extension; XSS on intentionally-HTML-allowed domains; tabnabbing; best-practice nits. (WordPress Foundation's separate program at hackerone.com/wordpress tightened scope Sept 2026 against most Contributor-role findings — same team culture.)
- **Rules:** own test accounts only; no disclosure before resolution → disqualification; attachments inside the HackerOne report only; same bug on different host → file inside existing report; same payload/different parameter → consolidate or payouts merge.
- **Focus (explicit):** "unauthenticated or customer/subscriber+ with actual security impact" — unauth stored XSS in visitor/admin sessions, payment bypasses, RCE.
- **WHY:** direct overlap with his WordPress security-audit freelancing lane — the PHP/WP surface he already studies; explicit focus guidance tells a beginner exactly what to hunt.

## 13. GitLab — https://hackerone.com/gitlab ⚠️ (secondary-sourced; substitutes for Atlassian)
- **Paid:** yes. Critical $20,000–$35,000 · High $5,000–$15,000 · Medium $1,000–$3,000 · Low $100–$750 (CVSS-driven via GitLab's AppSec CVSS calculator). $1M+ paid in 2024 across 275 valid reports.
- **Scope:** gitlab.com, self-hosted GitLab instances, gitlab-org/* source, registry.gitlab.com. DoS moved out of scope (Jan 2026).
- **Rules:** severity = f(CVSS + business impact), deterministic. Free self-service signup — low barrier.
- **WHY:** best-in-class beginner pick — entire codebase open source (white-box hunting), transparent CVSS→payout mapping, huge ceiling. (Substituted for Atlassian — Atlassian's H1 page wouldn't render and field notes say its paid bounty moved to an invite-only Bugcrowd engagement; verify before investing time.)

## 14. Amazon Vulnerability Research Program — https://hackerone.com/amazonvrp
- **Paid:** yes, but **rewards fully discretionary** — no fixed USD table; program can be cancelled anytime. Severity guidance: RCE Critical; SQLi/XXE/XSS High–Critical; SSRF Medium–Critical; auth bypass/priv-esc/IDOR Medium–High; misconfiguration Low–High; cache deception/CORS/CRLF/CSRF/open redirect/info disclosure Low–Medium; GenAI prompt injection Medium–Critical, unauthorized PII/PHI High–Critical.
- **Scope:** **all retail marketplaces (wildcard `*.amazon`)**; mobile apps (MShop, Alexa, FireTV, Kindle, Photos, Key, Luna); Amazon Devices (Fire, Echo, Kindle, Blink, Luna) + device web apps; GenAI/LLM issues; fraud/abuse with substantial impact. Out: anything with "aws" in the subdomain (AWS strictly out); Zoox; Amazon Leo; `*.a2z`; `*.dev`; non-production; Twitch and subsidiaries unless named; Whole Foods/physical stores. Out-of-scope classes: clickjacking, self-XSS, SPF, missing headers, social engineering, cookie flags, low-impact CSRF, content spoofing, stack traces/path disclosure, banner grabbing, CSV injection, user enum, DoS, raw scanner output, host-header without impact.
- **Rules:** **safe harbor YES** (research "authorized" under CFAA/DMCA in good faith; ToS/AUP waived). **Automated scanning explicitly allowed: ≤5 requests/second per service** with User-Agent `amazonvrpresearcher_<username>`; create accounts with `<h1username>@wearehackerone.com`. SSRF testing via `bugbounty-sheriff.aka.amazon.com:443` only (no third-party infra). Subdomain takeovers: hidden non-root HTML file with your H1 username. **Disclosure STRICT** — no sharing findings with any third party, publicly or privately. No post-exploitation, no DoS/brute-force, no touching others' accounts/data. 18+ to be paid.
- **Focus:** retail marketplace web (one of the largest public scopes), device companion APIs, LLM/GenAI security, fraud-and-abuse logic at scale. High-quality reporters get invited to the Amazon Private Program.
- **WHY:** the `*.amazon` wildcard is one of the largest public web scopes in existence; scanning explicitly permitted with clear rate rules; unusually well-documented policy — ideal for learning program-compliant hunting at scale. Caveat: heavily hardened, payouts discretionary.

## 15. Booking.com — https://hackerone.com/bookingcom ⚠️ (policy page unfetchable this session)
- **Paid:** yes — confirmed active (disclosed report: subdomain takeover of `ci-support.booking.com`, June 2024; H1 blog quotes their Head of AppSec on program ROI). Bounty table, scope list, and rules NOT obtained.
- **Provisional scope signal:** `*.booking.com` subdomains in scope (from the disclosed takeover). Researcher-facing detail: use your `@wearehackerone.com` email so their internal monitoring identifies you as a researcher, not a malicious actor.
- **⚠️ ACTION:** delegate a live-browser read of https://hackerone.com/bookingcom (or Shivam opens it) to fill the bounty table + scope before hunting.
- **WHY (provisional):** same travel/hospitality vertical as Agoda — recon tooling and booking-flow test methodology transfer directly; disclosed history shows subdomain-takeover and OAuth issues pay here.

---
---

# 5 HackerOne VDPs — best for practice

| VDP | URL | Scope | Why |
|---|---|---|---|
| Basecamp | hackerone.com/basecamp | `*.hey.com`, app.basecamp.com, APIs, 37signals OSS | Pays $100–$10K actually — auth→IDOR→injection syllabus; chaining encouraged |
| Supabase | hackerone.com/supabase | supabase.com, api.supabase.com, `*.supabase.co` (own projects), `*.database.dev` | Free own sandbox, open source, gold-standard safe harbor, ~2-day triage |
| Drupal | hackerone.com/drupal | Drupal core + drupal.org ecosystem | Fully open-source PHP; textbook XSS/access-bypass/SQLi classes; zero payout pressure |
| Artsy | hackerone.com/artsy | artsy.net + `*.artsy.net` | Publishes known-issues + fixed-issues lists; rewards classic web bugs up to $3,500 |
| Aptible | hackerone.com/aptible | api/auth/billing/dashboard/gridiron.aptible.com only | Tiny explicit scope; manual-only policy forces real skills |

## VDP 1 — Basecamp — https://hackerone.com/basecamp
Paid $100–$10,000 (assigned as VDP but it pays — treat as low-stakes paid). Full detail in section 6 above.

## VDP 2 — Supabase — https://hackerone.com/supabase ⚠️ (secondary-sourced)
- **Type:** VDP — recognition-only, no cash (paid bounties reportedly planned for 2026).
- **Scope (18 assets):** supabase.com, api.supabase.com, mcp.supabase.com/mcp, github.com/supabase + community repos, `*.supabase.co` (**your own projects ONLY**), `*.database.dev`.
- **Rules:** `@wearehackerone.com` emails for all accounts; header `X-SUPABASE-VDP: {H1 HANDLE}` on all requests. Out: intended SQLi on `api.supabase.com/platform/pg-meta/{id}/query`, clickjacking, CSRF on non-sensitive forms, DoS, rate limiting, automated tools without manual verification. Raw unvalidated AI-generated reports = N/A. **Safe harbor: "Gold Standard"** ("we will not take any legal action against you" if you follow the instructions); response within 5 business days; credit as discoverer. Coordinate disclosure; share drafts 30 days before public writeup.
- **WHY:** free sandbox (your own Supabase project = test surface you control), fully open-source, fast triage, explicit safe harbor — the safest place to build real report-writing reps before touching paid programs.

## VDP 3 — Drupal — https://hackerone.com/drupal
- **Type:** VDP only — no monetary bounties (GraphQL-verified `offers_bounties: null`). Credit / Hall of Fame.
- **Scope:** Drupal core and the drupal.org ecosystem; per drupal/drupal SECURITY.md — report to the Drupal Security Team, keep confidential, never via public GitHub issues.
- **Rules:** confidential coordinated disclosure on the team's timeline; include repro steps, affected versions, PoC.
- **WHY:** fully open-source PHP codebase = source-assisted hunting (grep sinks, trace data flow) — the fastest way to level up; long CVE history of textbook XSS/access-bypass/SQLi; zero payout pressure makes it ideal for practicing report writing.

## VDP 4 — Artsy — https://hackerone.com/artsy
- **Type:** technically pays (up to $3,500 for fixed issues) — behaves like a low-stakes paid program.
- **Scope:** artsy.net and `*.artsy.net` — web platform, mobile apps, APIs. Out: partners.artsy.net; beta/staging/review apps; third-party-looking domains. Published known-issues list (do NOT report): username/email enumeration, missing security headers, DMARC, session-cookie reuse before logout…
- **Rules:** no safe-harbor clause — responsible-disclosure terms only: no accessing other users' accounts/data; no DDoS/spam; **no public disclosure before fix**; no social engineering; **no scripting/automation or brute-forcing**; duplicates first-come-first-served; rewards via PayPal (W-9/W-8BEN may be required; sanctions countries excluded). Recently fixed issues (XSS in user bios, open redirects, OAuth CSRF, password-reset flaws, S3 misconfigs) show exactly what gets rewarded.
- **WHY:** publishes known-issues + fixed-issues lists (never waste time on dead ends); rewards classic web bugs a beginner can actually find; free signup makes authenticated testing trivial.

## VDP 5 — Aptible — https://hackerone.com/aptible
- **Type:** disclosure-policy program; "cash and prizes" for qualifying reports.
- **Scope:** tight explicit list — **only**: api.aptible.com, auth.aptible.com, billing.aptible.com, dashboard.aptible.com, gridiron.aptible.com. Out-of-scope classes: DoS, brute force, physical, social engineering, CSRF on anonymous forms, self-XSS, clickjacking, descriptive errors, HTTP 404s, banner disclosure, robots.txt, user enum, absence of rate limits.
- **Rules:** four hard rules — NEVER access another user's account/data, NEVER degrade services, NEVER impact other users, test only in-scope domains. **"Do not use fuzzers, scanners, or other automated tools"** — manual only; violating = ineligible. Report via email.
- **WHY:** tiny precisely-defined scope + strict manual-only, no-noise policy forces exactly the skills that matter most (manual auth testing, IDORs, business logic on api/dashboard/billing) instead of scanner spray.

---

## Dead/redirected handles (do not waste time)
- **hackerone.com/mailru** — redirects; VK runs its own platform at bugbounty.standoff365.com, not H1.
- **hackerone.com/asana** — no H1 program; disclosure via security@asana.com (email only, no bounties).
- **Atlassian** — H1 page wouldn't render; field notes say H1 listing is now VDP/points-only with paid bounty on invite-only Bugcrowd — verify before investing time. (GitLab is the recommended substitute.)

---

## Starter ladder (suggested)
1. **Practice:** Supabase or Aptible VDP → Drupal → Artsy/Basecamp — build real report-writing reps and triage-quality PoCs.
2. **Reputation farm:** GitHub public tier (fixed payouts, VIP ladder) — every accepted report multiplies future payouts 3–4×.
3. **Paid targets:** Airbnb (best policy, 2-day triage) → Shopify (own test stores, IDOR) → Dropbox (published payout menu) → Coinbase/HackerOne-own (auth/IDOR toolkit).
4. **Scale plays:** Amazon VRP (`*.amazon` wildcard, scanning allowed) and Verizon Media (`*.yahoo.com` etc., takeover goldmine) once fundamentals are solid.

## Operational notes
- Set up once, reuse everywhere: `@wearehackerone.com` email alias + researcher-identification headers (`X-HackerOne-Researcher: <username>`, program-specific deconfliction headers, program-mandated User-Agents).
- Coinbase prices Low/Medium at **$0** — aim at High+ only there.
- GitHub newcomers get ~4 submissions — submit only validated reports.
- Affirm publishes **no bounty amounts** — hunt there only with payout expectations set by the researcher, not the program.
- Booking.com needs a live-browser policy read to fill the bounty table + scope.
