# DEEPHUNT Swarm — Hypothesis Pool Synthesis (Agent #80)

Date: 2026-09-27
Target: `https://ywh-kw-public.bounty.kiteworks.dev` (Kiteworks YesWeHack, passive-only per policy)
Input: `hyp_known.jsonl` (108 total across both files: 72 known-class + 36 novel-class)
Job: deduplicate → rank by (1) falsifiability, (2) test information value, (3) program eligibility, (4) target fit → 20 experiment-ready hypotheses with exact confirm/kill tests.

## Deduplication log (merged clusters)

| Cluster | Merged from | Kept as |
|---|---|---|
| Folder/file member role management | #55-BFLA3 (Manager→Owner), #57-H1 (roleId not clamped), #54-BOLA-2 (non-owner member update), #56-invite-role | H1: "Member role grant lacks privilege clamping" |
| Privilege assignment to users | #55-/adminRoles, #55-/profiles, #57-H2 (guarded attrs on PUT /rest/users/{id}), #56-profile-role-param | H2: "Admin/profile grant reachable by non-admin" |
| Provisioning-path strip gaps | #76-H-PRCHAIN-2, #77-create_user-strip-bypass, #77-zero-privilege-fallback | H3: "JIT/LDAP provisioning skips admin-strip and zero-privilege default" |
| Direct content / viewer bypass | #53-H2 (viewer download bypass), #54-BOLA-4 (content keyed on bare ID) | H5: "Direct byte endpoints skip role/relationship checks" |
| Version-object authz | #53-H1 (initiateUpload-version on another's file_id), #54-BOLA-3 (promote by viewer) | H6: "Version-object actions skip per-object write checks" |
| Recipient Only bypass | #53-H4 (token replay by non-recipient), #58-auth#4 (self-registration without inbox control) | H7: "'Recipient Only' readable by non-recipient" |
| Link expiry enforcement | #66-expired-link-alternate-path, #60-JWT#3 (qualified-link expiry), #72-dormant-desync, #73-share-snapshot-LDAP | H8: "Share-link expiry/exhaustion/policy-change not enforced on all paths" |
| Auxiliary-object BOLA | #54-BOLA-1 (comments), #53-H3 (activity log / track report ID swap) | H9: "Nested-object endpoints skip parent permission checks" |
| LDAP injection | #47-login-filter, #69-multi-entry-first-match | H10: "Login username concatenated into LDAP filter (multi-entry → first-match bind)" |
| CSRF | #51-multipart, #51-SameSite-GET, #51-pre-auth | H11: "State-changing endpoints accept cookie-only cross-site requests" |
| Token revocation | #60-JWT#4 (tokens survive disable/pw-change), #70-revoked-tokens-valid, #69-device-binding | H17: "Token classes survive revocation lifecycle events" |
| MCP localhost OAuth | #70-mcp-intercept, #73-mcp→RAG (duplicate) | H18: "MCP localhost:9999 callback interceptable on shared hosts" |
| Preview-pipeline injection | #61-preview-SSRF/XXE, #63-XXE-preview-XFA | folded into H20 test variants |
| ICAP verdict gaps | #68-AV-vs-ICAP-mismatch, #72-delegated-evidence, #79-fail-open, #73-version-inherits-verdict | kept as follow-up wave (see below) |
| LDAP group endpoints | #47-/ldapGroups, #47-autocomplete, #47-recipient-validation | sub-variants of H10, follow-up |

## Ranking method

Score = falsifiability × information value × program eligibility × target fit.
Program rules applied: privilege/role escalation, LDAP injection, and real-impact authz flaws are IN; user enumeration, race conditions, rate limits, self-XSS, AV-bypass-by-rename, "anyone after authentication" disclosure, and generic best-practice issues without impact are OUT. Every test below assumes: ResearchSession workflow, two consenting test identities (A/B) where cross-user effect is needed, synthetic data only, ≤10 spaced requests, UA suffix `-public-yeswehack`, no brute force / no DoS / no real-user data.

---

## Top 20 hypotheses → controlled experiments

### H1. Member role grant lacks privilege clamping (privilege escalation)
**Detail:** POST /rest/folders/{id}/members binds roleId without clamping to inviter's role; PUT /rest/files/{id}/members/{uid} lets non-owners change roles; folder Managers may promote self to Owner (CVE-2025-53939 class).
**Exact test:** (a) B (Uploader/Downloader on folder F) POSTs members with userId of controlled identity C and roleId=Owner enum (from GET /rest/roles); (b) B (Viewer on file) PUTs its own member record to editor; (c) Manager token updates its own folder role to Owner.
**Confirm:** GET members shows elevated role effective on subsequent owner-only action.
**Kill:** All attempts return 403 or are clamped to ≤ caller's role, verified in members listing.

