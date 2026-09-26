# MASTER HIT LIST — 2026-09-26
All 10 workstreams consolidated. Ordered by expected value × feasibility.
Your move is marked [YOU]; machine-done is marked [DONE].

## TIER 1 — highest expected value, start tonight

### 1. Aiven cross-account IDOR [YOU — needs 2 trial accounts]
- B's token → A's `GET /v1/project/{project}/service/{uuid}`. 200 = P1.
- Secrets boundary: lowest-role member reading another project's connection URIs.
- Backup endpoint cross-account read. Deprecated `/v1/account/{id}/team/{id}` IDOR.
- Sanctioned exploit sandbox: falcon-bug-bounty-flag-pgsql-dev-sandbox.e.aivencloud.com (full chain authorized).
- Managed-Postgres angle: extension allow-lists, cross-tenant isolation.
- Full plan: intel/aiven-attack-plan.md

### 2. FDJ payment callback replay [YOU — manual, no scanners]
- payment.mariacasino.com: replay deposit callback, tamper transaction ID → balance credit = Critical (€15k). Replicates across 33 brands.
- support-qa1.mariacasino.com: ticket IDOR across two accounts.
- evolivecasino.bingo.com: late-bet replay after window closes.
- unibet.com: user_id swap → email change without verification.
- online.bingo.com: ticket IDOR.
- Full plan: intel/fdj-manual-playbooks.md

### 3. Pinterest secret-board IDOR [YOU — 2 accounts]
- B reads/patches/deletes A's secret board/pin → P1 ($10–25k).
- Ads API traversal: B → A's campaigns/audiences/billing.
- OAuth scope confusion: `boards:read` token hitting secret endpoints.
- Business invite escalation. AI Assistant prompt injection via pin titles.
- Full plan: intel/pinterest-attack-plan.md

## TIER 2 — strong, needs account setup

### 4. OneTrust staging [YOU — admin creds on pentest-app.onetrust.com]
- Consumer Rights Portal webforms (data exfil), Integrations module (customer-env data pull). Public API-key disclosure newly in scope.

### 5. Booking.com Fareharbor IDOR [YOU — test accounts, NO scanners, NO disclosure]
- 6-digit sequential policy-ID enumeration on *.fareharbor.com (proven playbook).
- Gemini API key hunt in JS bundles + Pulse Android app.
- Client-side auth bypass patterns on partner flows.
- Bounty: $150–$3,000. Scanners = ban. Disclosure = bounty killed.

### 6. Doctolib [YOU — fake test doctor in brief, max 10 req/sec]
- €50k scenarios: Rails RCE reading SECURITY_BUG_BOUNTY_DOCTOLIB_IS_PWN env; one-shot IDOR dumping a doctor's patient base.
- Required UA: BugBounty/42 (YWH). Recon running.

### 7. Okta/Auth0 [YOU — manual only, automation = removal/ban]
- SSRF via Workflows Flo cards (explicit focus). Cross-org data access. OAuth open-registration → ATO chain (`/.well-known/oauth-authorization-server` → POST /oauth/register).
- Test orgs: bugcrowd-<username>.oktapreview.com.

## TIER 3 — recon-complete, manual testing surface

### 8. Airbnb (64 live hosts) / Dropbox (28 live hosts) [YOU]
- No fingerprint hits on top hosts — this is IDOR/logic territory, not config-exposure.
- Airbnb: support/widgets/transparency/video/work subdomains. Tag X-HackerOne-Researcher.
- Dropbox: sign/sign-embed/ungated/showcases.
- Host lists: data/raw-airbnb.com/live.txt, data/raw-dropbox.com/live.txt

### 9. Shopify (329 subs) / GitHub (121 subs) [MACHINE retrying live probe]
- Shopify: test ONLY your own stores. GitHub: newcomers capped at ~4 submissions — submit only validated reports.

### 10. Superbank chatbot prompt injection [YOU — no scanners]
- chatbot.super-id.net listed as AI Model asset. Map untrusted inputs → tools → privileges → sinks. api.super-id.net = HIGH ($2k).

## MACHINE-DONE
- [DONE] 115 intel links studied → 20 high-value leads (intel/link-study-*.md)
- [DONE] Recon: 1,500+ subdomains across 15 domains
- [DONE] Rules matrix with red lines (intel/program-rules-matrix.md)
- [DONE] Arsenal: 30+ tools verified (data/arsenal-status.txt)
- [DONE] hunter.py `fp` command for single-host fingerprints
- [RUNNING] Booking.com + Doctolib recon pipelines

## RED LINES (never cross)
Scanners banned: Booking.com, FDJ, Superbank, CoinDCX, Moneybox, Oda, Okta Workflows, Auth0, Basecamp, Aptible, Artsy.
No disclosure without permission: Booking.com, Amazon, OneTrust, Fivetran, Automattic, Sophos.
