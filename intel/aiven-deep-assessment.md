# AIVEN — Deep Security Assessment
**Date:** 2026-09-26 | **Researcher:** shiva92 | **Program:** Bugcrowd aiven-mbb-og ($50–$25,000)
**Method:** Manual, unauthenticated analysis (no scanners, single-digit request volume). Test accounts were still being created during this assessment — all authenticated cross-account tests are documented as ready-to-run.

## 1. Executive summary

The unauthenticated attack surface of Aiven's in-scope assets is **well-hardened at the perimeter**: Cloudflare in front of everything, HSTS everywhere, `X-Frame-Options: deny` on console and API, no open S3 buckets found via headers, no secrets in the console JS bundle, no open redirect on the OAuth authorize endpoint, and the 96+55 public GitHub repos contain only tooling mirrors.

Three findings came out of the unauthenticated pass, none above Medium:

1. **(Low, confirmed)** `POST /v1/oauth2/token` returns raw PostgreSQL errors including the internal schema/function name (`funcs_26_7_0_8672_g52e229fc7605b.oauth2_client_get`) and SQLSTATE — verbose error disclosure, and notable because input parsing happens *before* authentication on this endpoint.
2. **(Low, confirmed)** `api.aiven.io` reflects any `Origin` in `Access-Control-Allow-Origin` (no `Allow-Credentials`). Real-world impact is limited because the API uses the `aivenv1` Authorization header, not cookies — but any website can read unauthenticated API responses in a victim's browser, and the allowlist should be strict.
3. **(Medium, high-confidence suspected)** The public, unauthenticated `regatta.aiven.io` SPA ships its internal Admin API OAuth `clientSecret` (`OAUTH_B`) in a world-readable config JS, used in the authorization-code token exchange against `https://admin-api.aiven.io:4343/v1`. Whether the secret is accepted as a confidential client could not be validated — `admin-api.aiven.io` is **not** in the program's in-scope list, so no request was sent to it. Needs scope confirmation, then one token-exchange attempt.

