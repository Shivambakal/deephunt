# OneTrust — Deep Static Analysis (passive)

Date: 2026-09-26. Method: read-only fetching of public resources only — no
logins, no state-changing requests. All findings below are verified from
fetched public content (developer docs, OpenAPI specs, knowledge articles).
Nothing here is a confirmed vulnerability; leads are framed for authenticated
testing on **pentest-app.onetrust.com** (the only bounty-eligible target).

Methodology: ~/workspace/hacker-agent/deep-vuln-methodology.md (§1 app model,
§3 cross-feature, §6 source/client analysis).

---

## [CONFIRMED EXPOSURES] — verified attack-surface facts

### C1. Full OpenAPI specs are publicly downloadable
- Source: https://developer.onetrust.com/onetrust/openapi/platform-access-management.json
  (also embedded as JSON in every `.md` API doc page, e.g.
  `.../reference/getoauthtoken-1.md`).
- The spec enumerates all 17 access-management paths with methods, parameters,
  request schemas, and per-operation OAuth scope requirements. An attacker gets
  the complete authorization map for free. Not a vuln by itself — it makes
  every lead below cheap to weaponize.

### C2. Tenant/org/role are first-class auth context in the token
- Source: `Platform-AccessManagement_ClientCredentialsResponse` schema in the
  spec above.
- The OAuth token response (`POST /api/access/v1/oauth/token`,
  `multipart/form-data`, `grant_type`+`client_id`+`client_secret`) returns:
  `access_token`, `tenantId`, `tenantGuid`, `orgGroupId`, `orgGroupGuid`,
  `role`, `ot_scopes`, `sessionId`, `email`, `user_name`, `languageId`.
- Validates the standing lead: authorization decisions downstream are keyed on
  tenant/org-group/role carried from this token. Any endpoint that also
  accepts these as request parameters is a confused-deputy candidate.

### C3. Integration webhook triggers are externally callable endpoints
- Source: https://my.onetrust.com/s/article/UUID-fc73aede-a246-99a3-15c9-ddf9f29b22e3
  ("Introduction to the OneTrust Integrations Platform").
- "A webhook is an externally callable endpoint, for which you can configure
  an expected payload to then use as input throughout the integration
  workflow." Auth: "An OAuth Token with the `INTEGRATION` scope is required."
- Trigger types: system events (Assessment Submitted, DSR Created, Consent
  Profile Updated, …), scheduled, **webhook (external)**, subflow (internal).

### C4. Generic integration actions can make HTTP requests, handle files, and run DB queries — with FreeMarker in any text field
- Source: same article.
- "Generic" system "includes the ability to perform HTTP requests, handle
  files, and perform database requests."
- "FreeMarker can actually be embedded in any text input for any action",
  referencing trigger payload: `${event.payload.someAttributeInThePayload!}`
  and prior steps: `${step.http_0.someAttributeFromThePriorHttpRequest!}`.
- C3 + C4 is the documented mechanism for a webhook-payload → server-side
  HTTP request chain (see lead L1).

### C5. DSR creation uses a client-supplied idempotency key, and status is looked up by it
- Source: https://developer.onetrust.com/onetrust/reference/createrequestqueuev2usingpost.md
  (embeds OpenAPI for `POST /api/datasubject/v2/requestqueues/{templateId}`).
- Request body includes `requestTraceId`: "Unique trace id for request. This
  can be used to avoid creating duplicate request." — **chosen by the client**.
