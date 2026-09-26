# FDJ United — Payment Surface Recon (manual-only)

**Date:** 2026-09-26 · **Analyst:** subagent (manual recon) · **Program:** FDJ United (YesWeHack)
**Scope verified:** `program-rules-matrix.md` (FDJ row — scanners/automation BANNED, own accounts only, no disclosure without written permission) + `fdj-manual-playbooks.md` (authoritative playbook, followed).
**Constraint honored:** no scanners (no nuclei/ffuf/sqlmap/zap), no automation, human-paced single requests only. No deposits, no real money, no KYC docs, no other users' data. Stayed unauthenticated (test-account credentials not available to this agent).

---

## 1. Surface map

| Asset | Observed behavior |
|---|---|
| `payment.mariacasino.com` | Resolves (198.18.219.252). `Server: Ironman-Loadbalancer`. **Every probed path returns the identical 22-byte stub** `<!DOCTYPE html></html>` with HTTP 200: `GET /`, `GET /callback`, `GET /robots.txt`, `POST /`. CSP `default-src: 'none'`. No path/method differentiation — no 404s, no 405s, no verbose errors. |
| `www.mariacasino.com` | Direct egress gets **HTTP 503** (`Server: kindred-loadbalancer`, `X-OS-Class: M` device-classification headers) — geo/bot filtering of datacenter egress. Reachable via alternate fetch path (homepage = marketing content, no cashier links visible pre-login). |
| Sibling payment hosts | `payment.unibet.com`, `payment.bingo.com`, `payment.32red.com` — probe pending (see §4). |
| Certs (CT logs) | `*.mariacasino.com` wildcard (Let's Encrypt, renewed 2026-07-13); `welcome.mariacasino.com`; `evolivecasino.mariacasino.com` (SSL.com); SendGrid aliases under `*.email.mariacasino.com`. No dedicated `payment.*` cert observed — covered by wildcard. |

**Interpretation:** `payment.mariacasino.com` behaves as a **dedicated gateway-return/callback receiver**, not a user-facing cashier. The uniform stub means real callback endpoints are **opaque paths** (tokenized URLs) only discoverable from inside an authenticated deposit flow — they cannot be guessed from outside, which is good design (no path oracle). The cashier UI itself lives behind login on `www.mariacasino.com`.

## 2. Findings

### F-1 — Payment callback host fingerprint: uniform stub, no error oracle [INFO]
- **Evidence:** 4 single manual requests (`GET /`, `GET /callback`, `GET /robots.txt`, `POST /`) → all HTTP 200, identical 22-byte body, `Content-Type: text/html`, no `Server` version leak beyond `Ironman-Loadbalancer`.
- **Severity:** Informational. **Confidence:** High.
- **Security read:** Positive — no verbose errors, no method/path differentiation to mine. Callback replay testing is **impossible without a genuine callback URL**, which only the authenticated deposit flow yields. This validates the playbook's prime hypothesis as *account-required*, not externally reachable.

### F-2 — Production www host 503s datacenter egress (bot/geo gating) [INFO]
- **Evidence:** `curl` from research egress → `503 Service Temporarily Unavailable` (nginx body, `kindred-loadbalancer`, `X-OS-Class: M`); same URL renders fine via residential/text-fetch path.
- **Severity:** Informational (defensive note, not a vuln). **Confidence:** High.
- **Read:** Automated recon from cloud egress is filtered; manual browser-based testing (the sanctioned path) is unaffected.

### F-3 — Sibling payment hosts share the identical stub (platform-wide) [INFO]
- **Evidence:** single manual `GET /` to `payment.unibet.com`, `payment.bingo.com`, `payment.32red.com` → all HTTP 200, 22-byte body, `Server: Ironman-Loadbalancer`, same `default-src: 'none'` CSP.
- **Severity:** Informational. **Confidence:** High.
- **Read:** the stub is Kindred shared-platform behavior, not brand-specific. A callback-signing flaw would therefore be **systemic across brands** (report once per program rules) — raises the value of the authenticated callback test in §3.

## 3. Callback hypothesis — theoretical analysis (no live callback available)

Since callback URLs are opaque and account-gated, the replay hypothesis remains **theoretical** until the test account lands. The playbook's test plan stands as written; key checks for the authenticated session:
1. **Capture** the gateway return URL during a minimum deposit (do not complete payment).
2. **Inspect signing:** look for `signature`/`hmac`/`checksum` params, signed amount fields, or server-side session binding (opaque `transaction_id` only).
3. **Single replay** with `status=success` on a *cancelled/failed* transaction — credit without payment = Critical. **One attempt, minimum amount, stop at the credit screen.**
4. **Do NOT** loop, fuzz, or brute-force callback params (rule: manual-only, no heavy traffic).

## 4. Test/sandbox modes in production JS
- **Not assessable unauthenticated:** cashier JS loads post-login. Deferred to the authenticated session — check bundles for `sandbox`, `testMode`, `mockGateway`, staging API hosts.

## 5. Eliminated / not pursued
- Path enumeration on `payment.mariacasino.com`: uniform stub kills this vector (no oracle). Stopped after 4 requests — further guessing = scanner-like behavior, out of bounds.
- Public web search for callback format docs: no results (no public documentation to leverage).

## 6. Recommended next steps (for the authenticated session)
1. Log in with the test account → walk the minimum-deposit flow → capture the full request sequence including the gateway return/callback URL.
2. Run playbook TARGET 1 tamper battery (amount/currency/param-pollution/negative) — one at a time, never completing.
3. Single callback-replay test per §3.
4. Dump cashier JS bundles → grep for `sandbox|test|mock|staging` hosts and signing logic.
5. If `support-qa1.mariacasino.com` resolves, run playbook TARGET 2 (QA ticket IDOR).

---
*No vulnerability confirmed. No deposits made, no accounts created, no other users' data touched. Total outbound requests to target infra: <15, human-paced.*
