# Reusable Technique Notes — swarm agent #97 (technique generalizer)

Derived from `obs_recon.jsonl`, `obs_app.jsonl`, `hyp_known.jsonl` (Kiteworks YesWeHack campaign, 2026-09-27). Each note is a transferable tactic: usable on other targets, independent of this target's specifics.

---

## T1. Distinguish infra outage from target throttling with a neutral control host

- **Technique:** When direct requests to a target start timing out, immediately issue the same request to a neutral third-party host (e.g. `https://example.com`, `https://www.google.com/generate_204`) from the same egress path. If the control also fails, the problem is your network, not the target.
- **When to use:** Whenever a target goes dark mid-session, before spending request budget on retries or re-planning.
- **What it found here:** Four independent agents (crawler #7, auth #13, static-asset #10, TLS #5) independently proved a sandbox egress outage — all target requests AND `example.com` failed identically. Prevented the team from misclassifying it as target-side tarpitting or WAF rate-limiting.
- **Limits:** A control host passing while the target fails only proves *your* egress works — the target could still be tarpitting, blocking your UA, or geo-blocking. Also pick a control host unlikely to block HEAD/GETs.

## T2. Treat wildcard certs as a CT blind spot, not an exhaustive inventory

- **Technique:** When enumerating subdomains via Certificate Transparency, check whether a wildcard cert (e.g. `*.zone`) covers the zone. If it does, CT can only ever show hosts that got *dedicated* certs — hosts hiding behind the wildcard are invisible by construction. Pivot to DNS brute-force, bug bounty scope pages, or certificate SANs of related hosts instead.
- **When to use:** Any subdomain-enumeration phase where a wildcard cert exists.
- **What it found here:** `*.bounty.kiteworks.dev` wildcard (DigiCert, renewed yearly since 2021) covers the authorized hunting host, which has NO dedicated CT entry — so CT enumeration was inherently incomplete. A dedicated LE cert for `ywh-kw-res-h3.bounty.kiteworks.dev` revealed a second program-infra host that CT only caught because it got its own cert.
- **Limits:** Wildcards are usually deliberately minimal-information; this technique only tells you CT is *incomplete*, it doesn't reveal the hidden hosts. Don't burn time re-querying CT hoping for more.

## T3. Mine the runtime-config endpoint (`/login_config` pattern) before touching auth

- **Technique:** On SPA login pages, look for a `<script src>` pointing at an extensionless/config-like path (e.g. `/login_config`, `/config`, `/settings.js`). These are server-generated JS fragments that inject enabled auth methods, SSO/LDAP toggles, feature flags, and tenant identifiers into the client. One GET answers what hours of doc-reading would.
- **When to use:** First contact with any SPA login surface — before mapping auth flows from documentation.
- **What it found here:** `/login_config` identified as the highest-value unverified lead by four agents (auth #13, static #10, crawler #7, integration #14); it would directly resolve the open questions of enabled auth integrations and SSO/LDAP endpoints on this instance. It was unreachable during the egress outage — deprioritized correctly rather than retried into a throttle.
- **Limits:** Some deployments serve it only to authenticated sessions or only render it in a browser (requires JS execution); a timed-out GET may be tarpit, not absence (see T7). Never brute-force variants of the path — one polite request, then move on.

## T4. Build the unauthenticated API inventory from the vendor's own OpenAPI spec and third-party client SDKs

- **Technique:** Before probing, locate the vendor's published OpenAPI/Swagger spec (developer portal, API docs) and any community SDKs generated from it. Extract endpoints by namespace (`/public/`, `/requestFile/{ref}/`, `/shortLinks/{ref}`) to find endpoints that by design need no session auth. Ref-token-gated resources are the highest-value unauthenticated surface.
- **When to use:** Any target with a documented REST API — the recon phase, before any active testing.
- **What it found here:** From the vendor OpenAPI v28 spec via a community Kotlin SDK, agent #11 mapped the unauthenticated surface: `POST /rest/public/mail/actions/sendFile`, `/rest/requestFile/{ref}/*`, `GET /rest/shortLinks/{ref}`, plus `GET /rest/uploads/config` (upload server config disclosure) — all without sending a single request to the target.
- **Limits:** Docs may lag the deployed version; a documented endpoint may not exist on the instance, and real endpoints may be undocumented. Always verify existence passively (e.g. OPTIONS/HEAD or docs URL) before treating as a live attack surface.

## T5. Use the program's own accepted-risk list as the boundary map

- **Technique:** Read the bounty program page's exclusions/accepted-risks section as a *positive* map of where the real boundary is. Each accepted risk names the tier just below the valid one — the valid finding is the bypass of the tier above it. Aim hypotheses exactly at that seam.
- **When to use:** Scoping any bounty target; hypothesis generation for file-sharing / SaaS targets.
- **What it found here:** The Kiteworks program page states file disclosure is valid only if it bypasses "Recipient Only" or reaches a file unauthenticated — files marked "anyone after authentication" are accepted risk. This defined the exact testable seam (recipient-validation enforcement, Viewer-download bypass, link-token replay) and excluded a whole wasted class.
- **Limits:** Program text is legal framing, not technical truth — verify the named tiers actually exist as enforcement points in the product (docs + config endpoints), since marketing tiers and code paths can diverge.

## T6. Rank privilege boundaries by "who grants what to whom" from API docs, not by UI roles

- **Technique:** Extract the privilege-management API endpoints (`/adminRoles`, `/profiles`, `/ldapGroups`, member-role updates) from API docs and rank the escalation seams: (1) non-admin → admin via role-grant endpoints, (2) role-ladder jumps (Viewer→Downloader is the classic read-capability split), (3) action-privilege vs content-access (RBAC/ABAC split), (4) licensed vs non-licensed user classes. Test each seam at the *API* layer, since UIs often enforce what the API doesn't.
- **When to use:** Any multi-role SaaS/file-sharing target with an admin API.
- **What it found here:** Produced the ranked boundary list used by the BFLA, IDOR, privesc, and mass-assignment hypothesis agents — e.g. `/adminRoles` grant by non-admin token, `roleId` clamping on `POST /rest/folders/{id}/members`, Viewer-vs-Downloader on direct `/rest/files/{id}/content`.
- **Limits:** Pure docs analysis — several ranked boundaries may be correctly enforced server-side. Each needs a controlled two-account test; never report the seam as a finding.

## T7. Read path-selective timeouts as a signal (WAF whitelist / tarpit), not just failure

- **Technique:** If `/` returns 200 quickly but *every* other path times out at the TCP/connect level — including static assets referenced by the page itself — suspect a WAF/reverse-proxy whitelist or deliberate tarpitting of non-whitelisted paths, especially when the first non-root attempt already hangs (rules out rate-limiting).
- **When to use:** When probing a hardened enterprise app and getting uniform timeouts on non-root paths.
- **What it found here:** Agent #9: 8/8 non-root paths (`/login_config`, JS bundles, CSS, `/robots.txt`, `/favicon.ico`) timed out while `/` returned 200; pattern was path-based, not rate-based. Correctly stopped at ~10 requests instead of hammering.
- **Limits:** Indistinguishable from a coincidental egress outage without the T1 control test — always run the neutral-host control first. Also, "tarpit" is an inference; confirm with header/timing analysis on a healthy network before asserting.

## T8. Diff the passive dossier against live behavior; treat stale intel as unconfirmed

- **Technique:** When a prior dossier claims resources exist (robots.txt, security.txt, specific endpoints), re-verify each claim with a single live request before building on it. Record discrepancies explicitly as UNCONFIRMED rather than silently inheriting them.
- **When to use:** Whenever inheriting intel from a previous agent/run/report.
- **What it found here:** The passive dossier claimed `/robots.txt` and `/.well-known/security.txt` existed; live GETs timed out. Agent #9 flagged the discrepancy (with the honest caveat that the outage could explain it) instead of letting downstream agents treat the files as established fact. Similarly, the "Apache Airflow lineage" dossier claim was checked against vendor MFT materials and marked UNVERIFIED.
- **Limits:** A single failed request during degraded conditions isn't disproof — mark as unconfirmed, not false, and schedule a re-check rather than asserting absence.

## T9. Map identity lifecycle states — deprovisioning gaps live between states

- **Technique:** Enumerate the user object's lifecycle flags from API docs/admin guides (`active`, `suspended`, `deactivated`, `deleted`, `verified`) and treat each *transition* as a test seam: does deactivation revoke sessions? does deletion reassign or orphan owned objects? is there a protected state (sole admin) and can it be circumvented? Historical CVEs cluster at these transitions.
- **When to use:** Any target with admin user-management and session handling.
- **What it found here:** Kiteworks user JSON showed five distinct flags (suspend → deactivate → delete pipeline, not a single delete); deactivation preserves data but historically sessions survived disable (CVE-2026-29092, EPG pre-9.2.1); sole-active-admin cannot be deactivated (ownership-safety invariant worth testing around).
- **Limits:** Docs describe intended semantics; the actual session-revocation behavior must be tested with two controlled accounts. Never test deprovisioning against real users.

## T10. Follow the delegated-trust chain: verdicts made outside the app are the app's weakest enforcement

- **Technique:** Inventory every external system whose verdict the app consumes (ICAP AV/DLP/ATP/CDR, LDAP attribute→role mapping, IdP SAML assertions, MIP labels, SIEM export). For each, ask: what happens when the external service is permissive, unreachable, or lies? Fail-open vs fail-closed is the finding; the app's own code is often fine.
- **When to use:** Enterprise targets with documented integrations (email gateways, DLP, directory services).
- **What it found here:** Kiteworks delegates file disposition to ICAP verdicts, role/profile assignment to LDAP attributes, auth to IdP assertions, and email policy to MIP labels — each mapped as a trust boundary with a concrete test question (e.g. unreachable ICAP: fail open or closed?).
- **Limits:** These are usually deployment-configured, not code bugs — a finding here may be "insecure default configuration" which many programs exclude. Check the program's accepted-risk list (T5) before investing.

## T11. Search-result metadata is an IDOR oracle: check whether metadata leaks past the access boundary

- **Technique:** On targets with search, verify two properties: (a) does search return objects the searcher shouldn't see (result-set boundary), and (b) does each result carry metadata (creator/userId, IDs) usable as an oracle for direct-object probing. Sequential numeric IDs + rich metadata = IDOR fuel.
- **When to use:** Any target exposing search over access-controlled objects.
- **What it found here:** Kiteworks search has no server-side owner filter (ownership filtered client-side), every result carries creator/userId, content search is folder-scoped but name search is tenant-wide, and file IDs are small sequential numerics (e.g. `id: 1240`) — the combination that powered the H1–H3 IDOR hypotheses (version-overwrite, Viewer-download bypass, activity-log ID swap).
- **Limits:** Metadata exposure alone isn't a finding — it only becomes one when it enables access beyond the intended boundary. Confirm the downstream access, not just the metadata.

## T12. Version-overwrite is an authorization seam distinct from upload validation

- **Technique:** Where a platform versions files on same-name re-upload, test the *new-version* path (`initiateUpload` on an existing file_id) separately from the *new-file* path. Versioning often reuses the upload handler but with a different (weaker) authorization check — the question is whether the caller needs edit rights on *that object* or merely membership in the container.
- **When to use:** File-sharing/collaboration targets with versioning.
- **What it found here:** `POST /rest/files/{file_id}/actions/initiateUpload` creates a new version of an existing file; the hypothesis (H1, agent #53) is that it checks folder membership but not per-object edit role — letting a Viewer/Downloader overwrite another user's file. Grounded in numeric IDs + same-name-versioning docs.
- **Limits:** Requires two controlled test accounts with distinct roles; the endpoint may correctly re-check. Also confirm the version actually replaces content served to others, not just metadata.

## T13. Fingerprint the SAML SP stack from integration docs, then inherit its CVE history

- **Technique:** Vendor/IdP integration guides (Entra ID, Okta tutorials) often leak the SP implementation via endpoint paths (e.g. `/sp/module.php/saml/...` = SimpleSAMLphp). Once identified, pull that stack's CVE history for signature-handling and XML-parsing bugs and test the ACS endpoint against them — you're testing the vendored library, not the app's code.
- **When to use:** Any target with documented SAML SSO setup guides.
- **What it found here:** The Entra SSO tutorial's ACS pattern `https://<host>/sp/module.php/saml/sp/saml2-acs.php/sp-sso` fingerprints a SimpleSAMLphp-based SP, inheriting its known vulnerability classes (assertion signature handling, XML parsing). Flagged as medium-confidence since the path is from a tutorial placeholder.
- **Limits:** Tutorial paths are often placeholders — verify the actual ACS path on the instance before testing. Also check whether the deployment pins a patched SimpleSAMLphp version; old CVEs on new versions are noise.

## T14. Sandbox DNS lies: validate resolver output against known-good external resolution

- **Technique:** If DNS answers look wrong (RFC 5737/1918/benchmark ranges like 198.18.0.0/15 for public names), treat the local resolver as compromised/sandboxed and switch to external DoH or the operator's network. Record which answers came from the tainted resolver so downstream agents don't build on them.
- **When to use:** Any recon in a sandboxed/egress-proxied environment.
- **What it found here:** `getent hosts` returned 198.18.92.35/36 (benchmarking range) for public hostnames while the world model recorded the real IP (3.0.1.193) via DoH — agent #3 correctly flagged all local-resolver results as sandbox artifacts.
- **Limits:** DoH itself may be blocked from the sandbox (it was here); have a fallback plan (operator-side resolution) rather than assuming DoH always works.

## T15. Mine historical CVEs for the *seam*, not the bug

- **Technique:** For each historical CVE on the target product, extract the *code seam* (upload validation, role-management input handling, session-on-disable, access-control on content) rather than the specific payload. The deployed version has the CVE patched — the value is in adjacent/variant logic at the same seam (different parameter, different transition, different role).
- **When to use:** Hypothesis generation on any product with a public CVE history.
- **What it found here:** CVE-2025-53939 (shared-folder role management elevation, pre-9.1.0) → variant hypotheses on role-id handling, downgrade-then-upgrade transitions, stale role caching in 9.5.1; CVE-2026-23636 (SDF dangerous-type upload) → non-rename upload-validation vectors; CVE-2026-29092 (sessions survive disable) → deprovisioning-transition tests.
- **Limits:** Vendors often fix the whole seam, not just the reported vector — several variants will come back clean. Time-box variant hunting; don't re-test the exact CVE payload expecting a different result.
