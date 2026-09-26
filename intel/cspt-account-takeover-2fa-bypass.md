# CSPT to Account Takeover + 2FA Bypass via Prototype Chain ($15k)
Source: https://whoareme.com/blog/cspt-account-takeover-2fa-bypass/
Date saved: 2026-09-26

## Summary
Two chained primitives, $15k bounty. (1) Client-Side Path Traversal (CSPT): a team-invite link feature built API URLs by concatenating `window.location.search` params (`teamId`, `inviteId`, `method`) with no validation — `"/api/v2/teams/" + teamId + "/invites/" + inviteId`. By setting `teamId` to a traversal payload with encoded `?`/`&` (`%3f`, `%26`), the browser normalized the request into an arbitrary authenticated `PUT /api/v2/user?email=attacker@...`, rewriting the victim's email → password reset → account takeover. `method=1` selected PUT, `method=2` selected DELETE. (2) 2FA bypass: the SMS-code check was `if (pendingCodes[code])` on a plain JS object — sending `__proto__` as the `X-2FA-Code` header value resolved through the prototype chain to truthy `Object.prototype`, passing the check with no valid code. Not prototype pollution — a read-side `[[Get]]` issue. Same primitive hits any plain-object lookup gate: session stores, rate limiters, feature flags (`toString`, `constructor` also truthy).

## Agent relevance — DETECTION FINGERPRINTS
- CSPT markers: front-end JS building API URLs from `URLSearchParams` / `window.location.search` via string concatenation (search bundles for `"api/" +` patterns); invite/share/settings links carrying `action=`, `method=`, id-like params; DevTools Initiator tab showing PUT/DELETE fired from page load with query-derived paths.
- 2FA bypass markers: OTP/2FA verify endpoints accepting the code in a header (`X-2FA-Code`) or param; Node.js/Express backends (`X-Powered-By: Express`); error strings like `auth.code_invalid`; verify endpoints returning session tokens.
- Test values for lookup-gate bypass: `__proto__`, `toString`, `constructor`, `hasOwnProperty` — any truthy response or session issuance = vulnerable pattern.

## Guided manual-test steps (own authorized test accounts only)
1. In Burp/DevTools, find any feature where page-load query params flow into API request paths or methods; try `../` segments and encoded `?`/`&` in those params and watch the resulting request line.
2. If you can redirect an authenticated PUT/DELETE to another endpoint, test against your OWN second account's profile endpoint (email change) — never another person's.
3. On any OTP/2FA verification endpoint, submit prototype-chain keys (`__proto__`, `toString`, `constructor`) as the code value and compare responses against a wrong code — a 200/session where a wrong code gives 401 is the signal.
4. Generalize: anywhere a lookup table gates access (rate limits, feature flags, session checks), try the same keys via the relevant header/param/IP field.
