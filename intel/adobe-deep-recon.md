# Adobe Bug Bounty — Deep Recon (AI-focus)
**Program:** Adobe Public Bug Bounty on Intigriti
**Program URL (verified via Adobe's own security.txt, 2026-09-26):** https://app.intigriti.com/programs/adobe/adobepublic/detail
**Recon date:** 2026-09-26 (Asia/Calcutta) — policies change without notice; re-verify before testing.
**Method:** Passive only. Public web pages, Intigriti's public program page, Adobe security blogs, Adobe's security.txt, crt.sh certificate transparency, GitHub docs repos. No scanning, no probing, no logins, no traffic beyond loading public pages.

---

## 0. Program history (context)

- Adobe's bounty ran on **HackerOne** for years (VDP since ~2015, paid bounty added later).
- **2026-08-04**: Intigriti announced as new provider; Adobe Security blog confirms.
- **2026-09-01**: Program went **live on Intigriti** as "Adobe Public" (company handle `adobe`, program handle `adobepublic`, managed, public confidentiality).
- **2026 (recent)**: Adobe expanded the program with a dedicated **AI Bonus Tier** — top-tier critical AI findings earn up to **$15,000**. Blog: "Adobe expands bug bounty program to incentivize AI security research" (blog.adobe.com/security).
- Security contact per Adobe's security.txt (fetched 2026-09-26): `psirt@adobe.com`, encryption key at helpx.adobe.com/security/key.html, policy at helpx.adobe.com/security.html/security/policy.ug.html, file expires Jul 30, 2027.

---

## 1. Live policy (read 2026-09-26)

### 1.1 Source status — what is verified vs gated
- ✅ **Verified (public):** the full program page at `https://app.intigriti.com/programs/adobe/adobepublic/detail` renders without login: Introduction, Tier Guidance, and the test-plan attachment listing. The complete domain/asset list was additionally verified from the public Intigriti scope dump (arkadiyt/bounty-targets-data `intigriti_data.json`, crawled ~1 day ago, program entry `company_handle: adobe`, `handle: adobepublic`, `status: open`, `min_bounty: $75`, `max_bounty: $15,000`, `tacRequired: false`, `twoFactorRequired: false`).
- ⚠️ **Login-gated (unverified):** the full bounty table per tier and the **"Adobe Public Policy Test Plan Attachment"** (`Adobe_Bug_Bounty_Test_Plans.docx`, updated 8/28/2026) — the page says product-specific test plans take precedence and testing must follow them. **Read it inside Intigriti before testing anything.**

### 1.2 Bounty range & tiers (verified)
- Overall range: **USD $75 – $15,000** (per program metadata + third-party mirror).
- **Tier 1 — AI Bonus Tier** (explicit quote): *"applies to approved Adobe AI bonus features where the report demonstrates clear AI, agentic, MCP, model, training-data, supply-chain, data exposure, privilege escalation, unauthorized action, or backend security impact."* Covers: AI data exfiltration, unauthorized actions through tool use, cross-account access, privilege escalation, **prompt injection with backend impact**, model/training-data security issues, MCP-related impact, AI-assisted workflow issues. Top-tier critical AI findings: up to **$15,000**.
- **Tier 2 — High-Value Adobe Web, Mobile and Product Assets**: Adobe Commerce, Acrobat Web, Adobe Stock, Firefly, ColdFusion (without CF Admin), Lightroom Web, Photoshop Web, approved mobile apps, open-source/locally-installable products.
- **Tier 3 — Enterprise, Identity and Supporting Product Assets**: Adobe Learning Manager, ColdFusion Administrator, Behance, Express, Portfolio, Fonts, IMS, account services, Commerce web properties.
- ⚠️ Exact per-tier payout numbers (Exceptional/Critical/High/Medium/Low) are **not publicly visible** — login required. $75–$15,000 is the verified envelope.

### 1.3 Explicitly in-scope assets (verified, 40 entries from the live scope dump)

**Tier 1 — AI bonus features (asset type "other", all bounty-eligible):**

| # | Feature asset | Served on (per policy) |
|---|---|---|
| 1 | Acrobat AI Assistant (+ PDF Spaces, Create Presentations, Create Podcast) | `acrobat.adobe.com` |
| 2 | Acrobat PDF Spaces | `acrobat.adobe.com` |
| 3 | Acrobat Create Presentations | `acrobat.adobe.com` |
| 4 | Acrobat Create Podcast | `acrobat.adobe.com` |
| 5 | Adobe Express AI Assistant | `new.express.adobe.com` |
| 6 | Lightroom AI Features (AI Edits + "Edit suggestions" Tech Preview) | `lightroom.adobe.com` |
| 7 | Adobe Firefly AI Features (Image Models, Video Model, Custom Models) | `firefly.adobe.com` |
| 8 | Photoshop AI Assistant | `photoshop.adobe.com` |
| 9 | Adobe Stock AI Studio | `stock.adobe.com` |

Per-feature testing focus (quoted from policy): *"prompt injection leading to sensitive content disclosure, unauthorized access to documents, unauthorized actions, cross-account access, data exfiltration, privilege escalation, or bypass of enforced backend security controls"* — for Firefly additionally *"model or training-data security issues, prompt injection with backend impact, unauthorized actions, and cross-account or cross-tenant access."*

**Tier 2 — Web/mobile:**
- `*.acrobat.adobe.com` (Acrobat Web; auth/authz, document access controls, file handling, session handling, business logic)
- `stock.adobe.com` (+ `contributor.stock.adobe.com`)
- `firefly.adobe.com`
- `*.lightroom.adobe.com` (+ `photos.adobe.io`)
- `photoshop.adobe.com`
- Adobe Commerce / Commerce B2B / Magento Open Source (self-hosted test env; "other" asset)
- Adobe ColdFusion without CF Administrator ("other" asset)
- Mobile: Frame.io (iOS), Adobe Fresco (iOS), Photoshop Express (iOS), Lightroom Video & Photo Editor (iOS+Android), Adobe Scan (iOS+Android), Acrobat Reader (iOS+Android)

**Tier 3 — Identity/enterprise/supporting:**
- `account.magento.com`, `commercemarketplace.adobe.com`, `repo.magento.com`, `magento.com`
- `learningmanagerstage4.adobe.com` (**stage only** — production Learning Manager OOS)
- `net.s2stagehance.com` (Behance staging)
- `new.express.adobe.com` (Express)
- `portfolio.ccpsx.com` (Portfolio)
- `fonts.adobe.com`
- IMS/account cluster: `account.adobe.com`, `ims-na1.adobelogin.com`, `adobeid-na1.services.adobe.com`, `auth.services.adobe.com`, `federatedid-na1.services.adobe.com`
- ColdFusion Administrator ("other" asset)

**Notable explicit exclusions / carve-outs (verified from policy text — these kill hypothesis classes):**
- ❌ `.adobesign.com` (Document Cloud Adobe Sign production) — OOS for Acrobat Web testing.
- ❌ **"Firefly backend API IDORs related to jobs and data are out of scope where IDs are random UUID4 and short-lived."** → plain Firefly job-ID IDOR is explicitly OOS. (Cross-tenant/prompt-injection classes remain Tier 1.)
- ❌ `express.adobe.com` and `express-embed.adobe.com` — OOS (only `new.express.adobe.com` is in).
- ❌ Denial-of-service testing — explicitly OOS (Photoshop Web, Express, Lightroom, IMS).
- ❌ Production Behance (`www.behance.net`), production Portfolio websites, `adobelogin.com` (except listed IMS hosts), additional static-content domains, third-party endpoints loaded by Photoshop Web.
- ❌ Fonts: DRM/licensing bypass findings OOS.
- ❌ Lightroom: Google Photos vulnerabilities, disabled-download share renditions via API, Lightroom Community API liked-content, search-engine-indexed public shares.
- ❌ IMS: Plans/Payment sections of account.adobe.com, non-identity settings, and **"temporarily excluded IMS OAuth vulnerabilities"** (check test plan before OAuth work).
- ❌ General: anything not listed in Domains; testing outside the product-specific test plan (unapproved production/customer environments, unlisted third-party endpoints) is OOS and may void eligibility.
- Researchers must self-sign-up; no credentials provided; free trial for premium features. Attribution header/User-Agent expectations were not publicly visible — check the test plan.

### 1.4 Rules of engagement & disclosure (partially verified)
- Test only approved assets/accounts/environments/roles per the product-specific test plan; product test plans override general guidance.
- Worst-case scenarios the program explicitly invites (verified): RCE, injection (SQL/command/LDAP), SSRF, XSS, privileged CSRF, traversal, auth/session flaws, **IDOR / cross-account access / privilege escalation**, ATO, customer-data access, sensitive file/document/media/asset exposure, misconfig → data exposure, **prompt injection → data disclosure / privesc / unauthorized tool use**, **AI-specific vulns with real backend impact (authz bypass, data exposure, tool-use abuse)**.
- Disclosure norms from Adobe's history: first-to-report, give Adobe reasonable fix time before public disclosure; submit via Intigriti. Safe harbor is listed as "Partial" by a third-party mirror — **unverified detail; treat standard safe-harbor rules as requiring the test plan read.**

---

## 2. Architecture & tech (public docs/dev sources)

### 2.1 Auth model — Adobe IMS (verified from Adobe developer docs)
- Central IdP: **IMS (Identity Management Services)**. Endpoints: `https://ims-na1.adobelogin.com/ims/authorize/v2` (authorization), `/ims/token/v3` (token exchange), legacy `/ims/authorize/v1`, `/ims/token/v1`.
- Flows: OAuth 2.0 authorization code (user apps), client-credentials (server-to-server), deprecated JWT exchange (`/ims/exchange/jwt`).
- Scopes seen in docs: `openid, AdobeID, email, profile, session, read_organizations, additional_info.*, firefly_api, ff_apis, creative_sdk, user_management_sdk`.
- Token shape: `access_token` + `refresh_token` + `id_token`, 24h lifetime (`expires_in: 86399`).
- IMS is itself **in scope** (Tier 3, five listed hosts) — but note the "temporarily excluded IMS OAuth vulnerabilities" carve-out.

### 2.2 Acrobat AI Assistant (verified from Adobe's AI Assistant Security Fact Sheet, Aug 2025, and enterprise security architecture doc)
- Components: AI Assistant chat, Generative Summary, **PDF Spaces** (AI knowledge hubs over files + **links** + text, with collaboration/sharing), **Acrobat Generative AI Service**.
- Data flow: user signs in via IMS → opens doc → app sends auth token to IMS, checks entitlements → document passed to Acrobat Generative AI Service, which **creates a unique session key**, extracts content, **caches content for 12 hours**, sends content to **Azure OpenAI** → overview + suggested questions generated.
- A **Content Filter** sits between the service and the model; **Content Cache** holds extracted doc text for 12h; user content stored beyond cache only on harm/bias reports or feedback.
- Encryption: TLS 1.2+ in transit, AES-256 at rest. Model backend: GPT-4o-class via Azure OpenAI (per press coverage).
- Limits: up to 600-page PDFs, up to 10 files per session, supports PDF/Word/PowerPoint/meeting transcripts; intelligent citations engine links answers to source pages.
- Serving host: `acrobat.adobe.com` (scope) / `*.acrobat.adobe.com` (Tier 2). AI features = Tier 1.

### 2.3 Firefly (verified from Adobe developer docs + SDK READMEs)
- Web app: `firefly.adobe.com` (Tier 2 web; AI features Tier 1). Features: text-to-image, Generative Fill/Expand, Object Composite, Upscale, style reference images, **Custom Models** (train on own assets), Video model, Firefly Boards/Spaces.
- Backend API: `https://firefly-api.adobe.io` (v3, e.g. `POST /v3/images/generate-async`), OAuth client-credentials via IMS with scopes `firefly_api, ff_apis`, `x-api-key` header + Bearer token.
- Job model: **async jobs with presigned-URL outputs**; reference inputs accepted as `upload_id` | pre-signed URL (allow-listed cloud storage) | local path. Outputs include **C2PA Content Credentials** (tamper-evident provenance metadata) automatically.
- Uploads: `firefly_upload_image` → upload id → referenced in generation calls.
- Credits/quota: generative credits meter usage (free tier limited). ❗ Remember: backend API IDORs on jobs/data with random UUID4 + short-lived IDs are **explicitly OOS**.
- `foundry.firefly.adobe.com` (+ `*.foundry.firefly.adobe.com`) exists in CT (DigiCert, current) — "foundry" reads as the model/inference backend. **Not explicitly listed in scope** (only `firefly.adobe.com` is) → treat as **ambiguous**, confirm via test plan before touching.

### 2.4 Express / Lightroom / Photoshop / Stock (verified from scope text + docs)
- Express AI Assistant served on `new.express.adobe.com` (Tier 3 web asset; AI feature Tier 1). Focus per policy: AI-assisted content creation workflows, project/account boundary issues, cross user/account/org boundaries.
- Lightroom Web `*.lightroom.adobe.com` + `photos.adobe.io`: photo access controls, sharing workflows, API authz, metadata exposure. AI features: AI Edits, Edit-suggestions Tech Preview.
- Photoshop Web `photoshop.adobe.com`: asset access, file handling, workflow abuse. DoS prohibited in testing.
- Stock `stock.adobe.com` (+contributor): contributor workflows, asset access, cross-account. AI: Stock AI Studio.
- Sharing/collaboration is a cross-cutting theme: PDF Spaces (collaborate on AI knowledge hubs), Lightroom shares, Express project sharing, Firefly shared generations — all named in Tier-1 focus language ("cross-account", "cross-tenant").

### 2.5 Mobile apps (scope only, no arch detail gathered)
- In scope: Acrobat Reader, Adobe Scan, Lightroom, Photoshop Express, Fresco, Frame.io (iOS; Android where listed). AI features are web-first per the expansion blog; mobile AI coverage is "coming throughout the year" — mobile currently Tier 2.

---

## 3. Third parties & partners (public sources)

| Party | Role | Evidence |
|---|---|---|
| **Microsoft Azure / Azure OpenAI** | Model backend for Acrobat Generative AI Service (document content sent to Azure OpenAI; overview/questions generated there) | Adobe AI Assistant Security Architecture doc (data-flow diagram steps 4–5) |
| **OpenAI (via Azure)** | Underlying LLM family (GPT-4o-class per press) | Computerworld hands-on; Adobe newsroom |
| **DigiCert** | TLS CA for Adobe web properties (all CT certs observed) | crt.sh |
| **Google Trust Services** | TLS CA for some dev hosts (insights-dev.acrobat.adobe.com) | crt.sh |
| **CDN** | Adobe historically uses Akamai; `static.adobesigncdn.com` / `static.adobesigncdnstage.com` appear as SANs on Acrobat certs | crt.sh observations; ⚠️ CDN vendor unverified in this pass |
| **C2PA / Content Authenticity Initiative** | Content Credentials provenance standard embedded in Firefly outputs | Adobe blog (2024 ethical-hackers announcement) |
| **Adobe Stock contributors** | Contributor content pipeline (`contributor.stock.adobe.com`) | scope text |
| WAF/bot mitigation | Not identified in this pass — unverified | — |

---

## 4. Code & repos (public GitHub)

Official orgs (verified via search): **`adobe`**, **`adobeio`**, **`AdobeDocs`**, **`Firefly-Services`**.
Relevant repos:
- `Firefly-Services/firefly-services-sdk-js` — official JS SDK: `@adobe/firefly-apis`, `@adobe/photoshop-apis`, `@adobe/lightroom-apis`, `@adobe/firefly-services-common-apis` (auth). Maps the full Firefly/Photoshop/Lightroom API surface incl. async job endpoints, upload flows, storage-reference shapes (`upload_id` vs pre-signed URL) — useful for understanding request shapes before any dynamic testing.
- `AdobeDocs/firefly-api` — Firefly API docs source.
- `adobeio/Adobe-IMS-OAuth-Playground` — IMS OAuth test utility (auth flow reference).
- `adobedocs/*` — analytics, commerce-webapi, cloudmanager docs (IMS endpoint patterns).
- `api-evangelist/adobe-suite` (+ `providers/`) — third-party catalog of Adobe API surface incl. OpenAPI/Postman collections (unofficial mirror, handy for endpoint inventory).
- `Focus-GTS/firefly-services-mcp` — community MCP server wrapping the Adobe SDKs; documents tool surface (generate/fill/expand/composite/video/upload/job-status) and backend hosts (`firefly-api.adobe.io`, `image.adobe.io`, `ims-na1.adobelogin.com`).
- Developer docs: `developer.adobe.com/firefly-services/`, `developer.adobe.com/express/`, `developer.adobe.com/lightroom/`.

---

## 5. Videos & writeups

- **Adobe MAX / engineering blogs:** no specific MAX security talk on the AI features surfaced in this pass. Adobe's engineering blog (blog.developer.adobe.com) and the 2024 Adobe Blog post "Adobe Collaborates with Ethical Hackers to Build Safer, More Secure AI Tools" are the closest: Adobe explicitly asked researchers to apply the **OWASP Top 10 for LLMs** (prompt injection, sensitive information disclosure, training-data poisoning) to Firefly + Content Credentials. **This is the closest thing to an official AI test playbook from Adobe.**
- **Disclosed Intigriti reports:** program went live 2026-09-01; no public disclosed Adobe-Intigriti reports found in this pass (expected — too new). Adobe's historic HackerOne program kept hacktivity largely private.
- **Public vuln writeups touching Adobe AI:** none found specifically for Acrobat AI Assistant / Firefly prompt-injection in this pass — consistent with the "thinly-hunted" thesis. (Nearby signal: 2026 Adobe Reader zero-day CVE-2026-34621 / prototype-pollution RCE chains were **desktop** products — desktop is currently out of scope; web/mobile only, with desktop AI coverage "coming throughout the year" per Adobe.)
- **Crowd/reference:** hackerone-disclosed-reports mirrors (ajaysenr, gh0stspy) contain no Adobe-AI entries found.

---

## 6. Asset inventory — passive (crt.sh, 2026-09-26)

Queried via `https://crt.sh/?q=%25.<zone>&output=json` (no scanning/probing).

**`%.firefly.adobe.com`** — small zone:
- `firefly.adobe.com` (DigiCert, current to 2027-03) ✅ in scope (Tier 2 web / Tier 1 AI features)
- `foundry.firefly.adobe.com` + `*.foundry.firefly.adobe.com` (DigiCert, current to 2027-01) — likely model/inference backend; ⚠️ **not explicitly in scope** (scope lists only `firefly.adobe.com`) — ambiguous, confirm in test plan.

**`%.acrobat.adobe.com`** — notable names (from CT, deduped):
- `acrobat.adobe.com` ✅ (Tier 1 AI features live here per policy)
- `dev.acrobat.adobe.com`, `stage.acrobat.adobe.com`, `stage-dc.acrobat.adobe.com` (DigiCert SAN cert, current) — stage envs under the `*.acrobat.adobe.com` wildcard (Tier 2)
- `www-stage01.acrobat.adobe.com`, `local-test.acrobat.adobe.com` (likely non-routable; low value)
- `insights-dev.acrobat.adobe.com` (Google-issued, **expired 2026-06**) — dev telemetry host; low value, likely dead
- `dev.wopi.acrobat.adobe.com`, `stage.wopi.acrobat.adobe.com`, `prod.wopi.acrobat.adobe.com` — **WOPI hosts** (Office-online-protocol document collaboration/co-authoring). `prod.wopi.acrobat.adobe.com` sits under the in-scope wildcard — collaboration-token/session surface worth mapping.

**From docs/SDK recon (not CT; mentioned in official/community docs):**
- `firefly-api.adobe.io` — Firefly Services REST backend (v3 async jobs)
- `image.adobe.io` — Photoshop/Lightroom/image API host
- `ims-na1.adobelogin.com` — IMS (in scope, Tier 3)
- `photos.adobe.io` — in scope via Lightroom asset
- `contributor.stock.adobe.com` — in scope via Stock asset

**Full scope recap:** see §1.3 (40 entries verified from the live scope dump; a third-party mirror reports 41 targets — 1-entry delta unverified, likely a counting difference).

---

## 7. Hypothesis seeds (AI-weighted, policy-grounded)

Skipped classes per policy: Firefly backend job/data IDOR where IDs are random UUID4 + short-lived (explicit OOS); any DoS; `express.adobe.com` (use `new.express.adobe.com`); Fonts DRM bypass; Lightroom Google-Photos/community-likes/disabled-download-share vectors; adobesign.com; "temporarily excluded IMS OAuth" items.

**H1 — Indirect prompt injection across the share boundary (Acrobat PDF Spaces / AI Assistant).**
- *Hypothesis:* PDF Spaces ingest attacker-controlled content (files **and links**). An attacker shares a PDF Space / document with a victim; hidden prompt instructions in the shared doc steer the victim's AI Assistant session to disclose the victim's *other* (unshared) document content or take unauthorized actions.
- *Why this target:* Policy's Tier-1 language names exactly "prompt injection leading to sensitive content disclosure, unauthorized access to documents, unauthorized actions"; PDF Spaces explicitly support links + collaboration — the classic indirect-injection trust boundary.
- *Expected observation:* Victim-side AI answer reflects attacker instructions (e.g., quotes content from a document the attacker never had access to, or issues a tool action) when the victim queries the shared Space.
- *Class:* Indirect prompt injection → cross-user data disclosure / unauthorized tool use. **Tier 1.**

**H2 — IDOR on AI conversation/session stores (acrobat.adobe.com).**
- *Hypothesis:* The Generative AI Service mints a unique session key per document session and caches extracted content 12h. Conversation/session endpoints may authorize by session possession only, or use predictable session/conversation IDs.
- *Why:* Document Q&A over private PDFs is the highest-value data in the product; session stores are new code.
- *Expected observation:* With two self-owned accounts, replaying account A's conversation/session identifier under account B's IMS token returns A's questions/answers or cached document extracts.
- *Class:* IDOR / broken object-level authorization. **Tier 1 if it touches AI assets.**

**H3 — Malicious-document / link pipeline abuse (Acrobat AI Assistant + PDF Spaces).**
- *Hypothesis:* Upload path accepts PDF/Word/PowerPoint (and links in Spaces). Crafted documents or link targets may trigger SSRF in link-fetch/thumbnail/summarization fetchers, stored XSS in AI-generated summaries rendered in the web UI, or content-filter bypass yielding disallowed exfiltration.
- *Why:* File→extract→cache→LLM pipeline is new, complex, and explicitly Tier-1 ("AI vulnerabilities with clear security impact"); Spaces fetch remote links server-side.
- *Expected observation:* (a) link-preview/fetch of an attacker-controlled URL from Adobe infra (SSRF signal via collaborator, no exfiltration beyond DNS/HTTP hit); (b) AI-generated summary containing active markup that executes in the acrobat.adobe.com origin; (c) filter bypass producing attacker-chosen verbatim output.
- *Class:* SSRF / stored XSS / AI filter bypass. **Tier 1.**

**H4 — Firefly Custom Models: cross-tenant model/data access + training-data leakage.**
- *Hypothesis:* Custom Models let users train on their own assets. Tenant isolation bugs could let one account list/query/use another account's custom model, or generation outputs may regurgitate training data across tenants.
- *Why:* "Model or training-data security issues" and "cross-account or cross-tenant access" are named Tier-1 targets; custom-model training is the newest Firefly surface.
- *Expected observation:* Account B can invoke or enumerate account A's custom model (via model ID), or B's generations contain A's training imagery.
- *Class:* Cross-tenant access / training-data extraction. **Tier 1.** (Avoid the OOS variant: plain job-ID IDOR with UUID4/short-lived IDs.)

**H5 — Express AI Assistant: share/publish permission confusion (new.express.adobe.com).**
- *Hypothesis:* AI-generated content and projects move through share/publish flows; project/account/org boundary checks may be weaker on AI-generated artifacts than on user-authored ones.
- *Why:* Policy focus: "AI-assisted content creation workflows… misuse of AI functionality that crosses user, account, or organisation boundaries."
- *Expected observation:* A share link or API call exposes AI-generated content (or lets a non-collaborator modify/regenerate it) outside the intended audience; org-restricted AI features reachable cross-org.
- *Class:* Broken access control / permission confusion. **Tier 1.**

**H6 — Lightroom AI edit-job cross-account access (lightroom.adobe.com / photos.adobe.io).**
- *Hypothesis:* AI Edits / Edit-suggestions run as async jobs over user photos; job or rendition endpoints may miss ownership checks.
- *Why:* "Unauthorized access to user content, cross-account data exposure" named for Lightroom AI features; photo libraries are high-sensitivity.
- *Expected observation:* Account B retrieves A's AI-edited renditions or edit-job metadata via job/asset identifiers. (Steer clear of the explicitly OOS vectors: disabled-download share renditions via API, Community likes API, Google Photos.)
- *Class:* IDOR / cross-account data exposure. **Tier 1.**

**H7 — Stock AI Studio: contributor/asset workflow authz (stock.adobe.com).**
- *Hypothesis:* AI Studio generates/modifies stock assets inside contributor workflows; asset, draft, or licensing-state transitions may be manipulable cross-account.
- *Why:* Named focus: "unauthorized access to assets, sensitive data exposure, cross-account access, AI workflow manipulation."
- *Expected observation:* Account B accesses/modifies A's AI Studio drafts or unpublished AI-generated assets; contributor-only states reachable as a buyer account.
- *Class:* IDOR / privilege-boundary bypass. **Tier 1.**

**H8 — Firefly generative-credit/quota bypass (business logic).**
- *Hypothesis:* Generation is metered by credits; client-side or race-condition paths may allow generation beyond quota, or free-tier gates may be bypassable via API parameter manipulation.
- *Why:* Metering on a paid AI product is classic business-logic territory; not excluded by policy (the OOS carve-out is only for job/data IDORs with UUID4+short-lived IDs).
- *Expected observation:* Successful generations after credits are exhausted, or quota counters that don't decrement, using only self-owned accounts.
- *Class:* Business-logic / quota bypass. Likely Tier 2 (web asset) unless framed as AI-feature abuse.

**H9 — IMS-adjacent session/account boundary issues (account.adobe.com cluster).**
- *Hypothesis:* The five IMS hosts (account.adobe.com, ims-na1.adobelogin.com, auth.services.adobe.com, adobeid-na1.services.adobe.com, federatedid-na1.services.adobe.com) handle identity for every product above; session fixation, scope confusion, or cross-service token acceptance could yield account takeover.
- *Why:* Identity is the skeleton key to all AI assets; IMS is explicitly in scope (Tier 3).
- *Expected observation:* Token minted for one service accepted by another's AI endpoints, or scope/redirect_uri manipulation on IMS authorize endpoints.
- *Class:* Auth/session flaw → ATO. **Caveat: "temporarily excluded IMS OAuth vulnerabilities" are OOS — read the test-plan attachment first.**

**H10 — WOPI collaboration token confusion (prod.wopi.acrobat.adobe.com).**
- *Hypothesis:* WOPI endpoints broker document co-authoring between Acrobat and Office-online integrations; WOPI access tokens may be overly broad or the discovery/bootstrapper endpoints may leak document URLs.
- *Why:* Found in CT under the in-scope `*.acrobat.adobe.com` wildcard; collaboration protocols are a known source of token-scope bugs; document URLs are the crown jewels here.
- *Expected observation:* WOPI token issued for one document grants access to another user's document, or unauthenticated WOPI discovery leaks internal endpoints.
- *Class:* Token-scope / access-control failure. Tier 2 (wildcard asset), Tier 1 if it reaches AI document content.

---

## 8. Gaps & follow-ups

1. **Test-plan attachment** (`Adobe_Bug_Bounty_Test_Plans.docx`, 8/28/2026) is login-gated — it contains per-product setup, limitations, and the full out-of-scope lists (incl. the "temporarily excluded IMS OAuth vulnerabilities"). **Must-read before any testing.**
2. Per-tier payout table (Exceptional/Critical/High/Medium/Low) not publicly visible — verify in Intigriti.
3. Scope status of `foundry.firefly.adobe.com` and `firefly-api.adobe.io` (backend API hosts) — confirm in test plan; backend API IDOR carve-out suggests the API is otherwise fair game for other classes.
4. Whether `stage.acrobat.adobe.com` / `dev.acrobat.adobe.com` are valid test targets or staging-only (wildcard covers them, but test plans may restrict).
5. No public disclosed Adobe-Intigriti reports yet (program 25 days old) — re-check hacktivity/Intigriti disclosures periodically.
6. CDN/WAF fingerprinting and mobile-app API mapping left undone (passive scope respected; requires traffic analysis during authorized testing).

*Report written 2026-09-26. Policy verified against the live Intigriti program page and Adobe's security.txt on the same date.*
