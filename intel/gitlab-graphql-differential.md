# GitLab GraphQL vs REST Authorization Differential (passive, docs + source)

Date: 2026-09-26. Method: public GitLab docs and public GitLab source (fork mirror, CE+generated docs). No authenticated testing.
Methodology: `~/workspace/hacker-agent/deep-vuln-methodology.md` §3 (cross-feature) and §4 (differential across APIs/roles/methods/formats/states).

## Authorization model (documented, applies to everything below)

- GraphQL is versionless, served at `/api/graphql`. Some queries permit anonymous access; **all mutations require authentication**.
- Token-scope split: queries are satisfiable with `read_api`; mutations require the **`api`** scope
  (`Mutations::BaseMutation.authorization_scopes == [:api]`, checked via `:execute_graphql_mutation`).
  Session-cookie (`_gitlab_session`) auth bypasses scope checks.
- Per-mutation authorization is declared with `authorize :ability` (checked against the boundary object)
  and/or `authorize_granular_token permissions: ..., boundary_argument: ...` (applies when the caller
  authenticates with a granular PAT).
- Object identity: GraphQL uses **Global IDs** (`gid://gitlab/Project/123`); REST uses numeric IDs or URL-encoded paths.
- The generated GraphQL reference in this repo snapshot documents **712 mutations** — this report's
  catalog is drawn from that reference plus the mutation source files.

## [OBJECT COMPARISON TABLE]

Legend: GQL-only = no REST equivalent found in `doc/api`; REST-only = no GraphQL mutation in the 712-mutation reference.

### Issues / Work items

| Capability | GraphQL | REST | Auth notes / differential |
|---|---|---|---|
| Create / update / delete issue | `issueCreate`, `issueUpdate`, (`workItemsDelete`) | `POST/PUT/DELETE /projects/:id/issues` | Parity expected; both funnel to issue services |
| Move issue cross-project | `issueMove` | `POST /projects/:id/issues/:iid/move` | **Differential:** GQL mutation declares **no classic `authorize` ability** (only `authorize_granular_token`); relies on read-scoped `authorized_find!` + `WorkItems::DataSync::MoveService`. REST doc explicitly returns 400 on insufficient permission. Policy: `move_issue` requires `admin_issue` (issue_policy.rb). Structural seam — probe whether service enforcement matches REST controller enforcement |
| Target project lookup on move | `resolve_project(...).sync` — **not** `authorized_find!` | `to_project_id` param, controller-authorized | Second-object lookup unauthenticated at mutation layer; service must enforce |
| Set confidential | `issueSetConfidential` | `confidential` attr on issue update | Parity |
| Lock discussion | `issueSetLocked`, `mergeRequestSetLocked` | `discussion_locked` on update | Parity |
| Link alerts to issue | `issueLinkAlerts`, `issueUnlinkAlert` | No equivalent in issues REST API (alert promotion is separate) | **GQL-only** |
| CSV import/export of work items | `workItemsCsvImport`, `workItemsCsvExport` | No REST equivalent found | **GQL-only** |
| Hierarchy / linked items | `workItemsHierarchyAddChildrenItems`, `workItemsHierarchyReorder`, `workItemsLinkedItemsAdd/Remove`, `workItemConvert` | Partial (epic links REST) | Mostly **GQL-only** surface |
| Time tracking | — | `POST .../issues/:iid/add_spent_time`, `/reset_time_spent`, `/time_estimate` | **REST-only** |

### Merge requests

| Capability | GraphQL | REST | Auth notes / differential |
|---|---|---|---|
| Create / update / delete MR | `mergeRequestCreate/Update` | `POST/PUT/DELETE /projects/:id/merge_requests` | Parity |
| Accept (merge) | `mergeRequestAccept` (`authorize :accept_merge_request`) | `PUT .../merge_requests/:iid/merge` | Both; GQL **requires caller-supplied `sha`** that must equal `diff_head_sha` (SHA_MISMATCH guard) — REST has `sha` param too but optional-ish; compare enforcement |
| Re-request review | `mergeRequestReviewerRereview` | No match in `doc/api/merge_requests.md` | **GQL-only** |
| Set assignees/reviewers/labels/milestone/draft/subscription | `mergeRequestSet*` family | Covered by MR update / separate endpoints | Parity |
| Saved views | `mergeRequestSavedViewsCreate/Update/Delete` | No equivalent | **GQL-only** |
| Approvals / approval rules | — | `/projects/:id/merge_requests/:iid/approve`, `approval_rules` | **REST-only** (no approve mutation in GQL reference) |

### CI/CD variables

