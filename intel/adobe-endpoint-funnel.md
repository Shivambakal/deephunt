# Adobe Acrobat — Passive Endpoint Funnel (AI Surface: AI Assistant + PDF Spaces)

**Date:** 2026-09-26
**Scope (assigned):** `acrobat.adobe.com` and `*.acrobat.adobe.com` only. Features: Acrobat AI Assistant and PDF Spaces.
**Method:** public-only — crt.sh, public Adobe docs (security fact sheet, admin help, solution guide), unofficial open-source generated client. No scanning, fuzzing, auth, or form submission performed.
**Status of `acrobat.adobe.com` fetch:** the live site returned only "Something went wrong / We're sorry for the inconvenience." — no script-bundle URLs captured, no JS bundle analysis completed. A Wayback Machine fetch was unavailable after retries and was not retried further. Treat JS-bundle-derived claims as absent.

---

## 1. Host inventory (passive, crt.sh)

Confirmed certificate hostnames for the in-scope zone:

- `acrobat.adobe.com` (production web app — the AI Assistant / PDF Spaces client)
- `www-stage01.acrobat.adobe.com`
- `stage.acrobat.adobe.com`
- `stage-dc.acrobat.adobe.com`
- `dev.acrobat.adobe.com`
- `local-test.acrobat.adobe.com`
- `insights-dev.acrobat.adobe.com` (certificate expired June 2026 — recent dev presence)
- `dev.wopi.acrobat.adobe.com`
- `stage.wopi.acrobat.adobe.com`
- `prod.wopi.acrobat.adobe.com`

**Note — adjacent but OUT OF the delegated hostname scope (architecture evidence only until the Intigriti test plan confirms eligibility):**

- `dc-api-v2.adobe.io` — Adobe's Document Cloud API v2; the Acrobat Web client is built from its private discovery document (confirmed by the codegen pipeline below). Route patterns here are the most concrete endpoint evidence available, but they are NOT `*.acrobat.adobe.com`.
- `dc-api-v2.adobecontent.io` — direct download/rendition host.
- `taggedpdf.adobe.io`, `sensei.adobe.io` — tag/Sensei predict services.

The codegen tooling that produced the client below refreshes its schemas "from the live API, needs IMS_SID" — i.e., Adobe's own live discovery document is the source of these routes, but I did **not** re-fetch it (that would require an authenticated session). The generated snapshot was accessed 2026-09-26 via the public repo; its freshness against the live API is unverified.

---

## 2. Endpoint inventory (routes confirmed in the public generated client snapshot)

Pattern note: all paths carry a `{expiry}` segment — an expiry timestamp prefix that scopes the discovery schema version per session.

### Discovery
- `GET https://dc-api-v2.adobe.io/discovery`
- `GET https://dc-api-v2.adobe.io/{expiry}/discovery/services`
- `GET https://dc-api-v2.adobe.io/{expiry}/discovery/resources/assets/createpdf/options`
- `GET https://dc-api-v2.adobe.io/{expiry}/discovery/resources/assets/exportpdf/options`
- `GET https://dc-api-v2.adobe.io/{expiry}/discovery/resources/assets/source/options`

### Assets (host: `dc-api-v2.adobe.io`, plus adjacent hosts noted)
Upload / authorize:
- `PUT /{expiry}/assets/authorize/client/verb` — client authorization handshake
- `POST /{expiry}/assets/block_upload/initialize`
- dynamic `asset_block_upload_extend_uri` and `asset_block_upload_finalize_uri` (returned by initialize)
- `POST /{expiry}/assets` (multipart file upload)
- `PUT /{expiry}/assets{?asset_uri}` (multipart file update of existing asset)

Asset operations (all `POST /{expiry}/assets?operation=<name>`, JSON body, async → job):
- `createpdf`, `createpdf_from_html`, `createppt_from_html`, `createexpress_from_html`
- `exportpdf`, `exportnotedoc`
- `pdf_actions`, `redactpdf`, `splitpdf`, `import_`
- `tag` via `POST https://taggedpdf.adobe.io/{expiry}/assets?operation=tag{&format,async,qualify,client_version}` with `format`: `instance_data` | `fully_tagged_pdf`
- `tag_sensei` via `POST https://sensei.adobe.io/services/v1/predict` (multipart file)

