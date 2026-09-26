# Link Study — Batch 01 (32 URLs)

Read-only recon intelligence extracted 2026-09-26. Fetched via curl through the sandbox proxy; JS-rendered pages (HackerOne, Bugcrowd) returned shells only.

## HIGH-VALUE LEADS (top 5)

1. **Booking.com Fareharbor IDOR + numeric-ID enumeration pattern** — Booking.com's own policy accepts Fareharbor IDORs on POST/PUT/DELETE or GET-with-PII; the api_key_leak writeup shows a proven 6-digit sequential policy-ID enumeration playbook (`/api/.../policies/$id?subscription-key=$KEY`). Test Fareharbor endpoints (`*.fareharbor.com`, `compass/demo/spark`) for predictable numeric IDs and missing object-level authz.
2. **Exposed Gemini API keys via geminiHunter** — tool finds assessable Google Gemini keys in web assets and Android APKs. Scan in-scope JS bundles (booking.com, agoda.com, pinterest.com) and the in-scope mobile apps (Booking.com `com.booking`, Pulse) for `AIza`-style keys.
3. **Pinterest browser extensions are in scope + BragJack pattern** — Pinterest's scope explicitly covers Chrome/Edge/Firefox/Safari extensions; BragJack showed browser *agents* hijackable zero-click via malicious extensions with 2 CVEs assigned. Review Pinterest's extension code and agent-like features for prompt-forcing / tool-abuse.
4. **Agoda builds AI agents (api-agent MCP server)** — `agoda-com/api-agent` turns any GraphQL/REST API into an MCP server with OpenAPI/Swagger auto-introspection and SQL post-processing. Superbank's scope includes an AI chatbot. Apply the Dark Marc AI-agent methodology: map untrusted inputs → tools → privileges → sinks, then test indirect prompt injection via browsed pages/documents.
5. **GeoNetwork pre-auth RCE quartet as a pattern** — CVE-2026-63219 (unauth file upload, formatter endpoint missing `@PreAuthorize`), CVE-2026-55864 (SSRF in SLD tool), CVE-2026-57582 (reflected XSS), CVE-2026-58400 (Saxon XSLT RCE). The meta-lesson: Spring apps where *one* controller method forgot `@PreAuthorize` while siblings are guarded. Hunt this pattern on any Java/Spring surface (admin/formatter/upload endpoints).

---

## 1. https://bugcrowd.com/engagements/t-mobile
- **WHAT:** T-Mobile's Bugcrowd program engagement page (JS shell via curl; content lives behind login).
- **ATTACK SURFACE:** Special P1 payout $133,700+, core P1 $55k (per dossier). Telecom account/SSO surface.
- **ACTIONABLE LEAD:** Already covered in `intel/programs-bugcrowd.md` — no new intel from this URL alone; verify live brief before testing.

## 2. https://bugcrowd.com/engagements/usagm-vdp
- **WHAT:** US Agency for Global Media VDP page (JS shell).
- **ATTACK SURFACE:** 8 wildcard federal-broadcast domains, unpaid VDP, full safe harbor (per dossier).
- **ACTIONABLE LEAD:** Good reputation farm — no cash, no rep required; verify the 8 wildcards in the dashboard.

## 3. https://bugcrowd.com/engagements/zendesk
- **WHAT:** Zendesk's Bugcrowd program page (JS shell).
- **ATTACK SURFACE:** $100–$50k range; helpdesk/support SaaS with heavy SSO/SAML integrations.
- **ACTIONABLE LEAD:** Already in dossier; focus on SSO/SAML and agent-portal authz — classic Zendesk bug classes.

## 4. https://chanzep.github.io/posts/pwn
- **WHAT:** Dead link — GitHub Pages 404, page never published or removed.
- **ATTACK SURFACE:** None.
- **ACTIONABLE LEAD:** None — drop this URL.

## 5. https://cn0
- **WHAT:** Malformed/truncated URL, not fetchable.
- **ATTACK SURFACE:** None.
- **ACTIONABLE LEAD:** None — drop.

