# Security Invariants — Kiteworks hunting environment
Agent #96 (memory / security-invariant extractor), 2026-09-27.
Derived from WORLD_MODEL.md, obs_app.jsonl, obs_diff.jsonl. All sources are
docs-grade/passive-OSINT unless noted; invariants below state the application's
OWN claimed security contract. A violating observation = candidate finding
(worth independent verification, not a confirmed vuln on its own).

## Authentication / identity invariants

1. **A non-admin caller must never succeed on `/adminRoles` or privilege-mutating `/profiles` calls.**
   Source: admin guide via obs_app n18/n34 — "/adminRoles REST API requires authentication as an administrative user; only system administrators can designate users as administrators."
   Violation observed when: a low-privilege Bearer token gets 200 (not 403) on POST /rest/adminRoles/*, or on assign_user_profile / bulk_assign_profile.

2. **A user must never be able to promote themselves to system administrator.**
   Source: admin guide (obs_app n18) — "Users cannot promote themselves to system administrators."
   Violation observed when: any self-directed call (profile edit, role edit, mass assignment, SSO/JIT claim) results in the caller holding system-admin scope.

3. **Server-side must strip/ignore admin roles on `create_user`; the guard must hold on every provisioning path.**
   Source: MCP DEPLOYMENT_GUIDE (obs_app n20) — "create_user cannot create administrators in any case, because the Kiteworks API ignores an admin role on that endpoint." World model agent-20 note: unverified for SSO JIT and LDAP sync paths.
   Violation observed when: a user created via REST with an adminRole parameter, or provisioned via SSO JIT / LDAP sync with admin attributes, ends up with admin role.

4. **Only system admins may create application admins (system admin > application admin hierarchy).**
   Source: admin guide (obs_app n18/n20).
   Violation observed when: an application admin or delegated admin successfully grants admin roles to another user.

5. **A delegated admin must never be able to expand their own role's component scope (admin role CRUD must not permit self-escalation).**
   Source: Defence Standard 05-138 guide via obs_app n20 — delegated admin roles with configurable component scope; self-edit guard undocumented.
   Violation observed when: a delegated admin adds privileged components to their own role definition.

6. **`update_user` must never change profile or adminRole fields (mass-assignment guard).**
   Source: MCP docs (obs_app n20) — update_user mutable fields are name, password, suspended, verified, deactivated, active; profile/adminRole must go through assign_user_profile.
   Violation observed when: a user-update request carrying a profile/adminRole parameter changes the target's profile.

7. **Demotion must promptly revoke the subject's privileged sessions/tokens.**
   Source: CVE-2026-29092 precedent (EPG sessions survived account disable pre-9.2.1, obs_app n19/n38) — establishes the class; current expected behavior is prompt revocation.
   Violation observed when: a demoted/deactivated admin's session token still succeeds on admin endpoints after the state change.

8. **Deactivated/suspended users must never perform authenticated actions (folder access, sends, downloads).**
   Source: obs_app n16/n19 — deprovisioning pipeline (suspend→deactivate→delete); deactivation removes access.
   Violation observed when: a deactivated user's existing session or token completes any authenticated operation.

9. **The sole active admin must not be deactivatable; users assigned to scheduled jobs must not be deactivatable.**
   Source: user-management docs (obs_app n19) — ownership-safety invariant.
   Violation observed when: API accepts deactivation of the sole active admin or a job-assigned user.

10. **LDAP injection must never alter directory query semantics: user-controlled input (login username, group names, LDAP search text) must never change which directory objects are matched.**
    Source: program focus area (WORLD_MODEL bounty focus); input-flow map obs_app n28.
    Violation observed when: metacharacters in search_users_ldap / login fields change the returned directory result set vs. a benign baseline.

11. **IdP assertion attributes must never grant more than the configured provisioning mapping allows (JIT/LDAP sync must apply the same admin-strip as create_user).**
    Source: Oracle IDCS guide (obs_app n28) — JIT provisioning driven by assertion attributes; agent-20 open question.
    Violation observed when: IdP-supplied group/claim produces a privileged profile or admin role at JIT/LDAP provisioning.

## File / share confidentiality invariants

12. **A "Recipient Only" share must never be downloadable by anyone who is not a named recipient, and no file must be retrievable without authentication (unless explicitly configured "anyone after authentication" — which is accepted risk, not a finding).**
    Source: YesWeHack program page (obs_app n25) — the program's own validity line: "you must be able to bypass 'Recipient Only' or [access] a file without being authenticated."
    Violation observed when: an authenticated non-recipient (or an unauthenticated request) downloads content from a Recipient-Only share link or /rest/files/{id}/content.

13. **A user with the Viewer role must never obtain a direct file download (only Online Viewer rendered view).**
    Source: obs_app n33/n25 — "Viewers can view documents within the browser or Mobile App without being granted permission to download them."
    Violation observed when: a Viewer-role identity fetches the raw file bytes via any endpoint (REST content URL, secure link, WOPI token).

14. **An Uploader must never see other users' files in the folder (upload-only + own files).**
    Source: RFP role definitions (obs_app n25) — "Uploader: upload and manage own files, cannot see others' files."
    Violation observed when: an Uploader lists or opens files uploaded by other users.

15. **An expired share link must never serve the file; expired send-links delete files from the server.**
    Source: Accellion/Kiteworks security FAQ + Getting Started Guide (obs_app n25) — qualified links "block access to the file after its expiration"; "After the link expires, the files are deleted from the server."
    Violation observed when: a download request with an expired link token returns file content.

16. **Download-count limits on secure links must be enforced server-side.**
    Source: security overview (obs_app n25) — senders control "how many downloads the secure link will allow."
    Violation observed when: downloads beyond the configured count still succeed.

17. **A forwarded secure link must never work for someone outside the original recipient list when recipient validation / challenge-response is enabled.**
    Source: accellionsecurityfaq.pdf (obs_app n25) — RECIPIENT VALIDATION "prevents forwarding links."
    Violation observed when: with validation enabled, a different authenticated identity replays the link token and downloads.

18. **Sender-side deletion must not revoke the recipient's copy (lifecycle asymmetry — an invariant for reasoning, not a bug to report).**
    Source: SEC guide (obs_app n19/n22) — "If you delete a sent message, it will not delete the message for the recipient."
    Violation of the INVERSE: a design assumption to encode — never assume delete = revoke in exploit chains; do not report as a finding.

## Authorization / role-ladder invariants

19. **Folder membership/role management (add/remove users, assign roles) must succeed only for Owner/Manager callers.**
    Source: obs_app n33 — "Only Owners and Managers can manage folder users/roles" (POST /rest/folders/{id}/members).
    Violation observed when: a Collaborator/Downloader/Uploader/Viewer (or non-member) successfully calls the members endpoint to add/change/remove roles. (Historical precedent: CVE-2025-53939 — same class, fixed 9.1.0; look for variants, not the same bug.)

20. **Folder Details/activity log must be visible only to Owner/Manager/Collaborator.**
    Source: Packaging doc (obs_app n33/n34).
    Violation observed when: a Downloader/Uploader/Viewer retrieves the folder activity/tracking log.

21. **Secure link generation must be limited to Owner/Manager/Collaborator; desktop-sync toggling to Manager only.**
    Source: obs_app n33.
    Violation observed when: a Viewer/Downloader creates a shareable secure link, or a non-Manager toggles folder desktop sync.

22. **Only the email-package sender (owner) may access the Track report; recipients must never.**
    Source: Packaging doc (obs_app n33).
    Violation observed when: a recipient retrieves the Track view / exportable audit report on a package they received.

23. **Action privilege must never confer content access when ABAC classification forbids it.**
    Source: insider-threats page (obs_app n18) — "action privilege does not confer content access."
    Violation observed when: an admin with manage-action rights but no content clearance reads file content via an endpoint that skipped the ABAC check.

24. **Least-privilege defaults: a fresh user has zero privileges until a profile is assigned; data access only by invitation.**
    Source: Defence Standard guide (obs_app n34/n20).
    Violation observed when: a newly provisioned user (no profile) can use features or access data without an invitation/profile assignment.

25. **Administrators must never reach end-user content outside their ABAC scope, nor log into the OS / access data directly.**
    Source: company/product overview (obs_app n18) — "Administrators can't log into the operating system or access data."
    Violation observed when: an admin identity reads user file content outside its delegated scope, or reaches OS-level access.

26. **Search results must never include objects (or their metadata/snippets) the searcher has no access to — including content indexed from connected external repositories.**
    Source: VDR page (obs_app n26) — VDRs "expose virtual data room files and folders only to parties with a need to know" while offering full-text search; cross-repository search doc.
    Violation observed when: two accounts with different access run identical searches and the lower-privilege one sees objects/snippets/creator metadata it cannot open.

27. **The shared-mailbox filter in mail listing must never cross mailbox membership.**
    Source: MCP docs (obs_app n26) — the 'shared mailbox' filter is the interesting boundary.
    Violation observed when: a non-member enumerates messages via the shared-mailbox filter.

28. **Non-licensed external users must never gain licensed capabilities (edit/manage / upload+download combined) without the license state changing.**
    Source: Packaging/Licensing doc (obs_app n18/n33).
    Violation observed when: a non-licensed external user performs Collaborator+ actions while still classified non-licensed.

## Data-integrity / upload / processing invariants

29. **AV/ATP/CDR verdicts must never be bypassable for inbound files (excluding the accepted-risk rename bypass).**
    Source: Security white paper (obs_app n22); program accepts AV-bypass-by-rename as known risk — do NOT report rename-only bypasses.
    Violation observed when: a malicious payload reaches a recipient/download without the configured AV/ATP/CDR scan applying (non-rename vector), or the file is addressable/downloadable while fingerprint shows "Generating..." before scan completes.

30. **DLP outbound policy must never be bypassable: a blocked transfer must not leave the appliance.**
    Source: white paper (obs_app n22) — DLP "can alert, log, and/or block transfers based on the DLP results."
    Violation observed when: content matching a block policy is exfiltrated (mail send, MFT export, share) despite the policy.

31. **Chunked upload sessions must be caller-scoped: one user must never hijack, read, or complete another user's upload session.**
    Source: API guide upload-session model (obs_app n21) — session state keyed by numeric ID with userId field; DELETE /uploads/{id} terminates.
    Violation observed when: user B GETs/DELETEs/completes a session ID created by user A.

32. **The SFTP-style lastChunk=1 path must not skip content validation while the declared-total path enforces it (no validation asymmetry between upload workflows).**
    Source: API guide (obs_app n21) — declared workflow "server validates content at end" vs SFTP-style "NO content validation on final chunk."
    Violation observed when: hostile content passes through the lastChunk path that the declared path rejects.

33. **Version-upload authorization: creating a new version of a file must require the same write rights as editing it (no version-overwrite of files the caller cannot edit).**
    Source: API semantics (obs_app n21/n22) — same-name re-upload creates a NEW VERSION.
    Violation observed when: a user without edit rights on a file creates a new version of it (via /files/{file_id}/actions/initiateUpload or name-collision path), or enumerates/reverts versions they should not see.

34. **Soft-deleted objects (deleted=true, not yet permDeleted) must remain subject to the same authorization checks as live objects.**
    Source: API guide two-stage delete (obs_app n21) — listings filterable via ?deleted=false (client-controlled).
    Violation observed when: a non-authorized caller retrieves soft-deleted files/folders by toggling the deleted filter, or restore/permDelete actions succeed for non-owners.

35. **File locks (SafeEDIT / locked flag) must block conflicting writes; revocation mid-session must end the session immediately.**
    Source: DRM page + API guide locked flag (obs_app n41).
    Violation observed when: a second writer commits changes during another session's lock, or a revoked user continues a SafeEDIT session.

## Session / token invariants

36. **OAuth/API tokens and web sessions must be distinct, scope-bound credential types; a token must never exceed its granted scope set.**
    Source: API guide scopes (obs_app n17/n21) — scope format method/path wildcards; per-app lifetimes.
    Violation observed when: a token scoped to */files/* performs admin actions (e.g. */admin/*), or scope checks differ between API versions (client-controlled X-Accellion-Version).

37. **Expired tokens (access past lifetime, refresh disabled/expired) must never authenticate.**
    Source: API guide per-app lifetimes (obs_app n21).
    Violation observed when: a request with an expired access token succeeds.

38. **The 2FA OTP (8-digit, 5-minute expiry) must be single-attempt-bounded and unguessable; "Remember this device" trust must be revocable and admin-controllable.**
    Source: SEC guide + CMMC mapping (obs_app n17).
    Violation observed when: OTP accepts brute-force attempts without lockout/CAPTCHA, expired OTPs validate, or a trusted-device token survives admin revocation.

## Notification / disclosure invariants

39. **Tracking-access grants must never expose the Bcc recipient list to trackers (or: must expose it only per documented design).**
    Source: Web User Guide v9.1.0 pp.39-41 (obs_app n27) — trackers see "the FULL recipient list INCLUDING Bcc recipients."
    Note: this is documented behavior, so the invariant is documentation-vs-expectation: verify whether the program treats Bcc exposure to non-recipient trackers as intended. Violation observed when: a tracker who was never a recipient learns Bcc addresses the sender intended to hide (privacy-boundary question for the human operator, not an automatic bug).

40. **Protected message bodies ("recipients must sign in") must never leak body content or attachment lists to unauthenticated viewers; the subject line is documented as visible (accepted).**
    Source: Web User Guide Table 4 (obs_app n27).
    Violation observed when: an unauthenticated fetch returns body text or attachment list on a protected message (subject-line visibility is documented, not a violation).

## Cross-cutting

41. **Client-controlled versioning (X-Accellion-Version) must never weaken authorization: deprecated versions must enforce the same checks as current.**
    Source: API guide (obs_app n21) — "several API versions, all of which are supported."
    Violation observed when: the same operation is denied on v28 but allowed on an older pinned version.

42. **Numeric user IDs must not be enumerable into other users' data (accepted risk for restricted/recipient messaging, not for content access).**
    Source: program Known Issues (obs_app n44) — "Listing internal users by ID... (ID will be replaced by UUID in the next release.)"
    Violation observed when: sequential user IDs enable access to another user's files/messages beyond the accepted-risk listing.

---
Summary: 42 invariants extracted, docs-grade, covering auth/identity (1–11), file/share confidentiality (12–18), role ladders (19–28), upload/processing integrity (29–35), sessions/tokens (36–38), notifications (39–40), cross-cutting (41–42).
Program-excluded classes respected: race conditions, user enumeration, self-XSS, rename-only AV bypass, "anyone after authentication" disclosure, rate limits — none of the invariants above depend on those classes.