Metadata:
- `GET {asset_uri}/metadata` (basic), `GET {asset_uri}/metadata/{fields}`
  - readable fields: `uri name asset_id parent_uri parent_id size type md5_digest page_count created modified last_access last_pagenum source created_by_client favorite starred tags custom_tags sign`
- `PATCH {asset_uri}/metadata/{fields}` — fields limited to `tags`, `custom_tags`
- `PUT {asset_uri}/metadata/{fields}` — fields limited to `last_access`, `last_pagenum`, `favorite`, `starred`, `sign`
- `DELETE {asset_uri}/metadata/{fields}` — observed field: `last_access`
- `DELETE {asset_uri}`

Download / rendition (the highest-signal cluster):
- `GET {asset_uri}/uri/download?make_ticket=&make_direct_storage_uri=` — **mint either a shareable ticket or a direct storage URI for an asset**
- `GET {asset_rendition_uri}?format=&fallback=` — `format`: `ftpdf` | `jcos` | `owp`; `fallback`: `original` | `none`
- `GET {asset_uri}/uri/rendition?make_ticket=&type=` — `type`: `paged` | `document`; ticket-minted rendition URI
- `GET {asset_uri}/document/rendition/status`
- `GET {asset_download_uri}` (dynamic, returned by server)
- `POST {export_uri}` (dynamic, returned by server)
- `GET {asset_rendition_uri}{&format,size,wait,page,markup,processing_hint,download,rendition_class}` — page-level rendition; `format`: `png` | `jpg`; `processing_hint`: `speed_over_quality` | `quality_over_speed`; `markup`: bool; `rendition_class`: string
- `GET https://dc-api-v2.adobecontent.io/{expiry}/assets/download/{asset_id}/rendition{?format,size,wait,page,markup,processing_hint,download,rendition_class}` — **direct rendition fetch keyed only by `asset_id`**
- `GET {asset_upload_status_monitor_uri}`
- `POST https://dc-api-v2.adobe.io/{expiry}/assets/zip/uri/download` (JSON body `zip_download_params_v1` → zip download URI), `GET {zip_download_uri}`

### Folders
- `POST /{expiry}/folders`, `DELETE {folder_uri}`
- `GET /{expiry}/folders/root`, `GET /{expiry}/folders/system_folders`
- `GET {folder_uri}/contents{?order_by,sort_order,page_size,metadata,include_composite_types}` — `metadata`: `min` | `basic`; `include_composite_types`: `horizon`; page_size default 5000
- `GET {next_page_uri}` (pagination continuation URI, server-issued)
- `GET {folder_uri}/breadcrumbs`
- `GET/PATCH/PUT {folder_uri}/metadata{/{fields}}` — fields: `uri name folder_id parent_uri parent_id created modified source favorite starred tags custom_tags`

### Jobs
- `GET {job_uri}/status` — async-operation status for any asset operation

### Cloud connectors (third-party storage ingress)
- `POST https://dc-api-v2.adobe.io/{expiry}/{cloud_id}/connector/link` — `cloud_id`: `msft` | `teams` | `gdrive` | `box` | `dropbox`
- `GET .../{cloud_id}/connector/list`, `DELETE .../{cloud_id}/connector/{connector_id}`

### Users / system / feedback
- User-information and discovery routes exist in the generated client (per its README); individual method signatures were not enumerated — marked unverified, low priority for the AI surface.

---

## 3. Architecture evidence (public Adobe documents, accessed 2026-09-26)

From Adobe's Acrobat AI Assistant security fact sheet (Aug 2025) and Admin Console help article:

