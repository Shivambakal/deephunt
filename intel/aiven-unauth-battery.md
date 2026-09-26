# AIVEN — Unauthenticated Attack-Surface Battery
**Date:** 2026-09-26 | **Researcher:** shiva92 | **Program:** Bugcrowd aiven-mbb-og ($50–$25,000)
**Method:** Unauthenticated only. ~60 single curl requests, `User-Agent: Mozilla/5.0 (hackerone-shiva92)`. No scanners, no brute force, no DoS, no credential stuffing. Builds on `aiven-deep-assessment.md` (F1–F3 already reported there — not repeated here).

## CONFIRMED FINDINGS

### U1 — User enumeration via POST /v1/userauth/login_options (Low, Confirmed)
- **Repro:**
  - `curl -X POST https://api.aiven.io/v1/userauth/login_options -H 'Content-Type: application/json' -d '{"email":"no-such-user-zzz-987654321@gmail.com"}'` → `200 [{"action":"signup"}]`
  - Same request with a real account email (`attacksurface.alerts@gmail.com`, own test account) → `200 [{"action":"google_oauth","method":"POST","redirect_url":"/v1/sso/google_oauth/redirect?action=login"}]`
- **Root cause:** endpoint returns the account's available login methods vs. a signup prompt; response body differs by account existence. Both HTTP 200.
- **Impact:** attacker can validate which emails have Aiven accounts (phishing/targeting recon). Timing differential negligible (0.80s vs 0.69s, single samples) — oracle is message-based.
- **Remediation:** return a uniform response (e.g. always `[{"action":"signup"}]`-shaped or a neutral "if an account exists, check your inbox" flow); rate-limit the endpoint.
- **Confidence:** Confirmed (valid vs invalid differential reproduced).

### U2 — User enumeration via POST /v1/userauth message differential (Low, Confirmed)
- **Repro:**
  - Nonexistent email + any password → `403 {"message":"User does not exist"}`
  - Valid email + wrong password → `403 {"message":"Authentication failed"}`
- Same status code, distinct messages = reliable oracle. (Prior assessment suspected this; now confirmed against a known-valid account.)
- **Remediation:** single generic message ("Authentication failed") for both branches.
- **Confidence:** Confirmed.

### U3 — CORS origin reflection is API-wide (Low, Confirmed — extends F1-report F2)
- Reflected `Access-Control-Allow-Origin: https://evil.example.com` verified on: `GET /v1/service_types`, `/v1/clouds`, `/v1/service_versions`, `POST /v1/oauth2/token`, and `POST /v1/userauth/login_options` **with a valid JSON body** (actual request, not just preflight).
- Preflight (`OPTIONS /v1/userauth/login_options`) also reflects origin and advertises broad methods (`DELETE, GET, OPTIONS, POST, PUT, PATCH`) plus headers including `X-MCP-Tool-Name`, `X-MCP-Client`, `X-MCP-Transport` (confirms a live MCP surface), `X-Trial-Challenge`, `X-Signup-Welcome`, `X-Referral-Code`.
- No `Access-Control-Allow-Credentials` observed anywhere; API auth is the non-ambient `aivenv1` header, so cross-origin session theft is not possible. Impact stays defense-in-depth / P4-class.
- **Remediation:** strict origin allowlist; `Vary: Origin`.

## ELIMINATED / NOT FINDINGS

- **`POST /v1/user/password_reset_request`** (correct path; `/v1/password_reset_request` 404s): both nonexistent and valid emails → `200 {"message":"email sent"}`. No oracle. (Timing 0.87s vs 0.95s on single samples — not a reliable differential; not claimed.)
- **`POST /v1/pg/query/validate` and `/v1/mysql/query/validate`** (public, no auth): `query` must be **base64-encoded** SQL. Valid SQL → `200 {"status":"success"}`; invalid SQL → `400` with a JavaCC-style parser error (reveals Java SQL-parser tech, echoes the base64 input); **nonexistent table → `{"status":"success"}`**, i.e. parse-only, no schema resolution, no execution. Stacked queries also parse OK. SQLi-execution angle dead; parser-tech disclosure is info-level only.
- **`GET /v1/pg/database-metadata-query`**: returns the metadata-query SQL template (info disclosure of internal query structure, no data). Info only.
- **`POST /v1/account/{id}/invite/{code}`**: `410` — endpoint retired 2026-03-23, spec is stale. Dead end.
- **`GET /v1/project/{p}/download-sbom/{fmt}/{download_cookie}`** and invoice CSV endpoints: random cookie → `400`. Cookie entropy not assessable unauthenticated; no finding.
- **`GET /v1/user/credit_code/{code}`**, **`GET /v1/me/referral/validation/{code}`**: clean `400` on garbage. No oracle.
- **Debug/actuator surface:** `/actuator*`, `/health*`, `/metrics`, `/swagger-ui.html`, `/v3/api-docs`, `/graphql`, `/.well-known/*`, `/debug*`, `/status`, `/version`, `/info` → all `404` on `api.aiven.io`. On `console.aiven.io` they return `200` with identical 6785-byte body = SPA fallback serving index.html. Not a finding.
- **Malformed-input battery** on `/v1/userauth/login_options` (truncated JSON, wrong types, nested objects, 200KB oversized body, `text/plain` content-type): clean `400`s, no stack traces. One quirk: `text/plain` body returns `200 [{"action":"signup"}]` (unparseable input falls into the signup branch) — info-level logic note, not a vulnerability.
- **Trial-signup flow:** `v1/signup`, `v1/complete-signup`, `v1/subscription/activate` strings in the console bundle resolve to **AWS/Azure marketplace** endpoints (`/marketplace/aws/v1/complete-signup`, `/marketplace/azure/v1/subscription/activate`), not trial signup. No client-side validation bypass or tamperable trial parameter found in static review. Actual trial signup is Google-OAuth-based (already exercised via browser).
- **Console bundle endpoint re-grep:** `v1/chat/completions`, `v1/jobs*`, `v1/overview`, `v1/summary` are authenticated console features; one obfuscated `v1/Hrl3JtU/...` string is a hash, not a route. No new unauthenticated endpoints.

## PASSIVE RECON (no active probing — out-of-scope leads only)

- **crt.sh, `%.aiven.io`:** 60 names. In-scope assets confirmed live: `console`, `api`, `regatta`, `www`, docs/blog/handbook (marketing). **Out-of-scope candidates — DO NOT TEST without scope confirmation:** `console-beta.aiven.io`, `staging.aiven.io`, `api-http2-preview.aiven.io`, `ts-admin.api.aiven.io`, `rest.aiven.io`, `iam.aiven.io`, `play.aiven.io`, `robjecter.aiven.io`, `nevia.aiven.io`, `admin-api.aiven.io` (already flagged), `*.internal.aiven.io`.
- **crt.sh, `%.aivencloud.com`:** 618 names — overwhelmingly per-customer wildcard instances (`*.{customer}-{hash}.aivencloud.com`); customer data plane, out of scope. Sanctioned sandbox host already documented in the deep-assessment report.

## REMEDIATION PRIORITIES (unauthenticated)

1. Unify `login_options` and `userauth` responses (U1, U2) — cheap, kills both oracles.
2. Strict CORS allowlist on `api.aiven.io` (U3).
3. Nothing else on the unauthenticated surface warrants a report above Low.

**Bottom line:** the unauthenticated surface yields two new confirmed **Low** user-enumeration findings (U1, U2) plus a broadened CORS note (U3). No Medium+ unauthenticated issue found. The P1 money remains in the authenticated cross-account battery.