### H2. Admin/profile grant reachable by non-admin token (vertical escalation)
**Detail:** /adminRoles grant, privilege-mutating /profiles writes, or guarded attrs (admin flag, userType) on PUT /rest/users/{id} enforce only authentication.
**Exact test:** Low-privilege token calls documented /adminRoles grant for self and /profiles privilege mutation; PUT /rest/users/{id} (own record) with admin/system-role field carried.
**Confirm:** 2xx and /rest/users/me shows admin role / privilege change effective.
**Kill:** 401/403 on all grant verbs; unknown fields stripped or 400; no effective change.

### H3. JIT/LDAP provisioning skips admin-strip and zero-privilege default
**Detail:** create_user strips admin roles, but SSO JIT and LDAP/AD sync construct records from IdP/directory attributes without re-applying the strip or the "zero privileges until profile assigned" invariant.
**Exact test:** Provision test accounts via SSO JIT and LDAP sync carrying a privileged mapped attribute, with no matching default profile.
**Confirm:** Account lands with admin role or a default profile granting folder/share rights.
**Kill:** All three paths (create_user, JIT, LDAP sync) land the account at zero privileges / strip admin claims identically.

### H4. Self-edit attribute + profile mapping rule = auto-promotion
**Detail:** update_user permits changing a self-editable attribute (department/title/email-alias) that an admin profile-mapping rule matches to auto-assign a privileged profile.
**Exact test:** Change a rule-matched attribute on own low-privilege account; open a fresh session; check effective profile/privileges.
**Confirm:** Privileged profile assigned with no admin action.
**Kill:** Profile unchanged across fresh session; or rule-matched attributes not self-editable.

### H5. Direct byte endpoints skip role/relationship checks
**Detail:** GET /rest/files/{id}/content checks auth + folder membership but not Viewer-vs-Downloader split (Viewer gets raw bytes); bare-ID lookup may fail open on stale/edge memberships.
**Exact test:** B (Viewer-only on shared folder, file_id learned from its own search) GETs /rest/files/{id}/content; separately request content for another user's file_id with no shared relationship (numeric neighbor).
**Confirm:** 200 with file bytes in either case outside the documented sharing model.
**Kill:** 403/404 consistently; Viewer gets render-only or denial on the byte path.

### H6. Version-object actions skip per-object write checks
**Detail:** POST /rest/files/{file_id}/actions/initiateUpload (new version) verifies folder membership, not edit-grant on that file — a Downloader/Viewer can force a new version onto another's file; version promote action lacks write check.
**Exact test:** B (Downloader, no edit) initiates version upload on A's file_id with lastChunk block; B (Viewer) calls versions/{vid}/actions/promote.
**Confirm:** New version attributable to B appears; promote succeeds.
**Kill:** 403 for non-edit callers on both; success only for Collaborator/Manager+.

### H7. "Recipient Only" readable by non-recipient
**Detail:** Download endpoint validates the double-128-bit-MD5 token + expiry/count but not caller identity vs recipient list (recipient validation is a configurable option); or the recipient self-registration flow doesn't require inbox control.
**Exact test:** A creates Recipient-Only share addressed to a controlled identity; B (authenticated, never a recipient) downloads via the token URL; separately, attempt recipient self-registration without clicking the inbox activation.
**Confirm:** B receives file bytes, or registration completes without inbox proof.
**Kill:** B rejected (403/login-wall); activation is single-use, unguessable, address-bound, mandatory.

### H8. Share-link expiry/exhaustion/policy-change not enforced on all paths
**Detail:** Expiry/download-budget enforcement may live in the share-page controller while alternate paths (direct download URL, preview/thumbnail, API download) check only token validity; policy may be snapshotted at issuance.
**Exact test:** Create link with max-downloads=1 and ~1-minute expiry (owned accounts); after 1 download / after expiry, request file via share page, direct download URL, preview/thumbnail endpoint, API download.
**Confirm:** Any path returns 200 bytes after expiry/exhaustion.
**Kill:** All paths uniformly deny (403/expired) and file is unrecoverable.

### H9. Nested-object endpoints skip parent permission checks
**Detail:** GET/PUT/DELETE /rest/comments/{id} validate comment existence, not caller's access to the parent file; folder activity log / sent-mail Track endpoints authorize on numeric ID without per-object role check (Details tab is documented Owner/Manager/Collaborator-only).
**Exact test:** B (no access to file X) GETs /rest/comments/{comment_id} harvested from a shared file; B (Downloader on folder F) requests activity log for folder G / Track report for package Q via ID swap.
**Confirm:** 200 with content including other users' emails/timestamps/IPs.
**Kill:** 403/404 unless caller holds the required parent-object role.