## 6. https://darkmarc.substack.com/p/the-hackers-guide-to-attacking-ai
- **WHAT:** "The Hacker's Guide to Attacking AI Agents" (Sep 15, 2026) — practical methodology for assessing agentic AI.
- **ATTACK SURFACE:** Five-question target model: (1) untrusted inputs — direct prompts plus indirect: browsed pages, ingested docs, retrieved chunks, memory, tickets, emails, other agents' output; (2) tools ranked by action severity; (3) privilege/identity of the agent; (4) downstream interpreters (DB query, shell, URL choice, code exec = injection sinks); (5) output/exfil sinks. OWASP Agentic Top 10 (2026) ASI01–ASI10; ASI01 = Agent Goal Hijack.
- **ACTIONABLE LEAD:** Use the five questions as the checklist for Superbank's in-scope AI chatbot and any Agoda/Pinterest AI features; start with indirect prompt injection (data the agent reads but the user didn't write).

## 7. https://darknavy.org/blog/the_biometric_authtoken_heist
- **WHAT:** Fetch failed (connection blocked/timeout).
- **ATTACK SURFACE:** Title suggests biometric auth-token theft research.
- **ACTIONABLE LEAD:** Retry later via browser text fetch; relevant to 2FA/biometric playbook if retrievable.

## 8. https://dungnm.hashnode.dev/pwn
- **WHAT:** Fetch failed (connection blocked/timeout).
- **ATTACK SURFACE:** Unknown.
- **ACTIONABLE LEAD:** Retry later; cannot assess.

## 9. https://elttam.com/blog/ruby-4-0-universal-rce-deserialization-gadget-chain
- **WHAT:** elttam (Luke Jahnke) — universal Ruby **Marshal** deserialization gadget chain achieving RCE; builds on Ruby YAML/JSON unsafe-deserialization history.
- **ATTACK SURFACE:** Any endpoint that `Marshal.load`s attacker-controlled bytes; Ruby 4.0 gadget availability. Airbnb and Shopify are Rails shops — classic targets for this class.
- **ACTIONABLE LEAD:** On Rails-backed targets, hunt for Marshal/YAML deserialization sinks (session cookies, cache payloads, background-job params); test with benign gadget probes only, never weaponized payloads.

## 10. https://ethiack.com/info-hub/research/geonetwork-preauth-RCE
- **WHAT:** Ethiack research — 4 pre-auth GeoNetwork findings (Java/Spring geospatial catalog, UN FAO origin, common behind gov geoportals).
- **ATTACK SURFACE:** `GET /srv/api/records/{uuid}` (public metadata by design); formatter upload endpoint **missing `@PreAuthorize`** → CVE-2026-63219 unauth file upload; SLD tool SSRF (CVE-2026-55864); reflected XSS (CVE-2026-57582); Saxon XSLT misconfig RCE (CVE-2026-58400). Pattern: siblings guarded, one method forgotten.
- **ACTIONABLE LEAD:** Apply the "forgotten `@PreAuthorize`" pattern to any Spring/Java admin surface in scope; GeoNetwork fingerprint already in hunter.py — add these CVEs to the nuclei template watchlist.

## 11. https://forever.security/blog/bragjack-attack-hijacks-every-browser-agent/
- **WHAT:** BragJack — one ordinary browser extension hijacked the *internal* agents of Chrome (Gemini Live), Perplexity Comet, Edge Actions, Opera Neon, Claude in Chrome; $20k bounties, 2 CVEs (CVE-2026-0628, CVE-2026-55945), zero clicks.
- **ATTACK SURFACE:** Browser-agent prompt forcing → local file access, mic/camera, screenshots, profile/history leaks.
- **ACTIONABLE LEAD:** Pinterest's browser extensions are in scope — audit their permissions, content-script message passing, and any agent/AI features for prompt-forcing and over-broad tool access.

## 12. https://github.com/agoda-com/api-agent
- **WHAT:** Agoda's open-source **API Agent** — turns any GraphQL/REST API into an MCP server; auto-introspects OpenAPI 3.x / Swagger 2.0; stores results in DuckDB with SQL post-processing; recipe-learning (`r_<tool_name>` cached workflows).
- **ATTACK SURFACE:** MCP server semantics, GraphQL/REST introspection, DuckDB SQL layer (read-only by default, mutations gated), OpenAI key via env.
- **ACTIONABLE LEAD:** Agoda ships AI-agent infra — expect agent-style surfaces on Agoda properties; probe for MCP/SSE endpoints and test whether agent tool-calling can reach mutations that should be read-only.

