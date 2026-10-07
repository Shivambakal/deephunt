# DEEPHUNT Swarm — Application Synthesis (agent #30)
2026-09-27. Sources: obs_app.jsonl agents 16–28 (roles: identity-flow, session-state,
authorization, object-ownership, role-transition, api-state, file-processing,
import-export, sharing-permission, search-filter, integration) + WORLD_MODEL.md.
Missing roles with NO observations: 24, 27, 29. Everything below is docs/OSINT-grade
until verified against the hunting environment.

## 1. Identity
- Users have a multi-flag lifecycle: active / suspended / deactivated / deleted /
  verified, plus internal flag, userTypeId, syncdirId. Deprovisioning is a pipeline
  (suspend → deactivate → delete), not a single delete. Note: CVE-2026-29092 showed
  EPG sessions could survive account disable pre-9.2.1 — "deactivated" ≠ "no access"
  was historically violable.
- Every identity auto-gets a root folder object at provisioning (syncdirId = "My Folder").
- Identity origins: local admin creation, invite-triggered self-provisioning (email
  entered must match invite address; optional sender activation code, CAPTCHA,
  email verification, mobile OTP), LDAP/AD sync, SCIM, SSO Just-In-Time
  provisioning (IdP-assigned user gets access even with no pre-existing Kiteworks
  account), bulk import tooling.
- External invitees default to "restricted user", time-bounded (SEC: 120-day validity).
- Identity is a hub: folders + devices (tracked, remote-wipeable, /devices/) +
  linked external repositories (SharePoint, Documentum via Enterprise Connect) +
  contacts / personal groups (/contacts/, /groups/).

## 2. Sessions
- Web UI session cookies vs API tokens are distinct credential types.
  API auth: Bearer api_key (server-to-server), OAuth 2.0 access tokens w/ optional
  refresh-token rotation, mutual TLS client certs, legacy HMAC-SHA1 signature flows.
- OAuth: 7 grant types (Authz Code, signature-based variants, User Credential /
  HTTP Basic, SAML 2.0 Assertion, JWT Assertion). Access-token and refresh-token
  lifetimes are PER-CUSTOM-APPLICATION (admin-configurable), not global. Signature
  auth codes valid 1 hour. Scopes are method/path wildcards (e.g. `*/files/*`).
- Session timeout is an admin-configured idle-disconnect policy (default unknown).
- "Remember this device" = persistent trusted-device token that skips 2FA on
  subsequent logins; admin-controlled whether allowed.
