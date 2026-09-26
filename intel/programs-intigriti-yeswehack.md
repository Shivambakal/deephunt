# Bug Bounty Programs — Intigriti / YesWeHack / HackenProof / BugBase / Yogosha

Researched 2026-09-26. All programs public and open to registered hunters unless noted.
Currency note: EUR→USD ≈ 1.17 (Sept 2026) where equivalents are given.

## Quick-comparison table

| Program | Platform | Paid? | Top payout | Scope size | Why pick it |
|---|---|---|---|---|---|
| intigriti (own program) | Intigriti | Paid | €13,337 (~$15.6k) | Wildcards: `*.pwn.intigriti.rocks`, `*.intigriti.me` | Unrestricted PWN test env over VPN — best beginner ground that actually pays |
| FDJ United (betting/gaming) | YesWeHack | Paid | €15,000 (~$17.6k) | 33 scopes (Unibet, MariaCasino, 32Red, bingo.com brands + payment.* subdomains) | Betting = business-logic gold; 716 reports spread thin across 33 scopes |
| Superbank | YesWeHack | Paid | $2,000 | 6 scopes (API, web, mobile, AI chatbot) | Only 123 reports; self-registration; API + AI chatbot in scope |
| Moneybox | YesWeHack | Paid | €2,000 (~$2.3k) | 6 scopes incl. 3 admin panels at Critical tier | Admin panels = IDOR/auth territory; only 137 reports |
| Kiteworks | YesWeHack | Paid | $50,000 | 12 scopes (dedicated hunting environment) | Launched Sept 2026 — fresh surface; $25k crown-jewel RCE bonus; advanced level |
| Doctolib | YesWeHack | Paid | €50,000 (~$58.5k) | 9 scopes (`*.doctolib.(fr/de/it/com/net)` + siilo) | Fake-doctor test account provided; IDOR-friendly; special-scenario bonuses |
| CoinDCX | YesWeHack | Paid | $2,000 | `*.coindcx.com` wildcard + API + mobile apps | India's largest crypto exchange; wallet/account-takeover focus; <1-day triage |
| TrueLayer | Intigriti | Paid | €6,000 (~$7k) | Tiered API assets | Open Banking APIs = IDOR/priv-esc territory; explicit 10 req/sec automation allowance |
| BMW Group | Intigriti | Paid | €6,000 (~$7k) | Tier 1–2 assets | Connected-car + web scope; matches car-enthusiast angle |
| Oda | Intigriti | Paid | €4,000 (~$4.7k) | `*.oda.com` + `*.prod.nube.tech` wildcards | E-commerce wildcard; safe harbor; documented scanner rate limits |
| Personio | Intigriti | Paid | €5,000 (~$5.9k) | Tier 2–3 HR SaaS | HR platform = PII/IDOR-rich; clear tier structure |
| Suivo | Intigriti | Paid | €2,000 (~$2.3k) | Staging env (copy of prod) | Test staging, not prod — low-risk learning; fleet-tracking web app |

## Platform notes — who lets a brand-new hunter start immediately

- **YesWeHack** (France, EU): public programs open to any registered hunter, no reputation needed. Fast in-house triage (typically <1 day). Dojo CTF training built in. Hunter collaboration (up to 5 collaborators, reward split). **Start immediately: YES.**
- **Intigriti** (Belgium, EU — "Best Security Company 2026"): public programs open to any registered account. Safe harbor applied on programs. Tiered reward model. Reputation unlocks private invites over time. Requires `X-Intigriti-Username` header or `intigriti-<username>` user-agent on most programs; some require 2FA. **Start immediately: YES.**
- **HackenProof** (Estonia): 400+ programs but heavily crypto/DeFi/web3. Some programs require KYC, reputation points, or even submission fees. Triaged by HackenProof. Better for smart-contract hunters; web-only hunters will find fewer fits. **Start immediately: mostly yes, check per-program gates.**
- **BugBase** (India): India-rooted, banks/fintechs/SaaS. Groww campaigns paid up to $4,500/vuln. Ai+ launched a ₹100 crore device-security bounty (mobile-focused). **Start immediately: YES** — good home-field advantage for Indian targets.
- **Yogosha** (France): private programs only — invite/reputation gated. Not a day-one option; earn reputation elsewhere first.
- ⚠️ **Avoid right now**: Intel (Intigriti program SUSPENDED Sept 2026 — now unpaid VDP) and Grafana (bug bounty shut down — now unpaid VDP). Don't burn recon time there.

