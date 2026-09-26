# OneTrust — Public OpenAPI Scope Differential

**Source:** `https://developer.onetrust.com/onetrust/openapi/platform-access-management.json`
("Platform - Access Management 1.0", fetched 2026-09-26, read-only)
**Method:** §3 + §6 of `~/workspace/hacker-agent/deep-vuln-methodology.md` — build the full
operation→scope table from the public spec, then flag semantic mismatches between the
declared OAuth scope and the operation's privilege (same technique that found Aiven's
UI-gate-vs-API-scope mismatches). All findings are spec-declared facts; none is a confirmed
vulnerability — each needs authenticated reproduction on `pentest-app.onetrust.com` with
synthetic data. Scope reminder: only `pentest-app.onetrust.com` is bounty-eligible.

## Scope model (the whole trust model fits in two scopes)

From the spec's `securityDefinitions` (`Platform-AccessManagement_OAUTH2`, clientCredentials flow):

| Scope | Spec-declared meaning (verbatim) |
|---|---|
| `ORGANIZATION` | "Grants full access to manage organizations. This includes Create, Read, Update and Delete operations." |
| `USER` | "Grants full access to manage Users, User Groups and User Group membership. This includes Create, Read, Update and Delete operations." |

There is **no read/write split, no admin/non-admin scope, and no tenant-isolation scope**.
A token minted with `USER` is *declared by the spec* to have full CRUD over users, groups,
memberships, and role assignments. Every privilege boundary below therefore rests entirely
on server-side role checks the spec does not describe — exactly the Aiven shape
(UI/console gate vs coarse API scope).

## [SCOPE TABLE]

All 36 operations. "Privileged?" = the operation creates, grants privilege, deletes, or
touches cross-user/tenant data.

| # | Method | Path | Scope | Privileged? |
|---|---|---|---|---|
| 1 | GET | `/api/access/v1/external/organizations` | ORGANIZATION | read org hierarchy |
| 2 | POST | `/api/access/v1/external/organizations` | ORGANIZATION | **CREATE ORG** |
| 3 | PUT | `/api/access/v1/external/organizations/{externalId}` | ORGANIZATION | update org |
| 4 | DELETE | `/api/access/v1/external/organizations/{externalId}` | ORGANIZATION | **DELETE ORG**, moves its objects to another org |
| 5 | GET | `/api/access/v1/login-history` | USER | **all users' login history** (default, past 7 days) |
| 6 | POST | `/api/access/v1/oauth/token` | (none) | token minting — normal |
| 7 | GET | `/api/access/v1/user-groups` | USER | list groups |
| 8 | POST | `/api/access/v1/user-groups` | USER | **create group** |
| 9 | PUT | `/api/access/v1/user-groups/{userGroupId}` | USER | update group |
| 10 | DELETE | `/api/access/v1/user-groups/{userGroupId}` | USER | delete group |
| 11 | GET | `/api/access/v1/user-groups/{userGroupId}/members` | USER | list members |
| 12 | POST | `/api/access/v1/user-groups/{userGroupId}/members` | USER | **add member(s)** |
| 13 | DELETE | `/api/access/v1/user-groups/{userGroupId}/members` | USER | remove member(s) |
| 14 | GET | `/api/access/v2/user-groups` | USER | list groups |
| 15 | POST | `/api/access/v2/user-groups` | USER | **create group** |
| 16 | GET | `/api/access/v2/user-groups/{groupId}` | USER | read group |
| 17 | PUT | `/api/access/v2/user-groups/{groupId}` | USER | update group |
| 18 | DELETE | `/api/access/v2/user-groups/{groupId}` | USER | delete group |
| 19 | GET | `/api/access/v2/user-groups/{groupId}/access-levels` | USER | read group roles |
| 20 | PUT | `/api/access/v2/user-groups/{groupId}/access-levels` | USER | **set group roles** |
| 21 | POST | `/api/access/v2/user-groups/{groupId}/access-levels` | USER | **add role to group** (`organizationId` + `roleId` client-supplied) |
| 22 | DELETE | `/api/access/v2/user-groups/{groupId}/access-levels` | USER | remove group role |
| 23 | GET | `/api/access/v2/user-groups/{groupId}/members` | USER | list members |
| 24 | POST | `/api/access/v2/user-groups/{groupId}/members` | USER | **add member(s)** |
| 25 | DELETE | `/api/access/v2/user-groups/{groupId}/members` | USER | remove member(s) |
| 26 | POST | `/api/access/v2/user-groups/{groupId}/members/{memberId}` | USER | **add single user to group** |
| 27 | DELETE | `/api/access/v2/user-groups/{groupId}/members/{memberId}` | USER | remove single user |
| 28 | GET | `/api/access/v2/users` | USER | list users |
| 29 | POST | `/api/access/v2/users` | USER | **CREATE USER** (body accepts `accessLevels`, `internal`, `externalId`) |
| 30 | GET | `/api/access/v2/users/{userId}` | USER | read user |
| 31 | PUT | `/api/access/v2/users/{userId}` | USER | update user (body accepts `accessLevels`, `internal`, `externalId`) |
| 32 | GET | `/api/access/v2/users/{userId}/access-levels` | USER | read user roles |
| 33 | POST | `/api/access/v2/users/{userId}/access-levels` | USER | **ADD ROLE TO USER** (`organizationId` + `roleId` client-supplied, required) |
| 34 | DELETE | `/api/access/v2/users/{userId}/access-levels` | USER | remove user role |
| 35 | PATCH | `/api/access/v2/users/{userId}/default-organization` | USER | change user's default org |
| 36 | GET | `/api/audit/v1/users/{userId}/activities` | USER | **user's profile/role/org change history** (cross-user read) |

