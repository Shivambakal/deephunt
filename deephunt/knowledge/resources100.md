# DEEPHUNT 100 — curated research resources (ingested 2026-09-27)

Source: curated research list. Purpose: feed DEEPHUNT's brain — technique cards,
world-model design, inference engine, experiment design, falsification.
Rule: execution stays in authorized scope (own infra, CTFs, labs, explicit bounty scope).

## A. Web/API security (1–15)
1. OWASP Web Security Testing Guide (WSTG, v5.0 in dev) — core testing methodology — https://owasp.org/www-project-web-security-testing-guide/
2. PortSwigger Web Security Academy — interactive labs, modern vulns — https://portswigger.net/web-security
3. OWASP API Security Top 10 — API authz, business-flow, inventory — https://owasp.org/API-Security/
4. OWASP ASVS — security requirements as machine-checkable properties — https://owasp.org/www-project-application-security-verification-standard/
5. OWASP Cheat Sheet Series — large security knowledge base — https://cheatsheetseries.owasp.org/
6. OWASP Testing Project — broader methodology ecosystem — https://owasp.org/
7. OWASP Authorization Cheat Sheet — authorization model design — https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
8. OWASP REST Security Cheat Sheet — API security reasoning — https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html
9. OWASP GraphQL Cheat Sheet — GraphQL attack-surface modeling — https://cheatsheetseries.owasp.org/cheatsheets/GraphQL_Cheat_Sheet.html
10. OWASP SSRF Prevention Cheat Sheet — trust-boundary modeling — https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html
11. OWASP Business Logic Abuse Prevention — **critical**: logic flaws — https://cheatsheetseries.owasp.org/cheatsheets/Business_Logic_Security_Cheat_Sheet.html
12. OWASP Threat Modeling Cheat Sheet — observations → hypotheses — https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html
13. OWASP Dependency-Check — dependency intelligence — https://owasp.org/www-project-dependency-check/
14. OWASP ZAP — automation platform for authorized envs — https://www.zaproxy.org/
15. OWASP Juice Shop — controlled target for automated experiments — https://owasp.org/www-project-juice-shop/

## B. Bug bounty / real-world methodology (16–25)
16. HackerOne Hacker Resources — program/disclosure structures — https://www.hackerone.com/hackers
17. Bugcrowd University — practical methodology — https://www.bugcrowd.com/hackers/bugcrowd-university/
18. Intigriti Academy — vuln research training — https://academy.intigriti.com/
19. Google VRP (bughunters.google.com) — public bug-hunting ecosystem — https://bughunters.google.com/
20. Microsoft MSRC — disclosure + research — https://msrc.microsoft.com/
21. GitHub Security Lab — real vuln research — https://securitylab.github.com/
22. Google Project Zero — elite researcher thinking — https://googleprojectzero.blogspot.com/
23. Trail of Bits Blog — program analysis, fuzzing, research — https://blog.trailofbits.com/
24. Project Discovery — modern security automation — https://projectdiscovery.io/
25. Nuclei — template detection; know where it stops — https://github.com/projectdiscovery/nuclei

## C. Static analysis / semantic reasoning (26–40)
26. CodeQL — code as queryable data — https://codeql.github.com/
27. CodeQL docs — query + data-flow reasoning — https://codeql.github.com/docs/
28. CodeQL GitHub repo — security query libraries — https://github.com/github/codeql
29. Semgrep — lightweight semantic analysis — https://semgrep.dev/
30. Semgrep GitHub — implementation study — https://github.com/semgrep/semgrep
31. LLVM — compiler infrastructure — https://llvm.org/
32. Clang Static Analyzer — static analysis foundations — https://clang-analyzer.llvm.org/
33. AddressSanitizer — memory-safety instrumentation — https://clang.llvm.org/docs/AddressSanitizer.html
34. UndefinedBehaviorSanitizer — UB detection — https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html
35. Tree-sitter — syntax trees from source — https://tree-sitter.github.io/tree-sitter/
36. Tree-sitter GitHub — parser implementation — https://github.com/tree-sitter/tree-sitter
37. Joern — code property graphs for vuln research — https://joern.io/
38. Joern GitHub — graph-based program analysis — https://github.com/joernio/joern
39. Code Property Graph paper (Yamaguchi 2014) — conceptual foundation — https://www.sec.cs.tu-bs.de/pubs/2014-icse-yamaguchi.pdf
40. Infer — static analysis ecosystem — https://fbinfer.com/

## D. Fuzzing (41–55)
41. OSS-Fuzz — continuous distributed fuzzing — https://github.com/google/oss-fuzz
42. OSS-Fuzz docs — https://google.github.io/oss-fuzz/
43. OSS-Fuzz-Gen — **LLM-powered fuzz-target generation** — https://github.com/google/oss-fuzz-gen
44. AFL++ — coverage-guided fuzzing — https://github.com/AFLplusplus/AFLplusplus
45. libFuzzer — in-process coverage-guided fuzzing — https://llvm.org/docs/LibFuzzer.html
46. Honggfuzz — major fuzzing engine — https://github.com/google/honggfuzz
47. Jazzer — JVM fuzzing — https://github.com/CodeIntelligenceTesting/jazzer
48. Atheris — Python fuzzing — https://github.com/google/atheris
49. Hypothesis — property-based testing — https://hypothesis.readthedocs.io/
50. Echidna — smart-contract fuzzing — https://github.com/crytic/echidna
51. Foundry — Ethereum dev/testing — https://book.getfoundry.sh/
52. ClusterFuzz — distributed fuzzing infra — https://github.com/google/clusterfuzz
53. ClusterFuzzLite — CI fuzzing — https://google.github.io/clusterfuzzlite/
54. FuzzBench — fuzzer benchmarking — https://google.github.io/fuzzbench/
55. OSS-Fuzz research — large-scale fuzzing ops — https://google.github.io/oss-fuzz/