---

## 1. intigriti — Bug Bounty Program (Intigriti's own)
- **URL:** https://app.intigriti.com/programs/intigriti/intigriti/detail
- **Paid bounty.** Tiers: Tier 2 €50–€13,337 | Tier 3 €50–€5,000 | Tier 4 up to €1,500 (severity × tier grid; exceptional maxes at €13,337).
- **Scope:** `*.pwn.intigriti.rocks` (Tier 2 wildcard — the PWN test environment), `*.intigriti.me` (Tier 3 wildcard), `https://vpn.intigriti.rocks/*` (Tier 4). Out of scope: `*.intigriti.io`, `*.intigriti.net`, Intercom, HubSpot pages, any CTF/challenge. Subdomain takeover on out-of-scope assets still pays up to €50 if actually taken over.
- **Rules highlights:** Safe harbor applied. Dedicated **PWN test environment over WireGuard VPN — "play around without any restrictions"**; create unlimited researcher accounts at login.pwn.intigriti.rocks. No DoS/brute-force. No disclosure without consent. Validation SLA: exceptional/critical 2 working days (+€25 bonus if they miss it; +€50 "check our fix" bonus). Worst-case scenarios they name: submission-data access, PII disclosure, priv-esc.
- **Focus areas:** Their crown jewels are submission data + user PII; IDOR and priv-esc on the platform.
- **Registration:** Free Intigriti account only. VPN config from your profile.
- **WHY:** A deliberately hackable mirror of a real bounty platform, no fear of breaking prod, explicit permission to go hard — the single best place to practice the exact skills (IDOR, auth, business logic) that pay on every other program.

## 2. FDJ United (Online Betting and Gaming) — YesWeHack
- **URL:** https://yeswehack.com/programs/fdj-united-online-betting-gaming-bug-bounty-program
- **Paid bounty.** Critical tier: Low €150 / Medium €1,000 / High €5,000 / Critical €15,000. High tier: €50 / €150 / €800 / €2,500. ~716 reports.
- **Scope:** 33 scopes, all at Critical asset value: `www.unibet.(com|it|se|co.uk|be|nl|dk|ro|ee|ie|com.au|mt)`, `payment.unibet.*` (same TLDs), `www.mariacasino.(com|se|ee|dk)`, `int.32red.com`, `www.32red.com`, `www.bingo.com`, `(se|fi|uk).bingo.com`, `payment.bingo.com`, `www.ottokasino.com`, `www.storspiller.com`, `www.storspelare.se`, `www.casinohuone.com`, `www.kolikkopelit.com`, `www.vladcazino.ro`, `pci.kindredgroup.com`, plus mobile apps. `/blog/` endpoints on all sites at High tier.
- **Rules highlights:** Test only your own accounts. No automated scanners / heavy traffic. No DoS, no social engineering, no attacking end users. No disclosure without written permission. Same vuln on multiple brands = systemic handling.
- **Focus areas:** They explicitly list: RCE, SQLi, PCI-environment access, account takeover (with/without user interaction), stored/blind XSS, subdomain takeover on main brands, CSRF on sensitive actions.
- **Registration:** Free YesWeHack hunter account.
- **WHY:** Betting platforms are business-logic machines (odds, balances, payouts, coupons) — exactly the `checkout-logic` playbook's home turf. 33 scopes with only 716 reports = thin coverage per brand.

## 3. Superbank — YesWeHack
- **URL:** https://yeswehack.com/programs/superbank-public-bug-bounty-program
- **Paid bounty.** High tier: $150 / $400 / $1,000 / $2,000. Medium tier: $100 / $300 / $800 / $1,000. Only **123 reports**.
- **Scope (6):** iOS app, Android app (`id.co.bankfama.android`), `api.super-id.net` (High), `ecosystem-experience.super-id.net`, `superbank.id` (Medium), `chatbot.super-id.net` **AI chatbot** (Medium).
- **Rules highlights:** No automated scanners/heavy traffic, no DoS, no user-data exfiltration. Self-registration allowed — use your YesWeHack email alias for account creation.
- **Focus areas:** Standard web/API: SQLi, XSS, RCE, IDOR, priv-esc, auth bypass, business logic, LFI/RFI/XXE/SSRF.
- **Registration:** Free YesWeHack account; self-register in the apps.
- **WHY:** Lowest report count of any paid YWH program here — the fewest hunters have looked. API + an AI chatbot scope (prompt-injection-adjacent logic) give two under-hunted surfaces.

