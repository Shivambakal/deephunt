# AI-Security Books — Deep-Read Dossier (2026-09-27)

Mission: "read all" six AI-security titles from legal public sources; extract offensive
technique knowledge; ingest what is genuinely novel into DEEPHUNT. Read-only research —
no system was probed.

## Verification verdicts

| # | Title | Verdict |
|---|-------|---------|
| 1 | *Practical AI Security* — Harriet Farlow, No Starch Press, Jun 2026, ISBN 9781718504660 | **REAL, verified** — publisher page, full ToC PDF, full index PDF, free Ch.3 sample |
| 2 | *Adversarial AI Attacks, Mitigations, and Defense Strategies* — John Sotiropoulos, Packt, Jul 2024, ISBN 9781835087985 | **REAL, verified** — Packt page, full ToC, free ch.1 + backdoor teaser, distilled-chapter analysis |
| 3 | *AI Under Attack* — Kris Kimmerle & David Okeyode, Packt, copyright 2026, ebook ISBN 9781806119929 | **REAL but pre-release** — no chapter ToC, no reviews, no excerpts public; parts + toolkit list only |
| 4 | *HACKING LLM-POWERED SYSTEMS* — "field guide to weaponizing prompt injection" | **REAL but unvetted KDP self-pub** — Amazon UK listing only (£14.19); no author name, no ISBN, no publisher trace on Goodreads/O'Reilly/No Starch/Packt. Treat as purchasable-but-unverified, not an established resource |
| 5 | *Prompt Injection and LLM Security* — "Glenn Derick" | **LIKELY HALLUCINATED** — no book, no author page, no retailer listing under any spelling; "Glenn Derick" is not a real security author. The phrase exists only as a Lakera research-topic label |
| 6 | *The Loop* — Jacob Ward, Grand Central 2022, ISBN 9780316487184 | **REAL, verified** — but societal/behavioral AI journalism, not offensive security. Relevance note only (see §6) |

