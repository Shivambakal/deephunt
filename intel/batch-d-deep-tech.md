# Batch D — Deep-Tech Intel (19 sources)

Compiled 2026-09-26. Rules for this file: detection and manual-test patterns only.
No exploit payloads, no PoC code. Record primitives and safe check patterns.
Browser/binary writeups carry a **Methodology lesson** instead of a fingerprint.

---

## 1. Redacted.NET — localhost WebSocket RCE via AI-assisted reversing
Source: `https://blog.voorivex.team/first-rce-via-reverse-engineering-with-ai`

- **What:** A Windows service ("Redacted.NET", observed software version `2.7.1.6`) exposed a local WebSocket at `ws://127.0.0.1:3100` with no Origin validation. Attacker-controlled WebSocket commands reached process-launch behavior, yielding RCE. The bug was found by reverse-engineering the desktop client with AI assistance.
- **Affected:** Redacted.NET Windows service v2.7.1.6 (desktop client / local agent software).
- **Methodology lesson:** Treat localhost services as untrusted-origin attack surface. Enumerate downloadable desktop clients, hardcoded strings, update metadata, and localhost listeners (`netstat`/`ss`); check Origin validation on every local WebSocket/HTTP endpoint; audit all command-handler variants, not just the first one reached. Encode as: inventory local listeners + probe Origin enforcement on researcher-owned installs only.

## 2. Universal Ruby `Marshal.load` deserialization gadget chain (Ruby 3.3 → 4.0.6)
Source: `https://elttam.com/blog/ruby-4-0-universal-rce-deserialization-gadget-chain`

- **What:** A universal Ruby deserialization gadget chain that works unchanged from Ruby 3.3 through 4.0.6 — untrusted bytes reaching `Marshal.load` yield RCE across the whole supported range.
- **Affected:** Any Ruby application deserializing untrusted input via `Marshal.load`/`Marshal.restore`, Ruby 3.3 through 4.0.6.
- **Fingerprint-or-test-pattern:** Static/config review — search codebases and configs for `Marshal.load` / `Marshal.restore` fed by request data, cookies, cache entries, or queue payloads. Safe detection only; never transmit serialized gadget bytes.

## 3. Three-bug V8 chain (Chrome for Testing 150.0.7871.46 / V8 15.0.245.13)
Source: `https://blog.himanshuanand.com/posts/pwn-v8`

- **What:** Three-bug V8 exploit chain: CVE-2026-15903 (address oracle), CVE-2026-15776 (GC/UAF-style primitive), and a JSPI / JS Dispatch Table mismatch, composed into a full browser chain.
- **Affected:** Chrome for Testing 150.0.7871.46, V8 15.0.245.13.
- **Methodology lesson:** Pin exact builds; climb a capability ladder (oracle → memory primitive → control flow); demand observable proof at every primitive before composing; reliability-test the final chain. No browser exploit fingerprint is encoded — browser chains are not live-test patterns.

## 4. PostGIS `address_standardizer` memory corruption (CVE-2026-73514)
Source: `https://mehmetince.net/blog/postgis-memory-corruption`

- **What:** Missing bounds validation on custom-rule Type/Weight values in PostGIS `address_standardizer` produces out-of-bounds access/write. Reported impact across managed PostgreSQL providers including NeonDB, Supabase, and Xata.
- **Affected:** PostGIS installations with the `address_standardizer` extension enabled; managed Postgres providers listed above.
- **Fingerprint-or-test-pattern:** Inventory whether `address_standardizer` is installed and record the extension version. Never send malformed custom rules.

## 5. SQL Server 2025 AI-feature abuse surface
Source: `https://specterops.io/blog/mssql-2025`

- **What:** Post-compromise / permission-design risk from SQL Server 2025 AI features: `sp_invoke_external_rest_endpoint`, `CREATE EXTERNAL MODEL`, and `AI_GENERATE_EMBEDDINGS` widen data-access paths once an attacker holds database access. Not an unauthenticated web vulnerability.
- **Affected:** SQL Server 2025 deployments with AI/external-model features enabled.
- **Fingerprint-or-test-pattern:** Authorized configuration inventory — check whether external REST endpoints and AI runtimes are enabled and whether external-model definitions exist. No callback or coercion tests.

## 6. GCP Application Integration Rhino sandbox escape (CVE-2025-0982)
Source: `https://nopnop.pro/posts/google-cloud-application-integration-sandbox`

