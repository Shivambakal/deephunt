# Easy Bounties Shortlist — 10 softest paid programs (as of 2026-09-26)

Method: current HackerOne directory snapshot (2026-09-26) + verified policy pages fetched the same
day (Agoda Public, Wolt, Arc, common_codes) + public launch announcements (Adobe/Intigriti,
OpenAI/Bugcrowd, 1Password/Bugcrowd). Handles written as `hackerone.com/<handle>` only where the
handle was observed in fetched content or announcements; where the handle is unconfirmed the entry
says so — search the program name in the platform directory instead of guessing a URL.

Ranking = ease for a beginner-to-intermediate hunter: low competition (few resolved reports /
recent launch / platform migration churn), broad or wildcard scope, pays for Low findings,
demonstrated payout history, currently accepting reports. Entries marked HARD-SKILL are "less
hard", not genuinely easy — read the caveats.

---

## 1. Agoda Public — HackerOne (EASIEST, and you're already here)

- **Platform/link:** https://hackerone.com/agoda-public (verified live 2026-09-26)
- **Launch:** June 2026 public; private program since 2016 with hundreds of researchers — new-to-public, not immature
- **Resolved reports:** 0 (directory snapshot 2026-09-26); previously paid $576–$2,000 average
- **Min bounty:** $50; max reported in June 2026 launch announcement: $6,000
- **Scope (bounty-eligible):** agoda.com web/API, ycs.agoda.com, Rocketmiles, Hitrewards, mobile apps — core booking flows
- **Bounty guidance:** Critical (P1) / High (P2) / Medium (P3) / Low (P4) all eligible; eligible Lows include stored XSS, OTP weaknesses, auth rate limiting, reflected/DOM XSS, some open redirects
- **Softness (honest):** Genuinely beginner-friendly. Pays Lows, manual-only (no scanning needed or allowed), real booking/payment logic to poke. "0 resolved" is mostly real — the private program cleaned the obvious stuff years ago, but the public launch brings fresh scope and fresh eyes
- **Recon steps (read-only):**
  1. Read the full policy page top-to-bottom; map every listed asset into your scope file before touching anything
  2. Crawl agoda.com booking flow with proxy and enumerate every parameter the checkout/payment requests carry (names, hidden fields, currency/region fields)
  3. Test OTP and rate-limit behavior on your own accounts only (attacker-controlled credentials), watching for weak verification or unlimited attempts

## 2. Wolt — HackerOne (test accounts handed to you)

- **Platform/link:** https://hackerone.com/wolt (verified live 2026-09-26)
- **Launch:** July 2026 on HackerOne (migrated from Intigriti)
- **Resolved reports:** 0 (platform artifact — legacy Intigriti hall of fame is large, so the target is not untouched)
- **Min bounty:** $100; no average yet on H1
- **Scope (bounty-eligible):** wolt.com web + iOS/Android consumer/merchant apps; customer accounts self-registerable, specific consumer/venue test entities provided on the policy page
- **Restrictions:** must send `X-HackerOne-Research: [username]`; CSV injection, homograph attacks, enumeration, impact-less rate limiting, and most low-value web findings are excluded
- **Softness (honest):** Very good for a disciplined beginner. The exclusions list is long but *clear* — no guessing what gets paid. Food-delivery logic (addresses, orders, promos, courier/merchant flows) is a classic logic-bug surface. Legacy hunters know it, but the migration resets the crowd
- **Recon steps (read-only):**
  1. Follow the policy's test-account setup exactly; add the `X-HackerOne-Research` header to every request from the start
  2. Map consumer → merchant → courier API surfaces (the three roles are where access-control gaps live)
  3. Inventory promo/voucher/order-modification endpoints and note which parameters are client-controlled vs server-verified

## 3. Live Nation — HackerOne (brand new, $50 floor)

- **Platform/link:** HackerOne directory (search "Live Nation"; handle unconfirmed — do not guess it)
- **Launch:** September 2026
- **Resolved reports:** 5 (directory snapshot 2026-09-26)
- **Min bounty:** $50; average $500–$2,000
- **Scope:** verify on the policy page (expect livenation.com / ticketmaster.com ecosystem — confirm before testing)
- **Softness (honest):** Newest retail-adjacent program on the list. Five resolved reports means nearly zero competition on a ticketing empire (tickets, resale, refunds, artist pages, venues — huge state machine). Low floor of $50 invites Low findings
- **Recon steps (read-only):**
  1. Open the policy page first; copy the exact asset list and the testing-window rules (ticketing programs often restrict live-event timing)
  2. Enumerate subdomains/API hosts for ticketmaster.com + livenation.com (cert logs, DNS) and diff which belong to the program
  3. Trace the checkout/refund/resale flow with your own account; log every server-computed value (fees, seat holds, timers) for tampering candidates

