# Batch A — Infra / Pre-auth RCE intel (ingested 2026-09-26)

> Source URLs supplied by the researcher. Several supplied URLs returned 404 upstream
> (wrong slugs/site restructures); where the exact article couldn't be fetched, the
> section is built from search-verified sources on the same topic/CVE, or the URL is
> listed under Skipped. No PoC code or exploit payloads recorded — detection only.

## FreePBX CVE-2025-57819 — unauth SQLi → RCE via cron_jobs (watchTowr)
- **What:** watchTowr Labs writeup "You Already Have Our Personal Data, Take Our Phone
  Calls Too". Zero-day exploited in the wild Aug 2025. The Endpoint Manager (commercial
  module) `admin/ajax.php?module=endpoint` path passes the `brand` parameter into SQL
  unsanitized; stacked queries allow INSERT into the `cron_jobs` table with
  `schedule='* * * * *'` → command runs as `asterisk` user within ~60s → RCE. Bigger
  underlying quirk: certain module `.php` files are directly reachable pre-auth because
  FreePBX's Ajax dispatcher skips auth for localhost-originated requests and the
  `.htaccess` allow-list exposes `ajax.php`/`config.php` — patch fixed only the SQLi,
  not the core reachability quirk.
- **Affected:** FreePBX 15/16/17 with Endpoint module < 15.0.66 / < 16.0.89 / < 17.0.3.
  CVSS 9.8. CISA KEV.
- **Fingerprint/test-pattern (detection only):** `/admin/` login page or
  `/admin/ajax.php` reachable; unauthenticated request to
  `/admin/ajax.php?module=endpoint` returns 401 `{"error":"Not Authenticated"}` on
  patched-but-reachable installs vs 500 SQL error on vulnerable ones — never send
  injection payloads; banner/version check + patch-level inference only.

## FortiClient EMS 0-day — unauth API auth-bypass → RCE
- **What:** Critical unauthenticated RCE/auth-bypass in FortiClient Enterprise
  Management Server, actively exploited in the wild (Apr 2026). Attacker bypasses API
  authentication/authorization with no credentials, executes remote code, escalates
  within EMS. The internet-facing telemetry endpoint widens exposure. (Supplied ZDI
  blog URL for CVE-2026-26310 did not resolve; facts verified via CISA KEV listing and
  Shadowserver reporting.)
- **Affected:** FortiClient EMS (0-day, Apr 2026). Shadowserver: 2,000+ publicly
  accessible instances, 2 confirmed exploited. CISA KEV with 3-day remediation window.
- **Fingerprint/test-pattern (detection only):** EMS web/API port banner on exposed
  hosts; version string vs fixed release. Flag internet-exposed EMS as critical
  exposure — no request crafting, no auth attempts.

## NetAlertX < 25.4.1 — auth bypass via /index.php include chain → RCE (GHSA-h4x5-vr54-vjrx)
- **What:** The fix for CVE-2024-46506 (unauth `savesettings` → command injection via
  `/front/php/server/util.php`) was bypassed: `index.php` → `php/server/init.php` →
  `util.php` include chain, but `templates/security.php` does not mandate auth for
  requests targeting `/index.php` itself — so crafted requests to `/index.php` reach
  the sensitive settings-update functions unauthenticated (settings changes →
  command execution).
- **Affected:** NetAlertX < 25.4.1. Patched in v25.4.14.
- **Fingerprint/test-pattern (detection only):** NetAlertX login page / version
  string on the web UI (default port 20211); version < 25.4.1 = flag the auth-bypass
  class. Never POST settings functions.

## CVE-2026-24061 — GNU Inetutils telnetd NEW-ENVIRON → root
- **What:** NOTE: the supplied URLs labeled this CVE as "SuiteCRM 8.9 pre-auth RCE"
  but both URLs 404'd; the CVE ID is verified (GitHub/CISA) as GNU Inetutils telnetd:
  `NEW-ENVIRON` option carrying `USER=-f root` is appended directly to argv of
  `/bin/login`, which treats `-f root` as pre-authenticated root. Trivial one-liner
  from any telnet client; mass scanning/exploitation observed since late Jan 2026.
  Separately, SuiteCRM ≤ 8.9.2 has verified *authenticated* issues (CVE-2026-29102
  RCE in modules, CVE-2026-29096 second-order SQLi in AOR_Reports, CVE-2026-29109
  unsafe deserialization) — patched in 7.15.1 / 8.9.3.
- **Affected:** GNU Inetutils telnetd 1.9.3–2.7 (TCP/23). Fixed ≥ 2.8. CISA KEV
  (Jan 26, 2026). Common on legacy embedded/OT/HMI gear.
- **Fingerprint/test-pattern (detection only):** open TCP/23 with telnet banner
  (`Debian GNU/Linux ... telnetd`) on non-busybox hosts = flag Inetutils class.
  Banner-grab only — never send NEW-ENVIRON options.

