# Novel Attacks Playbook — 2026-09-26

Strategist-authored, not scanner-derived. Every idea names the exact trust
assumption (invariant) it violates, gives concrete test steps against OUR
actual capabilities, and explains why default tooling misses it.

**Our capabilities (ground truth):** authenticated browser sessions on
Pinterest (`attacksurfacealerts`) and Aiven (super-admin, own trial org, $50
credits, no services); GitLab source at `~/workspace/hacker-agent/src/gitlab`
(sparse clone — deep tracing delegated to white-box teams); working mitmproxy
harness (`proxy/`) with repeater/intruder. **Blocked:** raw HTTP with custom
headers, JS execution in browser, second accounts, paid actions, mailbox
access to the research Gmail, inbound webhook receivers.

**Feasibility legend:** ✅ testable now · ⚠️ partially testable · 🔒 blocked
(states what unlocks it) · 📖 white-box only for now.

---

## SECOND-ORDER / STORED-PAYLOAD FLOWS (write in A, detonate in B)

### 1. Stored HTML in pin/board metadata → notification email rendering — Pinterest — ⚠️
- **Violated invariant:** "User-controlled strings are neutralized at every
  render sink, including non-web sinks (email, push, embeds)."
- **Steps:** (1) Create pin/board with `<img src=x onerror=alert(1)>`,
  `{{7*7}}`, and markdown-image payloads in title/description on own account.
  (2) Trigger every downstream render: board-collaborator invite email,
  weekly digest, push notification, profile widget view. (3) Inspect each
  sink for unescaped HTML / executed template expressions.
- **Why scanners miss it:** Scanners test the input endpoint's immediate
  response, never the email/push sinks that render the same data hours later.
- **Feasibility:** ⚠️ — web-UI sinks testable now; email sink needs mailbox
  access we don't have (unlock: research-Gmail mailbox read).

### 2. Issue/MR title → email subject CRLF injection — GitLab — 📖
- **Violated invariant:** "Control characters in stored fields can never
  alter email envelope semantics."
- **Steps (white-box):** grep mailer views for `subject:` interpolation of
  `issue.title`; check whether `\r\n` in a title set via API survives to
  `mail(to:, subject:)`. Modern Rails strips CRLF — confirm or refute in
  source; if stripped, check Bcc/CC fields and custom notification templates.
- **Why scanners miss it:** Requires tracing a stored value across the
  mailer boundary; DAST never sees the email.
- **Feasibility:** 📖 now; runtime needs GitLab account verification (🔒).

### 3. CSV formula injection via exports — GitLab / Pinterest / Aiven — ✅
- **Violated invariant:** "Exported data is inert when opened in spreadsheet
  software."
- **Steps:** (1) GitLab: create issue titled `=HYPERLINK("https://evil.example","click")`
  and `=cmd|'/c calc'!A0` (own project). Export issues CSV; open raw and check
  whether the formula survives without `'`/`"` prefix sanitization or
  tab-prefixing. (2) Pinterest: same via analytics/audience export if
  available. (3) Aiven: audit-log / invoice export with formula-bearing org
  or project names.
- **Why scanners miss it:** The "vulnerability" only manifests in Excel/LibreOffice
  on the victim's machine; no scanner models that sink.
- **Feasibility:** ✅ via browser on own data (exports are read-only).

### 4. Webhook payload secret inclusion — GitLab — 📖
- **Violated invariant:** "Outbound webhook payloads contain only the event
  data the subscriber is entitled to — never secrets."
- **Steps (white-box):** read webhook data builders
  (`app/models/hooks/`, `lib/gitlab/data_builder/`) for `token:`,
  `secret`, or full variable values included in push/pipeline event payloads.
  Cross-check against masked-variable guarantees.
- **Why scanners miss it:** Requires code-level data-flow tracing across the
  event→payload boundary.
- **Feasibility:** 📖 now; runtime needs inbound receiver (🔒 sandbox has no
  inbound; unlock: third-party request-bin).

### 5. Org/project name → invoice/PDF/email rendering — Aiven — ⚠️
- **Violated invariant:** "Billing-adjacent renderers (PDF, email) escape
  tenant-controlled strings."
- **Steps:** (1) Rename own org/project to include `<script>`, `{{}}`,
  LaTeX-ish and Unicode-bidi payloads (revert after). (2) Trigger renders:
  invoice preview (none exist — note), invite emails, audit log page,
  support-ticket prefill. (3) Observe escaping in each sink.