## 4. Abercrombie & Fitch — HackerOne (retail = logic bugs)

- **Platform/link:** HackerOne directory (search "Abercrombie"; handle unconfirmed)
- **Launch:** July 2026
- **Resolved reports:** 64 (directory snapshot 2026-09-26)
- **Min bounty:** $50; average ~$750
- **Scope:** verify on policy page (expect A&F brand family: abercrombie.com, hollisterco.com, kids — confirm before testing)
- **Softness (honest):** Retail e-commerce is historically the softest target class: cart, pricing, promo codes, account merging, loyalty — all state machines built for shoppers, not adversaries. 64 resolved is moderate noise but the scope is wide and the $50 floor pays small stuff
- **Recon steps (read-only):**
  1. Open the policy page; list every brand domain and confirm which are bounty-eligible
  2. Walk cart → checkout → payment on a test order; record every client-submitted price/quantity/promo field
  3. Map loyalty/account APIs (points, returns, address book) — retail IDORs live here

## 5. Coupang Taiwan — HackerOne (marketplace, $50 floor)

- **Platform/link:** HackerOne directory (search "Coupang"; handle unconfirmed — the TW program is distinct from the Korean one)
- **Launch:** May 2026
- **Resolved reports:** 20 (directory snapshot 2026-09-26)
- **Min bounty:** $50; average $421–$448
- **Scope:** verify on policy page (expect Taiwan storefront + seller/buyer APIs — confirm before testing)
- **Softness (honest):** Marketplaces are three-sided (buyer/seller/platform) — that triples the access-control surface. Twenty resolved reports in four months is light. Sub-$500 average means they pay mid-severity logic bugs regularly, not just unicorns
- **Recon steps (read-only):**
  1. Open the policy page; separate buyer-scope from seller-scope endpoints
  2. Register buyer + seller test accounts (if policy allows) and map where the two roles' APIs diverge
  3. Trace listing → order → payout for any value the client can set (price, quantity, shipping) that the server should verify

## 6. Chess.com — HackerOne (pays small stuff, documented table)

- **Platform/link:** HackerOne directory (search "chess.com"; handle unconfirmed)
- **Bounty table (recon-repo data, May 2026 — re-verify on the policy page):** roughly $80–$4,000; observed paid examples: $100 info, $150 CORS, $250 XSS
- **Resolved reports:** check the current directory listing (data above is May 2026)
- **Scope:** web platform (chess.com) — verify exact assets on the policy page
- **Softness (honest):** One of the few programs with a *published track record of paying three-figure amounts for low findings*. Real-time game logic, chat, clubs, and puzzles are a huge interactive surface. Not "new", so no first-mover edge — but the payout floor is real
- **Recon steps (read-only):**
  1. Open the policy page; confirm the current bounty table and whether the $80 floor still holds
  2. Map the game-session and chat APIs — real-time features have the weakest authorization historically
  3. Enumerate club/forum/puzzle endpoints for object-reference patterns (IDs you can increment)

## 7. Arc (Circle) — HackerOne (HARD-SKILL: it's a blockchain)

- **Platform/link:** https://hackerone.com/arc-bbp (verified live 2026-09-26) — note: this is **Circle's Arc**, the blockchain, NOT the Arc browser company
- **Launch:** September 2026
- **Resolved reports:** 2 (directory snapshot 2026-09-26)
- **Min bounty:** $100; average ~$500
- **Scope/summary:** Circle's mission statement on the policy page; blockchain + stablecoin infrastructure — verify exact assets on the policy page
- **Softness (honest):** NOT genuinely easy. Crypto/blockchain targets attract serious researchers and the vuln classes (consensus, signing, key management) are advanced. Included because it's 2-weeks-old with 2 resolved reports — if you have any chain/API background it's thin competition; otherwise skip for entries 1–6
- **Recon steps (read-only):**
  1. Open the policy page; separate web/API scope from chain/protocol scope and pick only the side you understand
  2. Read Circle's Arc docs end-to-end (archived testnet faucets/explorers if listed) before designing any test
  3. Enumerate the API surface (RPC endpoints, indexers) and note auth boundaries

## 8. Common Codes (German EUDI wallet) — HackerOne (HARD-SKILL: gov ID wallet)

