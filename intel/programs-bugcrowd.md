# Bugcrowd Programs — In-Depth Research
**Researched:** 2026-09-26 | **Researcher:** shiva92 (Bugcrowd account) | **Method:** Bugcrowd engagement briefs + bountyhunte.rs scope/reward tracking + ROI dataset (207 Bugcrowd programs)

> Verify scope, rewards, and rules on the live program brief before testing. Programs change scope frequently.

## Quick-reference table

| # | Program | Rewards | Top targets | Why start here |
|---|---------|---------|-------------|----------------|
| 1 | Okta | $100–$75k (+$500k RCE bonus) | Researcher tenants, Workflows, MFA, browser ext | Tenants + creds provided; identity = highest-value web class |
| 2 | Auth0 | $100–$50k | Wildcard test tenant, OpenFGA, SDKs, jwt.io | 3 users × 3 tenants; auth bugs = your playbooks |
| 3 | Zendesk | $100–$50k | Zendesk AI, Suite, marketplace apps, mobile | AI surface new + explicitly in scope |
| 4 | Aiven | $50–$25k (verify) | Managed DB services, console/api, GitHub | Brief tells you where dupes aren't; cross-account = P1 |
| 5 | Pinterest | P1 $10–25k / P2 $5–8k / P3 $1–3k / P4 $200–500 | api.pinterest.com, web, mobile, AI features | Exact grid; AI features low-dupe; paying Sep 2026 |
| 6 | Chime | $50–$20k (verify) | Web, mobile, Salt Labs, QA staging | GraphQL + money-movement logic; QA env for non-US |
| 7 | Fivetran | up to $15k (P1–P3 only) | *.fivetran.com, Connector SDK | Data-pipeline access class; P4s pay nothing — skip them |
| 8 | Atlassian | $200–$10k | Rovo AI, Forge, MCP server, Jira/Confluence | AI-agent vuln menu published by the vendor itself |
| 9 | Keeper | $300–$20k | Web Vault, Admin Console, SSO/SAML, PAM | $20k ceiling; strictness scares off low-effort hunters |
| 10 | Canva | $200–$15k | Editor, Connect API, Apps SDK, *.canva.com | Collaboration authz everywhere; free multi-accounts |
| 11 | T-Mobile | P1 $133.7k+ special / $55k core / $20k suppl | account/API, DIGITS, T-Life | Highest advertised P1s on this list |
| 12 | HotDoc | $50–$8k (verify) | Web + mobile apps | Healthcare PII; low hunter traffic |
| 13 | Bullish | up to $15k (verify status) | *.bullish.com, simnext test env | Subdomain takeover = explicit focus |
| 14 | Sophos | $100–$80k | Sophos Central (prod), Firewall, endpoints | Central = multi-tenant SaaS; $80k special targets |
| 15 | OneTrust | $300–$6.5k | pentest-app.onetrust.com staging | Admin creds + staging; DSR workflows = IDOR heaven |

**VDPs (no cash, reputation + practice):** NASA, USAGM, VA, State of California, DHS — details in the VDP section below. **Do NOT start:** Kiteworks (closed), Cash App (ends 2026-09-30) — see Appendix A.

---