1. **Auth/session model:** IMS authenticates user + entitlements → Acrobat Generative AI Service creates a **unique session key**; extracted content is cached for **12 hours**; cache lives on the same servers as the GenAI service; session data is keyed on **User ID + Doc ID** (admin article).
2. **Cache deletion exceptions:** content auto-deletes after 12h **except in cases of feedback submission or sharing documents** (admin article) — cached content can outlive the 12h window when a share is involved.
3. **Web chat persistence:** desktop/mobile chat history stays on-device; **Acrobat web chat history is stored in Adobe cloud storage**.
4. **PDF Spaces ingestion:** PDFs, other files, written text, **and webpage links**. URL sources are converted into PDFs that **do not retain original document-level permissions**.
5. **Spaces sharing model:** owners can share with named users, an organization, or **anyone through a public link — public-link sharing is ON by default** unless an admin disables it. Recipients authenticate for private/domain-restricted shares. Recipients can view/download generated insights, source documents, and owner notes (subject to PDF Services entitlement). **Each recipient starts a new private chat, stored in their own cloud location.**
6. **Custom assistants:** predefined assistants (Analyst, Instructor, Entertainer) plus owner-created **custom assistants with workflow-specific instructions**. Per the fact sheet: **"Owner-created custom AI Assistant instructions apply to all subsequent recipient chats."** Per the admin article, copies of "goals, custom agents, and notes" are saved in Adobe cloud storage.
7. **Copy / revoke:** "Copy PDF Space" copies **source documents and notes, not owner chat history**. Revoking sharing is described as making the Space "immediately inaccessible."
8. **Permission-model discrepancy:** the security fact sheet describes sharing as "View Only" for all share types; the PDF Spaces solution guide describes richer roles — "Sharing for review" (recipients chat, comment, **add files**) and "Contributors" (can **add, update, or delete project content**, including files added by owners and notes they create), plus public/private spaces. The guide may be newer; treat the true role model as unverified.

---

## 4. The funnel

### 4a. Inventory (raw, ~60+ route/param surface points)
All routes in §2 plus hostnames in §1 plus behavioral parameters (`make_ticket`, `make_direct_storage_uri`, `format`, `fallback`, `operation`, `expiry`, `processing_hint`, `rendition_class`, `include_composite_types=horizon`).

### 4b. Interesting (auth · sharing · AI · upload · URL-fetch · chat/history · session · copy/revoke)
- `{expiry}` path prefix on every API call — session-scoped schema version.
- `make_ticket` / `make_direct_storage_uri` on `uri/download` and `uri/rendition` — two distinct download-capability mechanisms.
- Direct `GET .../assets/download/{asset_id}/rendition` on `adobecontent.io` keyed only by `asset_id`.
- Server-issued dynamic URIs (`asset_uri`, `asset_rendition_uri`, `asset_download_uri`, `export_uri`, `next_page_uri`, block-upload extend/finalize) — URI-as-capability pattern.
- URL-source ingestion (`createpdf_from_html`, `createppt_from_html`) + "URL→PDF drops original document-level permissions".
- 12h GenAI content cache keyed on User ID + Doc ID, with share/feedback exceptions.
- Owner custom-assistant instructions propagate to every recipient chat.
- Public-link sharing ON by default; recipients can download insights, sources, owner notes.
- Copy-Space copies sources+notes but not owner chat history; revoke claimed to be immediate.

### 4c. Security-sensitive (cross-account access · public-link ACLs · download tickets · dynamic asset URIs · custom-assistant propagation · cloud chat storage)
1. **Ticket/direct-storage URI lifecycle vs. Space revoke** — do minted `make_ticket`/`make_direct_storage_uri` URLs survive unshare, and do they require auth at redemption?
2. **Dynamic `asset_uri` as bearer vs. server-side ownership check** — `DELETE`/`GET` on arbitrary `asset_uri` values, including another account's URIs, across metadata/rendition/download sub-resources.
3. **Custom-assistant instruction propagation across trust boundary** — owner instructions execute inside the recipient's private chat session (per fact sheet); a malicious owner can ship instructions to a victim's session.
4. **Public-link default-ON + generated insights** — AI-generated summaries/attributions derived from source docs inherit the link's viewability; check whether insights reference content the link-recipient couldn't otherwise see (e.g., from later-added or removed documents).
5. **12h cache keyed on (User ID, Doc ID) across share/copy transitions** — a Doc ID reused across owner/recipient contexts (shared Space, copied Space) may collide cache entries or leak cached prompts/answers.
6. **URL→PDF permission stripping** — converted PDFs lose original document-level permissions; a shared Space's AI can answer from content the URL's own access controls restricted.
7. **`asset_id`-keyed direct rendition on `adobecontent.io`** — page images served by asset ID alone; test whether the CDN/edge layer enforces the same entitlement as the API layer.
8. **Cloud-stored web chat history** — Acrobat web persists request+response in Adobe cloud; check chat-history retrieval endpoints for cross-user / cross-space scoping (unverified endpoints — needs JS bundle work).

