# Past attacks worth studying — patterns that keep paying

Not CVEs. These are *bounty shapes* — vulnerability patterns that hunters keep
finding in the wild because the underlying engineering mistake repeats across
companies. DEEPHUNT's hypothesizer should reach for these first when the
funnel shows matching signals.

## Authorization (the #1 paid class, year after year)
- **BOLA on sequential IDs** — invoice/order/document IDs that increment.
  Hunters routinely find these on new API versions (v2/v3) while v1 was fixed.
  Lesson: always test the newest API surface, not the documented one.
- **IDOR via "shared link" features** — share links that are just
  `?token=<short>` or sequential; link enumeration or token reuse after revoke.
- **Tenant isolation failures in multi-tenant SaaS** — `org_id` from the JWT
  trusted instead of the path; switching the header/param reads another tenant.
- **GraphQL field-level authz** — endpoint protected, individual fields not.
  Introspection disabled but error messages leak the schema.

## Business logic (the human-only class — scanners never find these)
- **Coupon/credit races** — parallel redemption requests; the classic is 5-10
  requests, not floods. Ledger math proves it.
- **Negative quantity / price tampering** — cart math trusted from the client.
- **Workflow skipping** — calling step-3 APIs without step 1-2 (KYC, checkout,
  onboarding wizards gate in UI only).
- **Email-change TOCTOU** — change email, verify the new one, the account's
  identity flips with weak re-auth.

## AI/LLM (the new Tier-1)
- **Indirect prompt injection via shared/collaborative content** — the attacker's
  instructions ride inside content the victim's AI reads. 2024-2026 bounty
  programs started paying Tier-1 for this with data-disclosure impact.
- **Custom-instruction channels** — products that let one user define assistant
  behavior for other users (custom GPTs, shared assistants, space instructions).
  The instruction channel IS the injection channel — no document needed.
- **AI tool/function abuse** — assistants with email/calendar/file tools acting
  on injected instructions in the victim's session.

## SSRF / cloud
- **URL-fetch features** (webhooks, avatar-by-URL, file import, link preview)
  remain the most reliable SSRF source. Parser differentials beat blocklists.
- **Cloud metadata** is increasingly excluded by programs — prove with an
  owned collaborator + internal 403-vs-timeout oracle instead.

## Subdomain takeover
- Dangling CNAMEs to deprovisioned Heroku/S3/Azure/Github Pages. The check is
  fully passive (DNS + fingerprint); claiming needs program permission.

## Secrets in client code
- JS bundles shipping `sk_live`, Firebase configs, Algolia keys, Mapbox tokens.
  Validate by type, never use. High signal-to-effort ratio.

## Cache / CDN
- Cache poisoning via unkeyed inputs (UTM params, `X-Forwarded-Host` reflected
  into cached pages, `.css` suffix on dynamic routes). Two-session proof.

## Mobile/API leftovers
- Old API versions (`/api/v1`) left running with weaker authz than v2.
- Debug endpoints (`/debug`, `/actuator`, `/console`) exposed in prod builds.
- Mass assignment: `{"role":"admin"}` smuggled into profile updates.

## The meta-lesson
Vendors fix the *reported instance*, not the *class*. The same bug reappears in:
new API versions, new products (PDF Spaces vs old Acrobat sharing), new
platforms (mobile vs web), and acquisitions. Hunt the class, not the instance.
