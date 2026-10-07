# Rejected-Hypothesis Memory — Agent 94 (Failed-Hypothesis Learner)

**Date:** 2026-09-27
**Purpose:** Stop the swarm from burning experiment budget on hypotheses that are weak by structure, not just by luck. This file records WHY weak hypotheses are weak and exactly what evidence would strengthen or kill each one.
**Rule for future research direction:** a hypothesis with (a) no target-specific evidence, (b) an unverified feature-existence precondition, and (c) an expensive falsifier costs more than it can return. Kill the precondition first — a cheap feature-existence check kills whole families at once.

---

## 1. Pattern-level lessons (the real learning)

### L1. The dominant failure mode: class-prior-only evidence
~80% of the pool rests on "class-level prior" with literally zero target-specific observation ("No evidence from this target yet", "Untested; world model confirms only headers"). A class prior is a *starting point*, not evidence. **Lesson:** never allocate an experiment to a class-prior-only hypothesis before at least one passive observation grounds the feature's existence. One observation (e.g., `/login_config` 200 — agent 50) converts a weak hypothesis into a medium one. That is the highest-ROI step in this entire pool.

### L2. Feature-existence preconditions are cheap killers
Many hypotheses require a feature that may not exist in the hunting env: comment endpoints (BOLA-1, stored-XSS comments), Secure Data Forms 123FormBuilder legacy paths, AS4/SOAP receive endpoints, EPG inbound mail path, MCP localhost callback availability, SimpleSAMLphp deployment. **Lesson:** run a feature-existence triage wave first — one ≤10-request passive sweep answering "which of these endpoints/features exist" kills or upgrades ~30 hypotheses at once. Testing a non-existent feature is the most common waste.

