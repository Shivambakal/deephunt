# Link Study — Batch 00 (31 URLs)

Read-only research. Fetched 2026-09-26. No exploitation, logins, or fuzzing performed.
Platform brief pages (Bugcrowd/Intigriti) were read for scope, rules, and focus areas.

---

## HIGH-VALUE LEADS (top 5)

1. **Aiven runs a sanctioned exploit sandbox.** The brief names `falcon-bug-bounty-flag-pgsql-dev-sandbox.e.aivencloud.com` as a challenge target where the report must include the server's `/etc/ssh/ssh_host_ed25519_key`, its external IP, and the method used — i.e. full exploit-chain testing is explicitly authorized on managed DB services. Cross-account access and internal-network pivot are called out as top priorities. → Start here: spin up free-tier services, hunt cross-account IDOR and internal-service exposure.
2. **OneTrust gives admin creds on a staging target.** All testing must happen on `pentest-app.onetrust.com` (other envs = ineligible); the brief hands out admin-level credentials. Focus areas: Consumer Rights Portal webforms/workflows (data exfiltration) and the Integrations module (pulling customer data out of customer environments). Public API-key disclosure was just moved in scope. → Authenticated IDOR/data-exfil testing in DSR webforms with the provided admin account.
3. **Proxmox VE 7.0–8.0.3 has a single-request unauthenticated root auth bypass (CVE-2023-54391).** `POST /api2/json/access/ticket` with `username=root@pam&password=x&tfa-challenge=1` mints a full root ticket; exploitation in the wild reported; EOL installs still exposed. → Add to hunter fingerprints: probe `:8006/api2/json/access/ticket` on any Proxmox instance found during recon (detection only — check 200 vs 401).
4. **Okta's brief names SSRF-via-Workflows-Flo-cards as an explicit focus area**, plus cross-org data access, XXE in XML-heavy endpoints, and SAML/OAuth/OIDC protocol bugs. Test orgs live at `bugcrowd-<username>.oktapreview.com`; automation is strictly banned (instant removal). → Manual-only: Flo-card SSRF and cross-org visibility on your own test org.
5. **Pinterest's new AI features are explicitly flagged for testing with low dupe rates** (Pinterest Assistant, AI Board Upgrades, GenAI Interest Settings), with a published P1–P4 grid ($10–25K / $5–8K / $1–3K / $200–500). Recent accepted reports on `api.pinterest.com` (Sep 17) and `github.com/pinterest` OSS (Sep 25) prove both surfaces pay. → Enroll a v5 API developer app and audit Pinterest Ads / Private Profiles; static-audit their OSS repos.

---

## 1. http://supplyota.agoda.com/b
- **WHAT:** Agoda supplier-portal host (`supplyota.agoda.com`) — returns HTTP 403 on `/b` (alive, WAF/filtered).
- **ATTACK SURFACE:** Host confirmed live; 403 suggests path-based or header-based filtering rather than a dead host.
- **ACTIONABLE LEAD:** In-scope via `agoda.com` root. Probe `/` and common supplier paths with the researcher UA; compare 403 vs 404 vs 200 to map the filter, then run the hunter `vuln` fingerprint set against it.

## 2. https://*/*.
- **WHAT:** Malformed/truncated URL from notes — not fetchable.
- **ATTACK SURFACE:** None.
- **ACTIONABLE LEAD:** None — dropped.

## 3. https://app.intigriti.com/programs/bmw/bmwgroup/detail
- **WHAT:** Intigriti program detail page (BMW Group). Renders marketing shell only without login — no program data accessible anonymously.
- **ATTACK SURFACE:** None extractable; scope/rules live behind researcher login.
- **ACTIONABLE LEAD:** Covered in `intel/programs-intigriti-yeswehack.md`. Needs Shivam's logged-in Intigriti session (browser) to pull live scope.

