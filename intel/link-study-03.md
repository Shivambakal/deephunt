# Link Study — Batch 03 (24 URLs)

Read-only recon research, 2026-09-26. Dead/truncated URLs noted, no exploitation attempted.

## HIGH-VALUE LEADS (top 5)

1. **Doctolib YWH program — fake-doctor test account + €50k scenarios.** Program page publishes a test doctor ("Dr Albertus Boulenfunkierchenblah", booking code `42`), required UA string `BugBounty/42 (YWH)`, max 10 req/sec, and two €50,000 special scenarios: RCE on the Rails monolith reading env `SECURITY_BUG_BOUNTY_DOCTOLIB_IS_PWN`, and a one-shot IDOR dumping a whole doctor's patient base. → Immediate: create the fake-doctor appointment, hunt IDOR on appointment/patient-sync endpoints.
2. **FDJ United YWH program — exact scope grid.** 33 brand scopes published; `payment.<brand>.tld` subdomains explicitly in scope at Critical tier (€15k: SQLi/RCE/PCI-env access/no-interaction ATO). `payment.mariacasino.com` (already found live in our recon) is therefore a Critical-tier target. → Manual checkout/payment-logic testing on payment.mariacasino.com and payment.unibet.*.
3. **Superbank YWH program — exact scope + AI chatbot target.** In scope: `api.super-id.net` (HIGH, $2k max), `superbank.id`, `ecosystem-experience.super-id.net`, and `chatbot.super-id.net` listed as **AI Model** asset. No automated scanners. → Manual API testing on api.super-id.net; prompt-injection / P2P testing on the chatbot (see SearchLeak lead below).
4. **Google OAuth device-code hijacking (weirdmachine64).** RFC 8628 device flow: transferable session URL + unbound client_id/scope server-side + `prompt=none` = one-click account takeover on any "Sign in with Google" app ($13,337 Google VRP). → Add to SSO playbook: test device-code flows on any target offering Google sign-in (Agoda, Booking.com, Pinterest all do).
5. **HEIF Heist (Hacktron) — libheif RCE via image upload.** Heap overflow in libheif 1.19.x–1.23.x reachable through HEIC/AVIF uploads (ImageMagick path); affected Slack, Meta, Shopify, GitHub Enterprise. → Any target with image upload (Pinterest pins, profile avatars on Doctolib/FDJ) is worth a version-fingerprint check of the image pipeline.

---

## 1. https://pwn.ai/blog/click
- **WHAT:** Dead link — HTTP 404 (blog slug truncated in source notes).
- **ATTACK SURFACE:** none retrievable.
- **ACTIONABLE LEAD:** none; drop from list.

## 2. https://ret
- **WHAT:** Invalid URL stub (not a real address).
- **ATTACK SURFACE:** none.
- **ACTIONABLE LEAD:** none; drop from list.

## 3. runtimewire.com — GitHub $100k RCE (CVE-2026-3854)
- **WHAT:** News writeup of @sagitz_'s unauthenticated RCE on GitHub via crafted repository URLs; $100,000 bounty, patched in 48h.
- **ATTACK SURFACE:** Repository-URL parsing on GitHub backend; unauthenticated trigger; led to shell access, repo-secret reads, code-in-transit tampering. GitHub VRP caps criticals at $150k; >$15M paid since 2016.
- **ACTIONABLE LEAD:** github.com is in scope — prioritize URL-parsing edge cases (repo names, branch paths, raw URLs) on api.github.com and github.com; malformed repo URLs are a proven critical class here.

## 4. https://semgrep.dev/blog/
- **WHAT:** Semgrep blog index (generic vendor blog, no specific article).
- **ATTACK SURFACE:** none specific.
- **ACTIONABLE LEAD:** none; skip unless a specific post is named later.

## 5. https://slcyber.io/research-center/e
- **WHAT:** Truncated URL stub — unresolvable.
- **ATTACK SURFACE:** none retrievable.
- **ACTIONABLE LEAD:** none; needs the full URL.

## 6. https://slcyber.io/research-center/wp
- **WHAT:** Truncated URL stub — unresolvable.
- **ATTACK SURFACE:** none retrievable.
- **ACTIONABLE LEAD:** none; needs the full URL.

## 7. https://specterops.io/blog/mssql-
- **WHAT:** Truncated URL stub (SpecterOps MSSQL blog series) — unresolvable.
- **ATTACK SURFACE:** none retrievable.
- **ACTIONABLE LEAD:** none; needs the full URL (likely AD/MSSQL tradecraft — low priority for web bounty).

## 8. https://vpn.intigriti.rocks/*`
- **WHAT:** Invalid URL (wildcard + stray backtick; Intigriti VPN endpoint reference).
- **ATTACK SURFACE:** none.
- **ACTIONABLE LEAD:** none; Intigriti VPN access comes from your own Intigriti profile after registration.

