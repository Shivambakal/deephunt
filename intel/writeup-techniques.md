# Writeup Technique Playbook

Mined 2026-09-26 from public bug-bounty writeups. Passive research only.
Format per technique: [TECHNIQUE] → [ROOT CAUSE PATTERN] → [HOW TO APPLY TO OUR TARGETS].

Targets in scope for mapping: Pinterest (Bugcrowd, authenticated session live),
Aiven (trial account live), OneTrust staging (pentest-app.onetrust.com,
authenticated testing blocked on Bugcrowd login), FDJ brands (unibet.com,
32red.com, bingo.com, mariacasino.com — manual-only).

---

## T1. Cache poisoning via unkeyed inputs

Source: https://herish.me/blog/cache-poisoning-case-studies-part-1-foundational-attacks/
(Herish — "$100K+ Case Studies Part 1", cases from HackerOne #487, GitHub
$4,850, Shopify $6,300, GitLab #1160407, Cloudflare CDN-wide, Red Hat OG-tag XSS)

[TECHNIQUE] Send a request with an attacker-influenced input the cache key
ignores but the application reflects: `X-Forwarded-Host`, `X-Forwarded-Scheme`,
`Content-Type`, `X-HTTP-Method-Override`, or case-mangled `Host`. If the
response (redirect, OG meta tags, JS file, error page) embeds the input AND is
cached, every subsequent visitor gets the poisoned response — turning reflected
XSS/redirects into stored, mass-impact bugs. Variants: method-override HEAD
→ empty-body DoS on GCP-backed static hosting; OG-tag poisoning amplified via
social embeds; static-file 301 loops.

[ROOT CAUSE PATTERN] Cache key ≠ response inputs. The app trusts proxy headers
/ method overrides; the CDN caches without keying on them. Architectural blind
spot, not a code bug in one endpoint.

[HOW TO APPLY]
- Pinterest: probe `/resource/*` API paths and board/pin pages with
  `X-Forwarded-Host: <own-collaborator>` + cache-buster; inspect `Age`,
  `X-Cache`, `Cache-Control` headers. Check whether 301s from URL variations
  reflect the host. Test secret-board URL + fake static suffix (`?.css`) for
  cache deception (private content cached = high severity).
- Aiven: check cacheability of console GET responses with unkeyed header
  injection; only observe on own responses, use unique cache-busters, never
  poison shared entries.
- OneTrust staging: determine if staging sits behind a CDN; repeat unkeyed-
  header probes on DSR/webform endpoints.
- FDJ brands: many hosts likely share cache layers — test one brand, check
  whether poisoning would cross hosts (observe only, do not persist).
- Safety: always use `?cachebuster=<unique>` so you only ever test YOUR cache
  entry; confirm reflection before claiming anything cacheable.

## T2. React Server Components deserialization RCE (React2Shell, CVE-2025-55182)

Source: https://www.wiz.io/blog/critical-vulnerability-in-react-cve-2025-55182
(Wiz Research — unauthenticated RCE in RSC "Flight" protocol; default
`create-next-app` configs vulnerable; 39% of cloud envs had vulnerable
instances; exploited in the wild Dec 2025 for cred harvesting + cryptomining)

[TECHNIQUE] Fingerprint the frontend stack (Next.js `/_next/` asset paths,
`x-powered-by`, RSC flight markers). If the target runs vulnerable
react-server-dom 19.0.x–19.2.x / Next.js 15.x–16.x App Router, the RSC Flight
endpoint accepts crafted payloads → insecure deserialization → unauth RCE.

[ROOT CAUSE PATTERN] Server trusts a complex serialized client payload
(RSC Flight) and deserializes it into executable logic. Default-on feature,
no developer code needed.

[HOW TO APPLY]
- Fingerprint passively first on all four targets: Aiven console, OneTrust
  staging/my.onetrust.com, Pinterest (historically Django — lower odds), FDJ
  brand frontends. Look for `/_next/static`, RSC `__nextjs__` markers.
- If a target matches: this is a known-CVE check, not novel research — verify
  version, report per program rules. Do NOT fire public RCE exploits without
  explicit target-by-target approval; many programs treat exploit-attempt
  traffic as hostile.
- Fits methodology weakly (patch-gap, not logic flaw) — keep it as a cheap
  fingerprinting step, not the main hunt.

## T3. SAML authentication bypass via XML parser differentials

Source: https://portswigger.net/research/the-fragile-lock (PortSwigger —
full auth bypass in Ruby/PHP SAML via attribute pollution, namespace
confusion, void canonicalization; signature-verification and assertion-
processing use DIFFERENT parsers — REXML vs Nokogiri / libxml2 quirks)

