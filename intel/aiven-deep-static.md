# Aiven — Deep Static Attack-Surface Analysis

Passive only. No logins, no state-changing requests. Sources: public console JS
bundles from `https://console.aiven.io/` (7 bundles, fetched 2026-09-26),
official OpenAPI spec `https://api.aiven.io/doc/openapi.json` (v3.0.1, 341 paths,
fetched 2026-09-26). Every claim cites its source. Nothing below is a confirmed
vulnerability — these are verified surface facts plus leads for authenticated probing.

## Trust model (as the client artifacts describe it)

Two authorization layers are visible:

1. **Coarse OAuth scopes** (`accounts:read`, `accounts:write`, `services:write`,
   `projects:read`, …) — declared per-endpoint both in the console's generated API
   client (`f(y,"oauth2",[...],s)` before each call) and in the official OpenAPI
   spec's `security` blocks.
2. **Fine-grained role permissions** (`organization:users:write`,
   `role:organization:admin`, `organization:billing:read`, …) — a 131-entry
   permission table embedded in the console bundle gates UI elements
   (e.g. `organization_user_invitation_add: ["organization:users:write",
   "role:organization:admin"]`).

The probing question throughout: where the UI/scope says "low privilege is
enough," does the server independently enforce the fine-grained role — or does
it trust the coarse scope? Any endpoint where the server mirrors only the scope
is a broken-access-control candidate.

## [CONFIRMED EXPOSURES]

### 1. Complete API path inventory in public console JS
643 distinct path literals extracted from `main.ac1adb5b.bundle.js`
(`https://console.aiven.io/main.ac1adb5b.bundle.js`). The console ships a
generated API client containing the full REST surface, including endpoints
**absent from the public OpenAPI spec** (console-only API): all
`/project/{project}/appbuilder/*` endpoints, `/organization/{organization_id}
/invitation/weblink/{invite_verification_code}`, `/mcp`, `/pg-editor/*`,
`/query-editor`. Source: bundle strings + diff against spec's 341 paths.

### 2. Governance credentials endpoint needs only `accounts:read` (per spec)
`GET /organization/{organization_id}/governance/access/{access_id}/credentials`
— "Get organization access credentials". The official spec declares
`security: [{"tokenAuth": [], "oauth2": ["accounts:read"]}]`, and the 200
response schema returns live Kafka service-user secrets: `access_cert`,
`access_key`, `password`. The endpoint is flagged unstable
("may be changed or removed at any time. Don't use it in production").
Source: `openapi.json` paths + `components.schemas
.OrganizationGovernanceAccessCredentialsGetResponse`. Whether the server adds
role checks beyond the scope is the probing question — the spec's declared
scope is minimal for a secret-returning endpoint.

