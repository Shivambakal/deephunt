# Link Study — Batch 02 (28 URLs, studied 2026-09-26)

Read-only research. HackerOne program pages block non-browser fetches; scope/rules below are taken from the verified local dossiers (`intel/programs-hackerone.md`, `intel/programs-bugcrowd.md`). Three links in this batch were already studied by earlier workers — those sections reference the existing intel files.

## HIGH-VALUE LEADS (top 5)

1. **OAuth metadata + open client registration probe** (iamshafayat writeup): `GET /.well-known/oauth-authorization-server` exposes `registration_endpoint`; unauthenticated `POST /api/v2/oauth/register` with arbitrary `redirect_uris` + auth-less `POST /api/v2/oauth/authorize` returning 201 + token endpoint accepting `auth_methods: ["none"]` + wildcard CORS = full ATO chain. → Add these two probes to `hunter.py` fingerprints; run against Okta/Auth0/Aiven/OneTrust targets.
2. **Burp TLS fingerprinting gets you silently blocked** (kecman): Burp's Java TLS stack sends ~49 cipher suites (JA3 `e5ba05202909ac1ea81e3f940a583d20`) vs a real Firefox's 15 — Cloudflare/Akamai/DataDome score this and fail flows closed with no captcha. Fix: "Bypass Bot Detection" BApp → Adjust ciphers to common browsers; verify against `tls.peet.ws`. → Install the BApp before touching bot-protected targets (booking.com, Cloudflare-fronted scopes); if auth flows mysteriously fail, check JA3 first.
3. **Client-side auth bypass patterns** (kuldeep): forge `localStorage` `token`/`tokenExpiry`, forge `sessionStorage` `userInfo`/`loggedIn`, Burp match-and-replace on session-info responses (`GetSessionInfo`, `GetNotifications`), flip `is_active: false→true` to reveal hidden functionality. → Apply to Agoda partner portals (`portal.agoda.com`, `partnerhub.agoda.com`) and Booking.com partner flows; complements the existing `client-side-auth` playbook.
4. **SAML auth bypasses are still live in 2026** (oblique.security): Authentik NameID comment-injection account truncation (CVE-2026-57580), signature-wrapping in lightsaml/OneUptime/saml-client, bypasses in non-Response messages (AuthnRequest/LogoutRequest), XSLT DoS in Python SAML libs. → Feed NameID comment injection + signature-wrapping tests into the existing `sso` playbook; research corpus at `github.com/oblique-security/saml-research`.
5. **Managed-Postgres extension attack surface** (mehmetince): PostGIS `address_standardizer` OOB write (CVE-2026-73514) → `rolsuper` flip → superuser + RCE on NeonDB/Supabase/Xata; 40+ extension vulns; 5 undisclosed PG-core RCE 0-days teased. Aiven's Bugcrowd scope explicitly includes managed DB services (PostgreSQL, MySQL, OpenSearch…); Supabase is a HackerOne VDP. → Review Aiven/Supabase scope for DB-extension and cross-tenant threat-model angles.

---

## 1. https://hackerone.com/coinbase
- **WHAT:** Coinbase's HackerOne program page (fetch blocked — JS/proxy; details from `intel/programs-hackerone.md`).
- **ATTACK SURFACE:** Paid; Extreme bounties to $1M, Critical to $15K. Scope: platform, exchange, wallet, cb-mpc. Note: Low/Medium priced at $0 — aim High+ only.
- **ACTIONABLE LEAD:** Money-relevant web layer is the sweet spot: 2FA, KYC, fee logic, IDOR on wallet/exchange endpoints.

## 2. https://hackerone.com/dropbo
- **WHAT:** Truncated URL (intended `hackerone.com/dropbox`); page fetch blocked; details from dossier.
- **ATTACK SURFACE:** Paid ($216 min). Published payout menu: RCE on servers $32,768 · auth bypass $17,576 · trivial RCE in clients $15,625 · CSRF on critical actions $13,824 · XSS on www.dropbox.com $12,167. Scope: web, iOS/Android, desktop, Core SDK.
- **ACTIONABLE LEAD:** Target the published $12–17K payout-menu rows directly (XSS on www.dropbox.com, CSRF on critical actions).

