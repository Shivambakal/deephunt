# DEEPHUNT Wave 1 — Historical web/API cases (2025–2026)

Real incidents and disclosures only. Each case: what happened, why scanners missed it, and the DEEPHUNT lesson. Research-only; no live probing performed.

---

## Case 1 — React2Shell: unauthenticated RCE in Next.js via RSC prototype pollution (CVE-2025-55182, Dec 2025)

**What happened.** The React Server Components handler in Next.js (e.g. 15.0.3) processed the `Next-Action` header without adequate sanitization. An attacker injected a crafted Flight-protocol payload that exploited prototype pollution plus unsafe deserialization, achieving unauthenticated remote code execution on the Node server. Public exploits circulated within days and mass scanning followed.

**Why scanners missed it.** The vulnerable surface was a single HTTP *header* driving a framework-internal deserialization protocol — invisible to crawlers, with no CVE signature at scan time and no obviously "injectable" parameter. SAST/DAST tools model routes and params, not framework wire protocols.

**DEEPHUNT lesson.** Fingerprint framework + version first, then probe framework-protocol inputs (headers like `Next-Action`, RSC flight bodies) with benign evaluation oracles. Never rely on CVE feeds for zero-day-window framework bugs. (Card W1-036.)
Sources: https://github.com/aliakbar-babayev/htb-reports/blob/HEAD/Manual-WriteUps/Reactor/README.md

---

## Case 2 — WSO2 API Manager JWT fail-open (CVE-2026-5430, exploited Sep 2026, CVSS 9.8–10.0)

**What happened.** WSO2 API Manager's token validator failed to strictly enforce the configured signing algorithm: JWTs bearing *unsupported* algorithms were accepted instead of rejected. Attackers minted `sub: admin` tokens with full API-management scopes — no credentials needed. watchTowr's honeypots captured forged admin JWTs on Sep 13, 2026, four months after the patch shipped; CISA KEV-listed it with a Sep 27 federal deadline. The gateway is an aggregation point, so compromise exposed backend URLs, consumer keys/secrets, and OAuth token stores.

**Why scanners missed it.** Scanners test `alg:none` and RS256→HS256, but rarely fuzz *unknown/garbage* algorithm strings — the fail-open branch. And API gateways are assumed hardened, so the management plane gets less adversarial testing than the apps behind it.

**DEEPHUNT lesson.** Always run the full algorithm-confusion matrix including unknown, empty, and case-variant `alg` values (fail-open hunting), and treat the gateway/management plane as a first-class target. (Cards W1-011, W1-012.)
Sources: https://forkast.news/wso2s-cvss-10-0-jwt-bypass-has-been-exploited-for-12-days-the-patch-has-been-out-since-april/ · https://threatseye.io/blog/wso2-api-manager-jwt-bypass-under-active-exploitation-forged-admin-tokens-hit-ho

---

## Case 3 — The 2025 desync wave: Expect-header trick hits Akamai, T-Mobile, Cloudflare

**What happened.** James Kettle's "HTTP/1.1 Must Die" research introduced CL.0/0.CL variants and the `Expect: 100-continue` trick, which open desync on links with no CL+TE conflict at all. Real payouts followed: Akamai (CVE-2025-32094, $9,000, potential large-scale credential theft), T-Mobile non-prod ($12,000, internal systems access), Cloudflare CDN ($7,000, redirecting protected sites' visitors), GitLab ($7,000), Netlify (undisclosed). CDN-level desync meant one edge flaw affected every customer behind it.

**Why scanners missed it.** WAF and scanner signatures were built for classic CL.TE/TE.CL. The new variants need no TE header, so "reject CL+TE together" mitigations were no-ops, and Expect-triggered framing changes were outside every detection model.

**DEEPHUNT lesson.** Probe 0.CL/CL.0 and the Expect trick on *every* CDN-fronted target as a standing check, and treat CDN-edge desync as a multi-tenant blast radius, not a single-app bug. (Cards W1-001, W1-002.)
Sources: https://github.com/guan4tou2/bug-bounty-vault-framework/blob/HEAD/09%20-%20Knowledge%20Base/Pattern%20-%20HTTP%20Request%20Smuggling%20Modern%20Variants.md · https://github.com/aw-junaid/bug-bounty/blob/HEAD/resources/cheatsheets/HTTP%20Request%20Smuggling.md

---

## Case 4 — Figma zero-click RCE via a prototype-pollution chain (Apr 2026, DavenSec)