| Capability | GraphQL | REST | Auth notes / differential |
|---|---|---|---|
| Read variable **values** | `project.ciVariables`, `group.ciVariables`, `inheritedCiVariables` → `CiProjectVariable.value` | `GET /projects/:id/variables` | GQL field gated by `authorize: :admin_cicd_variables` on the connection; the **type itself declares no authorize** (`# rubocop: disable Graphql/AuthorizeTypes`) and `value` resolves via `Ci::VariableValue#evaluate`. Documented roles: project = **Maintainer**, group = **Owner** (permissions matrix). Probe: masked/hidden value leakage to sub-Maintainer via GQL vs REST; inherited group vars readable by project Maintainer (documented) vs group Owner-only rule |
| Create / update / delete variables | **None** — zero variable-write mutations in the 712-mutation reference | `POST/PUT/DELETE /projects/:id/variables`, group/instance equivalents | **REST-only writes**. The frontend's `addProjectVariable`/`updateProjectVariable`/`deleteProjectVariable` (and group/admin equivalents) are **local Apollo resolvers that call REST** — not server GraphQL mutations. Do not misclassify |
| Disable pipeline variables (safe-disable) | `safeDisablePipelineVariables` | No direct equivalent | **GQL-only** |

### Pipelines / jobs

| Capability | GraphQL | REST | Auth notes / differential |
|---|---|---|---|
| Create / cancel / retry / delete pipeline | `pipelineCreate/Cancel/Retry/Destroy` (`authorize` per mutation) | `POST/GET .../pipelines`, `POST .../pipelines/:id/cancel|retry`, `DELETE` | Parity |
| Job play / cancel / retry / unschedule / erase artifacts | `jobPlay/Cancel/Retry/Unschedule`, `jobArtifactsDestroy`, `jobArtifactBulkDestroy` | `POST .../jobs/:id/play|cancel|retry|erase` | Parity; GQL adds bulk artifact destroy |
| Pipeline schedules | `pipelineScheduleCreate/Update/Delete/Play/TakeOwnership` | Full CRUD + `POST .../take_ownership` | Parity (take_ownership exists in both) |
| Pipeline triggers (tokens) | `pipelineTriggerCreate/Update/Delete` (`authorize :manage_trigger`) | `POST/PUT/DELETE /projects/:id/triggers` | Both. **Differential:** GQL `PipelineTriggerType` exposes **`token` field** and `hasTokenExposed` under `:manage_trigger` — compare with REST serialization of trigger tokens on read |
| Runners | `runnerCreate/Update/Delete`, `runnerBulkDelete`, `runnerBulkPause`, `runnerAssignToProject`, `runnerUnassignFromProject`, `runnerCacheClear` | `POST/PUT/DELETE /runners`, assign/unassign, bulk delete/pause | Broad parity. GQL `runnerCreate`: `authorize :create_runners`; instance runners additionally require `can?(:create_instance_runners)` |
| Runner registration token reset | `runnersRegistrationTokenReset` | `POST /runners/reset_registration_token` (+ project/group variants) | Parity |
| Runner ephemeral token | `Runner.ephemeralAuthenticationToken` field, `authorize: :read_ephemeral_token` → policy grants it to **creator only** (runner_policy.rb) | No queryable equivalent; token shown once at registration | **GQL-only read** of a live credential, tightly scoped — probe the `registration_available?` window and creator check |
| CI job token scope allowlist | `ciJobTokenScopeAddProject/AddGroupOrProject/RemoveProject/RemoveGroup/UpdatePolicies` (`authorize :admin_project`) | `GET/PATCH /projects/:id/job_token_scope`, `POST/DELETE .../job_token_scope/allowlist` (doc: **Maintainer or Owner**) | Parity on role. **Differential:** GQL `target_project = Project.find_by_full_path(target_project_path)` — **no mutation-layer authz on the target**; service-enforced. Probe: can a Maintainer of project A add arbitrary project B (where caller has no role) to A's allowlist? |
| Cross-project/child pipeline visibility | GQL types for bridges, trigger jobs, nested pipelines; docs recommend GQL for trigger jobs "not accessible from the UI" | Limited | **GQL-favored reads** — probe cross-project pipeline/job field visibility vs REST |

### Imports (project / group / bulk)