- **Why scanners miss it:** Billing renderers are outside the auth-focused
  test paths everyone runs.
- **Feasibility:** ⚠️ — UI sinks ✅; email/PDF sinks 🔒 (no invoices exist;
  email needs mailbox).

### 6. Markdown/mention stored payload → Slack/Teams integration rendering — GitLab — 📖
- **Violated invariant:** "Chat-integration formatters neutralize stored
  markdown the same way the web UI does."
- **Steps (white-box):** compare the web markdown pipeline vs the
  Slack/Teams/Jira notifier formatters for allowed tags; look for
  `<a href="javascript:">` or unfurl-based SSRF via attacker-controlled URLs
  in issue bodies.
- **Why scanners miss it:** Cross-system rendering differential; scanners
  test one app.
- **Feasibility:** 📖 now; runtime 🔒 (needs integration + receiver).

---

## STATE-MACHINE DESYNC

### 7. Scheduled-pin vs deleted-board desync — Pinterest — ✅
- **Violated invariant:** "A publish job re-validates its target's existence
  and visibility at fire time, not just at schedule time."
- **Steps:** (1) Create secret board, schedule a pin to it. (2) Delete the
  board before fire time. (3) Observe: does the job fail closed, publish to
  a resurrected board, or error-leak board metadata? Also try: board
  secret→public→secret toggles around fire time.
- **Why scanners miss it:** Time-delayed state transitions are invisible to
  point-in-time scanning.
- **Feasibility:** ✅ own account, reversible.

### 8. Secret→public toggle race vs unauthenticated cache — Pinterest — ✅
- **Violated invariant:** "Visibility transitions are atomic with respect to
  the unauthenticated read path (no window where a secret object is served
  as public)."
- **Steps:** (1) Toggle a board secret→public→secret rapidly. (2) During
  the public window, fetch board/pin URLs unauthenticated (fresh profile +
  curl) and check CDN/API cache headers for how long the public version
  persists after re-secreting.
- **Why scanners miss it:** Requires a timed two-principal dance; scanners
  don't toggle state.
- **Feasibility:** ✅.

### 9. App-user token double-submit → duplicate mint — Aiven — ✅
- **Violated invariant:** "Token creation is idempotent under double-submit;
  exactly one credential exists per user intent."
- **Steps:** (1) In Admin > Application users, create token and double-click
  submit rapidly / resubmit via back-button. (2) Count minted tokens in the
  token list. (3) Same test on invite resend (already shown idempotent —
  use as control).
- **Why scanners miss it:** Race windows under human-paced double-clicks
  aren't in any scan profile.
- **Feasibility:** ✅ own org; revoke test tokens after.

### 10. Token revocation propagation delay — Aiven — 🔒
- **Violated invariant:** "Revocation is effective at all enforcement points
  before the UI confirms success."
- **Steps:** (1) Mint low-scope app-user token. (2) Revoke in console.
  (3) Immediately replay the token against the API in a tight loop for
  60s; measure the revocation-propagation window. (4) Also test: revoke
  while a long-lived session derived from the token is mid-use.
- **Why scanners miss it:** Requires precise revoke→replay timing with a
  real token; scanners don't hold credentials.
- **Feasibility:** 🔒 needs raw HTTP with Authorization header (unlock:
  HTTP-client capability + token wielding).

### 11. Invite-accept token replay after removal — Aiven — 🔒
- **Violated invariant:** "An invitation token dies the moment the invitation
  is removed; late acceptance is impossible."
- **Steps:** (1) Invite synthetic address. (2) Capture the accept URL
  (needs mailbox). (3) Remove the invitation. (4) Visit the captured accept
  URL. Observe: accepted / rejected / error-oracle.
- **Why scanners miss it:** Crosses the email boundary; scanners can't read
  the token.
- **Feasibility:** 🔒 needs mailbox access to the invite recipient.

### 12. Back-button resubmission of destructive console actions — Aiven — ✅
- **Violated invariant:** "Destructive actions are guarded by idempotency or
  one-time tokens, not by the dialog closing."
- **Steps:** (1) Perform remove-user / revoke-token; (2) hit back-button and
  resubmit; (3) check audit log for duplicate execution entries.
- **Why scanners miss it:** Browser-navigation state machines aren't
  modeled by API scanners.
- **Feasibility:** ✅ own org, synthetic objects only.

---

## CROSS-FEATURE TRUST

