"""DEEPHUNT identity module: owned test-account lifecycle for bug bounty targets.

Design principles:
- Passwords are NEVER stored here, in logs, or in memory files. They live
  only in the Secure Vault (user sets them via a secure entry card) and the
  browser fills them from the vault at sign-in time.
- This module keeps metadata only: target, email, status, dates, notes.
- Signup execution goes through live browser tasks driven by studied
  per-target playbooks (identity/playbooks/*.yaml).
- Hard stops: any step asking for real KYC/PII (SSN, ID documents, real
  name/DOB beyond a test persona, payment instruments) halts automation and
  hands to the user. No exceptions.
"""
