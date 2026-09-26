# Live Nation — Deep Recon Report (PASSIVE ONLY)

**Date:** 2026-09-26 · **Method:** public web sources only (no scanning, probing, logins, or automated traffic)
**Sibling plan:** `~/workspace/hacker-agent/intel/deep-hunt-plan.md` (hypotheses L-1–L-10 already drafted there — this file does NOT duplicate them; Section 7 seeds are NEW)
**Program status at time of writing:** LIVE on HackerOne.

> ⚠️ **HUMAN-OPERATED DISCOVERY ONLY.** Live Nation's policy explicitly bans "bots, automated scanning tools, LLMs, or generative AI in the discovery of bugs. We only accept bugs found by humans." Passive intel-gathering (this report) is fine; every hypothesis in Section 7 is marked **human-operated-only**: a human drives the browser/devtools, the agent may only plan, analyze, and write the report.

---

## 1. Live policy (fetched live 2026-09-26 from https://hackerone.com/live_nation)

Program handle **verified via HackerOne directory search** (directory lists "Live Nation — Managed — Offers bounties $50 minimum bounty — hackerone.com/live_nation"). Public policy page carries the header **"HackerOne Program Policy – Proposed Public Launch Policy"**.

### Program rules
**Must:**
- Provide detailed, reproducible reports; one bug per report unless chaining is required.
- Create accounts using the HackerOne email alias (`<h1username>@wearehackerone.com`) and comply with terms of use.
- Identify all testing traffic with header **`X-HackerOne-Research: <H1 username>`** (mandatory — browser-task traffic cannot inject this; tests needing the header are operator-manual/proxy-only).

**Must not:**
- Use bots, automated scanning tools, LLMs, or generative AI in discovery. Human-only bugs.
- Test/interact with anyone else's accounts.
- Test unlisted sites/hostnames/domains — **assets not explicitly listed are out of scope by default.**
- Send excessive traffic or DoS test.
- Access internal systems/admin endpoints/other people's data (if an exposed internal system is found: stop and report, do not explore).
- **Publicly disclose findings of any kind — strictly prohibited**, including after remediation/closure. Violation risks bounty forfeiture + removal.

**Submission requirements:** clear repro steps + proof of impact, private submission, only own accounts/data, first reproducible report wins (no duplicate payouts), minimum data necessary, **redact all PII/credentials**, **do NOT name specific artists, event names, or team names in reports**.

### Rewards
- Monetary bounties for valid in-scope reports; **minimum $50** (directory listing). Awards scale with severity and demonstrated impact **per the In-Scope Asset Table** — the per-severity ranges live in that table, which was **not visible in the public snapshot** (requires logged-in HackerOne session; mark as *unverified — confirm in-session before testing*).

### Bug scope
**In scope:** account takeover · privilege escalation · IDOR · **authentication, MFA, and OTP bypass** · **identity verification (IDV) bypass** · SQL/NoSQL injection · command injection · RCE · SSTI · CSRF **with demonstrable real-world impact** · SSRF · **DNS subdomain takeover** · insecure deserialization · unauthorized access to sensitive data incl. personal/payment data · hard-coded/exposed secrets with demonstrated exploitability · **SafeTix 2.0 bypass** (see below) · **onsale queue exploitation (reaching the front of the queue without waiting)** · **ticket transfer bypass (transferring tickets without MFA)**.

**Out of scope:** HackerOne core ineligible list, plus: **XSS (all)** · missing/misconfigured security headers without proof of impact · bugs requiring unrealistic user interaction · DoS · social engineering (phishing/vishing/smishing/quishing) · physical security testing.
**Out-of-scope assets:** third-party platforms not owned/operated by Live Nation · internal/corporate/VPN/employee infra · dev/staging/QA/test unless explicitly listed · deprecated apps/domains.

### SafeTix 2.0 campaign (standing section of the policy)
Policy definition: SafeTix 2.0 "keeps a digital ticket on a fan's mobile device and prevents it from being transferred outside the Ticketmaster chain of custody."
**In-scope bugs:** tickets transferred to another account **without MFA or OTP** · a ticket barcode rendered off the fan device · **creation of new tickets**.
**A bypass qualifies if, without an authorized transfer within the Ticketmaster ecosystem:**
- a ticket is rendered and successfully scanned on an unbound/unauthorized device outside a Ticketmaster account;
- a ticket is duplicated so multiple devices scan successfully outside chain of custody;
- a ticket is made scannable after violating device limits, untrusted-device enforcement, or partner restrictions;
- a ticket is made scannable via legacy/fallback paths (**wallet, web, compatibility mode**).