## 4. https://app.intigriti.com/programs/intigriti/intigriti/detail
- **WHAT:** Intigriti's own program page — same login wall as above.
- **ATTACK SURFACE:** None extractable anonymously.
- **ACTIONABLE LEAD:** See dossier; the PWN environment details (up to €13,337) require login.

## 5. https://app.intigriti.com/programs/oda/oda/detail
- **WHAT:** Intigriti program page (Oda) — explicitly returns "Forbidden: You don't have access to this page" (private/invite-only or login-required).
- **ATTACK SURFACE:** None extractable.
- **ACTIONABLE LEAD:** See dossier; Oda allows max 5 req/sec manual-style testing once registered.

## 6. https://app.intigriti.com/programs/personio/personio/detail
- **WHAT:** Intigriti program page (Personio) — marketing shell only without login.
- **ATTACK SURFACE:** None extractable.
- **ACTIONABLE LEAD:** See dossier; needs logged-in session.

## 7. https://app.intigriti.com/programs/suivo/suivoweb/detail
- **WHAT:** Intigriti program page (Suivo) — "Forbidden" like Oda.
- **ATTACK SURFACE:** None extractable.
- **ACTIONABLE LEAD:** See dossier; needs logged-in session.

## 8. https://app.intigriti.com/programs/truelayer/truelayer/detail
- **WHAT:** Intigriti program page (TrueLayer) — marketing shell only without login.
- **ATTACK SURFACE:** None extractable.
- **ACTIONABLE LEAD:** See dossier; TrueLayer permits light automation (10 req/sec) with `X-Intigriti-Username` header after registration.

## 9. https://blog.calif.io/p/the-wordpress-chain-massacre
- **WHAT:** "The WordPress Chain Massacre" (Aug 2026) — full wp2shell → wp2root chain: pre-auth WordPress RCE → PHP Serializable UAF → self-resolving ROP → memfd fileless exec → "Copy Fail" kernel LPE → root.
- **ATTACK SURFACE:** WordPress REST batch route confusion → pre-auth SQLi → forged `WP_Post` objects → admin + plugin upload (wp2shell, AssetNote). Post-exploit: PHP `Serializable` unserialize UAF (unfixed), `memfd_create` + `execveat(AT_EMPTY_PATH)` fileless staging, page-cache overwrite of setuid binaries.
- **ACTIONABLE LEAD:** Any WordPress target in scope: check version/plugin surface for wp2shell-style REST batch abuse first (detection: does `/wp-json/` batch endpoint exist and accept unauthenticated requests?). Add wp2shell-version fingerprint is already in hunter — extend it with REST-batch reachability check.

