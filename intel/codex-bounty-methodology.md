# Codex-for-bugbounty methodology (ingested 2026-09-26)

Source: https://www.yeswehack.com/learn-bug-bounty/llm-series-codex

## What transfers to the hunter agent
Evidence discipline for AI-assisted hunting (from HashKitten's WordPress zero-day
work + YesWeHack's blind-lab tests with GPT-5.6):

1. **Hypothesis registry** — every candidate tracks: hypothesis + evidence
   location, evidence FOR, evidence AGAINST, next distinct test + expected
   signal, status (open/blocked/rejected/confirmed).
2. **Falsification first** — before sending a variation, state the hypothesis,
   the expected signal, and what result would DISPROVE it. Reopen a blocked path
   only when new evidence changes the mechanism, never because the payload
   string changed.
3. **Parallel agents, genuinely different ideas** — parallelism helps only when
   agents explore different theories; four agents running the same search is
   token burn. One agent owns the hypothesis registry; adversarial agents
   challenge concrete findings before acceptance.
4. **Observation vs inference** — cite the exact request/response/source behind
   each claim. Replace long speculative lists with evidence around the few
   candidates that may actually be exploitable.

Applied: the `ai` command prompt now demands this structure (hypothesis,
evidence for/against, falsifying test, status) instead of generic suggestions.
