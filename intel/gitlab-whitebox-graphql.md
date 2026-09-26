# GitLab GraphQL Mutations — White-Box Authorization Audit

**Date:** 2026-09-26 · **Source:** `~/workspace/hacker-agent/src/gitlab` (sparse clone, master @ 43572ea) + targeted service/model/lib paths pulled read-only into `/tmp/gitlab-wb` (public gitlab-org/gitlab, same master). Source tree NOT modified.
**Method:** mutation file → `authorize` directive chain → `authorized_find!`/`authorize!` mechanics → underlying service → model/policy enforcement. A gap between where the decision SHOULD happen and where it ACTUALLY happens = CODE-CONFIRMED.

## Verdict up front

**[CODE-CONFIRMED ISSUES]: none. Zero.** All five hypothesized seams were traced to a real enforcement point. The recurring architectural fact this audit established: **GitLab enforces target-object authorization in the SERVICE layer, not the mutation layer.** The prior differential flagged "no authorize at the mutation layer" as suspicious, but in every case the service re-validates with an equal or stricter ability. The prior `issueMove` hypothesis was additionally based on a false premise (see §1).

---

## [CODE-CONFIRMED ISSUES]

*(none — every seam below resolved to an enforced check)*

---

## [HIGH-CONFIDENCE LEADS]

### L1 — The "unauthorized target resolution" PATTERN (watchlist, not a finding)
Four mutations resolve a security-relevant target object with **zero mutation-layer authorization**, delegating entirely to the service:

| Mutation | Target resolution (no authz) | Service backstop (verified) |
|---|---|---|
| `CiJobTokenScopeAddProject` | `Project.find_by_full_path(target_project_path)` — `app/graphql/mutations/ci/job_token_scope/add_project.rb:45` | `validate_source_project_and_target_project_access!` — `app/services/concerns/ci/job_token_scope/edit_scope_validations.rb:18-26` |
| `CiJobTokenScopeUpdatePolicies` | `find_target_using_path` (Group OR Project) — `update_job_token_policies.rb:76-79` | `validate_permissions!` — `app/services/ci/job_token_scope/update_policies_service.rb:65-69` |
| `ProjectTransfer` | `find_object(namespace_id)&.sync` — `app/graphql/mutations/projects/transfer.rb:31` | `ensure_allowed_transfer` — `app/services/projects/transfer_service.rb:178-192` |
| `GroupTransfer` | `find_object(target_id)&.sync` — `app/graphql/mutations/groups/transfer.rb:37` | `ensure_allowed_transfer` — `app/services/groups/transfer_service.rb:228-289` |

All four backstops verified present (details in REJECTED). **Why it's a lead:** this is the exact shape a future authorization bug will take — any new mutation that resolves a target and calls a service *without* such validation inherits the gap silently. If GitLab ever refactors these services to drop the target check (e.g. "the mutation already authorized"), the mutation layer will not catch it. Worth re-verifying on each GitLab upgrade, but NOT reportable today.

### L2 — Runner registration-token reset is fail-closed to the point of looking broken (CE)
`update_runners_registration_token` is `enable`d **only** for `ApplicationSetting` + admin (`app/policies/application_setting_policy.rb:8-11`). `GroupPolicy` and `ProjectPolicy` contain only conditional `prevent` rules (`group_policy.rb:269-272`, `project_policy.rb:946-947`) and **no enable rule** for this ability on group/project subjects. Under declarative_policy fail-closed defaults, the GraphQL `RunnersRegistrationTokenReset` mutation (`app/graphql/mutations/ci/runners_registration_token/reset.rb:9,27`) can therefore only succeed for the instance scope (admin-only). Either group/project resets are intentionally admin/instance-only (secure, possibly a UX bug) or EE grants it elsewhere (this tree is CE-only, `ee/` absent). Not a vulnerability — the failure direction is deny — but flag-worthy if anyone claims group owners can rotate runner tokens via GraphQL.

---

## [REJECTED] — traced to enforced checks

### R1. `issueMove` — REJECTED (prior hypothesis was factually wrong)
- **False premise corrected:** the differential claimed "no classic `authorize` ability at the mutation layer." In fact `Mutations::Issues::Base` — which `Move` inherits — declares `authorize :update_issue` (`app/graphql/mutations/issues/base.rb:21`).
- **Enforcement mechanics:** `authorized_find!` (`lib/gitlab/graphql/authorize/authorize_resource.rb:56-61`) → `authorize!(object)` → `authorized_resource?` checks `self.class.authorization.ok?(object, current_user)` (`authorize_resource.rb:64-70`), where the authorization object aggregates inherited `authorize` directives. So `:update_issue` IS enforced on the source issue.
- **Granular tokens:** `authorize_granular_token permissions: :move_issue, boundary_argument: :project_path` (`move.rb:8-9`).
- **Service backstop (the strict check):** `MoveService#verify_can_move_work_item` (`app/services/work_items/data_sync/move_service.rb:86-110`) → `Issue#can_move?` (`app/models/issue.rb:717-722`):
  ```ruby
  def can_move?(user, to_namespace = nil)
    if to_namespace
      return false unless user.can?(:admin_issue, to_namespace)
    end
    !moved? && persisted? && user.can?(:admin_issue, self)
  end
  ```
  Requires `:admin_issue` on the **target namespace AND the source** — strictly stronger than the mutation layer's `:update_issue`.
