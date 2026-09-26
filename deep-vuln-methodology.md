# Deep Vulnerability Research Methodology

Adopted 2026-09-26. This is the standing playbook for high-impact, non-obvious
vulnerability research. It replaces generic checklist scanning.

## Objective

Discover HIGH-IMPACT, NON-OBVIOUS vulnerabilities through deep attack-surface
analysis, authorization reasoning, state analysis, API behavior analysis, and
business-logic research. Think like a vulnerability researcher, not a scanner.

## Rules

- Stay strictly within the authorized scope and the live program brief.
- Use synthetic/test accounts and synthetic data only.
- Do NOT destroy, alter, ransom, persist in, or exfiltrate real data.
- Stop escalation once impact is conclusively demonstrated.
- Never assume a scanner result is a vulnerability. Every finding needs
  reproduced evidence with a minimal safe test case.

## 1. Build a complete application model

Map: users, roles, privileges, objects/resources, API endpoints, parameters,
state transitions, trust boundaries, internal/external integrations,
authentication mechanisms, authorization checks, client/server responsibilities.

## 2. Find security invariants

For every sensitive operation determine: "What must ALWAYS be true for this
operation to be allowed?" Examples:

- User A must never access User B's object.
- A low-privilege user must never perform an admin-only operation.
- A resource ID must remain bound to the authorized principal.
- A workflow step must not be reachable without completing its prerequisite.

Then actively search for violations of those invariants.

## 3. Look for cross-feature vulnerabilities

Never analyze endpoints in isolation. Investigate combinations:

- authentication + API authorization
- file upload + parsing
- OAuth + account linking
- webhooks + authorization
- password reset + session handling
- billing + object ownership
- admin functions + alternate API versions
- mobile API + web API
- caching + authorization
- CORS + credentials
- race conditions + state transitions

## 4. Hunt for differential behavior

Compare: authenticated vs unauthenticated, user vs privileged user, owner vs
non-owner, old vs new API versions, GET vs POST vs PUT vs PATCH, JSON vs
form/multipart, browser vs direct API requests. Look for security decisions
that differ unexpectedly.

## 5. Business-logic research

Model important workflows as state machines. Look for: skipped states,
reordered operations, replayable operations, duplicate execution, inconsistent
authorization, race conditions, trust placed in client-controlled state,
server/client state disagreement, object substitution, privilege transitions
without authorization.

## 6. Source + client analysis

Where JS/source is available: trace sensitive data flows, identify
authorization middleware, locate trust boundaries, find hidden endpoints,
compare client assumptions with server enforcement, inspect feature flags and
undocumented functionality, identify dangerous server-side sinks.

## 7. Impact validation

For every suspected issue: reproduce with the smallest safe test case,
establish a baseline, prove the security boundary was crossed, use only
synthetic data, determine the maximum demonstrated impact, stop once
sufficient evidence exists.

Require evidence for: cross-account access, privilege escalation, arbitrary
code execution, sensitive-data exposure, authentication bypass, meaningful
server-side compromise, material integrity impact.

## Final report format

[CONFIRMED] — title, root cause, affected endpoint/component, preconditions,
minimal reproduction, evidence, security boundary violated, demonstrated
impact, severity rationale, remediation.

[HIGH-CONFIDENCE LEADS] — why each deserves manual investigation.

[REJECTED HYPOTHESES] — interesting paths investigated but disproven.

Prioritize novel interactions, broken assumptions, authorization boundaries,
state-machine flaws, and business logic. Never fabricate evidence.
