# Yahoo (Paranoids) — HackerOne Recon & Hunt Plan

Passive research only. No testing performed. Prepared 2026-09-26.
**Before any active testing: re-verify the live program brief on HackerOne —
scope details below come from the published policy (mirrored) plus archived
scope documents and may have changed.**

---

## [SCOPE SUMMARY]

- **Platform:** HackerOne. Two programs: **public** + **Elite** (invite-only).
  "All products and services owned by Yahoo are included in either our public
  or Elite bug bounty program." Elite scope visible to invited researchers only.
- **Catch-all rule:** "If you've found a vulnerability that affects an asset
  belonging to Yahoo, but is not included as in scope on any of the Yahoo
  programs, please report it to this program."
- **Assets referenced as in scope** (policy mirror + archived scope docs):
  `*.yahoo.com`, `*.aol.com`, `*.techcrunch.com`, plus Yahoo brands —
  `*.aolpublishers.com`, `*.uplynk.com`, `*.compuserve.com`,
  `*.isp.netscape.com`, `*.lite.aol.com`, wmconnect.com subdomains,
  ad-manager/DSP properties. Out-of-scope assets are listed **only** on the
  live HackerOne policy page — check it before testing.
- **Bounty table:** Critical $10,000–$15,000 · High $3,000–$10,000 ·
  Medium $500–$3,000 · Low $100–$500 · Informative $0.
- **First-to-disclose only.** Bounty at Yahoo's sole discretion; complex /
  negligible-impact chains pay less; policy violations forfeit rewards.
- **Rules of engagement (binding):**
  - Test ONLY accounts you own (or have the holder's permission for).
  - **No automated scanners/tools** — explicitly banned (payloads can damage
    production). Manual, low-volume testing only.
  - Tag all traffic: `X-Bug-Bounty: HackerOne-<username>` header; report the
    header value in the submission. Provide your IP in the report.
  - Register test accounts with `<username>+x@wearehackerone.com` —
    **required by some properties for bounty eligibility.**
  - Never exfiltrate/pivot; if you touch PII, don't retain it.
  - No social engineering, phishing, physical, or DoS. Safe harbor applies
    only with full policy compliance.
  - **No public disclosure** without Yahoo's express written permission —
    including to any third party.
- **Won't pay (borderline/no-bounty):** self-XSS, open redirect (rated Low/Low
  in their CWE table — chain primitive only), account/email enumeration,
  missing cookie flags/headers, clickjacking, login/logout/unauth CSRF,
  scanner output, known-vuln libraries without exploitability, verbose errors
  without exploitability, Flash, CSV injection, EOL software.
- **Explicitly valued:** RCE / OS command injection (Critical), SQLi
  (High–Critical), XXE (Critical), SSRF (Medium–Critical), improper
  authentication (Medium–Critical), IDOR/privilege escalation
  (Medium–High), CSRF with real impact (Medium–High), stored XSS
  (Low–Medium), subdomain takeover (up to Medium), hard-coded creds
  (Low–High). 0-day/CVE reports eligible 30 days after publication.

Sources: policy mirrored at https://firebounty.com/644-yahoo/ (Yahoo program
on HackerOne since 2014-02-03); archived scope PDF
https://ia801309.us.archive.org/0/items/yahoo-bug-bounty-program-hacker-one/Yahoo!%20-%20Bug%20Bounty%20Program%20_HackerOne.pdf

---

## [DISCLOSED-REPORT PATTERNS]

