# FDJ/Kindred — Hybrid-App Bridge Attack Surface (Passive)

**Date:** 2026-09-26 · **Analyst:** subagent (passive only — no exploitation, no probing)
**Scope note:** FDJ/Kindred brands are MANUAL-ONLY. This is recon for later manual
testing with the user's own account. Methodology: `deep-vuln-methodology.md` §3, §5
(cross-feature: mobile-app × web × auth; differential: iOS vs Android link handling).
**Evidence base:** archived `www.mariacasino.com` homepage HTML + SystemJS module map
(2026 Wayback snapshot), `kaf-kmf-login` bundle `1c00e1b1.system.min.js` v0.42.116,
`kmf-webview-terminator` stub, `.well-known/apple-app-site-association` and
`assetlinks.json` for mariacasino.com + unibet.com. Raw artifacts:
`~/workspace/hacker-agent/data/kwp/`.

---

## [SCHEME/BRIDGE INVENTORY]

### S1. Per-brand custom URL schemes (CONFIRMED — bundle evidence)
`kaf-kmf-login/0.42.116/1c00e1b1.system.min.js` contains the app→scheme map:
```
JC={UNIBET_PRO:"unibetpro", UNIBET_PRO_FR:"unibetprofr", CASINO_APP:"casinoapp",
    CASINO_APP_FR:"casinoappfr", MARIA_CASINO_APP:"mariacasino",
    RED_32_CASINO:"red32casino", VLAD_CAZINO_APP:"vladcazinoapp"}
```
Seven schemes across the brand family (Unibet sports/casino, Maria Casino, 32Red,
Vlad Cazino — the Kindred portfolio). Any app on a victim's device can fire these
URLs; the OS routes them to the Kindred native app.

### S2. WebView bridge scheme `jockey:` (CONFIRMED — CSP evidence)
Prior static work (`fdj-deep-static.md` §6) captured the live CSP:
`default-src 'unsafe-inline' 'unsafe-eval' http: https: data: wss: blob: jockey: unibetpro: *`.
`jockey:` is the JockeyJS-style iOS webview-bridge scheme (web→native event
channel via hidden navigations). **No Jockey client code was found in any downloaded
web bundle** (login bundle: 0 `postMessage`, 0 `messageHandlers`, 0 `jockey`
references; dev-tools bundle: 0 hits) — the bridge client is almost certainly
**injected by the native app at runtime**, so the true native method table is NOT
recoverable from web bundles. APK/IPA analysis is the missing source.

### S3. Universal Links route table — iOS (CONFIRMED — AASA evidence)
`.well-known/apple-app-site-association` (14,685 bytes, identical on mariacasino.com
and unibet.com — shared platform). 23 unique paths across 8 app IDs
(`com.unibet.unibetmobile`, `com.unibet.flashgordon`, `com.unibet.casino-us`,
`com.unibet.sports-us`, each in App-Store and enterprise variants):
```
/unibetpro/myaccount/mymoney/cashier        ← PAYMENTS
/unibetpro/registration                     ← ACCOUNT CREATION
/unibetpro/itsme-verification-completed      ← KYC CALLBACK (itsme, Belgium eID)
/unibetpro/itsme-registration-completed      ← KYC CALLBACK
/sportsapp/dk-identification-completed       ← KYC CALLBACK (Danish ID)
/casinoapp/myaccount/mymoney/cashier        (casino-app equivalents of all above)
/casinoapp/itsme-verification-completed
/casinoapp/itsme-registration-completed
/casinoapp/dk-identification-completed
/casinoapp/registration
/casinoappus/*, /unibetprous/*              (US-app equivalents)
/promotions/*                               (wildcard)
/betting/sports/event/live/*, /betting/sports/filter/*, /betting/sports/racing/*,
/betting/racing*, /racing*, /racing#/next/all*
```

### S4. Android App Links (CONFIRMED — assetlinks.json evidence)
`delegate_permission/common.handle_all_urls` granted to `com.unibet.mariacasino`,
`com.mariacasino.casino`, and (unibet.com) `com.unibet.unibetpro`. **Android imposes
no path restriction** — any URL on the brand domain can open the native app; the
app's own intent-filters decide what to do with it. Differential vs iOS (23-path
allowlist): the Android surface is strictly larger.

### S5. Cross-app SSO ticket handoff (CONFIRMED — bundle evidence)
Login bundle: ``window.location.assign(`${C}/ssologin?ssoLoginTicket=${i}&redirectUrl=${encodeURIComponent(e)}`)``
where `redirectUrl` is derived from `window.location.href` minus origin (path-only
in the observed code). A ticket-in-URL SSO between the brand apps — the session
bootstrap primitive for app-to-app handoff.

### S6. Identity-provider routes (CONFIRMED — bundle evidence)
Login bundle routes external eID verification through provider paths:
`[/\/bankid(\/|$)/,"bankid"], [ /\/criipto(\/|$)/,"criipto"], [ /\/itsme(\/|$)/,"itsme"], [ /\/paynplay(\/|$)/,"paynplay"]`
(BankID SE, Criipto, itsme BE, Pay N Play). The `*-verification-completed` deep
links (S3) are the return leg of these flows.

