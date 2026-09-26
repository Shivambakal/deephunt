# AIVEN ATTACK PLAN

Program: https://bugcrowd.com/engagements/aiven-mbb-og
Rewards: historically $50 – $25,000 (VERIFY current range on the live brief before starting).
Status: #1 Bugcrowd pick — the brief literally tells you where dupes aren't and what pays most.

---

## 1. What Aiven is (and why the surface is huge)

Aiven is managed open-source data infrastructure. Customers click "create service" and Aiven provisions real database/streaming clusters on cloud VMs:

- **PostgreSQL, MySQL** — full DB servers with connection URIs containing passwords
- **Apache Kafka (+ Connect, MirrorMaker)** — brokers, topics, ACLs, schema registry
- **OpenSearch, ClickHouse, Valkey (Redis), Grafana, Metrics**

Every managed service is a multi-tenant attack surface: a control plane (console + API), a data plane (the actual DB ports), and an identity/permission layer gluing them together. The program brief says it outright: **website vulns are heavily duped; managed DB-app issues are mostly unique**, and **cross-account access to other customers' services is the top-paying class**. Chained goals are blessed: credential theft → internal network services → cross-account access.

Key API facts (from https://api.aiven.io/doc/ and https://aiven.io/docs/tools/api):
- Base URL: `https://api.aiven.io/v1`
- Auth: `Authorization: aivenv1 TOKEN` header (NOT cookies — copying your own header is not a bug, per the brief)
- Tokens: generated at `console.aiven.io/profile/auth`; OAuth2 authorization-code flow also supported with granular scopes
- Permission model (scoped strings, e.g.): `project:services:read`, `service:secrets:read`, `project:services:write`, `service:configuration:write`, `project:integrations:write`, `role:services:maintenance`, `role:services:recover`, `organization:projects:write`
- Notable: `ServiceGet` requires `service:secrets:read` — there IS a permission boundary between "see the service exists" and "read its credentials". Boundaries are where bugs live.
- Deprecated-but-live endpoints exist (e.g. `/v1/account/{account_id}/team/{team_id}/project/{project}` — slated for removal; deprecated endpoints historically carry weaker authZ).

---

## 2. Per-target manual test checklists

### console.aiven.io (the web console)
- [ ] **Auth**: password policy, rate limiting on login (manual, few attempts — never brute force), session handling, SSO/OAuth flows, password-reset token entropy and expiry
- [ ] **IDOR on projects/services**: every console XHR that takes a `project_name`, `service_name`, or UUID in the path — replay it with the *other* account's identifiers (see §3 for the two-account setup)
- [ ] **Team/group invite logic**: invite acceptance flow — tamper the `role` parameter in the invite-accept request; try accepting an expired/revoked invite; try enumerating valid invite tokens; test whether a low-priv member can invite with admin role
- [ ] **Billing**: invoice/receipt endpoints — IDOR across organizations (`/v1/.../billing`); test upgrading plan via direct API call on a trial account; check what billing metadata leaks (card last-4, emails)
- [ ] **API token management**: token creation scopes — request a token with scopes beyond your role; test token of a removed team member still working; check token listing exposes other users' token metadata
- [ ] **Service integration endpoints**: `ServiceIntegrationCreate` (`project:integrations:write`) — integrations bridge services (e.g. Kafka→PostgreSQL sink). Test creating an integration from YOUR service to a service name/UUID you don't own.

### api.aiven.io (the real prize)
Enumerate from the OpenAPI spec at https://api.aiven.io/doc/ — it's public and complete. Then:
- [ ] **AuthZ on every project/service read**: with Account B's token, `GET /v1/project/{projectB}/service/{serviceUUID_from_A}`. Also try the reverse identifier styles (name vs UUID). Expect 403/404 — anything else is a finding.
- [ ] **Secrets boundary**: `ServiceGet` needs `service:secrets:read`. Create a read-only/limited-role member in your own org; have that member request another project's service details. Credential URIs (with passwords) must never cross that boundary.
- [ ] **Deprecated endpoints**: hit `/v1/account/{account_id}/team/{team_id}/project/{project}` and `/projects` with the other account's IDs — deprecated code paths are prime IDOR territory.
- [ ] **Organization permissions API**: `/v1/organization/{organization_id}/permissions/project/{project_id}` — swap organization_ids between your two accounts.
- [ ] **JWT/OAuth handling**: if using OAuth2 flow, test `alg=none`, weak secrets, scope escalation (`scope=admin` in the authorize request), redirect_uri validation (open redirect → token theft), and code replay.
- [ ] **Service task endpoints**: `ServiceTaskCreate` (`role:services:maintenance`) — tasks trigger upgrades/backups/restarts. Test triggering a task on the other account's service.
- [ ] **VPC peering**: VPC peering requests between projects — test approving/creating peering to a project you don't own.

### regatta.aiven.io (internal app — UNAUTHORIZED ACCESS ONLY)
- [ ] Unauthenticated recon only: what loads without a session? Directory/endpoint enumeration via passive means.
- [ ] Auth bypass attempts are limited to logic flaws (e.g. forced browsing to internal paths) — NO credential attacks, NO brute force.
- [ ] Any authenticated-feeling content served without auth = immediate report. Do not poke further than confirming it's reachable.

### aiven.io (marketing site + docs)
- [ ] Deprioritize — the brief says website vulns are heavily duped. Only test if you spot something novel (e.g. docs search reflecting unsanitized input, authenticated docs features).
- [ ] `aiven.io/docs` is still valuable as RECON: endpoint names, parameter formats, and feature flags documented there feed the api.aiven.io tests.

---

## 3. The managed-service angle — two-account cross-account isolation testing (highest value)

This is the P1 class. The brief explicitly wants cross-account access findings. Do it with TWO accounts you own — never another customer's resources.

**Setup (safe, by the book):**
1. Create two accounts using `@bugcrowdninja.com` email aliases (required by the brief). E.g. `shiva92-a@bugcrowdninja.com`, `shiva92-b@bugcrowdninja.com`.
2. Use free tier + trial credits. If you need more services running, request extra credits via the program — the brief offers this.
3. Account A: project `proj-a`, create one PostgreSQL service and one Kafka service. Note their UUIDs, connection URIs, and ports from console.
4. Account B: project `proj-b`, create one PostgreSQL service (so B is a "legitimate" customer too).

**Test battery (API layer):**
- T1: From B's token: `GET /v1/project/proj-b/service/{A_pg_uuid}` → must be 403/404.
- T2: From B's token: `GET /v1/project/proj-a/service/{A_pg_uuid}` (A's real project name) → must be 403/404.
- T3: Limited-role member test: in org A, add a member with the lowest role; that member calls ServiceGet on org A's production service → connection URI with password must NOT be returned without `service:secrets:read`.
- T4: Backups: `ServiceBackupsGet` needs `service:configuration:write` — from B, request A's backup list. Backups contain full data dumps; any leak here is critical.
- T5: Service integration: from B, `ServiceIntegrationCreate` with `sourceServiceName` = A's Kafka service name → must fail.

