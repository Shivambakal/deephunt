# SSO Authentication Bypass to Super Admin (AT&T) — Tyrion404
Source: https://medium.com/@Tyrion404/from-zero-credentials-to-super-admin-an-sso-authentication-bypass-on-at-t-996fe9d0ec1e
Date saved: 2026-09-26

## Summary
Zero-to-Super-Admin in under 60 seconds. Chain: (1) unauthenticated Spring Boot Actuator `/api/actuator/logfile` leaked 77k log lines incl. a Super Admin's username; (2) public `config.js` held API key + Azure SAS token + OIDC creds; (3) `POST /api/home/ssoAuthentication` with body `{"username":"<attuid>"}` returned a fully-signed JWT + refresh token with NO password/MFA/IdP — the "SSO" endpoint just looked up the user and signed a token; (4) `POST /api/user/listUsers` enumerated 3,182 employees; (5) integrity proven via write to `/api/reportstore/commentsReportStoreV2` attributed to victim identity (test record deleted after). Triage fought it from High 8.2 to Critical 9.3 after the write proof. Reward: $$$$.

## Detection fingerprints (for agent)
- Spring Boot Actuator: GET `/actuator`, `/actuator/logfile`, `/api/actuator/logfile`, `/actuator/env`, `/actuator/heapdump` — 200 without auth = finding.
- `X-Application-Context` / `spring` headers, `/error` JSON with "Spring" traces.
- Public `config.js` / `env.js` / `settings.js` containing `apiKey`, `sas`, `client_secret`.
- Open Swagger: `/swagger-ui.html`, `/v3/api-docs`, `/swagger.json`.
- Auth endpoints accepting username-only JSON and returning `accessToken`/`token` — flag for MANUAL verification only (never auto-test auth bypass beyond a single benign request with own test account).

## Agent relevance
- Add `springboot` check module: probe actuator paths + config.js + swagger on live hosts; report exposures.
- Auth-bypass pattern goes in the manual-test playbook: "does any login/SSO endpoint return a session for identifier-only input?" — manual, own accounts only.
- Lesson for reports: always prove integrity impact (a write) — triagers downgrade read-only ATO claims.