## 13. https://github.com/agoda-com/macos-vz-kubelet
- **WHAT:** Agoda's Virtual Kubelet provider — runs native macOS VMs as Kubernetes pods on Apple Silicon (CI/CD build farms).
- **ATTACK SURFACE:** Kubelet API surface, VM networking config; infra tooling, not a web target.
- **ACTIONABLE LEAD:** Low direct bounty value; note as Agoda infra context only.

## 14. https://github.com/devploit/geminiHunter
- **WHAT:** Tool that finds and assesses **exposed Google Gemini API keys** across web assets and Android apps.
- **ATTACK SURFACE:** `AIza…` key patterns in JS bundles, APKs, config files; key-validity assessment.
- **ACTIONABLE LEAD:** Replicate the check manually on in-scope JS (booking.com, agoda.com, pinterest.com) and the in-scope Android apps (`com.booking`, `com.booking.hotelmanager`) — leaked keys with billing enabled = valid finding class.

## 15. https://github.com/jarrettj/travel-agents/blob/HEAD/docs/SWARM-SETUP.md
- **WHAT:** Dead link — GitHub 404 (repo renamed, moved, or deleted).
- **ATTACK SURFACE:** None.
- **ACTIONABLE LEAD:** None — drop.

## 16. https://github.com/louislee
- **WHAT:** GitHub profile with one repository (name not extractable via curl; JS-rendered).
- **ATTACK SURFACE:** Unknown.
- **ACTIONABLE LEAD:** Low priority; fetch via browser if needed.

## 17. https://github.com/mcfly1983/channelmanager3
- **WHAT:** "Hotel Booking Engine" — full-stack booking system with **OTA channel-manager integration (Booking.com, Agoda, Airbnb)**, inventory sync, admin panel, multi-currency.
- **ATTACK SURFACE:** OTA sync APIs, admin panel, booking modification flows, pricing/availability logic.
- **ACTIONABLE LEAD:** Read its channel-manager code to learn real Booking.com/Agoda/Airbnb partner-API request shapes — then test those same API patterns against the real in-scope properties for authz gaps.

## 18. https://github.com/philipposk/travel/blob/HEAD/API_SETUP.md
- **WHAT:** "API Setup Guide for Real Booking Data" — documents real partner/travel APIs: Skyscanner, Kiwi.com, Amadeus (OAuth client id/secret), Booking.com Affiliate API, **Agoda Partner API**, Expedia Partner Solutions, Trip.com, GetYourGuide, Viator.
- **ATTACK SURFACE:** Partner API credential flows (Amadeus OAuth, affiliate IDs, API keys in `.env.local`).
- **ACTIONABLE LEAD:** Map the Agoda/Booking.com partner API auth model from these docs; test partner endpoints for broken auth and IDOR between affiliate/partner accounts (your own test accounts only).

## 19. https://github.com/projectdiscovery/nuclei/releases/tag/v3.9.0
- **WHAT:** Nuclei v3.9.0 release page (JS-rendered; content not extractable via curl).
- **ATTACK SURFACE:** None directly.
- **ACTIONABLE LEAD:** None — installed nuclei is v3.11.1 (newer); no action.

## 20. https://github.com/sagarsakre/blog_hotel_links_verifier
- **WHAT:** "Hotel Links Monitoring System" — scrapes travel blogs for **Agoda affiliate hotel links**, verifies availability via **Agoda API**, daily GitHub Actions runs, live dashboard.
- **ATTACK SURFACE:** Agoda API usage patterns, affiliate link structures.
- **ACTIONABLE LEAD:** Study its Agoda API calls for undocumented/legacy endpoints and parameter shapes; verify affiliate-link parameter handling for open-redirect or ID confusion on Agoda.

## 21. https://github.com/skraft9/vulnerability-research/blob/HEAD/write-ups/api_key_leak.md
- **WHAT:** Write-up: exposed `env.js` in front-end source leaked API keys; endpoint required key + **6-digit Policy ID**; researcher enumerated sequential IDs (`/api/…/policies/$id?subscription-key=$KEY`) and retrieved other customers' policy data — classic IDOR + key leak.
- **ATTACK SURFACE:** `env.js`/config.js exposure, `subscription-key` query-param auth, sequential numeric object IDs.
- **ACTIONABLE LEAD:** Hunt `env.js`/`config.js` on booking.com and Fareharbor subdomains; where numeric IDs appear (reservations, properties, invoices), test sequential enumeration with your own test accounts — this is exactly Booking.com's accepted Fareharbor IDOR class.