## 1. Okta — https://bugcrowd.com/engagements/okta
- **Paid:** Yes | **Rewards:** $100 – $75,000 (plus limited-time bonus up to **$500,000** for RCE/SQLi in in-scope products)
- **Type:** Managed engagement
- **In scope (21 targets):** researcher-provisioned tenants — `bugcrowd-pam-###.oktapreview.com`, `bugcrowd-pam-###.pam.oktapreview.com`, `bugcrowd-pam-###.workflows.oktapreview.com`, `bugcrowd-pam-###.at.oktapreview.com`, `bugcrowd-pam-###-admin.oktapreview.com`, `personal.trexcloud.com` (Okta Personal), `app.scaleft.com` (Advanced Server Access), `support.okta.com`, Okta Verify iOS/Android/macOS/Windows, Desktop MFA, on-prem agents (AD/LDAP/RDP/IWA), browser plugin
- **Out of scope:** `*.okta.com`, `*.trexcloud.com`, `login.okta.com`, `developer.okta.com`, `trust.okta.com`, `www.okta.com`, backend non-app infra, network-layer issues, anything not explicitly listed
- **Test accounts:** YES — click "Get Credentials" for 2 sets; Okta Personal via @bugcrowdninja.com signup
- **Focus areas (explicit):** SAML/OAuth/OIDC protocol vulns, XXE in XML intake, cross-org/multi-tenancy vulns, privilege escalation, SSRF via Workflows Flo cards, sandbox escape via API Endpoint & Return Raw, Okta Personal crypto, MFA bypass (strict criteria), browser plugin compromise
- **Rules highlights:** NO automation on Workflows (immediate removal); NO AI-generated/low-effort reports (removal); theoretical issues out of scope — full PoC required; if you pop a server, do NOT pivot — report; chaining encouraged; **no public disclosure** (explicit permission required)
- **Signal:** accepted submissions on workflows.oktapreview.com + support.okta.com as recently as Sep 2026 — program is actively paying
- **WHY:** Identity is the highest-value web target class; they hand you tenants + creds, publish exactly what they want (SSRF, cross-tenant, protocol bugs), and pay up to $75k ($500k bonus for RCE). Your oauth-misconfig and client-side-auth playbooks map directly.

## 2. Auth0 by Okta — https://bugcrowd.com/engagements/auth0-okta
- **Paid:** Yes | **Rewards:** $100 – $50,000 (past bonus: P1 3x, P2 2x, P3 1.5x multipliers on focus areas)
- **Type:** Managed engagement
- **In scope:** researcher tenant `manage.cic-bug-bounty.auth0app.com` + wildcard `*.cic-bug-bounty.auth0app.com`; `marketplace.auth0.com`; OpenFGA (`dashboard.fga.dev`, `api.us1.fga.dev`, `customers.us1.fga.dev`, `play.fga.dev`); Auth0 SDKs on GitHub (auth0.js, lock, spa-js, nextjs-auth0, etc.); `jwt.io`, `samltool.io`, `webauthn.me`, `openidconnect.net`; Auth0 Guardian mobile apps
- **Out of scope:** `auth0.auth0.com`, `manage.auth0.com` (production — instant OOS), customer instances, abandoned domains, login-page XSS, race-condition limit bypasses
- **Test accounts:** YES — "Get Credentials" gives 3 users × 3 tenants
- **Focus areas (explicit):** OAuth 2.0 / OIDC / SAML identity protocol vulns, auth bypass, PII exfiltration, cross-tenant privilege escalation
- **Rules highlights:** automated scanning = immediate BAN; Burp Intruder ≤ 5 req/s; no DoS; no AI-generated reports; private program since 2019 — old bugs are dupes, hunt new features; no pivot on server access
- **WHY:** Same identity goldmine as Okta with a wildcard test tenant and 3 credential sets. Auth bugs are your playbook's home turf; the "no scanners" rule thins the automated competition.

## 3. Zendesk — https://bugcrowd.com/engagements/zendesk
- **Paid:** Yes | **Rewards:** $100 – $50,000
- **Type:** Managed engagement
- **In scope:** Zendesk AI, Zendesk Front End, Zendesk Marketplace Apps (built by Zendesk), Zendesk Mobile Applications, Zendesk Public Repositories, Zendesk Suite
- **Out of scope:** `support.zendesk.com`, `www.zendesk.com`, `*.zdassets.com`, Zendesk for Sales/Sell, supply chain/vendors, known CVEs in third-party libs
- **Focus areas:** AI features (Zendesk AI explicitly in scope — prompt injection / data exfiltration via AI is fresh territory), marketplace apps, mobile
- **WHY:** $50k ceiling on a SaaS suite where the AI surface is new and explicitly in scope. AI-feature bugs have low dupe rates right now.