- **What:** Rhino JavaScript sandbox escape in Google Cloud Application Integration. Google moved new JavaScript tasks to V8 in January 2025; Rhino was fully deprecated and blocked on 2026-03-30 (bulletin GCP-2026-044). The issue is mitigated — not live-testable.
- **Affected:** Legacy Rhino-based JavaScript tasks in Google Cloud Application Integration.
- **Methodology lesson:** Study denied operations, information-bearing error messages, readable local artifacts, trust tracking, and boundary inconsistencies when auditing sandboxes. Encodes as a sandbox-review checklist, not a live test.

## 7. Unitree G1 multi-vector chains (CVE-2026-76639 / CVE-2026-76640)
Source: `https://boschko.ca/g1-ble-rce`

- **What:** Chained issues on the Unitree G1 robot: chatbot path traversal / whitelist weakness, unauthenticated BLE writes, missing cloud ownership checks, unsafe Wi-Fi configuration handling, and memory corruption. Observed firmware V1.5.1.1 and V1.5.2; firmware 1.5.5.0 (released 2026-09-01) reportedly blocks the chain but the author had not independently verified it.
- **Affected:** Unitree G1 robots on firmware below 1.5.5.0.
- **Methodology lesson:** Firmware inventory plus local protocol analysis (BLE characteristics, chatbot input handling, cloud binding checks) on researcher-owned hardware. No BLE or cloud probing against devices you do not own.

## 8. Google Messages `AvatarContentProvider` confused deputy
Source: `https://blog.devploit.dev/posts/google-messages-avatarcontentprovider`

- **What:** An exported `AvatarContentProvider` in Google Messages dereferenced caller-selected Contacts photo URIs using Messages' own permission — a confused deputy. Reported build: `messages.android_20260306_02_RC09.phone_dynamic`, version code `302567063`; fixed 2026-06-12.
- **Affected:** Google Messages builds prior to the 2026-06-12 fix.
- **Fingerprint-or-test-pattern:** Static review — exported provider + no required caller permission + caller-controlled URI dereference. Dynamic validation only on a researcher-owned Android test device with researcher-owned contacts.

## 9. Android biometric AuthToken heist
Source: `https://darknavy.org/blog/the_biometric_authtoken_heist`

- **What:** Android biometric Trusted Applications could mint or leak valid shared-HMAC AuthTokens through signing interfaces, type confusion, log output, or memory corruption. Research covered 30+ devices from nine manufacturers; validated on eight devices from seven manufacturers, with BFU/CE bypass on six.
- **Affected:** Android devices with vulnerable biometric TAs.
- **Methodology lesson:** Firmware/TA inventory, debug-string and command-dispatch review, and shared-trust-key threat modeling. No operational AuthToken forging is encoded.

## 10. Burp TLS fingerprint vs. browser headers (JA3/JA4 bot scoring)
Source: `https://kecman.co/posts/burp-suite-tls-fingerprint`

- **What:** Burp's outbound Java TLS ClientHello can mismatch browser headers and trigger JA3/JA4 bot scoring. This is a tooling artifact, not a target vulnerability.
- **Affected:** Researchers proxying through Burp Suite against bot-protected targets.
- **Fingerprint-or-test-pattern:** Compare direct-browser and proxied TLS fingerprints using an authorized echo service; treat generic failures observed through Burp as possible tooling artifacts before declaring an application bug.

## 11. Apple Private Cloud Compute `darwin-init` path traversal (CVE-2026-20685)
Source: `https://blog.sentry.security/beyond-prompt-injection-hacking-apples-private-cloud-compute/`

- **What:** $150,000 bounty (Drinor). Path traversal in `darwin-init`'s `extract(to:)` (FilePath+Archive.swift:95): tar archives fall through the 4-byte magic check into generic libarchive extraction with no security flags, and entry names are appended to the output dir unsanitized. Four `..` levels escape the extraction base (`/var/tmp/darwin-init/cryptex/<UUID>/`) into `/var/db/`, which persists across the userspace reboot. The `validate(cryptexConfig:)` stub was empty and the per-cryptex sha256 digest optional. Chained to redirect `splunkloggingd` via `/var/db/prcos/splunkloggingd/config-main.plist` to an attacker listener, exfiltrating node telemetry and per-request inference metadata. Attestation bundles were identical between clean and poisoned boots (except per-boot nonce/timestamp) — an attestation gap. Demonstrated in the VRE against PCC release 37684.
- **Affected:** Apple Private Cloud Compute nodes.
- **Methodology lesson:** Audit archive-extraction dispatch (magic-byte routing → default branch), verify sanitization at the extraction join, compute persistence paths through reboot boundaries, and check validator stubs and optional integrity fields. Cloud/VRE-only target — no live bug-bounty fingerprint.

## 12. Burp Suite Professional browser-crawl file-input path traversal (Report #3712279)
Source: `https://hackerone.com/reports/3712279`