**What happened.** Researcher Benjamin Mamoud found prototype pollution in Figma's variant counter — alone, just a crash. He chained it: let the plugin context survive the main-context crash, won a race against `$INTERNAL_DO_NOT_USE$RERUN_PLUGIN$`, flipped the `jsx_debugging` feature flag to unlock a *second* prototype pollution in `figma.jsx.deserialize`'s expression evaluator, turned a polluted `errorHandler` gadget into XSS, and rode a forgotten `writeFileToPath` IPC in the Electron desktop app to cross-platform zero-click RCE from a published plugin. Figma patched within hours.

**Why scanners missed it.** No scanner chains primitives across trust boundaries (web plugin sandbox → desktop IPC), and nobody's model includes "win a race against an internal rerun function, then flip a feature flag." Each link looked benign alone.

**DEEPHUNT lesson.** Treat every primitive (crash, pollution, flag, IPC) as a chain link, not a dead end; explicitly hunt race windows that convert crashes into footholds and forgotten IPCs that convert XSS into RCE. (Cards W1-022, W1-024, W1-031.)
Source: https://github.com/criticalthinkingpodcast/criticalthinkingpodcast.github.io/blob/HEAD/writeups/articles/WriteupNo0006/post.md

---

## Case 5 — Authlib trio: JWT forgery + padding oracle in 86M-download OAuth library (2026)