## AEM Dispatcher takeover patterns (Searchlight Cyber — supplied Horizon3 URL 404'd)
- **What:** AEM's Apache Dispatcher (`disp_apache2.so`) has default-config paths that
  bypass the dispatcher ruleset entirely via `ProxyPassMatch`: `/adobe/dynamicmedia/deliver/*`
  and `/graphql/execute.json/*` forward straight to the AEM Jetty host. Jetty blocks
  `..;/` traversal on modern versions but very old Jetty allows it
  (`/adobe/dynamicmedia/deliver/..;/..;/..;/bin/querybuilder.json`). Known AEM
  dispatcher-bypass primitives: CRX Package Manager auth bypass via combined special
  chars (`%0a;` style) at `/crx/packmgr/*`; QueryBuilder servlets
  (`/bin/querybuilder.json`, `/bin/querybuilder.feed.servlet`); SSRF via Opensocial
  (Shindig) proxy and ReportingServicesProxyServlet (CVE-2018-12809).
- **Affected:** Adobe Experience Manager sites behind Apache Dispatcher with default
  cloud config.
- **Fingerprint/test-pattern (detection only):** probe the two ProxyPassMatch paths
  for direct-to-origin behavior (response differences vs dispatcher-handled paths);
  check `/bin/querybuilder.json` reachability; check `/crx/packmgr/` for auth wall.
  GET-only probes, never upload packages.

## CUPS RCE chain context (Pwn2Own Ireland 2025 — supplied ammaraskar/watchTowr URLs 404'd)
- **What:** Pwn2Own Ireland 2025 (Oct 2025, Cork) featured printer/IoT RCE chains;
  the "VM escape to RCE via CUPS" narrative is binary-exploitation territory
  (scheduler/parser bugs in the CUPS printing stack), not web-bounty surface — kept
  here only as a reminder that exposed IPP (TCP 631) on appliances is in-scope
  infrastructure.
- **Affected:** CUPS-based print stacks on appliances/printers.
- **Fingerprint/test-pattern (detection only):** TCP/631 banner (`Server: CUPS/IPP`)
  + version string vs patched releases. Banner-grab only.

## Skipped URLs (unreachable or already ingested)
- `securitylabs.datadoghq.com/.../hunting-the-web-j2ees-vulnerability/` — 404, no verified replacement found.
- `synacktiv.com/publications/engineering-a-pre-auth-rce-in-gogs` — 404.
- `zerodayinitiative.com/blog/2026/3/24/cve-2026-26310-...` — 404 (topic covered via CISA/Shadowserver above).
- `blog.projectdiscovery.io/hunting-saml-authentication-bypass-vulnerabilities/` — not fetched; SAML/SSO basics already ingested per batch rules.
- `rhinosecuritylabs.com/.../demystifying-saml-part-1-understanding-the-basics/` — not fetched; basics already ingested.
- `rhinosecuritylabs.com/.../demystifying-saml-part-2-exploiting-saml-vulnerabilities/` — not fetched within budget.
- `labs.watchtowr.com/pre-auth-rce-chains-in-commvault-part-1/` and `-part-2/` — 404 (slug mismatch).
- `labs.watchtowr.com/xerox-vs-the-savages/` — 404.
- `blog.qualys.com/.../ivanti-endpoint-manager-mobile-pre-auth-rce-cve-2026-5377` and `.../epmm-auth-bypass-cve-2026-5967` — not fetched within budget.
- `github.com/w181496/Joomla-component-property-manager` — not fetched (exploit repo; needs care).
- `blog.itpilotx.com/demystifying-http-request-smuggling/` — not fetched within budget.
- `blog.landh.tech/notes-to-myself-when-the-checkout-got-the-price-wrong/` — unresolvable upstream.
- `blog.landh.tech/gaining-root-on-an-aerospace-server-via-cve-2026-24334/` — not fetched within budget.
- `xbow.com/blog/xbow-engineering-and-product-updates-6` — not fetched within budget.
- `eaton-works.github.io/2026/03/06/J-and-J-Journey/` — 404.
- `blog.soufiane.io/mcp-server-vulnerabilities/` — not fetched within budget.
- `kimi.com/code/detail/...` — not fetched (unknown content).
- `blog.dragonsector.pl/2026/01/threat-modeling-tool/` — not fetched within budget.
- `medium.com/@gopaljee01071994/exploiting-cve-2025-5777-netscaler-...` — Medium blocked upstream.
- `wiz.io/blog/critical-rce-vulnerability-in-n8n-cve-2026-21858` — already ingested (batch rules).
- `ethiack.com/info-hub/research/geonetwork-preauth-RCE` — already ingested (batch rules).
- `projectdiscovery.io/blog/nuclei-v3-9-0-release` — already ingested (batch E).

## Top 3 encodable items
1. **freepbx-endpoint-reachability** — fingerprint: `/admin/ajax.php` reachable; note whether
   `?module=endpoint` returns 401 vs 500-class error; flag Endpoint module < 15.0.66/16.0.89/17.0.3
   as CVE-2025-57819 class. Detection rule: presence + error-shape, never inject.
2. **netalertx-version** — fingerprint: NetAlertX web UI (port 20211) version string;
   < 25.4.1 = GHSA-h4x5-vr54-vjrx auth-bypass→RCE class. Detection rule: version compare only.
3. **aem-dispatcher-passthrough** — fingerprint: GET `/adobe/dynamicmedia/deliver/` and
   `/graphql/execute.json/` and compare response handling vs dispatcher-managed paths;
   direct-to-origin behavior = dispatcher-bypass class; also probe `/bin/querybuilder.json`
   and `/crx/packmgr/` reachability. Detection rule: GET-only behavioral differential.