**Rules of engagement:** use ONLY test tickets provided on request · all device types/OS/networks permitted · **rooted/jailbroken device testing permitted** · replay/capture/duplicate/externally-reproduce visible barcodes permitted for test events · test on the **most current mobile app version** (iOS + Android).
**Evidence required:** device model + OS, app version (+SDK version if visible), account state, network condition, event tested, scanner mode (online/offline), high-level repro steps, screenshots/video with timestamps, severity classification: Critical (unauthorized device scans) / High (scannable artifact produced outside custody) / Medium (bypass under unlikely conditions) / Low (UX/logging/messaging).
> Expected-behavior carve-out: **low-risk accounts over 90 days old transferring to other low-risk 90-day-old accounts is EXPECTED behavior** — exclude it or the report dies as N/A.

### Persona / Artist Sign-Up verification campaign (dedicated, time-boxed test event)
- Objective: demonstrate **verification steps bypassed** in the Artist Sign-Up (ASU) flow.
- **Only two areas accepted:** (1) bypassing Persona identity verification during sign-up; (2) bypassing the ASU screen itself.
- A bypass = **MFA/OTP circumvented to and/or from high-risk accounts**; "if you are able to complete a sign-up, reach a post-verification state, or otherwise progress through the flow without a valid Persona verification having occurred, that is a reportable finding."
- **Authorized scope: the isolated test event ONLY — https://signup.ticketmaster.com/bugbountytest** (live on production infra but isolated). Testing any other live event or production sign-up flow is out of scope.
- Rooted/jailbroken permitted; rooted/jailbroken device testing permitted; all networks permitted.
- Evidence: browser name+version, account state, network, event tested, scanner mode, repro steps, screenshots/video with timestamps, severity classification (same 4-tier scale).
- **ASU flow (policy-documented):** 1. Landing (test event URL) → 2. Account creation (username+password) → 3. Email verification → 4. Phone verification → 5. Redirect to IDV → 6. Persona verification (photo ID + selfie match) → 7. Completion.
- **Both campaigns confirmed live in the policy on 2026-09-26.** ✅

---

## 2. Architecture & technology (public sources)

### SafeTix internals (public reverse-engineering research + press)
- SafeTix ("Presence"/"Secure Entry") is a **rotating barcode** (introduced 2019) replacing static PDF417/QR. Public research (walt-app/walt-passes-android `docs/research/rotating-credential-tickets.md`, GitHub, current as of Sept 2026) documents the payload:
  `[base64 Bearer <redacted> (~48 bytes)] :: [6-digit eventKey TOTP] :: [6-digit customerKey TOTP] :: [unix timestamp]`
- The two 6-digit codes are **RFC 6238 SHA-1 TOTPs at a 15-second timestep**, from 20-byte hex secrets: an **eventKey** (per event) and **customerKey** (per ticket holder). PDF417 in the US; QR in EU — identical payload structure.
- The visible shimmer/animation is CSS-only; only the codes+timestamp rotate. **Generation is fully client-side** once secrets are provisioned — the mobile app, the web client (`presence-secure-entry.js` / `generateSignedToken`), and Google Wallet all compute the TOTP locally. No per-display server roundtrip.
- **Secrets are re-issued ~20 hours before each event** via the Ticketmaster **Order Management endpoint**; partner integrations must fetch the encrypted Rotating Entry Token at display time (partner API gated, contract-only).
- At the gate, scanners validate the timestamp window, recompute both TOTPs from server-held keys (or pre-synced cache), and look up the Bearer <redacted> for ticket/seat ownership **before burning it**. Some venues use SDK-based **offline verification**.
- Security properties that matter for testing: the **Bearer <redacted> is the real identity**; rotating TOTPs are an anti-screenshot layer that fails closed on static screenshots. The Ticketmaster app ticket Activity sets **`FLAG_SECURE`** (blocks screenshots, recents thumbnails, accessibility bitmap retrieval). PKPASS/webServiceURL push is rate-capped far below 15s rotation cadence.
- Independent reverse-engineered SafeTix renderers exist (TicketGimp, Amosa, Secure.Tickets) but require DevTools secret extraction from an authenticated session — **do not replicate; they are the subject of active litigation and violate TM ToS** (noted here only to explain the threat model the program wants defended).
- DOJ antitrust filings (2024–2026) describe SafeTix as the mechanism "designed to force all ticket transfers to occur within the Ticketmaster platform" — transfers are the single most-guarded state machine.