## 3. https://hackerone.com/drupal
- **WHAT:** Drupal's HackerOne VDP page (fetch blocked; dossier).
- **ATTACK SURFACE:** Unpaid VDP. Scope: Drupal core + drupal.org ecosystem. Fully open-source PHP.
- **ACTIONABLE LEAD:** Textbook XSS / access-bypass / SQLi classes with full source available — reputation farm with zero payout pressure.

## 4. https://hackerone.com/github
- **WHAT:** GitHub's HackerOne program page (fetch returned JS-required shell; dossier).
- **ATTACK SURFACE:** Paid ($250 min). Fixed payouts: Critical $10K / High $5K / Medium $2K / Low $250. Scope: github.com + Enterprise/Desktop/Actions. VIP ladder to $30K+ criticals.
- **ACTIONABLE LEAD:** Best reputation farm in the set; newcomers get ~4 submissions — submit only validated reports.

## 5. https://hackerone.com/gitlab
- **WHAT:** GitLab's HackerOne program page (fetch blocked; dossier).
- **ATTACK SURFACE:** Paid. Critical $20,000–$35,000 (CVSS-driven via GitLab's AppSec CVSS calculator) · High $5–15K · Medium $1–3K. Scope: gitlab.com, registry, source. $1M+ paid in 2024.
- **ACTIONABLE LEAD:** Fully open source — audit the actual codebase for vulns instead of black-box fuzzing; huge ceiling.

## 6. https://hackerone.com/hackerone
- **WHAT:** HackerOne's own program page (fetch blocked; dossier).
- **ATTACK SURFACE:** Paid ($200 min), ~$20,000 disclosed top. Scope: hackerone.com, hackerone.net, hacker101.com.
- **ACTIONABLE LEAD:** Hack the triage platform itself — auth, IDOR, and host-header bugs are proven payers here.

## 7. https://hackerone.com/reports/3
- **WHAT:** Dead link — HTTP 404 (old public report ID, no longer resolves).
- **ATTACK SURFACE:** n/a.
- **ACTIONABLE LEAD:** None — skip.

## 8. https://hackerone.com/shopify
- **WHAT:** Shopify's HackerOne program page (fetch blocked; dossier).
- **ATTACK SURFACE:** Paid ($500 min), calculator up to $200,000. Scope: **own test stores only** (created with `@wearehackerone.com` alias). No public disclosure before resolution; IDOR judged on identifier predictability + data + impact.
- **ACTIONABLE LEAD:** Spin up test stores — zero legal risk to others; IDOR is the proven focus area.

## 9. https://hackerone.com/stripe
- **WHAT:** Stripe's HackerOne program page (fetch blocked; dossier).
- **ATTACK SURFACE:** Paid ($100 min), $5,000–$25,000. Scope: stripe.com, api.stripe.com, Stripe.js, SDKs. Test accounts available.
- **ACTIONABLE LEAD:** API-first target — payment-logic bugs (amount tampering, currency, webhook) are proven payers.

## 10. https://hackerone.com/supabase
- **WHAT:** Supabase's HackerOne VDP page (fetch blocked; dossier).
- **ATTACK SURFACE:** Unpaid VDP. Scope: supabase.com, api.supabase.com, `*.supabase.co` (own projects), `*.database.dev`. Free own sandbox, gold-standard safe harbor, ~2-day triage.
- **ACTIONABLE LEAD:** Starter-ladder VDP — free sandbox + fast triage makes it ideal for first validated reports; see also lead #5 (Postgres extension angle).

## 11. https://hackerone.com/verizonmedia
- **WHAT:** Verizon Media's HackerOne program page (fetch blocked; dossier).
- **ATTACK SURFACE:** Paid, $10,000–$15,000 range. Scope: `*.yahoo.com`, `*.aol.com`, `*.techcrunch.com`.
- **ACTIONABLE LEAD:** Huge legacy surface — subdomain-takeover goldmine; run takeover checks across the three wildcards.

## 12. https://hakluke.com/are-bug-bounties-cooked
- **WHAT:** hakluke essay on AI vs bug bounties (fetched, 15.8K chars).
- **ATTACK SURFACE:** n/a (strategy piece). Key points: AI collapsed the cost of finding commoditized bugs; platforms' agentic scanners (H1 Agentic PTaaS, Bugcrowd Savant) compete with hunters; frontier models need less harnessing; top hunters spend $100s–1000s/month on tokens; diversity of human methodologies is the remaining edge.
- **ACTIONABLE LEAD:** Stop hunting commoditized scanner-findings; prioritize fresh AI-feature surfaces (Atlassian Rovo AI, Pinterest AI features — both explicitly in scope) and novel bug classes where AI coverage is thinnest.

## 13. https://hakluke.com/how-to-start-or-come-back-to-bug-bounties-in-
- **WHAT:** Truncated URL — HTTP 404. Correct full URL not recovered.
- **ATTACK SURFACE:** n/a.
- **ACTIONABLE LEAD:** None — skip.

## 14. https://innerfirez.github.io/posts/the-secret-life-of-probe-requests/
- **WHAT:** Writeup of CVE-2026-5667 — Mitsubishi MAC-577IF-2E WiFi adapter takeover via setup-mode SSID "DefaultSSID" + hardcoded HTTP Basic creds found in a public GitHub repo (fetched, 10.2K chars).
- **ATTACK SURFACE:** Endpoints on the device: `/config`, `/service`, `/update`, `/default`, `/network`, `/server`, `/license` (all 401 except `/license` 200). Attack chain: Karma attack on probe requests → half-handshake crack → device joins attacker AP → hardcoded creds from GitHub repo `mac-577if-e` → full AC control (power/temp). Affected: ACs, fridges, heat-pump water heaters, IH cooktops, rice cookers.
- **ACTIONABLE LEAD:** GitHub-dork for hardcoded credentials tied to in-scope vendors' devices/infra (not just web apps) — default creds in public repos remain a live bug class.

## 15. https://itis911.github.io/writeups/RCE-Me
- **WHAT:** HTTP 404 — page not found at that path; correct URL not recovered.
- **ATTACK SURFACE:** n/a.
- **ACTIONABLE LEAD:** None — skip.

## 16. https://kecman.co/posts/burp-suite-tls-fingerprint
- **WHAT:** Truncated URL (404); recovered correct URL via search and fetched: `https://kecman.co/blog/burp-suite-tls-fingerprint-bot-detection-bypass.html` — "When a Web App Detects Burp Suite via TLS Fingerprinting".
- **ATTACK SURFACE:** Burp runs two TLS connections; the server only sees Burp→target (connection #2) using Java's TLS stack: ~49 cipher suites incl. legacy ones, JA3 `e5ba05202909ac1ea81e3f940a583d20`, vs real Firefox: 15 suites, JA3 `020ee54457b3c1d5f5a5050b22bee1f3`. Cloudflare/Akamai/DataDome/PerimeterX score JA3/JA4 + HTTP/2 fingerprints and fail closed silently (no captcha — just broken auth flows). Fix: "Bypass Bot Detection" BApp → Adjust ciphers to common browsers (drops to ~14 suites, JA3 `b765f4534bce3740f769b0254478e9bd`); verify via `tls.peet.ws`; "Brute force ciphers" for stubborn targets.
- **ACTIONABLE LEAD:** Install the Bypass Bot Detection BApp on Shivam's Burp before testing bot-protected targets (booking.com, Cloudflare-fronted scopes). If auth/session flows fail with vague errors and nothing changed functionally, check the TLS fingerprint before assuming the endpoint is broken.

## 17. https://kuldeep.io/posts/client-side-authentication-bypass/
- **WHAT:** "Client-side Authentication Bypass" — 4 case studies incl. one that led to a $4,000 SQLi (fetched, 12.8K chars).
- **ATTACK SURFACE / TECHNIQUES:** (1) `localStorage.setItem("token", <any JWT>)` + `tokenExpiry` future date bypassed `isUserLoggedIn()`; (2) `sessionStorage` `userInfo={}` + `loggedIn=true` bypassed Angular route guard; (3) Burp match-and-replace on `POST /api/api.svc/GetSessionInfo` (inject `Groups:["Production Admin"]`, `PluginId`) + strip `"TimeoutStatus":"Timeout"` from `GetNotifications` → full app access, led to $4K SQLi; (4) flip `is_active: false→true` in `/areaprivada/api/payments/dashboard/v1/accounts/me` to reveal hidden webhook functionality.
- **ACTIONABLE LEAD:** Apply to Agoda partner portals (`portal.agoda.com`, `partnerhub.agoda.com`) and Booking.com partner flows: grep JS for `authRequired`/`isUserLoggedIn`/`tokenExpiry`, try localStorage forgery, and flip boolean privilege flags in API responses. Complements the existing `client-side-auth` playbook.

## 18. https://kymu.dev/article/BlindOracle/
- **WHAT:** Blind search-oracle writeup (fetched; already studied — see `intel/blind-search-oracle.md`).
- **ATTACK SURFACE:** `GET /api/search?limit=50&offset=0&page=1&query=...&revision=1` with Lucene syntax; indexed restricted fields (Notes, creator emails, attachment names). Binary signal: 200 = substring exists, 204 = not. Extraction via greedy bidirectional extension (anchor on `@` for emails).
- **ACTIONABLE LEAD:** Test search APIs on Agoda/Booking.com/Airbnb/Pinterest for restricted-field indexing — search a value invisible to your role; if result presence correlates, you have an oracle (stop, document, report; no mass extraction).

## 19. https://medium.com/@AliMojaver/the-most-dangerous-oauth-bug-ive-ever-found-a
- **WHAT:** Medium blocked with 403; per instructions, not retried via other routes.
- **ATTACK SURFACE:** Unknown (title indicates an OAuth bug writeup).
- **ACTIONABLE LEAD:** None recovered — the OAuth-misconfig class is covered by #22's writeup instead.

## 20. https://medium.com/@HariHa
- **WHAT:** Bare Medium profile URL — 403; no article content.
- **ATTACK SURFACE:** n/a.
- **ACTIONABLE LEAD:** None — skip.

## 21. https://medium.com/@Tyrion404/from-zero-credentials-to-super-admin-an-sso-authentication-bypass-on-at-t-996fe9d0ec1e
- **WHAT:** AT&T SSO auth-bypass writeup (fetched; already studied — see `intel/sso-auth-bypass-att-tyrion404.md`).
- **ATTACK SURFACE:** `GET /api/actuator/logfile` (77K log lines, Super Admin username) → public `config.js` (API key + Azure SAS + OIDC creds) → `POST /api/home/ssoAuthentication` `{"username":"..."}` returned signed JWT + refresh token with zero credentials → `POST /api/user/listUsers` (3,182 employees) → write proof via `/api/reportstore/commentsReportStoreV2`. CVSS 9.3 after integrity proof.
- **ACTIONABLE LEAD:** Hunter already fingerprints Spring Actuator/logfile — extend the check to `config.js`/`env.js` secret harvesting and flag any login/SSO endpoint that returns a session for identifier-only input (manual verification only, own test accounts).

## 22. https://medium.com/@iamshafayat/how-i-found-a-critical-oauth-misconfiguration-that-led-to-account-takeover-abfec43eaea6
- **WHAT:** OAuth misconfiguration → account takeover writeup (fetched via browser, 535 lines).
- **ATTACK SURFACE:** `GET /.well-known/oauth-authorization-server` disclosed `authorization_endpoint`, `token_endpoint`, `registration_endpoint` (`/api/v2/oauth/register`), `token_endpoint_auth_methods_supported: ["none", "client_secret_post"]`. Chain: (1) unauthenticated `POST /api/v2/oauth/register` with arbitrary `redirect_uris` → client_id + client_secret issued; (2) `POST /api/v2/oauth/authorize` returned **201 with a valid code redirect without any authenticated session**; (3) PKCE S256 required but token endpoint needed no client secret (`"none"`); (4) wildcard `Access-Control-Allow-Origin: *`; (5) Google SSO auto-provisioning (`GET /auth/google` → 302 to accounts.google.com). Victim approves consent → code → attacker exchanges → JWT access + refresh tokens → victim's `/auth/user/me`, `/api/v1/db/meta/projects`.
- **ACTIONABLE LEAD:** Add two probes to `hunter.py` fingerprints: `/.well-known/oauth-authorization-server` (parse `registration_endpoint`) and unauthenticated `POST /oauth/register` / `/api/v2/oauth/register` open-registration test. Run against Okta/Auth0 (identity vendors), Aiven, OneTrust. Feeds the existing `oauth-misconfig` playbook.

## 23. https://medium.com/@lazysharaf/how-i-hacked-a-live-chatbot-and-earned-my-first-4-digit-bounty-5c43c8891
- **WHAT:** Medium blocked with 403; per instructions, not retried.
- **ATTACK SURFACE:** Unknown (title indicates AI-chatbot hacking, 4-digit bounty).
- **ACTIONABLE LEAD:** None recovered — AI-chatbot attack classes are covered in `intel/batch-c-ai-agent-security.md`.

## 24. https://medium.com/@pankaj_
- **WHAT:** Bare Medium profile URL — 403; the linked article was already studied (see `intel/idor-to-admin-pankaj.md`).
- **ATTACK SURFACE:** IDOR on profile-update `user_id` → changed admin's email → password reset → admin JWT (`id:1`, `role:administrator`) → hidden `/admin/panel` via client-side role check. $4,500, CVSS 9.8.
- **ACTIONABLE LEAD:** IDOR escalation chain for the `idor` playbook: read-IDOR → write-IDOR on email field → password-reset takeover; always try low IDs (1, 2).

## 25. https://mehmetince.net/blog/postgis-memory-corruption
- **WHAT:** Truncated URL (404); recovered correct URL via search and fetched: 6-part series "Systemic Risks in the Managed PostgreSQL Industry", Part 1 — PostGIS memory corruption at NeonDB/Supabase/Xata (46K chars ingested).
- **ATTACK SURFACE:** PostGIS `address_standardizer` missing bounds check in `classify_link()` — user-controlled `Type`/`Weight` rule values → OOB write primitive (CVE-2026-73514). Chained with a memory-disclosure bug to flip `rolsuper` on local backend caches ("shadow superuser" — stays under vendor monitoring) → superuser → RCE in production on NeonDB, Supabase, Xata. Claims: 40+ vulns in the PG extension ecosystem, 5 undisclosed PostgreSQL-core RCE 0-days (v14–19), privilege-relaxation design flaws in managed Postgres.
- **ACTIONABLE LEAD:** Aiven's Bugcrowd scope explicitly includes managed DB services (PostgreSQL, MySQL, OpenSearch, Kafka, ClickHouse, Valkey); Supabase is a HackerOne VDP. Probe the managed-DB threat model: extension allow-lists, cross-tenant isolation, and privilege-relaxation logic — not just the web console.

## 26. https://nopnop.pro/posts/google-cloud-application-integration-sandbo
- **WHAT:** Truncated URL — 404; web search did not recover the correct URL.
- **ATTACK SURFACE:** n/a.
- **ACTIONABLE LEAD:** None — skip.

## 27. https://oblique.security/blog/hacking-saml/
- **WHAT:** "Hacking SAML with Claude Code" — AI-assisted audit of SAML libraries (fetched, 9.8K chars).
- **ATTACK SURFACE:** Full auth bypasses found in 4 projects: Authentik (comment injection in NameID truncates to another user's account — CVE-2026-57580, e.g. `<NameID><?p not-an-?>admin@example.com</NameID>`), PHP litesaml/lightsaml, OneUptime, Java saml-client (signature wrapping on Response). 12 more signature bypasses in non-Response messages (AuthnRequest/AttributeQuery/LogoutRequest — rarely audited). DoS: XSLT transforms in Python libs (unfixed), quadratic memory in Go's xmldsig (patched), xmldom (private). Research corpus: `github.com/oblique-security/saml-research`.
- **ACTIONABLE LEAD:** Feed into the existing `sso` playbook: on any target with SAML SSO, test (a) NameID comment/PI injection (`<?...?>`, `<!--...-->` truncation), (b) signature wrapping (duplicate/move Assertion), (c) unsigned non-Response messages. Newly written SAML integrations are the softest targets.

## 28. https://potato.id/en/posts/i-accidentally-logged-into-threat-actor-website/
- **WHAT:** Threat-actor malware panel takeover via exposed installer (fetched, 8.3K chars).
- **ATTACK SURFACE:** ffuf found `/admin/login.php`, `/config/database.php`, `/install/install.php` on a live production app. Re-running the installer (no already-installed check) with an attacker-controlled MySQL instance → created admin account → valid session (PHP server-side sessions survived the threat actor's DB fix). IOCs: `micronsoftwares[.]com`, `wetransfer[.]icu`.
- **ACTIONABLE LEAD:** Add exposed-installer/setup probes to `hunter.py` expose checks: `/install/install.php`, `/install.php`, `/setup`, `/admin/installer`, `/wp-admin/install.php` on forgotten subdomains — a live bug class that still yields full admin.
