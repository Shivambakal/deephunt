# Agent #45 — Differential Synthesis (agents 31–44)
Date: 2026-09-27. Synthesizer view only; no new research conducted.

## Coverage note
- Observed agents: 32 (user-vs-user), 33 (owner-vs-nonowner), 34 (role-vs-role), 35 (http-method), 36 (header-env), 37 (api-version), 38 (old-vs-new), 40 (timing), 41 (concurrent), 42 (encoding-context), 43 (mobile-vs-web), 44 (staging-vs-prod).
- Agents 31 and 39 produced no records in obs_diff.jsonl. Agents 35, 36, 40, 42 attempted live probes; ALL failed — the sandbox egress cannot reach the hunting host (proxy CONNECT to ywh-kw-public.bounty.kiteworks.dev:443 times out; sandbox DNS returns 198.18.92.34, an RFC 2544 blackhole address). Every live-path differential (timing, method, header, encoding) is therefore UNTESTED from here, not negative.

## Top 10 differences by information value

### 1. Current build uses numeric sequential user IDs; next release moves to UUIDs — with a live accepted-risk boundary around who can message whom
Agent 44 (high confidence, from the live program page Known Issues/Accepted risks): "Listing internal users by ID. Only restricted users and recipient should not be able to send a message to other users. (ID will be replaced by UUID in the next release.)"
Why it matters: the CURRENT hunting build exposes predictable user IDs, and the program itself names a messaging boundary (restricted users / recipients → other users) that is only "accepted risk" per their wording. Two testable hypotheses: (a) internal-user ID enumeration is trivial on the current build; (b) the restricted-user messaging boundary is actually enforced — any bypass is the highest-information test in this batch, because the vendor itself flagged the seam. NOTE: user enumeration is program-excluded as a *finding class*, but a messaging-authorization bypass is a different, in-scope seam.

### 2. Folder members endpoint: the CVE-2025-53939 seam is the documented home of broken owner-checks
Agent 33 + 38: pre-9.1.0, improper input validation when managing shared-folder roles could elevate another user's share permissions (patched 9.1.0). Hunting env is 9.5.1-claimed, so the specific bug is dead, but the seam is now mapped: POST /rest/folders/{id}/members with roleId/userId payloads, Owner/Manager-only membership management. Testable hypothesis: any residual input-validation weakness on the members surface that lets a non-Owner/non-Manager add users or escalate roles (e.g., type-juggling on roleId, negative values, group-membership confusion). Highest-value known-class probe in the set.

### 3. API version is header-pinned (X-Accellion-Version, v8 → v28) with no deprecation schedule and no per-version changelog
Agent 37 (high/medium): all endpoints share /rest/... paths; behavior is pinned by the X-Accellion-Version header; docs say "several versions of the API, all of which are supported" with no sunset policy; no published delta between any of the ~20 version bumps. Testable hypothesis: sending a request with an old X-Accellion-Version value (e.g. 8, 10, 15) hits older validation/enforcement code paths — a classic differential primitive. If the hunting env honors low version values, every newer check is worth re-testing under the old pin. Strong experiment candidate once a reachable network path exists.

### 4. Owner-vs-nonowner checklist: 7 concrete observable seams (agent 33, high confidence)
1. Non-owner/non-Manager calling POST /rest/folders/{id}/members to add/change roles
2. Folder Details/activity log returned to Downloader/Uploader/Viewer (must be Owner/Manager/Collaborator-only)
3. Secure link creation by a Viewer/Downloader (must be Owner/Manager/Collaborator-only)
4. Viewer obtaining a direct file download instead of Online-Viewer render
5. Downloader uploading/editing files (Collaborator+-only)
6. Email recipient accessing the sender-only Track report on a received package
7. Non-Manager toggling folder desktop sync; Viewer/Uploader subscribing to notifications
These are *observable differences*, not vuln claims — they form the test battery for any owner-check hypothesis. Highest-density test plan in the batch.

### 5. Secure Data Forms 9.3.0 ownership-check boundary: a whole IDOR family was just closed
Agent 38 (medium): pre-9.3.0, authenticated users could tamper with other users' form approval flows (CVE-2026-23638), modify others' form resources and their permissions (CVE-2026-24753/24756, 24755), and read others' resource metadata (CVE-2026-24761) — all fixed by 9.3.0 ownership checks. The boundary was *just* drawn. Testable hypothesis: adjacent form/data endpoints in the current build may have the same missing-ownership-check pattern on resource types not covered by those CVEs. Also unmapped: the Kiteworks form-owner vs submitter/reviewer model has no public docs (agent 33 gap note) — that gap is itself a research target.

### 6. Mobile-vs-web client enforcement delta: Viewer can't download on web, but mobile has Open-In, offline access, and a manager-push-to-device flow
Agent 43 (medium): the mobile datasheet documents Open-In to whitelisted helper apps, offline-access file pull, and admin manager-push of files to devices; the web client's Viewer is deliberately no-download (Online Viewer render only). Testable hypothesis: a Viewer-role user who cannot download via web may obtain the file through a mobile API path (Open-In/offline flows) if the backend does not enforce the no-download constraint uniformly across clients. Classic client-trust differential. (Requires in-app/API testing from an eligible network, not the sandbox.)

### 7. Legacy OAuth grant types: docs narrowed from 7 grants to 2 named flows with no deprecation statement
Agent 37 (low/medium): old API guide lists Authorization Code, Signature-based Authorization Code, Signature-based Access, User Credential, User Credential (HTTP Basic), SAML 2.0 Assertion, JWT Assertion; current portal documents only OAuth 2.0 Authorization Code and JWT Assertion. Testable hypothesis: legacy grants (esp. User Credential / Signature-based Access) may still be accepted by the hunting env — if live, they bypass the narrowing. Related seam from the world model: MCP Server (9.5+, localhost:9999 callback) is a new OAuth client surface.