### Onsale queue / Verified Fan (public docs + press)
- **Verified Fan**: pre-registration per tour; TM assesses human-vs-bot signals (past purchase history, social handles, phone/email); selected fans get a **unique code tied to their account** that "can't be shared" (per Ticketmaster's own description). Two ticket limits per order are common on high-demand sales.
- **Artist Presale (newer model)**: no codes — "your account is recognized when you go to join the queue"; signup window → waiting room 15–30 min before sale → randomized place in line at sale start. Signup requires sign-in + email/phone on file.
- Bot defense stack: **Akamai Bot Manager** (Ticketmaster blocks ~200M bots/day per company statement; 5B/year NA historically) and **Queue-it virtual waiting rooms** — Akamai+Queue-it launched the joint "Hype Event Protection" (Oct 2025): Queue-it throttles traffic in, Akamai Bot Manager fingerprints, bots are blocked or re-queued to the back at sale open. Randomization of queue position at onsale time is the documented fairness mechanism.
- Policy names "onsale queue exploitation: reaching the front of the queue without waiting" explicitly in scope — the realistic seams are client-side position tokens/cookies and waiting-room→sale handoff parameters.

### Account & auth model (public help docs)
- Ticketmaster accounts: **email + password**, email verification at signup; profile/password changes behind login.
- **2FA exists as email/SMS one-time codes** — "verification code when signing in from a new device"; password changes trigger "Authenticate Your Account" with OTP via text or email. **Sensitive actions (transfer, profile/password change) prompt OTP** — these custom sensitive-action OTP paths (not the commoditized login OTP) are the higher-value seam.
- Password reset: "Forgot Password" → reset instructions emailed to registered address → link-based reset. Standard single-use/expiring-token model expected (unverified — needs in-flow observation).

### Mobile apps & web
- Ticketmaster mobile app (iOS/Android) — primary SafeTix surface; FLAG_SECURE ticket Activity; Google Wallet "Add to Wallet" via PayClient SDK intent or auto-verified App Link; Apple Wallet via companion-app pattern.
- Web client ships `presence-secure-entry.js` with `generateSignedToken` for browser barcode rendering (web fallback = a policy-named bypass vector).
- **signup.ticketmaster.com** hosts the ASU flow (campaign host).
- Public developer surface: `developer.ticketmaster.com` portal, `app.ticketmaster.com/discovery/v2/` (Discovery API, key=query param, 5k/day free), Commerce/Partner APIs (`app.ticketmaster.com/partners/v1`). Partner API is contract-only and gated.

---

## 3. Third parties & partners

| Party | Role | Source |
|---|---|---|
| **Persona** (withpersona.com) | Identity-verification vendor for the ASU campaign (photo ID + selfie match). Public SDKs: `persona-id/*` on GitHub (inquiry-android-2 etc.); inquiry flow = create inquiry → user completes hosted flow → poll status (`completed/approved/declined/needs_review`) → approve/decline; supports **`redirect_uri`** on inquiry completion (added in Android SDK v2.29.0, Nov 2025); webhooks: `inquiry.completed`, `verification.passed/failed`, etc. | Persona GitHub + hookdeck webhook-skill docs |
| **Akamai** | Bot Manager (bot detection/mitigation); CDN/WAF layer for ticketmaster.com (Akamai x Queue-it "Hype Event Protection") | PR Newswire Oct 2025; TM statements |
| **Queue-it** | Virtual waiting room / queue randomization | PR Newswire Oct 2025 |
| **Adyen** | Payment processing (Ticketmaster **Spain** selected Adyen, 2022). Global processor mix unverified — **third-party payment platforms are out of scope**; do not test them | appsruntheworld customer record |
| **Google Wallet / Apple Wallet** | SafeTix wallet fallback paths — **policy explicitly names wallet fallback as a bypass vector** (ticket scannable via legacy/fallback paths) | Live Nation policy §SafeTix 2.0 |
| **Bazaarvoice** | Reviews UGC (`ticketmaster.ugc.bazaarvoice.com`) — third-party, out of scope | EFF HTTPS Everywhere atlas |

> Note: out-of-scope rule "third-party platforms or services not owned or operated by Live Nation" excludes the vendors themselves; the *integration seams* on Live Nation's own hosts (e.g., how TM consumes Persona's callback, how TM provisions wallet passes) remain the target.

---

## 4. Code & repos (public)