Yahoo discloses **zero** reports publicly on HackerOne
(https://www.bugbountyhunter.com/program?id=yahoo — "This program has not
disclosed any reports"). Patterns below come from researcher writeups and
press. Duplication risk is therefore hidden — assume the obvious is taken.

| # | Finding | Payout | Pattern / lesson |
|---|---------|--------|------------------|
| 1 | Yahoo Mail **stored XSS via HTML-filter bypass** (Jouko Pynnönen, Klikki Oy) — malformed HTML passed the mail filter; PoC exfiltrated inbox + self-replicated via signature. Reported twice, months apart. | **$10,000 × 2** | Mail HTML sanitizer is a repeat-yield surface. Whitelist bypasses (e.g. YouTube-link vector) paid twice. http://threatpost.com/critical-yahoo-mail-flaw-patched-10k-bounty-paid/115930/ ; https://thehackernews.com/2016/12/hack-yahoo-email.html |
| 2 | Yahoo Mail **SSRF → RCE via gopher to Redis** | **$15,000** | URL-fetching features chained to internal services = top payout class on this program. Cited in SSRF hunting knowledge bases (SeaGull/cstrien skills). |
| 3 | **Flickr account hijacking** (Josip Reizelman) — `.done` login-token parameter only validated as *starting with* `https://www.flickr.com/signin/yahoo/`; appended `../../test` redirected `.ys`/`.data` tokens; exfiltrated via `<img>` embedded in Flickr help-forum comments (no CSP there). | **$7,000** | Partial redirect validation + missing-CSP exfil channel. https://securityaffairs.com/58607/hacking/flickr-account-hijacking-flaw.html |
| 4 | **SQLi** on sports.yahoo.com/nfl/draft (H1 #1538) | $3,705 | Legacy media properties had injectable endpoints. |
| 5 | **RCE / LFI / XSPA / SSRF** on sb*.geo.sp1.yahoo.com (H1 #6674) | $3,000 | Geo/load-balancer hostnames = soft underbelly. |
| 6 | **LFI** on marketing-dam.yahoo.com (H1 #7779) | $2,500 | Marketing/internal-adjacent hosts. |
| 7 | **IDOR — contact deletion** (DELETE missing ownership check) | $2,500 | Destructive endpoints skipped authz. Cited in bountyforge knowledge base. |
| 8 | **Stored XSS** on Flickr main page via user tagging (H1 #916 / #940) | $2,173 / $1,960 | Social features (tags, comments) → stored XSS. |
| 9 | **XSS Yahoo Messenger via calendar.yahoo.com** (H1 #914) | $677 | Cross-property: calendar → messenger. |
| 10 | **Unrestricted file upload → RCE** (H1 #4836) | $800 | Upload + parse chain. |
| 11 | **Header injection** on rmaitrack.ads.vip.bf1.yahoo.com (H1 #6322) | $1,000 | Ad-tracking hosts. |
| 12 | **Two XSSI chained → user info theft** (0xHyde) | $750 | JSONP/XSSI on authenticated endpoints. https://medium.com/@0xHyde/yahoo-two-xssi-vulnerabilities-chained-to-steal-user-information-750-bounty-e9bc6a41a40a |
| 13 | Mass comment/post deletion via missing authz on delete endpoint (Ibrahim E.) | paid (amount undisclosed) | "A potential attacker with little knowledge of programming could write an automated script to delete all the comments and posts." https://thehackernews.com/2014/03/yahoo-vulnerability-allows-hacker-to_1.html |

Program scale (2015, HackerOne): ~600 hackers, ~1,500 reports, 58 valid, $41,100 total, avg $1,082. Program is 12 years old — shallow bugs are exhausted; only deep logic/authz chains are realistic.

Sources: https://github.com/reddelexc/hackerone-reports/blob/HEAD/docs/tops_by_program/TOPYAHOO!.md and TOPVERIZONMEDIA.md; writeup links above.

---

## [ATTACK SURFACE MAP]

Built from public evidence only (writeups, program docs, observed hostnames).

**Identity & auth (highest value)**
- `login.yahoo.com` — central login, `.done`/`.src` redirect params (cf. Flickr
  $7k token-redirect pattern), session cookies (`.ys`, `.data`)
- `account.yahoo.com` / account settings — email change, password change,
  2FA enrollment, recovery options, connected apps
- `api.oauth.yahoo.com` — OAuth service (a 2026 hunt found exposed `/health`
  there; service exists and is in scope)
- `developer.yahoo.com` — OAuth app registration; test redirect_uri
  validation on *your own* registered apps
- Legacy: Yahoo OpenID endpoints, AOL login flows, `*.lite.aol.com`

**Yahoo Mail (repeat $10k surface)**
- `mail.yahoo.com` — HTML filter/sanitizer, attachment preview, signatures,
  filters/rules, vacation responders, calendar invites rendering in mail
- Invariant: attacker HTML must never execute in a victim's mailbox
- Differential: web vs mobile API rendering pipelines

**Flickr**
- `flickr.com` — photo upload + parsing, tags, comments, help forum
  (historically missing CSP → exfil channel), screen-name HTML injection
  (H1 #1483, iOS app vector)

**Media & commerce properties**
- `sports.yahoo.com`, `finance.yahoo.com`, `news.yahoo.com`,
  `techcrunch.com`, fantasy sports — legacy code, injectable endpoints
  (SQLi precedent on sports draft page)

**AOL / legacy**
- `aol.com`, `mail.aol.com`, `*.compuserve.com`, `*.isp.netscape.com`,
  wmconnect.com — old stacks, takeover candidates

**Ads**
- DSP / admanager (`apiv3.admanagerplus.yahoo.com`),
  `rmaitrack.ads.vip.bf1.yahoo.com` (header-injection precedent)

**Infra-adjacent hostnames (from disclosed reports)**
- `sb*.geo.sp1.yahoo.com`, `marketing-dam.yahoo.com`,
  `api-beta-internal.g11n.yahoo.com` — treat as leads, verify scope live

---

## [HYPOTHESES] — ranked by expected value

1. **Login/OAuth token-destination validation bypass → ATO.**
   Invariant: *authentication tokens must only be delivered to the exact
   registered endpoint.* The $7k Flickr bug was prefix-only validation on
   `.done`. Probe `.done`/`.src`/`.intl` params on login.yahoo.com and
   "Login with Yahoo" relying-party flows for traversal/append tricks
   (`../`, `%2f..`, subdomain confusion). Expected: High–Critical.
2. **Mail HTML-sanitizer bypass → stored XSS → ATO.**
   Invariant: *untrusted message content must never execute script in the
   victim's session.* Two $10k payouts on this exact surface. Focus on new
   surfaces since 2016: attachment previewers, calendar-invite rendering,
   new compose editor, AMP/email-interactive features. Expected: High.
3. **SSRF in URL-fetching features → internal/RCE.**
   Invariant: *the server must never fetch attacker-influenced internal URLs.*
   $15k precedent (gopher→Redis). Candidates: link unfurling/previews, image
   proxies, RSS/feed import, "fetch from URL" uploads, webhook test buttons,
   rich-content validators. Expected: High–Critical.
4. **IDOR on state-changing endpoints.**
   Invariant: *a resource ID must remain bound to the authenticated
   principal.* Precedents: contact deletion ($2.5k), mass comment deletion.
   Probe mail filters/rules, contacts, account settings, fantasy rosters with
   two owned test accounts. Expected: Medium–High.
5. **Account recovery / settings state-machine flaws.**
   Invariant: *privilege transitions (email change, password reset, 2FA
   enrollment/disable) require fresh authentication; tokens are single-use
   and bound to the account.* Model each flow as a state machine; try
   skipping, reordering, replaying steps. Expected: High–Critical if ATO.
6. **Subdomain takeover on legacy Yahoo/AOL/Compuserve/Netscape assets.**
   Invariant: *DNS must not point at unclaimable/claimed-by-other resources.*
   Program explicitly values SDTO (up to Medium). Passive CNAME sweep only.
   Expected: Low–Medium, cheap to test.
7. **Web vs mobile/API differential authorization.**
   Invariant: *authorization must not depend on the client.* Mobile and
   alternate API versions historically skip checks (industry-wide pattern;
   Yahoo's CWE table rates missing-auth Critical). Expected: Medium–High.
8. **File upload + parsing chains (Flickr, mail attachments, avatars).**
   Invariant: *uploaded bytes must never execute as code/markup in a victim
   context.* Precedents: upload→RCE ($800), Flickr tag XSS ($2.1k).
   Expected: Medium–High.
9. **XSSI / JSONP on authenticated endpoints.**
   Invariant: *authenticated responses must not be readable cross-origin.*
   $750 precedent. Expected: Low–Medium.
10. **Open redirect — chain primitive only.**
    Program rates it Low/Low standalone. Only valuable feeding hypothesis 1
    (OAuth/token theft). Do not report alone.

### Hunt discipline for Yahoo specifically
- Manual only (scanners banned). Tag every request `X-Bug-Bounty:
  HackerOne-<username>`. Use `<username>+x@wearehackerone.com` test accounts.
- Two owned accounts minimum before any authz differential work.
- Assume heavy duplication: prioritize *novel interactions* (cross-feature,
  state-machine, differential) over single-endpoint checks.
- Stop at minimum safe PoC; never retain another user's data; never disclose
  publicly without written permission.
