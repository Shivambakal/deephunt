# GeoNetwork Pre-Auth RCE — Ethiack research (ingested 2026-09-26)

Source: https://ethiack.com/info-hub/research/geonetwork-preauth-RCE

## What it is
GeoNetwork is a Java/Spring open-source geospatial metadata catalog (OSGeo project,
ex-FAO/UN). Sits behind government open-data portals, environmental agencies, EU
spatial-data infrastructure. Quiet infra, high-value targets.

## The four findings
- **CVE-2026-63219** — Unauthenticated file upload. FormatterAdminApi's addFormatter
  lost its `@PreAuthorize` line in the 4.0.6 refactor → anonymous users can upload
  new XSLT formatters to disk. Vulnerable: **>= 4.0.6**.
- **CVE-2026-58400** — RCE via unsafe Saxon XSLT. Saxon-B's ALLOW_EXTERNAL_FUNCTIONS
  never set to false (default true) → uploaded stylesheet can call Java Runtime
  directly. Chain: POST malicious XSLT formatter → GET
  `/srv/api/records/{uuid}?formatter={name}` on a public record UUID → RCE.
  Demonstrated reverse shell on **4.4.11**.
- **CVE-2026-55864** — Unauthenticated SSRF. `POST /api/tools/ogc/sld` takes a
  caller-supplied WMS `serverURL`, server-side GETs it with no allowlist. Fetched
  body parsed as XML flows back into the response (blind-ish, needs XML-returning
  internal target).
- **CVE-2026-57582** — Reflected XSS. `/srv/eng/catalog.search?uiconfig=(alert(1),{})`
  lands unsanitized in an inline `<script>` via base-layout-cssjs-loader.xsl.
  XSRF-TOKEN cookie is JS-readable (not HttpOnly) → one-click full account takeover.

## Scale
121 affected 4.x deployments across 39 countries; 89% government/military/national-agency.

## Fingerprints (safe, detection-only)
- `GET /srv/api/info` (also under `/geonetwork/srv/api/info` — common context path)
  → GeoNetwork 4.x returns version JSON. Flag >= 4.0.6 for the upload/RCE chain.
- `GET /srv/eng/catalog.search` HTML contains "GeoNetwork" → instance confirmed.
- `GET /srv/api/formatters` → 401/403/200 means the formatter admin API exists
  (upload endpoint's neighborhood); 404 means absent.

## Agent rules
- Detection + version flagging ONLY. Never upload formatters, never trigger XSLT,
  never send SSRF callbacks, never fire XSS payloads at real users.
- On authorized targets: verify version first, then follow the standard
  report-and-stop flow for the upload/RCE chain.
