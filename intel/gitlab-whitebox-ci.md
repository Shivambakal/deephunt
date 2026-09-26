# GitLab white-box audit: CI variables + job-token scoping

Source: `~/workspace/hacker-agent/src/gitlab` (policies, GraphQL) + fresh sparse clone at `/tmp/gitlab-wb`
(gitlabhq/gitlabhq master, 2026-09-26) for `app/models/ci`, `lib/api`, `lib/gitlab/auth`, `app/services`.
Method: traced every `authorize` on variable reads; traced job-token auth from finder → identity → scope enforcement.

Key architectural fact: a CI job token authenticates as **the job's user with full abilities**
(`lib/gitlab/auth/auth_finders.rb:491-515` — `find_user_from_job_token_query_params_or_header` /
`find_user_from_job_token_basic_auth` → `resolve_composite_identity_user(job.user)`).
The token scope (inbound allowlist) is a *restriction* layered on top, enforced at exactly two points:
- `authorized_project_scope?` (`lib/api/helpers.rb:199`) — only when the route sets `job_token_scope: :project`
- `authorize_job_token_policies!` (`lib/api/helpers.rb:191`) → `job_token_policies_authorized?`
  (`lib/api/helpers.rb:1282`) → `Ci::JobToken::Scope#policies_allowed?` → `inbound_accessible?`
  (`app/models/ci/job_token/scope.rb:84-100`) — **skipped entirely when the route sets
  `skip_job_token_policies: true`** (`lib/api/helpers.rb:1312-1316`).

