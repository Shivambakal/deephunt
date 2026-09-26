# SSTI Chained to Account Takeover ($1,000 max payout)
Source: https://medium.com/@HariHax/everyone-chains-ssti-to-rce-i-chained-it-to-account-takeover-c279188ff9ce
Date saved: 2026-09-26

## Summary
On a subscription billing platform (Twig/PHP), the email-template editor evaluated author-controlled input server-side. Key lessons beyond the RCE reflex: (1) default template text already revealed the engine — `{{invoice.balance|number_format(2)}}` and `{% if %}` blocks = Twig; (2) "200 OK" responses proved nothing — the invoice-number field silently discarded input, so always reload and re-read the saved value before ruling a field out; (3) the attack needed two requests with different jobs — Request A (POST template save) injects the expression into the subject line, Request B (GET email preview with `ref_id=<invoice>`) renders it against whichever customer's data that invoice belongs to; (4) instead of chasing RCE (failed 3x — no callable functions in scope), dumping `{{_context|json_encode}}` exposed the raw DB row including `users[0].saas_password` (hash), `saas_salt`, and `login_token`. Chain: trigger public password-reset form for the target email (creates a `login_token` without changing their password) → preview the invoice email → read the live token off the screen → redeem at the token-login URL → full portal login as the customer. The app's own API already stripped those fields — the template got the raw row. CVSS 8.5, CWE-1336 → CWE-522/640.

## Agent relevance — DETECTION FINGERPRINTS
- SSTI markers in template editors: default content containing `{{ }}`, `{% %}`, `${}`, `#{}`; preview/render endpoints (paths with `preview`, `render`, `email`, `template`); save endpoints for message/notification templates.
- ATO-via-template markers: preview URLs taking an object id (`?ref_id=`, `?invoice_id=`, `?customer_id=`) — test whether changing the id renders ANOTHER record's data in your template.
- Token-login markers: password-reset flows that create single-use login tokens; login URLs shaped like `/logintoken/<token>` or `?token=`; API user objects that omit password/token fields (compare API output vs template-rendered output for the same record — the delta is the bug).
- Probe sequence: `{{7*7}}` arithmetic check → `_context`/context dump for the engine in use → enumerate visible variables → look for credential/token fields.

## Guided manual-test steps (own authorized test accounts only)
1. In any template/message editor, save `{{7*7}}`-style probes per engine syntax, then RELOAD the saved value — a 200 that silently drops input is not a negative.
2. Find the preview/render path and test IDOR on its object parameter: does previewing another record's id render their data through your template? Use only your own second test account's records.
3. Dump the template context object to enumerate exposed fields; flag any credential, hash, salt, or token fields the API normally withholds.
4. If tokens are exposed, verify the full chain on your own accounts: public reset → preview → redeem token → confirm login, then report with both the SSTI and the excessive-data-exposure findings.
