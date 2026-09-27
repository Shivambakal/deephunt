# DEEPHUNT Experiment: discovery capability, measured

Started 2026-09-27. Architecture is FROZEN: no new models, sources, scanners,
agents, technique cards, brains, or dashboards until this experiment reports.

## The metric

**Confirmed, independently reproducible findings per unit of research time.**

Counts as a finding ONLY when all of these hold:
1. Observation → hypothesis → experiment → evidence, recorded in a ResearchSession.
2. `compete_finding()` eliminated the competing explanations.
3. Independently reproduced (different evidence path / second run / manual confirmation).
4. In scope, authorized, and reportable to the program.

Hypotheses, anomalies, "interesting behavior," and LLM confidence count as ZERO.

## The five questions

1. Can DEEPHUNT understand an unfamiliar target? (dossier + world model)
2. Can it generate hypotheses without being handed the vulnerability?
3. Can it design useful experiments from observations? (propose_test gate)
4. Can it kill its own false positives? (adversarial self-check + compete_finding)
5. Can it produce ONE independently reproducible security finding?

If #5 is zero after serious authorized research, that IS the result — and it is
more valuable than another 10,000 lines of architecture.

## Targets (all policies read live 2026-09-27)

- adobe — passive only
- shopify — active, throttled (nuclei rl 20, no commercial scanners, merchant stores off-limits)
- yahoo — active, throttled
- kiteworks — PASSIVE ONLY (program forbids automated tools; human does manual low-rate testing)
- anthropic — active at reasonable rate (X-HackerOne-Handle header required)
- openai — passive only (automated scanners trigger bans)
- monzo — passive only; scope partially verified (operator confirms asset list in Intigriti UI before any active testing)
- okg (OKX) — passive only (no automated scanners, 5 req/s, 24h report window)

Excluded: agoda (dry well), wolt (parked), live nation (human-operated),
robinhood (blocked pending attribution proof).

## Kiteworks note (anti-distortion)

Kiteworks confirmed 2026-09-25: credible federal threat intel, precautionary
shutdown recommended, NO indication of compromise, all known vulns fixed in
9.5.1. No CVE, no confirmed zero-day, no confirmed exploitation. Nothing public
establishes the suspected issue is remotely exploitable, in Core,
unauthenticated, or reproduced by the hunting environment. The $25k bonus /
$50k-at-CVSS-10.0 for new unauth RCE-as-root is real but must not distort the
experiment. Policy: stop at what is necessary to confirm; no destructive RCE
validation on the live environment.

## Log

- 2026-09-27: experiment opened. Confirmed findings: 0.