### 8. 9.2.x access-control boundary: Core let authenticated users access unauthorized content (fixed 9.2.2); EPG let blocked users keep sessions after account disable (fixed 9.2.1)
Agent 38 (medium): CVE-2026-23514 (Core 8.8 High), CVE-2026-29092 (EPG blocked-user session survival), CVE-2026-23635/23636 (Forms credential-transport / manager-side dangerous upload, fixed 9.2.1). The fixes are claimed for the current build, but these are the *recent* boundaries — testable hypothesis: variant paths to the same classes (e.g., stale-session invalidation, upload validation on non-manager roles) are the most likely residual deltas. Note the world model already flags session survival after demotion as a manual-test candidate (H5) — this corroborates it.

### 9. Licensed/non-licensed user state flips on folder-role assignment; profile mapping rules auto-assign by username/email match
Agent 32 (low) + world model (agent 20, H2/H4): an External User becomes Licensed when granted Collaborator+ folder role (edit+download+upload+manage) or email-initiation; profile mapping rules auto-assign profiles by username/email match. Testable hypothesis: self-promotion paths via profile-rule manipulation or update_user mass assignment on the current build. Enforcement point unverified; SSO JIT / LDAP sync paths may not strip admin roles the way create_user does (agent 20's documented guard only covers create_user).

### 10. Same filename rendered in three contexts (web inbox UI, notification email, download flow) — encoding differential unobserved
Agent 42 (low, docs-grade): SEC user guides show filenames rendered in the HTML inbox, email attachment links, and the authenticated download flow. Whether each context encodes identically is UNOBSERVED (live site unreachable from sandbox). Testable hypothesis once reachable: filename-context XSS (stored via upload, reflected via share-email link, header-injection via Content-Disposition) — but note the bounty requires XSS with REAL impact, and self-XSS is program-excluded. Medium-low priority; flag for a reachable-network agent.

## Explained differences (by design — low research value)
- Internal vs External user licensing tiers; folder-role ladder (Owner/Manager/Collaborator vs Downloader/Uploader/Viewer); three-tier admin model (system > application > end user); profile-driven feature enablement vs invitation-driven data access: all documented by design (agents 32, 34).
- Admin Console (all activity) vs web app (per-folder activity) visibility: by design (agent 34).
- Mobile/web sharing one REST backend; OAuth authorize m=1 mobile page variant: by design (agent 43).
- Single-tenant hardened-appliance model (no shared staging tier): by design, per program page (agent 44). The plural "hunting environments" on the program page vs one listed URL is a wording artifact, not a finding.
- SafeEDIT lock-then-version-on-commit; same-name upload creates a new version; no documented optimistic-concurrency tokens: documented design (agent 41). Any race-condition angle is program-EXCLUDED — do not pursue timing races as findings.
- Sandbox unreachability, DNS blackhole artifact (198.18.92.34), crt.sh failure: infrastructure/methodology, not target behavior (agents 35, 36, 40, 42).

## Information gaps (not differences, but blocking)
- No public 9.4/9.5/9.5.1 feature changelog (agent 38, high) — current-build behavior can only be probed live.
- No public Kiteworks-specific Secure Data Forms owner/submitter model docs (agent 33, low).
- No per-version API changelog v8→v28 (agent 37, medium).
- All live-path work (timing, method, header, encoding) needs an eligible agent with working egress (agents 35, 36, 40, 42).

## Corrections/updates for WORLD_MODEL.md (listed, not applied — do not edit)
1. DNS: agent 42 reports sandbox resolver returns 198.18.92.34 (RFC 2544 blackhole) for the hunting host vs the world model's A=3.0.1.193 — this is a sandbox-egress artifact, not a target change; consider annotating both with the caveat.
2. Reachability: agents 35/36/40/42 independently corroborate the agent-35 correction — host unreachable from sandbox. This is now 5-agent corroborated; standing instruction for all direct-request agents: do not burn request budget on connectivity, route live work to an eligible network.
3. Add program-page Known Issue (agent 44): current build uses numeric internal user IDs → UUIDs in next release; restricted users / recipients messaging boundary. This is live-program-grade, not docs-grade.
4. Add owner-check seam checklist (agent 33, 7 points) as the standard broken-access test battery for folder/file/mail surfaces.
5. Add API versioning primitive: X-Accellion-Version header pinning, Core spec v28 / Pub-Sub v1, no deprecation schedule (agent 37).
6. Add version-boundary CVE families for residual testing: CVE-2025-53939 (folder role input validation), CVE-2026-23638/24753-24761 (Forms IDORs), CVE-2026-23514 (Core authz), CVE-2026-29092 (EPG session survival) — all patched per public records; value is as variant-test targets, not live claims.
7. Add mobile client surface (agent 43): Open-In whitelisted apps, offline access/manager push, AES-256 secure container with remote wipe — client-dependent enforcement differential.
8. Add AS2 B2B surface: Kiteworks Secure MFT Server 9.4 earned Drummond AS2 certification (agent 38) — new externally-reachable protocol surface if present on hunting env.

## Three-line summary
Most valuable: the program's own known-issue (numeric user IDs → UUID next release) names a live messaging-authorization boundary to test, and the CVE-2025-53939 folder-members seam plus the just-closed Secure Data Forms IDOR family give three concrete, testable access-control hypotheses. Highest-information experiment: pin old X-Accellion-Version header values and re-run owner-check tests — version-pinned endpoints may skip newer enforcement. All live-path differentials (timing/method/header/encoding) are untested, not negative: five agents independently confirm the sandbox cannot reach the host, so direct-request work must move to an eligible network.
