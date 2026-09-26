# BragJack — Browser Agent Hijack via Malicious Extension
Source: https://forever.security/blog/bragjack-attack-hijacks-every-browser-agent/
Date saved: 2026-09-26

## Summary
Forever Security hijacked 5 Chromium-based browser agents (Gemini Live/Chrome, Perplexity Comet, Edge Actions, Opera Neon, Claude in Chrome) with ONE ordinary MV3 extension. $20k bounties, 2 CVEs (CVE-2026-0628, CVE-2026-55945).

## Key technique: "DiNneR Serving"
1. Extension with declarativeNetRequest + host_permissions https://*/*.
2. WEAKEN: strip/modify security headers (CSP, X-Frame-Options, document-isolation-policy) on the agent's web origin.
3. EXECUTE: redirect a remote JS resource the agent page loads to attacker JS -> code runs in privileged agent context.
- Chrome flaw: DNR applied inside WebViews loading https: pages (chrome://glic embeds gemini.google.com).
- Comet flaw: over-broad externally_connectable list (staging/preview origins included).
- Impact: local file read, screenshots, mic/camera, profile/history leak — zero clicks.

## Agent relevance
- Emerging attack class: AI browser agents = new privileged targets. Add "AI agent features" to recon checklist (look for agent/assistant endpoints, chrome://-style internals, embedded WebViews).
- Prompt Forcing attacks pair with this — track as technique family.
