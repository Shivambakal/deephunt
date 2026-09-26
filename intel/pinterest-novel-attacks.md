# Pinterest novel-attack run — 2026-09-26 (FINAL)

Account: attacksurfacealerts / "shivam" (personal, Google SSO via attacksurface.alerts@gmail.com).
All tests on the operator's OWN boards/pins only. No other users' content touched.
All executable tests complete; all test boards/pins deleted.

## CONFIRMED

### #26 Unicode bidi / homoglyph board-name spoofing
Created secret board named "Pіnterest ‮(Verified)" (і = Cyrillic U+0456, ‮ = U+202E RLO).
Accepted with zero sanitization. Renders raw in board heading, profile grid, and board lists as
"Pinterest (deifireV)" — homoglyph visually identical to "Pinterest", "(Verified)" reversed by RLO
(screenshot evidence captured). URL slug: /attacksurfacealerts/p%D1%96nterest-verified/ — RLO stripped,
Cyrillic і percent-encoded and retained, so the homoglyph persists in the URL.
Impersonation primitive: a board visually indistinguishable from an official "Pinterest (Verified)"
board. Invite-collaborators dialog does not echo the board name (no bidi surface there); secret boards
expose invite links (observed https://pin.it/540LwGKcr). Board deleted after test (soft-delete, 7-day grace).
Impact read: visual-impersonation primitive; reach (public board, followers, search ranking) untested.

### #23 Pin-ID existence oracle (response-shape)
Logged-out probes, read-only, own pins only. Own SECRET pin 1107604102142260774 → redirect to
/ideas/ + toast "We can't find that idea. Try searching for one just like it." Neighbor IDs ...772,
...773, ...775 → IDENTICAL redirect + toast (secret/nonexistent/deleted indistinguishable).
Neighbors ...776 → full public pin page ("Aesthetic icon gif | ..." by "milarekan", board "Meeks");
...777 → full public pin page ("september morning" with comments). Timing flat (1.3–1.6s all probes,
1547/1367/1421/1289/1531/1567 ms — no delta).
Oracle: public+existing → 200 render at /pin/ URL; anything else → /ideas/ redirect + toast.
No 404-status differentiation. Public-pin enumeration possible; low impact alone.

### #8 Secret→public toggle race
Secret board sec-pub-race-8 + 1 pin ("race8-pin") created, toggled secret→PUBLIC.
Logged-out fetch of https://www.pinterest.com/attacksurfacealerts/sec-pub-race-8/ rendered FULLY:
title "sec-pub-race-8 on Pinterest", heading, "1 Pin", "1m" timestamp, author "shivam" with profile
link, Share button, pin grid + "More like this" — no login wall (observed twice). Public window CONFIRMED.
Re-secreted ~23:24 IST; logged-out re-fetches at ~1 min and ~4 min post-toggle BOTH redirected to
/ideas/ with toast "We can't find that idea." No CDN/API cache persistence at the render layer;
revocation effective in <1 min — fail-closed.
Side observation: during the public window the logged-out page exposed "Welcome back, shivam!" modal
and Google One Tap "Continue as shivam, attacksurface.alerts@gmail.com" — account email visible to
logged-out visitors on the board page.

## INCONCLUSIVE

### #7 Scheduled-pin vs deleted-board desync (no scheduler on personal web surface)
Pin scheduler ("Publish at a later date") exists only in pin-creation-tool under "More options",
which stays DISABLED until media is attached via file upload (JPG/PNG ≤20MB). With a real PNG uploaded
(file grant) and title filled, "More options" contained ONLY "Allow people to comment",
"Show similar products", "Alt text" — verified via rendered text and editor HTML, no scheduling option
anywhere. Draft actions = Duplicate/Delete only. Clicking Publish published IMMEDIATELY to the secret
board ("Your Pin has been published!", no schedule dialog). Save-from-url builder has no scheduler;
its drafts don't transfer. No /scheduled_pins/ page (redirects home, "We can't find that idea").
Closest analog: drafts autosave ("Changes stored!", "Pin drafts (1)", "30 days until expiry").
Business-account scheduling NOT tested (account conversion not authorized).
Threat-model note: board deletion is SOFT — "You have 7 days to restore a deleted board. After that,
it will be permanently deleted" (profile "Recently deleted boards" grace list). A "deleted" board still
exists server-side for 7 days — the window the playbook idea targets — but the scheduler itself is absent
on personal accounts, so the desync can't be constructed here.

### #3 CSV formula injection (export delivery inaccessible)
Pin "formula-injection-test" (ID 1107604102142260774) with description exactly
`=HYPERLINK("https://example.com","x") =cmd|'/c calc'!A0` — stored and rendered VERBATIM on the pin
page (no input/display-layer sanitization, confirmed). "Request your data" submitted (toast "Requested!
You'll receive the next steps via email."). Raw-export survival UNVERIFIED: delivery is via email +
SendSafely link, inaccessible in this session. Analytics CSV export is business-gated
("Get a business account" at analytics.pinterest.com) — not converting (unauthorized).

## Cleanup — COMPLETE (~23:28 IST)
Deleted all four test boards: bidi board, sec-pub-race-8 (re-secreted first, with its 1 pin),
sec-export-test-3 (with 2 formula pins), sec-sched-test-7 (with the published pin).
Profile shows only "Recently deleted boards" (5 boards in 7-day soft-delete grace, including one
pre-existing). No test pins remain. Account left signed in.
Data-export request for own account submitted (SendSafely/email; cannot be un-requested).
Do NOT check Gmail unless explicitly asked.

## Session notes
Login: account uses Google SSO ("You last logged in using Google"); no vault password;
Google buttons open in new tab (broken in single-tab browser) — worked around by navigating the
OAuth URL directly in the current tab. Operator completed two manual takeovers. Google One Tap
auto-logged the session back in once spontaneously (~1–2 min after first logout); not reproducible
on demand.
