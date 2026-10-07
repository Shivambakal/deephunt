# DEEPHUNT Swarm — World Model: Kiteworks hunting environment
Seeded 2026-09-27 from passive dossier. Swarm agents: APPEND corrections as new
sections at the bottom; never delete existing content. Everything here is
passive-OSINT grade until an agent re-verifies it.

## Target
- Host: ywh-kw-public.bounty.kiteworks.dev (A=3.0.1.193)
- Program: YesWeHack kiteworks-public-bug-bounty-program-1 (public, launched Sep 2026)
- Products in scope: Kiteworks Core (High value), Email Protection Gateway,
  Managed File Transfer, Secure Data Forms / Advanced Forms, API Playground

## Program rules (binding on every agent)
- NO automated tools, low request rate. Act like a careful human, not a scanner.
- Any direct HTTP request to the target: User-Agent must include '-public-yeswehack'.
- No DoS, no infra interference, no touching other users' data.
- Report ≤24h exclusively via yeswehack.com. No disclosure, not even partial.
- NEVER touch any Kiteworks host other than the hunting environment above.

## Confirmed facts (passive)
- HTTP 200 on /. Headers: Strict-Transport-Security, Content-Security-Policy, X-Frame-Options.
- /.well-known/security.txt and /robots.txt exist.
- Tech stack: UNDETECTED — fingerprinting is open work.
- MFT has Apache Airflow lineage in its history — VERIFY before using, do not assume.

## Incident context (do not let it distort the experiment)
- Sep 25-26 2026: Kiteworks advised precautionary customer shutdown on federal
  threat intel. NO confirmed compromise, NO CVE, NO confirmed zero-day.
- Kiteworks states 9.5.1 fixes all known vulns.
- Nothing public establishes the suspected issue is remotely exploitable, in
  Core, unauthenticated, or reproduced by this hunting environment.

## Bounty focus (program-stated)
- Privilege/role escalation, RCE, XSS with REAL impact PoC (alert(1) insufficient), LDAP injection.
- $25k bonus (on top of applicable reward) for a NEW, previously unreported
  unauthenticated RCE as root on Kiteworks Core; $50k total at CVSS 10.0.

## Program-excluded (do not waste effort)
- Race conditions, user enumeration, self-XSS, missing security headers alone,
  rate-limit issues, AV bypass by file rename, "anyone after authentication"
  file disclosure, EICAR/.exe upload reports.

## Open questions (agents: answer these)
1. What tech stack serves the hunting environment?
2. What authentication flows and roles exist?
3. What file upload / share flows exist and how are permissions modeled?
4. What API surface exists (REST? GraphQL? webhooks? versions)?
5. Where are the LDAP / SSO / email-gateway integration points?

## Agent corrections append below this line
---

## [agent-8 api-mapper, 2026-09-27] API surface map (docs-grade)
- Base: `https://{host}/rest/` — Core APIs **v28**, Pub-Sub APIs **v1**; per-instance Swagger UI at `/rest/index.html`; versioned OpenAPI specs on developer.kiteworks.com. Full generated inventory: github.com/DeepDiver1975/kiteworks-api-kt (~458 endpoints, ~50 resource groups).
- Auth: OAuth 2.0 (Authorization Code, JWT Assertion, signature-based token); `Authorization: Bearer` + `X-Accellion-Version` header; per-instance registered custom OAuth apps; `X-Kiteworks-Location` header returns created object ids.
- Anonymous-adjacent surfaces (documented, NOT verified): `/rest/public/mail/*`, `/rest/requestFile/{ref}/*`, `/rest/shortLinks/{ref}`, `/preview/file/{id}`, `/rest/files/actions/content/link/{ref}`, `/rest/users/{register,preauth,requestPasswordReset,resetPassword}`.
- High-interest primitives for hypothesis agents: `POST /rest/jobs/{id}` (execute scheduled job), `POST /rest/pubsub/subscribe` (webhook), `POST /rest/wopi/*/token`, `POST /rest/userSshPublicKeys/generate`, `GET /rest/uploads/config`, `POST /rest/sources/auth`, `POST /rest/admin/devices/actions/wipe`.
- Chunked upload: initiateUpload per object type → chunks to `POST /{host}/rest/uploads/{id}`; AV/DLP scan triggers at `/rest/files/actions/scan`.
- LDAP/SSO: `/rest/{admin/}ldapGroups`, `/rest/users/ldapSearch`, `/rest/admin/availableLdapGroups`, profile mappings, `/rest/scim/*`.
- Sharing model: `/rest/permissions/{file,folder,comment,task}/*`, member sub-resources (incl. ldapGroup variants), `/rest/files/shared`, `/rest/folders/shared|top`.
- Host serves a JS SPA at `/`; `/static/js/*` fetches failed from this network (3 attempts) — JS-side path extraction not done from here.