## 10. https://blog.devploit.dev/posts/google-messages-avatarcontentprovider (404)
- **WHAT:** Original URL 404s; the live post is at `/posts/google-messages-avatarcontentprovider-contacts-bypass/` (see #19).
- **ATTACK SURFACE:** — / **ACTIONABLE LEAD:** See #19.

## 11. https://blog.himanshuanand.com/posts/pwn-v8 (404)
- **WHAT:** Dead link — returns 404.
- **ATTACK SURFACE:** None. / **ACTIONABLE LEAD:** None — dropped.

## 12. https://blog.nathangolez.com/
- **WHAT:** Security blog homepage (Nathan Golez). Recent posts include a Proxmox VE auth-bypass writeup (see #18).
- **ATTACK SURFACE:** Blog index only.
- **ACTIONABLE LEAD:** The Proxmox post (#18) is the high-value item; also watch this blog for future vuln writeups.

## 13. https://blog.sentry.security/beyond-prompt-injection-hacking-apples-private-cloud-compute/
- **WHAT:** Sentry SARC writeup of CVE-2026-20685 ($150,000 Apple bounty) — path traversal in `darwin-init`'s `extract(to:)` during PCC node boot: tar entries with `../../../../db/...` escape the cryptex extraction dir and get written as root to the persistent `/var/db/` volume; chained with `splunkloggingd` config overwrite to exfiltrate inference telemetry.
- **ATTACK SURFACE:** Archive-extraction path traversal (libarchive without security flags), empty `validate(cryptexConfig:)` stub, optional SHA-256 digest on cryptexes, LaunchDaemon `PathState` KeepAlive on attacker-writable plist.
- **ACTIONABLE LEAD:** Pattern to reuse on bounty targets: any file-upload/archive-import feature (ZIP/tar restore, backup import, theme/plugin upload) → test `../` traversal in entry names and check whether extracted files land outside the intended dir. Relevant to Agoda/Booking partner-upload surfaces.

## 14. https://blog.teknogeek.io/posts/what-happened-to-hackerone/
- **WHAT:** "What Happened to HackerOne?" (Aug 2026) — insider history of HackerOne's decline: VC-driven sales focus, triage quality collapse, HSP creating a lopsided playing field for new hackers, AI-era report spam.
- **ATTACK SURFACE:** None technical — platform meta.
- **ACTIONABLE LEAD:** Strategic, not technical: HackerOne triage is noisy and new-researcher-hostile → prioritize Bugcrowd/Intigriti/YesWeHack programs where response is better, and make every H1 report (e.g. Agoda, Booking.com) airtight with full PoC + impact to survive weak triage.

## 15. https://blog.viettelcybersecurity.com/sharepoint_cve- (truncated)
- **WHAT:** Truncated URL from notes — not fetchable as-is.
- **ATTACK SURFACE:** None. / **ACTIONABLE LEAD:** None — dropped. (Hunter already has SharePoint fingerprints.)

## 16. https://blog.voorive (truncated)
- **WHAT:** Truncated URL from notes — not fetchable as-is.
- **ATTACK SURFACE:** None. / **ACTIONABLE LEAD:** None — dropped.

## 17. https://boschko.ca/g1-ble-rce
- **WHAT:** "UniBLEed" (Aug 2026) — unauthenticated root RCE on Unitree G1 humanoid robots: BLE GATT characteristic `0xFFE2` writable without pairing → cloud oracle `POST /device/bindExtData` on `global-robot-api.unitree.com` decrypts any robot's AES key for any free account (no ownership check) → WiFi heredoc injection → chatbot path traversal → BSS overflow → `system()` as root. Wormable. CVEs 2026-76639/76640, $6,700 bounty.
- **ATTACK SURFACE:** Unauthenticated BLE writes, cloud API missing object-level authorization (IDOR on serial number), shell heredoc injection in `wpa_connect.sh`, path traversal in chatbot knowledge base, BSS buffer overflow in `btgatt-server`.
- **ACTIONABLE LEAD:** IoT/hardware-focused, low direct transfer to current web targets — but the **cloud-oracle IDOR pattern** (decrypt/lookup endpoint that doesn't verify account↔device binding) is directly reusable: on any bounty target with device-binding or key-recovery APIs (Okta ASA, OneTrust integrations), test whether one account can resolve another account's secrets.

## 18. https://blog.nathangolez.com/2026/08/proxmox-ve-7-08-0-3-unauthenticated-single-request-root-auth-bypass
- **WHAT:** Proxmox VE 7.0–8.0.3 unauthenticated auth bypass → full `root@pam` ticket (CVE-2023-54391, PSA-2026-00043-1). Root cause: `tfa-challenge` parameter skips password verification AND challenge verification when the user has no `keys` field in `user.cfg` (default for root@pam). Fixed in libpve-access-control 8.0.4 (2023, silently); exploitation in the wild reported.
- **ATTACK SURFACE:** `POST /api2/json/access/ticket` with `username=root@pam&password=x&tfa-challenge=1` → HTTP 200 + valid ticket + CSRF token → root shell via `POST /nodes/<node>/terminal`. Patched systems return 401.
- **ACTIONABLE LEAD:** Add a hunter fingerprint: `POST /api2/json/access/ticket` with the bypass body on any `:8006` Proxmox found in recon — 200 with a ticket = critical finding (detection only, do not use the ticket). EOL boxes are still exposed.

## 19. https://blog.devploit.dev/posts/google-messages-avatarcontentprovider-contacts-bypass/
- **WHAT:** Google Messages confused-deputy bug (Google Mobile VRP, fixed Jun 2026): exported `AvatarContentProvider` (`content://com.google.android.apps.messaging.shared.ui.avatar.AvatarContentProvider/r?m=<uri>`) dereferenced arbitrary caller-supplied `content://` URIs with Messages' own permissions and returned rendered PNGs — bypassing `READ_CONTACTS` for contact photos; contact IDs enumerable via stable fallback-avatar hash.
- **ATTACK SURFACE:** Exported content providers accepting caller-controlled URIs (`m` parameter), `grantUriPermissions=true`, no caller permission check.
- **ACTIONABLE LEAD:** Mobile-app angle for bounty targets with Android apps (Booking.com, Pinterest, Okta Verify): decompile the APK, enumerate exported providers/activities and test for caller-controlled URI dereference (confused deputy). Low competition surface.

## 20. https://blog.devploit.dev/posts/five-cves-hidden-in-npm-dependencies/
- **WHAT:** Five CVEs in npm packages: CVE-2026-39243/39246/39245 (`decompress` ≤4.2.1 — hardlink/symlink/prefix-bypass path traversal), CVE-2026-39244 (`adm-zip` ≤0.5.18 — 4GB `Buffer.alloc` from 103-byte ZIP), CVE-2026-49030 (`pathe` ≤2.0.3 — backslash normalization mismatch bypasses `../` validation, unpatched).
- **ATTACK SURFACE:** Archive extraction (hardlink/symlink entries, `indexOf` prefix containment), ZIP central-directory size fields, path normalization differentials.
- **ACTIONABLE LEAD:** For targets with Node.js upload/import features (Pinterest OSS, Aiven console, GitHub-hosted projects): check `package-lock.json` for `decompress ≤4.2.1` / `adm-zip ≤0.5.18` / `pathe ≤2.0.3`, then test whether untrusted archives/paths reach them. Also reuse the `indexOf`-prefix-bypass test on any path-containment check you find.

## 21. https://bugcrowd.com/engagements/aiven-mbb-og
- **WHAT:** Aiven Managed Bug Bounty brief (live page). Rewards $50–$25K.
- **ATTACK SURFACE:** `console.aiven.io` (auth via `aivenv1` token in `Authorization:` header, NOT cookies), `api.aiven.io` (Python/nginx), `aiven.io` (fly.io-hosted), `regatta.aiven.io` (internal app — unauthorized access only), managed services (PostgreSQL/MySQL/OpenSearch/Grafana/Kafka/Valkey/ClickHouse/Metrics), GitHub orgs `Aiven` + `Aiven-Open`, **sanctioned sandbox** `falcon-bug-bounty-flag-pgsql-dev-sandbox.e.aivencloud.com`. OpenSearch has two access-control models (console vs native) with known differentials.
- **ACTIONABLE LEAD:** Highest-value authorized lab in the batch: use free-tier credits, hunt cross-account access on your own services, and work the sandbox host for the SSH host-key objective. OpenSearch dual-ACL differential is a prime authz target.

## 22. https://bugcrowd.com/engagements/atlassian
- **WHAT:** Atlassian Bug Bounty brief ($200–$10K; Rovo AI in scope). Full brief already captured in `intel/programs-bugcrowd.md`.
- **ATTACK SURFACE:** Per dossier: Jira/Confluence/Bitbucket cloud + Rovo AI.
- **ACTIONABLE LEAD:** See dossier. AI-feature angle (Rovo) mirrors the Pinterest AI lead — low dupe rates on new AI surfaces.

## 23. https://bugcrowd.com/engagements/auth0-okta
- **WHAT:** Auth0/Okta joint brief ($100–$50K). Details in `intel/programs-bugcrowd.md`.
- **ATTACK SURFACE:** Per dossier: Auth0 authentication APIs, tenants.
- **ACTIONABLE LEAD:** Pair with #30 (Okta brief): OAuth/OIDC/SAML protocol bugs and cross-tenant isolation are the named focus areas.

## 24. https://bugcrowd.com/engagements/bullish
- **WHAT:** Bullish brief — status flagged "verify active" in dossier.
- **ATTACK SURFACE:** Per dossier: `*.bullish.com`, simnext test env; subdomain takeover = explicit focus.
- **ACTIONABLE LEAD:** Run hunter `takeover` across `*.bullish.com` subs — takeover is a stated focus area here, rare and explicit.

## 25. https://bugcrowd.com/engagements/canva
- **WHAT:** Canva brief ($200–$15K). Details in `intel/programs-bugcrowd.md`.
- **ATTACK SURFACE:** Editor, Connect API, Apps SDK, `*.canva.com`.
- **ACTIONABLE LEAD:** Collaboration/authz everywhere with free multi-accounts — same IDOR playbook as Pinterest: create two free accounts, test every object reference cross-account.

## 26. https://bugcrowd.com/engagements/chime
- **WHAT:** Chime brief ($50–$20K). Details in `intel/programs-bugcrowd.md`.
- **ATTACK SURFACE:** `*.chime.com`, `*.chimepayments.com`, `*.1debit.com`, `*.chimecard.com`, Salt Labs, iOS/Android apps.
- **ACTIONABLE LEAD:** Fintech = money-movement logic bugs; test transfer/ledger flows with two own accounts (checkout-logic playbook).

## 27. https://bugcrowd.com/engagements/fivetran-mbb-og
- **WHAT:** Fivetran brief (up to $15K, P1–P3 only — P4s pay nothing). Details in `intel/programs-bugcrowd.md`.
- **ATTACK SURFACE:** `*.fivetran.com`, Connector SDK.
- **ACTIONABLE LEAD:** Skip P4-class issues entirely here; only submit P1–P3. Connector SDK = data-pipeline access class — test connector credential isolation cross-account.

## 28. https://bugcrowd.com/engagements/hotdoc
- **WHAT:** HotDoc brief ($50–$8K; brief text partially rendered — verify grid live). Details in `intel/programs-bugcrowd.md`.
- **ATTACK SURFACE:** Per dossier: health-booking platform.
- **ACTIONABLE LEAD:** Health data = PII exfil focus; verify live scope in dashboard before testing.

## 29. https://bugcrowd.com/engagements/keepersecurity
- **WHAT:** Keeper Security brief ($300–$20K, P1/P2 impact only). Details in `intel/programs-bugcrowd.md`.
- **ATTACK SURFACE:** Password manager / secrets platform.
- **ACTIONABLE LEAD:** Only P1/P2-impact issues — crypto and vault-sharing authz; don't burn time on low-severity UI bugs.

## 30. https://bugcrowd.com/engagements/nasa-vdp
- **WHAT:** NASA VDP (no cash, full safe harbor). Details in `intel/programs-bugcrowd.md`.
- **ATTACK SURFACE:** Per dossier: NASA web assets.
- **ACTIONABLE LEAD:** Reputation farm: no payout but safe-harbor practice ground for report quality before paid programs.

## 31. https://bugcrowd.com/engagements/okta
- **WHAT:** Okta brief (live page, $100–$75K + $500K RCE bonus). Test orgs at `bugcrowd-<username>.oktapreview.com` / `*.workflows.oktapreview.com` / `*.pam.oktapreview.com`; must use `@bugcrowdninja.com` email; automation STRICTLY banned (instant removal); no AI-generated reports (repeat offenders removed).
- **ATTACK SURFACE:** Named focus areas: **SSRF via Workflows Flo cards**, provision/deprovision workflow orgs, cross-org Flo actions, cross-org sensitive-data viewing, sandbox escape via API Endpoint & Return Raw, Okta Expression Language, LDAP-as-a-Service, **SAML/OAuth/OIDC/Social-auth protocol bugs**, **XXE in XML-heavy endpoints**, cross-org multi-tenancy, priv-esc, on-prem agents (LDAP/AD/OPP/Radius/RSA), Okta Verify mobile, browser plugin. Scope: `*.okta.com`, `*.trexcloud.com`, `login.okta.com`, `developer.okta.com`, `trust.okta.com`, ASA/ScaleFT, mobile apps.
- **ACTIONABLE LEAD:** Manual-only program: get credentials via the brief, stand up your own test org, and work Flo-card SSRF + cross-org visibility. The explicit focus list is a test plan handed to you.

## 32. https://bugcrowd.com/engagements/onetrust
- **WHAT:** OneTrust brief (live page, $300–$6.5K). **Testing ONLY on `pentest-app.onetrust.com`** (staging; other envs ineligible). Admin creds via brief + forgot-password flow. Accepted reports Sep 18/21 2026.
- **ATTACK SURFACE:** `*.onetrust.com`, `*.convercent.com`, `*.dataguidance.com`, `*.vendorpedia.com`, `*.cookiepro.com`, `*.cookielaw.org`, `*.onetrustgrc.com`, `*.onetrust.de/.se/.es/.fr/.it`, `*.redacted.ai`, `*.privacytech.com`, `*.privacypedia.com`, `*.esgiq.com`, `*.trustweek2021.com`. Tech: Lodash, Zone.js (Angular).
- **ACTIONABLE LEAD:** Authenticated testing with provided admin creds: Consumer Rights Portal webforms/workflows (data-subject-request data exfil) and Integrations module (pulling customer data from customer environments). Public API-key disclosure newly in scope — sweep JS bundles for keys.

## 33. https://bugcrowd.com/engagements/pinterest
- **WHAT:** Pinterest brief (live page). Published grid: P1 $10–25K / P2 $5–8K / P3 $1–3K / P4 $200–500. Recent accepted: `api.pinterest.com` (Sep 17), `github.com/pinterest` OSS (Sep 25).
- **ATTACK SURFACE:** `api.pinterest.com` (Flask API), `*.pinterest.com` (React), iOS/Android/Lite apps, 4 browser extensions (JS), `github.com/pinterest` OSS (static analysis in scope), `shffls.com` + Shuffles apps. New: Pinterest Assistant (AI), AI Board Upgrades, GenAI Interest Settings — explicitly announced for testing.
- **ACTIONABLE LEAD:** v5 API developer app (use `@bugcrowdninja.com` email for fast approval) → test Pinterest Ads + Private Profiles for IDOR/authz; audit OSS repos statically; probe the new AI features first (lowest dupe rates).

## 34. https://bugcrowd.com/engagements/sophos
- **WHAT:** Sophos brief ($100–$80K). Details in `intel/programs-bugcrowd.md`.
- **ATTACK SURFACE:** Per dossier: Sophos Central, firewalls, endpoint products.
- **ACTIONABLE LEAD:** Highest ceiling in the batch ($80K) — but enterprise security products need deep product-specific testing; park until core web skills convert on easier targets.

---

## Dead / truncated links (dropped)
- `https://*/*.` — malformed.
- `https://blog.devploit.dev/posts/google-messages-avatarcontentprovider` — 404, superseded by #19.
- `https://blog.himanshuanand.com/posts/pwn-v8` — 404.
- `https://blog.viettelcybersecurity.com/sharepoint_cve-` — truncated.
- `https://blog.voorive` — truncated.

## Needs a logged-in session (deferred to parent/browser)
- All 6 Intigriti program pages (BMW, Intigriti, Oda, Personio, Suivo, TrueLayer) — scope/rules behind login; Oda and Suivo return explicit Forbidden.
- Bugcrowd credential redemption (Okta/Aiven/OneTrust test accounts) — requires Shivam's Bugcrowd login.
