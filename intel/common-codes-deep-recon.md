# Deep Recon — common_codes (d-you App & German EUDI Wallet Ecosystem)

**Research date:** 2026-09-26
**Mode:** Passive only (public pages, docs, public repos read via GitHub API/raw fetch; no scanning, no probing, no sign-ins)
**Program page:** https://hackerone.com/common_codes
**Note:** Program policies change without notice. Re-verify the live policy before testing.

---

## 1. Live policy (verbatim from hackerone.com/common_codes, 2026-09-26)

### Program context
- The German EUDI Wallet app **d-you** enables people to receive, store, and present government-issued identity data and other digital credentials on their smartphone.
- Responsibility: Federal Ministry for Digital and State Modernisation (**BMDS**); **Common Codes GmbH** acts as wallet provider and central orchestrator of the ecosystem.
- Built per Regulation (EU) 2024/1183 (eIDAS 2.0) + implementing acts. **Launch: 2 January 2027.**
- At launch: PID (Person Identification Data from German eID card / e-residence permit) + EAAs (Electronic Attestations of Attributes — e.g. digital driving licence, enrolment certificates, membership cards).

### In-scope assets (current iteration; scope expands in phases)
1. **d-you Wallet Apps (Android + iOS)** — PID/EAA issuance, storage, display, update, deletion, presentation; selective disclosure + user consent; built on the EU reference implementation + AusweisApp SDK + RASP component.
2. **Remote Wallet Secure Cryptographic Application (RWSCA) + Remote Wallet Secure Cryptographic Device (RWSCD)** — RWSCA authenticates the wallet-app user and authorises crypto operations on the RWSCD HSM cluster (remote-managed keys for wallet auth, credential refresh, presentation). Interest: PIN/auth bypass, using one holder's keys under another account, unauthorised PID signing/refresh/presentation, key-material compromise at scale.
3. **Wallet Provider Backend (WPB)** — wallet-instance accounts + lifecycle, device-security evaluation, issues/revokes **Wallet Instance Attestations (WIA)**. Interest: compromising the attestation signing authority, forging attestations, making revoked wallets accepted.
4. **Mobile Device Vulnerability Management (MDVM)** — verifies platform/app security signals, classifies devices, evaluates known vulns, checks compromised attestation keys, issues a **signed MDVM token** consumed by WPB and RWSCA. Interest: compromising MDVM signing authority, forging device-security decisions at scale, approving modified/vulnerable devices at scale.
5. **Status List Service** — publishes Token Status Lists for Wallet Instance Attestations; republished frequently, short cache lifetime. Interest: status-signing authority compromise, arbitrary status publication, rollback so revoked wallets stay trusted, marking valid wallets revoked at scale.
6. **Push Notification Service (PNS)** — opt-in push registrations; backend-triggered notifications via mobile platform providers prompt wallet to refresh device-security status → detect revocation → self-lock. Interest: cross-instance registration create/change/delete at scale, redirecting notifications to attacker devices, compromising the account DB.

**Coming into scope "in the upcoming weeks" (verify on live page):** PID Provider, EUDI Hub, EUDI Check DE App, Wallet Revocation Website.

### Test apps (as listed in policy)
- iOS: TestFlight — https://testflight.apple.com/join/a2Qxrr2C
- Android: join Google group https://groups.google.com/g/de-eudi-bug-bounty-test/ then https://play.google.com/apps/testing/org.sprind.wallet.sandbox
- Test apps connect to the **test environment only** (never production services). They ship a **virtual ID** for PID issuance/presentation testing and Test EAAs usable on https://playground.eudi-wallet.org/. **Only one virtual ID is provided for testing** (no multi-identity tests possible with the official fixture).
- **Known/intentional test-app characteristics (not eligible):** no certificate pinning to relying parties; diagnostic logging enabled; screenshots/screen recording permitted.

### Out of scope
- Third-party systems: relying parties, EAA/QEAA issuers, the eID Server, mobile platform attestation services, third-party infra management portals.
- **All Youniqx-operated systems (`*.youniqx.com`)** — sole exception: `wallet-backend-sandbox.apps.sandbox.nwb.youniqx.com` (explicitly in scope).
- Physical eID card + card-reading protocols, AusweisApp SDK, eID PIN letter/postal processes.
- Internal networks, non-public systems, anything not explicitly listed.
- DoS/DDoS, load/stress, excessive traffic; social engineering; physical testing; destructive testing / unauthorised high-risk methods.
- If you hit something in an out-of-scope third-party system while testing an in-scope asset: report it anyway (forwarded to operator, no bounty).