## 9. weirdmachine64.github.io — Google OAuth device-code hijacking
- **WHAT:** Research writeup: two stacked bugs in Google's RFC 8628 device authorization grant → silent one-click account takeover on any "Sign in with Google" app; $13,337 Google VRP, fixed Mar 2026.
- **ATTACK SURFACE:** `POST oauth2.googleapis.com/device/code`, `POST oauth2.googleapis.com/token` (polling), `accounts.google.com/o/oauth2/v2/auth`, `accounts.google.com/v3/signin/challenge/` with transferable `TL` session blob; unbound `client_id`/`scope` in auth URL; `prompt=none` consent skip; XOAUTH2 IMAP backdoor via `https://mail.google.com/` scope.
- **ACTIONABLE LEAD:** Add device-flow tests to the SSO playbook — for any target with Google sign-in (Agoda, Booking.com, Pinterest), check whether device-code/TV-app flows exist and whether client_id/scope are bound server-side.

## 10. https://whoareme.com/blog/cspt-account-takeover-
- **WHAT:** Truncated URL stub — unresolvable.
- **ATTACK SURFACE:** none retrievable.
- **ACTIONABLE LEAD:** none; needs the full URL.

## 11. https://www.cyera.com/research/ni8mare-unauthenticated-remote-code-e
- **WHAT:** Truncated URL stub — unresolvable.
- **ATTACK SURFACE:** none retrievable.
- **ACTIONABLE LEAD:** none; needs the full URL.

## 12. hacktron.ai — Hacking OpenAI / HEIF Heist
- **WHAT:** Research writeup: chained libheif heap overflow (RCE via HEIC upload on Discourse) + OpenAI SSO misconfiguration → ChatGPT/Codex employee account takeover; $6,500 bounty; 72h discovery-to-access.
- **ATTACK SURFACE:** Image-upload pipelines (HEIC/HEIF/AVIF), ImageMagick `magick` conversion path, libheif 1.19.x–1.23.x (Debian 12/13 shipped vulnerable 1.19.7/1.19.8); SSO identity flows bridging forum → main product; "Sign in with OpenAI" via auth.openai.com.
- **ACTIONABLE LEAD:** Fingerprint image-processing on upload endpoints (Pinterest pins, avatars on Doctolib/FDJ/betting sites); check for HEIC/AVIF acceptance + ImageMagick/libheif in stack disclosures. Also: map SSO bridges between a target's community/forum and its main app.

## 13. intigriti.com — "Intigriti named best security company"
- **WHAT:** Marketing/awards announcement — no technical content.
- **ATTACK SURFACE:** none.
- **ACTIONABLE LEAD:** none.

## 14. intigriti.com — AI systems security discussion (Leo Racanelli)
- **WHAT:** Opinion interview on AI + bug bounty (workflow, token-cost barrier, AI as teammate).
- **ATTACK SURFACE:** none technical; strategic notes: AI/chatbot scopes attract creative hunters; invisible prompt-injection references worth keeping; barrier-to-entry rising due to token costs.
- **ACTIONABLE LEAD:** Keep a prompt-injection reference file for chatbot scopes (chatbot.super-id.net, Superbank); prioritize AI components in programs — low dupe rates.