Strong leads for the authenticated phase (the program's stated P1 class): user-enumeration oracles on `userauth` / `password_reset_request` / `login_options` (differential not yet confirmable without a valid account email), and the full cross-account IDOR battery against service UUIDs, backups, deprecated `/v1/account/{id}` paths, and Kafka SASL cross-auth — all written up as ready-to-run test cases in §5.

The sanctioned exploit sandbox (`falcon-bug-bounty-flag-pgsql-dev-sandbox.e.aivencloud.com`) resolves to **132.145.163.127** with TCP/22 and TCP/5432 reachable, but SSH host-key retrieval is blocked by this assessor's egress policy — exact commands to finish the challenge from an unrestricted host are in §8.

**Bottom line: no critical or high-severity issue was confirmed on the unauthenticated surface. The money is in the authenticated cross-account tests (§5), which are fully scripted and waiting on the two trial accounts.**

## 2. Scope verification & asset inventory

Dossier (intel/programs-bugcrowd.md §4) is authoritative. Tested ONLY:

| Asset | Observed |
|---|---|
| `console.aiven.io` | 200, Cloudflare, HSTS, `X-Frame-Options: deny`, CSP (frame-ancestors aiven.io). SSO via Okta/Google/Microsoft (form-action). React SPA. |
| `api.aiven.io` | 301 → `/doc/` (public OpenAPI 3.0.1, **341 paths**). `X-Frame-Options: deny`, HSTS. Auth: `Authorization: aivenv1 <TOKEN>` header or OAuth2 (authorize `console.aiven.io/oauth/authorize`, token `api.aiven.io/v1/oauth2/token`). |
| `aiven.io` | Marketing site. `Access-Control-Allow-Origin: https://aiven.io` on root. Deprioritized per brief (heavily duped). |
| `regatta.aiven.io` | 200, React SPA "Aiven Regatta" served **fully unauthenticated**, including `/config.<ts>.js` with internal OAuth client credentials and `ADMIN_API_BASE_URL: https://admin-api.aiven.io:4343`. |
| Sandbox `falcon-bug-bounty-flag-pgsql-dev-sandbox.e.aivencloud.com` | A 132.145.163.127; TCP 22 + 5432 reachable (see §8). |
| GitHub orgs `Aiven` (96 repos), `Aiven-Open` (55 repos) | Public tooling mirrors only; no secrets found in listing pass. |

Out of scope — NOT touched, flagged as leads: `admin-api.aiven.io:4343` (referenced by in-scope regatta config), `mcp.aiven.live` (MCP server referenced in console bundle + `X-MCP-*` CORS headers), `ai.aiven.io`.

## 3. Endpoint / parameter / role map (from public OpenAPI spec)

Auth model: every `/v1/*` path (except a small public set) requires `aivenv1` token or OAuth2 bearer. Public-without-auth confirmed: `GET /v1/service_types`, `GET /v1/service_versions`, `GET /v1/clouds`, `POST /v1/userauth`, `POST /v1/userauth/login_options`, `POST /v1/password_reset_request`, `POST /v1/password_reset`, `POST /v1/verify_email`, `POST /v1/password_strength`, `POST /v1/oauth2/token`, `GET /v1/doc/openapi.json`.

High-value authenticated families (for the two-account battery):

- **Services:** `GET/POST/PUT/DELETE /v1/project/{project}/service/{service_name}` — `ServiceGet` requires `service:secrets:read` (the documented permission boundary: existence vs. credential URIs).
- **Backups:** `ServiceBackupsGet` requires `service:configuration:write` — full data dumps.
- **Integrations:** `POST /v1/project/{project}/integration` (`project:integrations:write`) — bridges services; test cross-account source/target.
- **Deprecated:** `/v1/account/{account_id}/team/{team_id}/project/{project}` — live but deprecated; historically weaker authZ. (Unauthenticated probe returned 405, not 401 — method-gated before auth; test authenticated.)
- **Organizations:** 67 GET + 24 POST + 12 PUT + 11 PATCH + 20 DELETE under `/v1/organization/{organization_id}` — includes `permissions/project/{project_id}`, `application-users`, `user-groups`, `governance/access`, VPC peering.
- **Tokens:** `GET/POST/PUT/DELETE /v1/access_token[/{token_prefix}]` — token of removed member still valid? scope escalation at creation?
- **Kafka:** ACL CRUD (`/acl/{kafka_acl_id}`), topics, quotas, schema-registry ACLs, connectors, MirrorMaker flows — SASL cross-auth tests live here.
- **ClickHouse:** `POST /v1/project/{project}/service/{service_name}/clickhouse/query` — **executes arbitrary SQL**; prime privilege-boundary target (can a low-priv role run it?).
- **Billing:** `/v1/billing-group`, `/v1/card`, invoices — IDOR across orgs; card metadata leakage.
- **VPC:** project + organization VPC peering create/approve/delete — peer into a project you don't own.
- **Users/teams:** invites, `invitation/{user_email}`, role assignment on accept — tamper `role` in invite-accept.

## 4. Confirmed vulnerabilities

### F1 — Verbose PostgreSQL error disclosure on /v1/oauth2/token
- **Severity:** Low | **Asset:** `api.aiven.io` | **Confidence:** Confirmed
- **Preconditions:** None (unauthenticated).
- **Root cause:** Exception handler serializes raw database errors to the API response, including schema-qualified function names.
- **Minimal reproduction:** `curl -X POST https://api.aiven.io/v1/oauth2/token -d "grant_type=authorization_code&code=fake&client_id=test"` → HTTP 400 with `InvalidTextRepresentation: invalid input syntax for type uuid: "test" ... funcs_26_7_0_8672_g52e229fc7605b.oauth2_client_get('test'::...` and SQLSTATE `22P02`.
- **Evidence:** Full response saved at `/tmp/aiven/oauth-err.json`. Reveals: Postgres-backed function API, internal naming convention (`funcs_<ver>_<hash>`), UUID-typed `client_id`, and that input parsing occurs before authentication on this endpoint.
- **Impact:** Information disclosure aiding further attacks (schema/function enumeration); no direct data access.
- **Remediation:** Map DB exceptions to generic error codes; log details server-side only.

### F2 — CORS origin reflection on api.aiven.io
- **Severity:** Low | **Asset:** `api.aiven.io` | **Confidence:** Confirmed
- **Root cause:** `Access-Control-Allow-Origin` echoes any request `Origin` (verified with `https://evil.example.com` on both preflight and actual GET); `Allow-Methods` includes DELETE/PUT/PATCH; no `Allow-Credentials`.
- **Reproduction:** `curl https://api.aiven.io/v1/service_types -H "Origin: https://evil.example.com"` → response carries `access-control-allow-origin: https://evil.example.com`.
- **Impact:** Limited — API auth is the non-ambient `aivenv1` header (no cookies), so a malicious site cannot steal an authenticated session cross-origin. It can, however, read all *unauthenticated* API responses in a victim's browser context and gets a clean error oracle. Defense-in-depth failure; some Bugcrowd programs pay P4 for this class.
- **Remediation:** Strict origin allowlist (console.aiven.io and known clients); consider `Vary: Origin`.

### F3 — Internal Admin API OAuth clientSecret exposed in public Regatta config (suspected)
- **Severity:** Medium (suspected) | **Asset:** `regatta.aiven.io` (exposure point; in scope) | **Confidence:** High (exposure confirmed; exploitability unvalidated — out-of-scope host)
- **Evidence:** Unauthenticated `GET https://regatta.aiven.io/config.2026-09-24T10:22:46Z.g7f75ea7095dd.js` returns `window.REGATTA_ENV = { OAUTH_A: 'lJXuUHUevuBUwhv8', OAUTH_B: 'lJb2B3jfp57OZJ43c9kewmYJk29Ltlh8', OAUTH_FLOWS: ['okta'], ADMIN_API_BASE_URL: 'https://admin-api.aiven.io:4343' }`. The app bundle (`assets/index-Bvn3J7Lg.js`) calls `authOauthTokenCreate({grantType: AuthorizationCode, code, clientId: OAUTH_A, clientSecret: OAUTH_B})` against `${ADMIN_API_BASE_URL}/v1`.
- **Why it matters:** If the admin API treats this as a confidential client, the publicly embedded secret breaks that assumption and lets anyone drive the admin OAuth flow as the internal Regatta client. If it's a public client + PKCE, impact is nil.
- **Not tested:** `admin-api.aiven.io:4343` is not in the program scope — zero requests sent. **Next step:** confirm scope with the program, then attempt one authorization-code exchange and observe whether the secret is actually validated.
- **Remediation (if confirmed):** Move the exchange server-side or switch the SPA to PKCE public-client flow; rotate the secret.

## 5. High-confidence suspected issues / ready-to-run authenticated tests

### S1 — User-enumeration oracles on auth endpoints (needs one valid email to confirm differential)
- `POST /v1/userauth` with `{"email":"t@t.com","password":"x"}` → **403 `{"message":"User does not exist"}`**. Wording implies a distinct branch for existing users (likely "invalid password").
- `POST /v1/password_reset_request` with fake email → same `User does not exist` shape.
- `POST /v1/userauth/login_options` with fake email → **200 `[{"action":"signup"}]`** — an existing user almost certainly gets login actions instead.
- To confirm: replay each with one known-valid account email (the trial accounts, once created) and diff. If the branches differ → confirmed enumeration (typically P4/P3).

### S2 — Ready-to-run cross-account IDOR battery (the P1 class; run the moment both trial accounts exist)
With Account A (project `proj-a`, one PG + one Kafka service) and Account B (project `proj-b`):
1. `GET /v1/project/proj-b/service/{A_pg_uuid}` with B's token → must be 403/404.
2. `GET /v1/project/proj-a/service/{A_pg_uuid}` with B's token (A's real project name) → must be 403/404.
3. Lowest-role member of org A calls `ServiceGet` on A's service → connection URI (with password) must NOT be returned without `service:secrets:read`.
4. `ServiceBackupsGet` from B against A's service → must fail.
5. `ServiceIntegrationCreate` from B with `sourceServiceName` = A's Kafka service → must fail.
6. `POST /v1/project/{project}/service/{service_name}/clickhouse/query` as low-priv member → must be denied (arbitrary SQL execution!).
7. Deprecated `GET /v1/account/{A_id}/team/{T_id}/project/{A_project}` with B's token → must fail.
8. Kafka: B's SASL credentials against A's broker host:port → must be rejected (data-plane isolation).
9. `GET /v1/organization/{A_org}/permissions/project/{A_project}` with B's token → must fail.
10. Invite flow: tamper `role` in invite-accept; accept expired/revoked invite; enumerate invite tokens.

