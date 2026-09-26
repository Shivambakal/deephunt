# Hacking OpenAI — libheif Heap Overflow + SSO Misconfiguration Chain
Source: https://www.hacktron.ai/blog/hacking-openai
Date saved: 2026-09-26

## Summary
- Hacktron (Harsh Jaiswal, Mohan Pedhapati, Rahul Maini) chained two bugs in <72 hours to take over OpenAI employees' ChatGPT/Codex accounts and reach internal repos via connected GitHub integration; $6,500 bounty. Demonstrated impact with a harmless PR to the internal monorepo, then stopped.
- Bug 1: heap buffer overflow in `libheif` (HEIC decoder) — Discourse passed HEIF files to ImageMagick's `magick` because FastImage didn't support HEIF; a non-CVE-documented upstream fix was never backported to Debian 12/13, leaving Discourse's Docker image on vulnerable 1.19.7. Image upload → RCE.
- Bug 2: OpenAI SSO identity misconfiguration — compromising any OpenAI-SSO-connected service (here community.openai.com) yielded ChatGPT/Codex account takeover, cascading into GitHub/Slack/email via connected integrations.
- Expanded into "HEIF Heist": libheif across Slack, Meta, GitHub Enterprise, Rails/Next.js/Astro/Gatsby — AI (Claude Opus) adapted each exploit in 1–2 days, <$3,000 in tokens; almost no target detected the probing.
- Key meta-lesson: AI has collapsed exploit-development economics — memory-corruption bugs that once needed rare expertise are now operationalizable in days; threat models must assume this.

## Agent relevance
- Dependency-chain auditing as an agent module: fingerprint image-processing pipelines (upload → FastImage/ImageMagick/libheif/libde265), check installed lib versions against upstream security fixes — including fixes never assigned CVEs (grep changelogs, don't rely on CVE feeds alone).
- SSO blast-radius mapping: for any target, enumerate SSO-connected services ("Sign in with X"); a compromise of the weakest connected service = account takeover on the main platform. Add "connected integrations inventory" to recon (GitHub/Slack/email connectors multiply impact).
- Detection fingerprints: `.heic/.heif/.avif` upload endpoints, `X-` headers or error messages revealing ImageMagick/Discourse, Debian-based Docker images with outdated media libs; test with benign malformed images only on authorized targets.
- Strategic: prioritize bug classes where AI-assisted exploit dev is now cheap (memory corruption in media parsers) — these are under-hunted in bounty programs relative to web logic bugs.