Substitute titles for the debunked #5: Steve Wilson *The Developer's Playbook for Large Language
Model Security* (O'Reilly 2024 — Wilson led the OWASP LLM Top 10 project);
Springer *Jailbreaking LLMs: Protecting the Future of Enterprise Security* (2025);
Ram Shankar Siva Kumar & Hyrum Anderson *Not with a Bug, But with a Sticker* (Wiley 2023);
Randall Tr's free *AI Hacking for Beginners* GitHub playbook (prompt-injection/jailbreak field guide).

## Primary sources read directly and fully

- **OWASP LLM Top 10 2025** (genai.owasp.org; LLM01 page read in full, LLM02–LLM10 cross-verified
  from three independent sources quoting the official release; published Nov 18, 2024).
  Ten categories, with two genuinely new: **LLM07 System Prompt Leakage** and **LLM08 Vector and
  Embedding Weaknesses**. Renumbered/renamed: LLM02 Sensitive Information Disclosure,
  LLM03 Supply Chain (expanded), LLM04 Data and Model Poisoning, LLM05 Improper Output Handling,
  LLM06 Excessive Agency (rewritten for action-capable agents), LLM09 Misinformation (expanded
  from Overreliance), LLM10 Unbounded Consumption (now covers cost drain, runaway agents, model-theft
  economics). Removed as standalone: 2023's Insecure Plugin Design (absorbed into LLM06) and
  Model Theft (absorbed into LLM10 + LLM03). Prompt injection stays #1; indirect/multimodal
  injection explicitly in scope.
- **MITRE ATLAS v2026.09** (atlas.mitre.org + canonical atlas-data repo): 16 tactics
  (incl. AI-specific *AI Model Access* and *AI Attack Adaptation*), 120 techniques + 88
  sub-techniques, 40 mitigations, 73 case studies. Each technique carries an evidence rating
  (Feasible / Demonstrated / Realized — 101 Realized). Official site is a JS SPA; technique
  detail corroborated from MITRE's canonical data repo via pinned third-party mirrors.

---

## Book 1 — *Practical AI Security* (Farlow, No Starch, 2026)

**What it is:** The most hands-on of the three verified books — 30 Python/Colab notebooks, each
attack chapter paired with a runnable demo. Framing device: AI security as a *systems* problem
("Stop securing the model. Secure the system instead" — her DEF CON 2026 talk title).

**ToC (from nostarch.com/download/resources/practical-ai-security_TOC.pdf):**
Part I — Ch.1 What Is AI? · Ch.2 Working with Models (incl. agents, MCP/A2A protocols, RAG) ·
Ch.3 AI Threats (MITRE ATLAS + OWASP worked example; MAESTRO 7-layer analysis of MCP; threat actors).
Part II — Ch.4 Attacks and Weaknesses (FGSM & PGD, adversarial patch, Carlini–Wagner, data
poisoning, backdoors incl. "skeleton key attack", direct/indirect prompt injection, membership
inference, model extraction incl. logprobs-based, side-channels incl. LeftoverLocals, RAG attacks,
supply-chain, agent risks) · Ch.5 Defenses (adversarial training, gradient obfuscation, randomized
smoothing, certified defenses, defensive distillation, ensembles, statistical detection; real-world
attack case studies: facial-recognition bypass with/without liveness, MathGPT inference DoS,
malicious Colab notebooks, malware-detector bypass, metamorphic ransomware).
Part III — Ch.6 Red Teaming AI (three executed test cases: prompt injection via OpenAI SDK,
prompt fuzzing with PyRIT's SinglePromptAttack, multi-turn Crescendo-style attacks; "chains of
techniques", differential trust profiles, economic DoS, permission hijacks; tools: PyRIT, Gandalf,
JailbreakChat, TensorTrust, HackerPrompt) · Ch.7 Attacking and Defending with AI (AI-accelerated
vuln discovery, FraudGPT/WormGPT, deepfake-as-a-service, voice-clone BEC, ReaperAI autonomous
agents, DARPA AIxCC, Common Crawl poisoning) · Ch.8 AI Safety (jailbreak/harm benchmarks as attack
oracles: AdvBench, JailbreakBench, AgentBench, CyBench; mechanistic interpretability) ·
Ch.9 Governance (AIVSS scoring, rapid risk audits) · Ch.10 What's Next (protocol confusion attacks,
Agent Name Server, open vs closed weights).

**Named prompt-injection variants taught (Ch.4, p.133–140):** direct attacks, overriding
instructions, persuasion, roleplaying, multiturn, contextual hijacking, format injection, token
smuggling, self-referential prompts, contradictions, low-resource-language payloads.

**Real incidents cited (sample Ch.3, pp.75–98):** Lloyds Bank Voice ID bypass via ElevenLabs
(2023); Hluhluwei anti-poaching AI cameras bypassed, 4 rhinos killed (2020); Chevrolet dealership
chatbot sold a Tahoe for $1 via prompt injection (Dec 2023); UK energy firm deepfake voice BEC,
~£220,000 (2020); Palo Alto ML C2-detector evaded by stripping HTTP headers; Microsoft AI Red Team
disrupting an Azure AI service with adversarial examples; Forest Blizzard targeting AI research
infrastructure; DeepSeek/OpenAI IP dispute (2025); Tay.

**Access gaps:** only Ch.3 legally free as sample; Ch.4–10 mechanics reconstructed from detailed
ToC + index + secondary analysis (Undercode Testing). No Reddit/Goodreads deep reviews yet
(book ~3.5 months old).

---

## Book 2 — *Adversarial AI Attacks, Mitigations, and Defense Strategies* (Sotiropoulos, Packt, 2024)

**What it is:** The broadest classical-ML coverage of the three (586 pp) — poisoning, evasion,
privacy attacks, trojans — plus a GenAI part. Author is an OWASP LLM Top 10 co-lead, OWASP AI
Exchange core member, US AI Safety Institute Consortium OWASP lead, Head of AI Security at Kainos.