[TECHNIQUE] Where SAML SSO exists: signature validation and assertion
consumption desynchronize when they parse XML differently. Attack classes:
XML Signature Wrapping (inject a second Assertion the verifier ignores but
the app consumes), attribute pollution (`ID` vs `samlp:ID` — namespace-
agnostic getters return different values by attribute order), namespace
confusion (hide the real Signature from one parser), void canonicalization.

[ROOT CAUSE PATTERN] Two components, two parsers, one trust decision.
Incremental patches fail because the architecture is fragile.

[HOW TO APPLY]
- OneTrust: PRIME candidate — B2B platform, likely offers SAML SSO for
  enterprise orgs. Inventory SSO/SAML endpoints on staging; check which
  library parses responses; test for unsigned-assertion acceptance and
  duplicated-Assertion handling with own IdP metadata.
- Aiven: check whether console offers organization SSO/SAML; same inventory.
- Pinterest / FDJ: consumer SSO is OAuth/OIDC, not SAML — low priority.
- Invariant: "the identity in the verified signature must be the identity the
  session is created for — under every parser the stack uses."

## T4. OAuth trust-inversion / dynamic discovery weaponization

Source: https://amlalabs.com/blog/oauth-cve-2025-6514/ (Amla Labs —
CVE-2025-6514: `mcp-remote` asked the MCP server "where do I authenticate?",
server returned a weaponized `authorization_endpoint` → OS command execution;
deeper point: OAuth assumes a known trusted IdP; agents/dynamic clients invert
every assumption)

[TECHNIQUE] Anywhere a client discovers auth endpoints from an untrusted party
(OAuth metadata, `authorization_endpoint` from server, tenant-supplied IdP
URLs), the discovery response is an injection point. Also: tokens/credentials
passed between components without binding to context get replayed out of
scope.

[ROOT CAUSE PATTERN] "Ask the server where to authenticate" — trust placed in
a party the client does not control; bearer tokens divorced from the context
that minted them.

[HOW TO APPLY]
- OneTrust staging: test OAuth tenant/org-group/role parameters — can the
  `tenant`/`org_id` in the authorization request be tampered to mint a token
  valid for another tenant? Invariant: "a token minted for tenant A must never
  authorize tenant B."
- Aiven: probe `/v1/oauth2/token` parameter confusion (it already leaks raw
  PG errors) — client_id/redirect_uri/grant swaps; test token scope creep.
- Pinterest: "Continue with Google" uses a fixed IdP (low discovery risk),
  but test OAuth unlink/relink session semantics — does the Pinterest session
  survive Google disconnect? Are stale tokens still honored?
- FDJ brands: social-login flows — check `redirect_uri` validation strictness
  (exact-match vs prefix) once the Maria account exists.

## T5. Managed-service privilege-escalation chains (SupaPwn pattern)

Source: https://www.hacktron.ai/blog/supapwn (Hacktron AI — chained
supautils hook race → postgres→superuser → host RCE via SUID → orchestration
creds → region-wide tenant takeover on Supabase; plus the Lovable lesson:
AI-built backends ship weak permission models)

[TECHNIQUE] In multi-tenant managed services, hunt the privilege boundary
itself: temporary-elevation hooks (extension install), FDW/dblink cross-
database access, `pg_read_file` / `COPY TO PROGRAM`, exposed orchestration
credentials on hosts. Chain: low-priv DB role → superuser → sandbox escape →
control plane.

[ROOT CAUSE PATTERN] The provider must sometimes elevate tenants (extension
installs, migrations); every elevation hook is a confused-deputy candidate.
Tenant isolation is only as strong as the weakest elevation path.

[HOW TO APPLY]
- Aiven: DIRECT mapping — Aiven IS a managed database provider. From the
  trial account: can a database user's role reach other tenants via
  extensions, foreign data wrappers, file-read functions, or exposed metadata
  endpoints? Invariant: "tenant X's database role must never read tenant Y's
  data, files, or credentials." NOTE: creating a database service needs
  explicit approval (cost/isolation rules) — keep this as a hypothesis until
  cleared; do API/console-layer probing first.
- Lovable corollary: where targets use AI-generated or freshly-shipped
  features (new Pinterest features, new FDJ brand flows), assume the
  permission model is the weakest link and test it first.