- Scope table (https://developer.onetrust.com/onetrust/reference/oauth-20-scopes.md)
  shows `GET /requestqueues/status/{requestTraceId}` and
  `GET /requestqueues/{requestQueueRefId}/language/{language}`.
- Client-chosen lookup keys are a classic cross-request oracle shape (L3, L9).

### C6. Attachment download is a two-step token flow
- Source: https://developer.onetrust.com/onetrust/reference/getattachmentdownloadtokenv4.md
  (embeds OpenAPI for `GET /api/document/v4/attachments/token/{attachmentId}`,
  scope `ATTACHMENT`/`ATTACHMENT_READ`).
- `attachmentId` "corresponds to the `attachmentId` returned by the V4 upload
  flow" — token issuance is the authorization checkpoint (see L5).

### C7. v1/v2 API generations coexist; deprecated endpoints are documented
- Source: access-management spec + https://developer.onetrust.com/onetrust/reference/deprecated-apis-list.md
- `/api/access/v1/user-groups` and `/api/access/v2/user-groups` both live;
  v1 `{userGroupId}` documents PUT/DELETE but no GET, v2 `{groupId}` has
  GET/PUT/DELETE — same `USER` scope declared on both.
- Deprecated (still documented, deprecation periods running through 2026):
  v1 "Create Request" (`createrequestqueuefrommessageusingpost`) → v2
  (`createrequestqueuev2usingpost`); several v1 consent/receipt GETs → v2/v3
  POST equivalents. Deprecated ≠ removed (see L4).

### C8. Environment/host inventory is public
- Source: https://developer.onetrust.com/onetrust/reference/url-variables-for-apis-sdks.md
- Shared envs: `app.onetrust.com`, `app-eu`, `app-de`, `app-uk`, `app-apac`,
  `app-in`, `app-ae`, `app-au`, `app-br`, `app-ca`, `app-ch`, `app-fr`,
  `app-jp`, `na01.onetrust.com`; `trial.onetrust.com`; `uat.onetrust.com`,
  `uat-de`, `uat-na01`. Privacy-portal hosts enumerated separately.
  (Recon aid only — do not test hosts outside the brief.)

---

## [HIGH-CONFIDENCE LEADS] — for authenticated testing on pentest-app.onetrust.com

### L1. Webhook-trigger → FreeMarker → Generic HTTP action = SSRF primitive
**Why:** C3+C4 document the full chain: an externally callable webhook
(INTEGRATION scope — weaker than full admin) feeds its payload into workflow
steps, and FreeMarker interpolation works "in any text input for any action",
including the Generic system's HTTP request action. If the HTTP action's URL
field accepts `${event.payload.url!}`, a low-privilege integration builder (or
anyone who can mint an INTEGRATION-scoped token) gets server-side fetch to an
attacker-influenced URL.
**Test:** build a workflow on the staging tenant: webhook trigger → Generic
HTTP GET with URL `${event.payload.target!}` → POST payload
`{"target":"http://<collaborator>"}` with an INTEGRATION-scoped token; observe
egress. Then test restrictions: internal metadata IPs, redirect following,
response exfiltration into subsequent steps (`${step.http_0...}`).
**Invariant attacked:** server-side requests must never go to
attacker-controlled destinations.

### L2. FreeMarker SSTI in the integration builder
**Why:** FreeMarker is a full template engine, embeddable in every action
field (C4). Test whether dangerous builtins/directives are sandboxed or an
author can reach Java statics / file read. Multi-tenant template injection
would be high impact.
**Test:** `${7*7}`, then progressively `${"freemarker.template.utility.Execute"?new()("id")}`
equivalents in a Data Transformation action; observe output vs error.
**Invariant attacked:** template rendering must not execute code.

### L3. DSR status oracle via client-chosen `requestTraceId`
**Why:** C5 — the trace ID is client-supplied at creation and is the lookup
key for `GET /requestqueues/status/{requestTraceId}`. If the status endpoint
doesn't bind the trace ID to the requesting principal, one requester can read
another's DSR status (PII-adjacent workflow metadata).
**Test:** create two DSRs as two principals (or one principal, two requests);
query each status with the other's trace ID; then probe an unguessable vs
sequential ID to characterize entropy.
**Invariant attacked:** requester A must never read requester B's request.

### L4. Deprecated v1 DSR "Create Request" still live with weaker checks
**Why:** C7 — v1 `createrequestqueuefrommessageusingpost` is deprecated in
favor of v2 but deprecation periods run through Dec 2026. Deprecated endpoints
frequently keep older, weaker authorization.
**Test:** replay the v2 request shape against the v1 path on pentest-app;
compare auth requirements, parameter validation, and error behavior
differentially.
**Invariant attacked:** old API versions must enforce the same authorization
as current ones.

### L5. Attachment download-token IDOR
**Why:** C6 — token issuance at
`GET /api/document/v4/attachments/token/{attachmentId}` is the authz
checkpoint before content download. If `attachmentId`s are sequential or
leaked (they're returned by the upload flow), test whether requesting a token
for another principal's attachment succeeds.
**Test:** upload attachments as principal A and B; as A, request a token for
B's attachmentId (and A_id±1); observe 200 vs 403/404.
**Invariant attacked:** attachment IDs must stay bound to the owning principal.

### L6. v1 vs v2 user-groups differential
**Why:** C7 — v1 lacks documented GET on `{userGroupId}` while v2 has it;
both declare the same `USER` scope. Undocumented-but-live methods on the old
version are a classic differential hole.
**Test:** GET `/api/access/v1/user-groups/{userGroupId}` directly; try PUT
with v2-shaped bodies on v1; compare error messages for oracle behavior.
**Invariant attacked:** API generations must not differ in security decisions.

### L7. Tenant/org/role context confusion
**Why:** C2 — every token carries tenantId/orgGroupId/role. Test whether any
endpoint also accepts these as query/body parameters or headers and prefers
the client-supplied value over the token's (privilege-boundary violation), and
whether a token minted for one org-group can be replayed against another
tenant's objects.
**Test:** with a staging token, replay requests swapping orgGroupId/tenantId
params; attempt cross-org object access (user-groups, DSR queues).
**Invariant attacked:** the authorized tenant/org must never be
client-overridable.

### L8. Collection-point token cross-use
**Why:** docs list `GET /v1/collectionpoints/{collectionpointId}/token`
returning a JWT used as `requestInformation` in the Consent Receipts API.
**Test:** whether point A's token is accepted for point B's receipt
submission (confused deputy across collection points / tenants).
**Invariant attacked:** a token must remain bound to its issuing collection
point.

### L9. `requestQueueRefId` entropy and IDOR
**Why:** C5 — `GET /requestqueues/{requestQueueRefId}/language/{language}`
exposes DSR details. Characterize ref ID format (sequential integer vs UUID);
if low-entropy, test cross-principal reads.
**Invariant attacked:** DSR objects must never be enumerable by non-owners.

### L10. SCIM scope privilege boundary
**Why:** scope table grants SCIM full user/group CRUD (`POST /Users`,
`PATCH /Users/{id}`, …). Test whether a SCIM-scoped credential — intended
for provisioning — can create/grant admin-level users or modify roles beyond
its provisioning purpose.
**Invariant attacked:** a provisioning credential must not be able to escalate
privilege.

---

## [REJECTED HYPOTHESES]

- **R1. my.onetrust.com as an application target.** It is a Salesforce
  Experience Cloud community site (login shell at `/s/login`, Aura framework);
  the actual application lives on `app.*`/`*.onetrust.com` hosts. Community
  login JS holds no app API surface.
- **R2. `tenant_id` as a documented request parameter.** Grep across the
  developer portal index and specs found no `tenant_id`/`orggroup_id` request
  parameters — tenant context is server-derived from the OAuth token (C2), not
  a documented client parameter. L7 remains testable (undocumented acceptance
  is exactly the question) but is downgraded from "documented parameter" to
  "behavioral probe".
- **R3. Secrets in public docs/JS.** The `llms.txt` index, `.md` doc pages,
  and fetched community/portal JS contained no credentials, internal hosts
  beyond the documented env table, or private keys. (The login page references
  `cdn.cookielaw.org`/`cdn.1trust.app` consent SDK assets — public by design.)
- **R4. Unauthenticated endpoint exposure on staging.** Covered by the
  separate unauthenticated staging assessment (clean: consistent auth gates,
  no Actuator/Swagger/GraphQL/debug/CORS issues) — not repeated here.

## Caveats
- Passive only: no authentication attempted, no requests beyond public GETs of
  documentation and spec files.
- Nothing above is a confirmed vulnerability. Each lead needs authenticated
  reproduction on pentest-app.onetrust.com with synthetic data, minimal test
  cases, and an immediate stop once the boundary decision is observed.
- Scope reminder: test ONLY pentest-app.onetrust.com per the program brief;
  the env-host table (C8) is recon context, not authorization to probe.
