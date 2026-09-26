# The Hacker's Guide to Attacking AI Agents
Source: https://darkmarc.substack.com/p/the-hackers-guide-to-attacking-ai
Date saved: 2026-09-26

## Summary
A full engagement methodology for assessing agentic AI systems. Core insight: what matters is where the system sits on the autonomy spectrum, mapped with five questions — (1) untrusted input (direct + indirect: browsed pages, ingested docs, RAG chunks, memory, tickets, emails, other agents' output), (2) tools it can call, ranked by severity, (3) privilege/authority it acts with, (4) downstream processing of its output (injection sinks: DB queries, shell, URLs, executed code), (5) where data can go (exfil sinks). The model cannot separate instructions from data — injection with no prepared statements. Catalogs the OWASP Top 10 for Agentic Applications 2026 (ASI01 Agent Goal Hijack, ASI02 Tool Misuse, ASI03 Identity/Privilege Abuse, ASI04 Agentic Supply Chain, ASI05 Unexpected Code Execution, ASI06 Memory/Context Poisoning, ASI07 Insecure Inter-Agent Communication, ASI08 Cascading Failures, ASI09 Human-Agent Trust Exploitation, ASI10 Rogue Agents). Kill chain in four stages: find the way in, get the agent to act on your input, turn that into real impact, take what you came for. Recon guidance: map delivery channel, integrations, host/OS/services, runtime sandbox, framework, model guardrails — proxy the client (Burp/mitmproxy) to find hidden input fields and API parameters; probe with off-topic questions to fingerprint guardrail layers.

## Agent relevance — DETECTION FINGERPRINTS
- Look for AI/chat/assistant features on in-scope targets: endpoints or UI containing `chat`, `assistant`, `copilot`, `agent`, `ask-ai`, `support-bot`; JS bundles referencing model APIs, `stream`, `sse`, `websocket` chat transports.
- Hidden input paths: proxy traffic and diff visible form fields vs actual request params; extra params reaching the backend are candidates for unguarded input.
- Fingerprint guardrails: send one off-topic question — identical flat refusal = pre-model classifier; polite model refusal = system prompt only; no refusal = keyword search, minimal AI.
- Map tools: UI that shows "connected apps", "integrations", file upload, URL fetch, email send, calendar access — each is a tool the agent can be steered to misuse.
- Indirect injection surface: any place the agent reads attacker-reachable content (support ticket queues, uploaded docs, RAG knowledge bases, email inboxes, calendar invites).

## Guided manual-test steps (own authorized sessions only)
1. Build the 5-question target map for the AI feature: list every input channel (chat box, file upload, URL fetch, API params) and every tool/output the agent has.
2. Test indirect injection: plant instruction-like text in content the agent ingests (a doc you upload, a page it can browse) and observe whether behavior changes.
3. Test tool misuse: ask the agent to use a legitimate tool against an attacker-chosen target (e.g. fetch a URL you control, summarize a file outside intended scope) and check whether privilege boundaries hold.
4. Test data exfil paths: ask for data from one context to be rendered into another (another user's ticket, an admin document) — watch for cross-context leakage.
