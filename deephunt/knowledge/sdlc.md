# How software gets built — and where each bug class is born.
# DEEPHUNT reads this to aim hypotheses at the phase that creates them.

## 1. Design / architecture
Decisions: trust boundaries, auth model, data classification, threat model (often skipped).
Bugs born here: broken access control (BIAS-01), missing authz on new services,
trust-boundary confusion (SSRF, BIAS-07), insecure defaults.
Hunt: reconstruct the intended trust model from the world model, then violate it.

## 2. Coding
Reality: deadline pressure (BIAS-06), copy-paste (BIAS-03), framework trust (BIAS-01),
AI-generated code (BIAS-19), regex validators (BIAS-09).
Bugs born here: injection, XSS, crypto misuse, mass assignment, hardcoded secrets.
Hunt: newest code + AI-assisted features first; they are reviewed thinnest.

## 3. Code review
Reality: reviewers check style and happy paths, not security invariants.
Bugs that survive: logic flaws (BIAS-04), missing authz on edge endpoints,
TOCTOU/race windows nobody traced.
Hunt: assume review missed the class, not the instance — test siblings (BIAS-20).

## 4. Build / dependencies
Reality: transitive deps, vendored copies, unpinned versions (BIAS-10).
Bugs born here: known CVEs in components, dependency confusion, malicious updates.
Hunt: fingerprint versions passively, match OSV/GitHub Advisory DB.

## 5. Deploy / infrastructure
Reality: debug flags left on, .git exposed, default creds, permissive CORS (BIAS-16),
dangling DNS from torn-down environments.
Bugs born here: takeover, secrets exposure, SSRF via metadata services.
Hunt: enumerate what deploy left behind — the infra nobody owns.

## 6. Operations / evolution
Reality: feature flags rot (BIAS-18), mobile/web parity drifts (BIAS-13),
test data lingers (BIAS-14), logs accumulate secrets (BIAS-17).
Bugs born here: abandoned endpoints, stale tenants, log disclosure.
Hunt: diff the current surface against history — the delta is the target.

## Team dynamics that manufacture vulnerabilities
- Conway's law: the system mirrors team boundaries — auth gaps live at the seams
  between teams' services. Hunt cross-service calls.
- Diffusion of responsibility: shared components (auth libs, upload handlers)
  get the least scrutiny. Hunt shared code paths.
- Metrics pressure: velocity rewards features, not hardening. Newest features
  are the softest targets.
- The "someone else's problem" field: WAFs, CDNs, and third-party scripts are
  trusted without verification. Hunt the supply chain (SUPPLY-01).
