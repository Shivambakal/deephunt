# Aiven novel-attack run — 2026-09-26

Scope: own trial org only ("My Organization", account a5e30aee95f0). No services, databases,
payment methods created; $0 spent; $50 trial credits intact. All synthetic artifacts cleaned up.
Session left signed in on the Projects page.

## REJECTED (tested, no vulnerability)

- **#9 Token double-submit** — double-clicking "Generate token" fires once; the dialog instantly
  unmounts the submit button, second click never dispatches. Exactly 1 token minted.
- **#12 Back-button resubmission** — revoke is a dialog-confirmed API call, not a replayable form
  POST; Back shows no resubmission prompt. Event log shows each of 8 project create/delete pairs
  exactly once — zero duplicates.
- **#18 Trial-credit arithmetic** — 8 empty projects created and deleted; banner read
  "$50.00 USD trial credits, 30 days left" after every transition. Zero drift.
- **#22 UUID case normalization** — upper/mixed-case org IDs render the identical not-found page;
  exact lowercase match required, no normalization.
- **#23 Existence oracle** — random vs one-hex-off foreign org IDs return byte-identical not-found
  pages; timing delta within SPA variance. No oracle.
- **#3 CSV formula injection** — project rename to `=HYPERLINK(...)` blocked by name allowlist
  (letter-start, alnum+dashes, 4–63 chars). Payload can't be stored, so no sink to test.
- **CHAIN B (stored payload across sinks)** — project names, tag keys, and org names all enforce
  strict allowlists (`<img src=x>{{7*7}}` rejected everywhere). The attack class dies at input
  validation; audit log, invite dialogs, lists, errors, support prefill untestable with live payload.

## INCONCLUSIVE (not testable with available tooling)

- **#16 Referer leak** — login flow not observable without signing out (lockout risk). Mitigation
  evidence in rendered HTML: `<meta name="referrer" content="strict-origin">` — query strings never
  leave in Referer. Third-party hosts on console pages: fe.sitedataprocessing.com, claydar,
  googletagmanager, doubleclick, cookielaw (OneTrust), flaticon, maxcdn. No session_id-in-URL observed.
- **#19 Quota ceiling** — 10 projects created without refusal; stopped to avoid abuse. No free-tier
  ceiling observed within bounds.
- **#25 session_id substitution** — real authorize endpoint template not capturable without sign-out;
  fabricated session_ids against guessed paths return safe SPA 404s. Real flow untested.
- **CHAIN A (real-time channel auth)** — devtools/CDP outside permitted tools; WS/SSE/polling
  endpoints and handshake auth unverified.

## OBSERVATION (audit gap, not a confirmed vuln)

- **Token lifecycle is not audit-logged.** Application-user token generate/revoke produce no event in
  Admin > Event logs; the Event-types filter lists no token-lifecycle types (ai_gateway_key_create/
  revoke exist, but nothing for application-user tokens). Security-relevant credential actions are
  invisible to org audit. Worth a retest if deeper access is available; potential Low (audit
  completeness).

## Cleanup verified

Deleted novel-proj-1..8; revoked test token; deleted app user novel-app-user; removed test tag rows.
Final state: 2 pre-existing projects (attacksurface-d344, attacksurface-d344-b), $50.00 credits /
30 days left, $0.00 total cost.
