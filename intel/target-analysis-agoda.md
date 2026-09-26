# Target Analysis — agoda.com (2026-09-26)

Passive-only analysis. No form submissions, no auth attempts, no requests beyond
normal public GETs. Researcher: shiva92 (HackerOne public program).

## Liveness sweep (20 hosts, single GET, no redirect follow)

| Host | Result | Notes |
|---|---|---|
| developer.agoda.com | 302 → /supply (Cloudflare) | Live ReadMe supply developer hub |
| developer.pps.agoda.com | 302 → /docs/ (Cloudflare) | Live ReadMe PPS hub |
| portal.agoda.com | 302 → /mldc/en-us/public/login | Live Partner Portal login |
| ycs.agoda.com | 307 → portal.agoda.com/ | YCS yield system redirects to portal |
| engage-api.agoda.com | 200 (1193 B) | Live; YCS-login popup + `tokenp` cookie poll |
| partnerhub.agoda.com | 403 Cloudflare "Just a moment" | Live, bot-challenged |
| sandbox.xml.agoda.com | 403 | Live, access-denied (sandbox API) |
| secure.agoda.com | 200 (35 B) | Live, tiny body |
| payapi.agoda.com | 404 | Live host, no root doc |
| connect.agoda.com | 302 → /en-us/list-my-property | Live property onboarding |
| backoffice.agoda.com | 301 → www.agoda.com | Parked |
| confluence-stg.agoda.com | 301 → www.agoda.com | Parked |
| candidate.agoda.com | 301 → www.agoda.com | Parked |
| bookapi.agoda.com | 301 → www.agoda.com | Parked |
| swipeapi.agoda.com | 301 → www.agoda.com | Parked |
| tmapi.agoda.com | 301 → www.agoda.com | Parked |
| staging-tableau.agoda.com | 301 → www.agoda.com | Parked |
| my.agoda.com | 301 → www.agoda.com | Parked |
| selfservice.agoda.com | 301 → www.agoda.com | Parked |
| qa.ycs.agoda.com / ycs4.agoda.com / sandbox.hq.xml.agoda.com | timeout | Dead |

## Ranked top 8 (manual testing)

1. **developer.agoda.com** — Live supply API docs hub. Public OTA base URLs:
   `http://supplyota.agoda.com/b2b/ota/2013A/hotels`,
   `http://supplyota.agoda.com/b2b/ota/2015B/hotels` (both 403 = live, auth-gated).
   OAuth 2.0 rollout docs for YCSAPI / CPAPI / PromoAPI (token-based auth by 2026,
   client ID+secret self-service since June 2025). `supplyota.agoda.com` was NOT in
   cert logs — new host. Next: enumerate reference pages, test OAuth flows with own
   partner account.
2. **portal.agoda.com** — Partner Portal login (React/Vite supply-IAM micro-frontend,
   served from cdn6.agoda.net). Only visible API path in bundles: `/api/experiment`.
   Next: login/SSO parameter analysis with own account.
3. **engage-api.agoda.com** — 200 page opens `ycs.agoda.com/en-us/kipp/public/login`
   in a popup, polls `document.cookie` for `tokenp`, reloads on match. Auth-gateway
   pattern. Next: observe tokenp cookie scope/HttpOnly flags in browser (passive).
4. **partnerhub.agoda.com** — 403 Cloudflare bot challenge. Live behind the wall.
   Next: access via real browser with own session; look for partner content APIs.
5. **sandbox.xml.agoda.com** — 403 live sandbox API. Next: look for sandbox docs/creds
   in developer hub; never hammer.
6. **developer.pps.agoda.com** — Second docs hub (agoda-pps project). Next: enumerate
   its reference pages for PPS API base URLs.
7. **secure.agoda.com** — 200 with 35-byte body, no redirect. Next: identify content.
8. **payapi.agoda.com** — live host, 404 at root. Payment API surface exists.
   Next: enumerate documented endpoints only.

Deprioritized: all 301→www.agoda.com parked hosts, dead hosts (qa.ycs, ycs4,
sandbox.hq.xml). Wayback (2000 URLs) is ~99% www.agoda.com content; no admin/upload/
actuator/swagger paths found.

## JS bundle findings

- ReadMe CDN bundles (3 fetched, cdn.readme.io): generic platform JS. No API keys
  (AIza/sk_live/xoxb), no internal hostnames, no /api paths, no TODO/FIXME.
- portal.agoda.com supply-IAM bundles: `api.QNTkRx5H.js` (117 KB),
  `UniversalLogin.CeMo7rdA.js` (70 KB), `appConstants.C4hE_PfT.js` (120 B stub).
  Minified; API calls are same-origin relative; only `/api/experiment` visible;
  no hardcoded keys or internal hostnames (only ycs.agoda.com referenced).
- **No secrets found anywhere in this pass.** Values redacted per policy regardless.

## Notable leads for Shivam (manual, own accounts only)

- OAuth 2.0 migration in progress on partner APIs → token endpoint / client-credential
  flows are the highest-value manual surface.
- `tokenp` cookie auth bridge on engage-api.agoda.com → check cookie flags/scope.
- `confluence.agodadev.io` referenced in supply docs → internal domain leak, note for
  scope confirmation (agodadev.io may be out of scope — verify before touching).