## 4. Aiven — https://bugcrowd.com/engagements/aiven-mbb-og
- **Paid:** Yes | **Rewards:** historically $50 – $25,000 (verify current range on the brief — bountyhunte.rs logged the advertised max being removed at one point)
- **In scope:** `console.aiven.io`, `api.aiven.io`, `aiven.io`, `regatta.aiven.io` (internal app — unauthorized access only), GitHub orgs `Aiven` + `Aiven-Open`, managed DB services (PostgreSQL, MySQL, OpenSearch, Grafana, Kafka/Connect/MirrorMaker, ClickHouse, Valkey, Metrics), sandbox challenge host, third-party dependency versions (capped payout tier)
- **Out of scope:** most other subdomains (third-party hosted — check hosting before testing), customer services you didn't create, test environment, `github.com/Aiven-Labs`, partner interfaces
- **Test accounts:** use free tier + trial credits; extra credits granted on request via the program
- **Focus areas (explicit):** MANAGED DATABASE APPS over the website ("website vulns are frequently reported and heavily duped; most DB-app issues are unique"); cross-account access to other customers' services; orchestration-plane/host security; chained goals: credential theft → internal network services → cross-account access
- **Rules highlights:** @bugcrowdninja.com emails only; only your own accounts/services; no social engineering; no DoS; version-based CVE reports need a working PoC on Aiven infra (they mitigate many upstream CVEs); console API uses `aivenv1` Authorization header, not cookies — copying your own header is not a bug
- **WHY:** They literally tell you where the dupes aren't (managed DB services) and what pays most (cross-account access). Multi-tenant IDOR/priv-esc is your playbook's sweet spot, and the brief even blesses chaining.

## 5. Pinterest — https://bugcrowd.com/engagements/pinterest
- **Paid:** Yes | **Rewards:** $200 – $25,000 — P1: $10,000–$25,000 | P2: $5,000–$8,000 | P3: $1,000–$3,000 | P4: $200–$500
- **In scope:** `api.pinterest.com`, `*.pinterest.com` web apps, iOS/Android/Lite apps, Chrome/Edge/Firefox/Safari extensions, non-forked `github.com/pinterest` open source, `shffls.com`, Shuffles apps
- **Out of scope:** unlisted properties (no payout, hall-of-fame only), scanner output, rate-limit bypass without impact, DDoS, vuln libs without demonstrable impact
- **Test accounts:** create business account + developer enrollment with @bugcrowdninja.com for API testing
- **Focus areas (explicit):** RCE, significant auth bypass, critical authz bugs, CSRF on critical actions, XSS (not self), PII exfil; Private Profiles, Pinterest Ads; NEW: Pinterest Assistant (AI), AI board upgrades, GenAI interest settings
- **Safe harbor:** explicit CFAA/DMCA authorization
- **Signal:** submissions accepted Sep 2026 on api.pinterest.com and open-source targets — actively paying
- **Disclosure:** explicit permission required; open to coordinated disclosure for P1–P4
- **WHY:** Published P1–P4 ranges (rare transparency), huge API + extension surface, and fresh AI features with low dupe rates. The wildcard `*.pinterest.com` gives you real subdomain recon room.

## 6. Chime — https://bugcrowd.com/engagements/chime
- **Paid:** Yes | **Rewards:** $50 – $20,000 — P1 primary: $10,000–$20,000 | P1 secondary: $4,500–$7,000 (past promo doubled P1s to $20k–$40k — watch for repeat promos)
- **In scope:** "All Chime Assets" — `*.chime.com`, `*.chimepayments.com`, `*.1debit.com`, `*.chimecard.com`, `*.chmfin.com`, `*.chimebank.com`, iOS/Android apps, Salt Labs (`*.saltlabs.com`, apps, staging)
- **Out of scope:** long third-party list (email infra, status pages, help, careers, etc.), `chime.financial`, `chimescholars.org`, non-Chime-owned assets
- **Test accounts:** ⚠️ production = US researchers only (needs SSN). **Non-US: use STAGING** — enroll at `member-qa.chime.com/enroll`, login at `app-qa.chime.com`, test SSN patterns (ending 1234/1235), VoIP numbers OK on QA. Salt Labs production is open to ALL researchers (US phone number only).
- **Focus areas (explicit):** GraphQL, mobile, member data, money movement between accounts/members; "business logic and API testing are especially valuable… can result in higher bounty payouts"
- **Safe harbor:** explicit CFAA/DMCA
- **Signal:** submissions accepted Sep 2026 — active
- **WHY:** They explicitly pay MORE for business-logic/API bugs (your checkout-logic playbook), GraphQL is named, and the staging env is open to non-US researchers. Money-movement logic = high impact.