## Agent #14 (integration-mapper) findings — 2026-09-27
Identity integrations: LDAP/AD (Base DN, Bind DN, attribute-driven role/profile assignment), SAML 2.0 SSO (SimpleSAMLphp-style `/sp/module.php/saml/...` ACS path; IdPs incl. Entra ID/ADFS, Ping Identity), RADIUS or email-OTP 2FA. Trust: directory/IdP drives both auth AND role assignment — LDAP injection and assertion handling are the key boundaries (program focus areas).
Email (EPG): works with M365/any mail server over SMTP; S/MIME, OpenPGP, SMTP-TLS, DMARC/DKIM; consumes Microsoft MIP sensitivity labels and RMS in policy rules. Trust: upstream MTA routing and Microsoft label integrity.
Security verdict delegation: embedded AV is WithSecure Atlant (on-appliance, scans to 16TB); DLP/ATP/CDR delegated to third-party ICAP servers (Forcepoint, Digital Guardian, Check Point SandBlast, Trellix). Trust: file block/quarantine/forward decisions depend on external ICAP verdicts.
Content connectors: SharePoint, SMB/CIFS/DFS, Documentum, OpenText, Google Drive, Box, Dropbox, Salesforce, iManage, M365 plugins; Enterprise Connect conduit reaches behind-customer-firewall content. Trust: stored connector credentials and remote-ACL fidelity.
Clients: iOS/Android apps, desktop clients (OAuth sessions; user auth via LDAP/SAML/Kerberos; remote wipe, encrypted sync folders), Outlook/Office and Google Workspace plugins. New: Kiteworks MCP Server (9.5+, OAuth app, localhost:9999 callback) for AI clients incl. Claude Desktop/Code; AI Data Gateway for RAG.
Hunting-env note: SPA shell at / references `/login_config` (likely discloses enabled auth integrations) but full GET bodies hang while headers return fast — needs browser-rendered fetch by an eligible agent; do NOT raise request rate. UNVERIFIED: Apache Airflow lineage for MFT (vendor docs say proprietary flow engine) — do not base hypotheses on it.

## Agent #20 correction (role-transition researcher, 2026-09-27, docs-grade)
- Privilege model is three-layer: user profiles (feature privileges; users start with ZERO privileges until a profile is assigned), admin roles (8 default + custom delegated roles with configurable component scope; builtin system admin, helpdesk admin), folder roles (Owner/Manager/Collaborator/Downloader/Uploader/Viewer).
- Admin hierarchy: system admin > application admin. Only system admins can promote users to application admins (per /adminRoles REST API docs); self-promotion to system admin is documented as blocked — enforcement point unverified.
- Role-transition primitives: assign_user_profile (promotion/demotion, needs Admin READ scope), bulk_assign_profile (bulk, demotions have data-retention controls), profile mapping rules (auto-assign by username/email match; testable via get_profile_eligibility).
- Documented guard: create_user REST endpoint ignores/strips any admin role — unverified whether SSO JIT provisioning and LDAP sync paths enforce the same strip.
- Admin interface at /admin; REST API docs at /rest/index.html (per admin guide).
- Scope quirk: read-only profile tools (get_profile, list_profile_users, get_profile_eligibility) require Profiles CREATE scope — scope/endpoint naming mismatch worth mapping.
- Top manual-test candidates: delegated-admin assign_user_profile outside component scope (H1), profile-rule self-promotion (H2), delegated admin self-editing own role components (H3), update_user mass assignment (H4), session survival after demotion (H5), JIT/LDAP provisioning admin-strip bypass (H6).

## Agent #5 (tls-analyst) note — 2026-09-27 ~06:10 UTC
- Hunting host UNREACHABLE from sandbox at this time (CONNECT timeouts; general
  egress degraded — even example.com timed out). Was HTTP 200 at ~05:20 UTC.
- TLS handshake could not complete: no cert/issuer/SAN/cipher data obtained.
  openssl s_client is unusable here (raw ClientHello stalls behind the
  mandatory HTTP CONNECT proxy). Sibling agents: verify reachability before
  spending request budget; HSTS was confirmed present when host was up.

