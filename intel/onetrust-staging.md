# OneTrust Staging Assessment — pentest-app.onetrust.com
**Date:** 2026-09-26 | **Scope verified:** Bugcrowd OneTrust brief (dossier: `intel/programs-bugcrowd.md` §15, `intel/program-rules-matrix.md`). ONLY `pentest-app.onetrust.com` staging is payout-eligible. Rewards $300–$6,500. Full safe harbor (CFAA/DMCA/ToS waived). Scanner policy: not explicitly banned — testing kept to gentle manual-style probing regardless.
**Out-of-scope classes (brief):** XSS-with-sanitization-disabled, CSRF, rate limiting, tinyMCE, auth issues without FULL Site Admin escalation, host-header without user-data proof, outdated libs, clickjacking on non-sensitive pages, anything outside staging.

## Method
Unauthenticated only. No browser available to this agent; the admin test credential lives behind the Bugcrowd brief's retrieve-credential section (login required) — **authenticated testing is blocked pending parent/browser retrieval of that credential.**

## Surface map
- Angular SPA shell (`<mfe-root>`), bundles: `runtime.*.js`, `polyfills.*.js`, `main.6510063f249117c0.js` (~1.1 MB). Cloudflare-fronted, HSTS (preload), `X-Frame-Options: SAMEORIGIN`, `nosniff`, restrictive CSP.
- API base paths (same host): `/api/access/v1/*` (auth, oauth, tenants, users, orgs, permissions), `/api/content/v1/*`, `/api/global-state/v1/*`, `/api/globalization/v1|v2/*`, `/api/branding/v1/*`, `/api/atlas/v1/*`, `/api/alert/v1/*`, `/api/watchdog/v1/*`, `/api/benchmarking/v1/*`, `/api/salesops/v1/*`, `/api/v1/private/*`.
- Auth: OAuth2/OIDC code flow; token endpoint `/api/access/v1/oauth/token`; Bearer tokens; IdP appears external (`my.onetrust.com` — production IdP, NOT payout-eligible, not tested).

## Findings
**No confirmed vulnerabilities on the unauthenticated surface.** Specifically eliminated:
1. **Debug exposure — none.** `/actuator`, `/actuator/health`, `/debug`, `/console`, `/v3/api-docs`, `/api-docs`, `/graphql`, `/api/graphql` → all 401. `/swagger-ui.html` and `/.well-known/openid-configuration` → 200 but serve the SPA fallback shell, not real docs.
2. **Verbose errors — none.** Malformed POST to token endpoint → empty 401. Wrong method → clean JSON `{"errors":[{"code":"ERROR_GENERIC_OPERATION_FAILED",...}],"traceId":"…"}` — no stack trace. Path traversal probe → generic 400.
3. **Auth bypass via method tampering — none.** GET/POST/PUT/DELETE/PATCH on `/api/access/v1/tenants/current` → consistent 401.
4. **CORS misconfig — none observed.** Evil-Origin GET on public endpoint → no `Access-Control-Allow-Origin` reflected.
5. **Client secrets — none.** No API keys, client secrets, internal hostnames, or debug flags in the shell JS bundle.
6. **Public endpoints are benign:** `/api/global-state/v1/no-auth-init` (languages, marketing content, CDN asset URLs), `/api/content/v1/info/version` → `202609.1.9`, `/api/globalization/v1/languages`, `/api/content/v1/attributes` (captcha URL, feature flags).

## High-confidence leads for the authenticated phase (need admin credential)
1. **Client-driven privilege context on OAuth flow (top lead).** Bundle shows the token/login flow accepts client-set query params: `tenant_id`, `orggroup_id` (= `organization_id`), `role_id`, `switchRole`, `context`, `contextVersion`. Test: low-priv user sets `switchRole`/`role_id` of a Site Admin, or swaps `tenant_id`/`orggroup_id` to another tenant's — classic privilege-boundary failure. Brief requires FULL Site Admin escalation for auth findings, so partial wins don't pay; aim for the full chain.
2. **DSR webforms/workflows IDOR.** Brief's explicit focus area ("IDOR heaven"). With two privilege levels: create data-subject requests as low-priv user A, then access/modify as user B; tamper `orggroup_id`/request IDs.
3. **Integrations module.** Brief focus: integrations that reach customer environments — test for SSRF/credential exposure in integration config (read-only, report the primitive, no pivoting).
4. **`/api/v1/private/orggroupuser/get`** — "private" endpoint; probe for IDOR on user/org identifiers once authenticated.

## Eliminated / not pursued
- User enumeration via token endpoint: single-probe only, and brief excludes auth issues without full Site Admin escalation — not valuable, not tested further.
- Cookie flags: could not verify (runtime redacts Set-Cookie values in tool output).
- `my.onetrust.com` IdP: production, non-staging → $0 payout, not tested.

## Recommended next step
Parent: retrieve the admin-level test credential from the Bugcrowd brief (retrieve-credential / forgot-password flow) via a logged-in browser task, then run the 4 authenticated leads above with two privilege levels.
