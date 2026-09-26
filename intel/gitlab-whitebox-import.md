# GitLab White-Box Audit — Import Subsystem
Date: 2026-09-26 | Source: `~/workspace/hacker-agent/src/gitlab` @ `43572ea` (master)
Scope note: checkout is sparse; audited `app/controllers/import/**`, `app/controllers/projects|groups` (imports),
`app/services/bulk_imports/**`, `app/services/projects/import_service.rb`, `app/services/projects/import_export/**`,
`app/services/groups/import_export/**`, `app/services/import/**`, `app/workers/bulk_imports/**`,
`app/workers/bulk_import_worker.rb`, `app/workers/repository_import_worker.rb`, `lib/gitlab/import_export/**`,
`lib/import/**`, `lib/bulk_imports/**`, `gems/gitlab-http/**`, `app/graphql/mutations/{import,jira_import,work_items/csv}/**`,
`app/policies/import/**`, `lib/api/bulk_imports.rb`, `app/finders/bulk_imports/**`, `app/models/bulk_imports/**`.
Working tree left unmodified (sparse-checkout expansion only). EE (`prepend_mod`) code not present — findings are CE-only.

---

## [CODE-CONFIRMED ISSUES]

### I-1. Unscoped `BulkImport.find` in HTML history/failures actions — cross-user migration metadata disclosure (IDOR)
**Files:**
- `app/controllers/import/bulk_imports_controller.rb:9` — `before_action :bulk_import, only: [:history, :failures]`
- `app/controllers/import/bulk_imports_controller.rb:107-113`
```ruby
def bulk_import
  id = bulk_import_id_param
  return unless id
  @bulk_import ||= BulkImport.find(id)   # <-- NOT scoped to current_user
  @bulk_import || render_404
end
```
- `app/controllers/import/bulk_imports_controller.rb:115-117` — `bulk_import_entity` does
  `@bulk_import.entities.find(entity_id_param)` — scoped to the *unscoped* import.
- Routes: `config/routes/import.rb:79-84` — `GET /import/bulk_imports/:id/history`,
  `GET /import/bulk_imports/:id/history/:entity_id/failures`.

**What leaks:** the `failures` view (`app/views/import/bulk_imports/failures.haml:5`) renders
`@bulk_import_entity.full_path_with_fallback` (= source group/project path being migrated, or
destination namespace/slug — `app/models/bulk_imports/entity.rb:244-246`), plus entity/import IDs in
page data attributes. The `history` view embeds another user's `@bulk_import.id` in breadcrumbs and
JS mount data. No `authorize`/`can?` call exists on these actions; only authentication is required
(`app/controllers/application_controller.rb:44`).

**Contrast (why this is a bug, not design):** the API equivalent properly scopes —
`lib/api/bulk_imports.rb:13` uses `BulkImports::ImportsFinder.new(user: current_user, ...)`, and
`app/finders/bulk_imports/imports_finder.rb:13` scopes to `user.bulk_imports`. The HTML actions were missed.

**Impact:** any authenticated user on the instance can enumerate sequential `:id`s and read other users'
bulk-import (direct-transfer migration) metadata: source group/project paths, destination namespaces,
entity IDs, failure messages. Expected severity: **Low** (auth required, metadata only, sequential IDs).
**Needs runtime proof** (two test accounts; not yet reproduced — GitLab signup is still blocked at phone verification).

---

## [HIGH-CONFIDENCE LEADS] (need runtime confirmation)

### L-1. Manifest import `remote` URL validation is nearly absent — relies entirely on downstream UrlBlocker
- `lib/gitlab/manifest_import/manifest.rb:52-62` — `validate_scheme` only rejects a `javascript:` prefix;
  `validate_remote` only requires a parseable host. So `<remote review="http://169.254.169.254/">` passes manifest validation.
- `lib/gitlab/manifest_import/project_creator.rb:17-27` feeds `repository[:url]` straight into
  `Projects::CreateService` as `import_url`.
- Mitigation in place: `Projects::ImportService#get_resolved_address`
  (`app/services/projects/import_service.rb:177-196`) runs `Gitlab::HTTP_V2::UrlBlocker.validate!` with
  `allow_localhost/allow_local_network` gated on the `allow_local_requests_from_web_hooks_and_services` admin
  setting, `dns_rebind_protection`, and `deny_cloud_metadata_requests: true` (default in
  `gems/gitlab-http/lib/gitlab/http_v2/url_blocker.rb:80-96`). Schemes limited to
  `Project::VALID_IMPORT_PROTOCOLS = %w[http https git]` (`app/models/project.rb:88`) — `file://` blocked.
- Verdict: **not exploitable as SSRF on default settings**, but the manifest layer itself performs no SSRF
  validation — any future regression in the worker-side check reopens it. Worth a differential probe
  (manifest `git://` URL to an attacker host vs `http://` — confirm both hit UrlBlocker identically).

### L-2. `Import::ValidateRemoteGitEndpointService` hands the validated URL to Gitaly
- `app/services/import/validate_remote_git_endpoint_service.rb:34` —
  `Gitlab::GitalyClient::RemoteService.exists?(uri.to_s)` after UrlBlocker validation. Gitaly performs the
  connection server-side. Validation and connection are not atomic (DNS TOCTOU), but
  `dns_rebind_protection` is enabled by default (skipped only when `http_proxy_env?` is set —
  `validate_remote_git_endpoint_service.rb:58-62`). If a target instance sets an egress HTTP proxy,
  DNS-rebind protection is silently disabled on this path — configuration-dependent, not directly exploitable.