### Explicitly NOT rewarded / closed
- RASP / root-jailbreak / emulator / debugger bypass without showing which security boundary it then defeats (compromised device is a modelled state; MDVM exists to respond to it — show the follow-on impact).
- Findings needing rooted/jailbroken/malware-infected device with no impact beyond that device's own data.
- Missing pinning/obfuscation/hardening flags without demonstrated attack.
- **Reports derived only from reading the published source code with no demonstrated impact on a listed asset.** ← critical: white-box hypotheses must be demonstrated against the live asset.
- Vulnerable/outdated deps without a working path to impact.
- Findings on outdated app versions (always retest on latest release).
- Missing security headers, cookie nitpicks, clickjacking on unauthenticated pages, tabnabbing, self-XSS, content spoofing, text injection.
- Logging in the test apps on its own.
- Rate limiting / brute force without demonstrated impact. **Exception: testing the Remote WSCA PIN retry policy is explicitly encouraged** (follow the testing rules).
- DoS/resource exhaustion/large-payload crashes; host/DNS hygiene on out-of-scope hosts; findings against sandbox test data that don't indicate a defect; third-party SDK/infra findings unless caused by Common Codes' integration/config and exploitable via a listed asset; user enumeration without privacy/security impact; automated-tooling/LLM output with no human verification and testing; functionality not yet implemented (current iteration = PID + EAA issuance and remote same-device presentation flow only).

### "Most interested in" (their words — highest-value outcomes)
- Obtaining a valid PID or EAA for an identity you don't control.
- Creating/modifying a PID/EAA the wallet, issuer, or relying party accepts as genuine.
- Extracting or using protected wallet or remote cryptographic keys.
- Reading/exporting/enumerating PID/EAA attributes of other holders.
- Getting genuine credentials via an unrecognised/modified/emulated/revoked/ineligible wallet by defeating wallet/device/key attestation controls.
- Disclosing attributes to a relying party without genuine informed consent, or a signed response materially differing from what the holder approved.
- Defeating revocation in either direction (revoked stays usable; valid gets revoked).
- Selective-disclosure failures in SD-JWT VC or mDoc releasing unapproved attributes.
- **Replay and binding failures** in challenges, nonces, attestations, authorisation artifacts, proof-of-possession artifacts across holders, wallet instances, issuers, relying parties.
- Conventional server-side impact (RCE, injection, SSRF, broken authorisation, secret exposure) on a listed backend.
- Chains of modest defects into one of the above are welcome and assessed on the chain.

### Testing rules
- Use only the virtual test identity in the test apps; never request/obtain another person's PID.
- Minimise data; stop + delete if you encounter someone else's personal data; disclose it in the report.
- **Rate limits: documented limits, else ≤2 req/s per endpoint and ≤60 req/min per source IP / test identity / client instance. No load/stress testing.**
- Required headers on all API/web requests: `User-Agent: HackerOne/<researcher-handle>` and `X-HackerOne: <researcher-handle or report-reference>` (unless that would prevent reproducing the vuln).
- Stop when asked. Report quality: working repro steps, affected asset, demonstrated impact, evidence; for crypto/protocol findings include request/response artifacts and state preconditions.

### Bounty table (2026-09-26)

| Asset (group) | Low | Medium | High | Critical | Extreme |
|---|---|---|---|---|---|
| d-you apps, MDVM, Status List, PNS | $0–100 | $300–1,200 | $1,500–4,000 | $5,000–10,000 | $15,000–40,000 |
| RWSCA, WPB | $0–200 | $500–2,000 | $2,500–6,000 | $8,000–15,000 | $15,000–40,000 |