### H10. Login username concatenated into LDAP filter (multi-entry → first-match bind)
**Detail:** Login username is interpolated into the LDAP search filter unescaped; a crafted filter returning multiple entries may cause the app to bind as the FIRST match (potentially privileged) with the attacker's password.
**Exact test:** Submit metacharacter usernames (`*`, `*)(uid=*))(|(uid=*`) vs benign invalid usernames of equal length across trials; compare error text, status code, latency. (Single careful probes; no enumeration loops — enumeration alone is program-excluded, only a semantics-changing filter effect counts.)
**Confirm:** Reproducible differential correlated with filter semantics (wildcard effect, multi-entry behavior, LDAP error surfacing).
**Kill:** Identical response class across trials; input treated as literal (escaped).

### H11. State-changing endpoints accept cookie-only cross-site requests (CSRF)
**Detail:** Share/file mutations (multipart upload endpoints, often token-exempt for chunked uploaders), GET-modeled actions, and pre-auth flows (form submit, share request) may lack synchronizer tokens.
**Exact test:** Passive first: inspect SPA JS for anti-CSRF header injection and Set-Cookie SameSite attributes. Then, authorized: cross-site form POST (multipart, no custom headers, no token) to a share-mutation endpoint with victim cookies; cross-site top-level GET to suspected GET-modeled actions.
**Confirm:** State change occurs identical to same-origin request.
**Kill:** Per-request session-bound token validated server-side; session cookies SameSite=Strict + custom header required; GET handlers strictly read-only.

### H12. Legacy HMAC-SHA1 "Signature Authentication Method" still mints API tokens
**Detail:** Accellion-era flow (base_string = client_id|@@|user_id|@@|timestamp|@@|nonce, HMAC-SHA1 signed, X-Accellion-Version: 8) may still validate server-side for migrated customers.
**Exact test:** Send a correctly-formed legacy signature auth-code request to the token endpoint with the legacy header.
**Confirm:** Token issued (vs mere invalid-credential rejection).
**Kill:** Rejected as unknown/unsupported grant or method naming the signature method as removed.

### H13. Delegated admin roles can alter or purge audit events
**Detail:** Kiteworks sells auditability; delegated/helpdesk/application-admin roles may have a delete/edit/purge path on the audit trail, letting a compromised delegated admin erase exfiltration evidence.
**Exact test:** Delegated-role token attempts audit-event delete/purge API calls and retention-policy changes.
**Confirm:** Events deleted/purged or retention weakened by non-system-admin.
**Kill:** Audit store append-only/immutable; purge is system-admin-only with retention lock.

### H14. Content-Type sniffing mismatch on uploaded previews/downloads
**Detail:** Upload accepts benign declared type (image/png) with HTML/JS body; the share link serves it inline without Content-Disposition: attachment / nosniff → stored XSS on the trusted origin.
**Exact test:** Upload HTML file declared as image/png; open via share link as recipient; inspect response headers and rendering.
**Confirm:** Renders inline as HTML on the kiteworks origin (script/markup executes under CSP).
**Kill:** Always served with Content-Disposition: attachment and/or nosniff + sanitized generic type.

### H15. Stored markup in cross-user rendered fields
**Detail:** Attacker-controlled filename, file comment/description, Secure Data Forms field label, or display name/share-invite message renders unescaped in ANOTHER user's view (folder listing, recipient share UI, form filler view).
**Exact test:** Markup token (quote/event-handler probe, <b> probe) placed via account A; viewed in account B's DOM (view-source).
**Confirm:** Live markup/script in B's browser under the CSP (creator-only preview does NOT count — self-XSS excluded).
**Kill:** Entities escaped in all recipient views; or feature absent in this environment.

### H16. Approval-chain step-skipping / stale approval applies
**Detail:** Approval endpoint validates "actor is an approver" not "actor is the CURRENT step's approver"; approvals on withdrawn/expired transfers may return success or resurrect the transfer.
**Exact test:** Configure workflow requiring approver A then B (owned accounts); B approves while A pending; separately approve a withdrawn/expired transfer via its token/link.
**Confirm:** Out-of-order approval releases the transfer; stale approval returns 200 success or re-activates it.
**Kill:** 403/422 on out-of-order; withdrawn transfer stays withdrawn with explicit invalid-state error.

### H17. Token classes survive revocation lifecycle events
**Detail:** Revocation on disable/password-change may cover only the reported class (cf. CVE-2026-29092 EPG sessions); OAuth refresh, custom-app API, upload-session, and remember-device tokens may keep authorizing.
**Exact test:** Issue each token class for test account B; disable B (or change password) from an owned admin identity; reuse each token.
**Confirm:** Any class still authorizes API/download calls post-disable.
**Kill:** Every class fails 401/403 immediately after disable/password change.

