# DOM-XSS Sink Mining — Pinterest, Aiven (Kindred/FDJ blocked)

Date: 2026-09-26. Passive static analysis only — public JS bundles downloaded
once, grepped locally. No exploitation, no payload delivery.
Methodology: deep-vuln-methodology.md §3 (cross-feature: URL input → DOM sink),
§4 (differentials across trust boundaries).

Bundles analyzed:
- Pinterest: 19 chunks from s.pinimg.com/webapp (homepage + login page set),
  including 17551-47ce3bd0cc75f76a.mjs (ad iframe), 44817-a1595bde0418efc5.mjs
  (LINE OAuth), 76463-3c12df4fddadeedc.mjs (survey), 40626/44175 (axios/hls),
  _client-d64afd47ba8fea89.mjs, gestalt, vendor-react.
- Aiven: console.aiven.io/main.ac1adb5b.bundle.js (6.4 MB),
  console.aiven.io/vendor/vendor-main.133c00a7.bundle.js (3.8 MB).
- Kindred/FDJ: NOT analyzed — live bundle store returns 503 bot-mitigation,
  web.archive.org was offline during this task, archive.today has no snapshot
  of kwp-bundle-store files. Gap, not a negative result.

## [SOURCE→SINK TABLE] ranked by reachability

### 1. Aiven — PostHog web-experiment preview → innerHTML (LEAD, low reachability)
- Bundle: vendor-main.133c00a7.bundle.js (PostHog SDK, web-experiments module)
- Source (URL-controllable): query params `__experiment_id` and
  `__experiment_variant` → `previewWebExperiment()` reads
  `Gi.getWindowLocation().search`, parses both params, calls
  `showPreviewWebExperiment(parseInt(q), ce, experiments)`.
- Sink: `applyTransforms()` → `xe.html && (rn.innerHTML = xe.html)` where
  `rn` = `document.querySelectorAll(xe.selector)` elements, `xe` = variant
  transform objects.
- Evidence: `previewWebExperiment(){var L=Gi.getWindowLocation();if(L!=null&&L.search){var q=Ze(L?.search,"__experiment_id"),ce=Ze(L?.search,"__experiment_variant");q&&ce&&(...this.getWebExperiments(xe=>{this.showPreviewWebExperiment(parseInt(q),ce,xe)},!1,!0))}}` and `applyTransforms(L,q,ce){...ce.forEach(xe=>{...var yt=document.querySelectorAll(xe.selector);yt?.forEach(Jt=>{var rn=Jt;xe.html&&(rn.innerHTML=xe.html),xe.css&&rn.setAttribute("style",xe.css)})}})}`.
- Why low reachability: the experiment/variant DEFINITIONS (including the
  `html` payload) are fetched server-side from PostHog's
  `/api/web_experiments/?token=<public key>` — defined in Aiven's PostHog
  workspace. The URL only selects WHICH experiment/variant to preview, not the
  HTML content. An external attacker cannot inject HTML via the URL alone.
  This becomes a real vector only under PostHog-workspace compromise
  (supply-chain class) or if variant selection has an index-confusion bug
  (`variants[ce]` with attacker string key → currently throws TypeError on
  undefined, not exploitable).
- Authenticated follow-up: none available client-side; note for supply-chain
  review only.

### 2. Pinterest — ad-slot iframe receives ad HTML via postMessage (informational)
- Bundle: 17551-47ce3bd0cc75f76a.mjs (SafePinSlotIframe, third-party ads)
- Source: ad-slot prop `e` (ad creative HTML from Pinterest's ad-server
  response, dsp Magnite) → parent executes
  `a.contentWindow?.postMessage({type:"third-party-html",html:e},"*")`.