- **Platform/link:** https://hackerone.com/common_codes (verified live 2026-09-26)
- **Launch:** September 2026
- **Resolved reports:** 0 (directory snapshot 2026-09-26)
- **Min bounty:** $100
- **Scope:** German national/EUDI wallet source and released applications; backend source published; Android findings must be demonstrated against the released app/backend (no static-only reports)
- **Softness (honest):** New and source-assisted, which is rare — but it's a government digital-identity wallet. The attack surface is narrow, the code has had heavyweight review, and "demonstrate against the released app" raises the bar. Included for source-code hunters; not a beginner's first target
- **Recon steps (read-only):**
  1. Open the policy page; confirm exactly which repos/releases are bounty-eligible
  2. Clone the published backend source and map the trust boundaries (issuance, storage, presentation of credentials)
  3. Diff the released Android app against the published source for build-level discrepancies

## 9. OpenAI Safety Bug Bounty — Bugcrowd (new vuln class, thinner crowd)

- **Platform/link:** Bugcrowd (search "OpenAI" on bugcrowd.com; program announced March 2026)
- **Launch:** March 2026 (AI-safety scope; distinct from older infra programs)
- **Resolved reports:** check the Bugcrowd listing (data unconfirmed at snapshot)
- **Min bounty:** check the program brief (unconfirmed at snapshot)
- **Scope:** AI safety issues — prompt injection, jailbreaks with security impact, model-abuse paths — verify the brief for the exact list
- **Softness (honest):** Traditional web hunters are weak here, so competition from the usual crowd is lower. But OpenAI is a mature security org and the *bar for a valid AI-safety finding is high* — "the model said something bad" is not a bounty. Best if you enjoy prompt-level tinkering and can show real impact (data exfil, action execution, guardrail bypass with consequence)
- **Recon steps (read-only):**
  1. Read the Bugcrowd brief end-to-end; separate "we pay for this" AI classes from the standard exclusion list
  2. Study the disclosed/similar AI findings to learn what "impact" looks like for this program
  3. Build a local prompt-injection test lab (your own API key, your own data) before touching anything in scope

## 10. Adobe — Intigriti (fresh platform, new AI scope — but a shark tank)

- **Platform/link:** Intigriti (search "Adobe" on intigriti.com; migration announced on the Adobe Security Blog, effective 2026-09-01)
- **Launch:** September 1, 2026 on Intigriti (program existed for years on HackerOne)
- **Resolved reports:** high historically (mature program) — the reset is the *platform*, not the target
- **Max bounty:** up to $15,000 (new AI-scope Critical); legacy HackerOne tiers: Tier 1 Critical $5K–$10K / High $1K–$5K / Medium $200–$1K / Low $100–$200
- **Scope:** broad Adobe web portfolio + NEW dedicated AI scope: Acrobat AI Assistant, Acrobat PDF Spaces, Express AI Assistant, Firefly image/video/custom models, Lightroom AI edits, Photoshop AI Assistant, Stock AI Studio (per Adobe Security Blog, 2026)
- **Softness (honest):** The least "easy" on this list. Adobe is one of the most-hunted programs in existence. The only edge: platform migration churn (researchers slow to move) and the *brand-new AI feature scope*, which has less historical review than the core products. Hunt the new AI features only; the old web surface is picked clean
- **Recon steps (read-only):**
  1. Create the Intigriti account and read Adobe's current policy there — confirm the AI scope section and the AI-specific exclusion list
  2. Read Adobe's public docs for each new AI feature (the policy points at them) and map where user content meets model output
  3. Probe the AI features' API boundaries for prompt-injection → data-leak or action-execution paths (your own account, your own files)

---

## Skip list (do NOT waste time here)

- **Intel (paid)** — suspended; replaced by an unpaid disclosure process around 2026-09-19
- **HackerOne Internet Bug Bounty** — paused 2026-03-27
- **Curl** — paid rewards ended 2026-01-31
- **Node.js** — paused 2026-04
- **Nextcloud** — paid bounty shut down 2026-04 (AI-spam flood cited)
- **Any VDP-only program** (CoinDCX VDP, Nebius VDP, Semtech, Vanguard, Essity, Omnicell, PhonePe VDP, F5, etc.) — no money, skip
- **Private/invite-only programs** — you can't submit

## Bottom line

For a beginner-to-intermediate hunter who wants real payouts with minimal competition, the honest
top 3 are **Agoda Public** (you're already set up there), **Wolt** (test accounts provided, $100
floor, clear exclusions), and **Live Nation** (brand new, $50 floor, 5 resolved). Abercrombie &
Fitch and Coupang TW are the retail/marketplace logic-bug backups. Everything from #7 down is
"less hard", not easy — pick one only if the target class matches a skill you already have.

*Caveat: bounty tables, scope, and resolved counts above are as observed on 2026-09-26. Programs
change policy pages without notice — re-verify each policy page and its current asset list before
any testing.*
