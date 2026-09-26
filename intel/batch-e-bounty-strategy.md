# Batch E — Bounty strategy & meta-intel (ingested 2026-09-26)

Strategy-level reading for the hunter agent: where the industry is going, how to
spend tokens, which platforms to trust, what tooling posture wins. No exploits.

---

## 1. hakluke — "Are bug bounties cooked?"
https://hakluke.com/are-bug-bounties-cooked

**Takeaways**
- AI is the quartz crisis of hacking: bug discovery got cheaper/faster/easier, so
  bug *supply* rose while demand stayed flat → prices for known bug classes fall.
- The frontier models don't need your submission data to find bugs; your edge is
  *methodology*, not individual reports. Keep methodology close.
- AI favors attackers: same underlying models on both sides, but attackers run
  scrappy/cheap setups with no compliance overhead.
- 1,000 diverse human brains still beat one LLM brain — diversity of approaches is
  the durable advantage. Dupes come from everyone pointing the same AI at the same
  low-hanging fruit.
- Verdict: not cooked. Adapt like Swatch: use AI in ways others aren't, find new
  bug classes, hunt the edges AI doesn't cover.

**Tactics**
- Don't run the zero-barrier prompt ("find vulns in this scope") — that's where
  the dupes live. Point AI at unmapped endpoints, second-order interactions,
  newly shipped features.

---

## 2. hakluke — "How to start (or come back to) bug bounties in 2026"
https://hakluke.com/how-to-start-or-come-back-to-bug-bounties-in-2026

**Takeaways**
- AI is now a core tool like Burp; hunting without it is a serious disadvantage.
- Always chase HIGH/CRITICAL: ATO, auth bypass, SSRF with real reach, IDORs at
  scale, RCE. Mediums are side-effects, never the goal.
- Medium is slop for writeups now. Learn from: Critical Thinking podcast,
  PortSwigger research, Shubs/Searchlight, X/Twitter, r/netsec, r/bugbounty.
- Foundations still matter: PortSwigger Web Security Academy (free, do the labs),
  HackingHub (run by actual earners).

**Tactics**
- THE key tactic: **make AI build deterministic tools, not do chores.** Every
  repetitive reasoning task should become a tool/skill. That library of tools is
  your edge — exactly the hunter-agent architecture. Saves tokens and thinking
  time at scale.
- Reports: let AI polish, but the technical claims must be yours and correct.

---

## 3. teknogeek — "What Happened to HackerOne?"
https://blog.teknogeek.io/posts/what-happened-to-hackerone/

**Takeaways**
- HackerOne shifted from hacker-first to sales-first after VC pressure (~2020+):
  capacity-based fees, multi-year lock-ins, triage quality declined, platform
  stagnated, founders sidelined.
- Feb 2026 ToS drama: reports usable for AI training (co-founder publicly denied
  training on researcher data; trust split).
- Hacker Success Program helps top hackers but creates a lopsided field for
  newcomers — advocacy is paywalled behind reputation.

**Tactics**
- Diversify platforms: don't build your whole operation on HackerOne. Intigriti
  (EU-strong), Bugcrowd, YesWeHack all deserve programs in the pipeline.
- Program selection matters more than ever: low-quality program flood + weak
  triage = wasted effort. Prefer programs with responsive triage and clear scope.

---

## 4. ret2p.lt — "The Future: AI Sovereignty, Vuln Research, Bug Bounty"
https://ret2p.lt/2026/08/10/ai-vuln-research-future.html

**Takeaways**
- Frontier cyber models get lobotomized or gated (Opus 4.6 → Mythos restrictions,
  OpenAI TAC, Anthropic CVP with mandatory data retention). Don't build your
  workflow on access that can be revoked or used to train on your findings.
- AI sovereignty: self-host open-weight models so you own your data and methods.
  Local hosting is viable (DeepSeek v4 Flash on ~192GB RAM + decent GPU).
- Alternatives exist: abliterated.ai, adversarial.ai (CyberKimi, no KYC), GLM 5.2,
  DeepSeek — cheaper than US frontier, fewer restrictions.

**Tactics**
- The harness matters more than the model: RAG over your own corpora (writeups,
  books, past transcripts), good prompt scaffolding, Python tooling.
- Build your own fine-tune corpora from public writeups; keep findings local.

---

## 5. FuzzingLabs — Le Hack 2026 keynote: "No need to be a Mythos"
(Patrick Ventuzelo; PDF slides)

**Takeaways**
- You don't need the classified frontier model. Mythos on curl: 15 "confirmed"
  findings → 1 LOW CVE (3 FPs, 1 non-bug). Earlier AI tools (AISLE, Zeropath,
  Codex Security) produced 200–300 bugfixes / ~12 CVEs over 8–10 months.
- Public models reproduced Mythos findings at <$30/file. Small models repeated
  beat big models on cost (21× Flash Lite scans per Opus scan).
- "The moat is moving up the stack — from model access to validation,
  prioritization, and remediation."

**Tactics — building blocks of a Mythos-equivalent**
- MEMORY: RAG knowledge base of past findings, CVEs, tool outputs, notes.
- TOOLS: MCP servers (WireMCP, Ghidra-MCP, RedTeam-MCP), fuzzers, disassemblers.
- MODELS: openweight (Gemma, Qwen, Hermes, GLM) — finetunable with Unsloth/Axolotl.
- HARDWARE: <$10K workstation (DGX Spark, Mac Studio, Ryzen AI Max+) replaces
  $200K/yr of 2024 compute.