- 2FA: 8-digit email OTP, 5-min expiry; alternatives SMS, RADIUS, PIV/CAC.
- Failed logins: admin-set threshold → lockout + email notification, possible CAPTCHA.
- GAPS: no public docs on concurrent-session limits, session list/revoke UI,
  "log out other devices", or session invalidation timing on demotion/deactivation
  (agent #20's H5: demoted admin may keep a live privileged session).

## 3. Authorization — three independent layers
1. **User profiles** (feature/privilege bundles): users start with ZERO privileges;
   the profile is the single choke point. Mutation primitive is
   `assign_user_profile` (promotion/demotion; bulk variant has data-retention
   controls). `update_user` documents only non-privilege fields (name, password,
   suspended, verified, deactivated, active) — profile/adminRole not listed.
   Quirk: read-only profile tools (get_profile, list_profile_users,
   get_profile_eligibility) require Profiles CREATE scope (naming mismatch).
2. **Admin roles**: two-tier hierarchy — System Admin > Application Admin, plus
   Helpdesk/DLI/Compliance/CISO/MFT/security-analytics and custom delegated
   roles with configurable component scope. Invariant: only System Admins can
   designate Application Admins; self-promotion blocked (documented, enforcement
   unverified — per-endpoint check vs UI-only unknown). Documented guard:
   `create_user` strips admin role server-side. OPEN: whether SSO JIT, LDAP sync,
   bulk import, self-registration paths enforce the same strip (agent #20 H6).
3. **Folder roles**: Owner > Manager > Collaborator > Downloader > Uploader > Viewer
   (n=25 names Uploader after Downloader; n=18 mobile-guide order differs slightly
   — see contradictions). Deny-by-default, least-privilege; role-granting is an
   admin-controlled privilege, not a right.
- ABAC layer on top of RBAC: action privilege does NOT confer content access;
  classification-based restrictions can deny admins the content itself.
- External-user licensing boundary: internal vs external; external = Licensed
  (Collaborator/Manager/Owner, or can initiate email) vs Non-licensed
  (Viewer/Downloader/Uploader only). Upload+download in same folder ⇒ licensed —
  a capability change that should flip licensing state.
- Privilege-management endpoints: /profiles, /roles, /adminRoles, /ldapGroups, /admin.
  Historical bugs cluster here: CVE-2025-53939 (pre-9.1.0 shared-folder role
  input validation → privilege elevation), CVE-2026-23514 (8.8, 9.2.0/9.2.1
  authenticated access to unauthorized content).

## 4. Ownership & state
- Folder ownership is a named role (Owner), default = folder creator. Owner owns
  the storage quota. Admin-driven transfer path exists ONLY at deletion
  (reassignment wizard; "Delete All Folders Owned by the User and All Files Sent
  to Others"). OPEN: whether ownership can transfer user-to-user outside deletion;
  whether a Manager can promote self to Owner or demote the Owner.
- Deactivation preserves data (license still consumed until data reassigned);
  sole active admin and scheduled-job owners cannot be deactivated (safety invariant).
- Objects are soft-deleted: `deleted` → `permDeleted` flags; children listings
  filter via client-controlled `?deleted=false` (authorization on soft-deleted
  objects is a missable check).
- Mailbox/send model: sent objects are COPIES. Deleting a sent message does NOT
  delete the recipient's copy — revocation after send is impossible by design.
  Mailbox files expire (SEC: 30 days). Contrast: shared-folder revocation is
  immediate. The send-copy vs shared-reference boundary is a key seam.
- Same-name re-upload creates a NEW VERSION (not reject/rename). Version state:
  `replaceId`, dedicated new-version endpoint, version history server-side.
  OPEN: version enumerate/revert permissions; do old versions keep old ACLs;
  does `replaceId` accept arbitrary IDs.
- File-level sharing is independent of folder access; Collaborator role includes
  "send" (re-distribute) — a delegation chain whose depth limits are undocumented.
- Search results carry creator/userId metadata on every hit; there is NO
  server-side owner/creator filter (consumers filter client-side). Tenant-wide
  name search; content search is folder-scoped. Search spans connected external
  repositories "regardless of storage location" — external-ACL fidelity at search
  time is undocumented. Stated invariant: search must never return objects the
  searcher can't access (need-to-know).

## 5. File pipeline (upload → scan → encrypt → share)
- Two upload paths: simple multipart POST /rest/folders/{id}/actions/file
  (file ID returned in X-Accellion-Location header); chunked upload session —
  POST .../actions/initiateUpload → session ID in X-Accellion-Location
  (/rest/uploads/{id}) → chunk POSTs (200 per chunk, 201 + file ID on last) →
  session exposes userId, totalSize/totalChunks, uploadedSize/uploadedChunks,
  completeOk, error, clientCookie. DELETE /uploads/{id} aborts. Two workflows:
  declared totals (server validates content at end) vs SFTP-style lastChunk=1
  (NO content validation on final chunk — per docs). Sessions keyed by numeric ID.
- Post-upload processing is ASYNC: final-chunk 201 shows `"fingerprint":
  "Generating..."` — a window where the file is addressable (by ID) before
  scanning completes.
- Security pipeline: embedded AV is WithSecure Atlant (on-appliance, up to 16TB);
  AV cluster role, DLP (Forcepoint/Digital Guardian), ATP (Check Point
  SandBlast/Trellix), CDR (Forcepoint Zero Trust) via ICAP. Inbound docs may be
  CDR-sanitized and REPLACED before delivery; failing ATP files quarantined.
  Per-file AES-256-CTR unique keys + FIPS 140-2 disk encryption; TLS in transit.
  Program-accepted risk: AV bypass by mere rename — do not report that class.
  Historical CVEs cluster exactly here: pre-9.2.0 arbitrary upload (missing
  validation), CVE-2026-23636 (SDF dangerous-type upload by form manager).
- Size enforcement is policy-configurable: no per-file limit, 100GB folder
  upload (SEC), up to 16TB licensed. Chunked upload is a designed, supported flow.
- No idempotency documented anywhere: retried initiateUpload with the same name
  = new version; duplicates/duplicate sessions are plausible on client retry.
- API versioning is per-request (X-Accellion-Version, multiple versions served
  concurrently) — deprecated versions may carry weaker validation.

## 6. Workflows (MFT automation)
- Airflow-powered graphical workflow designer (per vendor marketing pages) drives
  scheduled/polled/event/manual file movement, auto-resuming failed transfers
  (even 16TB). ~2,000 connectors + declarative custom operators (custom-code
  surface inside authoring). Import sources: SFTP/FTPS/SMB/CIFS/AS2, S3, Azure
  Blob/Files, SharePoint, OneDrive, Google Drive, GCS, Box, Wasabi, Dropbox.
  Same destinations for export; workflows move sensitive data machine-to-machine
  with no per-transfer human review. Authoring gated by vendor-claimed role-based
  controls over capabilities and data access.
- ⚠ CONTRADICTION: agent #14 records vendor docs claiming a PROPRIETARY flow
  engine (Airflow lineage UNVERIFIED). Do not base hypotheses on Airflow lineage
  until confirmed.

## 7. Sharing & send flows
- Compose → To/Cc/Bcc recipients → Add Files → Send → recipient email with link
  → recipient authenticates → downloads. Policy engine checks at send time:
  DLP outbound scan (alert/log/block) + AHEP (see below).
- Share tiers (program's own validity bar): "Recipient Only" (bypass = in-scope
  finding) vs "anyone after authentication" (accepted risk — do NOT test).
- Link mechanics: double 128-bit MD5 secure-link tokens (unguessable);
  qualified links add admin-configurable lifespan. Per-send sender controls:
  auth-before-download toggle, who may download, link duration, download count,
  per-recipient unique watermarks (default), email body behind auth.
- CHALLENGE/RESPONSE (pre-download identity check, LDAP-linked) and RECIPIENT
  VALIDATION (blocks forwarded links) are ADMIN-CONFIGURABLE OPTIONS — may be
  OFF. Whether they're enforced on the hunting env is the testable seam.
- External recipient onboarding: click "Access Message" → enter SAME email as
  invited → set password → activation email → account. Identity proof = control
  of the recipient inbox (no out-of-band verification in default flow).
- Tracking: recipient email + access time + IP logged per download; attribution
  (watermarks, tracking) complements prevention.
- AHEP (Agent and Human Error Prevention, Data Policy Engine module, launched
  Aug 2026): analyzes signals AT COMPOSE TIME — recipient type/volume, identity
  match, attachment presence, domain validity. Pre-built policies: BCC/reply-all
  protection, send-to-self detection (personal-domain recipient + 4-dimension
  identity match + attachment). OPEN: suppressibility of warnings, API-driven
  sends coverage, MFT-transfer coverage.
- EPG mail stream: sees ALL inbound/outbound mail; policy (60+ actions, 50+
  conditions) on sender/recipient/content/classification/attributes. Trusts
  client-applied MIP sensitivity labels; parses S/MIME, OpenPGP, DKIM/DMARC.
  Inbound mail from arbitrary senders = untrusted input into the policy parser.

## 8. Integrations
- Identity: LDAP/AD (Base DN, Bind DN, login filters on uid/sAMAccountName/mail,
  attribute→profile/role mapping, LDAP Username Attribute for 2FA); SAML 2.0 SP
  on SimpleSAMLphp-style `/sp/module.php/saml/...` endpoint (inherits that
  stack's vuln history); SSO toggles include SP Entity ID (default
  `https://kiteworks.com` — shared/fixed across tenants per Oracle docs),
  signed AuthnRequests, IdP Entity ID, SSO Service URL, certificate paste,
  IP-range auto-redirect. RADIUS or email-OTP 2FA.
- Trust: directory/IdP drives BOTH auth AND role/profile assignment — LDAP
  injection (login username, /ldapGroups group-name input, attribute mapping)
  and assertion/JIT attribute handling are the program-focus boundaries.
- Content connectors: SharePoint, SMB/CIFS/DFS, Documentum, OpenText,
  Google Drive, Box, Dropbox, Salesforce, iManage, M365 — trust stored connector
  credentials and remote-ACL fidelity.
- Clients: iOS/Android/desktop (OAuth, remote wipe), Outlook/Office + Google
  Workspace plugins, SFTP client (remote server surfaced as web folders).
- New: Kiteworks MCP Server (9.5+, OAuth app, localhost:9999 callback) for AI
  clients (Claude Desktop/Code); AI Data Gateway for RAG. Official MCP tool
  surface mirrors the REST API (search, mail, users, admin) with scope tables.
- Audit/export paths: human-readable admin reports, SIEM/syslog export (Splunk
  app, CISO dashboard), automated compliance reporting, Legal Hold/eDiscovery
  preservation with chain of custody, end-user exportable audit trails
  (Track button on sent mail, Details tab on folders), Secure Web Forms
  (structured data import; submission export format unconfirmed).

## Contradictions between observers
1. **MFT engine lineage**: agent #23 asserts "Airflow-powered" (high confidence,
   citing kiteworks.com marketing). Agent #14 says vendor docs describe a
   proprietary flow engine — Airflow lineage UNVERIFIED, do not assume.
   → Treat Airflow as vendor-marketing claim only; no hypothesis may depend on it.
2. **Folder-role ordering**: n=25 lists Viewer/Downloader/Uploader/Collaborator/
   Manager/Owner; n=18's mobile-guide ladder puts Downloader < Uploader <
   Collaborator. Trivial naming vs real capability-order disagreement — the exact
   capability delta between Uploader and Downloader (esp. licensing boundary:
   upload+download in same folder ⇒ Licensed) needs a live check.
3. **AV scope**: n=22 says dedicated AV cluster role + ICAP integrations; n=14
   says embedded WithSecure Atlant is the on-appliance engine. Compatible
   (embedded + cluster), not a real contradiction — noted for completeness.
4. **Scope-naming mismatch** (n=20): read-only profile tools require Profiles
   CREATE scope; Admin READ scope grants assign_user_profile while Admin CREATE
   only grants create_user. The scope table itself looks organic/inconsistent —
   worth a live scope↔endpoint map, not a contradiction in observations.

## Gaps (what no observer established)
- Live state of the hunting env: session cookie names/flags, /login_config
  contents, enabled auth integrations, timeout values, whether recipient
  validation / challenge-response are ON — all unmeasured (env unreachable from
  sandbox; agent #5/#35).
- Session invalidation on demotion/deactivation/deletion; concurrent-session
  policy; session list/revoke UI (agent #17: nothing found in public docs).
- Version-object authorization (enumerate/revert, old-version ACLs, replaceId
  semantics); soft-deleted-object authorization (?deleted filter client-controlled).
- Owner-transfer mechanics outside admin deletion; deactivated-owner share
  semantics; Manager↔Owner promotion rules; "Shared with me" after sharer
  deletion.
- AHEP warning suppressibility and coverage (API sends, MFT); whether DLP/ATP
  verdicts gate the async "fingerprint Generating..." window (i.e., is the file
  downloadable/shareable before scan completes?).
- Exact SSO/JIT/LDAP-sync attribute→role mapping and whether create_user's
  admin-strip is enforced on all provisioning paths.
- Live scope↔endpoint enforcement map (docs vs server).
- Roles 24, 27, 29 produced no observations (unknown which topics they covered).

## Candidate high-value test seams (for experiment designers, NOT findings)
1. Recipient-Only enforcement: is recipient validation actually enforced on the
   hunting env's download endpoints (token replay from a different authenticated
   identity)? (program validity line)
2. Viewer→Downloader ladder jump on direct /rest/files/{id}/content access.
3. Upload version-overwrite authorization: same-name re-upload as a non-owner;
   version enumeration/revert permissions.
4. Async-scan window: addressability of file ID between 201 Created
   ("fingerprint: Generating...") and scan completion.
5. Profile-mapping-rule self-promotion via user-controlled attribute change;
   delegated-admin assign_user_profile outside component scope.
6. JIT/LDAP provisioning path admin-strip bypass (create_user strips; do the
   other paths?).
7. LDAP injection in search_users_ldap and /ldapGroups inputs (program focus).
8. Chunked-upload: lastChunk=1 no-validation workflow; session-ID access by
   another user; orphaned/terminated session behavior.

## Corrections / additions for WORLD_MODEL.md
- **Airflow lineage is disputed**: agent #23 asserts Airflow-powered MFT from
  vendor marketing; agent #14's correction (already in WORLD_MODEL.md) says
  vendor docs claim proprietary flow engine and Airflow is UNVERIFIED. The
  WORLD_MODEL.md entry is correct to carry the caution; #23's claim should be
  marked marketing-grade only.
- WORLD_MODEL.md "Confirmed facts" section: tech stack still UNDETECTED —
  /login_config hint (from #14) remains the best next passive probe (browser
  render needed; env currently unreachable).
- **Bounty-focus alignment**: WORLD_MODEL.md lists LDAP injection as focus;
  observations add that RCE bonus terms ($25k + applicable, $50k at CVSS 10.0)
  are already recorded — no change needed.
- New items worth appending: AHEP module (compose-time policy enforcement, Aug
  2026 — new bypass/misconfiguration surface); MCP server (9.5+) as a new
  documented API consumer with its own scope table and OAuth callback on
  localhost:9999; recipient-onboarding identity proof = inbox control only.
- WORLD_MODEL.md open question #2/#3/#5 (auth flows, file flows, LDAP/SSO points)
  are substantially answered at docs-grade by this synthesis; mark them
  "docs-answered, live-unverified".
- Note in world model: obs roles 24, 27, 29 produced nothing — either unassigned
  or failed silently; flag for the research director.

## 3-line summary
Kiteworks is a three-layer authorization system (zero-privilege user profiles,
two-tier admin roles with documented anti-self-promotion invariants, six-rung
folder roles) wrapped around a file pipeline of chunked upload sessions, async
security scanning, and per-file encryption, with identity federated from
LDAP/SAML/SSO-JIT and sharing governed by Recipient-Only tiers whose enforcement
toggles are admin-optional. The historically buggy seams — upload validation,
file-access authorization, role/privilege transitions — match the program's
focus areas, and the richest untested boundaries are recipient-validation
enforcement, the async-scan addressability window, version-overwrite
authorization, and whether the create_user admin-strip holds on JIT/LDAP
provisioning paths. Open questions remain on live env state (sessions, timeouts,
enforced toggles) because the hunting host was unreachable from the sandbox, and
agents for roles 24/27/29 produced no observations.
