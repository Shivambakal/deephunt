# Aiven — Console-Only API vs Public OpenAPI Spec Differential

Passive only. No logins, no state-changing requests. Sources, both fetched
2026-09-26:

- Official spec: `https://api.aiven.io/doc/openapi.json` — **341 path objects,
  488 method+path entries**.
- Console bundle: `https://console.aiven.io/main.ac1adb5b.bundle.js`
  (6.5 MB) — the console ships a generated API client. Each operation follows
  the pattern `const o="/path/{param}".replace(...)`, `method:"POST"`,
  `await f(x,"oauth2",["scope"],s)`. Parsed **671 method+path+scope entries**
  from the client.

Method: extracted every `(method, path, oauth2-scopes)` triple from the bundle
client, every `(method, path, oauth2-scopes)` from the spec, and diffed.
Template-name-only differences were re-checked (normalized `{param}` → `{}`);
**zero false positives — all 193 console-only entries below are genuinely
absent from the public spec.**

Key: the declared OAuth scope is what the *client* claims is enough. The
probing question everywhere: does the server independently enforce the
fine-grained role model, or does it trust the coarse scope?

## [CONSOLE-ONLY ENDPOINT TABLE]

Format: `METHOD path — [declared scopes]`. `R` = read operation,
`W` = write/state-changing operation, `A` = analysis/read-only-op-that-uses-POST.

### WRITE operations on READ-only scopes (highest-value pattern)

| # | Endpoint | Scopes |
|---|----------|--------|
| 1 | `DELETE /project/{project}/appbuilder/app` (W) | `projects:read` |
| 2 | `POST /project/{project}/appbuilder/app` (W) | `projects:read` |
| 3 | `POST /project/{project}/appbuilder/apply-live-edit-changes` (W) | `projects:read` |
| 4 | `POST /project/{project}/appbuilder/fetch` (W) | `projects:read` |
| 5 | `POST /project/{project}/appbuilder/publish-preview` (W) | `projects:read` |
| 6 | `POST /project/{project}/appbuilder/zip-app` (W) | `projects:read` |
| 7 | `DELETE /organization/{organization_id}/governance/requests/{request_id}` (W) | `accounts:read` |
| 8 | `POST /organization/{organization_id}/governance/requests` (W) | `accounts:read` |
| 9 | `POST /organization/{organization_id}/governance/requests/{request_id}/operations` (W) | `accounts:read` |
| 10 | `POST /organization/{organization_id}/governance/requests/{request_id}/reviews` (W) | `accounts:read` |
| 11 | `POST /organization/{organization_id}/governance/kafka-acl-requests` (W) | `accounts:read` |
| 12 | `POST /organization/{organization_id}/governance/kafka-acl-requests/{request_id}/reviews` (W) | `accounts:read` |
| 13 | `POST /organization/{organization_id}/kafka-topic-requests` (W) | `accounts:read` |
| 14 | `PATCH /organization/{organization_id}/kafka-topic-requests/{request_id}` (W) | `accounts:read` |
| 15 | `POST /organization/{organization_id}/invitation/weblink/{invite_verification_code}` (W) | `accounts:read` |
| 16 | `PUT /project/{project}/service/{service_name}/pg/query/tags` (W) | `services:read` |
| 17 | `PUT /project/{project}/service/{service_name}/mysql/query/tags` (W) | `services:read` |

### Analysis operations on READ scopes (POST-as-transport; probe whether analysis executes)