**ToC (Packt + Legimi full ToC):** Part 1 (Ch.1–3) foundations/lab; Part 2 (Ch.4–6) model
development attacks — Ch.4 Poisoning (targeted/untargeted, backdoor trigger+label-flip, clean-label
PGD/feature-collision, hidden-trigger via ART, gradient-aware poisoning), Ch.5 Model Tampering
(pickle deserialization RCE, Keras Lambda layers, custom layers under benign names, neural payload
injection, edge weight tamper, model hijacking wrappers, model reprogramming), Ch.6 Supply Chain
(pre-trained model poisoning from hubs, transfer-learning backdoors, live-data poisoning of online
learners, dependency confusion, unpinned Docker bases, missing SBOM); Part 3 (Ch.7–10) deployed
AI — Ch.7 Evasion (FGSM, BIM, JSMA, Carlini–Wagner, PGD, adversarial patches, UAPs, TextAttack NLP
evasion, black-box transferability via surrogate), Ch.8 Extraction (functionally-equivalent,
learning-based substitute, generative student-teacher distillation), Ch.9 Data theft (model
inversion incl. GAN-assisted, attribute inference incl. poisoning-assisted, membership inference:
statistical, label-only, blind, white-box), Ch.10 privacy defenses; Part 4 (Ch.11–16) GenAI —
Ch.12 Weaponizing GANs (deepfake face/voice, biometric evasion, liveness bypass, GAN password
cracking), Ch.14 Adversarial prompts (direct, override, style injection, roleplay, impersonation,
GCG adversarial suffixes, BYOD, indirect PI; escalation to exfiltration, privilege escalation,
RCE; jailbreak vignettes: "system down for maintenance" functional DoS, "grandma's napalm bedtime
stories"), Ch.15 LLM poisoning (RAG embedding poisoning — during embedding generation, direct,
advanced; query-embedding manipulation; fine-tuning poisoning incl. worked ChatGPT-3.5 fine-tune
poisoning), Ch.16 Advanced GenAI (publishing poisoned/tampered LLMs on Hugging Face; LLM inversion,
training-data extraction, inference attacks, model cloning via secondary model); Part 5 (Ch.17–19)
threat modeling, MLSecOps, SBOMs, NIST/ATLAS mappings.

**Access gaps:** Packt+ locks all but Ch.1 + backdoor teaser; Legimi exposes ToC + front matter;
Ch.8–9/11–16 detail reconstructed from subsection titles + distilled-chapter analysis. The book
leans on lab-built attacks (its own CIFAR-10 CNN, ChatGPT-3.5 fine-tune poisoning) rather than
named breach case studies; only hub account takeovers verified as book-cited real incidents.

## Book 3 — *AI Under Attack* (Kimmerle & Okeyode, Packt, copyright 2026)

**What it is:** Governance-flavored practitioner guide — strongest on threat modeling, GRC
(NIST AI RMF, ISO 42001), SecOps, and agent authority assessment. Ships with an "AI Under Attack
Practitioner Toolkit": prompt-injection testing checklists, RAG & memory risk reviews, agent
authority assessments, model supply-chain checks, red-teaming and IR artifacts.

**Structure (parts only — chapter ToC not public):** (1) Foundations (threat modeling, attack
surfaces); (2) Attacks (system anatomy vectors, data/models, prompt injection, memory, RAG,
agents, red teaming & evaluation); (3) Secure design/deploy (MLOps hardening, APIs, defensive
prompting, agent security, supply-chain integrity, Zero Trust); (4) Operationalizing (GRC, SecOps,
safety/alignment, AI-driven misinformation); (5) Sustainable AI security programs.

**Offensive content (reconstructed from parts + toolkit artifact list):** direct/indirect prompt
injection; jailbreaks (roleplay, fictionalization, encoding, multi-turn escalation);
**memory & context abuse** (poison agent thread memory so goals persist across sessions);
**RAG vulnerabilities** (user-writable vector stores → persistent stored injection for all users);
**agent exploitation / tool abuse**; training-data poisoning via feedback loops; model supply-chain
(hub backdoors); AI red-teaming methodology as the capstone.

