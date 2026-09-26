# Cache-Behavior Differential Analysis — Pinterest & Aiven

Date: 2026-09-26. Method: 16 single, normal, read-only GET requests (one per URL/variant, ~2–3s pacing, standard browser UA). No flooding, no fuzzing, no scanners. Full headers saved under /tmp/cachediff/.

## [CONFIRMED OBSERVATIONS]

### Pinterest (www.pinterest.com — X-CDN: fastly)

1. HTML pages (`/`, `/ideas/`, `/login/`) return 200 with **no cache-status headers exposed** (no Age, X-Cache, CF-Cache-Status) and no explicit Cache-Control on HTML. `Vary: User-Agent, Accept-Encoding`. Edge caching behavior for HTML is not observable from outside — Fastly does not reveal HIT/MISS.
2. Unauthenticated `GET /resource/HomefeedResource/get/?source_url=%2F&data={...}` → **403** (no session). The internal resource API is not anonymously reachable; differential probing of it requires the authenticated session.
3. `GET /login/.css` → **301** to `https://www.pinterest.com/login/.css/` (trailing-slash route normalization). No content served — no static-extension deception on this path.
4. `X-Forwarded-Host: evil-cache-test.example.com` on `/` → 200, and the header value appears **0 times** in the response body. No host reflection.

### Aiven

5. `aiven.io/` homepage **IS edge-cached**: `CF-Cache-Status: HIT`, `Age: 283`, `Cache-Control: public, s-maxage=300, stale-while-revalidate=3600, max-age=0, stale-if-error=3600`, `Server: cloudflare`. CDN caches the marketing homepage for 300s.
6. Same URL with `?x-bust=cb9x7q2` → 200, identical body bytes (382034), but **no** CF-Cache-Status/Age headers — query string is part of the cache key (normal, expected).
7. `aiven.io/` with `X-Forwarded-Host: evil-cache-test.example.com` → **reproducible 403** (two separate requests), body is a Cloudflare "Attention Required" block page, `Cache-Control: private, max-age=0, no-store, no-cache, must-revalidate`. The block itself is not cached.
8. `console.aiven.io/` → 200, `CF-Cache-Status: DYNAMIC`, `cache-control: public, no-store` — the login app is not cached.
9. `console.aiven.io/login.css` → 403, `CF-Cache-Status: BYPASS`, `Content-Type: application/xml` — blocked path, bypasses cache; no private content served.
10. `api.aiven.io/v1/` → 404, `cf-cache-status: DYNAMIC` — not cached.

## [POISONING/DECEPTION LEADS] (ranked — for the authenticated browser sessions)

- **L1 — aiven.io cached homepage + unkeyed-input reflection.** The homepage is edge-cached for 300s (obs. 5). XFH is blocked (obs. 7) and query params are keyed (obs. 6), but other unkeyed candidates were NOT tested: `X-Forwarded-Proto`/`X-Forwarded-Scheme`, cookies (is any marketing-personalized variant cached?), `Accept-Language`. If any reflected input lands in the cached body → web cache poisoning. Caveat: marketing site only — impact caps at defacement-level; still worth one probe each.
- **L2 — Pinterest Fastly caching is a black box from outside.** No cache-status headers are exposed (obs. 1). The authenticated session should test directly: request authenticated-only URLs (secret board, resource API responses) twice and compare timing/size for cache HIT signals; request the secret-board URL with a fake static extension (`;.css`, `?.css`, path-param variants) and check whether private content is ever served with a static content-type or cacheable directives.
- **L3 — Pinterest `/login/.css` 301 normalization.** Only the redirect was observed (obs. 3); the redirect target was not followed. Worth one authenticated check whether `<private-path>.css`-style URLs serve content vs redirect — a differential in normalization between private and public paths is itself a signal.
- **L4 — Aiven console XML 403 on `/login.css`.** Not cache-relevant (BYPASS), but the `application/xml` 403 shape is a WAF-rule fingerprint worth noting for the console hunt.

## [REJECTED]

- **R1 — X-Forwarded-Host changes Pinterest's homepage.** Disproven: first XFH request body (1,246,543 B) looked different from baseline (1,040,731 B), but a repeat *without* the header returned 1,256,517 B — the ~200 KB variance is normal dynamic homepage content, and the evil host is reflected 0 times.
- **R2 — Cache deception via `.css` extension on Pinterest `/login/`.** Disproven: 301 redirect, no content served.
- **R3 — X-Forwarded-Host as a cache-poisoning vector on aiven.io.** Disproven: reproducibly blocked by Cloudflare (403, private/no-store) — the header never reaches the cacheable path.
- **R4 — Query-param cache-key anomaly on aiven.io.** Normal behavior: param is part of the key, body identical.
- **R5 — Cached personalized content on Aiven console/API (unauthenticated surface).** Disproven: `DYNAMIC` + `no-store` on console and API root.

## Notes for follow-up

- All differentials above are single-request observations except where marked reproducible (Aiven XFH 403 ×2; Pinterest size variance ×2 baselines). Treat L1–L3 as hypotheses, not findings.
- Do not re-run header-spraying at volume — the interesting next steps need the authenticated sessions (L2, L3), not more unauthenticated requests.