| # | Endpoint | Scopes |
|---|----------|--------|
| 18 | `POST /pg/query/format` (A) | `services:read` |
| 19 | `POST /pg/query/optimize` (A) | `services:read` |
| 20 | `POST /pg/query/optimize-by-token` (A) | `user:read` |
| 21 | `POST /mysql/query/format` (A) | `user:read` |
| 22 | `POST /mysql/query/optimize` (A) | `user:read` |
| 23 | `POST /mysql/query/optimize-by-token` (A) | `user:read` |
| 24 | `POST /project/{project}/service/{service_name}/pg/query/format` (A) | `services:read` |
| 25 | `POST /project/{project}/service/{service_name}/pg/query/optimize` (A) | `services:read` |
| 26 | `POST /project/{project}/service/{service_name}/pg/query/optimize-group` (A) | `services:read` |
| 27 | `POST /project/{project}/service/{service_name}/mysql/query/format` (A) | `services:read` |
| 28 | `POST /project/{project}/service/{service_name}/mysql/query/optimize` (A) | `services:read` |
| 29 | `POST /project/{project}/service/{service_name}/mysql/query/optimize-group` (A) | `services:read` |
| 30 | `POST /project/{project}/service/{service_name}/pg/query-insights` (A) | `services:read` |
| 31 | `POST /project/{project}/service/{service_name}/mysql/query-insights` (A) | `services:read` |
| 32 | `POST /project/{project}/service/{service_name}/pg/schema-insights` (A) | `services:read` |
| 33 | `POST /project/{project}/service/{service_name}/mysql/schema-insights` (A) | `services:read` |
| 34 | `POST /project/{project}/service/{service_name}/pg/databases-by-hash` (A) | `services:read` |
| 35 | `POST /project/{project}/service/{service_name}/mysql/databases-by-hash` (A) | `services:read` |
| 36 | `POST /project/{project}/service/{service_name}/clickhouse/parser/columns` (A) | `services:read` |
| 37 | `POST /project/{project}/service/{service_name}/validate-connector-configuration` (A) | `services:read` |
| 38 | `POST /project/{project}/services-performance` (A) | `projects:read` |
| 39 | `POST /organization/{organization_id}/project/{project}/service/{service_name}/kafka/template/download` (A) | `services:read` |

### Admin/sensitive-looking operations with weak or notable scopes

| # | Endpoint | Scopes |
|---|----------|--------|
| 40 | `GET /user/zendesk/token` (W-effect: mints Zendesk SSO token) | **(none — any valid token)** |
| 41 | `PUT /organization/{organization_id}/governance/kafka-services/project/{project_name}/service/{service_name}` (W) | `accounts:write` |
| 42 | `PATCH /organization/{organization_id}/governance/config` (W) | `accounts:write` |
| 43 | `POST /organization/{organization_id}/authentication-methods/{authentication_method_id}/scim-tokens` (W) | `scim:write` |
| 44 | `DELETE /organization/{organization_id}/authentication-methods/{authentication_method_id}/scim-tokens/{token_prefix}` (W) | `scim:write` |
| 45 | `POST /organization/{organization_id}/trial` (W: provisions trial) | `accounts:write`, `billing:write` |
| 46 | `POST /organization/{organization_id}/trial-extensions` (W) | `accounts:write`, `billing:write` |
| 47 | `POST /project/{project}/trial` (W) | `billing:write`, `projects:write` |
| 48 | `POST /project/{project}/trial_extensions` (W) | `billing:write`, `projects:write` |
| 49 | `POST /organization/{organization_id}/invoice/{invoice_number}/initialize-payment` (W: payment flow) | `billing:write` |
| 50 | `POST /sso/{provider}/api_callback` (W: auth flow) | `user:write` |
| 51 | `POST /user/email/unsubscribe` (W: triggers server-side email flow) | `authentication:write`, `user:write` |
| 52 | `GET /user/signup_methods` (R, but requires write scope — inverted) | `user:write` |
| 53 | `POST /user` (W: user creation) | `payments:write`, `user:write` |
| 54 | `GET /project/{project}/service/{service_name}/flink/proxy/v1/jobs` + 5 sibling proxy paths (R, server-side proxy to Flink REST) | `services:read` |

### Read-only console-only endpoints (100; read-on-read, listed for completeness)