| Capability | GraphQL | REST | Auth notes / differential |
|---|---|---|---|
| Start a bulk migration (direct transfer) | **None** — zero `bulkImport`-type mutations in the 712-mutation reference | `POST /bulk_imports` | **REST-only**. The "GraphQL" import client in frontend coverage is **local Apollo resolvers calling REST via Axios** — not server mutations |
| List / get / cancel bulk migrations | — | `GET /bulk_imports`, `GET /bulk_imports/:id[/entities]`, `POST /bulk_imports/:id/cancel` | **REST-only**. Note: `doc/api/bulk_imports.md` states **no role requirement** — auth is code-only, probe destination-group authorization |
| Project file import/export | — | `POST /projects/import`, `POST /projects/:id/export` (+ upload-to-URL), `POST /projects/remote-import` (caller-supplied `url`, Beta) | **REST-only**. Import accepts `overwrite` + `override_params` (override wins over archive); export can push the archive server-side to a caller URL |
| Group import/export | — | `POST /groups/import`, `POST /groups/:id/export`, `GET .../export/download` | **REST-only**; exported groups may include members/permissions; import takes caller-supplied `parent_id` |
| Placeholder-user reassignment (post-import) | `importSourceUserReassign`, `importSourceUserKeepAsPlaceholder`, `importSourceUserKeepAllAsPlaceholder`, `importSourceUserUndoKeepAsPlaceholder`, `importSourceUserRetryFailedReassignment`, `importSourceUserResendNotification`, `importSourceUserCancelReassignment` | Partial (bulk_imports source-user endpoints exist in newer REST) | **Mostly GQL surface** — probe: reassigning placeholder users to arbitrary users, notification spam via resend |
| Jira import | `jiraImportStart`, `jiraImportUsers` | `POST /projects/:id/jira/import` (separate) | Both exist; compare auth |
| Work-item CSV import | `workItemsCsvImport` | — | **GQL-only** |

### Members

| Capability | GraphQL | REST | Auth notes / differential |
|---|---|---|---|
| Add / update / remove single member | — (no single-member GQL mutations) | `POST/PUT/DELETE /projects/:id/members/:user_id`, group equivalents, approve endpoints | **REST-only** for single-member ops |
| **Bulk** update members (up to 50/call) | `projectMemberBulkUpdate` (`authorize :admin_project_member`, "at least Maintainer"), `groupMemberBulkUpdate` | **No bulk endpoints** in members REST docs | **GQL-only**. Guards: direct-members-only (`INVALID_MEMBERS_ERROR`), 50-member cap. Probe: `access_level` escalation above caller's own level; `expires_at` manipulation; inherited-member confusion |
| Export group members | `groupMembersExport` (introduced 17.4, **Experiment**) | Member list endpoints only | **GQL-only**, experimental — probe auth vs REST member visibility |
| Custom member roles | `memberRoleCreate/Update/Delete`, `memberRoleAdminCreate/Update/Delete`, `memberRoleToUserAssign` (17.7, Experiment) | `member_roles` REST API exists | Both; GQL versions are newer/experimental — compare role/permission parity |

### Tokens / credentials

| Capability | GraphQL | REST | Auth notes / differential |
|---|---|---|---|
| Personal access tokens | `personalAccessTokenCreate` (granular scopes, `sudo` arg), `personalAccessTokenRotate`, `personalAccessTokenRevoke` | `/personal_access_tokens` (list/get/rotate/revoke) + `/users/:id/personal_access_tokens` create | Both. GQL create runs a **privilege-escalation check** of requested granular scopes against the *calling token*, and `sudo: true` requires the owner be admin. Probe: session-auth path (no calling token → check skipped?), scope-boundary confusion on `SELECTED_MEMBERSHIPS` resource_ids (mutation does verify `:read_boundary` per resource) |
| Pipeline trigger tokens | `pipelineTriggerCreate/Update/Delete` | `/projects/:id/triggers` CRUD | Both; GQL type exposes `token` on read (`:manage_trigger`) |
| Runner tokens | `runnerCreate` (+ ephemeral token field), `runnersRegistrationTokenReset` | `/runners` create returns token; reset endpoints | Both; GQL ephemeral-token field is creator-only |
| Cluster agent tokens | `clusterAgentTokenCreate` (returns **`secret`** one-time; `authorize :create_cluster`), `clusterAgentTokenRevoke` | Cluster agents REST API | GQL documented; compare REST parity before probing |
| Deploy tokens | — | `/projects/:id/deploy_tokens`, `/groups/:id/deploy_tokens` | **REST-only** (no deploy-token mutations in GQL reference) |
| Integration tokens | `httpIntegrationResetToken`, `prometheusIntegrationResetToken`, `dastSiteTokenCreate` | Integrations REST API | GQL reset mutations — compare auth with REST integration update |

## [SENSITIVE MUTATIONS]

Mutations affecting imports, tokens, variables, or membership (all verified present in the generated
GraphQL reference; authorization from mutation source where CE-available, else as documented):

