# Pinterest — Unauthenticated Attack-Surface Battery

**Date:** 2026-09-26 | **Program:** Bugcrowd Pinterest ($200–$25k; P1 $10–25k)
**Scope tested:** `api.pinterest.com`, `*.pinterest.com` (per `pinterest-attack-plan.md` + Bugcrowd dossier §5)
**Method:** manual + light scripted requests only (no scanners — program rejects scanner output). Gentle rate throughout.

## Verdict

**No confirmed vulnerability on the unauthenticated surface.** Pinterest's public edge is well-hardened:
auth is enforced before input validation on the v5 API, CORS does not reflect origins, security headers
(HSTS, nonce-based CSP, X-Frame-Options, nosniff) are present, and the public embed API returns no
sensitive fields. The money remains in the authenticated battery (secret-board IDOR, Ads API authz,
OAuth scope confusion) — all of which require the test accounts.

## Findings

_None confirmed. Two informational observations below._

### OBS-1 — CSP references internal hosts (informational)
- **Evidence:** `www.pinterest.com` Content-Security-Policy `connect-src` includes `api.pinadmin.com`;
  `frame-src` includes `*.pinterdev.com`.
- **Check:** both hostnames do not resolve to reachable addresses from the test network
  (DNS sinkholed to RFC-2544 space; HTTPS connection fails).
- **Note:** unlisted in the program scope (hall-of-fame only, no payout). Recorded for completeness; no further testing performed.

### OBS-2 — Rich-pin validator fetches user-supplied URLs (unconfirmed SSRF primitive)
- **Evidence:** `https://www.pinterest.com/rich-pin-validator/` (HTTP 200) accepts a URL and
  server-side-fetches it to extract rich-pin metadata.
- **Status:** the exact fetch endpoint was not identifiable via static analysis of the page/bundles;
  confirming SSRF behavior needs JS execution or an authenticated session. **Not probed with
  internal/metadata IPs** — left for controlled follow-up.
- **Confidence:** low (primitive exists by design; exploitability unknown).

## Eliminated (checked, no issue)

| # | Check | Result |
|---|-------|--------|
| 1 | `api.pinterest.com/v5` unauth access (`/pins`, `/boards`, `/user_account`, `/oauth/token`) | 401 `Authentication failed` on all; malformed JSON to `/oauth/token` → same 401 (auth checked before parsing) |
| 2 | Legacy API versions (`/v1/`, `/v3/`) | Dead: `API method not found` |
| 3 | `widgets.pinterest.com/v3/pidgets/pins/info/` over-exposure | Public embed API by design; full response audited (77 keys) — no emails, phones, tokens, or private fields. `pinner` object contains only public profile data. CORS `*` is by design (no credentials) |
| 4 | Pin/board/user ID predictability | IDs are 19-digit snowflakes (e.g. `1019783909392286417`) — timestamp-based, not sequential; not practically enumerable |
| 5 | CORS misconfiguration | No `Origin` reflection on `api.pinterest.com` or `www.pinterest.com` |
| 6 | Open redirect on `/login/?next=` | 200, no server-side redirect; `next` echoed only inside JSON `current_url`/`visible_url` |
| 7 | Reflected XSS via `next` param | Payload `"><script>alert(1)</script>` reflected URL-encoded inside JSON string — properly encoded, not exploitable |
| 8 | Subdomain takeover / exposed staging (crt.sh, 61 hosts) | `adminapp`, `testing`, `developers-latest`, `mdp` → Pinterest "Not Found" edge page (no takeover); `anket` → 302 to `www.pinterest.com`; `pinfluencers`, `origin.sub` unresolvable |
| 9 | Secrets in webapp JS (50 bundles, landing page) | No API keys, client secrets, or internal endpoints (only false-positive React component paths like `/internal/manager/`) |
| 10 | `/resource/` webapp API without session | Requires `csrftoken` cookie even for anonymous requests; returns public data only |
| 11 | Security headers | HSTS (preload), nonce CSP, `X-Frame-Options: SAMEORIGIN`, `nosniff`, `referrer-policy` all present |

## Leads for the authenticated battery (not tested here)

1. **Post-login `next` handling** — whether the post-auth redirect validates `next` could not be tested without a session; verify with the test account.
2. **`ask.pinterest.com` (Pinterest Assistant AI)** — SPA loads unauthenticated but `/api/` → 401; prompt-injection / cross-user data access needs an account. Program-flagged low-dupe area.
3. **Rich-pin validator SSRF** (OBS-2) — single controlled probe (read response only, stop at first evidence) once a session or JS execution is available.
4. **Secret-board/pin IDOR + Ads API authz + OAuth scope confusion** — the P1 battery in `pinterest-attack-plan.md` §3; needs two test accounts + OAuth apps.

## Reproduction notes

All probes used `curl` with a standard browser User-Agent at ≤1 req/sec. Key commands:
```bash
curl -sk "https://api.pinterest.com/v5/pins"                       # 401 Authentication failed
curl -sk -X POST https://api.pinterest.com/v5/oauth/token \
  -H "Content-Type: application/json" -d '{"grant_type":'          # 401 (auth before parse)
curl -sk "https://widgets.pinterest.com/v3/pidgets/pins/info/?pin_ids=1019783909392286417"  # public pin JSON
curl -sk -H "Origin: https://evil.example.com" -D - -o /dev/null https://api.pinterest.com/v5/pins  # no ACAO
curl -sk "https://www.pinterest.com/login/?next=https://evil.example.com" -o /dev/null -w "%{http_code}"  # 200, no redirect
```
