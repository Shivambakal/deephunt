# Pinterest: Mobile-vs-Web API Differential Analysis

Passive only. No logins, no authenticated requests. All live probes were single
unauthenticated read-only requests. Date: 2026-09-26.

## [CONFIRMED]

### C1. Pinterest exposes THREE distinct API planes, not one

| Plane | Base | Auth model | Status (probed 2026-09-26) |
|---|---|---|---|
| Public REST v5 | `https://api.pinterest.com/v5` | OAuth2 Bearer (`pina_…`), granular scopes | LIVE — `GET /v5/user_account` → 401 `{"code":2,"message":"Authentication failed.","status":"failure"}` |
| Internal web client | `https://www.pinterest.com/resource/<Name>/<action>/` | Cookie session + `X-CSRFToken` (from `csrftoken` cookie) + `X-Pinterest-PWS-Handler` header | LIVE — `GET /resource/BoardsResource/get/` → 403 unauthenticated |
| Legacy v3 | `https://api.pinterest.com/v3/…` | `access_token` query param (2013-era mobile style) | **STILL LIVE** — `GET /v3/users/me/` → 401 `{"status":"failure","code":3,"message":"Authorization failed.","endpoint_name":"v3_get_user_handler","data":null,…}`. Different error schema than v5 = different stack still deployed. `GET /v3/` → 404 (namespace gated, handlers live). |

Sources: live probes; OpenAPI spec v5.28.0 from
https://github.com/pinterest/api-description (189 paths, servers:
`https://api.pinterest.com/v5`); internal client
https://github.com/bstoilov/py3-pinterest (mimics browser requests to internal
endpoints, 390 stars); v5 auth reference
https://github.com/vermsudh/pinterest_automation/blob/HEAD/Documentation/pinterest_api_reference.md.

### C2. Public v5 inventory (from official OpenAPI 5.28.0, 189 paths)

Organic (non-ads/business) surface: `GET,POST /boards`, `DELETE,GET,PATCH
/boards/{board_id}`, `GET /boards/{board_id}/pins`, sections CRUD,
`GET,POST /pins`, `DELETE,GET,PATCH /pins/{pin_id}`, `POST
/pins/{pin_id}/save`, product_tags (+ `bulk-delete`), `GET,POST /media`,
`/user_account` (+ analytics, followers, following, websites), `/search/boards`,
`/search/pins`, `/search/partner/pins`, `/trends/*`, `/terms/*`,
`/catalogs/*` (+ `POST /catalogs/items/batch`), `/integrations/*`, `POST
/notifications`, `/oauth/*`. Plus the large ads/business surface
(`/ad_accounts/*` incl. `POST …/bulk/upsert`, `POST …/bulk/download`).

Notable: scopes `boards:read_secret` and `pins:read_secret` exist — secret
content via the public API requires explicitly granted secret scopes.

### C3. Internal web `/resource/` inventory (from py3-pinterest source)

~40 resource families, actions `get/create/update/delete`, request encoding =
form/url-encoded `source_url` + `data={"options":…, "context":…}` +
`_=<timestamp>` (GET in query string, POST in body). Resources include:
`BoardsResource`, `BoardResource`, `BoardFeedResource`,
`BoardInvitesResource`, `BoardPickerBoardsResource`, `BoardSectionsResource`,
`BoardSectionResource`, `BoardSectionPinsResource`, `BoardSectionEditResource`,
`BoardContentRecommendationResource`, `PinResource`, `RepinResource`,
`PinLikeResource`, `PinCommentResource`, `AggregatedCommentResource`,
`AggregatedCommentFeedResource`, `SearchResource`, `BaseSearchResource`,
`AdvancedTypeaheadResource`, `VisualLiveSearchResource`,
`FindPinImagesResource`, `ConversationsResource`,
`ConversationMessagesResource`, `UserResource`, `UserPinsResource`,
`UserHomefeedResource`, `UserFollowersResource`, `UserFollowingResource`,
`UserFollowResource`, `UserSessionResource` (create/delete = login/logout),
`StoryPinResource`, `VIPResource`, and the generic **`ApiResource`
(create/update/delete)**.

