# Program Rules Matrix — Master Reference
**Built:** 2026-09-26 · **Sources:** `programs-intigriti-yeswehack.md`, `programs-hackerone.md`, `programs-bugcrowd.md` + live-browser pull of Booking.com's H1 policy (2026-09-26). ⚠️ = secondary-sourced or marked "verify live" in the dossier — re-check the live brief before testing.

## 1. Master table

| Program | Platform | Bounty range | Scope (domains) | Scanners? | Traffic tagging | Test accounts | Safe harbor | Disclosure | Focus areas |
|---|---|---|---|---|---|---|---|---|---|
| intigriti (own) | Intigriti | €50–€13,337 | `*.pwn.intigriti.rocks`, `*.intigriti.me`, vpn.intigriti.rocks | Unrestricted in PWN env over VPN; no DoS/brute-force | — | Unlimited at login.pwn.intigriti.rocks | Yes | No disclosure without consent | IDOR, priv-esc, PII/submission data |
| FDJ United | YesWeHack | €50–€15,000 | 33 scopes: unibet.*, mariacasino.*, 32red.com, bingo.com, payment.* subdomains, mobile apps | **BANNED** — no automated scanners / heavy traffic | — | Own accounts only | Not stated | No disclosure without written permission | RCE, SQLi, PCI access, ATO, stored/blind XSS, CSRF on sensitive actions, subdomain takeover |
| Superbank | YesWeHack | $100–$2,000 | `api.super-id.net`, `ecosystem-experience.super-id.net`, `superbank.id`, `chatbot.super-id.net`, iOS/Android | **BANNED** — no scanners / heavy traffic | — | Self-register w/ YWH email alias | Not stated | Not stated | SQLi, XSS, RCE, IDOR, priv-esc, auth bypass, business logic, AI chatbot |
| Moneybox | YesWeHack | €50–€2,000 | `api.moneyboxapp.com`, `admin.moneyboxapp.org`, `admin-roundups.moneyboxapp.org`, `sycamore.moneyboxapp.org`, iOS/Android | **BANNED** — no scanners / heavy traffic | Append `bugbounty-0421` to User-Agent | YWH email aliases | Not stated | Not stated | IDOR, auth bypass on 3 Critical admin panels |
| Kiteworks | YesWeHack | up to **$50,000** (+$25k RCE bonus) | Dedicated env `ywh-kw-public.bounty.kiteworks.dev` (12 scopes) | No DoS; no out-of-scope boxes | — | Brief (logged in) | Not stated | **No disclosure at all, even partial** | RCE, priv/role escalation, LDAPi, XSS w/ real impact PoC |
| Doctolib | YesWeHack | up to €50,000 (+€50k special scenarios) | `www./pro. doctolib.(fr/de/it)`, `*.doctolib.(fr/de/it/com/net)`, apps, `*.siilo.com` | Max **10 req/sec**; no scanners stated but keep light | UA `BugBounty/42 (YWH)` | **Fake doctor provided** (booking code 42); fake test accounts only | Not stated | No disclosure | IDOR/patient-data batch export (PII typology grid) |
| CoinDCX | YesWeHack | $100–$2,000 | `*.coindcx.com` wildcard, `api.coindcx.com`, Android/iOS | **BANNED** — no scanners / heavy traffic | — | Own accounts; verify creds only | Not stated | No disclosure | Wallet/ATO, sub-account withdrawal, Web3, auth/authz |
| TrueLayer | Intigriti | €75–€6,000 | Tiered Open Banking / PSD2 API assets | **Allowed ≤10 req/sec** | Header `X-Intigriti-Username: {username}` | Intigriti account | Standard Intigriti | No disclosure without consent | IDOR/BOLA on payment + financial-data APIs |
| BMW Group | Intigriti | €150–€6,000 | Tier 1–2: BMW/MINI/Rolls-Royce/Motorrad web + financial services | **≤2 req/sec** | Header `X-Intigriti-Username` | Intigriti account | Not stated | No disclosure without written consent (incl. YouTube/Vimeo PoCs) | Customer data, vehicle/financial systems |
| Oda | Intigriti | €75–€4,000 | `*.oda.com`, `*.prod.nube.tech`, iOS/Android | **Manual culture — no automated scanners**; max **5 req/sec** | Append `intigriti-<username>` to UA (also WAF-bypasses Fastly) | Intigriti account | **Yes** | Not stated | Checkout/pricing/account/order flows (e-commerce logic) |
| Personio | Intigriti | €50–€5,000 | Tier 2–3 HR SaaS platform | **≤2 req/sec** | Header `X-Intigriti-Username: {{username}}` | Intigriti account | Not stated | No disclosure without consent | Multi-tenant IDOR, role-based access, PII |
| Suivo | Intigriti | up to €2,000 | **Staging env** (copy of prod), fleet-tracking web app | **Manual only — no automatic scanners**; max **5 req/sec** | — | Intigriti account | **Yes** | Detailed reporting guidelines | RCE, fleet/vehicle-data impact |
| GitHub | HackerOne | $250–$10,000 (VIP to $30k+) | github.com, Enterprise, Desktop, Actions | Not explicit — stay manual (4-submission newcomer cap) | — | Standard GitHub accounts | **Yes** | Standard | Core web app, Actions, Enterprise, Desktop |
| Airbnb | HackerOne | $250–$25,000 | High-impact: `*.airbnb.com`, `*.airbnb.org`, `*.musta.ch`, `*.airbnbpayments.com`, apps · Low-impact: `*.atairbnb.com`, `*.muscache.com`, HotelTonight… | No mass account creation; no brute-force rate-limit probing | Header `X-HackerOne-Researcher: <username>` + source IP in report | Own accounts; HotelTonight test card `4111111111111111` | **Yes** | Standard | Booking/payments: auth, IDOR, SSRF, XSS |
| Shopify | HackerOne | $500–$200,000 (calculator) | Scope tab assets; **test ONLY stores you create** | No explicit clause — stay conservative | — | **Own test stores w/ `@wearehackerone.com` alias** | Not explicit | No public disclosure before resolution | IDOR (predictable IDs), leaked creds, merchant PII |
| Dropbox | HackerOne | $216–no max (menu: RCE $32,768, auth bypass $17,576, XSS $12,167) | Web app, iOS/Android, desktop, Core SDK | ⚠️ not explicitly confirmed | — | Own accounts | ⚠️ verify | No bounty for pre-patch public disclosure | RCE, auth bypass, XSS (browser breadth), SSRF, CSRF on critical actions |
| HackerOne (own) | HackerOne | $200–~$20,000 | hackerone.com, hackerone.net, hacker101.com | **Restricted — ask first** | **Custom HTTP header required** in all traffic + in report | Own accounts | **Yes** (incl. bypassing tech measures) | Public only w/ agreement; 180-day non-response window | Auth/session, host-header injection, IDOR, invite logic |
| Basecamp | HackerOne | $100–$10,000 | `*.hey.com`, app.basecamp.com, APIs, 37signals OSS | **PROHIBITED** — no Burp Intruder, no brute-forcing; scanner output = N/A | — | `@wearehackerone.com` in test-account email | Not explicit (cooperative tone) | Standard | Auth, access control, injection; chaining encouraged |
| Adobe ⚠️ | HackerOne | $100–$15,000 | `*.acrobat.adobe.com`, `*.lightroom.adobe.com`, Magento, Firefly, mobile apps | Not explicit — verify live | — | Own accounts | ⚠️ verify | Standard | XSS, CSRF, RCE, auth bypass/authz, SQLi, traversal |
| Stripe ⚠️ | HackerOne | $100–$25,000 | stripe.com, `api.stripe.com`, Dashboard, Stripe.js, SDKs | Not explicit — verify live | — | Self-serve test accounts | ⚠️ verify | Standard | Payment-intent logic, Stripe.js sandbox, fee-discount race conditions |
| Coinbase | HackerOne | High+ only (**Low/Medium = $0**) · up to $15k (Extreme $1M wallet-class) | Platform, exchange, wallet, cb-mpc | Not explicit — stay conservative | — | Own accounts | ⚠️ verify | Standard | 2FA/KYC bypass, fee-structure bypass, IDOR, MPC bugs |
| Airtable | HackerOne | $50–$10,000 | **STAGING ONLY: `staging.airtable.com`** | Allowed but scanner-output-only reports rejected — manual insight required | — | Test-account guide in policy | Not explicit | No disclosure without permission | RCE, stored XSS, priv-esc/auth, enterprise admin IDOR |
| Verizon Media | HackerOne | $100–$15,000 | `*.yahoo.com`, `*.aol.com`, `*.techcrunch.com`, mail/media assets | ⚠️ verify live | SSRF PoC format: fetch `http://<hostname>/hackerone-<username>` | Own accounts | ⚠️ verify | Standard | SQLi, OS command injection, XSS, auth, subdomain/DNS takeover |
| Automattic | HackerOne | $100–$1,000 | WP.com, Jetpack, WooCommerce, Tumblr, Beeper… | Own test accounts; no disclosure before resolution | — | Own test accounts | Not stated | **No disclosure before resolution → disqualification** | Unauth stored XSS, payment bypass, RCE |
| GitLab ⚠️ | HackerOne | $100–$35,000 (CVSS-driven) | gitlab.com, registry, source | Not explicit — verify live | — | Free self-service signup | ⚠️ verify | Standard | Open-source white-box: IDOR, auth, injection |
| Amazon VRP | HackerOne | Discretionary (no fixed table) | `*.amazon` wildcard, mobile apps, devices, GenAI | **Explicitly allowed ≤5 req/sec** | UA `amazonvrpresearcher_<username>` | Accounts w/ `<h1username>@wearehackerone.com` | **Yes** (CFAA/DMCA, ToS waived) | **STRICT — no sharing findings with ANY third party** | Retail web, device APIs, LLM/GenAI, fraud/abuse logic |
| Booking.com | HackerOne | $150–$3,000 (min $150) | 49 assets: `*.booking.com`, `*.fareharbor.com`, `*.rentalcars.com`, Android/iOS apps | **EXPLICITLY BANNED** — automated scanning tools | Use `@wearehackerone.com` email so monitoring IDs you | Test accounts (real only if unreproducible) | Not explicit | **No public disclosure — disclosing kills the bounty** | Fareharbor IDOR (POST/PUT/DELETE or GET w/ PII), booking flows |
| Affirm | HackerOne | Unpublished | `sandbox.affirm.com` (sandbox-only) | ⚠️ verify live | — | Sandbox | ⚠️ verify | Standard | Sandbox fintech logic |
| Okta | Bugcrowd | $100–$75,000 (+$500k RCE bonus) | Provisioned tenants `bugcrowd-pam-###.oktapreview.com` (+workflows/at/admin), `personal.trexcloud.com`, `app.scaleft.com`, Okta Verify apps | **NO automation on Workflows = immediate removal** | — | **"Get Credentials"** — 2 sets | Not explicit | **No public disclosure** (explicit permission required) | SAML/OAuth/OIDC, XXE, cross-org, SSRF via Workflows, MFA bypass |
| Auth0 | Bugcrowd | $100–$50,000 | Test tenant `manage.cic-bug-bounty.auth0app.com` + `*.cic-bug-bounty.auth0app.com`, OpenFGA, SDKs, jwt.io | **Automated scanning = immediate BAN**; Burp Intruder ≤5 req/s | — | **"Get Credentials"** — 3 users × 3 tenants | Not explicit | Standard | OAuth/OIDC/SAML, auth bypass, cross-tenant priv-esc |
| Zendesk | Bugcrowd | $100–$50,000 | Zendesk AI, Front End, Marketplace Apps, Mobile, Suite | Not explicit — stay conservative | — | Own accounts | Not explicit | Standard | AI features (prompt injection/data exfil), marketplace apps |
| Aiven | Bugcrowd | $50–$25,000 ⚠️ verify grid | `console.aiven.io`, `api.aiven.io`, `aiven.io`, `regatta.aiven.io`, managed DB services, GitHub orgs | No DoS/social eng; keep manual | — | Free tier + trial credits; `@bugcrowdninja.com` emails | Not explicit | Standard | Cross-account access to managed DB services (not the website) |
| Pinterest | Bugcrowd | $200–$25,000 (P1 $10–25k … P4 $200–500) | `api.pinterest.com`, `*.pinterest.com`, apps, extensions, `github.com/pinterest`, `shffls.com` | Scanner output out of scope — manual | — | Business account + dev enrollment w/ `@bugcrowdninja.com` | **Yes** (CFAA/DMCA) | Explicit permission required; coordinated disclosure OK | RCE, auth bypass/authz, XSS, PII exfil, AI features |
| Chime | Bugcrowd | $50–$20,000 | `*.chime.com`, `*.chimepayments.com`, `*.saltlabs.com`, apps | Not explicit — stay conservative | — | **Non-US: STAGING** `member-qa.chime.com` / `app-qa.chime.com` (SSN ending 1234/1235); US prod needs SSN | **Yes** (CFAA/DMCA) | Standard | GraphQL, money movement, business logic/API |
| Fivetran | Bugcrowd | up to $15,000 (**P1–P3 only; P4 = $0**) | `*.fivetran.com`, Connector SDK | No DoS/rate-limit testing, no brute force | Header `X-Bug-Bounty:<your-username>` | Signup w/ `@bugcrowdninja.com` | Not explicit | **Not allowed** | Pipeline-data access, auth, Connector SDK |
| Atlassian | Bugcrowd | $200–$10,000 | Guard, `admin./id.atlassian.com`, Jira/Confluence Cloud, Bitbucket, Forge, `mcp.atlassian.com`, Rovo AI | Not explicit — stay conservative | — | `bugbounty-test-<name>.atlassian.net` instances | Not explicit | Standard | Rovo AI: connector-auth breakage, permission drift, agent authz bypass, PII via AI |
| Keeper | Bugcrowd | $300–$20,000 (P1/P2 impact only) | Web Vault, Admin Console, PAM, SSO/SAML, extensions, apps | Manual testing encouraged; scanner-only output out | — | 30-day personal + 14-day enterprise trials; `@bugcrowdninja.com` | Not explicit | Standard | Cross-tenant vault access, auth/device-approval bypass, crypto |
| Canva | Bugcrowd | $200–$15,000 | `www.canva.com`, `api.canva.com`, `*.canva.com`, `*.canva-apps.com`, apps, integrations | Ethical testing; written PoC required | — | Free account; dev portal signup | Not explicit | ⚠️ verify live brief | Editor authz/IDOR (other users' designs), SDK sandbox violations |
| T-Mobile | Bugcrowd | P1 to $133,700+ special / $55k core | `t-mobile.com`, `account.t-mobile.com`, `*.api.t-mobile.com`, T-Life, DIGITS | Not explicit — stay conservative | — | Free signup; test MSISDN `404-200-7239` | Not explicit | Standard | Cellular-auth bypass, Entra ID self-registration, account/billing/API |
| HotDoc ⚠️ | Bugcrowd | $50–$8,000 ⚠️ verify grid | Web + mobile apps — verify exact targets live | ⚠️ verify | — | Own accounts | ⚠️ verify | ⚠️ verify | Healthcare PII / IDOR |
| Bullish ⚠️ | Bugcrowd | up to $15,000 ⚠️ **verify program is active** | `bullish.com`, `investor.bullish.com`, `*.bullish.com`, `simnext.bullish-test.com` | Unobtrusive testing | — | Free signup | **Yes** | Explicit permission required | **Subdomain takeover** (prove w/ `/yourusername.html`) |
| Sophos | Bugcrowd | $100–$80,000 | `central.sophos.com`, `*.sophos.com`, Firewall, endpoints, appliances | **No DoS against Central**; scanner-output-only reports rejected | — | Fresh trials; email **must contain `bugcrowdninja`** | Not explicit | **Coordinated only** — Sophos discloses first, customers get 30 days | Zero-click RCE, Central super-admin ATO, firewall pre-auth RCE |
| OneTrust | Bugcrowd | $300–$6,500 | **ONLY `pentest-app.onetrust.com` staging pays**; plus `*.onetrust.com`, `*.cookiepro.com`… | Not explicit — staging is fair game | — | **Admin credential from brief** (forgot-password flow); multi-privilege accounts | **Full** (CFAA/DMCA/ToS waived) | **Not allowed** | DSR webforms/workflows IDOR, data exfiltration, Integrations module |

### Practice VDPs (no cash)
| Program | Platform | Scope | Scanners? | Tagging | Safe harbor | Disclosure |
|---|---|---|---|---|---|---|
| Supabase | HackerOne | supabase.com, api.supabase.com, own `*.supabase.co` projects | No automated tools without manual verification | Header `X-SUPABASE-VDP: {H1 HANDLE}`; `@wearehackerone.com` emails | **Gold standard** | Coordinate; share drafts 30 days before writeup |
| Aptible | HackerOne | api/auth/billing/dashboard/gridiron.aptible.com only | **Manual only — fuzzers/scanners = ineligible** | — | Not explicit | Report via email |
| Artsy | HackerOne | artsy.net + `*.artsy.net` | **No scripting/automation or brute-forcing** | — | Not explicit | No public disclosure before fix |
| Drupal | HackerOne | Drupal core + drupal.org | Conservative | — | Not explicit | Confidential, team's timeline |
| NASA | Bugcrowd | NASA internet-accessible systems | No high-volume low-quality reports | — | Full (NASA won't pursue legal action) | Coordinate with NASA |
| USAGM | Bugcrowd | 8 wildcards: `*.rfa.org`, `*.rferl.org`, `*.voanews.com`-family (`*.alhurra.com`, `*.radiosawa.com`, `*.opentech.fund`…) | No DoS; stop on PII | — | Full (CFAA/DMCA/ToS waived) | Explicit permission required |
| VA / California / DHS | Bugcrowd | Verify slug in dashboard | Verify live | — | Full (public-sector VDP) | Verify live |

---

## 2. RED LINES — hard prohibitions that get Shivam banned or disqualified

**Automated scanning BANNED (instant ban/N/A risk):**
- **Booking.com** — automated scanning tools explicitly prohibited; reports from automated tools without a verified working PoC are rejected.
- **FDJ United** — no automated scanners / heavy traffic.
- **Superbank** — no automated scanners / heavy traffic.
- **CoinDCX** — no automated scanners / heavy traffic.
- **Moneybox** — no scanners / heavy traffic; UA must contain `bugbounty-0421` or risk block.
- **Oda** — manual-testing culture, no automated scanners; max 5 req/sec.
- **Suivo** — manual only, no automatic scanners; max 5 req/sec.
- **Basecamp** — automated scanning prohibited (Burp Intruder, brute-forcing, mail bombing); scanner output = N/A.
- **Aptible (VDP)** — no fuzzers/scanners/automated tools; violating = report ineligible.
- **Artsy (VDP)** — no scripting/automation or brute-forcing.
- **Okta** — NO automation on Workflows = immediate removal from program.
- **Auth0** — automated scanning = immediate BAN (Burp Intruder capped at 5 req/s).
- **HackerOne (own)** — automated scanning restricted, ask first.

**Disclosure — never publish without permission:**
- **Booking.com** — public disclosure NOT permitted; disclosing (even in videos/streams) makes the report bounty-ineligible.
- **Amazon VRP** — STRICT: no sharing findings with ANY third party, publicly or privately.
- **Kiteworks (YWH)** — no disclosure at all, even partial.
- **OneTrust** — disclosure NOT allowed.
- **Fivetran** — disclosure not allowed.
- **Automattic** — no disclosure before resolution → disqualification.
- **Okta** — no public disclosure without explicit permission.
- **FDJ United / CoinDCX / Doctolib / Suivo** — no disclosure without (written) permission/consent.
- **Sophos** — coordinate only; Sophos discloses first, customers get 30 days to patch before any publication.
- **Supabase (VDP)** — share drafts 30 days before any public writeup.

**Account / target-touching bans:**
- **Shopify** — test ONLY stores you create with `@wearehackerone.com`; touching live merchants = N/A and/or disqualification.
- **Booking.com** — no interacting with other users' accounts (accessing private user data disqualifies + can lead to bans); no fake bookings; no affecting hotel availability.
- **Airbnb** — own accounts only; no mass account creation; no brute-force rate-limit probing.
- **CoinDCX** — don't alter compromised accounts; hunting post-auth bugs on compromised accounts = ineligible.
- **Keeper** — own-account-only findings pay nothing; must demonstrate impact on ANOTHER user/tenant.
- **Stripe** — never incur loss of funds that aren't yours.
- **Amazon VRP** — no touching others' accounts/data; no post-exploitation; SSRF only via `bugbounty-sheriff.aka.amazon.com:443`.
- **HackerOne (own)** — own accounts only; no social engineering.
- **Pinterest** — unlisted properties get hall-of-fame only, no payout.

**Payout traps (wasted effort, not bans):**
- **Coinbase** — Low/Medium findings pay **$0**; aim High+ only.
- **Fivetran** — P4/P5 pay nothing; chase P1–P3 only.
- **OneTrust** — submissions from non-staging environments pay NOTHING.
- **GitHub** — newcomers capped at ~4 submissions; AI-generated reports rejected.
- **Bullish** — verify the program is actively accepting before investing time (past maintenance pause).
- **Kiteworks (Bugcrowd)** — CLOSED to new submissions (use security.kiteworks.com instead).
- **Cash App (Bugcrowd)** — program ends **2026-09-30**; do not start.
- **Atlassian (H1)** — paid bounty reportedly moved to invite-only Bugcrowd; verify before investing time.
- **Intel / Grafana (Intigriti)** — paid programs dead (now unpaid VDPs).

---

## 3. ACCOUNT SETUP CHECKLIST — do before testing

**One-time platform accounts (all free, no reputation needed):**
- [ ] **Intigriti** — register → note your exact username → use header `X-Intigriti-Username: <username>` on TrueLayer/BMW/Personio, and UA suffix `intigriti-<username>` on Oda (also whitelists you past Fastly WAF). Enable 2FA where required. Grab WireGuard **VPN config from your profile** for the PWN environment (`*.pwn.intigriti.rocks`).
- [ ] **YesWeHack** — register hunter account → use your **YWH email alias** for self-registration on Superbank, Moneybox, CoinDCX.
- [ ] **HackerOne** — account `shiva92` exists → set up the **`@wearehackerone.com` email alias**; use it for test accounts on Shopify, Airbnb, Amazon VRP, Basecamp, Supabase.
- [ ] **Bugcrowd** — account exists → use **`@bugcrowdninja.com` emails** for Aiven, Pinterest, Fivetran, Canva, Chime; Sophos trial email **must contain `bugcrowdninja`** (e.g. `you+bugcrowdninja@gmail.com`).

**Per-program test credentials / environments:**
- [ ] **Shopify** — create your OWN test stores with the `@wearehackerone.com` alias. Never touch a live merchant.
- [ ] **Okta** — open the brief → click **"Get Credentials"** (2 sets); Okta Personal via `@bugcrowdninja.com` signup.
- [ ] **Auth0** — open the brief → **"Get Credentials"** (3 users × 3 tenants).
- [ ] **OneTrust** — retrieve the **admin-level credential** from the brief's retrieve-credential section (forgot-password flow); create multiple privilege-level accounts.
- [ ] **Aiven** — free tier + trial credits; request extra credits via the program if needed.
- [ ] **Doctolib** — use the provided **fake doctor** (booking code **42**) + fake test accounts; set UA to `BugBounty/42 (YWH)`.
- [ ] **Atlassian** — spin up `bugbounty-test-<your-bugcrowd-name>.atlassian.net` instances; trial Rovo via support docs.
- [ ] **Airbnb (HotelTonight)** — test card `4111111111111111` for the low-impact HotelTonight tier.
- [ ] **Chime (non-US)** — STAGING only: enroll `member-qa.chime.com/enroll`, login `app-qa.chime.com`, test SSNs ending 1234/1235.
- [ ] **T-Mobile** — authorized test MSISDN `404-200-7239` for cellular-auth scenarios.
- [ ] **Fivetran** — add header `X-Bug-Bounty:<your-username>` to ALL traffic.
- [ ] **Airbnb** — add header `X-HackerOne-Researcher: <username>` + include your source IP in reports.
- [ ] **HackerOne (own program)** — set the **custom HTTP header** named in the policy on ALL testing traffic and include it in the report.
- [ ] **Supabase (VDP)** — add header `X-SUPABASE-VDP: {H1 HANDLE}` on all requests; test only your own `*.supabase.co` projects.
- [ ] **Amazon VRP** — set UA `amazonvrpresearcher_<username>`; create accounts with `<h1username>@wearehackerone.com`.
- [ ] **Moneybox** — append `bugbounty-0421` to your User-Agent or risk being blocked.
- [ ] **Oda** — append `intigriti-<username>` to your User-Agent (whitelists you past Fastly WAF).
- [ ] **Keeper** — start 30-day personal + 14-day enterprise trials; use `enableNetworkLog()` in Web Vault devtools to read traffic.
- [ ] **Airtable** — test ONLY `staging.airtable.com` (staging admin guide is in the policy).
- [ ] **Verizon Media** — SSRF PoC format: fetch `http://<hostname>/hackerone-<username>`, attach file + timestamp.
- [ ] **Bullish** — takeover PoC: serve `/yourusername.html` on the claimed subdomain.
- [ ] **Basecamp** — put `@wearehackerone.com` in the test-account email.

**Do-first order:** Intigriti account + VPN config → YesWeHack account → `@wearehackerone.com` alias → `@bugcrowdninja.com` pattern → Shopify test stores → Okta/Auth0/OneTrust credential grabs.
