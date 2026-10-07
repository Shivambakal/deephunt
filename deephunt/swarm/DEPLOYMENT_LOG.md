# Swarm deployment log — 2026-09-27

- 11:00 IST: All 100 agents deployed (pending_init).
- Workers (62): 1-14 recon, 16-29 app, 31-44 differential, 46-65 known-vuln, 66-79 novel.
- Synthesizers (4): 15, 30, 45, 80 → synth_*.md.
- Verifiers (10): 81-90 → obs_verify.jsonl.
- Memory (9): 91-99 → memory_*.md.
- Director (1): 100 → RESEARCH_PLAN.md.
- 4 transient spawn failures (DB lock timeout) in group B batch — all retried OK.
- Target: https://ywh-kw-public.bounty.kiteworks.dev only. Passive/analysis only.
- Findings so far: 0 confirmed. Metric: confirmed reproducible findings per research time.

## Operational note — 2026-09-27 ~11:06 IST (agent #40 report)
- Direct HTTPS from sandbox to ywh-kw-public.bounty.kiteworks.dev times out (proxy→origin TCP/TLS never completes; 8/8 probes failed at connect).
- Agents doing direct-request work should fall back to docs/OSINT and the browser route.
- Agent noted proxy credentials visible in tool output; it did not store/quote/reuse them.

## Swarm completion — 2026-09-27 ~11:10 IST
- All synthesis/memory/director stages completed. RESEARCH_PLAN.md written by agent 100.
- Final evidence: obs_recon 116, obs_app 131, obs_diff 92, obs_verify 10 (all confirmed, docs/program-grade).
- Hypotheses: hyp_known 76 + hyp_novel 40 = 116 -> deduped to 97 unique; top 20 ranked in synth_hyp.md.
- Confirmed vulnerabilities: 0. Live tests: 0. Reports submitted: 0.
- Known limits: sandbox direct-request egress to the hunting host failed (proxy CONNECT timeouts, 5-agent-corroborated); browser route works. Live experiments need working network + human test accounts.
