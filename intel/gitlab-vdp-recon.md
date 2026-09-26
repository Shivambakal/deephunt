# GitLab Bug-Bounty Reconnaissance (HackerOne)

Passive only. No testing performed, no logins, no requests beyond reading public
pages. Prepared 2026-09-26 as the target model for later authenticated hunting.
Primary source: https://hackerone.com/gitlab (program policy page, read 2026-09-26).
Secondary: disclosed HackerOne reports and press coverage of GitLab security releases
(cited per-item; press items are marked as such, not first-hand report reads).

---

## [SCOPE SUMMARY]

**Program:** GitLab on HackerOne (`hackerone.com/gitlab`).
**Scope rule:** All GitLab Inc. products are in scope unless explicitly noted otherwise.
Subdomains neither in nor out of scope: testing not encouraged, but a clear
business-impact finding may still be reported (closed as Informative if ruled
out of scope, no reputation hit).

**Reward tiers (official):** GitLab.com and all products' source code pay the
highest; non-production environments pay reduced bounties; static websites pay
the lowest. Severity is CVSS-based via GitLab's public CVSS calculator, decided
by the Bug Bounty Council. Critical/High reports get $1,000 at triage ($500 for
Medium), remainder after full severity analysis. Researcher-documented ranges
(verify against the live Rewards tab): Critical (9.0–10.0) $20,000–$35,000;
High (7.0–8.9) $5,000–$15,000; Medium (4.0–6.9) $1,000–$2,500; Low (0.1–3.9)
$100–$750. Documentation-only security updates: $100. GitLab assigns CVEs for
product vulnerabilities. Three+ valid findings → 1-year self-hosted Ultimate
license (5 users).

**Rules of engagement (binding):**
- Test accounts ONLY; on GitLab.com use your `@wearehackerone.com` HackerOne
  alias on the account. Never touch projects, groups, accounts, or instances
  you do not own. No accessing other users' private data, no spam/DoS, no mass
  creation of users/groups/projects, no typosquatting.
- Strongly encouraged: test on a local GitLab Development Kit (GDK) instance
  or your own self-hosted install. NEVER test DoS on GitLab.com.
- Reports MUST include reproduction artifacts (screenshots, video, logs) against
  your own installation — no-artifact reports are closed N/A and lose
  first-reporter standing. No unverified scanner output. AI-generated reports
  without clear PoC and demonstrated impact are rejected.
- Do not request Developer access to GitLab's own projects (Community Forks
  etc.). Do not bypass HackerOne triage by opening GitLab issues or DMing staff.
- Disruptive research belongs on your own install, never GitLab.com.

**Explicitly out of scope (abridged — full list on the policy page):**
automated scanning reports; third-party GitLab sites/services (incl.
`gitlab.cn`/JiHu → `security@gitlab.cn`); user-content permission mistakes;
tokens that don't reach GitLab company projects/groups/infra or team accounts;
customers' installs; intentionally public info; social engineering/phishing/
IDN/RTL/SPF/DKIM and most HTML injection (HTML/text injection eligible only
with significant impact + minimal user interaction); missing security
headers/cookie flags; TLS/SSH issues; impactless CSRF; user/project
enumeration or path disclosure without additional impact (incl. status-code
or timing oracles for private paths, email-registration checks, ID-only
disclosure of private elements); DoS (except persistent total disruption via
unauthenticated endpoints, at GitLab's discretion; volumetric never); missing
rate limiting; published CVEs without demonstrated GitLab impact; GitLab
Runner issues that can't affect other projects/infra (shell executor seeing
other projects on the same server is documented behavior); self-managed
runner issues; count-only exposure of private objects; unsigned git-commit
spoofing; clickjacking on non-sensitive pages; privileged users sabotaging
their own projects; direct attachment-URL access (documented); EXIF
stripping; license/feature-restriction bypasses without security impact;
dependency namesquatting without automated impact; `gitlabsandbox.net`
dangling DNS; banned-user behavior; open redirects unless chained; Debian
Package Registry vulns; ServiceNow; `*.runway.gitlab.net`;
test-bucket/domain takeovers without infra/customer impact
(`*.gitlab-private.org` ineligible); CI/CD *masked*-variable disclosure
(external secret storage is the stated mitigation); third-party domain/social
takeovers; attacks requiring a victim-shared privileged token (leaked *team
member* tokens remain in scope, non-CVSS bounty); physical access; MitM;
metadata/enumeration/info-gathering UNLESS it is a privacy breach exposing
confidential user data or credentials (in-scope examples: another user's
private email/credentials, another project's env vars/secrets/CI config,
private repo contents, confidential data from unauthorized projects);
`new-sentry.gitlab.net` DSN creds; GDK-only-reproducible vulns; prompt
injection without impact beyond the current boundary (known Duo instances
listed out of scope); AI-hallucination reports.