### 3. Organization invitation write-ops declared at `accounts:read`
- `POST /organization/{organization_id}/invitation` ("Invite a user to the
  organization") — spec scope `accounts:read`. The console's own UI permission
  table says inviting needs `organization:users:write` or
  `role:organization:admin` — a UI-gate vs API-scope mismatch worth testing.
- `DELETE /organization/{organization_id}/invitation/{user_email}` ("Remove an
  invitation") — spec scope `accounts:read`.
- `POST /organization/{organization_id}/invitation/weblink/{invite_verification_code}`
  (weblink invite accept) — console client scope `accounts:read`; not in the
  public spec at all. Source: spec + bundle API client.

### 4. AppBuilder write operations on `projects:read`, undocumented
`POST /project/{project}/appbuilder/apply-live-edit-changes`,
`POST /project/{project}/appbuilder/publish-preview`,
`POST /project/{project}/appbuilder/zip-app` — all declare only
`["projects:read"]` in the console API client, and none appear in the public
OpenAPI spec. Applying live-edit changes is a code-modifying write on a read
scope. Related: the appbuilder preview iframe uses `postMessage` with
`enable-live-edit`/`disable-live-edit` commands and a nonce
(source: `main.ac1adb5b.bundle.js`).

### 5. MCP server with client-controlled restrictions
`https://mcp.aiven.live/mcp` (or `https://mcp.aiven.live/mcp/{tenant}` for 3
allowlisted tenants). The console builds the MCP config URL with client-chosen
query params: `services_scope` (comma-joined tool list) and `read_only=true`
(source: `Ipe()` in `main.ac1adb5b.bundle.js`; docs at
`https://aiven.io/docs/tools/mcp-server`). If the MCP server trusts these
params instead of enforcing them, a "read-only" agent can write. Auth is
browser OAuth ("authenticate in your browser when prompted").

### 6. Server-side SQL analysis sinks
- `/pg/query/optimize`, `/mysql/query/optimize` (raw SQL in, optimization out),
  `/pg/query/optimize-by-token`, `/mysql/query/optimize-by-token`,
  `/pg/query/validate`, `/mysql/query/metadata-validate` — the AI query
  optimizer. Console client declares `accounts:read` for the account-level
  variants. Sinks that parse/analyze attacker-influenced SQL; error paths may
  leak schema.
- `POST /project/{project}/service/{service_name}/pg-editor/run-query`
  (scope `services:write`) and `/pg-editor/llm-answer` — the SQL editor proxies
  queries to the database and ships them to an LLM for explanation. Trust
  boundary: which DB principal executes the SQL server-side?

### 7. High-risk primitives in the surfaced API
- Flink JAR upload: `/project/{project}/service/{service_name}/flink/jar_application`
  (arbitrary code execution by design — probe upload authorization/validation).
- Kafka REST produce: `/project/{project}/service/{service_name}/kafka/rest/topics/{topic_name}/produce`
  (probe topic ACL parity between REST and native protocol).
- Service file API: `/project/{project}/service/{service_name}/file`,
  `/file/{file_id}` (Kafka custom plugin files).
- `PUT/POST /project/{project}/service/{service_name}/opensearch/security/admin`
  and `POST .../rotate-internal-secrets` (spec scope `services:write`).
- `/user/zendesk/token` (Zendesk SSO token minting), `/me/expire_tokens`.

## [HIGH-CONFIDENCE LEADS] (authenticated probing, trial account)

1. **Governance credential disclosure to low-privilege members.** With an org
   token carrying only `accounts:read`, GET another user's
   `/governance/access/{access_id}/credentials`. Invariant: "User A must never
   obtain User B's service credentials." Why: beta endpoint + secret response +
   minimal declared scope. If the server enforces the role model here, it fails
   closed — verify.
2. **Self-provisioning via invitation API.** As a read-only org member, POST
   `/organization/{organization_id}/invitation` for an external email, then
   accept. Invariant: "A low-privilege user must never add members." Why: the
   console's own UI demands `organization:users:write`/admin, but the spec
   declares `accounts:read`.
3. **Invitation deletion as a reader.** DELETE another admin's pending
   `.../invitation/{user_email}` with `accounts:read`. Invariant: readers must
   not mutate membership state.
4. **Weblink invite analysis.** Measure `invite_verification_code` entropy,
   expiry, and the role granted; check for a GET variant leaking invite metadata
   (role, inviter) without auth. Invariant: invite codes must be unguessable
   and least-privilege.
5. **AppBuilder live-edit as project viewer.** With only project read access,
   POST `apply-live-edit-changes` / `publish-preview` against another user's
   app. Invariant: "A reader must never modify." Why: write verbs on
   `projects:read`, undocumented in the public spec.
6. **MCP scope bypass.** Connect with `read_only=true`, then invoke a write
   tool; connect with `services_scope` limited, then call an out-of-scope tool;
   try a tenant-scoped URL for a non-allowlisted tenant. Invariant:
   "Client-declared restrictions must be re-enforced server-side."
7. **pg-editor DB principal.** With `services:write`, determine the effective
   database role behind `run-query` (create a least-privilege DB user, compare).
   Invariant: "The proxy must not execute with more DB privilege than the caller."
8. **Query-optimizer injection.** Feed malicious SQL to `/pg/query/optimize`
   and `/pg-editor/llm-answer`; look for error-based schema disclosure or prompt
   injection in the LLM path. Invariant: "Analysis must not execute or leak."
9. **Kafka REST produce ACL parity.** Produce to a topic the caller lacks native
   ACLs for via the REST endpoint. Invariant: "REST and native protocol must
   enforce identical ACLs."
10. **Cross-project object substitution.** Across all `/project/{project}/…`
    endpoints, swap `{project}` for a project the caller can't access while
    keeping a valid sibling object ID. Invariant: "A resource ID must remain
    bound to the authorized principal."

## [REJECTED]

- **Admin API OAuth secret in console JS:** no `regatta`, `4343`, or `admin-api`
  strings in any of the 7 console bundles (searched `main.*` and
  `vendor-main.*`). The suspected lead is not in the console client. The
  destination remains out of scope — do not test it.
- **XSS via `dangerouslySetInnerHTML`:** the 4 usages are icon-SVG rendering
  (iconify, `vendor-main`) and a code-snippet display (`main`). No
  server-controlled HTML injection path found statically.
- **`postMessage` trust issues:** handlers are app-internal (cross-tab reload
  signaling; appbuilder preview iframe with nonce). No missing origin check
  with security impact found statically.
- **`reset_password` over-permissioning:** `POST /organization/{organization_id}
/user/{member_user_id}/reset_password` requires `accounts:write` (spec) and is
  documented as "managed users" only — sanely gated, not the suspected
  `accounts:read` issue.
- **Feature flags as a vuln class:** `localFeatureFlags` gates UI with a
  `FeatureNotEnabled` blocker, but flags are server-issued — cosmetic
  client-side gating only.
- **CORS/API-wide issues:** covered by the earlier unauthenticated battery;
  not re-probed here.

## Notes for the authenticated battery
- OAuth scopes observed: `accounts:read`, `accounts:write`, `services:write`,
  `projects:read`, plus `tokenAuth` (personal access tokens). Map which scopes
  a trial user can self-grant on token creation — that defines the attacker's
  starting position.
- The console bundle is the more complete API reference (643 paths) than the
  public spec (341 paths); use the bundle's path list as the enumeration base.
- `api.aiven.io/v1` is the API base; `console.aiven.io` serves the SPA;
  `mcp.aiven.live` is the MCP server; `dc.aiven.io` is Snowplow telemetry.
