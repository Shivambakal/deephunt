# Pinterest — Deep Static Attack-Surface Analysis

**Date:** 2026-09-26 | **Method:** passive, read-only fetching of public resources only (homepage, login page, 70 JS chunks from `s.pinimg.com`, `__PWS_ROUTES__` route map, ads/developers homepages). No authentication, no state-changing requests.
**Scope note:** complements `pinterest-unauth-battery.md` (runtime probing). Every claim below cites the fetched source.

---

## [CONFIRMED EXPOSURES]

### C1 — Webapp runs a private `/v3/` API distinct from the documented public v5 API
- The www.pinterest.com client does **not** use `api.pinterest.com/v5`. It calls **77 `/v3/` endpoints** on `www.pinterest.com` itself (extracted verbatim from downloaded chunks, `s.pinimg.com/webapp/**`).
- Full list saved at `/tmp/pinstatic/v3_endpoints.txt`. Notable: `/v3/login/qr_auth/`, `/v3/qr_auth/`, `/v3/qr_auth/status/`, `/v3/batch/`, `/v3/oauth/authorizations/`, `/v3/users/magic_link/`, `/v3/register/progress_token/`, `/v3/register/exists/`, `/v3/hf_debug_tool/interests/`, `/v3/pins/debug/{source}/`, `/v3/legal/takedowns/test/`, `/v3/callback/invite_sent/external/`, `/v3/users/settings/mfa/*`, `/v3/connect/{amazon,etsy,facebook,google,gplus,instagram,line,meta_ads,mikmak,target,youtube}/`.
- The documented public API is v5 on `api.pinterest.com` (boards/pins/search per developer docs + OpenAPI). **Web-vs-public divergence is real: the web client's auth model, not the public API's, is the target.**

### C2 — Resource RPC pattern `/resource/:name/:method/`
- Chunks contain the literal route templates `"/resource/:name/:method/"` and `"/resource/commerce/:name/:method/"` (`switch_account-*.mjs` et al.).
- Resource names observed: `BoardInvitesResource`, `BoardInviteResource`, `BoardsResource`, `BoardResource`, `PinResource`, `UserResource`, `ApiResource`, `UserHomefeedResource`, `SearchResource`, `BoardSectionsResource`, `ShareSuggestionsTypeaheadResource`, plus commerce variants. So the effective webapp surface is `/resource/<Name>/<get|create|update|delete>/` — a much larger RPC surface than the `/v3/` list alone.

### C3 — `orbac_subject_id` is a client-supplied authorization parameter
- Passed as a query/body param across `BoardInvitesResource` (`{...L?{orbac_subject_id:L}:{}}`), `BoardResource`, pin-feed queries, and collaborator removal:
  `DELETE …/{board}/collaborators/{collaborator_ids}/` with `data:{...o?{orbac_subject_id:o}:{}}` (chunk strings, e.g. collaborator-edit code).
- In at least one flow the value is threaded from client-side state derived from the page/URL context. **Whether the server binds it to the session principal is unverified — this is the single highest-value authenticated probe** (see L1).

### C4 — Board-invite redeem flow is URL-parameter driven
- `POST /v3/invite_code/{invite_code}/redeem/` with `invite_code` taken from the URL query string (`(0,p.A)(t.search).invite_code`), auto-redeemed when `?accept_invite=true&seamless=true` (`invited-9626d2f9fd848f9a.mjs`).
- After redeem, navigation target comes from the **`board_url` query param**: `(n&&r&&r(i),s)?e(s,{replace:!0})` where `s` = `board_url` from `t.search`. Client-side redirect sink fed by URL param (see L3).

### C5 — QR-code login flow with pollable token
- `POST /v3/qr_auth/` → `{qr_token}`; client polls `POST /v3/qr_auth/status/` with `{qr_token}` on an interval until scanned/approved (two independent chunk implementations confirm the pattern). Separate `POST /v3/login/qr_auth/` completes login.

### C6 — Batch endpoint accepts JSON-stringified sub-requests
- `POST /v3/batch/` with `data:{requests: JSON.stringify(s)}`; client sends GET sub-requests with `fields` params. Server-side sub-request dispatch = classic batch-smuggling surface (see L5).

