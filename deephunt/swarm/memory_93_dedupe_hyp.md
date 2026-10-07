# Hypothesis dedupe map — agent #93 (memory)
Date: 2026-09-27

Scope: `hyp_known.jsonl` (72 entries, agents 46–65) + `hyp_novel.jsonl` (36 entries, agents 66–79) = **108 hypotheses total**.
Originals untouched — nothing deleted. This file is the canonical dedupe map.

## Clusters (kept formulation first)

### C1 — Document preview/conversion pipeline XXE/SSRF
- **KEPT:** n=63 (xxe, known) — "XXE in document preview/conversion pipeline via OOXML or PDF/XFA uploads" — most falsifiable: falsifier names the converter-stack identification step and cites the live 2026 Tika XFA CVE class.
- **DUPLICATE:** n=61 (file-upload, known) — "Preview-generator SSRF/XSLT-style transformation on uploaded documents" — same sink (server-side converter fetches external entity / resolves XXE), less precise framing. Retire as independent claim; its collaborator-DNS probe feeds the kept hypothesis.

### C2 — Zip-slip in server-side archive extraction
- **KEPT:** n=62 (path-traversal, known) — "Zip-slip in server-side archive extraction (uploaded archives)" — crispest falsifier: every entry lands inside the extraction root or the claim dies.
- **DUPLICATE:** n=61 (file-upload, known) — "Archive nested-payload smuggling past AV/preview pipeline" — same core primitive (traversal-bearing archive entry names); the nested-archive AV-recursion nuance becomes a sub-probe of the kept claim, not a second hypothesis.

### C3 — "Recipient Only" share boundary
- **KEPT:** n=53 H4 (idor, known) — "'Recipient Only' download endpoint validates token but not caller identity against recipient list" — pins the documented admin-configurable RECIPIENT VALIDATION seam; clean falsifier (B rejected while A succeeds).
- **DUPLICATE:** n=58 (auth-bypass, known) — "'Recipient Only' share readable by an unauthenticated party via the recipient self-registration flow" — same authorization property (non-recipient reads Recipient-Only content); its unauthenticated-registration angle is a second probe path inside one experiment, not a separate hypothesis.

### C4 — SSO/JIT + LDAP-sync provisioning skips the admin-role strip
- **KEPT:** n=77 (spec-vs-reality, novel) — "create_user admin-strip guard bypassed by SSO JIT and LDAP sync provisioning paths" — most falsifiable: requires demonstrating the strip in all three paths (create_user, SSO JIT, LDAP sync) and names the documented invariant being violated.
- **DUPLICATE:** n=76 H-PRCHAIN-2 (composition, novel) — "LDAP/SSO JIT attribute + missing admin-strip = first-login elevation" — same claim in chain language.
- Note: n=58 (auth-bypass, known) JIT-merge-into-victim-account kept SEPARATE — different outcome (account merge vs strip-bypass on new account).

### C5 — Token revocation / lifecycle gap
- **KEPT:** n=60 (jwt-token, known) — "OAuth refresh tokens / custom-application API tokens / 'remember this device' tokens survive account disable or password change" — per-token-class test matrix, cites the CVE-2026-29092 EPG precedent, falsifier covers every class.
- **DUPLICATE:** n=70 (assumption-breaker, novel) — "Revoked API/OAuth tokens remain valid because resource servers validate signatures without a revocation check" — same property (token valid after the event that should kill it); its explicit-revoke/remote-wipe trigger is an additional probe in the same experiment.

### C6 — MCP localhost:9999 OAuth callback interception
- **KEPT:** n=70 (assumption-breaker, novel) — "localhost:9999 MCP OAuth callback assumes one person per machine — shared-host code interception" — cleanest falsifier (bind port as second user; check for random port / PKCE / state binding).
- **DUPLICATE:** n=73 (emergent, novel) — "MCP localhost OAuth callback interception feeds AI Data Gateway RAG" — same primitive with a downstream RAG-exfiltration impact chain; the interception assumption is the shared testable core.
- Note: n=75 (misuse-case) "MCP Server turns AI client into a DLP-bypassing exfiltration channel" kept SEPARATE — different mechanism (authorized insider via LLM context, no interception).