## 4. Moneybox — YesWeHack
- **URL:** https://yeswehack.com/programs/moneybox-bug-bounty
- **Paid bounty.** Critical tier: €50 / €500 / €1,000 / €2,000. High tier: €100 / €300 / €800 / €1,200. Only **137 reports**.
- **Scope (6):** `api.moneyboxapp.com` (Critical), **`admin.moneyboxapp.org` (Critical)**, **`admin-roundups.moneyboxapp.org` (Critical)**, `sycamore.moneyboxapp.org` (Critical), iOS + Android apps (High). Explicit out-of-scope: the `/investment/payments/GetGiftUser/{code}` endpoint behavior (by design).
- **Rules highlights:** Must append `bugbounty-0421` to your User-Agent or risk being blocked. No scanners/heavy traffic, no DoS, no user data exfil. Use YWH email aliases for test accounts.
- **Focus areas:** Standard web/API list; IDOR and auth bypass on a savings/investment API and three admin panels.
- **Registration:** Free YesWeHack account; self-register.
- **WHY:** Three separate admin panels at Critical tier is rare — admin interfaces are classic IDOR/broken-access-control territory, and 137 reports means barely anyone has tried.

## 5. Kiteworks — YesWeHack
- **URL:** https://yeswehack.com/programs/kiteworks-public-bug-bounty-program-1
- **Paid bounty.** Grid by asset value × CVSS: Critical asset / Critical CVSS = **$50,000**; High asset Critical = $25,000. Plus a **$25,000 "Crown Jewels Heist" bonus** for unauthenticated RCE-as-root on the Kiteworks Core appliance (CVSS PR:N). ~177 reports. **Launched September 2026 — brand new.**
- **Scope (12):** Dedicated hunting environment at `ywh-kw-public.bounty.kiteworks.dev` — Kiteworks Core node, Email Protection Gateway, Advanced Forms, Managed File Transfer (Apache Airflow-based), user endpoints. All activity monitored.
- **Rules highlights:** No DoS, no touching out-of-scope boxes, no changing admin IP restrictions/roles, no deleting accounts. No disclosure at all (even partial). XSS needs real impact PoC (alert(1) insufficient). Admin-privilege vulns are downgraded via CVSS environmental metrics (MS:U) — only cross-tenant/cross-node counts as scope change.
- **Focus areas:** Explicitly: privilege/role escalation, RCE, XSS, LDAP injection.
- **Registration:** Free YesWeHack account.
- **WHY:** Newest program on the list — fresh attack surface, highest ceiling ($50k), and the rules read like a roadmap of what they fear (RCE, priv-esc). Advanced level, but the docs they link (user roles, app usage) are recon gold.

