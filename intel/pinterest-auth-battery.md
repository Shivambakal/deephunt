# Pinterest Authenticated Battery — Final Report (2026-09-26)

Account: attacksurfacealerts / 1107604239515479244 (Google SSO, own synthetic account).
Method: full 10-technique battery + token-layer battery + orbac lead, browser-driven, own objects only.

## CONFIRMED (verified facts)
- `orbac_subject_id` is NOT trusted on `v3/users/me/` — server binds identity to the session; forged numeric and malformed values are ignored without error or data substitution. REJECTED as vuln on this endpoint.
- No JWTs anywhere in the session — opaque HttpOnly cookie; no token leakage in v3 responses or page HTML.
- v5 API properly rejects web session cookies (Bearer-only isolation). Correct.
- All test objects (2 pins, 1 secret board) deleted and deletion verified. Board stayed private its entire lifetime.

## HIGH-CONFIDENCE LEADS (untested, need more capability)
- L1: v3 legacy API accepts the web session cookie but applies inconsistent per-endpoint authorization (own collection `users/me/pins/` succeeds; single-object `pins/{own_id}` denied for the same pins).
- L2: `orbac_subject_id` on the actual invite/collaborator POST endpoints remains untested — requires POST crafting + a second owned synthetic account for conclusive cross-user testing.

## REJECTED
- ORBAC subject-identity takeover (tested endpoint), JWT alg confusion / claim tampering (no JWTs), v5 cookie replay, secret-board exposure via privacy toggle, ApiResource confused deputy (could not reach the dispatcher with available tooling).

## Bottom line
No vulnerability confirmed. The hunt is complete with the available tooling. Remaining leads need: (a) request-crafting capability against the live session (mitmproxy harness in progress), (b) a second Pinterest account.