### S3 — Out-of-scope leads (request scope confirmation before touching)
- `admin-api.aiven.io:4343` — internal Admin API referenced by in-scope regatta config (see F3).
- `mcp.aiven.live` — MCP server referenced in console bundle; API sends `X-MCP-Tool-Name`/`X-MCP-Client` headers, indicating a live MCP surface (prompt-injection target class).
- `ai.aiven.io` — referenced in console bundle; purpose unknown.

## 6. False positives eliminated

- **CORS ≠ session theft:** reflected origin is real, but without `Allow-Credentials` and with header-based (`aivenv1`) auth, no ambient credential exists to steal. Downgraded to Low.
- **OAuth `redirect_uri` open redirect:** `GET /oauth/authorize?...&redirect_uri=https://evil.example.com/cb` returns HTTP 200 error page, no redirect issued. Not vulnerable.
- **Console bundle secrets:** 6.5 MB `main.*.bundle.js` grepped for `apiKey/secret/token` patterns and `pk_live/pk_test` — only placeholders, no live secrets.
- **Sandbox IP confusion:** local DNS returned `198.18.219.250` (egress-proxy artifact); Cloudflare DoH confirms the real external IP is **132.145.163.127**.
- **GitHub orgs:** 96 + 55 public repos are upstream mirrors and Aiven's own tooling (incl. their offensive `pghostile` tester) — no credential leaks in the listing pass.
- **Rate limiting:** 3 sequential bad logins → consistent 403s, no 429/`Retry-After`. Not conclusive of missing rate limiting (Cloudflare may throttle at higher volume); not claimed as a finding.