**Access gaps:** pre-release — Goodreads 0 ratings, no reviews, no excerpts; no incident names
public ("real-world scenarios" claimed only). Weakest of the three for offensive depth;
strongest for governance/reporting language.

---

## Book 4 — *HACKING LLM-POWERED SYSTEMS* (unvetted KDP)

Amazon UK listing: *HACKING LLM-POWERED SYSTEMS: Prompt Injection, Jailbreak Techniques,
Hallucination Exploitation, and AI Agent Misalignment for Security Professionals — With a 30-Day
Hands-On Red Team Project* (£14.19). Subtitle matches the list's description (prompt injection,
jailbreaks, agent threat behavior, hands-on red-team project). No author, ISBN, or publisher trace
anywhere else. All signals point to self-published KDP — buy-at-own-risk; do not cite as an
established source. Its niche (hands-on prompt-injection/jailbreak field guide) is better served
by Randall Tr's free *AI Hacking for Beginners* GitHub playbook or Steve Wilson's O'Reilly book.

## Book 5 — *Prompt Injection and LLM Security* ("Glenn Derick")

**Debunked.** Exhaustive negative searches: no book, no author page, no retailer listing under
any spelling; "Glenn Derick" is not a real security author. The phrase exists only as a Lakera
research-topic label — the list generator appears to have confused a topic page into a book title
and invented an author. Dropped entirely.

## Book 6 — *The Loop* (Jacob Ward, 2022)

Societal/behavioral AI journalism (Grand Central, ISBN 9780316487184): how AI systems exploit
cognitive biases and narrow human choice — biometric surveillance in India, social-credit
mechanisms, automated battlefield decisions, predictive-policing feedback loops (more policing →
more recorded crime → more policing). **Relevance to the hunt: zero offensive techniques.**
One useful mental model for DEEPHUNT's world-model reasoning: feedback loops where a system's own
outputs become its future inputs (applies to RAG corpora, fine-tuning feedback, agent memory).
Deprioritized — do not buy for bounty purposes.

---

## What DEEPHUNT already knew vs what's new

Already covered by cards AI-01…AI-12: indirect prompt injection (×2), system-prompt leakage,
tool abuse, LLM output handling, RAG ACL bleed, excessive agency, unicode smuggling, unbounded
consumption/DoW, stored injection via agent memory, tool-chain SSRF, query-oracle model extraction.

**Genuinely new material ingested as cards AI-13…AI-26 (14 cards):**

| Card | Technique | Source |
|------|-----------|--------|
| AI-13 | Multi-turn gradual-escalation jailbreak (Crescendo-style) | Farlow Ch.6; ATLAS T0054 |
| AI-14 | Triggered/dormant indirect prompt injection | ATLAS T0051.002 |
| AI-15 | RAG retrieval poisoning via embedding manipulation (PoisonedRAG) | Sotiropoulos Ch.15; ATLAS T0066/T0070; LLM08 |
| AI-16 | Fine-tuning API poisoning of shared/production models | Sotiropoulos Ch.15; LLM04 |
| AI-17 | MCP tool-description / registry poisoning | ATLAS T0010.005; CS0053/CS0045; Farlow MAESTRO/MCP |
| AI-18 | Poisoned model-hub artifacts (PoisonGPT-style backdoored weights) | Sotiropoulos Ch.5/6/16; ATLAS CS0019; LLM03 |
| AI-19 | Malicious model-file execution (pickle RCE, Lambda-layer trojans) | Sotiropoulos Ch.5; Farlow Ch.3 p.95 |
| AI-20 | Privacy attacks on inference APIs (membership/attribute inference, inversion) | Sotiropoulos Ch.9; Farlow Ch.4 |
| AI-21 | LLM distillation cloning via API scraping | Sotiropoulos Ch.8/16; ATLAS CS0056; LLM10 |
| AI-22 | Adversarial evasion of ML classifiers (FGSM/PGD/patch, transferability) | Sotiropoulos Ch.7; Farlow Ch.4–5 |
| AI-23 | Side-channel leakage from shared AI hardware (LeftoverLocals, timing, neural fingerprinting) | Farlow Ch.4 |
| AI-24 | Deepfake presentation attacks on biometric/KYC flows | Sotiropoulos Ch.12; Farlow Ch.5/7 |
| AI-25 | Agent-to-agent covert channels / emergent coordination abuse | ATLAS T0118; Jun 2026 DSEWiki incident |
| AI-26 | Persona manipulation / roleplay jailbreak | Farlow Ch.4; Sotiropoulos Ch.14 |

