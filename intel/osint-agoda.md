# OSINT — Agoda (passive only, 2026-09-26)

Method: public web/GitHub search only. ZERO requests to agoda.com infrastructure.
No credential was tested. No secret values reproduced (8-char prefixes max).

## 1. GitHub secret sweep — 8 candidates, 0 real

| # | Repo / file | URL | Assessment |
|---|-------------|-----|------------|
| 1 | philipposk/travel — API_SETUP.md | https://github.com/philipposk/travel/blob/HEAD/API_SETUP.md | FALSE POSITIVE — `VITE_AGODA_API_KEY=your-key` placeholder |
| 2 | jarrettj/travel-agents — docs/SWARM-SETUP.md | https://github.com/jarrettj/travel-agents/blob/HEAD/docs/SWARM-SETUP.md | FALSE POSITIVE — `export AGODA_API_KEY="your_key"` placeholder |
| 3 | louisleex05-byte/driftcoconut | https://github.com/louisleex05-byte/driftcoconut | FALSE POSITIVE — `AGODA_API_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` placeholder |
| 4 | mcfly1983/channelmanager3 | https://github.com/mcfly1983/channelmanager3 | FALSE POSITIVE — env var *names* only (`AGODA_API_KEY`, `AGODA_USERNAME`), no values |
| 5 | sagarsakre/blog_hotel_links_verifier | https://github.com/sagarsakre/blog_hotel_links_verifier | FALSE POSITIVE — keys stored in GitHub Secrets (proper), none in code |
| 6 | yx-laguna/nexus-gateway | https://github.com/yx-laguna/nexus-gateway | FALSE POSITIVE — env var name only, no value |
| 7 | agoda-com/api-agent (OFFICIAL org) | https://github.com/agoda-com/api-agent | CLEAN — placeholders only; `.env.example` pattern followed |
| 8 | agoda-com/macos-vz-kubelet (OFFICIAL org) | https://github.com/agoda-com/macos-vz-kubelet | CLEAN — infra code (macOS VM kubelet), no secrets |

**Verdict: no exposed Agoda credentials found in public GitHub code.**
Note: Agoda's partner API auth is Site ID + API Key (developer.agoda.com). The
official org repos (7, 8) are worth re-checking periodically for accidental
secret commits — watchlist, not findings.

## 2. Prior Agoda-related security history

- **Public program launched 2026-06-23** (HackerOne: agoda-public), max $6,000.
  Payout tiers: Low $150 / Medium $500–700 / High $2,000–3,000 / Critical $5,000–6,000.
  Agoda lists these as common payout classes: auth bypass, SQLi, RCE (High–Critical);
  IDOR (Medium–Critical); stored XSS, MFA bypass (Low–High). Private program ran
  since 2016; avg first response 30h, triage ~5 days. No disclosed Agoda hacktivity
  reports found (program too new / reports undisclosed).
- **"Agoda F1" — GCP API key in Agoda JS (prior hunt).** A hunter skill doc
  (sol0-dev/acy intel-hunt SKILL.md) cites `AIza` Google-key patterns as
  "NEW — from Agoda F1", i.e. a previous Agoda hunt surfaced a Google API key in
  Agoda's JS bundles. LESSON: Agoda ships Google keys client-side — the finding is
  in the *restrictions*, not the key. Test which APIs the key enables (Maps with
  referrer restriction = fine; unrestricted Places/Geocoding with billing = report).
- **Prestige Software S3 breach (2020).** Third-party channel manager left an S3
  bucket open exposing Agoda (and Booking/Expedia) guest PII incl. card data —
  not Agoda's own infra, but their supply chain. LESSON: Agoda's affiliate/channel
  integrations are historically the leakiest surface. (Scope caution: third-party.)
- **April 2026: alleged 82M-record Agoda breach — DENIED.** Attackers claimed theft;
  Agoda refuted, sample data looked non-Agoda (possibly Booking.com-breach spillover).
  No confirmed Agoda breach. Context only.

## 3. Most useful prior writeup — lesson for this hunt

Seth Kraft, "API Key Leak via exposed env.js" (May 15, 2026):
https://github.com/skraft9/vulnerability-research/blob/HEAD/write-ups/api_key_leak.md
Pattern: subfinder → page-source review → referenced `env.js` config file → multiple
plaintext API keys → key + enumerable 6-digit Policy ID → bulk data access. Paid.
LESSON for Agoda: always pull every referenced config JS (`env.js`, `config.js`,
`settings.js`) from Agoda's pages and grep for keys — then test what the key unlocks
with *your own* test data only. This is exactly the hunter's `vuln` config.js
fingerprint + Google-key check; keep both.

## 4. Recommended next OSINT passes (passive)
- Re-run the GitHub sweep monthly; add queries: `"agoda" "client_secret"`,
  `"agoda.com" "BEGIN RSA PRIVATE KEY"`, `agoda aws_access_key_id`.
- Watch the official agoda-com org repos for new repos/commits.
- Watch HackerOne hacktivity for first disclosed Agoda reports — they'll reveal
  which asset classes triage accepts vs. duplicates.