### 13. Granular PAT boundary_argument covers SOURCE only on issueMove — GitLab — 📖→🔒
- **Violated invariant:** "A scope boundary declared on one argument
  constrains every object the operation touches."
- **Evidence in hand:** `app/graphql/mutations/issues/move.rb` declares
  `authorize_granular_token permissions: :move_issue, boundary_argument:
  :project_path` (the SOURCE project), while the target is resolved via
  `resolve_project(full_path: target_project_path).sync` and passed to
  `WorkItems::DataSync::MoveService`.
- **Steps (white-box):** trace whether the granular-token check is
  re-evaluated against the TARGET project anywhere in `MoveService`/policies.
  If not: a PAT scoped to project A with `move_issue` could move issues
  INTO project B (cross-boundary write primitive).
- **Why scanners miss it:** Requires reading the authorization framework's
  boundary semantics, not just probing endpoints.
- **Feasibility:** 📖 now (sparse clone limits tracing — full trace is with
  the white-box team); runtime 🔒 (needs verified GitLab account).

### 14. CI_JOB_TOKEN accepted by GraphQL execution layer — GitLab — 📖→🔒
- **Violated invariant:** "A token minted for CI API access is rejected by
  the GraphQL execution layer (or constrained to the same scope)."
- **Steps:** (1, white-box) check how `Types::Base` / GraphQL controller
  authenticates `CI_JOB_TOKEN` vs PAT/OAuth — look for `ci_build` principal
  handling and whether `ci_job_token_scope` allowlist is enforced on
  GraphQL field resolution. (2, runtime when unblocked) run a pipeline in
  own project, exfiltrate `CI_JOB_TOKEN` to a job log (own data), replay it
  against `/api/graphql` for cross-project reads.
- **Why scanners miss it:** Token-type confusion across API paradigms
  (REST vs GraphQL) is a logic property, not a signature.
- **Feasibility:** 📖 now; runtime 🔒 (needs verified account + pipeline).

### 15. Web-session cookie vs API-token scope asymmetry — Aiven — 🔒
- **Violated invariant:** "The session token and an API token with the same
  nominal role can reach exactly the same endpoints."
- **Steps:** (1) Mint app-user token with minimal scopes. (2) Diff the
  reachable endpoint set: session-token-via-console vs scoped-token-direct
  across governance/appbuilder/connector/billing routes. (3) Any endpoint
  reachable by one but not the other = scope-enforcement differential.
- **Why scanners miss it:** Scanners test one credential type at a time.
- **Feasibility:** 🔒 needs raw HTTP with custom Authorization headers.

### 16. Console-SPA token in localStorage + third-party Referer leak — Aiven — ✅
- **Violated invariant:** "Session material in the URL never leaks to third
  parties via Referer."
- **Evidence in hand:** login redirects to the API authorize endpoint with
  `session_id` as a query param (browser-task finding).
- **Steps:** (1) In browser devtools network log, capture the authorize
  redirect chain. (2) List every third-party host loaded on the login/
  authorize/callback pages (analytics, fonts, chat widgets). (3) If any
  third-party subresource loads on a page whose URL contains `session_id`,
  the full session leaks via Referer — verify with the proxy harness
  header log.
- **Why scanners miss it:** Information-flow via Referer isn't an endpoint
  property.
- **Feasibility:** ✅ passive observation + proxy logs.

### 17. Staging↔production credential crossover — OneTrust — 🔒
- **Violated invariant:** "Credentials/tokens minted in staging are rejected
  in production (environment isolation)."
- **Steps:** when Bugcrowd access lands: (1) obtain staging session;
  (2) replay staging cookies/tokens against production endpoints and vice
  versa; (3) check shared SSO/OIDC issuer (`iss`) across environments.
- **Why scanners miss it:** Multi-environment trust isn't in scope of
  single-target scans.
- **Feasibility:** 🔒 blocked on Bugcrowd access.

---

## BUSINESS LOGIC (trial / quota / invite arithmetic)

### 18. Trial-credit arithmetic via org/project lifecycle — Aiven — ✅
- **Violated invariant:** "Credit grants are bound to account lifecycle
  events exactly once; no lifecycle path double-grants or refunds
  phantom credits."
- **Steps:** (1) Record credit balance. (2) Create then immediately delete
  empty projects (free); create/delete org units if permitted. (3) Check
  balance after each transition for grants, refunds, or negative drift.
  (4) Never create services; never touch payment methods.
- **Why scanners miss it:** Business arithmetic has no CVE signature.
- **Feasibility:** ✅ read-only-ish; stop at first anomaly.

