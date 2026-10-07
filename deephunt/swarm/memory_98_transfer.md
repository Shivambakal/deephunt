# Transfer Map — Agent #98 (cross-target transfer researcher)
Date: 2026-09-27. Analysis only — nothing tested.

## Method
- Source: hyp_known.jsonl (~55 hypotheses, roles 46–65), hyp_novel.jsonl (~35 hypotheses, roles 66–79), WORLD_MODEL.md, plus target profiles `anthropic.yaml`, `shopify.yaml`, `yahoo.yaml`.
- "Strong" = confidence medium or higher (28 hypotheses). Low-confidence items are grouped separately as pattern-only notes.
- Targets: **Anthropic** (HackerOne; active at reasonable rates; nuclei ≤20 high/critical only; mandatory `@wearehackerone.com` test accounts + `X-HackerOne-Handle` header; model-safety/jailbreaks out; manual PoC required), **Shopify** (HackerOne; open-source tools only, NO commercial scanners; ONLY own test shops — never merchant storefronts; nuclei ≤20), **Yahoo** (HackerOne; `*.yahoo.com`, `*.aol.com`, `*.techcrunch.com`; reasonable rates; owned accounts/data only).

---

## Strong hypotheses — transfer verdicts

| # | Hypothesis | Conf | Verdict | Transfers to |
|---|-----------|------|---------|--------------|
| 47 | LDAP login username → filter injection (login semantics change) | med | **Kiteworks-specific** (LDAP/AD login filter integration) | — (other targets use OAuth/email auth, no directory filter) |
| 52a | MFT "import from URL" → server-side fetch (SSRF) | med | **Transfers** | A (console/API import, SSRF is in-class), S (app-proxy SSRF — already a profile seed; own test shop only), Y (mail/newsletter link unfurling, attachment URL fetch) |
| 52b | EPG fetches remote content from inbound email (SSRF) | med | **Mostly KW-specific**, partial transfer | Y (Yahoo Mail inbound-mail processing → server-side fetch/preview is the analog; consumer-mail rules apply — owned accounts only) |
| 53 H1 | Version-overwrite IDOR via initiateUpload (role vs object check) | med | KW endpoint; **pattern transfers** | A (console org/project scoping vs direct object API), S (files/metafields replace in own test shop), Y (shared-folder/attachment replace flows) |
| 53 H2 | Viewer-role download bypass via direct REST content fetch | med | KW endpoint; **pattern transfers** | A (org role vs direct API object access — matches tenant-boundary seed), S (collaborator role vs direct admin API ID), Y (shared mail-drive objects) |
| 53 H3 | Activity-log / mail Track report IDOR via ID swap | med | KW endpoint; **pattern transfers** | A (console audit/activity per org+project), S (shop activity log per shop), Y (account activity surfaces) |
| 51 | CSRF via multipart upload endpoints skipping token validation | med | **Transfers (generic)** | A (console uploads/MCP), S (app upload endpoints in own test shop), Y (mail compose/attachment upload). Verify SameSite + custom-header requirements first on each target. |
| 57 H1 | roleId on folder member-add not clamped to inviter privilege | med | KW endpoint; **pattern transfers** | A (org member invite role — does invitee role exceed inviter's?), S (staff/collaborator role assignment in own test shop) |
| 61 | Content-Type sniffing mismatch on uploaded previews/download | med | **Transfers strongly** | Y (mail attachment inline rendering — historically rich class), S (Files/CDN serving in own test shop), A (file/artifact preview in claude.ai/console) |
| 64 H64-1 | PHP object injection via SimpleSAMLphp session handling | med | **Kiteworks-specific** (stack signal) | — |
| 65 | SAML RelayState open redirect via SimpleSAMLphp SP | med | KW endpoint; **pattern transfers** | Y (**strong**: Yahoo OAuth login flows explicitly seeded for open-redirect/state weaknesses), A (console/API OAuth — redirect/state weaknesses seeded), S (partner OAuth install flow — confused redirect_uri already a seed) |
| 63 | XXE via SAML IdP metadata XML import (admin SSO config) | med | **Kiteworks-specific** (SAML admin flow) | — |
| 50 | desanitize() decode-then-render stored DOM-XSS via tenant config | med | **Kiteworks-specific** (code-level finding) | — (pattern "config-driven DOM sink" noted for A console branding, low priority) |
| 54 BOLA-1 | /rest/comments/{id} skips parent-file ACL | med | KW endpoint; **pattern transfers** | A, S, Y — generic BOLA: nested-resource endpoints that check auth but not parent-object ACL (comments, versions, members) |
| 54 BOLA-2 | File member role update reachable by non-owner members | med | KW endpoint; **pattern transfers** | A (org/project member role update by non-admin), S (staff role update in own test shop) |
| 68 | SAML attribute→LDAP attribute role-mapping conflict (web UI vs API) | med | KW-specific (dual LDAP+SAML); **pattern transfers** | A (**moderate**: enterprise SSO + SCIM attribute mapping on console orgs — do the two sources ever disagree across UI vs API token evaluation?) |
| 70 | MCP localhost:9999 OAuth callback interception (shared host) | med | **Transfers to Anthropic strongly** | A (**strong**: MCP servers + Claude Desktop Extensions explicitly in scope; Anthropic owns the MCP ecosystem — PKCE/state/exact-redirect-URI on MCP OAuth flows is a prime target). S, Y: N/A (no MCP surface) |
| 66 | Expired/download-exhausted link still serves via alternate path | med | **Pattern transfers** | A (shared conversation/artifact links — expiry semantics per path), S (share/discount links in own test shop), Y (mail share links) |
| 66 | Approval-chain step-skipping (out-of-order approval) | med | **Mostly KW-specific** (MFT approval workflows) | Pattern ("validates actor-is-approver, not current-step") is worth one probe each on A/S multi-step flows if found; low priority |
| 73 | Versioned content replacement inherits prior ICAP verdict | med | **Kiteworks-specific** (ICAP delegation) | — |
| 73 | Share-link authorization snapshot survives LDAP role revocation | med | KW mechanism; **pattern transfers as "deprovisioning vs live tokens"** | A (**moderate**: does SSO/SCIM deprovisioning kill console API keys and sessions immediately?), S (staff deactivation vs app/personal tokens in own test shop) |
| 69 | LDAP filter injection → multi-entry return, app binds first match | med | **Kiteworks-specific** (LDAP) | — |
| 75 | Trusted-domain credential harvesting via Secure Data Forms | med | **Mostly KW-specific** (public form publishing) | S (weak: contact forms on own test shop — phishing-adjacent, handle with care); A/Y: no form-builder surface |
| 76 H-PRCHAIN-1 | Self-edit attribute + profile mapping rule = auto-promotion | med | KW mechanism; **pattern transfers** | A (**moderate**: SCIM/SAML attribute-driven role mapping fed by self-editable profile fields) |
| 76 H-PRCHAIN-2 / 77 | SSO JIT / LDAP sync provisioning bypasses admin-strip guard | med | KW endpoints; **pattern transfers** | A (**moderate**: SSO JIT provisioning of org members with admin-role claims — does JIT apply the same strip as the interactive path?), S (collaborator/app install role grants vs documented guards) |
| 74 | Legacy HMAC-SHA1 "Signature Authentication" still mints API tokens | med | **Kiteworks-specific** (Accellion legacy) | — |
| 79 | Delegated admin roles can alter/purge audit events | med | **Pattern transfers** | A (**moderate**: console audit-log immutability under delegated org roles), S (shop activity-log immutability for staff roles) |

**Tally:** 10 Kiteworks-only (47 LDAP, 64-1 SimpleSAMLphp, 63 XXE-SAML, 50 desanitize, 73 ICAP-verdict, 69 LDAP-first-match, 74 legacy-auth; plus KW-endpoint versions of 52b/66-step-skip/75 largely KW-bound). 18 transferable in full or as patterns.

## Per-target opportunity list (top transfers)

**Anthropic — highest transfer value**
1. MCP OAuth localhost-callback interception (#70) — directly in scope (MCP servers, Claude Desktop Extensions); test PKCE + state binding + exact redirect-URI validation.
2. Deprovisioning vs live tokens (#73 pattern) — SSO/SCIM member removal vs API-key/session survival.
3. Tenant-boundary IDORs (#53 H2/H3, #54 BOLA patterns) — org/project scoping on api.anthropic.com / console.anthropic.com; already seeded in the profile.
4. OAuth redirect/state weaknesses (#65 pattern) — lesser-used console/API endpoints.
5. Dual identity-source role-mapping conflict (#68 pattern) and JIT admin-strip bypass (#76/#77 pattern) — enterprise SSO/SCIM org provisioning paths.
6. Audit-log immutability under delegated roles (#79 pattern).
Rules to honor: `X-HackerOne-Handle` header on all traffic, `@wearehackerone.com` test accounts, reasonable rates, manual PoC before any report, no model-safety angles.

**Shopify — constrained but real**
1. Import-from-URL / app-proxy SSRF (#52a pattern) — own test shop only.
2. Content-Type sniffing on Files/CDN previews (#61).
3. Role-clamping gaps (#57 H1, #54 BOLA-2 patterns) — staff/collaborator role assignment and member updates in own test shop.
4. OAuth install-flow confused redirect (#65 pattern) — already seeded.
5. Deprovisioning vs tokens (#73 pattern) — staff deactivation vs surviving tokens.
Rules to honor: ONLY own test shops, never merchant storefronts; open-source tools only (no commercial scanners); nuclei ≤20.

**Yahoo — best for classic web classes**
1. OAuth login open-redirect/state (#65 pattern) — explicitly seeded in profile; test lesser-used properties.
2. Content-Type sniffing on mail attachment inline rendering (#61) — strongest classic class here.
3. Inbound-mail server-side fetch (#52b pattern) — URL unfurling/preview of inbound mail content.
4. CSRF on mail compose/upload flows (#51).
5. Expired-link alternate-path serving (#66 pattern) — share-link expiry per retrieval path.
Rules to honor: `*.yahoo.com` / `*.aol.com` / `*.techcrunch.com` only, reasonable rates, owned accounts/data.

## Low-confidence long tail — pattern-only notes (not strong, but cheap to keep)
SQLi sort/order_by and search-builder patterns (#46) → Shopify GraphQL Admin (connection-layer field exposure); stored-XSS filenames/comments/display-names (#48) → Yahoo Mail attachments and Shopify product/blog content; OAuth m=1 mobile-variant auth bypass (#58) → Yahoo OAuth variants; JWT alg-confusion (#60) → Anthropic API token validation (check JWT vs opaque first); login `?next=` open redirect (#65) → Yahoo (seeded); XXE in docx/XFA preview (#63) → Yahoo Mail preview pipeline; deserialization in import endpoints (#64) → form/workflow imports generally. These are leads, not claims — confidence is low across the board.

## Memory note for future runs
Cross-target transfer works best for **protocol/feature-class patterns** (OAuth redirect handling, deprovisioning-vs-tokens, nested-resource BOLA, content-type sniffing, approval-step validation) and poorly for **integration-specific** hypotheses (LDAP filters, EPG/ICAP, SimpleSAMLphp, Accellion legacy). When Kiteworks hypotheses reference LDAP/SSO/ICAP/MCP, the Anthropic translation is: SSO↔SCIM attribute mapping, MCP OAuth flows, API-key lifecycle.

## Summary
- 10 of 28 strong Kiteworks hypotheses are Kiteworks-specific (LDAP/SSO/ICAP/legacy-stack bound); 18 transfer in full or as reusable patterns.
- Anthropic has the richest transfers: MCP OAuth interception, deprovisioning-vs-token survival, tenant-boundary IDOR/BOLA, and SSO/SCIM role-mapping conflicts — all inside its stated vuln classes and OAuth/MCP scope.
- Yahoo is the best target for the classic web classes (OAuth open-redirect/state, mail attachment content-sniffing, inbound-mail SSRF); Shopify transfers are real but tightly bounded by the own-test-shop-only and no-commercial-scanner rules.