### C7 — OAuth authorization management endpoints
- `GET /v3/oauth/authorizations/` (fields: `authorization.consumer()`, `authorization.created_at`, `authorization.scope_descriptions`); `DELETE /v3/oauth/authorizations/{consumer_id}/` revokes by numeric consumer id (`oauth-e3356d341104cb65.mjs`).

### C8 — Debug tooling is in the public route map
- `__PWS_ROUTES__` (www.pinterest.com homepage, 376 routes) exposes `_/_/developer-tools/*` (experiments-override, request-headers-override, dev-url-params, cookies), `homefeed/debug.js` → `POST /v3/hf_debug_tool/interests/` (takes `interest_ids` JSON; redirects to `/` when empty), and `pins/debug/[source].js` → `/v3/pins/debug/{source}/` with `debug_options` JSON. Whether the endpoints are auth-gated is unverified (see L8).

### C9 — Internal hostnames referenced by client code
- `helium.pinadmin.com`, `pdocs.pinadmin.com`, `pintrace.pinadmin.com`, `w.pinadmin.com`, `gestalt-docs.pinterdev.com`, `pinterest.onelink.me` (chunk string extraction). None resolve to reachable addresses from the test network (consistent with prior battery's `api.pinadmin.com` / `*.pinterdev.com` CSP finding). No keys/secrets found in any downloaded chunk.

### C10 — Signup is a `progress_token` state machine
- `POST /v3/register/progress_token/` returns `{exists, is_valid, progress_token, email_verification_required, birthdate_validation}`; the token is threaded through subsequent signup steps (`EmailPasswordStep` sends `{..., progress_token}`). Step-skipping/replay is the seam (see L7). Note `exists` in the response = registration oracle (low severity).

### C11 — Magic-link login discloses account existence in UI copy
- Chunk string: `"The email you entered does not belong to any account."` shown in the magic-link flow after a `check_user_request`. Explicit enumeration by design; informational/low.

### C12 — Forgot-password client handles success/failure uniformly
- `POST /v3/users/forgot_password/` with `{username_or_email}`; both `.then()` branches perform the same UI transition (navigate to `/password/reset/sent/`), error branch only stops the spinner. No client-side oracle (server behavior unverified but client suggests uniform).

### C13 — Account linking covers 10 third-party providers
- `/v3/connect/{amazon,etsy,facebook,google,gplus,instagram,line,meta_ads,mikmak,target,youtube}/` — OAuth account-linking surface (see L9).

### C14 — MFA lifecycle endpoints enumerated
- `/v3/users/settings/mfa/`, `/backup/`, `/disable/`, `/eligibility/`, `/resend/`, `/verify/` — MFA disable/backup-code flows are high-value auth targets (see leads).

### C15 — ads.pinterest.com is an SPA on the public v5 API
- `https://ads.pinterest.com/` (200, "Pinterest Ads") loads `s.pinimg.com` chunks and references `api.pinterest.com`. The Ads Manager speaks the documented v5 API — so v5 OAuth scope/IDOR findings apply to the ads surface too.

---

## [HIGH-CONFIDENCE LEADS]

**L1 — `orbac_subject_id` trust (highest value).** Tamper/swap `orbac_subject_id` on `BoardInvitesResource` (`status_filters=new,accepted,…`), collaborator list/remove, and pin-feed resource calls. Invariant: it must always equal the session user. If the server trusts it, it's cross-user board-invite/pin disclosure and collaborator manipulation.

**L2 — Invite-code entropy on `/v3/invite_code/{code}/redeem/`.** Measure code format/entropy; test whether sequential/guessable codes redeem into arbitrary (secret) boards. The accept flow is fully client-driven from query params.

**L3 — `board_url` post-redeem navigation.** Verify whether an absolute `https://evil…` `board_url` escapes the SPA router (React Router `navigate` normally treats it as a path, but confirm; also check for `window.location` assignments in the invite flow).

**L4 — QR-auth token binding.** Capture a `qr_token`, poll `/v3/qr_auth/status/` cross-session; check token entropy, expiry, and whether approval binds to the *scanning* account vs the *displaying* session (session-fixation shape).

**L5 — `/v3/batch/` smuggling.** Try non-GET sub-requests (POST/DELETE), sub-paths outside the client's allowlist, and nested `/resource/` URLs inside `requests`. Invariant: sub-requests must inherit exactly the caller's authz, nothing more.

**L6 — OAuth authorization IDOR.** `DELETE /v3/oauth/authorizations/{consumer_id}/` with another user's/guessed `consumer_id`. Invariant: users can only revoke their own authorizations.

**L7 — `progress_token` step-skipping.** Replay a `progress_token` across steps; attempt to skip email-verification or birthdate-validation steps; test token reuse across accounts.

**L8 — Debug endpoint gating.** `POST /v3/hf_debug_tool/interests/`, `/v3/pins/debug/{source}/`, `/v3/legal/takedowns/test/` with and without session. Any 200 without auth = finding.

**L9 — `/v3/connect/*` linking CSRF/state.** Check `state` parameter validation and whether linking flows can be driven cross-account (attach attacker's third-party account to victim's Pinterest session or vice versa).

**L10 — `switch_account` id tampering.** The switch flow posts `{switch_account: <id>}` / `{business_id, owner_id}` (`switch_account-16e1a605fb2141d4.mjs`). Probe with a non-owned account id; invariant: server must reject.

**L11 — Collaborator privilege transitions.** `BoardInviteResource` create/accept with tampered role fields; `status_filters` values (`pending_approval`, `contact_request_not_approved`) suggest an approval workflow — test skipping the approval state.

**L12 — Rich-pin validator SSRF** (carried from unauth battery OBS-2, still unconfirmed): identify the server-side fetch endpoint behind `/rich-pin-validator/` now that chunk inventory exists; single controlled probe, read-only.

---

## [REJECTED]

- **R1 — postMessage wildcard in LINE OAuth redirect.** `window.opener.postMessage(e)` is a single-argument call (`redirect-588ac3e614969dc0.mjs`); per spec the missing `targetOrigin` defaults to `"/"` (same-origin only), not `*`. Not exploitable. (What it posts — the redirect's query string, i.e. the LINE auth code — stays same-origin.)
- **R2 — `dangerouslySetInnerHTML` XSS.** 10 chunks use it; all are React internals, the `InlineStyle` CSS renderer (`<style>` context, factory-processed), or skeleton/spinner markup switched on `e.length`. No server-controlled HTML sink found in downloaded chunks.
- **R3 — Secrets in JS.** 70 chunks grepped: no API keys, client secrets, or tokens. Only internal hostnames (C9).
- **R4 — `pinterest://` deep-link handlers.** No deep-link scheme strings in downloaded chunks.
- **R5 — Legacy API versions on `api.pinterest.com`.** `/v1/`, `/v3/` return `API method not found` (prior battery, re-verified 2026-09-26).
- **R6 — Forgot-password user oracle.** Client handles success/failure identically (C12); no oracle in the web flow.
- **R7 — Feature-flag exposure.** No `featureFlag`/`isFeatureEnabled` identifiers in downloaded chunks; experiments surface only via the `_/_/developer-tools` routes (C8), which are UI affordances, not flag dumps.

---

## Sources
- `https://www.pinterest.com/` (200, 1.2 MB, `__PWS_ROUTES__` 376 routes, `s.pinimg.com/webapp/*.mjs`)
- `https://www.pinterest.com/login/` (200)
- 70 downloaded chunks from `https://s.pinimg.com/webapp/` (7.8 MB decompressed), in `/tmp/pinstatic/chunks/`; endpoint list in `/tmp/pinstatic/v3_endpoints.txt`
- `https://ads.pinterest.com/` (200, "Pinterest Ads"), `https://developers.pinterest.com/` (200), `https://api.pinterest.com/` (404)
- Pinterest v5 public API surface per developer docs/OpenAPI (boards, pins, search endpoints on `api.pinterest.com/v5`)
