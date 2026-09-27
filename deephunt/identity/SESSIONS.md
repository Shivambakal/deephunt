# Session persistence design

## Where authenticated state lives

In the live browser's **persistent Chromium profile** — the same profile every
browser task shares. Cookies, localStorage, and session tokens stay inside the
browser. This engine NEVER writes session cookies or tokens to disk, logs, or
memory files.

## Why not a session file

- Session cookies are credentials. A `sessions.json` on disk is a credential
  store without a vault — one `cat` away from exposure.
- The Secure Vault holds passwords (user-set via secure cards). The browser
  fills them from the vault at sign-in time. The resulting session stays in
  the browser profile, which is the narrowest place it can live.

## How sign-in reuse works

1. First sign-in: browser task signs in with the vault-filled password.
   Task reports `SIGNED_IN`. Engine marks identity `active`.
2. Later runs: browser task starts, checks for an existing valid session
   (e.g. visits the login page — if redirected to the app, session is live).
3. If the session expired: task re-signs-in from the vault. Passwords are
   never typed by the agent and never appear in briefs.

## What the engine tracks

Only metadata: identity status (`active`), last verified date, and notes.
`identity/manager.py` holds this. Anything shaped like a secret is refused
by the registry — it has no field for it by design.

## Rotation / revocation

- If a target signs the session out or the password changes, the task reports
  it, the engine marks the identity `verifying`, and sign-in is retried from
  the vault.
- If the user revokes a test account, mark it `retired` in the registry.