## [MISMATCH LEADS] — ranked for authenticated probing on pentest-app.onetrust.com

**L1. Role assignment via client-supplied IDs on a USER-scoped token (privilege escalation shape).**
`POST /api/access/v2/users/{userId}/access-levels` ("Add User Role") declares only `USER`,
and its required body is `{organizationId, roleId}` — both caller-chosen UUIDs.
Same for `POST /api/access/v2/user-groups/{groupId}/access-levels`.
*Spec evidence:* op summaries "Add User Role" / "Add User Group Roles",
`PublicAccessLevelRequest` required: `['organizationId','roleId']`.
*Test:* with a non-admin USER-scoped token, assign a privileged `roleId` (harvested from
`GET .../access-levels` of own objects) to own test user in own org; then try a foreign
`organizationId`. Invariant: the server must verify the caller may grant that role in that
org — the spec declares no scope that would enforce it.

**L2. Create/Update User accepts `accessLevels` + `internal` + `externalId` (self-provisioning shape).**
`POST /api/access/v2/users` ("Create User") body (`PublicOrgUserCreateRequest`, required:
`email, firstName, lastName`) accepts `accessLevels[]` = `{organizationId, roleIds[],
defaultOrganization}`, plus `internal` (boolean) and `externalId`.
`PUT /api/access/v2/users/{userId}` ("Update User") accepts the same `accessLevels` and
`internal` fields.
*Test:* create a synthetic user while passing an `accessLevels` entry with a privileged
`roleIds[]`; check whether the created user actually holds the role. Then try `internal:
true`. Invariant: role-bearing user creation must require an admin-level check the `USER`
scope does not express.

**L3. Login history of ALL users on a USER-scoped token (cross-user read shape).**
`GET /api/access/v1/login-history` ("Get Audit Records for Login History") declares `USER`,
and the docs state: if no date range and no `userId` is specified, "the response will
include the login history for **all users** over the past 7 days"; with a `userId`, that
specific user's 365-day history. Query params: `userId, startDate, endDate, page, size`.
*Test:* with a non-admin USER-scoped token, call it with no params and with another
synthetic user's ID (from the same staged tenant). Invariant: org-wide login history must
require an admin role — `USER` scope alone must not reach other users' data.

**L4. Audit trail for an arbitrary userId (cross-user read shape).**
`GET /api/audit/v1/users/{userId}/activities` ("Get Audit Records for User's Profile")
declares `USER` (under the `AuditRecords_OAUTH2` scheme whose only scope is `USER`) and
"will include a history of changes made to the user's details, **roles, and
organizations**".
*Test:* request another synthetic user's `{userId}`. Invariant: role/org change history of
another user must not be readable on a plain `USER` token.

**L5. Organization create/delete under the root on an ORGANIZATION-scoped token (tenant-boundary shape).**
`POST /api/access/v1/external/organizations` ("Create Organization") — docs: if no
`parentExternalId` is given, the org "will be created as a child of the **root
organization**"; body also accepts `parentOrganizationId` (caller-chosen).
`DELETE /api/access/v1/external/organizations/{externalId}` deletes an org addressed by
caller-supplied `externalId` and "move[s] its associated objects to a different
organization".
*Test:* create an org with no parent (does it land under the *caller's tenant* root or a
global root?), then try `parentOrganizationId`/`externalId` values from a second staged
tenant — if two tenants are obtainable — and observe whether the server binds the
external ID to the caller's tenant. Invariant: the spec has no tenant-isolation scope, so
the binding must be server-derived from the token.

**L6. Default-organization switch (cross-org confusion shape).**
`PATCH /api/access/v2/users/{userId}/default-organization` ("Modify User Default
Organization") declares `USER`; docs note only "the user must have at least one role in
the specified organization".
*Test:* with own two synthetic users, switch user A's default org to org B via A's token,
then via user B's token targeting user A. Invariant: a caller must not move another
user's default org across the org boundary.

**L7. v1 vs v2 differential on the same objects.**
v1 has **no** `/users` paths at all (v2 introduced them); v1 user-groups use `{userGroupId}`
while v2 uses `{groupId}`; both generations declare the same `USER` scope for identical
semantics (create group, add/remove members).
*Test:* for each v1↔v2 pair, run the same unauthorized-shape request (foreign groupId,
foreign memberId) against both generations and diff the decisions — the older generation
is the classic weaker-check candidate.

## [REJECTED]

- **R1. Token endpoint without scopes** — `POST /api/access/v1/oauth/token` declares no
  security; normal for a client-credentials token URL, not a finding.
- **R2. `tenant_id` as a request parameter** — not present anywhere in this spec; tenant
  context is token-derived (confirms the earlier static finding; L5 is a behavioral probe,
  not a parameter-tampering lead).
- **R3. Fine-grained read/write separation** — does not exist in this API's scope model;
  the "mismatch" here is structural (only 2 scopes for the entire IAM surface), which is
  why every lead above targets the server-side role checks the spec cannot express.
- **R4. DSR/consent requester endpoints** — not in this spec (it covers access management
  and audit only); the DSR `requestTraceId` oracle lead lives in onetrust-deep-static.md.

## Handoff notes for the authenticated phase

- The sharpest single probe is **L2 then L1**: create-user-with-accessLevels, then
  add-role-to-user with a non-admin `USER`-scoped client-credentials token. Either success
  is privilege escalation by design-vs-implementation gap.
- **L3** is the cheapest: one GET with no params on a non-admin token; a 200 with other
  users' rows is the finding.
- Everything above needs two synthetic users (and ideally visibility into which roles are
  privileged, via `GET .../access-levels` on own objects) — all obtainable inside the
  staged tenant with synthetic data only.