## 22. https://github.com/v1
- **WHAT:** Truncated/mistyped URL — resolves to a bare GitHub profile "v1".
- **ATTACK SURFACE:** None.
- **ACTIONABLE LEAD:** None — drop.

## 23. https://github.com/y
- **WHAT:** Truncated/mistyped URL — bare GitHub profile "y".
- **ATTACK SURFACE:** None.
- **ACTIONABLE LEAD:** None — drop.

## 24. https://hackerone.com/adobe
- **WHAT:** **404 — program page does not exist** (slug dead or program closed/moved).
- **ATTACK SURFACE:** None currently.
- **ACTIONABLE LEAD:** Do not target Adobe via this slug; matches the dossier's ⚠️ flag.

## 25. https://hackerone.com/airbnb
- **WHAT:** Airbnb bug bounty program page (JS shell via curl; og:title confirms live).
- **ATTACK SURFACE:** `*.airbnb.com` tiered scope, Critical $18k–$25k, `X-HackerOne-Researcher` tagging, 2-day triage (per dossier).
- **ACTIONABLE LEAD:** Covered in `intel/programs-hackerone.md`; recon pipeline already running.

## 26. https://hackerone.com/airtable
- **WHAT:** Airtable bug bounty program page (JS shell; og:title confirms live).
- **ATTACK SURFACE:** Per dossier: Airtable paid program.
- **ACTIONABLE LEAD:** Covered in dossier; no new intel from URL alone.

## 27. https://hackerone.com/amazonvrp
- **WHAT:** Amazon Vulnerability Research Program page (JS shell; og:title confirms live).
- **ATTACK SURFACE:** Amazon's VRP scope.
- **ACTIONABLE LEAD:** Covered in dossier; no new intel from URL alone.

## 28. https://hackerone.com/aptible
- **WHAT:** Aptible program page (JS shell; no og:title — page may be restricted/dead).
- **ATTACK SURFACE:** Per dossier: Aptible VDP (no cash).
- **ACTIONABLE LEAD:** Verify slug in the HackerOne dashboard before relying on it.

## 29. https://hackerone.com/artsy
- **WHAT:** Artsy program page (JS shell; no og:title — may be restricted).
- **ATTACK SURFACE:** Per dossier: Artsy VDP.
- **ACTIONABLE LEAD:** Verify slug in dashboard.

## 30. https://hackerone.com/automattic
- **WHAT:** Automattic bug bounty program page (JS shell; og:title confirms live).
- **ATTACK SURFACE:** WordPress.com / Jetpack / WooCommerce surface (per dossier).
- **ACTIONABLE LEAD:** Covered in dossier; wp2shell/WP fingerprints already in hunter.py.

## 31. https://hackerone.com/basecamp
- **WHAT:** Basecamp program page (JS shell; og:title confirms live).
- **ATTACK SURFACE:** Per dossier: Basecamp paid program + VDP.
- **ACTIONABLE LEAD:** Covered in dossier.

## 32. https://hackerone.com/bookingcom
- **WHAT:** Booking.com bug bounty program page (JS shell; og:title confirms live).
- **ATTACK SURFACE:** 49 assets, `*.booking.com` / `*.fareharbor.com` / `*.rentalcars.com`, mobile apps, $150–$3,000 bounties, **automated scanning explicitly banned**, no public disclosure (verified via browser task 2026-09-26).
- **ACTIONABLE LEAD:** Policy already fully extracted; recon pipeline running; manual IDOR/authz work on Fareharbor is the top play.

---

## Dead / junk URLs to drop
chanzep.github.io/posts/pwn (404) · cn0 · v1 · y (truncated) · travel-agents SWARM-SETUP.md (404) · hackerone.com/adobe (404)

## Fetch failures (retry candidates)
darknavy.org biometric_authtoken_heist · dungnm.hashnode.dev/pwn
