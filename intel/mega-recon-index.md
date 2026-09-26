# Mega Recon Index — 10-target deep hunt
**Date:** 2026-09-26 · **Mode:** passive only (public pages/docs/repos; no scanning, probing, or logins)
**Source files:** `~/workspace/hacker-agent/intel/<slug>-deep-recon.md` (one per target, all dated 2026-09-26)
**Note:** Agoda was dropped from this hunt per operator correction (private since 2016, picked over). It does not appear in this index.

---

## 1. Per-target verdicts

| # | Target (program URL) | Softest entry point | Hardest wall |
|---|---|---|---|
| 1 | **Anthropic** — hackerone.com/anthropic · public since 2026-05-08 · **min $100** (live table; directory said $50) | Console/API authz seams: workspace-boundary confusion, Admin API key-scope, sharing IDOR | Extreme dup pressure (5,614 reports/90d, 466 resolved, $1.07M paid); permission-modal remediation in flight; model-safety/jailbreak classes OOS |
| 2 | **Wolt** — hackerone.com/wolt · min $100 · 0 resolved (snapshot) | Order/checkout state-machine logic with policy-provided test entities (consumer user_id, test venue) | Magic-link signup gate; mandatory `X-HackerOne-Research: shiva92` header; no merchant/courier accounts |
| 3 | **Live Nation** — hackerone.com/live_nation · launched 09/2026 · min $50 · 5 resolved | Two explicitly invited campaigns: Persona/ASU verification bypass (isolated URL) + SafeTix 2.0 bypass | **Human-only discovery** (no bots/scanners/LLM-assisted discovery); no public disclosure ever; the 5 resolved are invisible → dup risk unmeasurable |
| 4 | **Abercrombie & Fitch** — hackerone.com/abercrombie_fitch_bbp · min $50 · $250/$750/$2.5k/$4k | Custom commerce-stack order/checkout/account logic; fast ~2-day triage | "Promotional code abuse" explicitly OOS; scope asset table is JS-rendered (must confirm in-session) |
| 5 | **Coupang TW** — hackerone.com/coupang_tw · min $50 · 0 disclosed | Brand-new Edenred e-voucher integration (Sep 2026); Salesforce Experience Cloud marketplace host (July-2026 hunter case study) | Must obtain own **Taiwanese phone number**; TW/KR backend-overlap dedupe rule; scope table not retrieved |
| 6 | **chess.com** — hackerone.com/chess_com · email-first reports | OAuth `redirect_uri` validation + Apr-2026 2FA pre-auth bypass regression retest (regressions pay half of $600–800) | Game-integrity scope wording ambiguous (verify before game-state testing); reports email-first to bounties@chesscom.atlassian.net |
| 7 | **Arc (Circle)** — hackerone.com/arc-bbp · Extreme up to **$1,000,000** | Custom precompiles on **testnet** (mint authority, dual-decimal accounting) — zero fund risk | Mainnet testing banned; no public audits or writeups; vuln disclosure forbidden without consent |
| 8 | **common_codes** — hackerone.com/common_codes · Extreme $15k–40k | Published source (github.com/german-national-wallet) + **PIN-retry testing explicitly encouraged** by policy | Source-code-only reports are OOB (must demo live); mirrors sanitized; ≤2 req/s |
| 9 | **OpenAI safety** — bugcrowd.com/engagements/openai-safety · launched 2026-03-26 · $100k ceiling for exceptional criticals | Indirect prompt injection via connectors/MCP causing misuse (**explicitly in scope**); cross-workspace exposure | Generic jailbreaks / disallowed-content / system-prompt leaks explicitly OUT; ≥50% repro bar; test-account bans likely |
| 10 | **Adobe** — Intigriti `adobepublic` · live since 2026-09-01 (**25 days old**) · **Tier 1 AI Bonus up to $15k** | Brand-new AI surfaces: indirect prompt injection across share boundaries, AI session-store IDOR | Firefly backend job/data IDOR with random UUID4 + short-lived IDs explicitly OOS; test-plan doc is login-gated |

---

## 2. Ranked cross-target hypothesis shortlist — top 15

Ranked by **ease × impact × competition-thinness**. Each entry: target · vuln class · why now.

### Tier S — strike first
1. **Adobe · indirect prompt injection → cross-user disclosure** — Attacker shares a PDF Space / document with hidden prompt instructions; victim's AI Assistant session discloses the victim's *other* unshared documents or takes unauthorized actions. *Why now:* 25-day-old program; policy's Tier-1 language names exactly this class; up to $15k.
2. **Arc · mint-precompile confused deputy via Call From (testnet)** — The native-coin mint precompile (`0x1800..0000`) reachable by unprivileged callers, or `Call From` (`0x1800..0003`) msg.sender-preservation impersonating the mint authority → testnet unlimited minting. *Why now:* custom precompiles, publicly unaudited, Extreme tier up to $1M; testnet demo = zero fund risk.
3. **common_codes · RWSCA PIN-retry race** — Race the PIN-retry counter/lockout on the #1-ranked asset; policy **explicitly encourages** Remote WSCA PIN retry testing. *Why now:* invited testing + published source to white-box the counter logic first; Extreme $15k–40k bracket.
4. **Adobe · AI session-store IDOR (acrobat.adobe.com)** — Conversation/session endpoints authorize by session possession only or use predictable IDs → account B replays account A's session identifier under its own IMS token and reads A's Q&A / cached document extracts. *Why now:* new session-key architecture with 12h content cache; Tier 1.