### 4d. Unusual behaviors (product-assumption violations)
- U1. URL sources become PDFs that **lose** the source's document-level permissions — ingestion actively downgrades access control.
- U2. Public-link sharing is **ON by default** for PDF Spaces; security posture depends on an admin opt-out.
- U3. Owner's custom assistant applies to **all** recipient chats, including "private" ones — "private" means not visible to the owner, not isolated from owner influence.
- U4. Copy Space copies source documents and notes but **excludes** owner chat history — an asymmetric copy that changes what the new Space's AI has seen.
- U5. Cached GenAI content normally dies in 12h, **except when the document was shared or feedback was given** — sharing extends server-side data retention.
- U6. Sharing is described as "View Only" in one doc and as contributor-capable (add/update/delete) in another — the effective permission model is ambiguous.
- U7. WOPI hostnames (`dev/stage/prod.wopi.acrobat.adobe.com`) exist in certs — Microsoft WOPI token protocol wired into the Acrobat zone; WOPI token↔document binding is a classic confused-deputy seam (routes unverified).

---

## 5. Hypothesis seeds (new, grounded in the above)

**SH1 — Minted download tickets outlive Space revoke.**
*Grounded in:* `GET {asset_uri}/uri/download?make_ticket=` + `uri/rendition?make_ticket=` and the fact sheet's "immediately inaccessible" revoke claim.
*Idea:* A recipient (or an attacker with a leaked link) mints a download ticket/rendition ticket while the Space/link is active; after the owner revokes, the ticket URL still redeems the document or its AI rendition because revocation only flips the Space ACL, not issued bearer tickets. Test: self-owned two-account Space, mint ticket, revoke, re-request ticket URL, observe status/body. Failure: ticket carries expiry/signature bound to the share grant and 403s after revoke.

**SH2 — Direct-storage URIs (`make_direct_storage_uri`) are unauthenticated bearer URLs.**
*Grounded in:* same endpoint's `make_direct_storage_uri` flag; the name implies a raw storage URL (e.g., signed cloud-storage URL).
*Idea:* Direct-storage URIs redeem without IMS auth and may have long TTLs or overly broad scope (whole asset vs. single object, or listable bucket prefix). Test with two accounts: mint on A, fetch from B with no cookies. Failure: URL is short-lived and signature-bound to the requester's identity.

**SH3 — `asset_id`-keyed rendition endpoint skips entitlement checks at the edge.**
*Grounded in:* `GET https://dc-api-v2.adobecontent.io/{expiry}/assets/download/{asset_id}/rendition{?page,format,...}` — keyed only by `asset_id`, a different host from the API.
*Idea:* The edge/CDN layer serving page renditions trusts the `asset_id` (possibly sequential or guessable) without re-validating the caller's entitlement to the underlying document — a cross-account document disclosure via page images of a PDF the caller can't open. Test: asset_id from account A's private doc, request from account B. Failure: edge validates IMS token/entitlement per request.

**SH4 — Dynamic `asset_uri` sub-resources authorize inconsistently.**
*Grounded in:* `DELETE {asset_uri}`, `GET {asset_uri}/metadata/{fields}`, `GET {asset_uri}/uri/download`, `PUT .../metadata/{fields}` all act on server-issued URIs.
*Idea:* Some operations validate ownership of the URI's embedded identity while others treat possession of the URI as authorization (URI-as-capability). A leaked/shared `asset_uri` (e.g., via a Space's network traffic, a copied Space, or the `parent_uri` chain) could allow metadata overwrite (`favorite/starred/last_access` PUT), tag PATCH, or `DELETE` on another user's asset. Test per-operation matrix with two accounts. Failure: all operations consistently 403/404 on foreign URIs.