### 19. Project-count / quota ceiling enforcement — Aiven — ✅
- **Violated invariant:** "Free-tier object ceilings are enforced
  server-side, not just hidden in UI."
- **Steps:** (1) Create empty projects up to any documented free limit
  (second project already exists). (2) Attempt one beyond; observe whether
  the API or only the UI refuses. (3) Delete test projects after.
- **Why scanners miss it:** Quota logic isn't probed by vuln scanners.
- **Feasibility:** ✅ (empty projects are free; keep count small).

### 20. Subscription downgrade mid-cycle proration — PayPal sandbox — 🔒
- **Violated invariant:** "Downgrade/upgrade proration arithmetic can't
  produce negative charges or free premium windows."
- **Steps (when sandbox lands):** per battle plan — create subscription,
  upgrade/downgrade mid-cycle with trial periods, compare charged amounts
  vs expected proration; test downgrade→immediate-cancel→re-subscribe
  for stacked-trial abuse.
- **Why scanners miss it:** Pure business logic; invisible to scanners.
- **Feasibility:** 🔒 blocked on PayPal developer access.

---

## IDENTIFIER-TYPE CONFUSION

### 21. GlobalID type confusion on `target_work_item_type_id` — GitLab — 📖→🔒
- **Violated invariant:** "A GlobalID argument is only ever resolved as its
  declared type."
- **Evidence in hand:** `move.rb` takes
  `::Types::GlobalIDType[::WorkItems::Type]` then calls
  `target_work_item_type_id.model_id.to_i`.
- **Steps (white-box):** check `GlobalIDType`'s locator: does it verify the
  gid's model class matches `WorkItems::Type`, or does it blindly resolve
  any `gid://gitlab/.../<id>` and take `model_id`? If blind: pass a
  `Project` or `User` GlobalID and observe which record's id is used as the
  work-item type id (type-confusion → wrong-type record referenced).
- **Why scanners miss it:** Requires reading the scalar coercion code.
- **Feasibility:** 📖 now; runtime 🔒 (needs verified account).

### 22. UUID case-normalization differential — Aiven — ✅
- **Violated invariant:** "Identifier normalization is identical across
  routing, authorization, and cache layers."
- **Steps:** (1) Take own org/project UUIDs; request the same object with
  uppercased, mixed-case UUIDs via console navigation. (2) Compare: does
  authz behave identically? Do cache headers differ (cache-key desync =
  potential cache-poisoning/deception primitive)?
- **Why scanners miss it:** Case variants aren't in fuzz lists for UUID
  paths.
- **Feasibility:** ✅ read-only navigation.

### 23. Sequential-vs-UUID ID oracle on "not found" wording — Aiven/Pinterest — ✅
- **Violated invariant:** "Existence oracles don't distinguish 'no such
  object' from 'not yours'."
- **Steps:** (1) Aiven: compare response bodies/timings for random UUID vs
  well-formed-but-foreign UUID on account/project routes (already saw
  "could not be found" — now test TIMING differential for enumeration
  oracle). (2) Pinterest: numeric pin-ID enumeration on secret pins via
  unauthenticated fetch; compare 404 body vs redirect vs timing.
- **Why scanners miss it:** Timing/existence oracles need statistical
  probing, not payloads.
- **Feasibility:** ✅ own objects + unauthenticated probes.

---

## OAUTH / OIDC EDGE CASES

### 24. Doorkeeper `redirect_uri` loose matching — GitLab — 📖
- **Violated invariant:** "Registered redirect URIs match exactly; no
  subdomain, path-traversal, or fragment variance is accepted."
- **Steps (white-box):** read Doorkeeper initializer + OAuth application
  model for `redirect_uri` validation: exact match vs prefix/subdomain
  wildcards; check native-app loopback handling and custom-scheme
  registration rules.
- **Why scanners miss it:** Config-level property; invisible externally
  without an OAuth client.
- **Feasibility:** 📖 now; runtime 🔒 (needs OAuth app registration).

### 25. `session_id`-in-query SSO login CSRF/fixation — Aiven — ✅
- **Violated invariant:** "The SSO login handshake can't be driven by an
  attacker-supplied session identifier."
- **Evidence in hand:** API authorize endpoint accepts `session_id` as a
  query param.
- **Steps:** (1) Start login, capture the authorize URL template.
  (2) Substitute a fabricated/old `session_id`; observe whether the flow
  binds to it, errors safely, or (worst) authenticates the victim's
  browser into the attacker's session (fixation). All with own sessions
  only.