**New historical cases CASE-20…CASE-27 (8):** EchoLeak (CVE-2025-32711, zero-click Copilot
exfiltration); PoisonGPT (Hugging Face backdoor); Morris II (self-replicating RAG worm);
Chevrolet dealership $1-Tahoe prompt injection; Claude distillation campaigns; iProov deepfake
KYC bypass; ChatGPT package-hallucination exploitation; Lloyds Bank voice-ID bypass via
ElevenLabs (2023). Each carries `why_scanners_missed_it`.

Deliberately NOT added as cards (already covered or methodology, not vuln classes): system-prompt
extraction variants (AI-02 covers), cost harvesting (AI-09 covers), direct/indirect PI basics
(AI-01/AI-04 cover), red-team process (not a vuln class), MAESTRO as methodology (operationalized
in AI-17's test), governance/AIVSS (reporting language, noted in reading guide).

---

## Ranked READING GUIDE for Shivam (hands-on builder + bug-bounty hunter)

**Read first: *Practical AI Security* (Farlow).** The only one of the three built for a builder:
30 runnable notebooks, three executed red-team test cases (injection → fuzzing → multi-turn),
the MCP/MAESTRO agent threat model you can apply to any agentic target today, and bounty-shaped
case studies (MathGPT DoS = economic-DoS finding template; face-ID bypass = biometric test plan).
Start with the free Chapter 3 sample (nostarch.com/download/samples/AISecurityHandbook_chapter3.pdf),
then Ch.4 (attacks), Ch.6 (red teaming), Ch.5 case studies. Skip Ch.8–9 (safety/governance) on the
first pass — come back when writing reports.

**Read second: MITRE ATLAS (free, atlas.mitre.org) + OWASP LLM Top 10 2025 (free, genai.owasp.org).**
These are the two taxonomies every AI bounty program and triage team now speaks. Read all 16 ATLAS
tactics and the 73 case studies — they are the closest thing to a public AI-bounty writeup corpus.
OWASP's LLM07 (system-prompt leakage) and LLM08 (vector/embedding weaknesses) are the two newest
high-signal test areas.

**Read third: *Adversarial AI Attacks* (Sotiropoulos)** — but selectively: Ch.14–16 (prompt attacks,
LLM poisoning, LLM supply chain) for bounty work; Ch.4–9 (poisoning, trojans, evasion, privacy
attacks) when you hit ML-classifier or model-hub targets; skip the GAN chapters unless a target
has biometric/deepfake surface. 586 pages — treat as a reference, not a cover-to-cover read.

**Skip for now:** *AI Under Attack* (pre-release, no public depth, governance-heavy — revisit after
release if you need GRC/reporting language); the KDP *HACKING LLM-POWERED SYSTEMS* (unvetted);
the hallucinated "Glenn Derick" book (doesn't exist — use Steve Wilson's O'Reilly *Developer's
Playbook for LLM Security* or the free Randall Tr GitHub playbook for the jailbreak field-guide
niche); *The Loop* (interesting societal read, zero bounty value).

**One-line order: Farlow → ATLAS + OWASP LLM Top 10 (free) → Sotiropoulos (selective) → Wilson's
O'Reilly playbook as the jailbreak reference. Skip the rest until they earn it.**
