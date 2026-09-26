# chess.com — Passive Recon Deep-Hunt Report

**Recon date:** 2026-09-26
**Method:** PASSIVE ONLY — public web search, fetched public pages, crt.sh certificate-transparency JSON. No port scanning, no probing, no login attempts, no traffic beyond loading public pages.
**Policy snapshot note:** Bug bounty terms change without notice; re-read the live policy before any testing.

---

## 1. Live Policy (verified 2026-09-26 from the live page)

- **Policy page:** https://www.chess.com/news/view/chess-com-bug-bounty-policy — **v0.1.9, last updated May 20, 2025**
- **HackerOne program:** https://hackerone.com/chess_com (handle confirmed via a public directory-style listing; policy itself directs reports to email below and notes "chess.com uses [HackerOne] for tracking")
- **Report channel:** bounties@chesscom.atlassian.net (email-first; include PoC, working code/steps to replicate, real name + contact info; report to them first and exclusively — public disclosure before a fix voids the bounty)
- **In-scope assets:** **only the chess.com domain.** Explicitly: "only security issues within the chess.com domain will be eligible." ChessKid, Chessable and other domains are explicitly called out as out of scope (program may extend later; the policy article will be updated if so).
- **Program status:** the live policy page is current and a May-2026 third-party recon repo states the program is Active. One older (2022-era) third-party game-bounty list said "doesn't want bugs right now" — superseded by the current policy; treat the program as live.

### Bounty table (exact, from the live policy)