### C7 — Expired / exhausted share link still serving
- **KEPT:** n=66 (business-logic, novel) — "Expired/download-exhausted secure link still serving via alternate retrieval path" — strongest falsifier: create a 1-download / 1-minute link, then demand uniform denial across ALL retrieval paths.
- **DUPLICATE:** n=60 (jwt-token, known) — "Qualified-link expiry not enforced server-side; standard secure links may have no expiry at all" — same property tested through fewer paths; its "standard links may have no expiry at all" config question is a sub-nuance of the kept claim.

### C8 — Share-link capability / policy desync over time
- **KEPT:** n=72 (novel-class, novel) — "Dormant share-capability desync (policy re-evaluation skipped on share-link access)" — general formulation: issuance-time policy vs per-access re-evaluation, with reclassify/demote-then-re-access test.
- **DUPLICATE:** n=73 (emergent, novel) — "Share-link authorization snapshot survives LDAP role revocation (TOCTOU)" — LDAP-role-revocation is an instance of the kept mechanism, not a second class.

### C9 — LDAP filter injection in the login flow
- **KEPT:** n=47 (ldap, known) — "Login username flows unsanitized into LDAP login filter, changing filter semantics" — medium confidence, concrete metachar probes ('*', ')', '('), falsifier demands identical response class across trials.
- **DUPLICATE:** n=69 (trust-boundary, novel) — "App trusts its LDAP filter construction; injected filter logic returns multiple entries and the app binds as the first match" — the multi-entry-first-match mechanic is a failure-mode variant of the same probe; the kept falsifier's identical-response test disproves both simultaneously.
- Note: n=47's three sibling LDAP injections (ldapGroups, share-dialog autocomplete, secure-email recipient validation) are DIFFERENT sinks — kept separate.

### C10 — Mass assignment of admin/role flags on user update
- **KEPT:** n=57 H2 (mass-assignment, known) — "Guarded user attributes bindable on user update endpoint (admin/user flags via PUT /rest/users/{id})" — references documented /rest/index.html surface, explicit strip/400/403 rejection criteria.
- **DUPLICATE:** n=56 (privesc, known) — "Role parameter accepted on profile/update request" — same endpoint class, less falsifiable formulation.
- Note: n=56 "Self-registration assigns elevated default role" kept SEPARATE — different endpoint (signup vs update).

### C11 — Unclamped roleId on member-add / invite
- **KEPT:** n=57 H1 (mass-assignment, known) — "roleId on POST /rest/folders/{id}/members not clamped to inviter's privilege" — concrete payload (userId+roleId, numeric enum via GET /rest/roles), two-account confirming protocol.
- **DUPLICATE:** n=56 (privesc, known) — "Invitation flow grants requester-chosen role" — same claim, no endpoint or payload detail.

## Resulting counts
- Total read: 108 (72 known + 36 novel)
- Duplicate pairs collapsed: 11 → 11 canonical claims removed
- **Unique testable claims: 97** (66 known + 31 novel)

## Families kept separate deliberately (do not re-dedupe)
- ICAP-delegation family: n=68 verdict-timing/path mismatch, n=72 delegated-evidence divergence (audit vs data plane), n=73 version-verdict inheritance, n=79 fail-open on ICAP unavailability, n=76 H-EGCHAIN-3 forged MIP label — same trust boundary, five distinct failure modes, each with its own falsifier. Collapse only after one falsifier kills the shared mechanism.
- Folder/file member-role mutations: n=57 H1 (folder member-add roleId), n=54 BOLA-2 (file member update by non-owner), n=55 (Manager→Owner self-promotion / Owner demotion) — different endpoints, different role ladders; test as separate probes.
- Expired-link destruction: n=77 spec-vs-reality (link-expiry data-destruction guarantee vs retained derived copies) is a DELETION-lifecycle claim, distinct from C7's ACCESS-enforcement claim — keep separate.
- ?next=/returnUrl: n=49 reflected-XSS variant vs n=65 open-redirect variant — same parameter, different security properties; one probe covers both, log separately.
- Version objects: n=53 H1 (version overwrite IDOR), n=54 BOLA-3 (version promote authorization), n=72 version-slot desync (deleted version addressable), n=73 version-verdict inheritance — four distinct claims, keep all.