- **Why scanners miss it:** Login-flow parameter semantics aren't scanned.
- **Feasibility:** ✅ own sessions, no victim involved.

---

## EMAIL / NOTIFICATION INJECTION (no mailbox needed variants)

### 26. Unicode-bidi board/pin names → collaborator UI spoofing — Pinterest — ✅
- **Violated invariant:** "User-controlled names can't visually impersonate
  system UI or other users."
- **Steps:** (1) Create board named with RTL overrides + homoglyphs
  mimicking "Pinterest" or another user. (2) Screenshot how it renders in
  collaborator lists, notifications, and invite dialogs on own account.
  (3) Delete after.
- **Why scanners miss it:** Visual spoofing has no HTTP signature.
- **Feasibility:** ✅.

### 27. Mention/notification flooding as harassment primitive — Pinterest/GitLab — ✅
- **Violated invariant:** "Notification volume per actor is rate-limited."
- **Steps:** (1) On own account/objects only: generate mentions/comments at
  increasing rates; measure where throttling kicks in (or doesn't).
  (2) Document the ceiling — absence of a ceiling is the finding's core
  (harassment/abuse vector, usually accepted as informative/low).
- **Why scanners miss it:** Abuse-rate logic isn't a "vuln" scanners look for.
- **Feasibility:** ✅ keep volume modest on own objects.

---

## RACE / TIME WINDOWS

### 28. Membership-state TOCTOU: approve-then-revoke — GitLab — 📖
- **Violated invariant:** "A revoked membership confers zero residual access,
  including in-flight requests and cached policies."
- **Steps (white-box):** trace access-request approve → member add → revoke
  for cached permission checks (`User#can?` memoization, policy caches);
  look for windows where a revoked user retains access until cache expiry.
- **Why scanners miss it:** Requires code-level cache-lifetime reasoning.
- **Feasibility:** 📖 now; runtime 🔒 (needs two verified accounts).

---

## WHAT UNLOCKS THE 🔒 IDEAS (capability gaps, in priority order)

1. **Raw HTTP with custom headers** — unlocks ideas 10, 12, 15 and all five
   Aiven scope-differential leads. Path: extract the console's bearer token
   via browser-task JS execution (currently forbidden to the task) OR have
   the user paste a minted low-scope app-user token through Secure Vault.
2. **Second synthetic account** — unlocks 11, 24 (partially), 28-runtime,
   Pinterest invite/collaborator ORBAC differential.
3. **GitLab account verification** (email+phone) — unlocks ALL GitLab
   runtime ideas (2, 3, 6, 13, 14, 21, 24, 28).
4. **Research-Gmail mailbox read** — unlocks email-sink ideas 1, 5, 11.
5. **Bugcrowd access** — unlocks OneTrust idea 17.
6. **PayPal developer access** — unlocks idea 20.

## DELIBERATELY EXCLUDED

Tor/dark-web sourcing (refused — criminal-source material poisons any
disclosure), worm/self-propagation (refused), credential attacks,
brute-force, DoS, real-money flows, KYC-gated paths.

---

## Human-Reasoning Operating Loop (installed 2026-09-26)

OBSERVE → WHAT IS SUPPOSED TO HAPPEN? → WHAT ASSUMPTION IS THE SYSTEM MAKING?
→ WHAT IF THAT ASSUMPTION IS WRONG? → GENERATE 10+ HYPOTHESES → RANK → TEST ONE
→ LEARN FROM RESULT → GENERATE NEW HYPOTHESES → REPEAT

Personas applied at every step:

- ARCHITECT — "What does this application believe is trustworthy?"
- ATTACKER — "What assumption could I violate?"
- DEFENDER — "Why might this behavior actually be legitimate?"
- INVESTIGATOR — "What evidence would distinguish those explanations?"
- DEVIL'S ADVOCATE — "How could my current hypothesis be completely wrong?"
- RESEARCHER — "What unusual hypothesis haven't we considered?"

Modeling primitives: users (anonymous / A / B / admin), objects, trust boundaries
(browser→API→DB→third party), state machines (registration, login, payment, password reset).

Contradiction rule: when expected ≠ observed (e.g. GET checks ownership, PATCH checks only
authentication), that contradiction is the finding — investigate it directly.

403/400 diagnosis ladder: A. authz check · B. WAF · C. different backend · D. missing param
· E. session state · F. API version difference — always design the experiment that
distinguishes them before retrying anything.