## 7. Fivetran — https://bugcrowd.com/engagements/fivetran-mbb-og
- **Paid:** Yes | **Rewards:** points – $15,000, **P1–P3 only (P4/P5 excluded — no payout)**
- **In scope:** `*.fivetran.com` (Fivetran products); unlisted-but-owned accepted on review
- **Out of scope:** internal/staging/dev, `*.db.fivetran.com`, shop/status/support/trust/community-stage subdomains, HVR products, third-party providers; CTF target paused Sep 2026
- **Test accounts:** signup at fivetran.com/signup with @bugcrowdninja.com; add `X-Bug-Bounty:<your-username>` header to all traffic
- **Focus areas (explicit):** access to pipeline data, account authentication, Connector SDK
- **Rules highlights:** no DoS/rate-limit testing, no brute force, no social engineering, no leaked-credential reports for cash (points only), N-days in scope 30 days after public release
- **Disclosure:** not allowed
- **WHY:** Data-pipeline access = juicy impact class; the required `X-Bug-Bounty` header shows they triage researcher traffic carefully. Only chase P1–P3 here — P4s pay nothing.

## 8. Atlassian — https://bugcrowd.com/engagements/atlassian
- **Paid:** Yes | **Rewards:** $200 – $10,000
- **In scope:** Atlassian Guard, Admin (`admin.atlassian.com`), Identity (`id.atlassian.com`), Bitbucket Cloud, Confluence Cloud, Jira Cloud (Software/Service Management/Work Mgmt), mobile apps, Loom, Compass, Forge platform + GraphQL API, `mcp.atlassian.com` (MCP server), `marketplace.atlassian.com`, `*.atlastunnel.com`; any `*.atlassian.com`/`*.atl-paas.net` exploitable directly from your `*.atlassian.net` instance
- **Out of scope:** internal/dev services, marketplace 1st/3rd-party apps (separate `atlassianapps` program), shop.atlassian.com, HipChat/Stride (dead), enumeration/info-gathering (collaborative product — not interesting), GraphQL hydration issues, trivial jailbreaks
- **Test accounts:** create `bugbounty-test-<your-bugcrowd-name>.atlassian.net` instances; trial Rovo via support docs
- **Focus areas — Rovo AI is formally in scope:** Rovo Chat/Search/Connectors/Studio/Agents/Forge Agents/browser ext/Slack app; accepted classes: broken connector auth, token/secret leakage in auth flows, 3P data poisoning, permission drift (restricted doc titles/snippets surfacing in search), cross-product AI leaking restricted content, agent authz bypass, PII via AI; Forge: sandbox escapes, SSRF, IDOR, XSS in UI Kit
- **WHY:** AI-agent security is the lowest-dupe surface in bounty right now and Atlassian wrote you a menu of exactly which AI bugs they pay for. Your batch-C intel (prompt injection, agent authz, Rovo-style data leaks) maps 1:1.

## 9. Keeper Security — https://bugcrowd.com/engagements/keepersecurity
- **Paid:** Yes | **Rewards:** $300 – $20,000 — **P1/P2-level impact expected; self-only findings pay nothing**
- **In scope:** Web Vault (US/EU/AU/CA/JP/GovCloud), Admin Console, Enterprise, KeeperPAM, Connection Manager, Secrets Manager SDK, Commander CLI, SSO Connect Cloud/On-Prem (SAML), AD/LDAP Bridge, browser extensions, desktop/mobile apps, KeeperChat, checkout pages
- **Out of scope:** anything unlisted; self-XSS/self-only impact; local-compromise prerequisites; scanner-only output; AI slop (explicit disqualification); theoretical findings
- **Test accounts:** 30-day personal trial + 14-day enterprise trial; @bugcrowdninja.com signup; debugging: `enableNetworkLog()` in Web Vault devtools (AES-over-TLS otherwise opaque)
- **Focus areas (explicit):** auth bypass, device-approval bypass, RCE, cross-tenant/cross-account/cross-region data access, priv esc, crypto/key-management flaws, SSO
- **Rules highlights:** must demonstrate impact against ANOTHER user/tenant/system — own-account-only = ineligible; detailed exploit scenario + CVSS required; manual testing encouraged on production
- **WHY:** $20k ceiling on a password manager where cross-tenant vault access is the crown jewel. SSO/SAML + crypto focus fits your playbooks; the strictness scares off low-effort hunters.

