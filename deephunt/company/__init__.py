"""DEEPHUNT Company Hunter: name a company -> deep passive dossier -> ranked attack plan.

Boundaries (absolute, enforced by design):
- Workers are PASSIVE ONLY: public third-party APIs (crt.sh, DNS-over-HTTPS,
  GitHub public API, Google News RSS, HIBP breach list) plus the company's
  public homepage HTML. No port scans, no directory brute force, no active
  probing of any asset.
- employees.py collects PUBLIC data only. No contacting anyone, no pretexting,
  no phishing, no social engineering actions of any kind. Ever.
- Nothing active against the company until the user confirms a bug-bounty
  scope or explicit authorization. Active work goes through the enforced
  ResearchSession loop (propose_test + TestAuthorization), never around it.
"""