**What happened.** Three critical flaws in Authlib (Python's dominant OAuth/OIDC library): CVE-2026-28490 (CVSS 8.3) — RSA1_5 handling raised a distinguishing `ValueError` before validation, creating a clean exception oracle for padding-oracle decryption, active by default across Flask/Django/FastAPI; CVE-2026-28498 (CVSS 8.2) — unrecognized JWT `alg` silently returned `True`, bypassing ID-token integrity; CVE-2026-27962 (CVSS 9.1) — JWT signature verification bypass enabling arbitrary token forgery.

**Why scanners missed it.** Supply-chain trust: the vulnerability was *inside* the library everyone delegated crypto to, and the padding oracle lived in exception-type differences between HTTP responses — a signal DAST tools don't correlate.

**DEEPHUNT lesson.** Version-fingerprint auth libraries as a standing check, and probe crypto failure paths for distinguishable oracles (error-type, timing, message differences). Fail-open beats crypto every time — test it first. (Cards W1-011, W1-043-ish timing.)
Source: https://securityonline.info/broken-keys-critical-authlib-flaws-jwt-forgery-padding-oracles/

---

## Case 6 — MySQL Router MRS OAuth cached display-name account takeover (Aug 2026)

**What happened.** MySQL Router's REST Service cached OAuth users by `vendor_user_id`, but on a cache miss it scanned all cached users and treated an *email or display-name match* as an identity hit. Display names are mutable on every major provider. An attacker set their display name to the victim's, logged in, and inherited the victim's internal `user_id`, privileges, groups, and session state — the victim's DB row was permanently rebound to the attacker. Verified end-to-end from a clean deployment.

**Why scanners missed it.** The flaw was identity-resolution logic deep in C++ (`UserManager::cache_get`), invisible to HTTP-level scanning; no parameter looked injectable, and the "vulnerability" was a *correct-looking* fallback comparison.

**DEEPHUNT lesson.** Test identity binding with mutable attributes: create two accounts differing only in display name/email, and check which internal identity the session carries. Immutable `sub` must be the only identity key. (Card W1-017.)
Source: https://github.com/unrealisedd/exploitarium/blob/HEAD/mysql-router-mrs-oauth-cached-name-ato-poc/README.md

---

## Case 7 — Keycloak client-initiated account-linking hash forgery (CVE-2026-15571, CVSS 7.3)

**What happened.** The deprecated `/realms/{realm}/broker/{alias}/link` endpoint protected account linking with a SHA-256 digest over `nonce + userSessionId + clientId + providerAlias` — with no keyed MAC, no server secret, and no server-generated token. Every input was attacker-known (nonce chosen by caller, session id handed to every OIDC client as `session_state`). Anyone controlling a registered OIDC client could forge a linking URL binding their external identity to a victim's account: full ATO via the attacker's IdP credentials.

**Why scanners missed it.** The endpoint was deprecated (out of the tested surface), and "SHA-256 integrity hash" *looked* like a real control — scanners don't audit whether hash inputs include a server secret.

**DEEPHUNT lesson.** Audit deprecated/legacy endpoints explicitly, and for every "integrity hash" verify the preimage includes a server-side secret. Deprecated ≠ disabled. (Card W1-014.)
Source: https://github.com/1dayexploit/1day-archive/blob/HEAD/analyses/cve-2026-15571-keycloak-account-linking-auth-bypass/README.md

---

## Case 8 — GraphQL mutation aliasing DoS on account recovery (HackerOne 3287208, $12,500, disclosed 2026-04-16)

**What happened.** A GraphQL account-recovery flow allowed mutation aliasing: one HTTP request carried a huge batch of aliased phone-number mutations, each counting as a separate operation. Rate limiting was applied per HTTP request, not per operation, so the batch sailed through — denial of service against the recovery pipeline (and the same primitive enables OTP brute-forcing and SMS bombing).

**Why scanners missed it.** Rate-limit testing sends N sequential requests; the bypass needs *one* request with N aliased operations — a shape most scanners never generate. The endpoint "had rate limiting," so it was marked safe.

**DEEPHUNT lesson.** Always test alias/batching multiplication against rate-limited mutations: count real side effects per HTTP request, not requests per window. (Card W1-021.)
Source: https://github.com/ajaysenr/hackerone-disclosed-reports/blob/HEAD/by-year/2026.md

---

## Case 9 — WordPress Gutenberg media-finalize arbitrary file deletion (HackerOne 3931777, CVSS 9.9, disclosed 2026-08-28)

**What happened.** `POST /wp/v2/media/<id>/finalize` wrote attacker strings verbatim into `_wp_attachment_metadata` (no sanitize callback, no basename check). The `$backup_sizes` branch of `wp_delete_attachment_files()` derived *both* the file to delete *and* the confinement directory from the attacker-controlled `file` key — so the containment check compared the target against an attacker-chosen directory and became a no-op. Any Author could delete any file the PHP process could unlink: site takeover.

**Why scanners missed it.** The flaw lived in a REST API meta-key trust chain across two functions (`wp_ajax_image_editor` populating backup sizes, the deleter consuming them). Scanners test direct path traversal in filenames, not metadata-mediated containment bypasses where the guard itself is fed attacker input.

**DEEPHUNT lesson.** Trace attacker-controlled metadata into filesystem operations, and verify containment uses *server-derived* paths — any guard computed from attacker input is suspect. (Cards W1-035-adjacent; new card candidate: metadata-mediated path traversal.)
Source: https://github.com/ajaysenr/hackerone-disclosed-reports/blob/HEAD/reports/3931777.md

---

## Case 10 — Loyalty-wallet race: duplicating money with one promo code ($15,000, Jun 2026)

**What happened.** A GlobalAir loyalty wallet allowed a single low-value promotional code to be redeemed concurrently. The check-then-act sequence ran without row locking, so parallel redemptions all passed validation and money was duplicated out of thin air. Triaged Critical (P1) within 2.5 hours; fixed with `SELECT ... FOR UPDATE` pessimistic locking; $15,000 bounty.

**Why scanners missed it.** Functional tests never send concurrent requests. The race window needed HTTP/2 single-packet timing to hit reliably — beyond Burp Repeater's default parallelism and beyond every DAST crawler.

**DEEPHUNT lesson.** Every balance/coupon/inventory/token mutation gets a single-packet race probe as a standing check, and the oracle is always the *server-side state diff* — never the response codes. (Cards W1-031, W1-032.)
Source: https://medium.com/@21bec131/how-a-race-condition-in-a-loyalty-wallet-scored-a-15-000-critical-payout-a44e36d05825

---

## Case 11 — NetScaler CVE-2026-19490: pre-auth auth bypass whose blast radius is pure configuration (Sep 2026, Bishop Fox)

**What happened.** A single unauthenticated request bypassed authentication on NetScaler Gateway/AAA virtual servers with SAML configured (CVE-2026-19490). Bishop Fox showed the *bug* never changed — the *configuration* decided everything: an AAA vserver bounded it to a dead-end anonymous session, a Gateway vserver turned it into a real session, and `-defaultAuthorizationAction` decided whether that session proxied into the internal network and the management plane (weak management password → root on the appliance).

**Why scanners missed it.** Vulnerability scanners flag the CVE; they don't map the configuration branches that decide whether it's a dead end or domain-wide compromise. Most "verified vulnerable" reports stopped at the version check.

**DEEPHUNT lesson.** For every auth-bypass primitive, enumerate the configuration branches (vserver type, default actions, downstream stores) that amplify or bound it — the blast-radius map is part of the finding, not an afterthought. (Card W1-010 followups.)
Source: https://bishopfox.com/blog/mind-the-config-detecting-and-weaponizing-netscaler-cve-2026-19490