| Vulnerability type | Bounty |
|---|---|
| Remote code execution (file inclusion → execution, SQLi, server-side script execution, reverse shell) | $1,000–$4,000 |
| Mass user account data leakage (many users' private data/passwords, single exploit) | $800–$3,000 |
| Broken authentication & session management (auth bypass, session fixation → account access, 2FA bypass, account takeover, obtaining a target user's password) | $600–$800 |
| Server-side injection (SSTI, CRLF response splitting with demonstrated impact, SSRF with payload showing impact) | up to $400 |
| CSRF (damage user settings, perform actions on behalf of other users; excludes actions achievable via XSS) | up to $400 |
| Application logic bypass (flow bugs with security impact, BAC, IDOR) | up to $400 |
| XSS — payout for **discovering a new injection vector** enabling JS execution (basic alert() → filter bypass → untrusted script load/data exfiltration) | up to $250 |
| Content spoofing (HTML injection → believable phishing) | up to $250 |
| PII leakage (IP address, geolocation, email, telephone) | up to $200 |
| Captcha bypass (server security misconfiguration) | up to $150 |
| No rate limiting on critical forms | up to $100 |
| Non-sensitive info leakage (e.g. login form username-vs-password differential responses aiding brute force) | up to $100 |

Bounty is set by **severity × likelihood of attack ≈ amount of traffic to the endpoint**. Report must be new and unique (first-submitter wins by email receipt timestamp). **Regressions of previously fixed bugs pay half price.**

### Explicit exclusions / limitations

- UI/graphics/data bugs with no security impact (these go to the in-site "Report a Bug" system, sometimes rewarded with free memberships — not bounties).
- Reports from **automated tools**, exploits on unsupported browsers or old mobile apps, **physical-access or social-engineering attacks** (incl. phishing/staff impersonation), **denial of service**, email issues, systems outside chess.com's control, issues they already know about.
- Deviations from industry-standard procedures/settings need a demonstrated harmful exploit.
- Must confine work to **test accounts created for this purpose**; avoid experiments visible to the public or during **live events**. Unannounced testing indistinguishable from an attack "will be treated as an attack" and may be referred to law enforcement — contact them first if an exploit may cause harm.
- Response SLA target: 5 business days.

### Game-integrity / cheats — read carefully

The policy's edit history includes **v0.1.1 (2019-07-29): "clarified scope for cheats and obtaining unpaid-for membership features."** The current v0.1.9 page text no longer carries explicit cheat language; the live exclusions do not list game-logic manipulation as out of scope. Most plausible reading: game-integrity logic bugs (rating manipulation, unlocking paid features) are treated under **"Application logic bypass" (up to $400)**. That makes chess.com more permissive than most game companies here — but **confirm with the program before deep game-state testing**, since the wording was removed from the live text.

---

## 2. Architecture & Tech Stack (public sources)

- **Frontend:** React with SWR-style caching (third-party analysis of the `__Secure-cst` cookie and embedded config). Internal packages are **Svelte**-compiled (`@chesscom/chessboard` v1.178.0 is the production board).
- **Backend:** PHP + JavaScript footprint per the public GitHub org; REST-style internal API (`/api/{resource}/{id}`); legacy Bayeux/CometD long-polling library (`cometd.js`) with **WebSocket** primary for live games when connectivity allows.
- **Live play:** distributed real-time server network; millisecond-precision clock sync across continents; Glicko-2 rating/matchmaking processing millions of concurrent games (per a Vectree architecture teardown).
- **CDN/WAF:** Cloudflare in front (certs via Google Trust Services + Cloudflare SSL; 104.18.x.x ranges cited by third-party recon).
- **Auth model:** cookie-session based (`ACCESS_TOKEN` JWT-style cookie observed in writeups); "Extra Security" **risk-based 2FA** — OTP is only challenged when login looks unfamiliar (VPN/new device triggers it); **OAuth 2.0 server exists** for third-party apps (`external.oauth2.chess.com` in CT logs; OAuth onboarding via a Google Form + Notion docs at chesscom.notion.site; scopes not publicly documented).
- **Mobile apps:** iOS/Android apps are explicitly in scope per the policy ("site, mobile apps, or API").
- **Published-Data API (public, no auth, documented):** https://www.chess.com/news/view/published-data-api — base `https://api.chess.com/pub/`. Endpoints: `/player/{username}`, `/player/{username}/games/archives`, `/player/{username}/games/{YYYY}/{MM}`, `/player/{username}/stats`, clubs, tournaments, countries, leaderboards, streamers. Notable fields: `player_id` (immutable account ID), `status` (incl. `closed:fair_play_violations`), `is_streamer`, `twitch_url`, `last_online`, `followers`, `fide`. CORS is open (`access-control-allow-origin: *`) per third-party verification 2026-08-26; reported rate limit ~300 req/min/IP (**unverified**, third-party claim).
- **Fair-play / anti-cheat:** automated statistical models + human review; signals include engine move-matching, **timing patterns, cursor tracking / clicking outside the browser**, account history, sudden performance jumps (public docs). **Proctor** (webcam + screen-monitoring software, subdomain `proctor.chess.com` seen in CT) is now required for prize events (Titled Tuesday etc.). 2026 change: accounts closed for cheating are now **publicly marked**. Fair-play status leaks via PubAPI `status: closed:fair_play_violations` — useful for OSINT, not a vuln.

---

## 3. Third Parties & Partners

| Surface | What is known | Verification |
|---|---|---|
| Membership / Diamond payments | Paid membership tiers (Gold/Platinum/Diamond) + gift memberships; checkout exists on chess.com domain | confirmed (public pricing pages); **payment processor identity (Stripe/PayPal/etc.) UNVERIFIED** — no reliable public source found; web research returned only unrelated docs |
| Physical shop | shop.chess.com (in CT logs) | confirmed host only |
| Identity / login | Google/Apple login available on apps (per platform norm); **unverified for web SSO** | unverified |
| OAuth for third-party devs | Chess.com OAuth 2.0 server; `external.oauth2.chess.com`; approval via public form | confirmed (Notion docs + CT) |
| Twitch / streaming | PubAPI `is_streamer` + `twitch_url` fields; streamer profiles link Twitch | confirmed via API docs |
| Support desk | support.chess.com + localized variants (ayuda, suporte, destek, hulp, dovidka, podrska, arsupport, pomoc) → third-party help-desk | hosts confirmed in CT |
| File-transfer vendor | June 2025 breach was via a **third-party file-transfer application** (4,541 users, names + identifiers, no financial data; core systems unaffected) — supply-chain surface exists but the vendor was not named | confirmed (Maine AG filing, reported by CyberInsider) |
| Error monitoring | Public org publishes `chesscom/honeybadger-php` — Honeybadger.io in use | confirmed (public repo) |

---

## 4. Code & Repos

- **Official org:** https://github.com/ChessCom — 92 public repos. Almost entirely peripheral: infra tooling, forks of third-party libraries, PHP/Objective-C/Swift mobile tooling. **Game server, matchmaking, and core engine code is NOT public** (proprietary).
- Notable public artifacts:
  - `@chesscom/chessboard` (production web board, Svelte→JS, proprietary `UNLICENSED`, distributed via GitHub Packages npm registry requiring auth) and `@chesscom/js-chess-engine` (dependency-free chess logic lib with UCI engine drivers) — per a third-party evaluation of their published packages.
  - `ccc-configs` — Docker/config for the Chess.com Computer Chess Championship infra.
  - `stockfish` fork; `android-chessclock`/`ios-chessclock`; `browser-extension`; `k8s-numa-resource-plugin` (Go K8s device plugin).
  - Packagist `chesscom/` namespace: `chesscom/honeybadger-php`, `chesscom/chess-game`.
- **Unofficial ecosystem (useful for recon tooling, NOT targets):** dozens of PubAPI wrappers, clubs-reporting tools, chess-bot repos (some explicitly engine-cheat bots — do not run those against the live program).

---

## 5. Videos & Writeups

1. **"My First Bounty: How I Broke Chess.com's 2FA Logic" — brQ, Medium, Apr 2026** — https://medium.com/@brqexe/my-first-bounty-how-i-broke-chess-coms-2fa-logic-657cd7956158 — Two findings: (a) **no rate limiting** on the 2FA OTP endpoint (500+ intruder attempts) → $100 ("No Rate Limiting on Critical Forms"); (b) **pre-auth session issuance**: server sets `ACCESS_TOKEN` immediately after password acceptance *before* OTP submission; the token authorized `GET /v1/users` with full account data → full 2FA bypass. Awarded payout discussed as $600+ bracket. **Prime regression-check target.**
2. **"Rook to XSS: How I hacked chess.com with a rookie exploit" — HN discussion, Jan 2024** — https://news.ycombinator.com/item?id=39144906 — re-upload filter checked `starts with https://chess.com` but missed the trailing path; researcher registered `chess.com.<their-domain>` as a trampoline redirect and got past the same-origin check. Lesson: their origin-prefix string checks are historically weak — **redirect_uri / open-redirect and upload-flow validation remains a high-value zone.**
3. **"I got my First Bounty from Chess.com" — StvRoot, InfoSec Write-ups, Oct 2025** — profile "Status" field: payload `/*/prompt(document.cookie)/*/` caused a client-side JS crash that hid the profile from everyone (self-DoS). Also claims multiple bugs were declined — title suggests some reports were refused (likely DoS/UI-bug exclusions).
4. **ibrahimibrahimi/bug-bounty-leaks-in-websites — chess.com recon set (May 2026)** — https://github.com/ibrahimibrahimi/bug-bounty-leaks-in-websites — claims **UUID v1 badge IDs** in `/api/badge/{uuid}`: time-based, enumerable, embedding server MAC + timestamp (4 collected UUIDs, two server nodes), plus a claimed token/display-name leakage chain. **Treat as unverified third-party claims, not confirmed findings** — good seed material, not evidence.
5. **"How New Anti-Cheating Technology Is Changing Chess" — chess.com blog, ~Feb 2026** and **"Proctor Eliminates Most Cheating in Prize Events"** — public anti-cheat state of play (see §2).
6. **"How to Catch a Cheater on Chess.com" — chess.com blog, Sep 2025** — enumerates the detection signals (engine match, timing, account history) — useful to understand what server-side signals exist if testing game-logic surfaces.

No disclosed HackerOne *hacktivity* reports for chess_com surfaced in this pass (policy routes reports to email; disclosed-report visibility is uncertain). 

---

## 6. Asset Inventory (passive, from crt.sh 2026-09-26)

Pulled via `https://crt.sh/?q=%25.chess.com&output=json` (9,583 lines; sampled across the full range). Union of distinct subdomains observed — **all in scope under the policy (chess.com domain)**:

**Core / API / infra**
- `chess.com`, `www.chess.com`
- `api.chess.com` (internal API; `api.chess.com/pub` is the public API host), `services.chess.com`, `client-metrics.chess.com`
- `external.oauth2.chess.com` (OAuth 2.0 server)
- `live.chess.com`, `live3.chess.com`, `play.chess.com`, `4player.chess.com`, `4player-beta.chess.com` (live-game surfaces)
- `admin.chess.com` (reported by third-party recon; not confirmed live in CT sample)
- `*.mx-sat.chess.com` / `mx-sat.chess.com` (mail/satellite infra)
- `telos.broadcast.chess.com`, `ams.broadcast.chess.com`, `dev1.broadcast.int.chess.com` (event broadcast stack; a `dev1` internal-name host is interesting)

**Product verticals**
- `news.chess.com`, `blog.chess.com`, `events.chess.com`, `clubs.chess.com`, `go.chess.com`, `merch.chess.com`, `shop.chess.com`, `pogchamps.chess.com`, `friend.chess.com`, `brand.chess.com`, `er.chess.com`
- `chess24.chess.com` (Chess24 integration — acquired property, on-domain)
- `treasure.chess.com`, `variants.chess.com`, `variants-beta.gcp-prod.chess.com`, `variants-beta-alb.gcp-prod.chess.com` (**GCP-hosted; `-beta` hostnames = pre-prod, classic weak-config zone**)
- `ccccms.chess.com`, `ccccms-beta.chess.com`, `cccfiles.chess.com`, `newman.chess.com` (Computer Chess Championship stack; `newman` = Postman/Newman test runner — possible exposed test harness)
- `proctor.chess.com` (prize-event proctoring), `recommendation.chess.com`, `speech-audio-service.chess.com`, `speech-audio-cdn.chess.com`

**Assets / CDN**
- `assets-chess`, `assets-ds`, `assets-sdui`, `assets-experiments`, `assets-design-system`, `assets-courses`, `assets-themes`, `r2-assets-themes` (Cloudflare R2), `assets-flair`, `assets-coaches`, `assets-chess-engine`, `sitemap`

**Support (localized)**
- `support`, `ayuda`, `suporte`, `destek`, `hulp`, `dovidka`, `podrska`, `pomoc`, `arsupport`, `supporto` — third-party help-desk surface in many languages

**Caveats:** crt.sh shows *certificates*, not live hosts — presence ≠ reachable. No resolution or probing was performed (passive only). Interesting follow-ups for later (non-intrusive) recon: the `*-beta` GCP hosts, `newman.chess.com`, `dev1.broadcast.int.chess.com`, `external.oauth2.chess.com`, `recommendation.chess.com`.

---

## 7. Hypothesis Seeds (concrete, in-scope, testable by the researcher with own test accounts)

> Each hypothesis names the policy bracket it maps to. Nothing below has been tested — they are prioritized starting points.

**H1 — OAuth `redirect_uri` validation bypass on `external.oauth2.chess.com`** (Broken auth, $600–$800)
- *Hypothesis:* the Chess.com OAuth 2.0 server's redirect validation has the same class of weakness as the 2024 "Rook to XSS" re-upload bug (prefix/string checks rather than strict host parsing), allowing an authorization-code leak to an attacker host via a crafted `redirect_uri` (e.g. `https://chess.com.attacker.tld`, `https://chess.com%2eattacker.tld`, path-traversal on a whitelisted domain).
- *Why this target:* OAuth is on-domain, newly public, documented only in a Notion page (immature surface); the 2024 trampoline finding is direct precedent on this exact engineering culture.
- *Expected observation:* authorize endpoint 302s to the attacker-controlled URI with `?code=...` instead of rejecting it.
- *Vuln class:* open redirect / OAuth redirect mismatch → account takeover chain.

**H2 — 2FA pre-auth token regression** (Broken auth, $600–$800; regressions pay half)
- *Hypothesis:* the Apr-2026 brQ finding (usable `ACCESS_TOKEN` issued between password acceptance and OTP completion) is incompletely fixed or regressed on an alternate login path (mobile API, `external.oauth2` login, password-reset-login, "login as" support flows).
- *Why this target:* known-vuln class on this exact target, paid before, fix may be path-specific; policy pays half for regressions.
- *Expected observation:* a session token obtained pre-OTP authorizes `GET /v1/users` or other authenticated endpoints.
- *Vuln class:* authentication bypass / 2FA bypass.

**H3 — IDOR/BAC on club admin and tournament management endpoints** (App logic bypass, up to $400)
- *Hypothesis:* club-scoped admin actions (kick/promote member, edit club settings, manage club matches, tournament creation/registration controls) are keyed by guessable numeric IDs with missing ownership checks, letting a regular member act as club admin.
- *Why this target:* clubs/tournaments are the richest role hierarchy on the site (member → admin → super-admin); `clubs.chess.com` + PubAPI club endpoints confirm a large club API surface; classic IDOR territory.
- *Expected observation:* as Member-A, replaying an admin-only request with Member-B's club/member ID succeeds.
- *Vuln class:* IDOR / broken access control.

**H4 — UUID v1 enumeration on profile/badge objects** (App logic bypass, up to $400; PII leakage up to $200)
- *Hypothesis:* internal `/api/badge/{uuid}` (PUT/PATCH) accepts time-ordered UUID v1 identifiers, letting an attacker enumerate neighboring IDs to read or **assign** other users' badge/profile objects.
- *Why this target:* a May-2026 third-party recon repo documents v1 UUIDs with decodable server MAC + timestamp from `/settings/profile` traffic; PUT/PATCH on the same resource pattern is the escalation.
- *Expected observation:* neighboring UUIDs return other users' objects; a write request modifies an object you don't own.
- *Vuln class:* IDOR via predictable identifiers. (Verify the endpoint still behaves this way; the source repo is unverified.)

**H5 — Paid-feature unlock via lesson/puzzle/Game-Review API tampering** (App logic bypass, up to $400)
- *Hypothesis:* premium-gated actions (Game Review depth, lessons, drills, "insights") are enforced client-side or via a flippable API flag, so manipulating lesson-completion or entitlement endpoints grants unpaid membership features.
- *Why this target:* the policy's own edit history (v0.1.1) explicitly scoped **"obtaining unpaid-for membership features"** — the program has paid for this class before; gaming sites commonly leave entitlement checks in the client.
- *Expected observation:* API response flips `is_premium`/`entitlement` or premium content endpoints return full data for a free account.
- *Vuln class:* application logic bypass. (Stay within test accounts; do not redistribute unlocked content.)

**H6 — Fair-play report / user-report API abuse and account-flag oracle** (App logic bypass or PII, up to $200–$400)
- *Hypothesis:* the report-abuse endpoint (`!` icon flow) lacks rate limiting or leaks whether a target account was actioned; alternatively the PubAPI `status` field (`closed:fair_play_violations`) plus report-response differentials create a per-user enforcement oracle.
- *Why this target:* reporting is a state-changing, low-friction endpoint every logged-in user can hit; the 2026 "publicly marked cheaters" change shows enforcement state is now user-visible.
- *Expected observation:* response/timing differences reveal whether the reported account was closed, or mass-reporting triggers automated action against a test account.
- *Vuln class:* missing rate limiting / information disclosure. (Do NOT mass-report real users — test accounts only.)

**H7 — Matchmaking / game-creation parameter tampering for rating manipulation** (App logic bypass, up to $400)
- *Hypothesis:* live-game creation or result-submission endpoints accept client-supplied parameters (time control, rated flag, opponent, result) without server-side validation, enabling rating inflation or forced wins between two controlled accounts.
- *Why this target:* highest-value gaming-logic zone; policy history suggests cheats/logic abuse are in scope; two test accounts make this safely demonstrable.
- *Expected observation:* a game created/submitted with tampered parameters (e.g. `rated=true` on an unrated variant, or a result payload for a game never played) alters Glicko ratings.
- *Vuln class:* application logic bypass. (Use only your own two test accounts; never involve real opponents.)

**H8 — Streamer verification / `twitch_url` linkage without ownership proof** (App logic bypass or PII, up to $200–$400)
- *Hypothesis:* the profile settings flow that sets `is_streamer`/`twitch_url` accepts an arbitrary Twitch URL without verifying channel ownership, granting streamer badges/perks and a trusted profile marker to an impostor account.
- *Why this target:* PubAPI exposes `is_streamer` + `twitch_url` as first-class profile fields, implying a linkage flow; ownership-verification gaps in social-link features are a recurring bug class.
- *Expected observation:* linking `twitch_url` to a channel you don't own sets `is_streamer=true` with no verification step.
- *Vuln class:* broken access control / verification bypass.

**H9 — Password-reset / email-change token predictability or host-header poisoning** (Broken auth, $600–$800)
- *Hypothesis:* the reset flow issues tokens with insufficient entropy, or reset emails build links from the `Host` header, enabling token theft via a poisoned host on `chess.com` (classic when password-reset sits behind the same Cloudflare edge as other vhosts).
- *Why this target:* auth-reset is the single highest-payout non-RCE class in this policy ($600–$800); reset flows are historically the weakest auth link.
- *Expected observation:* reset link reflects an attacker-supplied Host, or tokens are sequential/low-entropy.
- *Vuln class:* account takeover.

**H10 — `*-beta` / `newman` / `dev1` pre-prod hosts with weaker controls** (varies; misconfig up to $150+)
- *Hypothesis:* one of the CT-visible pre-prod hosts (`variants-beta.gcp-prod.chess.com`, `variants-beta-alb.gcp-prod.chess.com`, `ccccms-beta.chess.com`, `newman.chess.com`, `dev1.broadcast.int.chess.com`) exposes debug endpoints, verbose errors, or an unprotected admin/test console.
- *Why this target:* they are in-scope (chess.com domain), cert-active, and pre-prod naming strongly correlates with weaker hardening; `newman` suggests an exposed API test runner.
- *Expected observation:* directory listing, debug toolbar, stack traces, or an accessible test console on the beta host.
- *Vuln class:* security misconfiguration / information disclosure. (Read-only inspection only; do not interact with any console found.)

---

## 8. Notes, gaps, and recommended next steps

- **Unverified items:** payment processor identity; mobile-app SSO providers; exact PubAPI rate limits; whether the HackerOne handle currently accepts reports (policy says email-first — submit via bounties@chesscom.atlassian.net and reference the program); whether `admin.chess.com` resolves; the UUID-v1 badge claims (third-party only).
- **Do not touch:** ChessKid / Chessable (out of scope); automated scanners (excluded by policy); DoS testing; real-user accounts; anything during live events; social engineering.
- **Suggested sequencing for the testing agent:** H2 (regression re-check, fastest) → H1 (OAuth, highest payout potential) → H4/H3 (IDOR, most likely to yield) → H5/H7 (game logic, needs two test accounts) → H9 (reset flow) → H10 (beta hosts, read-only) → H6/H8.
- **Useful reference URLs:** policy (above); PubAPI docs https://www.chess.com/news/view/published-data-api; fair-play explainer http://chess.com/cheating; support KB https://support.chess.com; org https://github.com/ChessCom; program https://hackerone.com/chess_com.

*End of report — passive recon complete 2026-09-26. No active testing performed.*
