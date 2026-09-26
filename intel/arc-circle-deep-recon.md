# Arc (Circle) — Passive Deep-Recon Report
**Date:** 2026-09-26 (IST). **Policy captured live from HackerOne on 2026-09-26.** Policies change without notice — re-read the policy before any test.
**Mode:** PASSIVE ONLY. All data below is from public pages/docs/repos fetched 2026-09-26. No scanning, probing, auth attempts, or transactions were performed.

> Arc = Circle's USDC-native Layer-1 blockchain. **NOT** the Arc browser company. Mainnet launched 2026-09-16.

---

## 1. Live policy — hackerone.com/arc-bbp (captured 2026-09-26)

**Program:** Arc (managed by HackerOne, collaboration enabled, includes retesting). Min bounty $100. Response efficiency >90%; avg first response 14h, triage 13h, bounty ~1d23h, resolution ~2d10h.

**Scope line from policy header:** `*.arc.io` (Tier B web) + "Arc Mainnet Chain/Protocol" (Tier A). "All assets" bounty line also listed for mainnet scope.

### Tier A — Arc Mainnet Chain/Protocol
| Criticality | Reward | Examples given |
|---|---|---|
| Extreme | Up to $1,000,000 | Unlimited minting; private key compromise; consensus safety failure / validator-set takeover; chain halt under clear criteria |
| Critical | $20,000–200,000 | Critical chain / system-contract flaws with direct fund losses |
| High | $10,000–20,000 | Significant privilege / operational impact with constrained preconditions |
| Medium | $5,000–10,000 | Bounded impact with compensating controls |
| Low | Up to $5,000 | Limited security consequence |

### Tier B — Arc Product / Web 2 (e.g. *.arc.io)
| Criticality | Reward | Examples given |
|---|---|---|
| Critical | $3,000–10,000 | Unauthenticated account takeover, RCE, unrestricted admin on Portal/Arc product backends |
| High | $800–3,000 | Account takeover w/ realistic user interaction, auth bypass into privileged Portal workflows |
| Medium | $400–800 | Stored XSS, limited-scope IDOR, constrained SSRF |
| Low | Up to $400 | Verbose errors, clickjacking on low-sensitivity pages, low-risk reflected XSS |

### Hard rules that matter for this hunt
- **Test ONLY on a local dev.net or the Arc testnet. "Please refrain from testing on the mainnet environment."** → Smart-contract/chain bugs must be reproduced on **testnet (chain 5042002)** or local devnet; mainnet testing is explicitly banned. Anything moving real mainnet funds is OUT.
- **"You need to show that you could exploit a vulnerability, but you must not actually exploit it."** PoC-on-testnet + argued mainnet impact is the intended path.
- One vulnerability per report (unless chained); duplicates → first reproducible report wins; one bounty per underlying issue.
- No social engineering (phishing/vishing/smishing).
- No privacy violations / data destruction / service interruption; only interact with accounts/wallets you own or have explicit permission for. No accessing/modifying others' data; no DoS; no loss of others' funds.
- 18+, English reports, no Circle employees/family, sanctioned-jurisdiction exclusion, tax your own responsibility, Circle sole discretion on payment.
- **Disclosure:** "Do not discuss any vulnerabilities (even resolved ones) outside of the Program without express written consent from the organization." Follow HackerOne disclosure guidelines. → Expect no public writeups/disclosed reports; none found for arc-bbp.
- Safe harbor: activity consistent with the T&C is treated as authorized; Circle will not initiate legal action. T&C may change without notice.
- Docs/test plan links in policy: arc.io (Arc docs), docs.arc.io ("Arc testnet"), docs.arc.network. **Note:** policy page references both `docs.arc.io` and `docs.arc.network` — as of 2026-09-26 the live canonical docs resolve at **docs.arc.network** (checked: connect-to-arc page live). docs.arc.io referenced by third-party dev docs as canonical; treat both as official but verify testnet hostnames at runtime.
- Out-of-scope vulnerability classes: standard HackerOne "Core Ineligible" list plus: source-manipulation vulns, unit-test vulns, clickjacking w/o sensitive actions, CSRF on unauthenticated/non-sensitive forms, MITM/physical-access-required, known-vuln libs without working PoC, CSV injection without demonstrating a vuln, SSL/TLS & CSP best-practice nits, missing HttpOnly/Secure flags, SPF/DKIM/DMARC nits, outdated-browser-only, version-disclosure/banner, zero-days with <1 month of official patch (case-by-case), tabnabbing, open redirect without added impact, issues requiring unlikely user interaction, rate-limit/bruteforce on non-auth endpoints, content spoofing/text injection without HTML/CSS modification, any DoS.