## E. Kernel / systems (56–63)
56. syzkaller — coverage-guided kernel fuzzing — https://github.com/google/syzkaller
57. syzkaller setup docs — https://github.com/google/syzkaller/blob/master/docs/setup.md
58. syzkaller usage — auto reproduce + minimize — https://github.com/google/syzkaller/blob/master/docs/usage.md
59. syzkaller research docs — https://github.com/google/syzkaller/tree/master/docs
60. QEMU — virtualization/emulation lab — https://www.qemu.org/
61. GDB — program-state inspection — https://www.sourceware.org/gdb/
62. Linux Kernel docs — systems knowledge — https://docs.kernel.org/
63. Linux Kernel CVEs — historical vuln classes — https://www.cve.org/

## F. Vulnerability knowledge / datasets (64–73)
64. CVE.org — identifiers — https://www.cve.org/
65. NVD — vuln database — https://nvd.nist.gov/
66. CWE — weakness taxonomy — https://cwe.mitre.org/
67. MITRE ATT&CK — adversary behavior — https://attack.mitre.org/
68. MITRE D3FEND — defensive techniques — https://d3fend.mitre.org/
69. CAPEC — attack patterns — https://capec.mitre.org/
70. EPSS — exploitability data — https://www.first.org/epss/
71. CVSS — severity methodology — https://www.first.org/cvss/
72. GitHub Advisory Database — OSS vuln intel — https://github.com/advisories
73. Google OSV — OSS vuln database — https://osv.dev/

## G. AI/agent security (74–84)
74. OWASP Top 10 for LLM Applications — https://owasp.org/www-project-top-10-for-large-language-model-applications/
75. OWASP GenAI Security Project — https://genai.owasp.org/
76. OWASP AI Testing Guide (v1 Nov 2025) — https://github.com/OWASP/www-project-ai-testing-guide
77. OWASP AI Testing Guide docs — https://owasp.org/www-project-ai-testing-guide/
78. NVIDIA garak — LLM vuln assessment — https://github.com/NVIDIA/garak
79. Promptfoo — LLM/agent eval + red teaming — https://github.com/promptfoo/promptfoo
80. Promptfoo red-team guide — https://www.promptfoo.dev/docs/red-team/
81. NIST AI RMF — AI risk methodology — https://www.nist.gov/itl/ai-risk-management-framework
82. NIST AI RMF Playbook — Govern/Map/Measure/Manage — https://www.nist.gov/itl/ai-risk-management-framework/nist-ai-rmf-playbook
83. NIST AI Resource Center — TEVV — https://airc.nist.gov/
84. MITRE ATLAS — adversarial AI knowledge — https://atlas.mitre.org/

## H. AI agents / LLM engineering (85–92)
85. LangGraph — stateful agent workflows — https://langchain-ai.github.io/langgraph/
86. LangChain — agent/tool orchestration — https://python.langchain.com/
87. LlamaIndex — retrieval/data architecture — https://www.llamaindex.ai/
88. DSPy — programmatic LM pipeline optimization — https://dspy.ai/
89. OpenAI Evals — evaluation architecture — https://github.com/openai/evals
90. Hugging Face Agents Course — agent fundamentals — https://huggingface.co/learn/agents-course/
91. Anthropic Model Context Protocol — https://modelcontextprotocol.io/
92. MCP GitHub — https://github.com/modelcontextprotocol

## I. Formal methods / verification (93–97)
93. Z3 SMT Solver — https://github.com/Z3Prover/z3
94. TLA+ — https://lamport.azurewebsites.net/tla/tla.html
95. Alloy — https://alloytools.org/
96. CBMC — https://www.cprover.org/cbmc/
97. Dafny — https://dafny.org/
Purpose: reason about INVARIANTS ("what must always be true") not just payloads.

## J. Benchmarking / experimentation (98–100)
98. CyberBattleSim — autonomous cyber reasoning env — https://github.com/microsoft/CyberBattleSim
99. AgentBench — agent capability benchmarking — https://github.com/THUDM/AgentBench
100. SWE-bench — agent eval on real software tasks — https://www.swebench.com/

## Priority-15 (study first)
CodeQL → Joern → Tree-sitter → Z3 → OWASP WSTG → PortSwigger Academy →
OWASP API Top 10 → ASVS → AFL++ → OSS-Fuzz → OSS-Fuzz-Gen → syzkaller →
MITRE ATT&CK/CWE → NIST AI RMF → OWASP AI Testing Guide.

## The six research capabilities (architecture)
1. WORLD MODEL — system as identities/objects/services/roles/states/APIs → trust boundaries → security invariants.
2. SECURITY INFERENCE ENGINE — ask "who owns / reads / modifies / transitions this object? what evidence establishes authority? what if the assumption is wrong?"
3. EXPERIMENT DESIGNER — cheapest experiment that maximally reduces uncertainty between competing hypotheses.
4. FUZZING + REASONING HYBRID — LLM finds interesting locations → static analysis → fuzz target → coverage-guided fuzzing → anomaly → minimize → reproduce.
5. SELF-ADVERSARIAL VERIFICATION — every candidate gets an internal skeptic; CONFIRMED only after alternatives disproven.
6. FAILURE LEARNING — memory stores hypothesis/experiment/observation/false-explanation/reason-rejected/successful-explanation/environment/technology/preconditions.