The web client ALSO still calls `www.pinterest.com` `/v3/` paths:
`/v3/boards/{id}/follow/`, `/v3/media/uploads/register/batch/`
(→ `pinterest-media-upload.s3-accelerate.amazonaws.com`). Old
`/upload-image/` is dead (401 per py3-pinterest issue #204, replaced by the
S3 flow). Issue #217 documents a `403` with an `_ngjs` URL prefix — evidence
of an additional internal URL namespace whose auth handling differs.

### C4. Differential table — internal-only capabilities (NOT in public v5)

| Capability | Internal `/resource/` | Public v5 |
|---|---|---|
| Comments (get/create/delete) | `PinCommentResource`, `AggregatedCommentResource` | absent |
| Direct messages / conversations | `ConversationsResource`, `ConversationMessagesResource` | absent |
| Follow / unfollow users & boards | `UserFollowResource`, `ApiResource/update+delete` w/ `/v3/boards/{id}/follow/` | absent (`POST /user_account/following/{username}` exists but board-follow does not) |
| Repin | `RepinResource/create` | absent (only `POST /pins/{id}/save`) |
| Pin likes | `PinLikeResource` | absent |
| Home feed / board feed | `UserHomefeedResource`, `BoardFeedResource` | absent |
| Personalized search, typeahead, visual search | `SearchResource`, `AdvancedTypeaheadResource`, `VisualLiveSearchResource` | only generic `/search/pins`, `/search/boards` |
| Board invites / collaborators | `BoardInvitesResource/get` | absent |
| Board recommendations ("more ideas") | `BoardContentRecommendationResource` | absent |
| Pinnable-image extraction | `FindPinImagesResource` | absent |
| Session login/logout | `UserSessionResource/create+delete` | `POST /oauth/token`, `/oauth/token/revoke` (different mechanism) |

Every social/messaging/discovery feature lives ONLY behind the cookie-session
internal API — the public OAuth API is a deliberately reduced subset.

### C5. `ApiResource` is a client-directed internal dispatcher

`follow_board()` does NOT call a dedicated follow endpoint. It POSTs to
`https://www.pinterest.com/resource/ApiResource/update/` with
`options = {"url": "/v3/boards/{board_id}/follow/"}`; unfollow uses
`ApiResource/delete/` with the same options shape; media upload uses
`_api_resource_post(url_path, data)` → `ApiResource/create/` with
`options = {"url": <arbitrary path>, "data": <arbitrary data>}`.
The client supplies the internal target path inside the request body — the
server dispatches on it. Source: `py3pin/Pinterest.py` (`FOLLOW_BOARD_RESOURCE`,
`_api_resource_post`).

### C6. Auth-model differentials across planes

- v5: Bearer token, least-privilege scopes; secret boards/pins need
  `:read_secret` scopes.
- Internal: ambient cookie session + CSRF token; no scope layer visible —
  authorization is per-resource server-side.
- v3 (legacy): `access_token` in query string; the 2013 email-disclosure bug
  (https://thehackernews.com/2013/08/pinterest-exploit-exposes-user.html?m=0 —
  `/v3/users/me/` → swap `me` for any username → leaked email) was this plane's
  bug class: **path-parameter identity vs token identity confusion**.

### C7. Upload-flow differentials

- v5: `POST /v5/media` (register) → S3 → `POST /v5/pins`.
- Internal: `/v3/media/uploads/register/batch/` → S3-accelerated upload →
  `PinResource/create` or `StoryPinResource/create`.

## [HIGH-CONFIDENCE LEADS]