- **Unbypassable ordering:** `WorkItems::DataSync::BaseService#execute` runs `verify_work_item_action_permission` before anything else (`app/services/work_items/data_sync/base_service.rb:22-25`); the `skip_work_item_type_check` bypass is an explicit Ruby keyword, not user-controllable params (`move_service.rb:10-17`).
- **Target type confusion closed:** `target_work_item_type_id` is validated against types available in the target namespace (`target_work_item_type_not_available_error_message`, `move_service.rb:131-133`).
- Verdict: three layers, fail-closed throughout. NOT a vulnerability.

### R2. Bulk member update (`ProjectMemberBulkUpdate` / `GroupMemberBulkUpdate`) — REJECTED
- **Mutation layer:** `authorize :admin_project_member` + granular `:update_member` (`app/graphql/mutations/members/projects/bulk_update.rb:11-12`); `authorized_find!` enforces on the source project.
- **Scope narrowing:** `BulkUpdateBase#ready?` restricts to direct members only, max 50, all-or-nothing (`app/graphql/mutations/members/bulk_update_base.rb:44-60`).
- **Escalation guard (service):** `Members::UpdateService#has_update_permissions?` (`app/services/members/update_service.rb:85-90`) requires ability + owner-transition guards + `!role_too_high?(member)`.
- `role_too_high?` → `Member#prevent_role_assignement?` (`app/models/member.rb:675-686`) → `source.can_assign_role?(current_user, assigning_access_level)` → `Authz::HasRoles#can_assign_role?` (`app/models/concerns/authz/has_roles.rb:16-21`): the caller's own max access level must encompass the level being assigned. A Maintainer mathematically cannot assign Owner.
- Verdict: `access_level` above the caller's own level is blocked at the service layer. NOT a vulnerability.

### R3. `ciJobTokenScopeAddProject` — REJECTED
- **Mutation layer:** `authorize :admin_project` on the source project (`add_project.rb:11`, enforced at `:44` via `authorized_find!`). Target resolved unauthenticated at `:45`.
- **Service backstop:** `Ci::JobTokenScope::AddProjectService#execute` → `validate_source_project_and_target_project_access!` (`app/services/concerns/ci/job_token_scope/edit_scope_validations.rb:18-26`): requires `:admin_project` on source **and** `:read_project` on target. Nil target fails the `can?` check → `ValidationError` → surfaced as mutation error (rescued in service).
- Same validation shape covers `UpdatePoliciesService` (`update_policies_service.rb:65-69`, group+project variants) and `AddGroupOrProject`.
- Verdict: target IS authorized — at the service, not the mutation. The split is defense-in-depth, not a gap. NOT a vulnerability.

### R4. `projectTransfer` / `groupTransfer` — REJECTED
- **Mutation layer:** `authorize :change_namespace` (`projects/transfer.rb:8`) / `:change_group` (`groups/transfer.rb:9`) on the source only; target namespace resolved without authorization (`projects/transfer.rb:31`, `groups/transfer.rb:37`).
- **Service backstop (project):** `Projects::TransferService#ensure_allowed_transfer` (`app/services/projects/transfer_service.rb:178-192`): `allowed_transfer_project?` → `can?(:change_namespace, project)` **and** `allowed_to_transfer_to_namespace?` → `can?(:transfer_projects, namespace)` (`transfer_service.rb:268-271`).
- **Service backstop (group):** `Groups::TransferService#ensure_allowed_transfer` (`app/services/groups/transfer_service.rb:228-289`): `can?(:change_group, group)` **and** `can?(:create_subgroup, new_parent_group)` (or `can?(:create_group)` for top-level) (`transfer_service.rb:284-289`).
- Both `schedule_async_transfer` and `execute` call `ensure_allowed_transfer` first — the GraphQL path (`schedule_async_transfer`) is covered.
- Verdict: target namespace authorized at the service layer. NOT a vulnerability.

### R5. Token mutations — all REJECTED
- **ClusterAgentTokenCreate** (`clusters/agent_tokens/create.rb:9,41`): `authorize :create_cluster` via `authorized_find!` on the agent; service independently re-checks `current_user.can?(:admin_pipeline, project) && current_user.can?(:create_cluster, project)` (`app/services/clusters/agents/create_service.rb:21`). One-time secret returned once by design.
- **PipelineTriggerCreate** (`ci/pipeline_trigger/create.rb:11,32`): `authorize :manage_trigger` via `authorized_find!`. Standard.
- **RunnersRegistrationTokenReset** (`ci/runners_registration_token/reset.rb:9,27`): `authorize :update_runners_registration_token`; instance scope requires admin (`application_setting_policy.rb:8-11`); group/project scopes fail closed in this tree (see L2). No privilege path for non-admins.
- **PersonalAccessTokenCreate** (`users/personal_access_tokens/create.rb`): when the caller authenticates with a granular token, `Authz::Tokens::PrivilegeEscalationCheck` (`app/services/authz/tokens/privilege_escalation_check.rb:18-33`) requires every requested scope's expanded permissions to be a subset of the calling token's scopes; `validate_sudo_not_escalated!` blocks sudo escalation (`create.rb`, `validate_sudo_not_escalated!`); `boundary!` requires `:read_boundary` on any project/group the token is scoped to. Session-authenticated creation is the user's own privilege — no escalation possible.
- **Job-token-scope allowlist mutations:** covered under R3.

---

## Methodology note for future audits
`authorized_find!` enforces the *inherited* `authorize` directives (via `AuthorizeResource#authorized_resource?`), so auditing a mutation's own file alone under-counts enforcement — the base classes (`Issues::Base`, `BulkUpdateBase`, `BaseMutation`) and the service layer must be read. In this codebase the security-critical invariant for cross-object mutations (move, transfer, allowlist) consistently lives in the service, one layer below where a mutation-only audit looks.