### H18. MCP localhost:9999 OAuth callback interceptable on shared hosts
**Detail:** Loopback callback assumes one user per machine; on shared hosts a second local user can pre-bind port 9999 and capture the authorization code, then redeem it (if no PKCE/state binding) for a session as the victim — feeding the AI Data Gateway RAG.
**Exact test:** On a shared test host, bind localhost:9999 as a second user during a test MCP OAuth flow; observe code delivery and redemption.
**Confirm:** Second user captures code and obtains a token for the victim's session.
**Kill:** Ephemeral random port, mandatory PKCE with per-session verifier, or flow refuses when port is held.

### H19. SAML SP accepts unsigned or signature-confused assertions
**Detail:** SimpleSAMLphp-style ACS at /sp/module.php/saml/sp/saml2-acs.php/sp-sso may accept an assertion the IdP never signed, or trust an unsigned inner element under a signed wrapper (signature policy is admin-configurable).
**Exact test:** Submit unsigned / signature-confused SAML response to the ACS with an attacker-controlled identity (test IdP context).
**Confirm:** Authenticated session minted for the asserted identity.
**Kill:** All inbound assertions require valid IdP signatures (Response + Assertion), unsigned rejected.

### H20. Server-side fetch of attacker-influenced URLs (SSRF family)
**Detail:** MFT "import from URL"/download-from-URL, link-preview unfurling, webhook/notification URL registration, and document-conversion of remote references may issue server fetches; preview converters may resolve XXE/external entities (SVG/DOCX/XFA).
**Exact test:** If a URL-import/preview/webhook flow exists: point it at a controlled collaborator host and observe the inbound request (headers, source egress). Upload SVG/DOCX/PDF-XFA with external-entity probe to controlled host; check preview output and callbacks.
**Confirm:** Server-side request arrives at controlled host, or preview reflects resolved entity content.
**Kill:** No such flow exists; or fetches blocked/sandboxed; or converter disables external entities.

---

## Dropped from the top-20 (with reason)

- **SQLi ×3** (#46): no endpoints mapped yet; recon precondition — re-run after agents 7/8 map listing/report/search parameters.
- **2FA set ×4** (#59): weak evidence, low target fit vs program focus; keep as follow-up.
- **Open redirect ×3** (#65): typically low impact / soft finding; RelayState kept as chain note only.
- **Path traversal ×4** (#62) + **XXE set** (#63 minus preview): falsifiable but lower fit than authz core; second experiment wave.
- **Deserialization ×4** (#64): no reachable sink characterized in this environment; untestable now.
- **EPG mail paths** (#52-EPG, #69-MTA-markers, #64-S/MIME): no inbound mail path verified in the hunting env.
- **JWT alg confusion** (#60): untestable until a JWT is observed; structural check first (opaque vs JWT).
- **Case-variant email registration** (#70): identity edge case, low program fit.
- **Abuse-of-feature** (#75 forms-phishing, MCP-DLP, connector-creds): design observations, hard to score as bounty-eligible findings; note for threat-model writeup.
- **Reflected XSS ×4** (#49): keep the error-page and login-page probes as cheap first-wave probes (single canary requests), not full experiments.
- **ICAP verdict family** (#68 mismatch, #72 delegated-evidence, #79 fail-open, #73 version-inherits-verdict): high value but requires ICAP test path in the env — gated on EPG availability; second wave.

## Notes for the experiment runners

1. H1–H9 are the authorization core — they match the program's stated focus (privilege/role escalation, LDAP, "bypass Recipient Only") and Kiteworks' documented weak seams (numeric IDs, three-layer privilege model, configurable recipient validation). Start here.
2. Every confirm signal must be independently reproducible (two trials, two sessions) and distinguishable from the excluded classes — especially "anyone after authentication" disclosure and user enumeration.
3. Any hypothesis whose precondition fails (feature absent in this environment, endpoint unreachable, LDAP not wired) is REJECTED for this experiment, not deferred silently — record why_failed.

## Summary

- Deduplicated 108 hypotheses into 31 merged clusters; ranked by falsifiability, information value, program eligibility, and target fit.
- Top 20 selected: 9 authorization/IDOR/BOLA experiments (the program's stated focus), 4 privilege-escalation chains, and 7 in auth/session/link-enforcement classes — each with an exact confirm/kill test.
- Dropped 11 hypothesis groups with reasons (unmapped surface, untestable in this env, excluded classes, or lower impact than the authz core); recorded as follow-up waves, not lost.