`GET /account/{account_id}/billing-groups/{billing_group_id}/invoices/{invoice_number}` — `accounts:read;billing:read`
`GET /account/{account_id}/billing/aggregate` — `accounts:read;billing:read`
`GET /account/{account_id}/billing/history` — `accounts:read;billing:read`
`GET /account/{account_id}/billing/summary` — `accounts:read;billing:read`
`GET /account/{account_id}/invoices` — `accounts:read;billing:read`
`GET /account/{account_id}/service_versions` — `accounts:read`
`GET /account/{account_id}/support-contracts` — `accounts:read`
`GET /me/organization/invites` — `authentication:read;user:read`
`GET /me/referral`, `/me/referral/codes` — `user:read`
`GET /organization/{organization_id}/authentication-methods/{authentication_method_id}/scim-tokens` — `scim:read`
`GET /organization/{organization_id}/billing-tier` — `accounts:read`
`GET /organization/{organization_id}/config/authentication_methods/{authentication_method_id}/errors` — `accounts:read;authentication:read`
`GET /organization/{organization_id}/config/features` — `accounts:read`
`GET /organization/{organization_id}/custom-cloud-environments[/{id}[/infra-templates/terraform/{template|variables}|/projects]]` — `accounts:read`
`GET /organization/{organization_id}/governance/{config|kafka-acl-requests[/{request_id}[/reviews[/{review_id}]]]|kafka-services|requests[/{request_id}[/operations|/reviews]]}` — `accounts:read`
`GET /organization/{organization_id}/kafka-topic-requests[/{request_id}]` — `accounts:read`
`GET /organization/{organization_id}/kafka/data-generator` — `projects:read;services:read`
`GET /organization/{organization_id}/pricing/rates` — `accounts:read;user:read`
`GET /organization/{organization_id}/project/{project_id}/{access|inkless/offerings|inkless/pricing/rates|offerings|products}` — `projects:read`
`GET /organization/{organization_id}/project/{project}/service/{service_name}/{kafka-acl-permissions|kafka/data-generator|topic/{topic_name}/kafka-acl-permissions}` — `services:read`
`GET /organization/{organization_id}/{services|subscriptions|support-contracts|trial-extensions|units}` — `accounts:read[;billing:read]`
`GET /organization/{organization_id}/user-groups/{user_group_id}/members/{member_user_id}` — `accounts:read`
`GET /project/{project}/{access|services-log-config|trial_extensions}` — `projects:read`
`GET /project/{project}/ai-gateway/{keys[/{key_id}]|models|usage}` — `projects:read`
`GET /project/{project}/appbuilder/{apps|generate-uuid}` — `projects:read`
`GET /project/{project}/custom-cloud-environments[/{custom_cloud_environment_id}]` — `projects:read`
`GET /project/{project}/datahub/dependent-service-configurations/plan/{service_plan}/cloud/{cloud}` — `projects:read`
`GET /project/{project}/integration_endpoint/{integration_endpoint_id}/{kafka/topics|services}` — `services:read`
`GET /project/{project}/service/{service_name}/application/environment-variables` — `services:read`
`GET /project/{project}/service/{service_name}/clickhouse/internal/db` — `services:read`
`GET /project/{project}/service/{service_name}/file[/{file_id}]` — `services:read`
`GET /project/{project}/service/{service_name}/flink/{application/{application_id}/version/query[/{query_id}]|connector_configs|proxy/v1/{jobs[/overview|/{job_id}[/exceptions]]|overview}}` — `services:read`
`GET /project/{project}/service/{service_name}/integration/{project[/{other_project}]|_types}` — `services:read`
`GET /project/{project}/service/{service_name}/kafka/{network-metrics|policies|storage/{storage-usage/{by-topic|total}|summary}}` — `services:read`
`GET /project/{project}/service/{service_name}/{mysql|pg}/{insights-databases|log-config|query/slowqueries|schema-group-insights|service-performance-trends}` — `services:read`
`GET /project/{project}/service/{service_name}/pg-data-api/{availability|databases}` — `services:read`
`GET /project/{project}/service/{service_name}/pg-editor/{saved-queries[/{query_id}]|schemas|table-data|tables}` — `services:read`
`GET /user/linking_auth_methods` — `authentication:read;user:read`
`GET /user/signup_methods` — `user:write` (inverted: read gated on write)
`GET /user/zendesk/token` — **no scopes declared**

## [SCOPE-MISMATCH LEADS] (ranked)

**L1. Governance review/approval workflow on `accounts:read`.** POST
`.../governance/requests/{request_id}/reviews` and
`.../governance/kafka-acl-requests/{request_id}/reviews`, plus
`PATCH .../kafka-topic-requests/{request_id}`, all declare `accounts:read`.
If a low-privilege org member can *approve* another member's Kafka ACL/topic
request, that's privilege escalation inside the governance model. Invariant:
"only approvers may approve." (Source: bundle client; none of these are in
the public spec.)