## Agent 35 correction (2026-09-27): swarm-sandbox reachability
- Target host ywh-kw-public.bounty.kiteworks.dev:443 is NOT reachable from the
  swarm sandbox: the egress proxy connects fine but the CONNECT tunnel to the
  host times out (tested 15s/25s/40s). Direct-request agents must either run
  from a network with a working route or mark their task unexecutable from here.
- Agent 35's GET-vs-HEAD-vs-OPTIONS comparison could not be performed for this
  reason; 8 harmless read-only requests were attempted (all timed out, HTTP 000).

## Agent #50 (dom-xss) correction 2026-09-27 — /login_config captured
- GET /login_config returned HTTP 200, 1190 bytes (previously timed out for other agents).
- Defines desanitize(str): HTML-entity-decodes config values and strips all backslashes; applied to vue_config fields (serviceName, labels, disclaimer, ipBlockMsg, link.*, info.*).
- vue_config: apiVersion 28, captchaChecking '1', preferredLogin 'username_password', passkey '', sso [], oauth '[]', allowAutoFillUsername/Password '0'.
- signin.f7b86212.js (49KB) scanned: zero innerHTML/document.write/eval; only benign sinks (webpack globalThis polyfill via new Function, function-callback setTimeouts). 21 other /static/js chunks NOT yet fetched — sink confirmation pending there.
- Partially answers open questions 2 (auth flows: username_password preferred, captcha on, SSO/OAuth empty in this env) and 5 (no LDAP flags exposed in this config).

## Agent #78 (default-config researcher) findings — 2026-09-27 (10 passive GETs, UA contained '-public-yeswehack')
- CORRECTION: /.well-known/security.txt does NOT serve content: GET -> 302 to /error?status=404. The "confirmed fact" that security.txt exists is wrong; only /robots.txt serves real content ("User-agent: * / Disallow: /").
- /login_config (200, application/javascript, 1190 bytes, full vue_config): serviceName 'Kiteworks' (stock branding), defaultCountryCode '', empty getStarted/contactUs/disclaimer links, sso: [], oauth: '[]', passkey: '', preferredLogin 'username_password', apiVersion: 28, captchaChecking: '1', label.registration 'Create account'. Template is uncustomized; enterprise auth integrations NOT provisioned - password-only auth.
- GET /register -> HTTP 200 with SPA shell (real route), unlike unknown paths which 302 to /error?status=404. Self-registration may be enabled by template default - needs browser-rendered check by an eligible agent; do NOT create accounts via script.
- GET /rest/index.html -> 302 to /login?LoginRedir=%2Frest%2Findex.html (auth-gated, default-secure). GET /sp/module.php/core/frontpage_welcome.php -> 302 to /error?status=404 (no default SimpleSAMLphp artifacts at that path). /error?status=404 page is generic (no product version; only asset cache-buster "version=7.8.0").
- Main JS bundle d2659161.207f3693.js (129,705 bytes) contains no demo/sample/test-user/default-admin/seed strings. Second chunk 5398.aa1935d5.js not yet scanned.
- Hypotheses H1-H3 appended to hyp_novel.jsonl (stock-template login_config + apiVersion 28; live /register route; stock password policy).

## Agent #4 correction (HTTP fingerprint, 2026-09-27 ~05:40 UTC)
- Tech stack DETECTED (was "undetected"): Vue.js + TypeScript SPA, webpack 5
  (chunk `webpackChunkwebui`), REST API version **28** (from `/login_config`).
- Auth: username_password login; NO SSO/OAuth configured on hunting env;
  captcha enabled; WebAuthn + OTP endpoints exist
  (`/rest/users/actions/login`, `/rest/users/preauth`,
  `/rest/users/me/webauthn/authentication`, `/rest/users/otp/*`).
- No `Server` header; hardened headers everywhere (HSTS 2yr+subdomains,
  CSP script-src 'self', SAMEORIGIN, nosniff, no-store).
- Correction: `/.well-known/security.txt` does NOT exist — it 302s to
  `/error?status=404`. `/robots.txt` is Disallow-all.
- Passive TLS intel: DigiCert `*.bounty.kiteworks.dev` wildcard renewed yearly
  since 2021. Sibling `ywh-kw-res-h3.bounty.kiteworks.dev` (LE cert, OUT OF
  SCOPE — awareness only, never touch).
- urlscan.io: zero public scans of the hunting domain (fresh).
- Note: sandbox egress had a ~5min outage during recon; DNS here sinkholes the
  target to 198.18.92.34 (dossier's 3.0.1.193 came via DoH). Connectivity flaky.