- This is the blueprint the hunter-agent is following: memory + tools + cheap
  models, not one expensive brain.

---

## 6. Semgrep — "We have Mythos at Home: GLM 5.2 beats Claude in cyber benchmarks"
https://semgrep.dev/blog/2026/we-have-mythos-at-home-glm-52-beats-claude-in-our-cyber-benchmarks

**Takeaways**
- GLM 5.2 (open-weight, MIT, Zhipu AI) scored 39% F1 on IDOR detection vs 32%
  for Claude Code — at ~$0.17 per vuln found, ~1/6th the cost.
- Harness > model: biggest gap was endpoint-discovery scaffolding vs bare prompt.
- Open weights crossed a real threshold; don't put all eggs in one LLM basket.
- IDOR is #4 on HackerOne's top vuln types — still a top-tier target class.

**Tactics**
- Per-bug economics decide what's usable at scale. Cheap open models + good
  harness beats expensive frontier on cost-adjusted results.
- For the hunter: IDOR remains a primary hunt class; GLM-class models are viable
  analysis backends when the OpenAI key has no quota.

---

## 7. nuclei v3.9.0 release notes
https://github.com/projectdiscovery/nuclei/releases/tag/v3.9.0

**New flags/features relevant to safe bounty scanning**
- **Protocol redirects support** — templates can now follow redirects across
  protocols. Useful for takeover/redirect-chain detection; keep scope tight
  since cross-protocol follows can wander.
- **DNS variables resolving fix** — fewer false negatives on DNS-based templates
  (takeover fingerprints, subdomain checks). Worth upgrading for this alone.
- impacket integration + wmi/tsch/scmr/dcom JS helpers — enterprise Windows
  protocol testing; not web-bounty relevant, skip.
- Bug fixes: JS runtime interrupt handling, reporting (jira/gitlab), template
  loader warnings for `.nuclei-ignore` exclusions.

**Tactics**
- Upgrade the hunter's nuclei to v3.9.0 (DNS fix + redirect support).
- Safe-scan posture unchanged: `-severity info,low,medium,high,critical`,
  exclude `dos,fuzz,intrusive` tags, `-rl` rate limit, in-scope targets only.

---

## 8. Intigriti — Best Security Company 2026 (SC Awards Europe)
https://www.intigriti.com/blog/awards/intigriti-named-best-security-company-of-2026-at-the-sc-awards

**Takeaways**
- Intigriti won Best Security Company (<250 employees) at SC Awards Europe 2026;
  positioned as Europe's largest crowdsourced security platform, EU-rooted
  operations/compliance.

**Tactics**
- Platform diversification: Intigriti is the credible EU alternative to
  HackerOne/Bugcrowd. Worth opening programs there alongside HackerOne —
  different program pool, often less picked-over.

---

## 9. Intigriti — Leo Racanelli on securing AI systems
https://www.intigriti.com/blog/business-insights/securing-the-uncharted-territories-of-ai-systems-a-discussion-with-leo-racanelli

**Takeaways**
- AI features in scope are prime targets: chatbots, prompt-injection surfaces,
  natural-text input that can't be sanitized like normal params. Companies rush
  AI to market without security review.
- AI as teammate > AI on autopilot: collaborative use finds new bug classes the
  hunter wouldn't have tried.
- Token price wall is the new barrier to entry — "bug bounty is no longer free
  to participate competitively." Spend tokens where they multiply skill.

**Tactics**
- Keep a markdown playbook (Obsidian-style) of findings AND dead ends per target
  so the AI doesn't re-pursue failed paths — mirrors the hunter's intel/ + notes
  design. Log what was tried and ruled out.
- When a program has a chatbot/AI feature in scope, open the prompt-injection
  and AI-security notes first (OWASP GenAI, invisible-prompt-injection refs).

---

## 10. FirefUXSS — Universal XSS in Firefox Focus for iOS (v12-security)
https://github.com/v12-security/pocs/tree/main/firefox

**Takeaways**
- 0-day UXSS via TOCTOU race in redirect-scheme validation: flood the redirect
  handler with HTTP→HTTP redirects, slip a `javascript:` redirect through the
  validator, script executes in the previous document's origin. CVSS 9.3.
  Unpatched after 11-month disclosure.
- Open redirects are the pivot ingredient — they're everywhere and trivial to
  find; the novel part was the validation race.

**Tactics (research pattern, not a payload)**
- Hunt TOCTOU in security checks: any validation that isn't atomic with the
  action it guards (scheme checks, auth checks, rate limits) is raceable.
- Mobile browsers / webviews are under-hunted attack surface vs desktop.

---

## 11. dungnm.hashnode.dev — "Pwn2Own with Microslop"
https://dungnm.hashnode.dev/pwn2own-with-microslop
- FETCH FAILED (upstream fetch error, not retried per policy). Not ingested.

---

## Cross-batch strategic summary
1. Harness > model; tools > prompts. Build deterministic tools once, invoke cheap.
2. Hunt where AI doesn't: unmapped endpoints, new features, novel bug classes.
3. Diversify: models (open-weight), platforms (Intigriti alongside HackerOne),
   data (self-hosted, own your findings).
4. Chase high/critical impact only; mediums are side-effects.
5. Log dead ends per target — the playbook of what failed is as valuable as hits.
