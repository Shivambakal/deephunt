# Security Policy

## This is offensive-security research tooling

DEEPHUNT is built to find vulnerabilities **only** in programs that authorize
testing: bug-bounty programs, VDPs, and systems the operator owns. The safety
rules in `README.md` and `CAMPAIGN_STATE.md` are load-bearing, not decorative.

## Rules of engagement (summary)

- Test only hosts in `scope.yaml`, and only within each program's published
  rules (passive-only stays passive-only).
- Every active test goes through `ResearchSession.propose_test()` and a
  minted `TestAuthorization`. Anything else is a bug in this system — treat
  it as one.
- Minimum-safe proof only. Never exfiltrate real user data, never degrade a
  service, never pivot beyond the authorized scope.
- Findings are drafted as reports; **humans submit**, and only to the
  affected program through its official channel.

## Reporting a vulnerability in DEEPHUNT itself

If you find a safety bypass in this system (e.g., a path that lets an
unauthorized test execute, a scope-gate failure, credential leakage), report
it privately to the repository owner. Do not open a public issue for
security defects.

## Disclosure ethos

This project exists to make vulnerability discovery more disciplined, not to
stockpile exploits. Confirmed findings follow coordinated disclosure through
the affected program's own process.