---

## [REJECTED] (checked, defended in depth — do not report)

**R-1. Tarball path traversal on project/group file import — REJECTED.**
`lib/gitlab/import_export/command_line_util.rb:63-68` extracts via `tar -zxf -C <dir>`. Verified locally
against GNU tar 1.35: `../` members are stripped and refused ("Member name contains '..'", exit 2),
absolute paths are stripped, and symlink-directory write-through is refused ("Cannot open: Not a directory").
Post-extraction `clean_extraction_dir!` (`command_line_util.rb:96-113`) additionally removes symlinks/pipes
and raises `HardLinkError` (deleting the tree) on hardlinks.

**R-2. Bulk-import SSRF via redirect bypass — REJECTED.**
`Import::Clients::HTTP` delegates to `Gitlab::HTTP` → `Gitlab::HTTP_V2` (`lib/gitlab/http.rb:33`),
and `NewConnectionAdapter#connection`
(`gems/gitlab-http/lib/gitlab/http_v2/new_connection_adapter.rb:41-60`) runs
`UrlBlocker.validate_url_with_proxy!` on **every** connection, including redirect hops
(`follow_redirects: true` in `lib/bulk_imports/clients/http.rb:96-102`). Redirect targets cannot escape the
blocker. Initial-URL checks (`verify_blocked_uri`, `FileDownloadStrategy#validate_url!` with
`Import::Framework::UrlBlockerParams`) are consistent with fetch-time enforcement.

**R-3. Bulk-import destination-namespace takeover — REJECTED.**
`BulkImports::CreateService#validate_import_destinations!` →
`Import::Framework::DestinationValidator#validate_destination_namespace!`
(`lib/import/framework/destination_validator.rb:24-34`) requires `can?(:create_subgroup, group)` for group
entities and `can?(:import_projects, group)` for project entities. API route itself requires
`:create_bulk_import` (`lib/api/bulk_imports.rb:66`).

**R-4. Import-by-URL SSRF (UrlController / project create) — REJECTED.**
Both the `validate` endpoint (`validate_remote_git_endpoint_service.rb:40-48`) and the worker import path
(`import_service.rb:177-196`) enforce `UrlBlocker` with localhost/link-local blocking (default),
DNS-rebind protection, and scheme allowlist (`http/https/git`). `ensure_auth_credentials!` re-validates after
credential injection and aborts if the hostname changed (userinfo-smuggling guard).

**R-5. Import source-user reassignment privilege escalation — REJECTED.**
GraphQL `ImportSourceUserReassign` requires `:admin_import_source_user`
(`app/graphql/mutations/import/source_users/reassign.rb:24`), and `ReassignService#run_validations`
(`app/services/import/source_users/reassign_service.rb:100-105`) re-checks
`current_user.can?(:admin_import_source_user, import_source_user)` service-side; assignee constrained to
human/bot/service-account per settings; personal namespaces rejected. Accept flow binds
`current_user.id == reassign_to_user_id` **and** a 32-char `reassignment_token`
(`accept_reassignment_service.rb:39-46`, `app/models/import/source_user.rb:27-28`) looked up via DB equality.

**R-6. Jira import / CSV work-item import authz — REJECTED.**
`JiraImportStart`/`JiraImportUsers` require `:admin_project`
(`app/graphql/mutations/jira_import/start.rb:12`, `import_users.rb:12`); `WorkItemsCsvImport` requires
`:import_work_items` (`app/graphql/mutations/work_items/csv/import.rb:16`) with csv-only extension allowlist.

**R-7. Bulk-import API object-level authz — REJECTED.**
All read endpoints scope through `ImportsFinder`/`EntitiesFinder` with `user: current_user`
(`lib/api/bulk_imports.rb:11-32`, `imports_finder.rb:13`); POST requires `:create_bulk_import`.

**R-8. Manifest/Project/Group import controllers — REJECTED.**
`Projects::ImportsController` (`app/controllers/projects/imports_controller.rb:8`) enforces
`authorize_admin_project!`; `GitlabProjectsController#new` checks `can?(:import_projects, @namespace)`
(`app/controllers/import/gitlab_projects_controller.rb:15`); `ManifestController#upload` checks the same
(`app/controllers/import/manifest_controller.rb:23`); all controllers inherit `authenticate_user!`.

**R-9. `remote_import_url` file download SSRF — REJECTED.**
`CommandLineUtil#download` (`command_line_util.rb:47-62`) fetches via `Gitlab::HTTP.get` → V2 adapter, which
applies UrlBlocker defaults on the connection (localhost blocked, DNS-rebind protection on, cloud-metadata
deny on). No unvalidated fetch path found.

---

## Method notes
- `git status` clean after audit (sparse-checkout expansion only; no file modifications).
- Local tar behavior tests (GNU tar 1.35) were run in `/tmp` only — no target interaction.
- No runtime reproduction performed; I-1 awaits the unblocked GitLab authenticated session.
