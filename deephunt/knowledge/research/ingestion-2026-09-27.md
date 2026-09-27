# Knowledge ingestion — 2026-09-27 (round 1)

Grounded in 2025-2026 primary sources. Read-only research; no active testing.

## Sources read

- HackerOne #2293343 — GitLab password-reset email array injection, $35k → CASE-10, AUTHN-03
- HackerOne #3353057 — SingleStore cross-tenant folder creation via clusterID (Jul 2026) → CASE-11, IDOR-03
- HackerOne #915114 — Automattic/Crowdsignal IDOR on user edit (Jan 2026) → CASE-18
- HackerOne #1250037 — Stripe email/personal-data change ($3k) → BLO-05
- HackerOne #1537568 — GitLab CSWSH internal repos ($2k) → CASE-14
- HackerOne #1368429 — Slack WS auth bypass ($4.5k) → CASE-15
- HackerOne #1719872 — Discord WS IDOR admin settings ($3.2k) → CASE-16
- CVE @cloudflare/workers-oauth-provider <0.0.5 (May 2025) — PKCE strip → CASE-12, OAUTH-03
- CVE-2025-54576 — oauth2-proxy skip_auth_routes bypass → OAUTH-05
- CVE-2025-25291/25292 — ruby-saml parser differential → SAML-01
- 2025 OAuth code-replay race ($8.5k) → CASE-13, OAUTH-04
- PortSwigger Research: "HTTP/2: The Sequel is Always Worse" (H2.CL/H2.TE), CRLF :path tunnelling, smuggling-to-cache-poisoning chains, cache deception via smuggling → SMUG-02/03/04, CACHE-03
- PortSwigger Web Security Academy OAuth labs (implicit-flow email/token mismatch) → CASE-17, OAUTH-06
- OWASP LLM Top 10 2025 (LLM01, LLM05, LLM06, LLM08, LLM10) + Agentic Top 10 2026 (AGENT04, LLMVault tiers: Note Keeper, Confused Deputy, Oracle, ASCII smuggling, retrieval without borders, model extraction) → AI-06..AI-12
- 2025-2026 GraphQL methodology (alias batching brute force, field-suggestion schema enum, subscription hijack, WS transport limits) → GQL-05/06, API-04, DS-10
- 2025-2026 CSWSH FP-killer guides (murrtada/kenxploitz: 101 ≠ finding, per-connection token check, marker proof) → WS-06, DS-11
- 2025-2026 prototype-pollution severity guides (Heyes methodology; guan4tou2 severity scale; RCE gadget chains) → PROTO-02/03, DS-12
- Chain-economics tables (open redirect + OAuth $5K-$15K; smuggling + cache $15K-$40K) → REDIR-02, CASE-19, AP-11

## Added

- 28 technique cards: AUTHN-03, OAUTH-03..06, SAML-01, IDOR-03, GQL-05/06, API-04, WS-06/07, SMUG-02/03/04, CACHE-03, PROTO-02/03, REDIR-02, AI-06..12, RACE-03, BLO-05 (total 117)
- 10 CASE cards: CASE-10..CASE-19 (total 19)
- 3 attack patterns: AP-09 (Downgrade dance), AP-10 (Batching amplification), AP-11 (Chain multiplier) (total 11)
- 4 detection strategies: DS-09..DS-12 (total 12)
- 7 negative examples (total 29)
- Regenerated knowledge/techniques.yaml (merged, 117) and knowledge/graph.json (117 techniques)

## Tests

- validate_cards(): (True, [])
- test_datapipeline.py: 84/84 pass (count assertions updated 89 → 117)
- test_ceo.py: 5/5 pass