### Tier A — high value, slightly harder
5. **chess.com · 2FA pre-auth token regression** — Retest brQ's Apr-2026 finding (usable `ACCESS_TOKEN` issued between password acceptance and OTP completion) on alternate login paths (mobile API, OAuth login, reset-login). *Why now:* known-vuln class on this exact target, fix may be path-specific; regressions pay half of $600–800.
6. **Coupang TW · Edenred e-voucher redemption logic** — Sep-2026-launched voucher flow (NT$100–3,000 serial codes): weak rate limiting, predictable codes, or cross-account reuse. *Why now:* brand-new integration = fresh code; voucher flows are logic-dense.
7. **OpenAI safety · ShadowLeak-class retest on Atlas Browser / new connectors** — Poisoned doc/email drives the agent to exfiltrate planted chat-history PII to an attacker URL (≥50% repro). *Why now:* headline in-scope sub-case; fixed on Deep Research but newer surfaces may persist.
8. **Live Nation · ASU Persona completed-inquiry replay** — Replay a *completed* Persona inquiry (state binding, not verification skip) to reach post-verification state. *Why now:* explicitly invited isolated campaign; bug likely in Live Nation's state machine around Persona, not Persona itself. 🔴 Human-operated only.
9. **chess.com · OAuth `redirect_uri` validation bypass** — Crafted `redirect_uri` (`chess.com.attacker.tld`, encoded-dot, path traversal) on `external.oauth2.chess.com` leaks the auth code. *Why now:* 2024 "Rook to XSS" trampoline is direct precedent on this engineering culture; $600–800 bracket.

### Tier B — strong, with friction noted
10. **Arc · dual-decimal (6 vs 18) accounting drift** — Native 18-dp vs ERC-20 6-dp views diverge on gas refunds, fee burn/treasury split, or failed-tx rollback → value created/destroyed. *Why now:* Arc-unique custom surface; official docs warn integrators (high bug density).
11. **Anthropic · claude.ai conversation/artifact sharing IDOR** — Account B requests account A's conversation/artifact by object ID without the share token. *Why now:* share-heavy surface, classic IDOR zone — but heavy dup pressure; deprioritize vs. Tiers S/A.
12. **Wolt · address-text vs geocoordinate zone/fee desync** — In-zone address string + out-of-zone coordinates (or vice versa) yields quotable order the zone logic should reject. *Why now:* policy-provided test entities; 0-resolved snapshot; coordinate/address seam is classic.
13. **Abercrombie · SHARE2PAY payment-link auth gap** — Hollister app-only "share cart, they pay" links as bearer tokens without expiry or payer binding. *Why now:* novel app-only feature = less-hardened path; ~2-day triage.
14. **Coupang TW · Salesforce Experience Cloud auth bypass** — Unauthenticated 37-version REST surface; older versions or the JWT/SAML2 bearer flow at `/tw/services/oauth2/token` may accept forged assertions → SOQL/data access. *Why now:* July-2026 hunter case study mapped it; Salesforce communities are a proven bug class. ⚠️ Verify host is in scope before touching (policy: ask first).
15. **Live Nation · post-transfer SafeTix secret non-revocation** — Old holder's app still renders valid barcodes after ticket transfer. *Why now:* invited SafeTix 2.0 campaign; transfer/revoke seams are the classic double-spend shape. 🔴 Human-operated only.

### Honorable mentions (next wave)
- common_codes: WPB status-list reuse / PNS hijack via MDVM-token bearer (revocation defeat); MDVM skip-integrity header; issuance hijack.
- Anthropic: console member→admin role escalation (H2); Admin API key-scope confusion (H3).
- Wolt: scheduled-order TOCTOU (H-2); Double Order cross-venue contamination (H-3).
- Adobe: Firefly Custom Models cross-tenant access (H4); Express share permission confusion (H5).
- OpenAI safety: cross-workspace connector data exposure (H2); full unsummarized CoT extraction.
- Arc: CCTP domain message verification replay; blocklist bypass via native-vs-ERC20 path.
- Abercrombie: order-tracking IDOR (H1); gift-card enumeration/race (H6).
- Coupang TW: seller↔buyer order/settlement IDOR; TW/KR region confusion.
- chess.com: club admin IDOR (H3); UUID-v1 badge enumeration (H4).

---

## 3. Drop / swap recommendation

- **Drop: none.** All 10 verified as live, paid programs with real scope.
- **Demote to secondary: Anthropic** — fits the launch/bounty criteria but is the most competition-dense target in the set (5,614 reports/90d, 466 resolved); also the live minimum is **$100, not $50**. Hunt here only with genuinely novel authz seams (H1–H3, H5), expect dup pressure.
- **Flag friction: Coupang TW** — highest pre-test cost (own Taiwanese phone number required; scope table unverified). Confirm scope + phone path before committing test time.
- **Flag rule: Live Nation** — every hypothesis is human-operated only (program bans bot/scanner/LLM-assisted discovery); no public disclosure ever.
- **Flag rule: Arc** — testnet/local devnet only; mainnet testing explicitly banned.
- **Flag rule: common_codes** — source-only findings earn nothing; every hypothesis needs a live demo; ≤2 req/s.

## 4. Suggested execution order (first 5, fastest signal)

1. **Adobe Tier-1 AI** (H1 indirect injection, H2 session IDOR) — newest program, explicit bonus tier, human + browser-driven.
2. **Arc testnet** (H1 mint precompile, H2 decimal drift) — local devnet/testnet, zero fund risk, highest ceiling.
3. **common_codes** (H3 PIN-retry race, revocation defeat) — white-box first from published source, then live demo.
4. **chess.com** (H2 2FA regression, H1 OAuth redirect) — fastest regression retest in the set.
5. **Live Nation ASU campaign** (NH-5 inquiry replay) — human-operated, explicitly invited.

*End of index — 2026-09-26. Policies change without notice; re-pull each live policy before testing.*