**Extreme rating** reserved for demonstrated: remote impersonation (using another holder's PID without their device/consent); forgery of arbitrary identities (genuine/accepted PID for arbitrary real/modified/fabricated identity); mass leakage of holders' PID; systemic compromise of ecosystem trust or signing authority (arbitrary valid PID, EAAs, wallet attestations, certificates, status information at scale).

### Disclosure / safe harbor
- Confidential until Common Codes confirms remediation; they aim to confirm as soon as fix is deployed + verified; they publish program statistics periodically.
- HackerOne Gold Standard Safe Harbor applies; conditional on staying in scope/rules; does not bind third parties.
- VDP mailbox: `vulnerability-disclosure@common.codes` (PGP key published on the policy page). Mailbox is disclosure-only (no tech support). Mailbox reports are not bounty-eligible; **bounty eligibility requires submitting via HackerOne + completing identity verification, tax, sanctions screening.** Anonymous HackerOne reports triaged/remediated but generally not reward-eligible.
- Ineligible: current Common Codes employees/subcontractors/consultants/temp/agency personnel + 6-month cooling-off for former members (unless independently discovered, no non-public info). No reward-splitting/circumvention with ineligible persons. Extortion/ransom/disclosure threats → removal + possible law-enforcement referral.

---

## 2. Architecture / tech (from official docs + published source, 2026-09-26)

### Ecosystem roles
- **Wallet Provider / orchestrator:** Common Codes GmbH (under BMDS).
- **Wallet Instance (WI):** the d-you app on the holder's phone.
- **PID Provider:** operated by **Bundesdruckerei** — core digital identity derived from the eID online function (currently entering scope).
- **EAA Providers:** issue EAAs (driving licence, enrolment certs, membership cards…).
- **Relying parties / verifiers:** consume presentations.
- **RWSCA/RWSCD:** remote crypto — the app holds no long-lived high-value keys; signing for presentation/refresh happens against HSM-backed keys after PIN auth. RWSCA authorises ops; RWSCD performs them.
- **WPB:** issues Wallet Instance Attestations (`oauth-client-attestation+jwt`, ES256, `cnf.jwk` binding) that PID/EAA issuers use to judge whether the wallet instance is recognised and eligible; also revokes wallet instances (bech32 revocation code, stored as SHA-256 hash).
- **MDVM:** attests device/app integrity (Android Key Attestation via the **Makoto** library config; iOS DeviceCheck attestation + assertion) and issues the signed **MDVM token** (`Mdvm-Token` header) that WPB, RWSCA, and PNS all require. MDVM is the single trust chokepoint: every authenticated backend call chains through it.
- **Status List Service:** Token Status Lists for Wallet Instance Attestations (IETF `application/statuslist+jwt` media type); public unauthenticated read; consumed by PID providers.
- **PNS:** push registration → prompts wallet to refresh device-security status → self-lock on revocation.

### Protocols in use (verified in source)
- **OpenID4VCI** (wallet role, Kotlin `eudi-lib-jvm-openid4vci-kt`; Swift `eudi-lib-ios-openid4vci-swift`) for PID/EAA issuance.
- **SIOPv2 + OpenID4VP** (`eudi-lib-jvm-siop-openid4vp-kt`; Swift `eudi-lib-ios-siop-openid4vp-swift`) for presentation to relying parties.
- **ISO/IEC 18013-5 mDoc** security (`eudi-lib-ios-iso18013-security`; Android wallet-core fork) — same-device presentation is the currently covered flow.
- **SD-JWT VC** — explicitly named in the policy's "most interested" list (selective-disclosure failures in SD-JWT VC or mdoc).
- **Wallet attestation:** OAuth Client Attestation JWT (`oauth-client-attestation+jwt`) with `cnf` key confirmation + Token Status List reference.
- **Backend auth scheme (custom, high-value for white-box review):** per-service challenge tokens (`auth-challenge+jwt`, HMAC-HS256, random nonce, issue-time validated — see hypothesis H2) + **HTTP Message Signatures (RFC 9421 style)** via the Authlete `hms` library. Algorithm strictly mapped: only `ecdsa-p256-sha256` → `SHA256withECDSA`. Required components per endpoint include `@method`, `@path`, `Auth-Challenge`, `Mdvm-Token`, `Rwsca-Account-Id`/`Wpb-Wi-Id`, and `Content-Digest` where a body matters. Signature labels: `mdvm-auth-sig`, `wpb-auth-sig`, `wpb-wia-sig`, `rwsca-auth-sig`, `rwsca-pin-sig`, `pns-auth-sig`.
- **Key management:** HSM via PKCS#11 (SoftHSM fixtures in the mirror; `HsmProvider`/`HsmSessionPool` in `shared/hsm/`). Key lineages (`shared/keyrollover/`): asymmetric signing lineages (`AsymmetricSigningLineage`) + symmetric lineages (challenge HMAC keys, PIN-session HMAC keys). Rollover scans HSM for active keys, adopts newest resolvable, signs proof-of-possession, and **holds last good key if no valid key resolves** (availability-preserving, log-only).

### Trust boundaries (white-box read)
1. MDVM token = ecosystem trust root for device eligibility. Forged/approved-anything MDVM token → WPB issues WIA → issuers trust the wallet.
2. RWSCA PIN session token (`rwsca-pin-session-token+jwt`, HS256, binds `rwsca_account_id`, has expiry) authorises HSM sign ops (`sign-data`) on behalf of a holder.
3. WPB revocation codes are bearer secrets (16 random bytes, bech32 `rev…`, SHA-256 hash stored server-side; given to the WI once at registration, never recoverable). Anyone holding it can revoke the wallet instance.
4. Status-list read path is public/unauthenticated; index allocation uses a Feistel (FPE FF1) permutation over a minimum 2^20 domain with empty tweak — determinism is by design (privacy: index doesn't reveal insertion order), not a flaw per se.
5. Mobile apps: credentials/keys locally protected (wallet-storage libs; Android Keystore / SQLCipher in the EC reference lineage); the policy's highest-value app outcomes are issuance hijack, consent-bypass disclosure, and wallet cloning defeating device binding.

### Official documentation
- **Architecture Documentation for the German National EUDI Wallet** — https://bmi.usercontent.opencode.de/eudi-wallet/wallet-development-documentation-public/latest/ (component decomposition, cryptography chapter, data flows: wallet activation, PID issuance, PID presentation, revocation; WPB/RWSCA/MDVM chapters; app attestation + eID flow appendices; GitLab source on OpenCoDE).
- **Blueprint for the EUDI Wallet Ecosystem** — same opencode.de site (implementation options, architecture decisions, governance).
- EU Architecture and Reference Framework (ARF): https://eudi.dev/ (also https://docs.eudi.dev/, https://conformance.eudi.dev/).
- General program info/FAQ: https://eudi-wallet.gov.de/.

---

## 3. Third parties & partners (all from official/press sources, 2026-09-26)

- **Common Codes GmbH** — wallet provider + ecosystem orchestrator (program owner).
- **BMDS** (Federal Ministry for Digital and State Modernisation) — responsible ministry.
- **SPRIND** (Federal Agency for Disruptive Innovation) — develops the state wallet on BMDS's behalf.
- **youniqx Identity AG** (digital subsidiary of the Austrian State Printing Company) — won the SPRIND Europe-wide tender for the wallet technical platform; consortium: A1 Digital International GmbH, CRYPTAS Group, msg group. **Note: `*.youniqx.com` is explicitly OUT of scope** except `wallet-backend-sandbox.apps.sandbox.nwb.youniqx.com`.
- **Bundesdruckerei GmbH** — PID Provider (core identity from eID online function).
- **Fraunhofer AISEC, BSI, PwC, Meiré und Meiré** — named partners on eudi-wallet.gov.de (security research, product/design).
- **AusweisApp SDK** (Governikus) — eID card reading; SDK itself out of scope.
- **Bitkom MoU** (75+ orgs incl. Deutsche Bank, Deutsche Bahn, Lufthansa Group, Mastercard, N26, SAP, Vodafone, Bundesdruckerei, IDnow) — adoption partners (relying parties; **out of scope** as third-party systems).
- **Launch partners** (~40 named in press: EON, Vodafone, Deutsche Post, Swisscom Trust Services, Lindner Group/inGo, city/state governments…) — relying parties / EAA issuers, **out of scope**, but note for context (report via Common Codes anyway if you hit something in them while testing an in-scope asset; no bounty).
- **Apple/Google** — DeviceCheck / Play Integrity + Key Attestation are the platform attestation services the MDVM consumes; **out of scope** as third-party attestation services.
- **European Commission EUDI Wallet reference implementation** — the upstream code the d-you apps fork; EC org: https://github.com/eu-digital-identity-wallet.

---

## 4. Code & repos — core deliverable (verified via GitHub API, 2026-09-26)

### Official org: https://github.com/german-national-wallet
One-way read-only mirrors of an internal repo. All 15 public repos (language, fork status, last push as of 2026-09-26):

| Repo | Lang | Type | Pushed | Role |
|---|---|---|---|---|
| `de-eudi-wallet-backend` | Kotlin | **original** | 2026-09-16 | WPB + RWSCA + MDVM + PNS + Status List (Spring Boot, one entry point per service + combined app on :8080) |
| `de-eudi-wallet-android` | Kotlin | **original** | 2026-09-21 | d-you Android app (multi-module; business-logic/src/{dev,sandbox,staging,production}) |
| `de-eudi-wallet-ios` | Swift | **original** | 2026-09-16 | d-you iOS app (IDGo; schemes Dev/Sandbox/Staging/Prod; bundle ids `org.sprind.wallet.*`, prod `codes.common.dyou.prod`) |
| `de-eudi-lib-ios-wallet-kit` | Swift | fork of EC | 2026-09-21 | EUDI Wallet Kit iOS library (wallet core services/models) |
| `eudi-lib-android-wallet-core` | Kotlin | fork of EC | 2026-09-25 | Android wallet core (builds as `:core:wallet-core` submodule) |
| `eudi-lib-jvm-openid4vci-kt` | Kotlin | fork of EC | 2026-09-10 | OpenID4VCI wallet role (`develop-0.30.2` branch pinned) |
| `eudi-lib-ios-openid4vci-swift` | Swift | fork of EC | 2026-07-28 | OpenID4VCI wallet role (Swift) |
| `eudi-lib-jvm-siop-openid4vp-kt` | Kotlin | fork of EC | 2025-05-16 | SIOPv2/OpenID4VP wallet role |
| `eudi-lib-ios-siop-openid4vp-swift` | Swift | fork of EC | 2025-10-22 | SIOPv2/OpenID4VP wallet role (Swift) |
| `eudi-lib-ios-wallet-storage` | Swift | fork of EC | 2026-04-01 | Wallet storage library |
| `eudi-lib-ios-iso18013-security` | Swift | fork of EC | 2026-05-07 | ISO 18013-5 mDoc security mechanisms |
| `eudi-app-ios-wallet-ui` | — | fork of EC | 2025-11-05 | Upstream reference UI fork (prototype) |
| `wallet-document-manager` | — | fork | 2025-01-15 | Document manager (stale, 2025-01) |
| `issues-tracker-ios` | — | **original** | 2026-09-18 | Public issue tracker for the iOS wallet |
| `issues-tracker-android` | — | **original** | 2026-09-18 | Public issue tracker for the Android wallet |

Upstream EC org: https://github.com/eu-digital-identity-wallet (~85 repos; ARF at `eudi-doc-architecture-and-reference-framework`).

### What the mirror strips (stated in READMEs — sets white-box expectations)
- Service endpoints and credentials are **placeholders**; signing/CI/fastlane omitted; **tests not published**; a commercial typeface omitted; issue tracking disabled on the mirrors (planned for October 2026).
- Android builds need two hand-cloned submodule forks (`eudi-lib-android-wallet-core` @ `develop-0.30.2`, `eudi-lib-jvm-openid4vci-kt` @ `develop-0.13.1`) — the exact dependency versions for diffing against upstream.
- Backend: dev PKI/key fixtures not published; `docker-compose.yml` runs PostgreSQL + Kafka + simulated S3 + SoftHSM.

### de-eudi-wallet-backend — white-box trust-boundary notes (Kotlin, Spring Boot WebFlux)
- **RWSCA** (`rwsca/`): `RwscaApi` — challenge → register (`wi_rwsca_pin_pubk`) → initialize-PIN + start PIN session → create-keys (`wi_key_binding_data_hash`, `rwscd_key_binding_signature`, `rwscd_wi_pubk`) → sign-data (HSM-backed). PIN session tokens: HS256 JWT, `rwsca_account_id` claim, expiry enforced server-side (`validateExpirationTime`). Two signature labels: `rwsca-auth-sig` (account-level) and `rwsca-pin-sig` (session-level for sign-data).
- **PIN retry policy:** `RwscaAccountService` — `maxTries` with `backoffDurations` (config-validated: `backoffDurations.size == maxTries - 1`), account locks when `pinTryCounter == 0`, state changes are `@Transactional`. **Policy explicitly encourages testing the PIN retry policy** — race/TOCTOU on the counter under concurrent wrong-PIN attempts is the natural white-box probe.
- **Account binding:** account operations verify the request signature key's JWK thumbprint equals the registered `wiMdvmAuthPubk` (`verifyAuthPubKey`); mismatch → `AccountNotFoundException` (uniform error, no oracle).
- **WPB** (`wpb/`): register → attestation (`wi_wia_pubk`, optional `wpb_client_instance_id` UUID for status-list entry reuse) → signed WIA (`oauth-client-attestation+jwt`, ES256, x5c chain, `cnf.jwk`, `client_status` → status-list uri/idx/exp). Revocation via bearer bech32 code (16 random bytes → bech32 `rev…`; SHA-256 hash stored). `WpbClientInstanceId` is a UUID — renewal reuses the same status-list entry (revocation-state continuity depends on this).
- **MDVM** (`mdvm/`): register/renewal per platform (Android Key Attestation chain; iOS DeviceCheck attestation + assertion), `MdvmAccountId` bound to the auth key, signed **MDVM token** (`MdvmTokenBuilder`/`MdvmTokenParser`) required by all other services. Config: `allow-skip-key-attestation` (dev/ci-test only), `allow-software-key-attestation`, iOS dev-environment App Attest, `expected-package-names` + signer fingerprints, `minimalAndroidVersion`, patch-level freshness, Android revocation lists (Google CRL + in-repo JSON placeholder), vulnerable-device-class lists (placeholders in mirror; curated in prod). The `Skip-Integrity-Checks: all` header path exists in code — production behaviour depends on deployed config (unverified).
- **PNS** (`pns/`): register/delete push tokens keyed by `mdvmAccountId` extracted from the MDVM token; MPP token max 1024 chars; hidden from logs (`toString` masking). Delete requires only a valid MDVM token + signatures — no proof of push-token ownership.
- **Status List** (`statuslist/`): public read `/status-lists/{segment}/{poolId}/{listId}` + `/aggregation`; weak ETags on version (`W/"<version>"`), `If-None-Match` honored, `Cache-Control: max-age=<pool.ttl>`; JWT media type `application/statuslist+jwt`; pool/segment validated → 404 otherwise. Index allocation via **FPE-FF1 Feistel permutation** (radix 2, min 20-bit domain, empty tweak, cycle-walking) — permutation hides insertion order by design. `StatusListGc` + scheduler republish frequently (policy: short cache lifetime).
- **Crypto plumbing** (`shared/`): HSM ECDSA/HMAC/JWE via PKCS#11 (`HsmEcdsaSigner`, `HsmHmacSigner/Verifier`, `HsmJweCrypter`); BouncyCastle; `HttpSignatureVerifier` (Authlete hms lib; strict alg map; required-components check is `containsAll` on canonical names + Content-Digest presence check); challenge tokens (HS256, random UUID nonce, `validateIssueTime` freshness); JWT validation helpers (`validateType`, `validateIssuer`, `validateExpirationTime`, `validatedKeyId`); `ContentDigestFilter`; key-rollover lineages with hold-last-good semantics.
- **Messaging:** Kafka topics for wallet-instance revocation events and push notifications (`KafkaWalletInstanceRevocationPublisher`, `PnsPushNotificationListener`, `MdvmRevocationListener`, `RwscaRevocationListener`) — revocation propagation path worth tracing.

### Mobile apps — notes for consent/presentation hypotheses
- Android: feature modules (`feature-issuance`, `feature-presentation`, `feature-proximity`, `card-reader-feature`, `authentication-logic`, `core-logic`, `business-logic` with per-env flavors dev/sandbox/staging/production); depends on `eudi-lib-android-wallet-core` + `eudi-lib-jvm-openid4vci-kt` submodules.
- iOS: `Modules/feature-issuance`, `feature-presentation`, `feature-proximity`, `feature-startup`, `logic-authentication`, `logic-api`, `logic-business`, `logic-analytics`; depends on `de-eudi-lib-ios-wallet-kit`.
- Policy's app-level interests: issuance hijack (credential bound to attacker wallet), consent-bypass disclosure, selective-disclosure failures (SD-JWT VC / mDoc), wallet cloning defeating device binding. White-box focus: compare the consent screen's disclosed-claims model against the claims actually signed in the VP/mDoc response.

---

## 5. Videos & writeups (2026-09-26; d-you-specific disclosures: none found)
- **No public d-you/Common Codes disclosed bounty reports or d-you-specific conference talks found** (program is new; wallet launches 2027-01-02). Mark as a gap, not as absence of material.
- EC reference implementation QA: `eu-digital-identity-wallet/eudi-docs-site` → `reference-implementation/quality-assurance.md` — security testing per release (OWASP MASVS/MASTG, MobSF, Burp, dependency-check; SQLCipher + Keystore). A NiScy security-testing results workbook is linked per release (e.g. `EUDI-Wallet-NiScy_Security Testing Results-Version_2025.07.28-Demo.xlsx` in `eudi-doc-testing-application`) — **worth reading**: findings against the upstream libraries the d-you apps fork.
- ENISA draft certification: "Draft Candidate EUDIW 0.4.614" (certification.enisa.europa.eu) — evaluation/certification requirements for EUDI wallets; useful for threat-model vocabulary (public consultation closed 2026-04-30).
- Press/landscape: Biometric Update (2026-09-14, d-you launch coverage), ID Tech (launch partners), pressat.co.uk (youniqx tender award, 2025-12-22), mobileidworld.com (Bitkom 75-org MoU), IDnow consumer survey (PRNewswire, 2026-09). Landscape research note: `andrevalenm/poh-aggregator` research file on eIDAS2/EUDI (third-party, unverified).
- Researcher angle: since d-you forks the EC reference implementation, **past disclosures against the EC reference libs** (OpenID4VCI/SIOP/mDoc components) are the closest prior art — check the EC org's security advisories and the NiScy workbooks before testing.

---

## 6. Asset inventory — passive only (domains taken from official docs/repos/policy only; NO scanning, NO probing)
- https://hackerone.com/common_codes (program)
- https://eudi-wallet.gov.de/ (program info/FAQ)
- https://bmi.usercontent.opencode.de/eudi-wallet/wallet-development-documentation-public/latest/ (architecture docs; blueprint alongside)
- https://github.com/german-national-wallet (source mirrors)
- https://github.com/eu-digital-identity-wallet (upstream reference implementation)
- https://eudi.dev/ · https://docs.eudi.dev/ · https://conformance.eudi.dev/ (EU ARF + reference docs)
- https://www.ausweisapp.bund.de/ (AusweisApp SDK info; SDK itself out of scope)
- https://playground.eudi-wallet.org/ (test EAA issuance/presentation playground)
- https://testflight.apple.com/join/a2Qxrr2C (iOS test app)
- https://play.google.com/apps/testing/org.sprind.wallet.sandbox (Android test app)
- https://groups.google.com/g/de-eudi-bug-bounty-test/ (Android test-app group)
- `wallet-backend-sandbox.apps.sandbox.nwb.youniqx.com` (only in-scope youniqx host; exact test-environment endpoints to be taken from the test apps/policy, not guessed)
- `vulnerability-disclosure@common.codes` (VDP mailbox, PGP key on policy page)
- https://certification.enisa.europa.eu/ (EUDIW certification draft)
- All other `*.youniqx.com` — out of scope.

---

## 7. Hypothesis seeds (white-box → live-test; all need demonstration on a listed asset — source-only reads are explicitly out of bounty)

**H1 — MDVM `Skip-Integrity-Checks` header honored in a non-dev deployment.**
Hypothesis: the MDVM register/renewal path accepts `Skip-Integrity-Checks: all` with no valid attestation outside the documented ci-test profile (config drift between mirror defaults and deployed env).
Why this target: `MdvmConfiguration`/`SkipIntegrityChecks.kt` implement the bypass; the README documents it as profile-gated (`DEPLOYMENT_ENVIRONMENT: ci-test`), so the security property rests entirely on deployed config. MDVM token is the ecosystem trust root — a skipped attestation yields a genuine MDVM token for an attacker-controlled device → WPB WIA → issuer trust.
Expected observation: MDVM token issued for a request with no attestation chain; then WPB attestation succeeds for that wallet instance.
Vuln class: broken access control / config flaw → privilege escalation at scale (Extreme-adjacent if systemic).

**H2 — Challenge tokens are single-issuance but not single-use or requester-bound.**
Hypothesis: `ChallengeTokenBuilder.parseAndValidate` checks type, issuer, key id, and issue-time freshness only — no nonce allowlist, no binding to a wallet instance or operation. A captured challenge JWT can be reused across operations (register → create-keys → sign-data) and possibly across wallet instances.
Why this target: `shared/challengetoken/ChallengeToken.kt` shows freshness-only validation; each API (`/challenge` per service) mints challenges with a random nonce but nothing consumes it. The HTTP signature binds the challenge *value* to the request, but the challenge itself is not bound to a requester.
Expected observation: use one `/challenge` response for two distinct mutating calls (or two wallet instances) and have both accepted within the freshness window.
Vuln class: authentication protocol weakness (challenge replay). Note: impact depends on what the replay enables beyond convenience — chain with H5/H7.

**H3 — PIN retry counter race (RWSCA).**
Hypothesis: concurrent wrong-PIN attempts against `start-pin-session`/PIN-auth race the `pinTryCounter` decrement, allowing more guesses than `maxTries` before lockout (or the backoff is enforced client-side/per-process rather than atomically).
Why this target: `RwscaAccountService` gates on `pinTryCounter == 0` with `@Transactional` updates and config-validated backoff schedule; the program **explicitly encourages** testing the Remote WSCA PIN retry policy. A 4–6 digit PIN with a bypassed retry limit = remote impersonation primitive (another holder's PID via their RWSCA account requires the account's auth key + PIN — the PIN is the remaining factor).
Expected observation: N parallel wrong-PIN attempts all return "wrong PIN" rather than lockout after `maxTries`; or successful auth after > maxTries attempts across parallel connections.
Vuln class: authentication bypass / race condition (TOCTOU). Stay within the 2 req/s guidance; the policy invites this test but rate rules still apply.

**H4 — Cross-endpoint HTTP-signature transplant within one service.**
Hypothesis: signature labels (`rwsca-auth-sig` vs `rwsca-pin-sig`; `wpb-auth-sig` vs `wpb-wia-sig`) and required-component sets differ per endpoint, but `HttpSignatureVerifier` checks only `containsAll(required)` — extra covered components are allowed and the `@path` component binds the endpoint, so same-endpoint replay is blocked by the challenge; however, check whether **two endpoints share identical required-component sets** (e.g. RWSCA register vs delete-account both require method+path+challenge+mdvm-token). If the server does not bind the signature to the label/operation, a signature minted for register could be replayed at delete-account with a fresh challenge… — the challenge freshness check would fail on reuse. Realistic variant: **required components do not include `Content-Digest` on some mutating endpoints** — verify each POST body endpoint covers `Content-Digest`; any that doesn't allows body substitution under a valid signature.
Expected observation: take a valid signed request, swap the body (where Content-Digest isn't required) or transplant a signature to a same-component-set endpoint; server accepts.
Vuln class: signature verification flaw → request forgery. (Code shows Content-Digest IS required on body endpoints seen; the check is to confirm none were missed, especially renewal paths.)

**H5 — PIN-session token bearer scope: account-scoped token accepted where session binding is assumed.**
Hypothesis: the PIN session token (`rwsca-pin-session-token+jwt`) binds only `rwsca_account_id` + expiry. `sign-data` authorisation requires the token in `Rwsca-Pin-Session-Token` header plus a `rwsca-pin-sig` HTTP signature made with the account auth key. If the session token leaks (e.g. via the intentionally verbose test-app logging — test-only, ineligible alone), anyone holding the account auth key… — they already have the key. Sharper variant: **token not bound to the PIN-auth event** — `initializePinAndStartPinSession` returns a fresh session on PIN verify; check whether an *old, unexpired* session token remains valid after the PIN is *changed* (re-PIN / PIN reset flow). A stale token authorising HSM sign ops after credential rotation = auth lifecycle flaw.
Expected observation: change/reset the wallet PIN, then use the pre-rotation PIN session token for sign-data; accepted ⇒ stale session honored.
Vuln class: session management / credential-rotation flaw.

**H6 — PNS registration hijack / deletion via MDVM-token bearer.**
Hypothesis: PNS register/delete authorise solely on the MDVM token (bearer) + HTTP signature with the MDVM auth key — there is no proof of ownership of the push token being registered, and delete takes no identifier of which registration to remove (it's keyed by `mdvmAccountId`). If an MDVM token for a victim instance is obtainable (same bearer-theft model as H5, or via the test app's diagnostic logging in the *test* environment), an attacker can overwrite the victim's push registration with their own MPP token → victim's revocation/self-lock notifications go to the attacker; or delete the victim's registration → victim's wallet never learns of revocation → **revocation bypass in the notification channel** (the program lists both "redirecting notifications to attacker-controlled devices" and "defeating revocation" as interests).
Expected observation: with victim MDVM token, register attacker's MPP token; subsequent backend-triggered notification is delivered to attacker device / victim registration gone.
Vuln class: broken authorisation (IDOR-adjacent) → revocation defeat. Note: requires MDVM-token theft as precondition — chain value.

**H7 — WPB status-list entry reuse on attestation renewal defeats revocation propagation.**
Hypothesis: `WpbAttestationRequest` accepts `wpb_client_instance_id` (UUID) to *reuse* a status-list entry on renewal; `WpbStatusListPoolCheck` and `StatusListGc` manage the pool. If a revoked wallet instance renews its attestation reusing the same client instance id while the revocation event is still propagating (Kafka `WalletInstanceRevocationEvent` → listeners), there may be a window — or a logic gap — where the renewed WIA points at a status-list index whose status flips late, and issuers caching the list (short TTL but non-zero) accept the wallet.
Expected observation: revoke instance, immediately renew attestation with the same client instance id, present the new WIA + freshly fetched status list to a verifier; acceptance ⇒ revocation not effective.
Vuln class: revocation defeat (explicitly in the "most interested" list, both directions).

**H8 — Consent/presentation mismatch in the mobile apps (selective disclosure bypass).**
Hypothesis: the presentation flow's consent screen (what the holder approves) and the actually signed VP/mDoc payload (what the verifier receives) are built from different data paths in `feature-presentation`; a discrepancy (e.g. extra claims included, or claims from a different credential) releases attributes the holder didn't approve.
Why this target: policy explicitly lists "causing the signed response to differ materially from what the holder approved" and "selective disclosure failures in SD-JWT VC or mdoc"; the app repos publish the full presentation modules (`de-eudi-wallet-android` feature-presentation, `de-eudi-wallet-ios` Modules/feature-presentation) against EC reference libs — diff the consent ViewModel against the signed-payload builder.
Expected observation: using the virtual ID + Test EAAs on the playground, approve disclosure of claim subset A; verifier receives A ∪ B (or a different credential's claims).
Vuln class: broken access control / consent bypass → unauthorised disclosure of identity attributes.

**H9 — Issuance hijack: attacker wallet completes the victim's OpenID4VCI session.**
Hypothesis: the OpenID4VCI issuance flow (authorization code / pre-authorized code) binds the credential offer to a wallet instance only via the WIA presented at the token/credential endpoint. If the binding between the issuance session (started in the victim's wallet) and the `cnf`/DPoP key that receives the credential is weak — e.g. the credential request's proof-of-possession key isn't matched to the key from the pushed authorization request — an attacker who can observe or steal the offer URI (QR/deep link, shoulder-surfing, clipboard) can complete issuance into their own wallet and obtain a PID/EAA for the victim's identity.
Why this target: policy's #1 interest is "obtaining a valid PID or EAA for an identity you do not control"; issuance is the exact chokepoint; the EC `openid4vci` libs are forked with German modifications (`develop-0.30.2`/`develop-0.13.1` branches) — diff the forks against upstream for binding checks.
Expected observation: start issuance in wallet A (test virtual ID), transfer the offer/QR to wallet B, complete in B; credential lands in B ⇒ issuance not bound to the initiating instance.
Vuln class: broken binding / issuance hijack → credential theft.

**H10 — Key-rollover "hold last good" signs with a compromised/expired key.**
Hypothesis: `AsymmetricSigningLineage.adoptNewestResolvable` holds the last good key and keeps signing when no valid key resolves (`logHoldingLastGood`); combined with a long-lived deployment, a compromised attestation/MDVM signing key could remain the active signer after its notAfter (the `current()` expiry check exists, so expired keys are refused — verify the check covers all lineages, including the symmetric challenge/PIN lineages). Sharper: during rollover, `validatedKeyId` accepts any key in `validKeys` — check whether retired keys remain in `validKeys` and for how long; a leaked retired challenge-HMAC key would let an attacker mint valid challenge tokens indefinitely.
Expected observation (code-confirmed, live-probed): inspect which key ids are accepted for challenge/PIN-session verification vs. which are current; if a retired key id still verifies, key-compromise impact is extended.
Vuln class: cryptographic lifecycle flaw → extended forgery window.

### Where to start (priority order, given the policy's own ranking)
1. **H3 (PIN retry)** — explicitly invited by the program; RWSCA is the top-ranked asset group.
2. **H7/H6 (revocation defeat)** — revocation in both directions is named twice in "most interested"; WPB/RWSCA are the top-paying group.
3. **H1 (MDVM skip)** — MDVM is the trust chokepoint for everything; a systemic bypass is Extreme-adjacent.
4. **H9/H8 (issuance/consent)** — the #1 stated interest (someone else's PID/EAA) via the app + EC-lib diff.
5. H2/H4/H5/H10 — protocol/lifecycle hardening checks; best as chains into the above.

---

## 8. Caveats & open verifications
- **Source mirrors are sanitised**: endpoints/keys are placeholders, tests unpublished, revocation/vulnerable-device lists are empty placeholders in the mirror. Behaviour observed in the mirror (e.g. `allow-skip-key-attestation`) reflects code paths, not deployed prod/test config — every config-dependent hypothesis (H1 especially) must be probed against the live test environment.
- **"Reports derived only from reading the published source code" are explicitly out of bounty** — every hypothesis above needs a live demonstration on a listed asset with request/response artifacts.
- Scope components entering "in the upcoming weeks" (PID Provider, EUDI Hub, EUDI Check DE App, Wallet Revocation Website): re-read the policy page before touching them.
- No d-you-specific disclosed reports, audits, or conference talks found as of 2026-09-26; closest prior art is the EC reference implementation's published security test results (NiScy workbooks) and the ENISA EUDIW certification draft.
- Mobile-app backend for the test environment: exact sandbox endpoints come from the test apps themselves (bundle `org.sprind.wallet.sandbox`); do not guess hosts. The only named in-scope non-app host is `wallet-backend-sandbox.apps.sandbox.nwb.youniqx.com`.

*End of report — 2026-09-26.*