**Disclosure:** resolved reports go public as GitLab.com issues 90 days after
the fix; HackerOne disclosure on request. Safe harbor granted.

---

## [DISCLOSED-REPORT PATTERNS]

Ranked by what GitLab actually paid. Report IDs are HackerOne report numbers;
CVE items are from press coverage of GitLab security releases (marked [press]).

### 1. Project / group import → file read, SSRF, RCE, cross-project theft
THE richest seam in program history.
- #1439593 — critical, **$29,000** — arbitrary file read via bulk imports
  UploadsPipeline.
- #827052 — critical, **$20,000** — arbitrary file read via UploadsRewriter
  when moving an issue.
- #743953 — critical, **$20,000** — steal private objects of other projects
  via project import.
- #767770 — critical, **$20,000** — private objects exposed through project
  import.
- #1132378 — critical, **$16,000** — arbitrary file read during project import.
- #341876 — critical, **$10,000** — SSRF via `remote_attachment_url` on
  import (internal services / cloud metadata).
- [press] CVE-2026-88765 — high 8.5, RCE: crafted project export overflows a
  Unicode conversion buffer during Advanced Search indexing (researcher
  joaxcar, HackerOne).

### 2. Serialization of internal models leaks secrets
- #509924 — critical, **$12,000** — JSON serialization of any Project model
  exposes all Runner tokens.

### 3. Authentication / account takeover (single biggest payout in program)
- #2293343 — critical, **$35,000** — account takeover via password reset:
  attacker JSON mixes victim + attacker email, reset link goes to both.
- #493324 — critical, **$10,000+** — any authenticated user → instance admin.
- [press] CVE-2026-0723 — high 7.4, 2FA bypass via forged device responses
  with knowledge of the victim's credential ID (researcher ahacker1,
  HackerOne).

### 4. CI/CD identity and secret scoping
- #894569 — critical, **$12,000** — attacker runs pipeline jobs as arbitrary
  user.
- [press] CVE-2026-79708 — high 8.5, developer-role user executes a policy
  test pipeline to read protected CI/CD variables outside intended scope
  (researcher yvvdwf, HackerOne).

### 5. Git-level command injection → RCE
- #658013 — critical, **$12,000** — git flag injection (branch/repo names)
  → local file overwrite → RCE.

### 6. Upload pipeline bypasses
- #850447 — critical, **$10,000** — gitlab-workhorse bypass in
  `Gitlab::Middleware::Multipart` allows files into `allowed_paths`.

### 7. GraphQL differential behavior
- #1122408 — high, **$3,370** — CSRF on `/api/graphql`: mutations executable
  via GET requests.
- [press] CVE-2026-87719 — critical 9.9, crafted GraphQL subscription
  argument bypasses serialization controls → server object lookups →
  Advanced Search configs and credentials exposed (researcher kyyblin,
  HackerOne).

### 8. Stored XSS / content injection with action forgery
- #1481207 — high, **$13,950** — XSS in ZenTao integration.
- #662287 — high, **$3,500** — stored XSS in RDoc wiki pages.
- #1409788 — high — Jupyter notebook HTML injection → arbitrary POST as
  victim user.
- #1533976 — high — Jira issue title content injection → arbitrary POST as
  victim.
- [press] CVE-2025-6948 — high 8.7, XSS executing actions on behalf of users.

### 9. Group-level policy restrictions bypassed via alternate API paths
(recurring mediums — high hit rate, lower severity)
- [press] CVE-2025-3396 — medium 4.3, project owners bypass group-level
  forking restrictions via API manipulation.
- [press] CVE-2025-4972 / CVE-2025-6168 — low, group invitation restriction
  bypasses via crafted API requests.
- [press] CVE-2024-10925 — medium 5.3, guest reads security policy YAML.
- [press] CVE-2025-0307 — medium 4.3, planner role reads code review analytics.

