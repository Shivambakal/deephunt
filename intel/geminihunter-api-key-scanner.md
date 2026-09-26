# geminiHunter — Exposed Google Gemini API Key Scanner
Source: https://github.com/devploit/geminiHunter
Date saved: 2026-09-26

## Summary
- Open-source Python tool (MIT, by @devploit, 102 stars) that finds and assesses exposed Google Gemini API keys across web assets and Android APKs — highly relevant to Shivam's Firebase/JS background.
- Discovery: crawls HTML scripts, linked JS, JSON manifests, webpack chunks, source maps, and Wayback-archived JS; APK path uses jadx decompilation with ZIP/binary-string fallback.
- Extraction handles obfuscation: concatenated strings, arrays, template literals, reversed strings, hex escapes, Base64.
- Validation: tests keys against the Gemini API (model-list 200 = valid), records restrictions; optional bounded bypass engine tries request variations on 403s. Rate limiting, concurrency controls, JSON output with curl evidence, exit codes per finding status.
- Explicitly an active scanner: validation contacts Google and can consume quota — authorized-scope-only.

## Agent relevance
- Direct candidate for the hacker agent's toolbelt: clone and integrate as the "exposed AI API key" module, or reimplement its discovery patterns (JS crawl + source-map + Wayback + deobfuscation) as a native agent capability.
- Generalize the pattern beyond Gemini: same pipeline detects exposed Firebase configs, AWS keys, Stripe keys, OpenAI keys in JS bundles — core "secret-in-client-asset" checklist item.
- Detection fingerprints to encode: source-map files (`.js.map`), webpack chunk naming, `apikey`/`api_key` patterns in JS, keys in Android `strings.xml`/native libs; validate-then-report workflow with restriction recording (don't just report presence — report what the key can actually do).
- Operational notes for agent: enforce rate limits, custom User-Agent tagging, scope checks before Wayback parent-domain expansion.