## 10. Canva — https://bugcrowd.com/engagements/canva
- **Paid:** Yes | **Rewards:** $200 – $15,000
- **In scope:** `www.canva.com` (Editor), Developer Platform (`api.canva.com`, developer portal, Apps SDK sandbox), `*.canva.com`, `*.canva-apps.com`, `*.canva.tech`, `*.canva.cn` (China — network-config findings pay NOTHING), Canva-built marketplace apps/integrations (Canva for ChatGPT, Canva for Slack), native apps (desktop/mobile/Chrome ext), leaked-credentials reports
- **Out of scope:** third-party-built integrations (points only); BigMarker; leaked credentials from malware/OSINT/dark-web dumps (informational only — do NOT test suspected credentials); recent legacy-auth patterns being phased out
- **Test accounts:** free Canva account; developer portal signup for API/SDK testing
- **Focus areas (explicit):** Editor: server-side vulns, broken auth (SSO/social/MFA), broken authz (IDOR on other users' designs/PII/API leakage), content injection; Dev platform: IDOR on other devs' API keys/apps, SDK sandbox violations; infra: AWS/Cloudflare misconfigs with demonstrated impact
- **Rules highlights:** complete written PoC required (description + repro steps + URLs + screenshots); ethical testing; third-party provider bugs rarely pay
- **Disclosure:** verify on live brief (not captured in extraction)
- **WHY:** Design-sharing + teams/orgs = collaboration authz bugs everywhere; the Connect API/SDK focus is an explicit invitation to hunt IDOR. Free accounts make multi-account authz testing trivial.

## 11. T-Mobile — https://bugcrowd.com/engagements/t-mobile
- **Paid:** Yes | **Rewards:** Special Target P1 $133,700+; Core P1 $55,000 / P2 $35,000; Supplemental P1 $20,000 / P2 $12,000 (P3/P4 bands — verify on live brief)
- **In scope:** Core web/API: `t-mobile.com`, `account.t-mobile.com`, `*.api.t-mobile.com`, `metrobyt-mobile.com`, `sprint.com`, `tfb.t-mobile.com`, `devedge.t-mobile.com`, `tess.service-now.com`, `digits.t-mobile.com`, `account.business.t-mobile.com`; Core mobile: T-Life (iOS/Android), DIGITS; Supplemental: `*.t-mobile.com`, `*.sprint.com`, `*.uscc.net`/`*.uscellular.com`, assurancewireless.com, vistarmedia/cortexpowered/blis/adstruc ad-tech domains
- **Out of scope:** T&P flag servers (temporarily out); anything outside listed assets
- **Test accounts:** free signup where available; authorized testing MSISDN `404-200-7239` for cellular-auth scenarios
- **Focus areas (explicit):** Special targets: cellular-network auth bypass (SIM/eSIM/MSISDN trust), self-registering an account in T-Mobile's Microsoft Entra ID tenant ($133k+ each); Core: account/billing/auth/API/customer workflows
- **WHY:** The highest publicly advertised P1s in this entire list. Realistic path: Core/Supplemental web + API targets (account, billing, DIGITS) with your IDOR/auth playbooks; the special targets are moonshots to keep in your back pocket. US-centric — web assets testable from anywhere.

## 12. HotDoc — https://bugcrowd.com/engagements/hotdoc
- **Paid:** Yes | **Rewards:** $50 – $8,000 (historical advertised range; exact tier grid — verify on live brief, full brief text did not render in extraction)
- **In scope:** web and mobile applications (per program intro); exact target list — verify on live brief
- **Test accounts:** create own accounts
- **WHY:** Australia's leading patient-engagement platform (8,000+ GPs) = healthcare data = high-impact IDOR/PII class; smaller Australian program gets less hunter traffic than US giants.

## 13. Bullish — https://bugcrowd.com/engagements/bullish
- **Paid:** Yes | **Rewards:** historical ceiling up to $15,000; exact grid — verify on live brief. **Status:** brief shows a past maintenance pause notice and "no recent activity" — confirm the program is actively accepting submissions before investing time
- **In scope:** `bullish.com`, `investor.bullish.com`, `*.bullish.com` (web + API), `simnext.bullish-test.com`; Bullish corporate sites/infra where unobtrusive
- **Out of scope:** the Bullish EXCHANGE webapp and APIs (separate program); DoS, open redirects, phishing sites (welcome but unpaid), outdated-system-only issues
- **Test accounts:** free signup where available
- **Focus areas (explicit):** subdomain takeovers are "of particular concern" (prove with a `/yourusername.html` file); technical vulnerabilities in software/websites only
- **Safe harbor:** yes — authorized, anti-circumvention exempt
- **Disclosure:** requires explicit permission via the disclosure-request option
- **WHY:** Subdomain takeover as an explicit focus + Cloudflare-fronted wildcards = a clean recon-to-takeover pipeline with your subfinder/dnsx/httpx stack.

## 14. Sophos — https://bugcrowd.com/engagements/sophos
- **Paid:** Yes | **Rewards:** $100 – $80,000 (normal grid); special targets pay up to $80k for zero-click RCE
- **In scope:** Sophos Central (production `central.sophos.com`), Intercept X Endpoint (Win/Mac/Linux), mobile, Sophos Firewall (XG/XGS), NDR appliances, other Sophos appliances, Sophos IT infra (`*.sophos.com`), catch-all "any other Sophos product/service"
- **Out of scope:** community.sophos.com, Cyberoam, public service desk, SPF/DKIM/DMARC, EAP versions, DoS against Central (explicitly prohibited), scanner-output-only reports, security-feature bypass/false negatives
- **Test accounts:** fresh trial versions; email MUST contain `bugcrowdninja` (e.g. `you+bugcrowdninja@gmail.com`); reproducible only on fully patched latest releases
- **Focus areas (special high-payout targets):** zero-click remote RCE in Endpoint Protection at Admin+ with no user interaction ($80k ceiling); Sophos Central large-scale data breach / zero-touch super-admin ATO / AWS IAM compromise; Firewall pre-auth RCE as root on WAN interface
- **Disclosure:** allowed only after coordinating with Sophos — let them fix + disclose first (incl. CVE), customers get 30 days to patch before any publication
- **WHY:** The Sophos Central web target is beginner-intermediate-friendly while the $80k special targets give the ceiling of a private program. Central = multi-tenant SaaS → your IDOR/SSO/priv-esc playbooks apply; huge catch-all scope means one account tests everything.

## 15. OneTrust — https://bugcrowd.com/engagements/onetrust
- **Paid:** Yes | **Rewards:** $300 – $6,500
- **In scope:** ONLY `pentest-app.onetrust.com` staging is payout-eligible; plus `*.onetrust.com`, `*.convercent.com`, `*.dataguidance.com`, `app.vendorpedia.com`, `*.preferencechoice.com`, `*.redacted.ai`, `*.cookiepro.com`, `*.cookielaw.org`, `*.onetrustpro.com`, `*.privacyconnect.com`, and regional domains — any unlisted domain is out
- **Out of scope:** XSS when sanitization disabled, CSRF, rate limiting, tinyMCE vulns, auth issues without FULL Site Admin escalation, host-header without user-data proof, outdated libs, clickjacking on non-sensitive pages; submissions from non-staging environments pay NOTHING
- **Test accounts:** admin-level credential from the brief's retrieve-credential section (forgot-password flow); create multiple accounts of varying privilege levels for testing
- **Focus areas (explicit):** data exfiltration; Consumer Rights Portal / Data Subject Requests (webforms + workflows); Integrations module (reaching customer environments and pulling customer data/metadata); public exposure of API keys/sensitive info (recently confirmed in scope)
- **Safe harbor:** full — CFAA-authorized, DMCA-exempt, ToS restrictions waived for research
- **Disclosure:** NOT allowed
- **Activity:** accepted submissions on 2026-09-18 and 2026-09-21; staging updated to version 202510.1.0 — actively triaged
- **WHY:** Admin creds + dedicated staging = test freely without fear of breaking production. DSR webforms/workflows are IDOR heaven and "must demonstrate full Site Admin escalation" is exactly the playbook you have.

---

## Appendix A — Status warnings: DO NOT START these on Bugcrowd

### Kiteworks — CLOSED to new submissions
**Kiteworks brief (moved here 2026-09-26):**
- **Paid:** Yes | **Rewards:** $250 – $25,000
- **In scope:** dedicated test env `kw-bug-bounty-pub.bounty.kiteworks.dev` (exact target names redacted publicly — read the brief logged in); file-sharing web app (Flask/Linux) + API
- **Out of scope:** anything not listed (strict); hypothetical flaws without PoC; unvalidated scanner output; open ports without PoC; self-XSS; unchained open redirects; clickjacking; missing headers/cookie flags; rate-limit issues; subdomain takeover
- **Test accounts:** YES — 4 provisioned profiles (Standard, Restricted, Recipient, Custom) via @bugcrowdninja.com plus-addressing
- **Safe harbor:** explicit CFAA/DMCA authorization statement in the brief
- **Signal:** program re-opened July 2026 after a pause; submissions accepted July 2026 — active again
- **WHY:** File-sharing = file upload attack surface (your ssrf playbook: parser differentials, content-type tricks). 4 test profiles are perfect for IDOR/cross-role testing. $250 minimum means even mediums pay.

- **STATUS (verified 2026-09-26):** the program's own brief announcement says the Bugcrowd program is **closed to new submissions** — vulnerabilities now go to security.kiteworks.com. Do not submit here.

### Cash App — program ends 2026-09-30
**Cash App brief (moved here 2026-09-26):**
- **Paid:** Yes | **Rewards:** $100 – $18,000 (takeover rubric: high-impact P2 $2,500; basic P3 $250–$500; concession P4 $100)
- **STATUS: Block is discontinuing ALL Bugcrowd programs effective September 30, 2026.** Cash App testing re-opened only Sep 21–30, 2026 for queue closure. Square already paused. Do not invest recon here; watch for their new intake channel.
- **Scope was:** Cash App iOS/Android, `*.cash.app`, `*.cashstaging.app`; unlisted-but-Block-owned subdomains accepted under takeover rubric
- **Focus was:** authentication flows (login, MFA, account recovery, $CashTag) — ATO; crypto issues could pay above advertised
- **Disclosure:** not allowed

- **STATUS (verified 2026-09-26):** Block announced all its Bugcrowd programs end **2026-09-30**; Cash App testing was only reopened 2026-09-21 → 2026-09-30. Do not start now.

---

## VDPs — 5 reputation-building programs (no cash, no rep required)

Bugcrowd VDPs pay **no money** and (per current Bugcrowd docs) no longer award points — the payoff is hall-of-fame credit, acknowledged reports, and report-writing reps on real targets. All five below are public, need no reputation to join, and carry full safe-harbor authorization.

### V1. NASA VDP — https://bugcrowd.com/engagements/nasa-vdp
- **Paid:** No — by submitting you waive all claims to compensation (per NASA's official policy)
- **Scope:** NASA internet-accessible systems (exact target list — verify on the live brief)
- **Authorization:** good-faith research is considered authorized; NASA will not recommend or pursue legal action, and will make the authorization known if a third party sues you
- **Rules:** reports used for defensive purposes only; may be shared with CISA/vendors; NASA acknowledges receipt within 3 business days; describe vuln + impact + repro steps; **Bugcrowd is the official channel** — do not report via other avenues; not for NASA employees/contractors
- **Disclosure:** coordinate with NASA; no unilateral public disclosure
- **WHY:** The most prestigious VDP in the world on your first-month resume, with enormous scope. Teaches the discipline that pays later: impact-first reports, clean PoCs, no scanner noise.

### V2. USAGM VDP — https://bugcrowd.com/engagements/usagm-vdp
- **Paid:** No
- **Scope (8 wildcard domains):** `*.opentech.fund`, `*.alhurra.com`, `*.radiosawa.com`, `*.rfa.org`, `*.rferl.org`, `*.radiotelevisionmarti.com`, `*.insidevoa.com`, `*.usagm.gov` — covers USAGM, Voice of America, Radio Free Europe/Radio Liberty, Radio Free Asia, Middle East Broadcasting Networks, Open Technology Fund
- **Out of scope:** any system not expressly managed by the listed agency orgs; vendor systems (report to the vendor)
- **Rules:** no DoS; no physical/social-engineering testing; use exploits only to the extent needed to confirm; STOP and notify immediately if you hit PII/sensitive data; no high-volume low-quality reports
- **Safe harbor:** full — CFAA-authorized, DMCA-exempt, ToS restrictions waived
- **Disclosure:** Bugcrowd standard terms; explicit permission required via the disclosure-request option
- **WHY:** Eight wildcard federal-broadcast domains with explicit authorization — a wide, legal recon surface (subfinder/dnsx/httpx, your batch-A pipeline) that doubles as report-writing practice.

### V3. US Department of Veterans Affairs VDP — on Bugcrowd (verify slug in dashboard)
- **Paid:** No
- **Scope:** VA internet-accessible systems — verify the exact target list on the live brief (find it via Engagements → filter `vdp:true`, search "Veterans Affairs")
- **WHY:** Confirmed on Bugcrowd's public-sector VDP roster. Massive federal web surface; healthcare-adjacent data means your IDOR/PII playbooks get real reps.

### V4. State of California VDP — on Bugcrowd (verify slug in dashboard)
- **Paid:** No
- **Scope:** California state systems (`ca.gov` estate) — verify the exact target list on the live brief (find it via Engagements → filter `vdp:true`, search "California")
- **WHY:** Confirmed on Bugcrowd's public-sector VDP roster. State-government web apps are classic IDOR/business-logic territory with lower hunter competition than federal programs.

### V5. US DHS VDP — on Bugcrowd (verify slug in dashboard)
- **Paid:** No
- **Scope:** DHS/CISA information systems — the RRB program brief states "any submissions of vulnerabilities pertaining to CISA's own information systems would be governed by the DHS VDP brief"; verify the exact engagement slug and targets on the live brief (Engagements → filter `vdp:true`, search "DHS")
- **WHY:** The agency that writes the rules other agencies follow. A DHS acknowledgment is the single strongest reputation line a VDP hunter can hold.

---

## Appendix B — Methodology, freshness, and top-3 picks

**Methodology (2026-09-26):** program selection and shortlisting used the ROI dataset of 207 cash-reward Bugcrowd programs (scraped 2026-04-07 — shortlist only, never overrides live status); reward/scope metadata cross-checked against bountyhunte.rs program pages; every program section above is grounded in the **live Bugcrowd engagement brief** fetched 2026-09-26 unless marked "verify on live brief."

**Freshness warnings:**
- Exact P1–P4 grids are published only for some programs (Pinterest, T-Mobile). Where only an advertised range exists, the range is given and the grid is marked "verify on live brief" — do not quote a tier payout that isn't in the brief.
- Programs close, pause, and re-scope constantly (Kiteworks and Cash App both changed status inside this research window). **Re-check the brief's "What's new" + Recent activity the day you start.**
- Historical ranges (HotDoc $50–$8,000, Bullish ceiling $15,000) come from the April 2026 dataset — confirm before treating them as current.
- Moovit appeared in the April dataset but its engagement URL no longer resolves publicly — treat as unavailable until found in your dashboard.

**Top-3 picks to start with (beginner→intermediate, web-focused):**
1. **Aiven (#4)** — the brief tells you exactly where the dupes aren't (managed database services) and what pays most (cross-account access). Free tier + trial credits, chaining blessed, your IDOR/priv-esc playbooks map 1:1.
2. **Pinterest (#5)** — exact P1–P4 grid, AI features newly in scope with low dupe rates, accepted payouts visible in Sep 2026, explicit safe harbor.
3. **OneTrust (#15)** — admin-level test credential + dedicated staging (break things freely), DSR webforms/workflows = IDOR heaven, accepted payouts on 2026-09-18 and 2026-09-21 prove it's actively paying.

**What this subagent could NOT do:** log into Bugcrowd, check program status behind login, read Known Issues lists, or start any actual testing — that needs Shivam's logged-in browser session (parent: delegate browser-capable work for account setup, credential retrieval, and beginning tests).
