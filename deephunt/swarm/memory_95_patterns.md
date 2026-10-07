# Novel-Pattern Extraction — Swarm Agent #95 (Memory)
Date: 2026-09-27 | Sources: `hyp_novel.jsonl` (agents 66–79), `obs_diff.jsonl` (agents 32–44)
Target context: Kiteworks YesWeHack hunting environment (`ywh-kw-public.bounty.kiteworks.dev`)

Each pattern below is a structural idea that does not fit a standard vuln class
(XSS/SQLi/IDOR/open-redirect/etc.). Each is a reusable technique-card seed:
the pattern, where it was observed, why it is novel, and how to test for it elsewhere.

---

## Pattern 1 — Authorization frozen at mint time (lifecycle-state desync)
**The pattern:** Access decisions are captured once (share created, upload initiated,
download started, session issued) and never re-evaluated against live state.
Revocation/lifecycle events that should kill the capability don't propagate to it.

**Where observed:**
- Share-link authorization snapshot surviving LDAP role revocation (#73)
- Dormant share-capability desync: policy re-evaluation skipped per link access (#72)
- Chunked upload session surviving folder role demotion mid-upload (#67)
- Share revocation not terminating in-flight chunked/range downloads (#67)
- EPG letting blocked users keep active sessions (CVE-2026-29092, fixed 9.2.1 — proof the class exists in this codebase)

**Why novel:** Standard classes (IDOR, broken access control) test whether a *check*
is missing. This tests whether a check is *stale* — correct at creation, wrong at use.
It is not a race condition; it reproduces sequentially and deterministically.

**How to test elsewhere:** For any capability token (share link, upload session,
download stream, OAuth token, approval link): (1) mint it, (2) trigger the
revocation/demotion/expiry lifecycle event through a separate account, (3) keep
using the token and demand denial. The signal is a 200-after-revoke, not a 200-after-race.

## Pattern 2 — Same rule, divergent code paths (cross-path enforcement gap)
**The pattern:** One business rule (expiry, download budget, external-recipient
restriction, DLP enforcement) is implemented independently in N client paths
(web UI, REST API, mobile app, Outlook plugin, direct-download URL, preview
endpoint). One path enforces strictly; another is the weak path.

**Where observed:**
- Expired/download-exhausted link still serving via direct-download/preview path (#66)
- External-recipient domain restriction on share-link path but not secure-email path (#66)
- Approval endpoint validating "is an approver" instead of "is the CURRENT approver" (#66)
- Per-role client allow-listing (web/mobile/SFTP) meaning the same nominal role has different attack surfaces (#32)

**Why novel:** Testers typically pick one client and hammer it. This pattern says the
vulnerability lives in the *difference between clients*, so single-surface testing
systematically misses it. It is a coverage strategy, not a payload strategy.

**How to test elsewhere:** Enumerate every path that serves the same object
(share page, direct download, thumbnail/preview, API, mobile-equivalent, plugin).
For each, apply the same denial trigger (expire, exhaust budget, revoke, restrict
recipient) and require uniform denial. Any path that diverges is the finding.

## Pattern 3 — Split-verdict trust delegation (external verdict gaps)
**The pattern:** A security decision is delegated to an external verdict service
(ICAP server for DLP/ATP/CDR; MIP-label validation; AV engine). The decision,
the verdict cache, the audit record, and the per-path consumers drift apart in
time, state, or trust.

**Where observed:**
- AV cleared vs ICAP DLP verdict mismatch across share/email release paths (#68)
- Audit trail derived from connector-reported verdict rather than data-plane outcome (#72)
- DLP/ATP fail-open when the ICAP server is unreachable/errors (#79)
- New file version inheriting the prior version's cached clean ICAP verdict (#73)
- Cached ICAP verdicts keyed on file hash surviving "deletion" (#77)

**Why novel:** The weak point is neither the verdict logic nor the enforcement
logic — it is the *seam between the two*: caching keys, subscription models,
fail-open defaults, and audit derivation. Standard DLP/AV testing checks "does it
block X"; this checks "does the block hold across versions, paths, outages, and
the audit log."

**How to test elsewhere:** For any delegated verdict: (1) force the verifier
offline and test fail-open vs fail-closed; (2) change the object *under the same
identity* (new version, re-upload) and check for re-verdict; (3) compare the audit
log entry against the actual delivered outcome; (4) check each consumer path
subscribes to the same verdict source.

## Pattern 4 — Guard lives on one path only (endpoint-local invariant)
**The pattern:** A documented platform-wide security invariant ("users start with
zero privileges", "create_user strips admin roles", "only system admins promote")
is enforced in one code path (interactive endpoint) while parallel provisioning
paths (SSO JIT, LDAP sync, legacy auth) bypass it entirely.

**Where observed:**
- create_user admin-strip guard bypassed by SSO JIT and LDAP sync provisioning (#77)
- Zero-privilege start vs default-profile fallback on automated provisioning (#77)
- LDAP/SSO JIT attribute + missing admin-strip = first-login elevation (H-PRCHAIN-2, #76)
- Legacy HMAC-SHA1 signature auth possibly still minting tokens alongside modern OAuth (#74)

**Why novel:** The docs tell the truth — about the path they describe. The class is
*spec-path divergence*: the invariant is real on the documented path and absent on
sibling paths that construct the same object. Testing one provisioning path proves
nothing about the others.

**How to test elsewhere:** Map every path that creates/elevates the object (UI,
REST, SSO JIT, directory sync, legacy/compat flows, bulk import). For each, feed a
privileged input and check the same invariant. Never assume the guard is
platform-wide because it was observed once.

## Pattern 5 — User-controllable attribute feeds auto-assignment rules
**The pattern:** A user can edit their own profile attributes (department, title,
email alias); admin-defined mapping rules auto-assign privileges by matching those
attributes. The re-evaluation trigger (edit-time vs login-time vs sync-time) is
the seam — if self-edit re-triggers evaluation, self-service becomes promotion.

**Where observed:**
- Self-edit attribute + profile mapping rule = auto-promotion (H-PRCHAIN-1, #76)
- LDAP/SAML attribute→role mapping conflict between web UI and mobile/API sessions (#68)

**Why novel:** Neither side is a bug: self-edit is by design, mapping rules are by
design. The vulnerability is the *composition and its trigger condition* — a
workflow-ordering question, not a missing-access-control question.

**How to test elsewhere:** Find self-editable fields; find rules/policies that
match on them (profile mapping, group rules, label automation). Change the field
and check whether re-evaluation happens at edit-time, next-login, or never.
Test all three — the bug is in the timing, not the fields.

## Pattern 6 — Versioned-object lifecycle incompleteness
**The pattern:** The platform presents a file as one identity but stores it as
multiple addressable objects: versions, previews/thumbnails, search-index entries,
verdict caches, quarantine copies. Delete/replace operations cover the primary
pointer but leave derived objects reachable.

**Where observed:**
- Deleted file version remains addressable via its prior version address (#72)
- Link-expiry "files are deleted from the server" guarantee vs retained derived copies (#77)
- Same-name upload creating a new version (last-writer-wins, no concurrency token) (#41)
- Version replacement inheriting prior ICAP verdict (also Pattern 3) (#73)

**Why novel:** Deletion is usually tested as "can I still GET the file URL."
This pattern demands enumerating the *derived-object inventory* (preview,
thumbnail, index, cache, quarantine) and testing each addressability class
independently.

**How to test elsewhere:** After any delete/replace/expire action, enumerate every
derived representation of the object (rendered previews, thumbnails, search hits,
cached verdicts, backup/quarantine copies) and request each directly. Byte-level
absence everywhere — or it isn't deleted.

## Pattern 7 — Local machine treated as a single principal
**The pattern:** Security flows assume one person per machine: OAuth loopback
callbacks assume only the initiator can reach the port; bearer tokens assume the
holder is the enrolled device; remote wipe assumes the compromised client still
checks in.

**Where observed:**
- MCP localhost:9999 OAuth callback interceptable by a second local user (#70)
- Refresh tokens as plain bearer tokens with no device binding; remote wipe advisory-only (#69)
- MCP callback interception feeding AI Data Gateway RAG exfiltration (#73)

**Why novel:** The trust boundary is the *operating-system user model*, not a
documented feature — so nobody tests it. It inverts the usual network-attacker
model: the attacker is a co-tenant of the victim's host (terminal servers, CI
runners, shared jump boxes).

**How to test elsewhere:** For any localhost-callback OAuth flow: pre-bind the
port as a second local user, check for PKCE/state binding/random ports.
For any token: replay it from a second client fingerprint after remote-wipe/revoke
and demand 401. Assume nothing about holder identity from possession.

## Pattern 8 — Forgotten legacy shims (rebrand/acquisition debt)
**The pattern:** Rebrands (Accellion→Kiteworks) and acquisitions (123FormBuilder→
Secure Data Forms) leave legacy auth flows, version-negotiation headers, and
wrapped old endpoints active alongside the hardened modern surface. Old branches
don't receive new fixes.

**Where observed:**
- X-Accellion-Version header possibly still changing server behavior (#74)
- Legacy HMAC-SHA1 "Signature Authentication Method" possibly still minting tokens (#74)
- 123FormBuilder-era endpoints living inside Secure Data Forms (#74)
- SDF rearchitected storage vs 123FormBuilder (CVE-2026-24782 scored 9.4→7.6 — proof legacy vs modern diverge) (#44)

**Why novel:** This is archaeology, not fuzzing: the attack surface is found in
old docs, old brand headers, and acquisition history — inputs standard discovery
never generates because it doesn't know the product's past.

**How to test elsewhere:** Research the product's rebrand/acquisition history.
Send legacy brand headers, legacy auth-code formats, legacy URL patterns from old
docs. The signal is *any* differential behavior (not just success) — a legacy
path that responds differently is a candidate old code branch.

## Pattern 9 — Who guards the guards (delegated-admin trust inversion)
**The pattern:** In governance/compliance products, the audit trail and the
credential lifecycle of privileged accounts are the real crown jewels — and they
are the least-tested negative space. Delegated admins may be able to purge the
audit evidence of their own abuse or reset the credentials of admins above them.

**Where observed:**
- Delegated admin roles altering/purging audit events (#79)
- Delegated admins resetting credentials/2FA of system admins (#79)
- Admin Console vs web app activity surfaces (audit data partitioned by role) (#34)

**Why novel:** Privilege-escalation testing studies promotion paths *upward*.
This studies credential and audit actions *downward/laterally*: who can touch the
accounts and records that constrain them. In a compliance product, the audit store
is the product — its mutability is a first-class finding, not a misconfiguration.

**How to test elsewhere:** With delegated-admin scope: (1) attempt audit
delete/edit/purge and retention-policy changes; (2) attempt password/2FA resets on
accounts at or above your level; (3) check whether retention locks require a
higher tier. Demand append-only, tier-gated answers.

## Pattern 10 — Security metadata lost at feature-boundary crossings
**The pattern:** A document's protection state (MIP sensitivity label, RMS
protection, DLP classification) is enforced in the pipeline that received it
(email gateway) but stripped or ignored when the document crosses into another
feature (share links, connector sync to SharePoint/Drive/Box, version replacement).

**Where observed:**
- MIP label consumed by EPG policy but ignored in share-link/connector path (#68)
- Forged/downgraded MIP label + ICAP-delegated verdict = EPG policy bypass (H-EGCHAIN-3, #76)

**Why novel:** DLP is usually tested within one pipeline. This tests *label
fidelity across pipelines*: the same bytes, re-homed in a new feature, shed the
policy context that governed them. The fix isn't a rule change — it's carrying
the metadata across the boundary.

**How to test elsewhere:** Introduce a labeled/protected object through pipeline
A (email gateway, upload), then move it through every other egress feature
(share link, connector sync, secure email, version replace, form attach).
At each step, check the label/RMS/classification is intact AND the policy verdict
matches pipeline A's verdict.

## Pattern 11 — Identity-string seam (app comparison vs infrastructure normalization)
**The pattern:** The app enforces uniqueness with one string semantics
(case-sensitive, un-normalized) while the infrastructure that *delivers* on that
identity (SMTP routing, directory matching) normalizes differently — yielding two
accounts for one mailbox, or one mailbox claimed by two parties.

**Where observed:**
- Case-sensitive email uniqueness vs case-insensitive mail routing → two accounts, one inbox (#70)
- SAML attribute vs LDAP attribute role-mapping conflict: two identity sources, one user, divergent privilege (#68)

**Why novel:** Each layer is individually correct; the bug is in the *contract
between layers*. It is found by reading two specs (app uniqueness rules + mail
routing rules) side by side, not by testing either in isolation.

**How to test elsewhere:** For any email-as-identity system: register case
variants, Unicode-normalization variants, and plus-addressed variants of an
owned address; then test where password-reset tokens land. Any divergence
between "account identity" and "mailbox identity" is the finding.

## Pattern 12 — License-classification doubling as access control
**The pattern:** A billing construct (Internal vs External, Licensed vs
Nonlicensed) gates features — and the classification itself is mutable by
ordinary user actions (receiving a Collaborator folder role flips a user to
Licensed). A state change in licensing silently changes the attack surface.

**Where observed:**
- External User becomes Licensed when granted Collaborator/Manager/Owner in one folder (#32)
- Role-based client allow-listing (web/mobile/SFTP) per role (#32)
- Guest users: no personal space, uploads owned by the sharer, quota is sharer's (#32)

**Why novel:** License checks are assumed to be a billing concern. Wherever
billing classification drives capability, a classification *transition* is a
privilege transition — and the code that flips it is rarely hardened like an
auth check.

**How to test elsewhere:** Map every rule that changes a user's billing/license
tier; trigger the transition with owned accounts; diff the feature surface
before and after. Test whether the tier change propagates to all enforcement
points (API, mobile, SFTP) or only some.

---

## Technique-card seeds (deduplicated, for card creation)
1. `lifecycle-desync` — mint capability, trigger revoke/demote/expire, reuse. (P1)
2. `cross-path-enforcement-diff` — same rule across all clients/paths, demand uniform denial. (P2)
3. `delegated-verdict-seam` — verifier offline, version replace, audit-vs-reality. (P3)
4. `endpoint-local-guard` — every provisioning path must honor the invariant. (P4)
5. `self-edit-triggered-rule` — self-editable attribute × auto-assignment rule × trigger timing. (P5)
6. `derived-object-inventory` — delete means byte-level absence everywhere. (P6)
7. `loopback-callback-shared-host` — PKCE/state/random-port on localhost OAuth; token replay post-wipe. (P7)
8. `legacy-shim-archaeology` — old brand headers, old auth flows, acquired-product URLs. (P8)
9. `guards-of-guards` — delegated admin vs audit store and admin credential lifecycle. (P9)
10. `label-fidelity-across-pipelines` — protection metadata must survive feature crossings. (P10)
11. `identity-string-seam` — app uniqueness semantics vs infrastructure normalization. (P11)
12. `license-tier-as-authz` — billing-classification transitions are privilege transitions. (P12)

---

## Summary
Twelve structural patterns extracted from 39 novel hypotheses and 63 differential
observations; the dominant meta-pattern is **state captured once and trusted
forever** (lifecycle desync, frozen guards, cached verdicts, stale capabilities).
All twelve are composition or boundary bugs — no single feature is broken alone —
and each has a deterministic, sequential test that needs no race and no exploit.
Top technique-card candidates: lifecycle-desync, delegated-verdict-seam, and
endpoint-local-guard, each with a falsifier that fits the ResearchSession workflow.