**Interpretation:** Smart-contract bugs ARE in scope (Tier A explicitly covers "chain / system-contract flaws"). Blockchain funds-at-risk severity model is used: Extreme examples (unlimited minting, consensus failure) map to protocol-level impact, mirroring the Circle precedent below (Asymmetric Research found an infinite-mint bug in Circle's noble-cctp bridge module on Cosmos via this bounty pipeline — disclosed 2024, no funds lost, message-sender verification flaw in BurnMessages). Severity is tied to demonstrable fund loss / chain safety impact.

---

## 2. Architecture / tech (from official docs, GitHub READMEs, press — 2026-09-26)

- **What:** EVM-compatible Layer-1 purpose-built for stablecoin finance ("Economic OS for the internet"). Testnet public since Oct 2025 (>700M tx before mainnet, ~3M wallets); **public mainnet live 2026-09-16**.
- **Gas token = native USDC (one balance, two views).** Fees paid directly in USDC. Dual-decimal design: **native coin 18 decimals**; the ERC-20 USDC interface is **6 decimals at `0x3600000000000000000000000000000000000000`** (UNVERIFIED — from community dev docs; wallet integration docs warn about dual decimals, so the 6/18 split is confirmed conceptually, the address is community-sourced). One pool of funds, not two assets. Base fee model: EIP-1559-style with **weighted moving average** of network demand (not per-block retarget); press cites a fixed 20 gwei base fee (UNVERIFIED). Fees flow to an on-chain Arc Treasury.
- **Consensus:** Malachite BFT (Tendermint-derived, Rust; Informal Systems team merged into Circle 2025). ~0.5s blocks, **deterministic finality in <1s** (no reorgs; one confirmation = final). **Proof-of-Authority now; transition to permissioned Proof-of-Stake planned 2027.** Consensus↔execution boundary = standard Ethereum **Engine API** (IPC or HTTP), forkchoiceUpdated/newPayload/getPayload.
- **Execution layer:** **Reth-based** (Rust Ethereum client) customized for Arc — repo: `circlefin/arc-node`, crates include execution layer, custom txpool, payload builder, evm. Full Solidity/Foundry/Hardhat/viem/wagmi compatibility out of the box. **Quirk (community-sourced, two independent dev repos):** compile with `evmVersion: "paris"` — Solidity ≥0.8.20's default Shanghai emits `PUSH0`, which Arc rejects (`ESTIMATION_ERROR` / `Create2: Failed on deploy`). UNVERIFIED officially.
- **Chain IDs:** mainnet `5042` (0x13b2); testnet `5042002` (0x4CEF52).
- **Custom EVM precompiles** (from official repo docs/ARCHITECTURE.md, `crates/precompiles`):
  - `0x1800..0000` — **Native Coin Authority**: mint, burn, transfer of the native coin (the unlimited-minting extreme tier maps directly here)
  - `0x1800..0001` — **Native Coin Control**: address blocklist (OFAC-style compliance control — testnet only for probing)
  - `0x1800..0002` — System Accounting: gas fee ring buffer
  - `0x1800..0003` — **Call From**: preserves original `msg.sender` through nested calls; plumbing for native batch and **memo transactions** (predeployed Memo contract wraps a call + emits `Memo` event)
  - `0x1800..0004` — **PQ Signature Verify**: SLH-DSA-SHA2-128s post-quantum signature verification
- **Other protocol features:** StableFX (24/7 on-chain FX settlement across USDC/EURC/GBPA/JPYC/KRW1 — press), **CCTP + Gateway** interop with 20+ chains (**CCTP domain 26 for Arc — community-sourced, unverified**), 20+ native fiat stablecoins (USDC, EURC, JPYC, KRW1, TRYB…), tokenized assets (BlackRock BUIDL, Circle USYC natively), **opt-in privacy sector** (confidential transfers with view keys — "in development for network-wide release"; businesswire 2026-09-16), custom transaction mempool with pending-tx filter + InvalidTxList, RPC sync mode for light nodes.
- **Node topology:** full node / RPC node / consensus node; public RPC for mainnet is HTTP-only on Circle's endpoint (WS via third parties: Alchemy, Blockdaemon, QuickNode); testnet supports WSS on the primary endpoint per community docs (unverified officially).
- **ARC token:** genesis mint of 10B ARC completed at mainnet launch; **not publicly launched/in circulation** — gas is USDC.

## 3. Third parties & partners (from press/official announcements)

- **Validators (founding PoA set, permissioned):** BlackRock, DTCC, Galaxy Digital, ICE, Mastercard, MoneyGram, SBI Group, Standard Chartered, Sumitomo Corporation, Visa, Worldpay (11; some articles list 12 incl. Circle). DTCC plans tokenizing DTC-custodied assets on Arc (2027); BlackRock moving ~$2.87B BUIDL onto Arc.
- **Launch apps (>100 day-one):** Aave V4, Morpho, Uniswap; payments: Rain, Tunes, Wirex (Wirex One neobank, day-one); Ripple day-one partner for Open USD.
- **Wallets/venues:** Kraken, MetaMask, Binance Wallet, Fireblocks, Ledger, Upbit.
- **Infra/RPC providers:** Alchemy, Blockdaemon, QuickNode, Chainstack, dRPC (third-party RPC/WS).
- **Explorers:** official `explorer.arc.io` (Blockscout) + `explorer.testnet.arc.io`; **Etherscan launched ArcScan at arc.etherscan.io** same day as mainnet (The Merkle); community mirror testnet.arcscan.app (unverified).
- **Consensus team:** Informal Systems (Malachite, Tendermint/IBC pedigree) joined Circle 2025.
- **Auditors:** NONE publicly named. Repo README: "alpha software currently undergoing audits" (as of Apr-2026 docs snapshot); Malachite README: "has not been externally audited; use at your own risk" (crawled 2026-09-25). No audit reports found publicly. Prior Circle precedent: Asymmetric Research audited/disclosed via bounty (noble-cctp infinite-mint, 2024).
- **Raise:** ARC token presale ~$222M at $3B valuation, led by a16z crypto with BlackRock, Apollo (UNVERIFIED — press).

## 4. Code & repos (all public GitHub)

- **github.com/circlefin/arc-node** — THE main repo (Rust). Contains: Execution Layer (Reth-based, `crates/node`, custom txpool `crates/execution-txpool`, payload builder, InvalidTxList), Consensus Layer (Malachite app integration, `crates/malachite-app`, libp2p P2P, RPC sync mode), EVM (`crates/evm`), **precompiles (`crates/precompiles`)**, **contracts** (system contracts, deployments, scripts), genesis configs (`assets/localdev/genesis.json`, `--chain=arc-testnet`), docs (ARCHITECTURE.md, running-an-arc-node.md, installation, ADRs), integration test framework (multi-node full-stack tests, crash/restart scenarios). **SECURITY.md → "report to Circle privately through Circle's Bug Bounty Program," no public GitHub issues for vulns.** NOTE: SECURITY.md currently links to hackerone.com/**circle-bbp** (Circle's older program) — arc-bbp is the Arc-specific program; use arc-bbp.
- **github.com/circlefin/malachite** — the BFT consensus engine (Rust, alpha, "not externally audited"). Informal Systems' repo under circlefin.
- **github.com/circlefin/arc-node** docs reference: `docs.arc.network/arc/references/*`, `docs.arc.network/arc/tutorials/*`.
- Ecosystem/community dev kits (unofficial, useful as reference clients): santozz-x/arc_dev_kit (network config from official docs), promanas0/archpulse, estmcmxci/signa-arc, yournahian/handshake ("use-arc" skills), vlsss12/arcinvoice, vasanthdev2004/kred, bela1401/arc-node-health-monitor.
- No official faucet/smart-contract monorepo found under circlefin beyond arc-node's contracts; token/bridge contracts for USDC-on-Arc are predeployed system addresses (see precompiles + `0x3600…0000` USDC).

## 5. Videos & writeups (publicly available)

- **"Why the Financial System Needs Arc"** — Jeremy Allaire's opening keynote at the Arc Mainnet launch event (NYC, 2026-09-16): https://www.youtube.com/watch?v=A4uiUaDhTuk
- **The Rollup: "Circle CEO: The Entire Financial System Is Coming Onchain"** — Allaire interview at the mainnet launch event (agentic finance, DTCC on Arc, $100T USDC transfer volume): https://www.youtube.com/watch?v=d2Vm2-uw110
- **CNBC FII 2025: "Circle CEO: We're building an economic operating system for the internet"** (Riyadh, 2025): https://www.youtube.com/watch?v=kGzlXORBslg
- **Circle official launch recap** (businesswire, 2026-09-16): https://www.businesswire.com/news/home/20260916108863/en/Circle-Launches-Arc-Mainnet-an-Economic-Operating-System-for-the-Internet
- **Seeking Alpha transcript** — Circle at Autonomous 2026 Future of Commerce Symposium (2026-09-22; Allaire: Arc "nearing $1B", fastest capital inflow): https://seekingalpha.com/article/4949372-circle-internet-group-inc-crcl-presents-at-autonomous-2026-future-of-commerce-symposium
- **Technical breakdown** (consensus/execution detail, Malachite + Reth + 0.5s blocks): https://www.odaily.news/en/post/5212985 ; https://www.panews.io/articles/01a0a089-0045-7655-96da-4aa43f5f9d09
- **Past disclosed reports for arc-bbp:** NONE found. Policy forbids public discussion of vulns without written consent; do not expect Hacktivity disclosure. Related precedent (Circle, not Arc): Asymmetric Research's noble-cctp infinite-mint writeup via Circle's bounty (2024): https://www.livebitcoinnews.com/circle-addresses-bug-that-could-have-led-to-millions-in-losses-if-exploited/
- Community "use-arc" skill docs and dev-kit READMEs (links in section 4) double as practical testnet guides.

## 6. Asset inventory (passive only — official sources only; mainnet rows are reference-only, NO testing)

**Official endpoints (from docs.arc.network/arc/references/connect-to-arc, fetched 2026-09-26):**
| Asset | Value | Status |
|---|---|---|
| Mainnet RPC (HTTP) | `https://rpc.mainnet.arc.io` | Official; NO testing allowed |
| Mainnet explorer | `https://explorer.arc.io` (Blockscout) | Official; reference only |
| Mainnet chain ID | 5042 | Official |
| Testnet chain ID | 5042002 | Official (via ArcScan/e2e docs) |
| Faucet | `https://faucet.circle.com` | Official Circle; public, permissionless; select "Arc Testnet" (faucet step per community docs — official page only says testnet USDC/EURC on all supported blockchains) |
| Policy scope | `*.arc.io` | Tier B (web) |

**Community-sourced (UNVERIFIED — confirm against docs.arc.network testnet page before use):**
- Testnet RPC: `https://rpc.testnet.arc.io` (or `.arc.network`); WSS `wss://rpc.testnet.arc.io`
- Testnet explorer: `https://explorer.testnet.arc.io` (official arc.io subdomain per one community doc) / `https://testnet.arcscan.app` (Blockscout mirror)
- USDC ERC-20: `0x3600000000000000000000000000000000000000` (6 decimals)
- EURC: `0x89B50855Aa3bE2F677cD6303Cec089B5F319D72a` (6 decimals)
- CCTP domain for Arc: 26
- Predeployed Memo contract + Call From precompile `0x1800..0003`

**Local devnet (policy-approved):** `assets/localdev/genesis.json` in arc-node; run EL+CL locally, get full control without touching shared infra — the cleanest route for deep protocol testing.

## 7. Hypothesis seeds (all testable on Arc TESTNET or LOCAL DEVNET only)

**H1 — Native Coin Authority mint/burn privilege (`0x1800..0000`)**
Hypothesis: the mint path of the native-coin precompile is reachable beyond the intended caller (e.g., missing caller-allowlist check or confused-deputy via Call From `0x1800..0003` preserving msg.sender), enabling testnet unlimited minting.
Why this target: policy's Extreme tier literally lists "Unlimited minting"; precompile is custom code (not battle-tested EVM); Call From explicitly preserves msg.sender, a classic confused-deputy primitive.
Expected observation: calling the mint entrypoint from an unprivileged EOA/contract on testnet increases native USDC balance without corresponding burn/deposit; or a contract calling through Call From can impersonate the authority.
Vuln class: access-control failure / confused deputy → token-minting logic flaw. Note: only demonstrate on testnet; frame mainnet impact by code parity (same bytecode/genesis logic).

**H2 — Dual-decimal (6 vs 18) accounting inconsistency between native view and ERC-20 view**
Hypothesis: the ERC-20 interface (`0x3600…0000`, 6 dp) and the native 18-decimal balance drift — e.g., a path (gas refunds, fee burn/treasury split, failed-tx rollback) updates one view without the 10^12 conversion on the other, creating or destroying value.
Why this target: custom dual-representation is Arc-unique; official docs explicitly warn integrators about it (high bug surface); treasury fee split + ring buffer accounting add more conversion points.
Expected observation: after a sequence (send native, wrap/unwrap-equivalent call, pay fees), `nativeBalance/1e12 ≠ erc20Balance` for the same account, or totalSupply of the ERC-20 view ≠ sum over native accounts.
Vuln class: accounting/precision bug → funds creation/loss.

**H3 — Fee-model edge cases: zero/negative effective gas price**
Hypothesis: the weighted-moving-average base fee + USDC-denominated fees mis-handle edge cases — e.g., priority fee in a different decimal view, zero-fee txs accepted, or fee underpayment due to 18-vs-6 conversion when gasPrice is charged from the native balance.
Why this target: custom base-fee logic (not stock EIP-1559); native coin is also the gas coin, so fee deduction and balance checks share the dual-decimal surface.
Expected observation: a testnet tx with gasPrice below the documented minimum is included, or fee charged ≠ gasUsed × gasPrice in USDC terms, or a zero-value account can spam blocks at zero cost.
Vuln class: economic/fee-logic flaw; if it enables free blockspace → testnet-only DoS-adjacent (note policy bans service disruption — demonstrate fee arithmetic, don't flood).

**H4 — Faucet abuse / rate-limit bypass (Tier B web, low severity but real)**
Hypothesis: faucet.circle.com's per-address/IP limits for Arc Testnet can be bypassed (IP rotation, address generation, API parameter tampering), allowing unlimited testnet USDC minting → pollutes testnet state and enables mass Sybil txs.
Why this target: official faucet is public/permissionless; testnet USDC is the gas token, so faucet economics directly gate testnet security.
Expected observation: N+1 successful drips to fresh addresses from the same source within the stated limit window.
Vuln class: rate-limit/bypass. Keep volume tiny and stop at proof of bypass (policy: don't degrade service).

**H5 — Txpool admission vs block-inclusion divergence (mempool edge)**
Hypothesis: custom txpool validation (gas checks, pending-tx filter, InvalidTxList) diverges from the executor's actual rules, so a tx accepted by `eth_sendRawTransaction` is silently dropped, or a tx the pool rejects is constructible in a block — breaking fee markets or enabling cheap censorship.
Why this target: custom txpool crate + custom validation logic + policy bans "testing on mainnet," so local devnet + public testnet RPC observation is the legit route.
Expected observation: tx hash returned by public testnet RPC never appears in blocks (mempool blackhole), or a nonce/fee edge-case tx is included despite RPC-level rejection.
Vuln class: mempool/logic inconsistency → DoS-adjacent or fee evasion. (Do NOT load-test; single txs only.)

**H6 — Address blocklist (`0x1800..0001` Native Coin Control) bypass**
Hypothesis: the compliance blocklist is enforced at only one layer (e.g., ERC-20 `transfer` but not native sends, or not on the Call From / memo paths), so a blocklisted address can still move funds via the unenforced path.
Why this target: blocklist is a stated native feature; partial enforcement is the classic failure mode; testnet-safe (blocklist yourself, move test funds).
Expected observation: after adding a controlled address to the testnet blocklist (if permission allows) — or observing genesis blocklist behavior — a native transfer succeeds where ERC-20 transfer reverts, or vice versa.
Vuln class: authorization-bypass → compliance-control failure. Mark as compliance-relevant; Circle cares (NYDFS-regulated).

**H7 — `eth_estimateGas`/RPC gas-estimation divergence (PUSH0/evmVersion quirk)**
Hypothesis: Arc's rejection of PUSH0 (Shanghai) or other Osaka/EVM config overrides causes `eth_estimateGas` to succeed where deployment later fails (or vice versa), letting attackers craft txs that waste block gas or brick contract factories relying on estimation.
Why this target: two independent community sources confirm PUSH0 rejection; custom EVM config overrides in `crates/evm`.
Expected observation: estimation returns success but on-chain deployment reverts with `ESTIMATION_ERROR`, or a CREATE2 factory behaves differently on estimation vs execution.
Vuln class: RPC/logic inconsistency → gas griefing / reliability. Testnet only.

**H8 — CCTP domain-26 message handling (bridge surface)**
Hypothesis: Arc's CCTP integration (domain 26, community-sourced) accepts malformed or replayed cross-chain messages on testnet — e.g., attestation verification gap or domain confusion between Arc testnet and other CCTP domains — crediting test USDC without a matching burn.
Why this target: Circle's own history — the Asymmetric Research noble-cctp infinite-mint was exactly a message-sender verification flaw in CCTP; Arc adds a NEW domain with NEW precompiles.
Expected observation: a crafted testnet CCTP receive mints testnet USDC without a corresponding source-chain burn (construct the message manually against testnet attestation service, or find the MessageTransmitter accepts unsigned/duplicate attestations).
Vuln class: bridge message-verification flaw → unlimited minting (Extreme tier). STRICTLY testnet; never touch real attestation service keys or mainnet CCTP.

**H9 — Call From (`0x1800..0003`) + Memo contract msg.sender spoofing**
Hypothesis: because Call From preserves the original msg.sender through nested calls, a malicious contract can launder its identity into downstream calls — e.g., tricking an allowance/identity check that assumes msg.sender == direct caller, or forging Memo events attributed to another user.
Why this target: preserving msg.sender across call boundaries breaks a core EVM invariant; the Memo contract is predeployed and wraps arbitrary inner calls.
Expected observation: on testnet, contract A routes through the Memo/Call From path and contract B observes msg.sender = victim EOA (not A); a Memo event is emitted with attacker-chosen content attributed to the victim.
Vuln class: authentication/identity spoofing → phishing-grade impact on any Arc-native protocol relying on msg.sender through memos.

**H10 — Engine API / consensus-RPC exposure on public nodes**
Hypothesis: some public Arc RPC operators expose the Engine API (port 8551) or consensus RPC (port 31000) without JWT auth, or the "unsafe RPC node" mode is reachable — allowing payload injection or node manipulation on testnet.
Why this target: node README documents "Unsafe RPC Node" mode, `--enable-arc-rpc` flag, and Engine API over IPC/HTTP; misconfigurations are the #1 node-ops finding class; purely passive check = attempt a single unauthenticated `engine_` call against PUBLIC testnet RPC hostnames from docs — if rejected, done.
Expected observation: unauthenticated engine API responds (fail-closed expected: 401/invalid JWT).
Vuln class: exposed admin API → chain-halt risk if a validator node were affected (Tier A Extreme adjacent). CAUTION: only query documented public RPC endpoints; never brute-force ports/IPs (that crosses into scanning — policy's safe harbor covers good-faith testing, but keep it to one benign call per documented endpoint).

---

### Open questions / caveats (2026-09-26)
- Smart-contract bugs ARE in scope (Tier A explicitly covers "chain / system-contract flaws with direct fund losses"); only MAINNET testing is banned. Test on testnet/devnet and argue mainnet impact via code parity.
- Auditors: none publicly named; Malachite README says unaudited (Sept 2026) — this is either stale or a genuine finding-gap; treat Malachite as the least-reviewed component.
- arc-bbp appears to be a newer/split program; arc-node SECURITY.md still points to circle-bbp — use arc-bbp for Arc findings.
- Several testnet constants (USDC address, CCTP domain 26, PUSH0 rejection, testnet RPC hostnames) are community-sourced, not official — verify against docs.arc.network testnet pages + on-chain state before building PoCs.