- **Official org: https://github.com/ticketmaster** — "Ticketmaster® & Live Nation Entertainment®", active (repos updated Sept 24–25, 2026 at time of check; languages: TypeScript, Go, Swift, Rust, Java, Starlark). Repo names render via JS — enumerate in a human browser session before relying on any specific repo; the org itself is the verified source.
- **Developer portal:** https://developer.ticketmaster.com — Discovery API v2 docs, Commerce API, Partner API docs, API explorer. Discovery API is read-only catalog data (low security value) but its SDKs reveal API conventions, auth patterns, and internal host naming.
- **Public Postman/OpenAPI collections** exist for the Commerce API (via api-evangelist mirror) — useful for learning TM's API envelope/auth conventions passively.
- **No official SafeTix SDK is public** — the closest public artifacts are the third-party research docs (walt-app research, Conduition's writeup via 404 Media/Engadget) and TM's own `presence-secure-entry.js` shipped to browsers (observable in a human session on an owned ticket page).

---

## 5. Videos, writeups & disclosed reports

- **Disclosed HackerOne reports for live_nation: NONE findable — and none will ever be.** The policy bans public disclosure of any kind, so the program's 5 resolved reports (per plan snapshot) are permanently private. Do not expect disclosure; treat all prior findings as unknown (duplicate risk is real but unmeasurable).
- **SafeTix reverse-engineering writeup:** anonymous researcher "Conduition" published SafeTix barcode generation details (Feb 2024; reported by 404 Media/Engadget, "Hackers reverse-engineer Ticketmaster's barcode system to unlock resales on other platforms"). Publicly confirms the TOTP-based mechanism and that codes are generated shortly before events.
- **walt-app/walt-passes-android** research docs (`rotating-credential-tickets.md`, ADR-0006) — the most detailed public SafeTix mechanism reference (payload format, FLAG_SECURE, wallet provisioning, partner API gating). https://github.com/walt-app/walt-passes-android/blob/HEAD/docs/research/rotating-credential-tickets.md
- **DOJ v. Live Nation antitrust filings** (2024–2026) — describe SafeTix transfer-lock design and internal "game-changer" framing of non-transferable tickets; useful for understanding which transfer paths the business guards hardest.
- **No hunter writeups specific to this program** exist publicly (Sept 2026 launch + no-disclosure rule). General ticketing/queue logic writeups (virtual waiting room bypasses, presale-code sharing) exist but are not Live Nation-specific.

---

## 6. Asset inventory (passive only)

**⚠️ Gap:** direct `crt.sh` JSON pulls for `%.ticketmaster.com` / `%.livenation.com` timed out at the transport layer during this session (2026-09-26); subdomain enumeration via crt.sh is **not completed** and must not be assumed. What is confirmed from public sources:

| Host | Role | Source |
|---|---|---|
| `signup.ticketmaster.com` | ASU campaign host (`/bugbountytest` — test ONLY this path) | Live policy verbatim |
| `www.ticketmaster.com` | Main storefront/checkout/account | Public knowledge; EFF atlas |
| `app.ticketmaster.com` | Discovery/Partner APIs (`/discovery/v2`, `/partners/v1`) | Dev docs, api-evangelist |
| `developer.ticketmaster.com` / `developer-acct.ticketmaster.com` | Developer portal + account | Public docs |
| `help.ticketmaster.*` (at/nl/de/be/dk/se/…) | Help center (Zendesk) — third-party hosted, likely out of scope | Help articles |
| `livenation.com` / `www.livenation.com` | Live Nation corporate + event listings | Public |
| `secure.store.ticketmaster.com`, `ticketsnow.ticketmaster.com`, `metrics.ticketmaster.com` | Store, resale legacy, analytics — historical; treat as *unverified current scope* | EFF atlas (dated) |

**Critical:** the policy says "Assets not explicitly listed are out of scope by default" and the real In-Scope Asset Table requires a logged-in HackerOne session. **Re-pull the asset table in-session before touching any host** — do not test hosts from this table on assumption.

**L-10 (subdomain takeover) feed:** check only hosts from the in-session asset table against dangling-CNAME fingerprints; no unlisted hosts.

---

## 7. NEW hypothesis seeds (human-operated-only; grounded in this recon; no overlap with L-1–L-10)

> Legend: **H** hypothesis · **W** why this target · **EO** expected observation · **VC** vuln class.
> All marked 🔴 **HUMAN-ONLY** per program rule (human drives browser/devtools; agent plans/writes).
> All use `X-HackerOne-Research: shiva92` header where raw requests are needed (operator-manual/proxy path), own accounts only, test tickets only where tickets are involved.

### NH-1 — Wallet fallback remains scannable after transfer/revocation (SafeTix legacy path)
- **H:** A SafeTix ticket added to Google Wallet ("Add to Wallet" via the PayClient/App-Link flow) is provisioned as a wallet object holding the TOTP secrets or a long-lived render token. After the ticket is transferred to account B (or voided/refunded) on the web, the wallet object on account A's device is not revoked and remains scannable.
- **W:** The policy *explicitly* names "a ticket made scannable via legacy or fallback paths (wallet, web, compatibility mode)" as a bypass definition — the program is inviting exactly this test. Public research shows wallet provisioning carries secrets to the device.
- **EO:** After authorized transfer A→B of a test ticket, account A's Google Wallet pass still renders a barcode that a test scanner accepts (or the pass object remains valid per wallet APIs).
- **VC:** SafeTix 2.0 bypass (High per policy: "scannable artifact produced outside custody").
- 🔴 HUMAN-ONLY. Needs test ticket + two devices/wallet.

### NH-2 — Post-transfer secret non-revocation: old holder's app still renders valid barcodes
- **H:** SafeTix barcode validity is checked by recomputing TOTPs from server-held `eventKey`/`customerKey`. After an authorized transfer A→B, the server rotates the `customerKey`; but if rotation is lazy/eventual, A's app (holding the old secrets, offline) still renders barcodes that scan within the timestamp window.
- **W:** Public mechanism: secrets are per-ticket-holder and re-issued ~20h pre-event via Order Management; the scanner looks up the Bearer <redacted> for ownership before burning. The race between "transfer recorded" and "old secrets invalidated" is the seam; scanners with pre-synced offline caches widen it.
- **EO:** Within a window after A→B transfer, A's device (airplane mode) renders a barcode that the test scanner accepts, or the Bearer <redacted> resolves to the ticket without ownership rejection.
- **VC:** SafeTix 2.0 bypass — duplicated ticket scanning outside chain of custody (Critical per policy if a second device scans).
- 🔴 HUMAN-ONLY. Test tickets on request; record timing precisely.

### NH-3 — Resale listing double-spend: listed ticket still scannable by the lister
- **H:** Listing a ticket for resale transitions it to a "listed" state, but the lister's app retains render capability until a buyer actually completes purchase. During the listed window the same ticket is both for sale AND scannable by the lister (or transferable again), creating a double-spend.
- **W:** Ticketmaster resale is core revenue (DOJ filings: SafeTix designed to keep resale inside TM). The listed→sold transition is a distributed state change across listing service, wallet provisioning, and scanner burn lists — exactly where desync hides. Distinct from L-4 (which is about MFA on transfer, not listing-state validity).
- **EO:** Test ticket listed for resale still renders a scannable barcode in the lister's app, or can be transferred a second time while listed.
- **VC:** Business logic / SafeTix bypass (ticket usable outside chain of custody while listed).
- 🔴 HUMAN-ONLY. Own test ticket; cancel/delist immediately after observation.

### NH-4 — Verified Fan code accepted cross-account (missing account binding)
- **H:** Verified Fan codes are described as "unique code tied to your account… can't be shared." If the code→account binding is enforced only in UI copy (or only at code-issuance display) and not server-side at redemption, account B can redeem account A's code at checkout.
- **W:** Classic issuance-vs-redemption asymmetry; the policy's in-scope list covers authz failures and the VF flow is custom TM logic (not a commoditized IdP). Distinct from L-5 (queue position) — this is presale *entitlement* binding.
- **EO:** Code issued to account A, entered in account B's presale checkout session, is accepted and unlocks the presale.
- **VC:** Authorization / business-logic bypass (presale entitlement theft).
- 🔴 HUMAN-ONLY. Two own accounts; use only a real VF registration the researcher legitimately received — never harvest others' codes.

### NH-5 — ASU campaign: replaying a completed Persona inquiry (state binding, not verification skip)
- **H:** After Persona completes, the redirect back to `signup.ticketmaster.com/bugbountytest` carries an inquiry/session reference. If the ASU backend marks "verification done" from a replayable parameter (inquiry ID, signed token without nonce/expiry, or a simple `verified=true` flag) rather than server-side polling of Persona's API, an attacker can replay a previous *own* completed inquiry (or a tampered reference) to reach post-verification state for a *new* signup without a fresh Persona check.
- **W:** Persona's documented integration pattern is create-inquiry → hosted flow → **server-side poll/webhook** (`inquiry.completed`, `verification.passed`). The bug class is TM trusting the client-returned signal instead of polling — a different seam than L-1's "skip the Persona step" (L-1 attacks the step; NH-5 attacks the *callback/state binding*). Persona added `redirect_uri` support (SDK v2.29.0) — check whether TM's ASU accept
...[truncated 4349 chars]