## 6. Doctolib — YesWeHack
- **URL:** https://yeswehack.com/programs/doctolib-public-bug-bounty-program
- **Paid bounty.** Grid: Critical asset / Critical = **€50,000**; Medium asset Critical = €20,000; plus **€50,000 special scenarios**: "game over" (RCE on the Rails monolith able to read env var `SECURITY_BUG_BOUNTY_DOCTOLIB_IS_PWN`) and "one shot" (dump a whole doctor's patient base in few requests). ~1,780 reports.
- **Scope (9):** `www.doctolib.(fr|de|it)`, `pro.doctolib.(fr|de|it)` (Medium), `*.doctolib.(fr|de|it|com|net)` (Low), iOS/Android apps, `*.siilo.com` (Medium). Government-ID-verified pro features out of scope.
- **Rules highlights:** Healthcare — do NOT touch real patient/care-team data; **they provide a fake doctor ("Dr Albertus Boulenfunkierchenblah", booking code 42) and require fake test accounts**. Use `BugBounty/42 (YWH)` user-agent; max 10 req/sec; no disclosure. Identity brute-force explicitly not rewarded.
- **Focus areas:** Their grid rewards by data typology — PII types 1–5, with health data (types 4–5) rating Critical. IDOR that dumps patient data is the jackpot.
- **Registration:** Free YesWeHack account + fake test account.
- **WHY:** They hand you a test doctor and tell you exactly where the crown jewels are (patient data sync flows). IDOR/batch-export bugs are the highest-paid pattern here — matches the `idor` playbook directly.

## 7. CoinDCX — YesWeHack
- **URL:** https://yeswehack.com/programs/coindcx-bug-bounty-program
- **Paid bounty.** Flat grid (all assets Critical value): Low $100 / Medium $300 / High $1,000 / Critical **$2,000**. ~305 reports on main program (three related CoinDCX programs exist).
- **Scope:** `*.coindcx.com` **wildcard** (Critical), `api.coindcx.com` (Critical), Android + iOS apps (Critical). Out of scope: blog, info., otcdesk., careers. subdomains, Zendesk/third parties, WordPress CMS sites.
- **Rules highlights:** No automated scanners/heavy traffic, no DoS. Don't alter compromised accounts; don't use compromised accounts to hunt post-auth bugs (ineligible). Exposed credentials: verify validity only, don't dig. No disclosure.
- **Focus areas:** They explicitly want: Web3 issues, accessing other users' accounts/financial info/wallets, withdrawing funds as a sub-account, auth & authorization, SSL pinning bypass.
- **Registration:** Free YesWeHack account.
- **WHY:** India's largest crypto exchange — home turf, INR-friendly payouts, <1-day first response, and a wildcard scope. Exchange account/wallet logic is prime IDOR/priv-esc territory, and the "sub-account withdrawal" hint points straight at business-logic bugs.

## 8. TrueLayer — Intigriti
- **URL:** https://app.intigriti.com/programs/truelayer/truelayer/detail
- **Paid bounty.** Tier 1: €175–€6,000 | Tier 2: €125–€4,000 | Tier 3: €75–€2,250 (severity × tier).
- **Scope:** Tiered Open Banking / PSD2 API assets (API-first fintech).
- **Rules highlights:** Automated tooling explicitly allowed at **max 10 requests/sec**. Must send `X-Intigriti-Username: {username}` header. Standard Intigriti code of conduct + no disclosure without consent.
- **Focus areas:** Payment initiation + financial-data APIs — the classic IDOR / broken object-level authorization hunting ground.
- **Registration:** Free Intigriti account.
- **WHY:** An API-only fintech that *permits* automation at a documented rate — rare and ideal for systematic endpoint enumeration (the hunter's `expose` + manual IDOR playbook). Open Banking means money-movement logic.

## 9. BMW Group — Intigriti
- **URL:** https://app.intigriti.com/programs/bmw/bmwgroup/detail
- **Paid bounty.** Tier 1: €250–€6,000 | Tier 2: €150–€3,000.
- **Scope:** Tier 1–2 assets across BMW, MINI, Rolls-Royce, BMW Motorrad web properties + financial services.
- **Rules highlights:** Max 2 req/sec automated tooling. `X-Intigriti-Username` header required. No disclosure without written consent (incl. YouTube/Vimeo PoCs).
- **Focus areas:** Customer data + vehicle/financial services systems.
- **Registration:** Free Intigriti account.
- **WHY:** Connected-car and owner-portal scope rewards the same auth/session/IDOR skills as every other web program, with a €6k ceiling — and it's the one program on this list aligned with a car enthusiast's domain knowledge.

## 10. Oda — Intigriti
- **URL:** https://app.intigriti.com/programs/oda/oda/detail
- **Paid bounty.** Tier 2: €100–€4,000 | Tier 3: €75–€2,500.
- **Scope:** `*.oda.com` **wildcard** (Tier 2), `*.prod.nube.tech` wildcard (Tier 3), plus iOS/Android apps.
- **Rules highlights:** Safe harbor applied. Max 5 req/sec; append `intigriti-<username>` to user-agent (also whitelists you past their Fastly WAF). No automated scanners per their note — "be creative and do it yourself" (manual testing culture). Chat widget is third-party and out of scope.
- **Focus areas:** E-commerce: checkout, pricing, account, order flows.
- **Registration:** Free Intigriti account.
- **WHY:** A wildcard e-commerce scope with safe harbor and WAF-bypass instructions handed to you — checkout/pricing logic bugs (`checkout-logic` playbook) are the natural target, and the anti-scanner stance means manual hunters face less competition.

## 11. Personio — Intigriti
- **URL:** https://app.intigriti.com/programs/personio/personio/detail
- **Paid bounty.** Tier 2: €175–€5,000 | Tier 3: €50–€2,000.
- **Scope:** Tier 2–3 assets of Personio's HR SaaS platform (Europe's leading HR software for SMEs).
- **Rules highlights:** Max 2 req/sec automated tooling. `X-Intigriti-Username: {{username}}` header required. Standard Intigriti conduct + no disclosure without consent.
- **Focus areas:** HR platform holding employee PII across thousands of companies — IDOR, tenant isolation, role-based access.
- **Registration:** Free Intigriti account.
- **WHY:** Multi-tenant HR SaaS is IDOR-by-design hunting: every employee record, document, and payroll object is a potential broken-access-control finding. Clear tier grid, respectable €5k ceiling.

## 12. Suivo — Intigriti
- **URL:** https://app.intigriti.com/programs/suivo/suivoweb/detail
- **Paid bounty.** Tier 2: up to **€2,000**.
- **Scope:** Suivo web platform (vehicle-tracking SaaS: real-time tracking, analytics, fleet management). **You test their staging environment** — a copy of production that gets features weeks early.
- **Rules highlights:** Safe harbor applied. Max 5 req/sec. **No automatic scanners** — manual testing only, they say so explicitly. Detailed reporting guidelines (attack scenario required, quality over quantity).
- **Focus areas:** RCE and anything impacting tracked vehicle/fleet data.
- **Registration:** Free Intigriti account.
- **WHY:** Testing staging instead of prod removes the fear of breaking things — ideal low-risk reps for a developing hunter, and pre-release features are historically under-tested.

---

## Honorable mentions (listing-level data, worth a look)
- **Infomaniak** (YWH): €100–€7,000, **51 scopes**, <1-day response — huge scope but 3,679 reports (heavily hunted).
- **Swiss Post** (YWH): €50–€10,000, 9 scopes, 2,707 reports — solid EU target, crowded.
- **Swiss Post E-Voting** (YWH): up to **€230,000** — the highest ceiling on YesWeHack, but extremely advanced scope.
- **Telenor Sweden** (YWH): €50–€6,000, 24 scopes, 1,962 reports — telecom, big scope, crowded.
- **Pine Labs** (YWH): $0–$1,000, **22 scopes** — Indian fintech (payments), lower ceiling but home turf.
- **DANA Indonesia / PT GoTo Gojek** (YWH): $0–$5,000, large Asian fintech scopes.
- **TeamViewer** (YWH): €100–€10,000 — remote-access software, high value per finding.
- **HackenProof web3**: GMGN Web & Mobile (up to $1,000,000), 1inch Aqua (up to $100,000) — only if you go the smart-contract route later.

## Dead ends — do not spend recon time here
- **Intel** (Intigriti): paid program SUSPENDED Sept 2026, now unpaid VDP.
- **Grafana** (Intigriti): bug bounty shut down, now unpaid VDP.
- **Yogosha**: private-only, invite-gated — revisit after building reputation.

---

## Top 3 picks for a skilled beginner-to-intermediate web hunter

1. **intigriti's own program (Intigriti)** — Unrestricted PWN test environment over VPN: you can attack freely with zero fear of breaking production, safe harbor, €50–€13,337 payouts, and the target IS a bounty platform (IDOR/priv-esc/PII — the exact skills that transfer everywhere). Train here, earn here.
2. **FDJ United (YesWeHack)** — 33 betting-brand scopes at Critical tier up to €15,000; betting = business-logic bugs (balances, odds, payouts, coupons); only 716 reports across 33 scopes means thin coverage. The `checkout-logic` and `client-side-auth` playbooks were built for exactly this.
3. **Superbank (YesWeHack)** — 123 reports is the lowest hunter density of any paid program found; self-registration; API + web + an AI chatbot in scope. Small enough to map fully, fresh enough that low-hanging fruit may remain.

**Registration order (all free, all immediate):** YesWeHack hunter account → Intigriti account → BugBase account (home-turf Indian programs) → HackenProof account (for later). No reputation needed anywhere for the public programs above.