**SH5 — Owner custom-assistant instructions execute in the victim's private chat (cross-user instruction injection without prompt-injection).**
*Grounded in:* fact sheet — "Owner-created custom AI Assistant instructions apply to all subsequent recipient chats" + "Each recipient starts a new private chat."
*Idea:* This is a **designed** cross-trust-boundary instruction channel: a malicious Space owner writes custom-assistant instructions that exfiltrate or mis-summarize; when the victim chats privately in the shared Space, the victim's session runs the attacker's instructions with the victim's context. Unlike classic prompt injection (needs poisoned document text), the payload lives in a first-class product field the victim never sees. Success per campaign bar: victim's assistant discloses the canary from the victim's unshared doc, or takes an unauthorized action. Control: same Space with benign instructions.

**SH6 — URL→PDF conversion leaks permission-restricted source content into shared Spaces.**
*Grounded in:* `createpdf_from_html` / `createppt_from_html` operations + "converted PDFs do not retain original document-level permissions" + contributors can add files/links to a Space.
*Idea:* A Space owner (or a contributor with add rights) adds a URL pointing at content gated by the source's own controls (login/paywall/IP); Adobe's fetcher converts it with whatever credentials/context the fetcher has (or the public version), the PDF lands in the shared Space stripped of permissions, and any recipient's AI Assistant answers from it. Two sub-cases: (a) fetcher-side SSRF/credential context — what network identity fetches the URL; (b) permission downgrade — restricted source becomes viewable/downloadable Space content. Failure: fetcher only converts publicly reachable URLs and marks origin clearly.

**SH7 — Cache/session confusion across share/copy transitions (canary persistence).**
*Grounded in:* 12h cache keyed on (User ID, Doc ID) + copy-Space copies docs/notes but not chat history + share extends cache lifetime.
*Idea:* (a) Owner shares a Space, then unshares/removes a document — the 12h cache (extended by the share exception) still answers recipient queries about the removed document. (b) Copy Space: the copied Space's Doc IDs may collide with or inherit the original's cache entries, so the new Space's AI answers from the original owner's cached extractions (stale or cross-owner context). Test with two accounts, timed queries after remove/unshare/copy. Failure: cache keys incorporate space/share-revision and invalidate on membership change.

**SH8 — WOPI token/document binding gap on `*.wopi.acrobat.adobe.com`.**
*Grounded in:* `dev/stage/prod.wopi.acrobat.adobe.com` in crt.sh; WOPI is a token-based protocol for browser-based Office collaboration.
*Idea:* If Acrobat's WOPI implementation issues access tokens bound loosely (e.g., token valid across documents, or `WOPISrc` not validated against the token's document), a token minted for one document could fetch another user's document. This is unverified — no public Adobe WOPI routes were found; the first step is JS-bundle or docs discovery of the WOPI REST surface (CheckFileInfo/GetFile endpoints) before any hypothesis testing. Failure: tight token↔file binding.

---

## 6. Unverified / inaccessible (honest gaps)

- No JavaScript bundle URLs were recovered from `acrobat.adobe.com` (app shell returned an error page; Wayback unavailable). The AI Assistant chat endpoints, Space CRUD/share endpoints, session-key issuance, and cloud chat-history endpoints on `*.acrobat.adobe.com` remain **undiscovered** — the actual in-scope attack surface.
- `dc-api-v2.adobe.io` routes are **out of the delegated hostname scope**; they are included as architecture/route evidence only. The Intigriti test plan (being reviewed in the parallel setup task) decides eligibility.
- PDF Spaces share/link/revoke routes are not present in the generated client snapshot — Spaces may run on a separate, newer service.
- The `pydcapi` snapshot's freshness vs. the live discovery document is unverified; `config.py` skip-lists mean some operations were deliberately excluded from generation.
- Cert-expiry on `insights-dev.acrobat.adobe.com` (June 2026) noted but not probed (probing = active; out of scope for this task).

## 7. Recommended next passive steps (for parent)

1. Recover the Acrobat Web JS bundles via an interactive browser session (DevTools network capture) to extract the real `*.acrobat.adobe.com` API routes for AI chat, Spaces, sharing, and session keys — this is the single highest-value remaining passive step.
2. Confirm from the Intigriti test plan whether `dc-api-v2.adobe.io` / `*.adobe.io` / `*.adobecontent.io` are eligible; if yes, SH1–SH4 become directly testable.
3. Feed SH1–SH8 into `brain/ResearchSession` as hypothesis seeds; SH5 is already the campaign's primary hypothesis.