### 10. Miscellaneous paid logic
- #790634 — medium, **$2,000** — branch named as a git hash gets checked out
  by dependents.
- #2523654 — low — GitLab Pages subdomain takeover.
- #928255 — high — delete user account(s) without user interaction.
- [press] CVE-2026-85706 — critical, unauthenticated path traversal turning
  the Repository API into a file reader (researcher s3ntago, HackerOne;
  observed exploited in the wild).

**Pattern synthesis:** (a) Import/export is the #1 paying feature family —
file reads, SSRF, RCE, and cross-project theft all flow through it.
(b) Serialized internal objects leak tokens. (c) Auth-adjacent flows (reset,
2FA, OAuth) pay the biggest single bounties. (d) Group-level restrictions
are repeatedly enforceable in UI but bypassable via API/GraphQL — a
differential-testing goldmine. (e) GraphQL resolvers/subscriptions lag REST
authorization. (f) CI job identity and variable scoping produce criticals.

---

## [ATTACK SURFACE MAP]

(Established public GitLab architecture; docs.gitlab.com was unreachable from
this environment, so endpoint paths below are the canonical public ones —
verify live before testing.)

**Permission model (roles → objects).**
Roles: Guest → Reporter → Developer → Maintainer → Owner (plus Minimal Access
and, on newer versions, Planner/Custom roles). Objects: instances, groups
(nested), projects, issues/MRs, pipelines, environments, packages, snippets,
wikis. Key trust boundaries: group ↔ project inheritance, project visibility
(private/internal/public), confidential issues/MRs, protected branches/tags,
protected environments, security policies, group-level settings (forking,
invitations, sharing) that must bind every enforcement path.