- **What:** Burp Suite Professional 2026.3.3 on Windows: the browser-powered crawler derived the temp upload filename from the file input's `accept` attribute (any token starting with `.`), then `tempDirectory.resolve(filename)` allowed path traversal — a crawled attacker page could write attacker-controlled content to arbitrary user-writable paths (e.g., a `.bat` into the Startup folder → delayed code execution at next login). Root cause: untrusted page attributes treated as safe local file metadata.
- **Affected:** Burp Suite Professional 2026.3.3 on Windows (researcher tooling, not a web target).
- **Methodology lesson:** Audit your own tooling's trust boundaries — scanner/browser drivers must never convert page-controlled metadata into local filesystem paths. Encodes as a defensive review checklist item for tooling, not a target test.

## 13. Hacking SAML with an AI harness (Authentik, litesaml, OneUptime, saml-client)
Source: `https://oblique.security/blog/hacking-saml/`

- **What:** An AI-assisted harness swept SAML implementations and found full auth bypasses in four projects — Authentik (comment-in-NameID truncation, CVE-2026-57580), PHP litesaml/lightsaml (Response signature wrapping, CVE-2026-63182), OneUptime (Response signature wrapping), Java saml-client (Response signature wrapping) — plus signature bypasses on AuthnRequest/AttributeQuery/LogoutRequest in twelve projects, and DoS vectors (Go xmldsig quadratic allocation, Node xmldom, Python libs passing unfiltered XSLT transforms to libxmlsec1).
- **Affected:** The listed SAML libraries and any products embedding them.
- **Fingerprint-or-test-pattern (authorized test instances only):** Canonicalization differentials (comments / processing instructions flattened into element text), signature-wrapping probes, and unsigned-vs-signed element confusion. Never against production IdPs or SPs. Also encodes a research workflow: gadget phase → findings phase with JSONL intermediate storage, threat-model-first prompting, adversarial double-checking.

## 14. Pwn2Own Ireland 2025 — Synology DS925+ SAML SSO auth bypass
Source: `https://chanzep.github.io/posts/pwn2own-ireland-2025-bypassing-authentication-via-synology-ds925-saml-sso/?preview=true`

- **What:** Logic bug in `SYNOPAMSSO::samlAuth` / `SSOSAMLClient::VerifySamlResponse`: the SAML client loads config from `/usr/syno/etc/ssoclient/saml.conf` (cert at `/usr/syno/etc/ssoclient/saml_cert.ca`); the local-user gate rejects NameIDs lacking `\` or `@` unless `saml_allow_local_user` is set; the bypass was found by focused binary reversing shortly before the registration deadline. No AI was used.
- **Affected:** Synology DS925+ SAML SSO.
- **Methodology lesson:** Reverse the SSO auth flow end to end; review config-file trust (paths, cert pinning, signature mode); verify NameID-to-local-account binding and local-user gating. Encodes as an SSO-integration review pattern.

## 15. Probe requests → Mitsubishi MAC-577IF-2E takeover (CVE-2026-5667)
Source: `https://innerfirez.github.io/posts/the-secret-life-of-probe-requests/`

- **What:** Unprovisioned Mitsubishi MAC-577IF-2E Wi-Fi adapters sit in setup mode broadcasting probe requests for their setup SSID. A karma AP matching the SSID plus half-handshake capture and default credentials from a public library gave LAN access to the units (HTTP Basic on port 80; full control via the public Python library — power on/off, temperature). Affected product types: room air conditioners, Wi-Fi LAN adapters for air conditioners, refrigerators, heat-pump water heaters / HEMS devices, bathroom drying / heating / ventilation units, Lossnay ventilation / smart ventilation switches, IH cooktops, rice cookers.
- **Affected:** Mitsubishi Electric devices with MAC-577IF-2E left in unprovisioned setup mode.
- **Fingerprint-or-test-pattern:** Passive probe-request monitoring (in an authorized RF environment) to inventory setup-mode IoT by SSID pattern and vendor MAC prefix. Active karma/handshake capture only against researcher-owned hardware.

## 16. MEXC Android app — JS bridge + native-lib cache RCE chain
Source: `https://itis911.github.io/writeups/RCE-Mexc-Andriod-App.html`