## 15. varonis.com — SearchLeak (M365 Copilot one-click exfil)
- **WHAT:** Research writeup: 3-stage chain in M365 Copilot Enterprise Search — Parameter-to-Prompt injection via `q` param → HTML-injection race condition during streaming → CSP bypass via Bing `searchbyimage` SSRF → one-click data exfiltration; CVE-2026-42824, Critical.
- **ATTACK SURFACE:** `https://m365.cloud.microsoft/search/?auth=2&origindomain=microsoft365&q=<PROMPT>`; streaming HTML rendering before sanitizer; `https://www.bing.com/images/searchbyimage?cbir=sbi&imgurl=<attacker-url>` as SSRF-to-exfil proxy.
- **ACTIONABLE LEAD:** Directly applicable to **chatbot.super-id.net** (Superbank's in-scope AI asset): test whether URL/query parameters are passed to the model as instructions (P2P), whether the chat UI renders HTML during streaming (race), and whether any allowlisted fetch endpoint can be abused as an exfil proxy.

## 16. https://www.yeswehack.com/learn-bug-bounty/llm-series-code
- **WHAT:** Dead link — HTTP 404.
- **ATTACK SURFACE:** none retrievable.
- **ACTIONABLE LEAD:** none; drop from list.

## 17. https://yeswehack.com/programs/coindc
- **WHAT:** Truncated program slug — unresolvable (CoinDCX program exists on YWH; exact slug unknown).
- **ATTACK SURFACE:** none retrievable.
- **ACTIONABLE LEAD:** Open the CoinDCX program from the YWH dashboard to get the live slug + scope before testing.

## 18. yeswehack.com — Doctolib public bug bounty program
- **WHAT:** Full live program brief: reward grid by PII typology, special scenarios, testing precautions, exact scopes.
- **ATTACK SURFACE:** Scopes: `www.doctolib.(fr|de|it)`, `pro.doctolib.(fr|de|it)`, `*.doctolib.(fr|de|it|com|net)`, `*.siilo.com`, iOS/Android apps. Fake test doctor: **Dr Albertus Boulenfunkierchenblah**, booking code **42**. Required UA: `BugBounty/42 (YWH)` for heavy traffic (max 10 req/s). Ruby on Rails monolith. **€50,000** game-over: RCE on prod Rails reading env `SECURITY_BUG_BOUNTY_DOCTOLIB_IS_PWN`. **€50,000** one-shot: IDOR dumping a whole doctor's patient base in few requests. Medical-data sync flow (email/phone link → account linking) with identity matching.
- **ACTIONABLE LEAD:** Book the fake doctor with a test account, then hunt IDOR on appointment/patient-sync endpoints — patient-base dump = €50k scenario. Never use a real account or real patient data.

## 19. yeswehack.com — FDJ United (Online Betting and Gaming)
- **WHAT:** Full live program brief: 33 brand scopes, exact rules, reward grids.
- **ATTACK SURFACE:** Scopes include `www.unibet.(com|it|se|co.uk|be|nl|dk|ro|ee|ie|com.au|mt)`, `payment.unibet.*`, `www.mariacasino.(com|se|ee|dk)`, `payment.mariacasino.*`, `www.bingo.com`, `(se|fi|uk).bingo.com`, `payment.bingo.com`, `www.32red.com`, `int.32red.com`, `pci.kindredgroup.com`, plus ottokasino/kolikkopelit/storspiller/storspelare/casinohuone/vladcazino + iOS/Android apps. **All brand sites on the same platform — a vuln on one likely exists on all.** Rewards: Critical €15k (RCE, SQLi, PCI-env access, no-interaction ATO); High €5k (stored XSS, subdomain takeover on main brands); `/blog/` endpoints capped at High tier. **No automated scanners / heavy traffic.** Leaks from out-of-scope sources not rewarded.
- **ACTIONABLE LEAD:** `payment.mariacasino.com` (found live) is Critical-tier — manual checkout/payment-logic testing there; replicate any finding across unibet/bingo/32red brands for multiple reports.

## 20. yeswehack.com — Kiteworks public bug bounty program
- **WHAT:** Full live program brief (note: other intel says closed to new submissions — verify status before testing).
- **ATTACK SURFACE:** Hunting env: `ywh-kw-public.bounty.kiteworks.dev` (Kiteworks Core, EPG, MFT/Apache Airflow, Advanced Forms). Crown-jewels: **$25k bonus** for unauthenticated RCE-as-root on Core appliance (up to $50k total). XSS needs real impact PoC (alert(1) insufficient). Admin-privilege findings downgraded via CVSS MS:U. ~1 req/sec, no automated tools.
- **ACTIONABLE LEAD:** Verify program status first (reported closed to new submissions); if open, focus on unauthenticated RCE on the dedicated hunting instance and privilege-escalation chains Core→other nodes.

## 21. https://yeswehack.com/programs/moneybo
- **WHAT:** Truncated program slug — unresolvable (Moneybox program exists; exact slug unknown).
- **ATTACK SURFACE:** none retrievable.
- **ACTIONABLE LEAD:** Open the Moneybox program from the YWH dashboard to get the live slug + scope.

## 22. yeswehack.com — Superbank public bug bounty program
- **WHAT:** Full live program brief: scopes, rules, reward grid, hunting requirements.
- **ATTACK SURFACE:** `api.super-id.net` (API, HIGH — $2k max), `superbank.id` (web, Medium), `ecosystem-experience.super-id.net` (web, Medium), `chatbot.super-id.net` (**AI Model**, Medium), iOS (`id6444720285`) + Android (`id.co.bankfama.android`) apps. Self-register with YWH email alias. **No automated scanners / heavy traffic.** No DoS. Long non-qualifying list (headers, cookie flags, user enum, rate-limit, GraphQL introspection all out).
- **ACTIONABLE LEAD:** Manual API testing on api.super-id.net (IDOR/authz — business-logic bugs qualify); prompt-injection testing on chatbot.super-id.net using SearchLeak techniques (#15).

## 23. https://zhero-web-sec.github.io/research-and-things/re-cache-e
- **WHAT:** Truncated URL stub — unresolvable.
- **ATTACK SURFACE:** none retrievable.
- **ACTIONABLE LEAD:** none; needs the full URL (likely web-cache deception research — relevant to the cache playbook if recovered).

## 24. zuksh.medium.com — checkout business logic article
- **WHAT:** Blocked — HTTP 403 from Medium (access denied); not retried per policy.
- **ATTACK SURFACE:** none retrievable.
- **ACTIONABLE LEAD:** Topic (checkout price manipulation) already covered by the hunter's `checkout-logic` playbook; apply it to payment.mariacasino.com and payment.unibet.*.

---

## Skipped / dead summary
Dead (404): pwn.ai/blog/click (#1), ywh llm-series-code (#16). Blocked (403): Medium checkout article (#24). Invalid stubs: `https://ret` (#2), `vpn.intigriti.rocks/*`` ` (#8). Truncated (need full URL): #5, #6, #7, #10, #11, #17, #21, #23. Low/no value: #4 (blog index), #13 (awards PR), #14 (opinion piece — minor strategic notes only).
