# Recon Synthesis — Kiteworks hunting environment
Agent #15 (synthesizer), 2026-09-27. Sources: obs_recon.jsonl (66 observations, agents 3,5,7,9,10,11,13,14)
+ WORLD_MODEL.md (seed + corrections from agents 14, 20, 5, 35).

Only the host ywh-kw-public.bounty.kiteworks.dev is confirmed in scope. Nothing here is a finding.

## Confirmed picture

- Target is a React/webpack SPA login shell: HTTP 200 on `/`, 2346-byte shell, 21 hashed JS chunks
  + named `signin.f7b86212.js` entry, 2 CSS bundles, `<div id="app">`, `<meta robots=noindex>`. Root `/` renders the sign-in view directly (route-split signin chunks loaded on `/`).
- Security headers are strict: HSTS max-age=63072000 + includeSubdomains, CSP `default-src 'self'; script-src 'self'; frame-ancestors 'self'`, X-Frame-Options SAMEORIGIN, X-Content-Type-Options nosniff, Referrer-Policy strict-origin-when-cross-origin, restrictive Permissions-Policy, Cache-Control no-store/no-cache. No `Server`/`X-Powered-By` leak.
- No session cookie set on unauthenticated GET; vendor docs describe OAuth access-token-in-JS sessions post-auth.
- Tech stack: still UNDETECTED beyond React/webpack frontend. No backend framework confirmed.
- CT enumeration: only 2 non-wildcard names under bounty.kiteworks.dev — apex + `ywh-kw-res-h3.bounty.kiteworks.dev` (dedicated Let's Encrypt cert, 2026-07-25→2026-10-23, matching ywh-kw-* hunting-infra naming). Hunting host rides a DigiCert wildcard `*.bounty.kiteworks.dev` (renewed yearly since 2021) — CT is inherently incomplete for this zone; other wildcard-hidden hosts may exist with no CT visibility.
- `ywh-kw-res-h3.bounty.kiteworks.dev` scope status = UNCERTAIN (same-infra naming but NOT explicitly listed; passive-only until operator confirms in YesWeHack UI). Apex is out of scope.
- Documentation-grade API surface: `/rest/` base (Core API v28, Pub-Sub v1), interactive docs at `/rest/index.html`; OAuth 2.0 with 7 grant types incl. JWT user-impersonation bearer flow; unauthenticated surface = `/rest/public/mail/*`, `/rest/requestFile/{ref}/*`, `/rest/shortLinks/{ref}` (ref-token gated); chunked upload sessions via `/rest/uploads/{id}` + `GET /rest/uploads/config`; DLI bulk export API (`/rest/dli/exports`, per-user cross-user export); SCIM provisioning; `GET /rest/users/ldapSearch`; access-verification step-up endpoints. None of this is live-verified on the hunting env.
- Auth model (docs): username/email → Next → password → optional 2FA (SMS/TOTP/email passcode/RSA/YubiKey), cert auth, SSO/SAML 2.0 (SimpleSAMLphp-style ACS at `/sp/module.php/saml/...`), LDAP/AD/LDAPS + Kerberos, trusted-device 2FA skip, CAPTCHA on failed logins, admin-configurable lockout. "Forgot Password" → `/rest/users/requestPasswordReset` + `/rest/users/resetPassword` (exact token mechanism undocumented publicly).
- Role model (docs): 3 layers — user profiles (privilege bundles; users start with ZERO privileges until profile assignment), admin tiers (system > application; 8 default + custom delegated roles; docs claim users cannot self-promote to system admin), folder roles Owner/Manager/Collaborator/Downloader/Uploader/Viewer.
- Integration surface (docs): LDAP/AD drives identity AND role/profile assignment (program focus: LDAP injection); SAML assertions trusted for auth (and possibly role assignment); 2FA via RADIUS or email OTP; EPG consumes M365 MIP sensitivity labels + RMS in policy rules; AV = embedded WithSecure Atlant (16TB file limit); DLP/ATP/CDR delegated to external ICAP servers (Forcepoint, Digital Guardian, Check Point SandBlast, Trellix); content connectors = SharePoint, SMB/CIFS/DFS, Documentum, OpenText, GDrive, Box, Dropbox, Salesforce, iManage, M365; clients = iOS/Android/desktop/Outlook plugins; Kiteworks MCP Server (9.5+, OAuth app, localhost:9999 callback) + AI Data Gateway.
- Highest-value unverified leads: `/login_config` (server-generated JS script tag exposing auth config client-side; answers open questions 2 & 5), `/rest/index.html` (live API surface), `/dbrand/theme/~cache/branding` (tenant-reflecting theme endpoint), browser-support scripts (legacy code paths).

## Conflicts / contradictions

1. **robots.txt / security.txt exist vs don't**: the passive dossier claims `/.well-known/security.txt` and `/robots.txt` exist; agents 9 and 7 report GET `/robots.txt` timed out. Status: UNCONFIRMED either way — timeouts are indistinguishable from non-existence under current network conditions.
2. **Tarpit vs egress outage**: agent 9 sees a path-based tarpit pattern (only `/` returns 200; 8/8 non-root paths time out), while agents 13/7/5 see a general sandbox egress outage (example.com, urlscan.io, Wayback also time out). Both are compatible — egress is degraded AND/OR the host tarpits non-root paths. Do not design tests assuming either.
3. **Airflow lineage**: dossier claims MFT has Apache Airflow lineage; agent 14 found vendor MFT materials describe a proprietary "next-generation flow engine" with NO Airflow mention. Treat Airflow as unverified; no hypotheses should depend on it.
4. **TLS/host state at collection time**: host returned HTTP 200 ~05:20 UTC but was fully unreachable ~06:00–06:10 UTC from sandbox; no handshake completed, so no cert/issuer/SAN data was captured this pass. The world model records A=3.0.1.193 from an earlier DoH lookup — sandbox-local DNS returns RFC benchmarking-range artifacts (198.18.92.x), not real resolution.

## Missing (no agent delivered)

- Agents 1, 2, 4, 6, 8, 12 did NOT append observations (asset mapper, DNS mapper detail, HTTP fingerprint beyond headers, port/service mapper, API mapper, historical surface). Their recon angles remain open.
- Live-verification of everything docs-grade: tech stack, `/rest/` reachability on this env, `/login_config` contents, cookie/token model, actual enabled auth integrations, actual TLS cert on the hunting host.
- JS bundle contents: no bundle fetched → no source maps, no embedded API paths, no React/library versions, no feature flags.
- robots.txt / security.txt existence and contents.
- `/rest/index.html` live API docs on the hunting host.
- Any evidence the res-h3 host is in scope.
- All sandbox-local DNS/TLS outputs must be re-verified from a network with a working route (egress degraded throughout this pass).

## World-model corrections / flags (do not edit WORLD_MODEL.md directly)

1. robots.txt + security.txt: marked "confirmed facts (passive)" in the seed — downgrade to UNCONFIRMED; dossier claim vs. direct GET timeouts, no resolution possible this pass.
2. MFT Apache Airflow lineage: flagged as "VERIFY before using" — strengthen: vendor MFT materials actively describe a proprietary flow engine; treat Airflow as unverified, and warn differential/known-vuln agents not to build on Airflow CVEs.
3. Scope note: add `ywh-kw-res-h3.bounty.kiteworks.dev` (LE cert 2026-07-25, ywh-kw-* naming) as explicitly UNCERTAIN — same-infra naming ≠ authorization; operator must confirm in YesWeHack UI before any active testing.
4. Sandbox DNS: record that local resolution returns 198.18.92.x (RFC benchmarking range, sandbox artifact) and sandbox-to-target TLS was impossible this pass — any future "no cert" observations need a healthy-egress re-run.
5. World model "Open questions": add — (a) does `/rest/index.html` resolve live on this env; (b) what does `/login_config` disclose; (c) which auth integrations are enabled on THIS instance; (d) why non-root paths time out (tarpit/WAF whitelist vs egress).

---
3-line summary:
Recon confirms the hunting host is a hardened React SPA login shell with strict security headers, docs-grade `/rest/` API v28 + deep integration surface (LDAP/SAML role assignment, ICAP-verdict delegation, MCP OAuth), but tech stack, auth integrations, and API reachability remain live-unverified — the whole pass was degraded by a sandbox egress outage, with 6 of 14 agents delivering nothing and `/login_config` unfetched as the top open lead.
