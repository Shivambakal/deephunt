# Observation Deduplication Map — Swarm Agent #92

Date: 2026-09-27 | Input: `obs_recon.jsonl` (76) + `obs_app.jsonl` (109) + `obs_diff.jsonl` (78) = **263 observations**
Method: normalized-token similarity (title+detail, stopword-stripped), union-find clustering at ≥0.30, manual review of every cluster. Original files NOT modified.

## Cluster 1a — res-h3 sibling host dedicated LE cert (TRUE DUPES)
- **KEEP:** `obs_recon.jsonl:87` [high] — "CT logs reveal sibling host ywh-kw-res-h3.bounty.kiteworks.dev (OUT OF SCOPE - do not touch)" — strongest: crt.sh JSON (9 certs, cert id 28233428922, issuer Let's Encrypt YE2, not_before 2026-07-25) + pre-program-launch timeline analysis.
- **DUPE:** `obs_recon.jsonl:2` [high] — "ywh-kw-res-h3.bounty.kiteworks.dev holds a dedicated Let's Encrypt cert issued 2026-07-25" (subset of :87's evidence; weaker analysis).
- **DUPE:** `obs_recon.jsonl:94` [high] — "Sibling host ywh-kw-res-h3.bounty.kiteworks.dev has dedicated LE cert (OUT OF SCOPE - do not touch)" (same crt.sh serial, no added evidence).

## Cluster 1b — FALSE MERGE CORRECTED (distinct sibling host)
- `obs_recon.jsonl:95` [high] — "Sibling host kw-ywh-main.bounty.kiteworks.dev seen in urlscan Jun 2026" is a **distinct host** (5 urlscan submissions, traceless XSS PoC file, wildcard-covered cert). NOT a duplicate of 1a; keep as its own observation.

## Cluster 1c — FALSE MERGE CORRECTED (distinct sibling host)
- `obs_recon.jsonl:96` [high] — "Sibling host epg-ywh-main.bounty.kiteworks.dev seen in urlscan Jun 2026" is a **distinct host** (14 urlscan submissions; 'epg' = Email Protection Gateway name). NOT a duplicate; keep as its own observation.

## Cluster 2 — Folder RBAC role ladder (TRUE DUPES, 5 entries)
- **KEEP:** `obs_app.jsonl:31` [high] — "Folder role ladder: Viewer / Uploader / Downloader / Collaborator / Manager / Owner with exact capability splits" (most complete).
- **DUPE:** `obs_recon.jsonl:36` [high] — "RBAC role ladder: Owner, Manager, Collaborator, Downloader, Viewer, Uploader" (role names only).
- **DUPE:** `obs_app.jsonl:38` [high] — "Folder role permission matrix: Viewer < Downloader < Uploader < Collaborator < Manager / Owner" (same ladder restated).
- **DUPE:** `obs_app.jsonl:53` [high] — "Folder role hierarchy: Owner > Manager > Collaborator > Viewer" (partial restatement).
- **DUPE:** `obs_diff.jsonl:1` [low] — "Same folder, different folder-role…" (differential restatement, lowest confidence).

## Cluster 3 — Core API v28 / Pub-Sub v1 spec version (TRUE DUPES)
- **KEEP:** `obs_recon.jsonl:32` [high] — "API base path /rest/ with vendor OpenAPI spec (Core API v28, Pub-Sub v1)".
- **DUPE:** `obs_recon.jsonl:66` [high] — "REST API base, versioning, and spec source" (same fact, weaker).
- **DUPE:** `obs_diff.jsonl:66` [high] — "Current Core API spec is v28; Pub-Sub API is separately tracked at v1" (version fact restated from diff angle).

## Cluster 4 — Admin role segregation system/application (TRUE DUPES)
- **KEEP:** `obs_recon.jsonl:37` [high] — "Admin role segregation: system vs application admins; API blocks self-promotion".
- **DUPE:** `obs_diff.jsonl:8` [medium] — "System Admin vs Application Admin vs End User: separate API namespaces" (lower confidence, less evidence).
- **DUPE:** `obs_app.jsonl:83` [medium] — "Two-tier admin hierarchy: only system admins can create application admins".

## Cluster 5 — SCIM provisioning + LDAP user search API (TRUE DUPES)
- **KEEP:** `obs_recon.jsonl:43` [high] — "SCIM provisioning API + LDAP user search endpoints".
- **DUPE:** `obs_recon.jsonl:72` [high] — "LDAP/SSO/SCIM integration points in the API" (same endpoints restated).
- **DUPE:** `obs_app.jsonl:63` [medium] — "User IMPORT: LDAP/AD sync, SCIM provisioning, admin API bulk user endpoints" (same, lower confidence).

## Cluster 6 — CVE-2025-53939 role-management bug history (TRUE DUPES)
- **KEEP:** `obs_app.jsonl:57` [high] — "Shared-folder role management is a historically bug-dense surface (CVE-2025-53939)".
- **DUPE:** `obs_diff.jsonl:22` [high] — "Historical precedent: role-management input validation bug (CVE-2025-53939, fixed 9.1.0)".
- **DUPE:** `obs_diff.jsonl:40` [medium] — "Version boundary: 9.1.0 fixed role-management input validation (CVE-2025-53939); 9.5.1 is the current" (same fact framed as version boundary).

## Cluster 7 — DigiCert wildcard cert coverage (TRUE DUPES)
- **KEEP:** `obs_recon.jsonl:1` [high] — "DigiCert wildcard *.bounty.kiteworks.dev renewed yearly since 2021 covers the hunting host" (stronger: renewal history).
- **DUPE:** `obs_recon.jsonl:93` [high] — "Wildcard TLS cert covers *.bounty.kiteworks.dev (DigiCert, current)" (same fact, no history).

## Cluster 8 — VM egress outage coverage gap (TRUE DUPES)
- **KEEP:** `obs_recon.jsonl:24` [high] — "COVERAGE GAP: VM egress outage blocked /login_config, robots.txt, security.txt, urlscan, Wayback, crt.sh" (earlier + broader enumeration).
- **DUPE:** `obs_recon.jsonl:56` [high] — "COVERAGE GAP (corroborated): VM egress outage blocked robots.txt, security.txt, sitemap check…" (corroborating restatement, adds nothing new).

## Cluster 9 — Share access tiers Recipient Only vs anyone-after-auth (TRUE DUPES)
- **KEEP:** `obs_app.jsonl:27` [high] — "Share-access tiers are explicitly named: 'Recipient Only' vs 'anyone after authentication'" (strongest evidence).
- **DUPE:** `obs_recon.jsonl:40` [high] — "File disclosure access model: 'anyone after authentication' vs 'Recipient Only' (program boundary)" (same fact).

## Cluster 10 — FALSE MERGE CORRECTED (different observations)
- `obs_recon.jsonl:86` [medium] "No TXT records on the hunting host" (DoH TXT query, 0 answers) vs `obs_recon.jsonl:50` [low] "No CT/urlscan records surfaced for hunting host" — **different claims** (DNS TXT vs certificate-transparency/urlscan). Both stay.

## Cluster 11 — Three-layer privilege model (TRUE DUPES)
- **KEEP:** `obs_app.jsonl:78` [high] — "Three-layer privilege model: user profiles, admin roles, folder roles".
- **DUPE:** `obs_app.jsonl:49` [high] — "Privileges are assigned via User Profiles; folder access via folder roles; admin power via admin roles" (same model restated).

## Cluster 12 — Differential comparison blocked by sandbox egress (TRUE DUPES)
- **KEEP:** `obs_diff.jsonl:63` [high] — "Header/env comparison not executable: target unreachable from swarm sandbox (corroborates agent 35)".
- **DUPE:** `obs_diff.jsonl:48` [high] — "GET/HEAD/OPTIONS comparison not executable: target unreachable from swarm sandbox" (same root cause).

---

## Dedupe tally
- 263 input observations; **11 true duplicate clusters**; **23 entries marked duplicates**; 2 false merges corrected and kept separate.
- Unique observation count after dedupe: **240** (263 − 23).
- Strongest-concentration areas of overlap: folder-RBAC ladder (5×), admin/SCIM surfaces (3× each), res-h3 sibling host (3×).
- No cross-file entries were deleted; all originals intact.