## T6. Weak HS256 JWT secrets → token forgery

Source: https://medium.com/@1998satheepu/from-token-to-takeover-exploiting-weak-hs256-secrets-poc-c53afb9a75a0
(INACCESSIBLE — upstream 403. Technique summarized from the well-known
pattern the title describes; the article's specifics could not be verified.)

[TECHNIQUE] If an app signs JWTs with HMAC (alg=HS256) using a short/guessable
secret ("secret", company name, "password123"), crack the secret offline
(hashcat/jwt_tool) against YOUR OWN token, then forge arbitrary tokens —
arbitrary user impersonation, role escalation.

[ROOT CAUSE PATTERN] Symmetric signing with a low-entropy secret; sometimes
combined with alg-confusion (server accepts HS256 when it issued RS256).

[HOW TO APPLY]
- All targets: harvest tokens from OUR OWN sessions only (Pinterest session
  cookies, Aiven API tokens, OneTrust staging tokens when unblocked, FDJ
  session cookies when the account exists). Decode header/payload; if
  alg=HS256, attempt offline cracking of OUR OWN token only.
- If cracked: test whether a forged token (modified sub/role) is accepted.
  Invariant: "a token must be unforgeable without the server secret."
- Also test alg-confusion where RS256 is in play: swap to HS256 using the
  public key as HMAC secret.

## T7. DOM-based XSS via source→sink tracing

Source: https://www.intigriti.com/researchers/blog/hacking-tools/exploiting-dom-based-xss-vulnerabilities
(Intigriti — DOM XSS guide: sources = URL-controllable JS properties;
sinks = innerHTML, eval/Function, location, jQuery .html()/append();
methods = static JS review + runtime interception with DOM Invader;
watch for atob/btoa decoding between source and sink; CSTI in Angular/Vue)

[TECHNIQUE] Map user-controllable DOM sources (query params, location.hash,
postMessage, referrer) to dangerous sinks (innerHTML, outerHTML, eval,
Function(), location=, jQuery .html()). Trace statically through JS bundles,
then confirm at runtime. Encoding layers (base64) between source and sink
hide real cases.

[ROOT CAUSE PATTERN] Client-side rendering trusts URL data; server never sees
the payload, so server-side filters don't apply.

[HOW TO APPLY]
- Pinterest: mine the JS bundles the static agent is already pulling —
  search for `location.hash`/`searchParams` → `innerHTML`/`dangerouslySetInnerHTML`
  flows; prime areas: search/typeahead, rich-pin validator URLs, board names,
  profile fields. Runtime-confirm with DOM Invader-style interception.
- Aiven console: project/service names, user profile fields reflected into
  the SPA — trace source→sink in console JS.
- OneTrust staging: DSR form inputs, workflow names, custom field labels.
- FDJ brands: search boxes, affiliate/tracking params (`?aff=`), game launch
  URLs — classic reflected-DOM-XSS territory.
- This is already half-covered by our JS-mining agents — hand them the
  source/sink keyword list.

## T8. HTTP Anomaly Rank — differential response analysis at scale

Source: https://portswigger.net/research/introducing-http-anomaly-rank
(PortSwigger/James Kettle — scores every response by how anomalous its
attributes are vs the set: status code, word count, etc. weighted by
stability; surfaces tiny consistent discrepancies in noisy responses;
evolved from Backslash Powered Scanner's payload-pair diffing)

[TECHNIQUE] Not a vuln class — a discovery engine. Send payload pairs (e.g.
`"` vs `"` for injection, valid vs tampered IDs for authz), compute per-
response attribute vectors, weight attributes by stability across the set,
rank by anomaly. Finds unknown bug classes by automating "these two
responses are consistently, slightly different."

[ROOT CAUSE PATTERN] Human eyes miss 1-word-count differences across 200
responses; statistical diffing doesn't.

[HOW TO APPLY]
- This upgrades our methodology's "differential behavior" section everywhere:
  Pinterest v3-vs-v5 same-object comparisons, Aiven cross-project IDOR probes
  (own objects), OneTrust tenant-parameter tampering, FDJ endpoint probing.
- Implement a lightweight version in our tooling: for each probe pair,
  record (status, word count, content-length, stable header set) and flag
  consistent deltas. Add to `~/workspace/hacker-agent/` scripts.
- Use it to re-scan existing swarm/response data for missed anomalies.

## T9. Remote MCP server attack surface (tools/resources/prompts)

Source: https://blog.kulkan.com/assessing-the-attack-surface-of-remote-mcp-servers-92d630a0cab0
(Kulkan Security — MCP servers expose tools (command injection — 43% per
Equixly), resources/read with unvalidated URIs → LFI/SSRF, IDOR on user-
bound resources, OAuth discovery flaws; test via MCP Inspector or NCC's
http-mcp-bridge into Burp)

[TECHNIQUE] Enumerate `tools/list`, `resources/list`, `prompts/list`; then:
call tools with unexpected args (injection), call `resources/read` with URIs
NOT in the list (LFI/SSRF if unvalidated), test user-bound resources for
IDOR, attack the OAuth handshake.

[ROOT CAUSE PATTERN] A new protocol re-implements classic web flaws —
unvalidated dispatch targets, unvalidated resource identifiers, ambient
authority.

[HOW TO APPLY]
- Pinterest's ApiResource IS this pattern in web form: the client supplies
  `options.url` (the "tool name") and `options.data` (the "args") to a server
  dispatcher. Test it exactly like an MCP `tools/call`: enumerate legit
  targets, then call with unlisted targets. (Already our #1 lead — this
  writeup validates the approach.)
- OneTrust integrations: any feature where the server fetches a user-supplied
  URL or invokes a user-chosen connector = MCP-resource-read equivalent →
  SSRF test.
- Aiven: API endpoints that take server-side actions with client-supplied
  targets (webhooks, integrations) get the same treatment.
- Forward-looking: if any target ships an AI/MCP endpoint, run the Kulkan
  checklist (Inspector + bridge + Burp).

## T10. List-Unsubscribe → SSRF/XSS gadget

Source: https://security.lauritz-holtmann.de/post/xss-ssrf-list-unsubscribe/
(INACCESSIBLE — fetch timed out. Pattern summarized from the title/general
knowledge; article specifics unverified.)

[TECHNIQUE] One-click List-Unsubscribe (RFC 2369/8058) makes mail clients or
servers fetch an attacker-influenced URL. If the fetch is server-side, it's
an SSRF primitive; if fetched content is reflected (tracking pixels,
redirect chains), it becomes XSS. Test: control the unsubscribe URL (own
mailbox + collaborator), observe what fetches it and with what headers.

[ROOT CAUSE PATTERN] A "safe" convenience feature performs server-side URL
fetching on untrusted input.

[HOW TO APPLY]
- OneTrust: highest irony value — a consent/privacy platform lives on email
  workflows. Probe DSR/notification email unsubscribe + webhook URLs for
  server-side fetching.
- Pinterest: account email preferences → unsubscribe links; check whether
  one-click triggers server fetch of attacker URL.
- Aiven: notification/billing emails; FDJ brands: marketing emails (heavy
  email users).
- Invariant: "unsubscribing must never cause the server to fetch an
  arbitrary URL." Test with own collaborator endpoint; observe only.

---

## Prioritization against our methodology

Highest expected value for authorization / state-machine / business-logic
hunting (our core methodology), ranked:

1. **T9 (dispatcher confusion)** — live on Pinterest now (ApiResource).
2. **T1 (cache poisoning)** — architectural, high impact, fits our
   differential testing; cheap to probe safely with cache-busters.
3. **T4 (OAuth tenant confusion)** — fits OneTrust staging exactly; also
   Aiven token endpoint.
4. **T3 (SAML parser differentials)** — if OneTrust/Aiven expose SAML, this
   is a critical-class hunt.
5. **T7 (DOM XSS source→sink)** — feeds directly off the JS-mining agents
   already running.
6. **T6 (JWT secret forgery)** — cheap offline test on our own tokens.
7. **T8 (anomaly ranking)** — force-multiplier for all differential work;
   implement in tooling.
8. **T5 (tenant-escape chains)** — Aiven-specific; needs service-creation
   approval first.
9. **T10 (unsubscribe SSRF)** — cheap probe wherever email flows exist.
10. **T2 (React2Shell)** — passive fingerprint only; patch-gap, not logic.

## Gaps

- Medium HS256 article: upstream 403, could not read. T6 above is the
  generic pattern, not the article's specifics.
- List-Unsubscribe article: fetch timed out, not retried per policy. T10 is
  the generic pattern, not the article's specifics.
- PortSwigger Fragile Lock: only the first ~277 of 452 lines were returned;
  the Void Canonicalization / Golden SAML sections were partially captured —
  enough for the technique summary, but the full exploit construction details
  were not reviewed.