## 7. Remediation priorities

1. Confirm scope for `admin-api.aiven.io:4343` and validate F3 (highest potential impact).
2. Confirm S1 enumeration differentials once trial accounts exist (cheap, likely valid).
3. Run the §5-S2 cross-account battery — this is the program's stated P1 class.
4. Fix F1 (generic error mapping) and F2 (strict CORS allowlist) — cheap hardening.

## 8. Reproduction evidence & sandbox notes

- OpenAPI spec: `/tmp/aiven/openapi.json` (341 paths); regatta app bundle: `/tmp/aiven/regatta-app.js`; console bundle: `/tmp/aiven/console-main.js`; OAuth error: `/tmp/aiven/oauth-err.json`.
- Sandbox: `falcon-bug-bounty-flag-pgsql-dev-sandbox.e.aivencloud.com` → **132.145.163.127** (DoH-verified). TCP/22 and TCP/5432 reachable from this network. Postgres SSLRequest probe returned an unexpected `0x6d` byte followed by connection reset (non-standard handshake behavior — possibly a filtering proxy; inconclusive).
- **Blocked by assessor environment:** outbound SSH is disabled in this sandbox, so the SSH host key could not be retrieved. From an unrestricted host, run:
  `ssh-keyscan -t rsa,ecdsa,ed25519 falcon-bug-bounty-flag-pgsql-dev-sandbox.e.aivencloud.com` (host key),
  `ssh -v -o PreferredAuthentications=none <host>` (offered auth methods),
  then attempt the challenge's intended path and record key + external IP + method for the report.
- All requests used `User-Agent: Mozilla/5.0 (hackerone-shiva92)`, single requests, no automation.