**L1 — ApiResource confused dispatcher (highest value).** The client controls
`options.url` dispatched server-side by `ApiResource/{create,update,delete}`.
Authenticated probe: with the research session, send `ApiResource/update` with
`options.url` set to internal paths beyond `/v3/boards/{id}/follow/` (other
`/v3/` handlers, other resource actions) and observe whether the server
allowlists the target. Missing/loose allowlist = authenticated action forgery
across internal endpoints. Minimal test: point it at a harmless read-only
internal path first and check for a dispatched response vs rejection.

**L2 — Legacy v3 plane still live.** `v3_get_user_handler` routes today.
Authenticated probe (own session only, single requests): compare the SAME
object access across v3 and v5 (e.g., user/board lookups) for authz
divergence — legacy handlers frequently miss newer authorization checks.
Historical precedent on this exact plane is identity-confusion (2013).

**L3 — Secret-scope gating vs session gating.** v5 demands
`boards:read_secret`/`pins:read_secret` for secret content; the internal API
serves secret boards to the owner under a plain session. Probe: does
`BoardsResource/get` (internal) vs `GET /v5/boards/{id}` (v5, without secret
scope) make the SAME decision for non-owner and logged-out callers? Any
divergence is an authz inconsistency.

**L4 — Follow/unfollow object substitution.** Follow goes through the generic
dispatcher with a client-supplied board ID in the URL string. Probe the
invariant "cannot follow/interact with a board you cannot see": attempt
follow on a secret board ID of the test account from a logged-out context,
and tampered IDs.

**L5 — `_ngjs` namespace (from py3-pinterest issue #217).** A distinct URL
prefix that 403s differently. Identify what `_ngjs` serves and whether its
auth checks match the `/resource/` plane.

**L6 — `UserSessionResource/create|delete`.** Login/logout via the resource
API. Probe session semantics: concurrent sessions, session fixation across
password change, whether `delete` truly invalidates server-side.

**L7 — Conversations (internal-only).** `conversation_id` is the classic
IDOR shape. Needs two controlled accounts; test cross-account conversation
read with tampered IDs.

## [REJECTED]

- **R1 — "Public v5 covers comments/messages/follows."** Disproven: full
  enumeration of the 189-path OpenAPI 5.28.0 spec shows none of these; they
  are internal-only.
- **R2 — "v3 is dead."** Disproven: `api.pinterest.com/v3/users/me/` returns
  a routed 401 with `endpoint_name: v3_get_user_handler` (probed 2026-09-26).
  (The earlier unauthenticated battery's "v1/v3 dead" referred to `www.`
  paths; the `api.` v3 namespace is alive.)
- **R3 — "Mobile apps use a separate private API."** No recent public
  evidence found. The 2013 account (https://readwrite.com/what-your-pinterest-ublic-api-will-look-like/)
  states the iOS app communicated over the same internal API as desktop.
  Treat mobile as the same internal plane until a teardown proves otherwise.
- **R4 — "A v1 REST API exists."** No evidence of a live v1 namespace found
  on either `api.pinterest.com` or `www.pinterest.com`.

## Sources

- Official OpenAPI 5.28.0: https://github.com/pinterest/api-description
- Internal API client (source of `/resource/` inventory + dispatcher):
  https://github.com/bstoilov/py3-pinterest
- v5 auth/scopes reference:
  https://github.com/vermsudh/pinterest_automation/blob/HEAD/Documentation/pinterest_api_reference.md
- v5 endpoint summary:
  https://github.com/adamtasteslikegood/tasteslikegoodtheangularsvegancookbook/blob/HEAD/pintrest-research.md
- 2013 v3 `/v3/users/me/` email disclosure:
  https://thehackernews.com/2013/08/pinterest-exploit-exposes-user.html?m=0
- 2013 iOS-app-on-internal-API:
  https://readwrite.com/what-your-pinterest-ublic-api-will-look-like/
- Live unauthenticated probes run 2026-09-26 (single read-only requests, no
  credentials): `api.pinterest.com/v5/user_account` → 401;
  `api.pinterest.com/v3/users/me/` → 401 (`v3_get_user_handler`);
  `www.pinterest.com/resource/BoardsResource/get/` → 403.