### L3. The environment-auth-mode blocker
The LDAP family (47) is the single best-armed family (docs-grade evidence) but every one of its hypotheses dies instantly if the hunting env uses local accounts only (world-model open question #2). **Lesson:** open questions flagged "authentication flows unverified" are single-point failures for entire hypothesis families. Resolve env-auth-mode before any LDAP/SSO experiment.

### L4. Falsifiers that cost more than the hypothesis is worth
Several hypotheses have correct falsifiers that require 2 test accounts, LDAP config control, MIP-labeled documents, or ICAP infrastructure (agents 66, 68, 69, 72, 73, 77). An expensive falsifier on a low-confidence hypothesis is a bad bet — the experiment planner should demand cheap falsifiers first (passive header/JS checks) before authorizing the expensive ones.

### L5. Compound/conjunctive hypotheses multiply weakness
Each additional required condition multiplies the prior against the hypothesis (e.g., 75 "MCP callback intercept → RAG exfil" needs: PKCE absent AND no state binding AND MCP scope includes RAG reads; 68 "MIP label survives EPG then stripped in share path" needs: label preserved in EPG AND stripped in connector AND ICAP verdict delegated differently). **Lesson:** for compound hypotheses, kill conditions *in order of cheapest test* and abandon at the first failure.

### L6. Excluded-class adjacency is a silent kill
Several hypotheses border program-excluded classes: login-username probes near user enumeration (49, 47), "anyone after authentication" disclosure (53-H4, 54 BOLA-4), AV bypass by rename (61 archive), rate-limit (none found). A confirmed-but-unpayable finding costs the same as a rejected one. **Lesson:** every hypothesis touching excluded classes must have its non-excluded boundary written into the success criteria *before* the experiment.

### L7. Sandbox reachability caveat
Agent 63 admitted the hunting host was unreachable from the sandbox (curl timeout, browser.open empty) — its XXE hypotheses are documentary-only. **Lesson:** hypotheses written without any live contact with the target must be labeled REACHABILITY: NONE so they don't get test budget before the feature-existence wave.

### L8. Version-safety: "env is 9.5.1" matters
Multiple hypotheses lean on pre-9.2/9.1 CVEs (CVE-2026-29092, CVE-2025-53939). The env runs 9.5.1; the prior for a *variant* of a patched CVE is much lower than the prior for the original. **Lesson:** CVE-adjacent hypotheses need evidence the patched surface was re-opened, not just that the old CVE existed.

---

## 2. Per-hypothesis weakness analysis

Confidence labels as written by the hypothesis authors. "Weak" below means low-confidence OR medium-confidence with a single-point-of-failure precondition.

### Agent 46 — SQLi (3, all LOW)
1. **Report-filter SQLi** — Why weak: no report endpoints mapped; rests entirely on class prior; stack undetected. Strengthen: map an admin/user report endpoint + observe one response differential on a benign type probe. Kill: typed 400s on all filters, or non-SQL backend for reports.
2. **order_by/sort SQLi** — Why weak: no listing endpoints mapped; sort parameter existence unverified. Strengthen: one listing endpoint that actually honors a `sort=` value. Kill: allowlisted sort columns or search-engine-backed ordering.
3. **MFT advanced-search SQLi** — Why weak: no search endpoints mapped; multi-field builder existence assumed. Strengthen: map one advanced-search endpoint with free-text + structured filters. Kill: per-field typed validation with identical boolean-probe results.

### Agent 49 — Reflected XSS (4, all LOW)
4. **404 error-page echo** — Why weak: no error-page behavior observed. Strengthen: one request showing path/query echoed. Kill: encoded echo or no reflection on single canary test.
5. **Share-link filename reflection** — Why weak: share-link URL structure unverified; upload flow not mapped. Strengthen: recon maps share-link structure. Kill: opaque-token links ignoring filename param.
6. **Login error echoes username** — Why weak: auth flow unmapped; adjacent to excluded user-enumeration class (boundary discipline needed). Strengthen: one canary login request showing interpolation. Kill: generic error text with no interpolation.
7. **next/returnUrl intermediate-page reflection** — Why weak: redirect-param existence unverified. Strengthen: one request showing an intermediate redirect page. Kill: direct 302s only, no rendered page.

### Agent 48 — Stored XSS (4, all LOW)
8. **Filename stored XSS in shared listing** — Why weak: upload/login flows unmapped; collaborator-view rendering unverified; CSP already constrains execution. Strengthen: confirm collaborator view renders raw filenames. Kill: escaped entities in view-source + CSP blocks inline script.
9. **Comment/description stored XSS** — Why weak: comment feature existence is an open question. Strengthen: verify comments exist on shared files. Kill: no comment feature in env → instant reject.
10. **Secure Data Forms label stored XSS** — Why weak: forms feature existence unverified; creator-vs-recipient rendering unmapped. Strengthen: verify forms exist and labels render to other users. Kill: no forms feature, or escaped labels; creator-only preview is excluded (self-XSS).
11. **Display-name/invite-message stored XSS** — Why weak: recipient-view rendering unverified. Strengthen: two-account test showing recipient DOM has live markup. Kill: escaped in recipient DOM; self-view rendering doesn't count.

### Agent 47 — LDAP injection (1 MEDIUM, 3 LOW)
12. **Login username → LDAP filter (MEDIUM)** — Why weak: best evidence in the pool (docs-grade filter construction), but single-point failure on env-auth-mode (LDAP vs local accounts). Strengthen: confirm env binds LDAP on login. Kill: env uses local accounts only, or identical metachar/benign response classes.
13. **/ldapGroups search injection** — Why weak: endpoint reachability unverified (admin-only or absent kills it). Strengthen: reach endpoint with a non-admin session. Kill: metachar group-name returns identical results to literal string.
14. **Share-dialog autocomplete injection** — Why weak: autocomplete search backend unverified (may be local users only). Strengthen: show autocomplete hits a live directory. Kill: only local/provisioned users searched.
15. **Secure-email recipient-validation injection** — Why weak: recipient-validation feature presence unverified; needs bypass (not just error differential) for impact. Strengthen: verify validation is enabled and reachable. Kill: pass/fail never flips on metachar input.

### Agent 52 — SSRF (2 MEDIUM, 2 LOW)
16. **MFT import-from-URL (MEDIUM)** — Why weak: the entire sink depends on an unverified URL-import feature. Strengthen: one UI/API surface element showing URL import. Kill: no URL-import flow in ≤10-request sweep.
17. **EPG inbound-mail fetch (MEDIUM)** — Why weak: inbound mail path to the hunting env unverified. Strengthen: confirm env accepts test email. Kill: no inbound mail path.
18. **Link-preview unfurl (LOW)** — Why weak: preview feature existence unverified. Strengthen: observe unfurl behavior. Kill: no preview/unfurl in UI or metadata.
19. **Webhook/notification or doc-conversion fetch (LOW)** — Why weak: two sinks bundled in one hypothesis; each unverified. Strengthen: find one user-influenced webhook URL registration or remote-reference conversion. Kill: neither exists.

### Agent 53 — IDOR (3 MEDIUM, 1 LOW) — strongest family, evidence-grounded
20. **H1 initiateUpload version-overwrite (MEDIUM)** — Why weak: assumes per-object role check absent; depends on numeric-ID addressability (strong evidence). Strengthen: confirm 9.5.1 endpoint signature matches docs. Kill: 403 for Viewer caller on another user's file_id, or documented design semantics.
21. **H2 Viewer download bypass (MEDIUM)** — Why weak: assumes byte endpoint skips Viewer-vs-Downloader split (UI does enforce). Strengthen: confirm direct content endpoint exposed to Viewer role. Kill: 403 on direct content GET for Viewer.
22. **H3 activity-log/Track ID swap (MEDIUM)** — Why weak: assumes ID-keyed read skips per-object role check. Strengthen: confirm log/Track endpoints accept caller-supplied IDs. Kill: 403/empty for under-privileged caller; sender-bound server-side.
23. **H4 Recipient-Only identity binding (LOW)** — Why weak: recipient validation is admin-configurable; env default unknown; "anyone after authentication" excluded-class boundary is subtle here. Strengthen: verify env has validation DISABLED and Recipient-Only creatable. Kill: B's download rejected while recipient succeeds.

### Agent 51 — CSRF (1 MEDIUM, 2 LOW)
24. **Multipart upload CSRF (MEDIUM)** — Why weak: no token mechanism observed; upload exemption is class prior. Strengthen: grep SPA JS for anti-CSRF header on mutations (cheap, passive). Kill: per-request token bound to session found in JS.
25. **GET-modeled state change + SameSite gap (LOW)** — Why weak: Set-Cookie attributes never inspected (this is a 1-request passive kill). Strengthen: inspect cookies for SameSite=Lax/None. Kill: SameSite=Strict found → dead.
26. **Pre-auth endpoint CSRF (LOW)** — Why weak: pre-auth session cookie existence unverified; impact may be rate-limit-excluded. Strengthen: observe pre-auth session cookie. Kill: no pre-auth session, or CAPTCHA/token on pre-auth mutations.

### Agent 56 — Privesc (4, all LOW)
27. **Role param on profile update** — Why weak: update endpoint parameter list unmapped. Strengthen: API surface mapping (agents 8/9) shows user/profile PUT route. Kill: extra role fields rejected/ignored.
28. **Invitation flow grants chosen role** — Why weak: invite parameter list unmapped. Strengthen: capture an invite request showing role param. Kill: no role param, or server clamps to inviter's role.
29. **Group-membership change lacks admin check** — Why weak: endpoint existence unmapped. Strengthen: map group-membership mutation endpoint. Kill: 403 for non-admin callers.
30. **Self-registration elevated default** — Why weak: signup flow unmapped; rests on "test env misconfiguration" stereotype. Strengthen: capture registration response + session token role claims. Kill: default role unprivileged, role param ignored.

### Agent 55 — BFLA (4, all LOW)
31. **/adminRoles grant by non-admin** — Why weak: endpoint admin-gating already documented ("requires authentication as an administrative user" — evidence points against). Strengthen: find a verb/path the documented gate misses. Kill: 401/403 across grant verbs with low-priv token.
32. **/profiles privilege mutation by non-admin** — Why weak: same documented-gate pattern as 31. Strengthen: identify a write path not covered by the admin gate. Kill: all privilege-mutating writes 401/403 for low-priv token.
33. **Manager→Owner self-promotion (CVE-2025-53939 variant)** — Why weak: variant-of-patched-CVE (L8); 9.5.1 may have closed it. Strengthen: find a member-API role-id parameter the fix missed. Kill: only Owner can mutate membership roles.
34. **/admin/devices remote-wipe by non-admin** — Why weak: destructive-impact test with tight consent requirements; docs place it admin-side. Strengthen: show path reachable by non-admin token. Kill: cross-user device ops 403 for non-admin.

### Agent 57 — Mass assignment (1 MEDIUM, 3 LOW)
35. **H1 roleId on folder members (MEDIUM)** — Why weak: assumes roleId not clamped to inviter privilege; payload shape is docs-grounded (strong). Strengthen: confirm member-add reachable by low-role caller. Kill: high roleId rejected/clamped, or member-add owner-only.
36. **H2 guarded attrs on user update** — Why weak: deserialization behavior of update endpoint unverified. Strengthen: observe update endpoint accepting unknown fields. Kill: unknown fields stripped/rejected; endpoint non-admin-unreachable.
37. **H3 ownerId on folder create/update** — Why weak: owner field name and bindability unverified. Strengthen: create request echoing supplied ownerId in metadata. Kill: owner derived from session; delegation flow explicitly authorized.
38. **H4 extra permission flags on share create** — Why weak: share payload schema unmapped (world-model Q3 open). Strengthen: capture a share-create request. Kill: strict enum validation; capabilities derived server-side.

### Agent 61 — File upload (1 MEDIUM, 2 LOW)
39. **Content-Type sniffing on preview/download (MEDIUM)** — Why weak: preview-serving layer behavior unobserved. Strengthen: one download/preview response showing Content-Type + Content-Disposition. Kill: always `attachment` + nosniff → dead (cheap falsifier).
40. **Archive nested-payload smuggling** — Why weak: archive ingestion endpoint unmapped; near excluded AV-bypass class (must be traversal, not rename). Strengthen: confirm server-side extraction for preview. Kill: tracer confined to sandbox temp dir.
41. **Preview-generator XXE/SSRF on uploads** — Why weak: converter stack unmapped. Strengthen: identify converter (headers/error text). Kill: external entities disabled; no outbound callback.

### Agent 59 — 2FA (4, all LOW)
42. **Remember-device marker without binding** — Why weak: marker format, binding, step-up behavior all unobserved. Strengthen: capture marker; replay across browsers. Kill: signed token + server-side fingerprint + step-up on sensitive actions.
43. **First-to-enroll 2FA interception** — Why weak: enrollment-vs-session binding undocumented; needs invite interception. Strengthen: observe enrollment endpoint accepting invite token alone. Kill: enrollment bound to verified session.
44. **Recovery-code regeneration without step-up** — Why weak: recovery-code flow not documented to exist. Strengthen: verify the flow exists at all. Kill: no such flow, or step-up required.
45. **LDAP Username Attribute identity confusion** — Why weak: resolution-key semantics unobserved; attribute uniqueness unknown. Strengthen: observe challenge routing on controlled colliding identities. Kill: resolution keyed on immutable object ID.

### Agent 58 — Auth bypass (4, all LOW)
46. **Mobile m=1 OAuth variant skips checks** — Why weak: pipeline-sharing between variants unverified. Strengthen: compare web vs m=1 flows on one auth step. Kill: identical pipeline, same mandatory 2FA/consent.
47. **SAML unsigned-assertion acceptance** — Why weak: signature policy is admin-configurable; env setting unknown; needs consenting IdP control. Strengthen: observe an unsigned assertion rejected/accepted. Kill: signed-only policy enforced.
48. **JIT SSO merge into victim account** — Why weak: JIT merge semantics unverified; needs IdP attribute control. Strengthen: one controlled JIT login with colliding attribute. Kill: JIT creates-only; merging requires admin-verified linking.
49. **Recipient-Only via registration without inbox** — Why weak: activation-token strength unverified. Strengthen: observe activation flow mechanics. Kill: single-use unguessable activation link mandatory.

### Agent 60 — JWT/token (4, all LOW)
50. **OAuth JWT alg confusion** — Why weak: token FORMAT never observed; if opaque tokens, hypothesis is structurally impossible. Strengthen: decode one self-issued access token (JWT vs opaque). Kill: opaque reference tokens → dead instantly.
51. **Upload-session token unbound to folder/user** — Why weak: session-ID binding undocumented; session ID may not even be client-visible. Strengthen: capture session ID in upload flow. Kill: chunk endpoints re-derive auth server-side.
52. **Qualified-link expiry not enforced server-side** — Why weak: enforcement point undocumented. Strengthen: one expired-link re-request through raw endpoint. Kill: uniform 403/expired across all paths.
53. **Token classes survive disable/password-change** — Why weak: variant-of-patched-CVE (CVE-2026-29092, L8); needs admin control of test account. Strengthen: test one token class post-disable. Kill: all classes fail post-disable.

### Agent 64 — Deserialization (1 MEDIUM, 3 LOW)
54. **H64-1 PHP unserialize via SimpleSAMLphp sessions (MEDIUM)** — Why weak: SimpleSAMLphp deployment on this instance unverified. Strengthen: probe /simplesaml/* and /login_config SSO flags. Kill: 404 on SimpleSAMLphp paths → dead.
55. **H64-2 form/workflow definition import deserialization** — Why weak: import format (JSON vs XML) unverified. Strengthen: verify an XML import path exists. Kill: JSON-only with strict schema, no class instantiation.
56. **H64-3 MCP OAuth token deserialization** — Why weak: opaque token mechanics unverified. Strengthen: show a non-JWT serialized blob decoded server-side. Kill: JWS-only, signature-first verification.
57. **H64-4 S/MIME PKCS#7 parsing in EPG** — Why weak: EPG inbound mail path may be unreachable (L7-style); untestable = rejected for this experiment. Strengthen: confirm reachable mail path. Kill: no reachable EPG mail path.

### Agent 65 — Open redirect (1 MEDIUM, 2 LOW)
58. **SAML RelayState open redirect (MEDIUM)** — Why weak: RelayState validation policy unobserved; needs completed SSO with consenting accounts. Strengthen: one SP-initiated login with canary RelayState. Kill: non-whitelisted RelayState rejected or forced to default landing.
59. **Login ?next=/returnUrl= external** — Why weak: destination-param existence unverified. Strengthen: one login-page request with canary param. Kill: relative-only validation or fixed landing.
60. **Logout/SLO redirect param** — Why weak: SLO endpoint reachability unverified; low standalone value. Strengthen: observe logout 302 chain with canary param. Kill: param ignored or same-origin-only.

### Agent 62 — Path traversal (4, all LOW)
61. **Zip-slip in archive extraction** — Why weak: no archive endpoints mapped. Strengthen: confirm server-side extraction exists. Kill: entries canonicalized into extraction root.
62. **Traversal in download/preview path param** — Why weak: no download endpoints mapped; may be token-only URLs. Strengthen: find a path/filename parameter on a download endpoint. Kill: opaque tokens only.
63. **Traversal via filename in export-ZIP generation** — Why weak: export flow existence unverified. Strengthen: observe export-as-ZIP flow. Kill: filenames sanitized or opaque entry names.
64. **Traversal in preview cache key** — Why weak: cache-key derivation unverified. Strengthen: observe cache behavior. Kill: hash/opaque-ID keys.

### Agent 54 — BOLA (2 MEDIUM, 2 LOW)
65. **BOLA-1 comments bypass parent-file ACL (MEDIUM)** — Why weak: comment feature existence unverified; API docs list endpoints (docs-grade). Strengthen: verify comments exist in env. Kill: 403/404 for low-priv cross-file comment access.
66. **BOLA-2 file member role update by non-owner (MEDIUM)** — Why weak: owner-only requirement undocumented either way. Strengthen: attempt role update as non-owner member. Kill: 403 for non-owner, owners succeed.
67. **BOLA-3 version promote lacks write check** — Why weak: per-object check unverified. Strengthen: attempt promote as viewer. Kill: 403 for viewer, editor succeeds.
68. **BOLA-4 content download on guessable ID** — Why weak: adjacent to excluded "anyone after authentication" class; needs outside-sharing-model access. Strengthen: cross-user ID request with no shared relationship. Kill: consistent 403/404.

### Agent 63 — XXE (1 MEDIUM, 3 LOW) — REACHABILITY: NONE (L7)
69. **SAML metadata import XXE (MEDIUM)** — Why weak: written with zero live contact with the target. Strengthen: any live observation of the admin SSO UI. Kill: no XML parsing in metadata import, or DOCTYPE rejected.
70. **Form-definition XML import XXE** — Why weak: XML import format speculative ("speculative on the format" — author's own word). Strengthen: confirm XML import path exists. Kill: JSON-only.
71. **AS4/ebMS SOAP envelope XXE** — Why weak: AS4/SOAP exposure "NOT publicly confirmed for Kiteworks". Strengthen: find one SOAP receive endpoint. Kill: no such endpoint.
72. **OOXML/PDF-XFA preview XXE** — Why weak: converter stack unmapped. Strengthen: identify converter chain. Kill: client-side rendering only, or XFA disabled.

### Agent 50 — DOM XSS (1 MEDIUM, 3 LOW) — best passive evidence in the pool
73. **desanitize() decode-then-render (MEDIUM)** — Why weak: sink unconfirmed in 21 remaining chunks (one chunk analyzed, zero sinks). This is the closest to a real finding — it needs grep work, not more hypothesizing. Strengthen: grep remaining chunks for innerHTML/v-html consuming vue_config. Kill: all rendering textContent/React-escaped.
74. **Tenant link URLs as javascript: href (LOW)** — Why weak: scheme validation unobserved; fields empty in this env. Strengthen: find link-rendering code. Kill: http/https allowlist or non-tenant-editable fields.
75. **location.search → location.assign (LOW)** — Why weak: x.fI semantics unde-minified; CSP blocks javascript: anyway. Strengthen: de-minify x.fI/x.JO. Kill: scheme-enforced or fixed-template merge (open-redirect variant may survive).
76. **username param pre-fill (LOW)** — Why weak: value only feeds React state in analyzed chunk; sink unconfirmed. Strengthen: trace state setter through remaining chunks. Kill: React-escaped only.

### Agent 68 — Cross-feature (1 MEDIUM, 2 LOW)
77. **SAML↔LDAP role-mapping conflict (MEDIUM)** — Why weak: needs dual-provisioned account + role divergence observed on two surfaces; expensive falsifier (L4). Strengthen: provision one dual-path test account. Kill: both surfaces agree on one role set.
78. **MIP label stripped in share path (LOW)** — Why weak: compound (L5): needs label survival in EPG AND stripping in connector AND divergent ICAP. Strengthen: first check label fidelity on one connector sync. Kill: label/RMS survives with consistent verdicts.
79. **AV-vs-ICAP verdict mismatch (LOW)** — Why weak: needs transient/verdict-split state observed across client paths. Strengthen: one DLP-triggering upload shared via two paths. Kill: all paths enforce the DLP verdict consistently.

### Agent 67 — Workflow state (3, all LOW)
80. **Share revocation doesn't kill in-flight downloads** — Why weak: session/revoke binding unobserved. Strengthen: one revoke-mid-download test. Kill: 403 on all chunks post-revoke.
81. **Chunked upload survives role demotion** — Why weak: finalize-time re-auth unobserved. Strengthen: one demote-mid-upload test. Kill: 403 on chunk commit/finalize post-demotion.
82. **Approval on withdrawn transfer** — Why weak: approval-idempotency unobserved. Strengthen: one approve-after-withdraw test. Kill: explicit invalid-state error, no resurrection.

### Agent 70 — Assumption breakers (1 MEDIUM, 2 LOW)
83. **localhost:9999 MCP callback interception (MEDIUM)** — Why weak: needs shared test host + PKCE/state absence unverified. Strengthen: inspect MCP OAuth flow for random port / PKCE / state binding. Kill: ephemeral port + PKCE + port-held refusal.
84. **Revoked tokens still valid (JWT-only validation)** — Why weak: revocation-propagation semantics undocumented. Strengthen: revoke one test token, replay after minutes. Kill: immediate 401/403 post-revoke.
85. **Case-variant email double-account** — Why weak: uniqueness-comparison semantics unverified. Strengthen: one controlled case-variant registration. Kill: rejected as duplicate.

### Agent 66 — Business logic (2 MEDIUM, 1 LOW)
86. **Expired link serves via alternate path (MEDIUM)** — Why weak: needs share-link creation + per-path re-request; falsifier is cheap and concrete. Strengthen: create one max-downloads=1 link, re-request via all paths. Kill: uniform deny → dead (this is a good experiment — cheap falsifier).
87. **Approval-chain step-skipping (MEDIUM)** — Why weak: approval-endpoint step validation unobserved. Strengthen: one out-of-order approval attempt. Kill: 403/422 + audit records rejection.
88. **External-recipient restriction bypass via secure email (LOW)** — Why weak: needs profile blocking external shares + email path comparison. Strengthen: verify profile blocks external share links first. Kill: both paths consult the same policy.

### Agent 72 — Novel class (3, all LOW)
89. **Dormant share-capability desync** — Why weak: policy re-evaluation timing unobserved; cache-vs-desync distinction is subtle. Strengthen: reclassify-then-reaccess with cache TTL exceeded. Kill: immediate 403 post-reclassification across nodes.
90. **Version-slot desync (deleted version addressable)** — Why weak: deletion implementation unobserved. Strengthen: delete v1, request prior address. Kill: consistent 404/410.
91. **Delegated-evidence divergence (audit vs ICAP)** — Why weak: needs ICAP-flow control + audit comparison; expensive. Strengthen: one ICAP flow with audit-vs-delivery comparison. Kill: audit always matches data-plane outcome.

### Agent 73 — Emergent (2 MEDIUM, 1 LOW)
92. **Versioned content inherits prior ICAP verdict (MEDIUM)** — Why weak: per-version scan semantics unobserved. Strengthen: upload v2 with DLP-triggering content, watch for fresh scan/audit entry. Kill: fresh ICAP verdict per version.
93. **Share-link auth snapshot survives LDAP revocation (MEDIUM)** — Why weak: needs directory control + share lifecycle observation. Strengthen: revoke role, re-access share. Kill: per-access re-evaluation or immediate stop.
94. **MCP callback → RAG exfil (LOW)** — Why weak: compound (L5): interception AND redeemability AND RAG scope. Strengthen: kill the cheapest condition first (PKCE check). Kill: PKCE/state binding or MCP scope excludes content queries.

### Agent 69 — Trust boundary (1 MEDIUM, 2 LOW)
95. **EPG trusts forged internal markers** — Why weak: needs direct SMTP access to gateway + classification logic. Strengthen: two spoofed messages, one with forged markers. Kill: identical policy treatment or direct delivery rejected.
96. **LDAP filter multi-entry → first-match bind (MEDIUM)** — Why weak: multi-entry handling unobserved; overlaps agent 47's family. Strengthen: controlled metachar login observing entry selection. Kill: escaped to literal match, zero/one entries.
97. **Refresh tokens lack device binding (wipe advisory)** — Why weak: wipe-then-replay needs device control; bearer-token design is standard. Strengthen: wipe test device, replay refresh token from second fingerprint. Kill: server-side revocation on wipe.

### Agent 75 — Misuse case (1 MEDIUM, 2 LOW)
98. **Credential harvesting via Secure Data Forms (MEDIUM)** — Why weak: form publishing + notification routing unverified; this is abuse-of-feature (no code bug — bounty value uncertain). Strengthen: verify public form publishing + attacker-controlled notification address. Kill: notifications locked to owner domain, or external-form warning unremovable.
99. **MCP as DLP-bypassing exfil channel** — Why weak: DLP-on-MCP-reads unverified. Strengthen: check MCP tool scope + consent. Kill: per-file consent or DLP evaluated on MCP reads.
100. **Stored connector creds as lateral bridge** — Why weak: credential-vault exposure unverified; admin role may already own backend. Strengthen: verify connector-admin session can reach backend beyond sync actions. Kill: vaulted creds, least-privilege service identity, same-role restriction.

### Agent 76 — Composition (2 MEDIUM, 1 LOW)
101. **Self-edit attribute + profile mapping = auto-promotion (MEDIUM)** — Why weak: mapping-rule re-evaluation timing unobserved. Strengthen: change matched attribute, check profile across fresh session. Kill: rules evaluated at login/SSO-sync only.
102. **LDAP/SSO JIT + missing admin-strip (MEDIUM)** — Why weak: JIT-path strip unverified (the documented strip is on create_user). Strengthen: provision with admin-claiming attribute via JIT. Kill: JIT applies identical strip.
103. **Forged MIP label + ICAP = EPG bypass (LOW)** — Why weak: compound (L5): label forgery AND gateway trust. Strengthen: submit manipulated label, observe verdict. Kill: gateway cryptographically validates labels.

### Agent 77 — Spec vs reality (1 MEDIUM, 2 LOW)
104. **Link-expiry destruction vs retained derived copies (LOW)** — Why weak: deletion scope unobserved; derived-store reachability is speculative. Strengthen: expire a link, probe preview/search/verdict caches. Kill: byte-level absence everywhere.
105. **Zero-privilege start vs default-profile fallback (LOW)** — Why weak: JIT/LDAP provisioning path behavior unobserved. Strengthen: provision via SSO JIT/LDAP with no matching rule. Kill: lands with zero privileges.
106. **create_user admin-strip bypassed on JIT/LDAP (MEDIUM)** — Why weak: same precondition as 102; distinct framing (spec claims platform-wide guard). Strengthen: same test as 102. Kill: uniform strip across all paths.

### Agent 74 — Forgotten feature (1 MEDIUM, 2 LOW)
107. **Legacy HMAC-SHA1 signature auth still mints tokens (MEDIUM)** — Why weak: token endpoint's legacy-grant support unobserved. Strengthen: one correctly-formed legacy auth-code request. Kill: rejected as unknown/unsupported grant (not just bad creds).
108. **123FormBuilder legacy endpoints live (LOW)** — Why weak: legacy URL patterns unprobed. Strengthen: probe legacy URL patterns. Kill: all 404/redirect.
109. **X-Accellion-Version shims change behavior (LOW)** — Why weak: header parsing unobserved. Strengthen: vary header, diff responses. Kill: byte-identical responses.

### Agent 79 — Negative space (1 MEDIUM, 2 LOW)
110. **Delegated admins can edit/purge audit events (MEDIUM)** — Why weak: audit-store immutability unobserved; nobody checked. Strengthen: attempt audit edit/purge as delegated admin. Kill: immutable storage, no delete path, retention locks.
111. **ICAP unreachable fails open (LOW)** — Why weak: failure-mode behavior undocumented. Strengthen: observe behavior during ICAP outage/error. Kill: demonstrably fails closed, not configurable to fail-open.
112. **Delegated admins reset system-admin credentials/2FA (LOW)** — Why weak: credential-lifecycle scoping undocumented. Strengthen: attempt reset targeting a higher-privilege account. Kill: system-admin-only + dual authorization.

---

## 3. Priority kills — the cheapest evidence that would retire the most hypotheses

1. **Auth-mode check** (local vs LDAP/SSO in hunting env): kills or upgrades agents 47, 58-SAML, 65-RelayState, 69-LDAP, 70-case-variant, 77. Single most leveraged observation.
2. **Feature-existence sweep** (comments, forms, EPG inbound mail, MCP callback, SimpleSAMLphp paths, AS4, 123FormBuilder URLs, share flows, version endpoints): kills ~30 hypotheses at once.
3. **Grep remaining 21 JS chunks** (agent 50): the desanitize hypothesis is the only one with real code evidence; sink confirmation is hours of work, not an experiment.
4. **JWT-vs-opaque token check**: one token decode kills or upgrades agent 60's alg-confusion hypothesis instantly.
5. **Set-Cookie SameSite inspection**: one passive response kills agent 51's GET-CSRF hypothesis.
6. **/rest/index.html reachability + admin-endpoint gating probe**: one low-priv token against /adminRoles, /profiles, /admin/devices falsifies agents 55/57's cheapest claims.

## 4. Anti-patterns for future hypothesis generation

- **Do not write hypotheses with REACHABILITY: NONE** without labeling them as such (agent 63).
- **Do not rest on "test environments are misconfigured"** as evidence (agent 56 #30).
- **Do not bundle two unverified sinks in one hypothesis** (agent 52 #19).
- **Do not cite a CVE as evidence for a variant on a patched version** without a re-opening signal (L8).
- **Adjacent-to-excluded-class hypotheses must state the non-excluded boundary in success criteria before testing** (L6).
- **Every hypothesis must name its cheapest falsifier first**, not its most thorough one (L4).

---

## Summary

- 111 hypotheses reviewed: ~80 are class-prior-only with no target evidence; the weakest families are XXE (no live contact), privesc/BFLA (docs already assert the gate), and speculative stored-XSS (feature existence unverified).
- The strongest candidates to promote are: dom-XSS desanitize() (real code captured), the IDOR family (docs-grounded + cheap falsifiers), and the expired-link alternate-path test (cheap falsifier, medium confidence).
- Six cheap observations (auth-mode, feature sweep, JS grep, token decode, cookie attrs, /rest gating probe) would kill or upgrade roughly half the pool before any experiment runs.