**API versions.**
REST `/api/v4` (primary), GraphQL `/api/graphql` (queries, mutations,
subscriptions). Differential testing between REST and GraphQL is historically
productive (see #1122408, CVE-2026-87719).

**Import / export.**
Project import (file upload, URL, direct transfer), group import, bulk
imports (group migration), project/group export download. Server-side
archive extraction + attachment fetching = file-read/SSRF/RCE surface
(pattern #1 above).

**CI/CD.**
Pipelines, jobs, runners (shared/group/project), CI_JOB_TOKEN, pipeline
triggers, downstream/multi-project pipelines, environments + deployments,
variables (project/group/instance; protected/masked/hidden), pipeline
schedules, pipeline security policies ("policy test pipelines" per
CVE-2026-79708). Invariant core: job identity and variable visibility must
follow the triggering user's/project's scope.

**Webhooks & integrations.**
Project/group webhooks, system hooks, Jira/Jenkins integrations, GitLab Duo
(Agentic Chat — note: known prompt-injection instances are out of scope;
only novel impact beyond the boundary counts).

**OAuth & tokens.**
OAuth applications, authorization flow, group/project access tokens, deploy
tokens, personal access tokens, CI job tokens, runner tokens. Token-scope
validation and redirect handling are the seams.

**File uploads.**
git workhorse multipart handling, UploadsRewriter, avatars, attachments,
package registries (incl. Maven proxy), release assets, design files,
notebook rendering. Uploaded content rendered in privileged contexts has
repeatedly paid (pattern #8).

**Repository layer.**
gitaly RPC, git smart HTTP, branch/tag names passed to git commands (pattern
#5), repository API (note CVE-2026-85706 file-reader), wiki.

---

## [HYPOTHESES]

Ranked by expected value (payout history × likelihood × impact).

**H1. Import must never read outside the archive.**
*Targets:* project/group import (file, URL, direct transfer), bulk imports
UploadsPipeline, export download paths, Advanced Search indexing of imported
content. *Invariant:* "An import operation must never read, expose, or
execute files outside the uploaded archive." *Why:* the richest seam in
program history — $29k, $20k ×3, $16k, $10k file reads/SSRF, plus an RCE
via indexing (CVE-2026-88765). Test: symlink traversal, path traversal in
filenames, `remote_attachment_url`/URL-import SSRF to metadata endpoints,
polyglot archives, post-import indexing/parsing of crafted objects.

**H2. Password reset / 2FA / session flows must never be completable by an
attacker.**
*Targets:* password reset request (JSON parameter confusion à la #2293343),
2FA device-response verification (cf. CVE-2026-0723), email-change +
session invalidation, OmniAuth account linking/unlinking, remember-me token
handling. *Invariant:* "No authentication state transition may be driven
without the victim's credentials or an unguessable secret delivered to the
victim." *Why:* $35,000 — the single largest GitLab payout — plus a 7.4
2FA bypass. Test differential JSON/form parameter handling on every auth
endpoint.

**H3. No object of another namespace may be reachable by ID substitution in
any API surface.**
*Targets:* `/api/v4/:id` endpoints, GraphQL node lookups, project import
of foreign objects (#743953/#767770), direct-transfer APIs, search APIs
spanning namespaces. *Invariant:* "A resource ID must remain bound to the
authorized principal in every API version and every import path." *Why:*
$20k ×2 for import-path cross-project theft; classic IDOR still pays when
the object is private.

**H4. CI job identity must never escape its project's scope.**
*Targets:* CI_JOB_TOKEN permissions, trigger tokens, downstream/multi-project
pipelines, pipeline schedules, policy test pipelines, protected/masked
variable visibility across environments. *Invariant:* "A pipeline job must
act only as its triggering project/user and see only variables in its
authorized scope." *Why:* $12k (jobs as arbitrary user), 8.5 (protected
variables via policy test pipeline). Test: token reuse across projects,
environment-scope confusion, scheduled vs manual pipeline identity.

**H5. GraphQL must enforce exactly the authorization the REST endpoint does.**
*Targets:* `/api/graphql` queries/mutations/subscriptions mirroring REST
resources — especially newer features (Duo, Advanced Search, security
policies, releases). *Invariant:* "For every REST authorization decision,
the equivalent GraphQL resolver must reach the same decision." *Why:* CSRF
via GET mutations ($3,370), 9.9 subscription serialization bypass
(CVE-2026-87719). Method: enumerate a REST endpoint, find its GraphQL
twin, diff the authz decisions (auth vs unauth, owner vs non-owner,
role vs role).

**H6. OAuth grants and token scopes must never exceed what was authorized.**
*Targets:* OAuth application authorization flow (`redirect_uri`
validation, scope parameter), group/project access token creation and
scope enforcement, token refresh/rotation, deploy tokens. *Invariant:* "A
token must confer no privilege beyond the intersection of the grantor's
role and the approved scope." *Why:* auth-adjacent flows pay the most;
scope-confusion is the classic OAuth bug class and GitLab's token zoo
(PAT/group/project/deploy/job/runner) multiplies the seams.

**H7. Uploaded content must never execute or act in a privileged context.**
*Targets:* workhorse multipart (cf. #850447), UploadsRewriter, notebook
rendering, wiki markup, package-registry metadata (Maven proxy CSP bypass
CVE-2025-0555), release assets, avatar uploads, Jira/integration content
ingestion. *Invariant:* "Attacker-supplied file content must be inert
wherever it is stored, rendered, or parsed." *Why:* $10k workhorse bypass,
multiple high-severity content-injection-as-victim bugs. Test: polyglot
files, SVG/mathml, metadata fields rendered as HTML, archive formats with
active content.

**H8. Group-level restrictions must hold on every enforcement path.**
*Targets:* forking restrictions, invitation/member restrictions, IP
restrictions, push rules, protected branch/tag rules — each tested via web
UI, REST, and GraphQL. *Invariant:* "A policy set at group level must be
evaluated identically regardless of which client or API path performs the
action." *Why:* lower severity (medium/low) but the highest hit rate —
CVE-2025-3396, CVE-2025-4972/6168, CVE-2024-10925, CVE-2025-0307 all fit
this shape. Ideal differential-behavior sweep: set the restriction in UI,
attempt the action via API with a low-privilege role.

---

## Notes for the authenticated phase

- Requires: HackerOne account + `@wearehackerone.com`-aliased GitLab.com
  test accounts in researcher-owned namespaces (2 accounts minimum for
  cross-principal IDOR), plus a local GDK install for anything disruptive.
- Every report needs screenshots/video/logs of reproduction on the
  researcher's own instance or test namespace — build the evidence harness
  before testing, not after.
- Check the live Rewards tab for current bounty ranges before prioritizing;
  ranges above are researcher-documented, not from the official page.
- Re-verify scope the day testing starts — the policy page evolves
  (e.g., the Jan 2026 DoS update).