- **What:** Chained primitives in the MEXC Exchange Android app (`com.mexcpro.client`): (a) open redirect on the `s.mexc.com` short-link generator via a backslash parser differential — the server whitelist saw `www.mexc.com` as host (via `@`) while browsers normalize `\` to `/`, landing the victim on the attacker host; (b) an unprotected `AndroidLocalJsBridge` (`jh.a`) with no domain check, whose file-write took the filename from an unsanitized `#filename=` regex → path traversal → arbitrary file write; (c) the DXRisk anti-fraud SDK's native-library cache in `code_cache/` was honored on `file.exists()` alone — no hash/signature/CRC — so a replaced ZIP-disguised `.so` was loaded as native code in the app process. No root, no app debugging, no user interaction beyond opening a link.
- **Affected:** MEXC Exchange Android app.
- **Fingerprint-or-test-pattern:** Static review patterns — deep-link/redirect host validation for parser differentials; every `addJavascriptInterface` registration checked for origin/domain gating (an unprotected second bridge defeats a protected first one); filename handling checked for canonicalization; native-lib caches checked for integrity verification. Dynamic tests only on researcher-owned devices.

## 17. wp2root — WordPress post-exploitation chain (PHP → native → root)
Source: `https://blog.calif.io/p/the-wordpress-chain-massacre`

- **What:** Post-exploitation chain built with Codex in under an hour, starting from constrained PHP execution (wp2shell): a legacy PHP `Serializable` `unserialize()` use-after-free yields arbitrary read and forged objects → native ROP → a memfd-based stager executed via `execveat(..., AT_EMPTY_PATH)` (nothing on disk) → "Copy Fail" (2026 kernel bug affecting ~9 years of kernels) overwrites the page-cached `/usr/bin/su` with a stub → setuid-root execution → interactive root shell. Not WordPress-specific: any PHP execution primitive suffices.
- **Affected:** Hardened Linux hosts reachable through any PHP execution primitive.
- **Methodology lesson:** Capability-ladder post-exploitation (escape the interpreter → native code → kernel), self-resolving addressing (no fixed binary profile), fileless staging. Detection-side lesson: PHP `disable_functions` is not a security boundary; monitor memfd/`execveat` usage and page-cache anomalies.

## 18. wp2shell — pre-authentication RCE in WordPress core
Source: `https://slcyber.io/research-center/wp2shell-pre-authentication-rce-in-wordpress-core/`

- **What:** Searchlight Cyber pre-auth RCE in WordPress core: anonymous attacker, stock install, no plugins. Affected: 6.9.0–6.9.4 and 7.0.0–7.0.1; not affected: ≤6.8.5; fixed in 7.0.2 / 6.9.5. Public exposure checker at wp2shell.com. Emergency mitigation: block anonymous access to `/wp-json/batch/v1` and `?rest_route=/batch/v1` at WAF/plugin level.
- **Affected:** WordPress 6.9.0–6.9.4 and 7.0.0–7.0.1 (ecosystem of 500M+ sites).
- **Fingerprint-or-test-pattern:** Version inventory (readme/generator/meta) plus anonymous reachability check of `/wp-json/batch/v1` (route presence only — no malicious subrequests sent).

## 19. wp2shell root cause — batch validation/execution desync (found with GPT5.6)
Source: `https://slcyber.io/research-center/exploit-brokers-pay-500000-for-a-wordpress-rce-i-found-one-with-gpt5-6/`

- **What:** Root cause of wp2shell: the batch API's two-loop design keeps parallel `$matches`/`$validation` arrays; a malformed first subrequest takes the `is_wp_error` `continue` branch, which appends to `$validation` but not `$matches` — shifting every later handler by one, so requests execute under a different endpoint's validation (sanitization bypass). A scalar `author_exclude` then flows into `author__not_in` unsanitized → pre-auth SQLi; a recursive batch call bypasses the GET-method restriction; the read-only SQLi escalates to admin without password cracking, then plugin upload → RCE. Found with GPT5.6 Sol Ultra for ~$25 of usage via a first-principles multi-agent prompt (git history and internet diffing disabled).
- **Affected:** Same versions as #18.
- **Methodology lesson:** AI-driven zero-day hunting — diverse agent portfolio, explicit approach registry, adversarial double-checking, keep incompatible routes alive, and forbid changelog/git diffing so the model reasons from source. Encodes as a research workflow, not a live test.

---

## Top 3 encodable items

1. **wp2shell version fingerprint:** report WordPress 6.9.0–6.9.4 / 7.0.0–7.0.1 instances with anonymously reachable `/wp-json/batch/v1` — version + route-presence check only, no payloads sent.
2. **Ruby `Marshal.load` sink:** flag any flow where untrusted bytes reach `Marshal.load`/`Marshal.restore` (Ruby 3.3–4.0.6 universal chain) via static/config review; never transmit gadget bytes.
3. **Android exposed-bridge patterns:** exported ContentProvider or `addJavascriptInterface` bridge with no permission/origin check that dereferences caller-controlled URIs or filenames (Messages `AvatarContentProvider`, MEXC `AndroidLocalJsBridge`); verify statically or on a researcher-owned device only.