Note: GraphQL explicitly rejects CI job tokens
(`lib/gitlab/auth/request_authenticator.rb:103-104`: "CI_JOB_TOKENs are not allowed for now,
since their access is too broad") — all GraphQL paths below are user/PAT-token only.

---

## [CODE-CONFIRMED ISSUES]

### 1. CI job-token scope (inbound allowlist) not enforced on package-registry endpoints (PyPI group/project, Composer group, npm namespace)

**Mechanism (code-confirmed):** These endpoints accept CI job tokens but never invoke the
allowlist check:

| Endpoint file | Routes | Job-token auth | Scope enforcement |
|---|---|---|---|
| `lib/api/pypi_packages.rb:200,229,253` | `GET /groups/:id/-/packages/pypi/files/...`, `.../pypi/simple`, `.../pypi/simple/:package_name` | `job_token_allowed: :basic_auth` | `find_authorized_group!` (`lib/api/helpers/packages/basic_auth_helpers.rb:43-58`) = pure `can?`, **no scope check**; `skip_job_token_policies: true` |
| `lib/api/pypi_packages.rb:283,329,357,385,423,466` | project-level PyPI incl. `POST` upload/authorize | `job_token_allowed: :basic_auth` | `authorized_user_project` → `authorized_project_find!` (same file:24-40) = pure `can?`, **no scope check** |
| `lib/api/composer_packages.rb:82,100,118,138` | group Composer metadata/packages | `job_token_allowed: :basic_auth`, `boundary_type: :group` | `find_authorized_group!`, **no scope check**; `skip_job_token_policies: true` |
| `lib/api/concerns/packages/npm_namespace_endpoints.rb:60-65` | `GET /*package_name` (npm metadata) | `job_token_allowed: true` | `project` resolved via `find_project!`, but `authorize_job_token_policies!` inside it short-circuits on the route's `skip_job_token_policies: true`; `authorized_project_scope?` passes (no `job_token_scope: :project` setting) |

**Impact:** A job token minted for project A can download private packages from any group/project
the *pipeline triggerer* can read — regardless of the job-token allowlist. The token never grants
more than the triggerer's own permissions (no direct privilege escalation), but it **defeats the
token-scoping containment control**: exfiltrating one CI_JOB_TOKEN (a well-known CI attack pattern —
malicious dependency/job script exfiltrating the token) gives the attacker the triggerer's package
read/download reach instead of being confined by the allowlist. Private package contents = secrets
(source tarballs, internal libraries) readable by a low-priv principal holding the token.

**Exploitability prerequisite (not statically provable):** attacker must obtain a job token from a
job triggered by a more-privileged user (e.g., scheduled pipeline owned by a maintainer, or a
compromised job in a shared project). The authorization gap itself is confirmed in code; end-to-end
validation needs a live instance and is left for the authenticated hunt.

**Why this looks unintended, not designed:** the npm route's own comment
(`npm_namespace_endpoints.rb:61-64`) says the skip exists for *granular PAT* authorization
("Granular token authorization is skipped because…"), but the flag also silently disables the
*job-token allowlist* — a different control. The container-registry routes with the same flag are
separately protected by `job_token_scope: :project`
(`lib/api/project_container_repositories.rb:24`), showing the intended defense-in-depth pattern
these package routes lack.

### 2. Job-token-scope allowlist target existence oracle (LOW)

- `app/graphql/mutations/ci/job_token_scope/add_group_or_project.rb:73-76`:
  `find_target_path` does unscoped `Group.find_by_full_path(target_path) || Project.find_by_full_path(target_path)`.
- `app/services/concerns/ci/job_token_scope/edit_scope_validations.rb`:
  nil target → `NotFoundError, 'The group or project does not exist.'`;
  found-but-unreadable target → `ValidationError, 'The target_group/target_project … does not exist or you don't have permission to perform this action'`.
  The mutation returns `errors: [result.message]`, so the two cases are distinguishable.
- Any user with `admin_project` on any project (maintainer+) can probe existence of private
  group/project full paths. Low severity (paths are often guessable), but a real oracle.

---

## [HIGH-CONFIDENCE LEADS]

None beyond the two items above — the remaining attack surface audited clean (see REJECTED).
The package-endpoint scope bypass (item 1) is the single finding worth runtime validation:
with two owned projects (A = attacker CI, B = victim with private PyPI package, triggerer of A's
pipeline = user who can read B), confirm `GET /groups/:id/-/packages/pypi/simple/...` with A's
`CI_JOB_TOKEN` succeeds while B's allowlist does not include A.

---

## [REJECTED]

**Variable values — no readable path for low-priv principals:**
- GraphQL: `project.ci_variables` (`app/graphql/types/project_type.rb:544-548`),
  `project.inherited_ci_variables` (`:550-554`), `group.ci_variables`
  (`app/graphql/types/group_type.rb:302-307`) all carry `authorize: :admin_cicd_variables`;
  root `query.ci_variables` (instance) is gated in the resolver by
  `current_user&.can_admin_all_resources?`
  (`/tmp/gitlab-wb/app/graphql/resolvers/ci/variables_resolver.rb:17-19`).
- REST: `lib/api/ci/variables.rb:9` (`before { authorize! :admin_cicd_variables, user_project }`),
  `lib/api/group_variables.rb:8`, `lib/api/admin/ci/variables.rb` — all gated.
- Hidden values are redacted at both layers via `Ci::VariableValue#evaluate`
  (`/tmp/gitlab-wb/app/models/ci/variable_value.rb`: `variable.hidden? ? nil : variable.value`),
  used by `ProjectVariableType#value`, `InstanceVariableType#value`, and
  `API::Entities::Ci::Variable` (`lib/api/entities/ci/variable.rb`). Masked (non-hidden) values
  are readable by variable admins — by design (masked ≠ hidden).
- `InheritedCiVariableType` exposes metadata only (key/protected/masked/hidden/group_name) —
  no `value` field (`app/graphql/types/ci/inherited_ci_variable_type.rb`); only
  `group_ci_cd_settings_path` is additionally gated. (Note: `InheritedVariablesResolver`
  declares `type ProjectVariableType`, but the field type `InheritedCiVariableType` governs at
  runtime — no value leak.)
- Job-token access to `GET /projects/:id/variables`: token confers the *triggerer's* abilities
  within the token's own project (`self_referential?` allowlist pass); a job already receives
  variable values as env vars, so no new disclosure.
- `read_manual_variables` (`app/graphql/types/ci/job_type.rb:95`) is never enabled in any policy —
  fail-closed dead field, not exploitable.
- Pipeline/schedule manual variable values gated by `read_pipeline_variable`
  (`app/policies/ci/pipeline_policy.rb:56-62`: maintainer+ or pipeline triggerer) and
  `read_pipeline_schedule_variables` (`app/policies/ci/pipeline_schedule_policy.rb:28-31`:
  maintainer+ or schedule owner) — owner-scoped by design.

**Job-token scope mutations — no unauthorized widening:**
- `CiJobTokenScopeAddProject` / `AddGroupOrProject` / `UpdateJobTokenPolicies` / removals all
  require `authorize :admin_project` on the source project; services additionally require
  `read_project`/`read_group` on the target
  (`app/services/concerns/ci/job_token_scope/edit_scope_validations.rb:
  validate_source_project_and_target_project_access!`,
  `validate_source_project_and_target_group_access!`). A maintainer can only allowlist targets
  they can already read — delegation, not escalation.

**Runner registration-token reset — fail-closed:**
- `update_runners_registration_token` is enabled **only** in `ApplicationSettingPolicy`
  (instance admins); for projects/groups it is only ever *prevented* when the feature is disabled
  (`app/policies/project_policy.rb:945-947`, `app/policies/group_policy.rb:269-272`) and never
  enabled — verified against live upstream master. GraphQL
  (`app/graphql/mutations/ci/runners_registration_token/reset.rb`), REST
  (`lib/api/ci/runners.rb:525,547`), and service
  (`app/services/ci/runners/reset_registration_token_service.rb`) all deny for group/project
  scope. Consistent with the runner-registration-token feature removal — fail-closed, not a bypass.

**Pipeline schedule take-ownership — properly gated twice:**
- Mutation: `authorize :admin_pipeline_schedule`
  (`app/graphql/mutations/ci/pipeline_schedule/take_ownership.rb:9`).
- Service: `TakeOwnershipService#allowed?` → `user.can?(:admin_pipeline_schedule, schedule)`
  (`app/services/ci/pipeline_schedules/take_ownership_service.rb`).
- Policy (`app/policies/ci/pipeline_schedule_policy.rb:28-31`): maintainer+ via `admin_pipeline`,
  or schedule owner with `update_build` — bound to the schedule's own project. No cross-project path.
  (`PipelineSchedule::Play` similarly gated by `play_pipeline_schedule`.)

**Triggers — no cross-project confusion:**
- `Ci::PipelineTriggerService#create_pipeline_from_trigger` returns unless
  `trigger.project == project` (URL-bound) (`app/services/ci/pipeline_trigger_service.rb:29`).
- Job-token trigger path requires `can?(job.user, :read_project, project)` (`:58`) — confers only
  the triggerer's own authority (documented multi-project pipeline behavior).

**Other `skip_job_token_policies` routes — not affected:**
- Container registry (`lib/api/project_container_repositories.rb`): protected by
  `job_token_scope: :project` → `authorized_project_scope?` enforces token-project equality.
- Conan `users/authenticate`, `users/check_credentials`, `ping`: self-credential/public endpoints;
  actual package reads use enforced `job_token_policies: :read_packages`.
- `GET /job`, `GET /job/allowed_agents` (`lib/api/ci/jobs.rb:318,336`): self-referential to
  `current_authenticated_job` — no cross-boundary access.

---

## Files of interest for follow-up

- `/tmp/gitlab-wb/lib/api/helpers.rb` — `authorize_job_token_policies!` (191),
  `authorized_project_scope?` (199), `job_token_policies_authorized?` (1282),
  `skip_job_token_policies?` (1312)
- `/tmp/gitlab-wb/lib/api/helpers/packages/basic_auth_helpers.rb` — `find_authorized_group!` (43),
  `authorized_project_find!` (24): no token-scope checks
- `/tmp/gitlab-wb/lib/gitlab/auth/auth_finders.rb` — job-token → user identity (491-515)
- `/tmp/gitlab-wb/app/models/ci/job_token/scope.rb` — allowlist logic (84-100)
- `/tmp/gitlab-wb/app/models/ci/variable_value.rb` — hidden redaction