**Test battery (data-plane / network layer):**
- T6: From a client inside B's service environment (or your machine), attempt TCP connections to A's service host:port WITHOUT credentials → must fail closed (TLS + auth).
- T7: Kafka ACLs: use B's Kafka SASL credentials against A's Kafka broker address → must be rejected. Never use A's credentials from B's context — that proves nothing.
- T8: DNS/hostname probing: check whether A's internal hostnames resolve or leak info (service discovery endpoints, metrics ports like Grafana) from an unauthenticated position.

**Rules for this battery:** touch ONLY proj-a and proj-b. If any test unexpectedly succeeds against a resource you don't recognize as yours, STOP and report — do not explore further.

---

## 4. Rate / safety discipline (per the brief)

- **Emails:** `@bugcrowdninja.com` only. No other addresses.
- **Scope of action:** only your own accounts, projects, and services. Customer services you didn't create are OUT OF SCOPE — never touch them.
- **No DoS:** no load testing against Kafka/PostgreSQL, no mass service creation/deletion loops, no backup/restore storms. Single-digit requests/second, manual-style.
- **No social engineering.** No phishing anyone, including fake "Aiven support".
- **No scanners** in the automated sense — this plan is manual requests + curl. Nuclei/ffuf/SQLmap stay off.
- **Version-based CVEs:** upstream CVE in PostgreSQL/Kafka/etc. is NOT a finding unless you demonstrate a working PoC against Aiven's actual infra (they mitigate many upstream CVEs).
- **The `aivenv1` header is not a vuln.** Don't report your own token working.
- **Out of scope, don't bother:** other subdomains (third-party hosted — verify hosting first), the test environment, `github.com/Aiven-Labs`, partner interfaces.
- **Before submitting:** re-verify the current reward range on the live brief (max was removed from advertising at one point); confirm the finding reproduces from a clean session; include both accounts' roles, exact requests, and impact (what data/action crossed the boundary).