- Sink: inside the 3p-display iframe
  (https://offsite.pinterest.com/v1/3p-display/ or /webapp/3p-display-*.html),
  which renders the posted HTML.
- Why not URL-controllable: the HTML originates from Pinterest's ad decisioning,
  not from the page URL. Receiving handler validates
  `a.source===iframe.contentWindow` AND `(a.origin===expectedOrigin ||
  a.origin==="null")`. Iframe sandbox is restrictive by default with
  `allow-same-origin` added only conditionally (`y=m?`${o} allow-same-origin`:o`).
  Trust boundary is the ad supply chain, not the DOM.
- Note: postMessage uses `"*"` as targetOrigin parent→iframe; recipient is
  Pinterest's own offsite iframe, so impact is limited. Informational only.

### 3. Aiven — highlight.js `innerHTML = Yn.value` (rejected as sink)
- Bundle: vendor-main.133c00a7.bundle.js. This is highlight.js's standard
  render path; the value is HTML-escaped during tokenization before assignment.
  Not attacker-influenced beyond the code being highlighted (own console
  content). Rejected.

## [POSTMESSAGE HANDLERS]

| Bundle | Handler | Validation | Verdict |
|---|---|---|---|
| pin 44817 + UnauthPageWrapperFooter (LINE OAuth popup) | `window.addEventListener("message", _)` → token exchange | `e.isTrusted` check AND `e===window.location.origin ? String(t) : null`; storage fallback validates `url.startsWith(window.location.origin)` + key match | REJECTED — properly origin-checked |
| pin 17551 (ad iframe) | `window.addEventListener("message", l)` | `a.source!==e.contentWindow → return`; `(a.origin===l \|\| "null"===a.origin)` where `l` = expected iframe origin | REJECTED |
| pin 76463 (AnketSurvey) | `window.addEventListener("message", this.processIFrameMessage)` | `a=e.origin\|\|e.originalEvent.origin; if(r.startsWith(a))` — note direction: the configured surveyLink must START WITH the event origin (strict, not the vulnerable `origin.startsWith(allowed)` pattern). Data values only fire callbacks (`surveyAnswersSubmitted`, `surveyFinished`, `surveyLoaded`), no DOM injection | REJECTED |
| pin 40626 (axios) | `W.addEventListener("message", ({source:e,data:t})=>{e===W&&t===u&&...})` | self-messaging (`source===window`) with random token — setImmediate polyfill | REJECTED — benign |
| pin 44175 (hls.js) | worker `addEventListener("message", this.onwmsg)` | Web Worker internal messaging, not window | REJECTED — benign |
| pin _client (service worker) | `serviceWorker.addEventListener("message", e=>{switch(e.data.message)...})` | internal SW protocol (`replay-resource-requests-*`) | REJECTED — benign |
| aiven main (AppBuilder preview nav) | `window.addEventListener("message", N)` | `if(!n?.nonce)return; ... C?.nonce!==n.nonce` → return; only `navigation-changed` type acted on | REJECTED — nonce-gated |
| aiven main (AI config) | `Yt.contentWindow.postMessage({type:"ai_config",config:{apiKey,vendor}},"*")` | Recipient is Aiven's own AppBuilder AI iframe; `"*"` targetOrigin is loose but the key is the user's own AI vendor key and the frame is first-party | Informational — no cross-origin leak to attacker frame |
| aiven vendor (image compression) | `addEventListener('message', async (e)=>{...self.importScripts(imageCompressionLibUrl)...})` | Web Worker scope (`self`), `imageCompressionLibUrl` set by Aiven's own calling code, not URL-derived | REJECTED — benign |

## [REJECTED] (checked, not issues)
- R1. Pinterest `dangerouslySetInnerHTML` (1469, 756, 76463, gestalt chunks):
  all factory-generated — i18n string factories (`String(o.factory(l))`) and
  Gestalt theme CSS (`` `.​__gestaltTheme${t}` ``). No URL-derived values.
- R2. Pinterest: zero `document.write`, `eval(`, string-`setTimeout`/
  `setInterval`, `insertAdjacentHTML`, or jQuery `.html()/.append()` DOM sinks
  in the 19 sampled chunks. `innerHTML` appears only in vendor-react (React
  internals).
- R3. Aiven `new Function("return this")` — standard global-object detection;
  `Function(...)` in AJV schema-codegen — standard, static template. Benign.
- R4. Aiven `.append(` hits are all `URLSearchParams.append` / `FormData.append`
  (MCP URL builder confirming `read_only`/`services_scope` query params per
  aiven-deep-static L4; OAuth signup `return_url` construction) — not DOM sinks.
- R5. Aiven Qualified analytics snippet via innerHTML — static string,
  `nonce` attribute set from `window.nonceForCustomScripts`. Not URL-influenced.
- R6. Aiven atob chains: data-URL→Blob (file upload handling) and PostHog
  toolbar auth (`Et(ce.hash,"__posthog")||Et(ce.hash,"state")` → base64url →
  JSON.parse → `ph_authorize` action). URL-hash-derived but terminates in auth
  state, no DOM sink. Informational.
- R7. PostHog `matchUrlConditions`/`matchUTMConditions` read `location`/UTM
  params to decide experiment ACTIVATION, but variant HTML is server-defined —
  no content injection via URL.

## Coverage gaps
- G1. Kindred/FDJ kwp-bundle-store bundles unreachable this round (503 live,
  Wayback offline, no archive.today snapshot). The 370 KB devtools bundle
  analyzed in fdj-deep-static.md was mined for hostnames, not DOM sinks —
  worth a dedicated pass when reachable.
- G2. Pinterest: only 19/623 chunks sampled (auth/messaging/rendering
  surface). A full-chunk sweep could be scheduled, but the sampled auth-heavy
  chunks are the highest-value DOM-XSS surface and came back clean.

## Bottom line
No URL-controllable source→sink DOM-XSS chain found in the analyzed bundles.
The single genuine sink (Aiven PostHog web-experiment `innerHTML`) has its
payload defined server-side in Aiven's PostHog workspace — URL params only
select experiment/variant, so external DOM XSS is not reachable through it.
All postMessage handlers in both targets validate origin and/or source+nonce.