### S7. Webview gate stub (CONFIRMED — bundle evidence)
`@global/logged-in/kmf-webview-terminator` (`kmf-webview-terminator/0.10.1/60383b58.system.min.js`)
is a no-op: `System.register([].…e("default",(()=>null))`. Whatever webview
lifecycle gating was planned here is inert in the archived build. Separately, the
forgot-password flow branches on an `isNative` flag — native vs web behavior
differs in auth flows (differential-testing note).

---

## [SENSITIVE BRIDGE METHODS]

Honest scoping: **the native bridge method table is not in the web bundles**
(S2). What IS confirmed sensitive, by deep-link entry point:

| Entry point | Touches | Why it matters |
|---|---|---|
| `…/myaccount/mymoney/cashier` (×4 app flavors) | Payments: deposits/withdrawals | Deep link lands the victim's app directly in the money flow |
| `…/registration` (×4) | Account creation | Pre-fill / state-confusion at signup |
| `…/itsme-verification-completed`, `…/itsme-registration-completed`, `…/dk-identification-completed` | KYC/identity verification state | If the app flips "verified" on link arrival without re-querying the provider, identity proof is URL-spoofable |
| `/ssologin?ssoLoginTicket=` | Session bootstrap across apps | Ticket-in-URL: theft via Referer/logs/shoulder-surfing = cross-app session hijack |
| `/promotions/*` (wildcard) | Bonus/promo claims | Wildcard path — check whether promo *actions* (not just pages) are reachable |

---

## [HYPOTHESES — ranked for manual testing]

**H1. KYC-callback trust (itsme / DK identification).** *Invariant: "verified"
state must come from the identity provider's server-side result, never from the
arrival of a deep link.* Test (own account, manual): complete a real itsme/BankID
flow, capture the exact `*-verification-completed` URL shape, then replay a
synthesized completion URL in a fresh state and observe whether the app/account
reflects verified status without a provider round-trip. *Why first: identity
verification bypass on a gambling operator = regulatory-grade impact.*

**H2. SSO ticket theft / replay.** *Invariant: the ticket must be single-use,
short-lived, and device-bound.* Test: obtain your own `ssoLoginTicket` (via your
own app-to-app handoff), then replay it from a second context (different browser /
cleared state) and observe whether it still bootstraps a session, and inspect
expiry. Also check Referer leakage on the redirect leg.

**H3. Deep links must be navigation-only, never action-triggering.** *Invariant:
opening a link must not execute a state-changing operation.* Test each sensitive
path (cashier, registration, `/promotions/*` wildcard) with parameter variations
on your own account: does any deep link pre-fill AND submit, claim a bonus, or
change account state without an explicit in-app confirmation?

**H4. `redirectUrl` open redirect in the ssologin flow.** The web code builds a
path-only value, but the server-side `/ssologin` handler is unobserved. Test with
your own handoff whether absolute/external `redirectUrl` values are honored
(manual, single request, own account).

**H5. `jockey:` bridge event injection from untrusted web content.** *Invariant:
the native bridge must only accept events from the app's own web origin.* The CSP
is permissive (`*`, `unsafe-inline`), and casino pages embed third-party game/
ad iframes. Manual test: in the native app's webview context (own device/account),
check whether bridge events fire from a non-first-party frame. (Requires the
native app + a proxy — manual only.)

**H6. Android `handle_all_urls` vs iOS allowlist differential.** Any
attacker-influenced path on the brand domain opens the Android app. Combine with
H4: an open redirect whose target is a crafted brand-domain path could route the
victim's app to an unintended in-app state.

**H7. Scheme-squat / FR-variant confusion.** Seven schemes incl. `-fr` variants;
verify the apps actually register every scheme they advertise, and that no
advertised scheme is left unclaimed (squattable by a malicious app on the same
device).

---

## [REJECTED / NOT RECOVERABLE PASSIVELY]
- R1. Native bridge method names/signatures — not in web bundles; needs APK/IPA
  analysis (not performed; flagged as the follow-up source).
- R2. `payment.mariacasino.com` JSF JS files returned empty (22-byte) bodies from
  Wayback — cashier-side bridge code unrecoverable this way.
- R3. 32red.com / bingo.com AASA not archived (Wayback miss); identical-platform
  assumption is NOT confirmed — verify live before relying on it.
- R4. No secrets, tokens, or keys in any downloaded bundle.
- R5. `kmf-webview-terminator` is inert — not a bypassable gate, just a stub.

## Caveats
- All evidence is from 2026 Wayback snapshots (newest bundle timestamps May 2026);
  current production may differ — re-verify live paths at manual-test time.
- AASA/assetlinks snapshots are per-domain; brand coverage verified for
  mariacasino.com and unibet.com only.
- Nothing here is a confirmed vulnerability. Every hypothesis needs minimal,
  own-account manual reproduction before any claim is made.