**Membership / roles**
- `projectMemberBulkUpdate`, `groupMemberBulkUpdate` — bulk role changes, ≤50, direct members only, Maintainer+ (`:admin_project_member` / `:admin_group_member`).
- `groupMembersExport` — member export, 17.4 Experiment.
- `memberRoleCreate/Update/Delete`, `memberRoleAdminCreate/Update/Delete`, `memberRoleToUserAssign` — custom roles (Premium), 17.7 Experiment.

**Tokens / credentials**
- `personalAccessTokenCreate/Revoke/Rotate` — granular PATs; `sudo` requires admin; escalation check vs calling token.
- `pipelineTriggerCreate/Update/Delete` — `:manage_trigger`; trigger token readable via `PipelineTrigger.token`.
- `runnerCreate/Update/Delete`, `runnerBulkDelete`, `runnerBulkPause`, `runnerAssignToProject`, `runnerUnassignFromProject`, `runnerCacheClear`, `runnersRegistrationTokenReset` — `:create_runners` (+ `:create_instance_runners` for instance runners).
- `clusterAgentTokenCreate` (returns `secret`), `clusterAgentTokenRevoke` — `:create_cluster`.
- `httpIntegrationResetToken`, `prometheusIntegrationResetToken`, `dastSiteTokenCreate` — integration credential resets.

**CI / job-token scope**
- `ciJobTokenScopeAddProject`, `ciJobTokenScopeAddGroupOrProject`, `ciJobTokenScopeRemoveProject`, `ciJobTokenScopeRemoveGroup`, `ciJobTokenScopeUpdatePolicies` — `:admin_project`; target looked up without mutation-layer authz.
- `safeDisablePipelineVariables` — GQL-only.

**Imports**
- `importSourceUserReassign`, `importSourceUserKeepAsPlaceholder`, `importSourceUserKeepAllAsPlaceholder`, `importSourceUserUndoKeepAsPlaceholder`, `importSourceUserRetryFailedReassignment`, `importSourceUserResendNotification`, `importSourceUserCancelReassignment`.
- `jiraImportStart`, `jiraImportUsers`; `workItemsCsvImport`.
- **No** `bulkImport`/start-migration mutation exists server-side.

**Project / group lifecycle**
- `projectTransfer`, `groupTransfer` — `authorize :change_namespace`; target namespace resolved via `find_by_gid` without mutation-layer authz (service-enforced).
- `mergeRequestAccept` — `:accept_merge_request`; requires caller `sha` == `diff_head_sha`.
- `issueMove` — **no classic `authorize` at mutation layer** (only granular-token directive); enforcement delegated to `WorkItems::DataSync::MoveService`.

**Secrets Manager (distinct from CI/CD variables)**
- `projectSecretCreate/Update/Delete`, `groupSecretCreate/Update/Delete`, `*SecretsManagerInitialize/Deprovision/Enroll/Unenroll`, `*SecretPermission*` — new surface; compare with REST coverage before probing.

## [DIFFERENTIAL LEADS ranked]

1. **`issueMove` has no mutation-layer ability check.** The mutation declares only `authorize_granular_token`
   (granular-PAT path) and relies on `authorized_find!` (read) + the move service. REST documents an explicit
   permission failure (400). Policy requires `admin_issue`. Probe with a low-priv role (e.g. Reporter without
   `admin_issue`, or Developer moving into a project where they lack rights) via GQL vs REST and compare decisions.
2. **Unauthenticated-at-mutation-layer second-object lookups.** `ciJobTokenScopeAddProject`
   (`target_project` via `find_by_full_path`), `projectTransfer`/`groupTransfer` (`namespace` via `find_by_gid`),
   `issueMove` (`target_project` via `resolve_project`). All delegate to services, but any service path that
   assumes the API layer vetted the target is a hole. Probe: Maintainer of A adding unrelated project B to A's
   job-token allowlist; transferring a project into a group where the caller has no role; moving an issue into a
   project the caller cannot read.
3. **GraphQL-only bulk member update.** 50 members per call, Maintainer+, direct-members-only guard. Probe:
   `access_level` above the caller's own level (Owner grant by Maintainer), `expires_at` clearing/extension,
   and inherited-vs-direct confusion — REST has no bulk path, so any flaw here is GQL-exclusive.
4. **CI variable value reads via GraphQL.** `CiProjectVariable.value` → `Ci::VariableValue#evaluate`; the type
   carries no authorize (parent field requires `:admin_cicd_variables`). Probe masked/hidden variable values as
   Developer (below Maintainer) via GQL vs REST `GET /projects/:id/variables`; probe `inheritedCiVariables`
   (group Owner-only variables surfacing to project Maintainers) for parity breaks.