**L2. AppBuilder create/delete/modify on `projects:read`.** `POST` and
`DELETE /project/{project}/appbuilder/app`, `POST apply-live-edit-changes`,
`POST publish-preview` — all `projects:read`. A project *viewer* modifying
another user's app. Invariant: "a reader must never modify." (Source: bundle
client, verified in context: `appBuilderDeleteApp` → `method:"DELETE"`,
`f(p,"oauth2",["projects:read"],s)`.)

**L3. Zendesk SSO token with no declared scope.** `GET /user/zendesk/token`
calls `f(c,"oauth2",[],s)` — an authenticated call requiring *no* scope, and
absent from the public spec. Probe: does *any* valid token (even scope-less)
mint a Zendesk SSO token? Invariant: "support-channel SSO must require a
privileged, scoped token." (Source: bundle client `userZendeskTokenGet`.)

**L4. Governance request deletion on `accounts:read`.**
`DELETE .../governance/requests/{request_id}` — a reader deleting another
user's pending request (denial of a governance action). Invariant: "readers
must not mutate request state." (Source: bundle client, verified:
`method:"DELETE"`, `["accounts:read"]`.)

**L5. Query-tag mutation on `services:read`.**
`PUT .../pg/query/tags` and `.../mysql/query/tags` — metadata writes on a
read scope. Lower impact but the same broken pattern; also a test of whether
the server distinguishes scope from intent. (Source: bundle client.)

**L6. Weblink invite accept on `accounts:read`.** Already a standing lead;
confirmed here as console-only and undocumented. Probe code entropy, expiry,
granted role. (Source: bundle client
`organizationUserInvitationWeblinkAccept`.)

**L7. Governance Kafka-service registration on `accounts:write`.**
`PUT .../governance/kafka-services/project/{project_name}/service/{service_name}`
— org-level governance enrollment gated only by the coarse `accounts:write`
scope. Probe whether a non-admin member can enroll rogue services into the
governance plane. (Source: bundle client.)

**L8. Connector-configuration validation on `services:read`.**
`POST .../validate-connector-configuration` — server-side validation of a
connector config with only read scope. If validation *connects* to
user-supplied hosts, it's an SSRF probe surface. Observe only with a
self-controlled catcher. (Source: bundle client.)

**L9. Unsubscribe-triggered server flow.** `POST /user/email/unsubscribe`
(`authentication:write,user:write`) — the List-Unsubscribe SSRF shape from the
writeup playbook: one click → server-side fetch. Test with own collaborator,
observe only. (Source: bundle client.)

**L10. Trial/provisioning business logic.** `POST .../trial`,
`POST .../trial-extensions`, `POST /project/{project}/trial` —
probe repeated-trial abuse and trial-extension stacking with synthetic orgs.
Invariant: "a user must not get unlimited trial value." (Source: bundle
client.)

**L11. Flink proxy on `services:read`.** Six
`GET .../flink/proxy/v1/...` endpoints proxy to the Flink REST API. Probe
whether the proxy passes through paths/verbs beyond the listed ones
(path-traversal into the proxied API). (Source: bundle client.)

## [REJECTED]

- **Analysis endpoints as "writes":** the 22 query-format/optimize/insights/
  schema-insights POSTs use POST for body transport; most are read-only
  analysis. Not scope mismatches by themselves — the real question is whether
  the analysis *executes* the SQL (see L-probes for pg-editor/run-query).
- **`POST /account/{account_id}/link-marketplace-subscription`:** declares
  `accounts:read;billing:write` — has the write scope, fine.
- **`POST /user`, `POST /sso/{provider}/api_callback`:** user-creation/SSO
  flows with appropriate scopes for their purpose.
- **Read-on-read GETs (100 listed above):** expected; no mismatch. Two
  exceptions kept as leads: `/user/zendesk/token` (no scope at all) and
  `/user/signup_methods` (inverted write-gated read, likely intentional but
  worth noting).
- **Spec-side norm check:** the official spec itself declares
  `POST /organization/{organization_id}/invitation` at `accounts:read` and
  the governance-credentials GET at `accounts:read` — Aiven's *declared*
  scope convention is loose by design in places. The declared scope is not
  proof of a vulnerability anywhere above; every lead needs an authenticated
  probe with a low-privilege synthetic principal to see whether the server
  enforces the fine-grained role model or trusts the scope.
- **The suspected out-of-scope Admin API:** still not referenced anywhere in
  the console client; unchanged from the prior report. Not tested.