5. **Pipeline trigger token readability.** GQL exposes `PipelineTrigger.token` + `hasTokenExposed` under
   `:manage_trigger`. Determine exactly when `hasTokenExposed` is false and whether REST ever returns tokens
   where GQL hides them (or vice versa) — a token-visibility differential.
6. **Runner ephemeral token window.** `Runner.ephemeralAuthenticationToken` is creator-only and time-limited
   (`registration_available?`). Probe the window edges and whether project/group runner creators can re-read
   another creator's token.
7. **Granular PAT creation (`personalAccessTokenCreate`).** Escalation check compares requested scopes to the
   *calling token*. Probe: (a) session-cookie auth (no calling token — is the check skipped?); (b) `sudo: true`
   as non-admin; (c) `SELECTED_MEMBERSHIPS` with resource IDs the caller cannot read (mutation checks
   `:read_boundary` per resource — verify it holds).
8. **Import surface is REST-only with thin documented auth.** `POST /bulk_imports` has no documented role
   requirement; group import accepts caller-supplied `parent_id`; project remote-import accepts a caller-supplied
   `url` (Beta, SSRF surface); `override_params` override archive values. Probe destination-namespace
   authorization (import into a group you don't belong to) and the remote-import URL fetch.
9. **`groupMembersExport` (17.4, Experiment).** New GQL-only member-export path. Probe its authorization against
   REST member-list visibility (e.g. minimal-access or Guest callers).
10. **`api` vs `read_api` scope split.** Mutations hard-require `api`; some queries allow anonymous. Probe for
    state-changing behavior reachable through query-shaped operations (custom fields, `clientMutationId`
    confusion) — low probability but cheap to rule out.
11. **`mergeRequestReviewerRereview` and other GQL-only MR/issue ops** (`issueLinkAlerts`, saved views, CSV
    import/export). Newer, less-reviewed code paths — probe each for missing ability checks against its REST
    neighbors.
12. **Secrets Manager mutations vs REST.** `projectSecret*/groupSecret*` and enrollment mutations are new;
    map REST coverage first, then probe for parity breaks in who can create/read secret values.

## Anti-pitfalls (verified this session)

- Frontend "GraphQL mutations" for CI variables (`addProjectVariable`, …) and for direct transfer
  (`importGroups`, `updateImportStatus`) are **local Apollo resolvers calling REST** — they are not server-side
  GraphQL operations. Only the 712 mutations in the generated reference are real.
- There is **no server-side `bulkImport` mutation** — bulk migration start/list/cancel is REST-only.
- There are **no CI/CD-variable write mutations** in GraphQL — variable CRUD is REST-only; GraphQL reads only.
- Deploy tokens have **no GraphQL mutations** — REST-only.

## Sources

- GitLab GraphQL auth/scopes: `doc/api/graphql/index.md`, `doc/api/graphql/getting_started.md` (public mirrors used when docs.gitlab.com was unreachable: github.com/yonathanpy/gitlabhq blob HEAD).
- Mutation catalog: `doc/api/graphql/reference/_index.md` (generated from current schema; 712 mutations enumerated).
- Mutation authorization: `app/graphql/mutations/*.rb` (esp. `base_mutation.rb`, `users/personal_access_tokens/create.rb`, `ci/job_token_scope/add_project.rb`, `projects/transfer.rb`, `members/projects/bulk_update.rb` + `bulk_update_base.rb`, `merge_requests/accept.rb`, `ci/pipeline_trigger/create.rb`, `ci/runner/create.rb`, `clusters/agent_tokens/create.rb`, `issues/move.rb`).
- Type/field authorization: `app/graphql/types/ci/{pipeline_trigger_type,project_variable_type,group_variable_type,runner_type}.rb`, `app/graphql/types/project_type.rb`, `app/graphql/types/group_type.rb`; policies `app/policies/{issue_policy,project_policy,ci/runner_policy}.rb`.
- REST endpoints/auth: `doc/api/{bulk_imports,project_import_export,group_import_export,project_job_token_scopes,project_level_variables,group_level_variables,instance_level_ci_variables,project_members,group_members,personal_access_tokens,pipeline_triggers,pipeline_schedules,runners,issues,merge_requests}.md`.
- Role matrix: `doc/user/permissions.md` (group CI/CD: manage runners/variables = Owner; project: manage variables/runners = Maintainer).
- Frontend local-resolver finding: gitlab-org.gitlab.io coverage-frontend lcov reports for `import_groups/graphql/client_factory.js` and `ci/ci_variable_list/graphql/settings.js`.
