# Proxmox VE pre-8.0.4 unauthenticated root auth bypass (ingested 2026-09-26)

Source: https://blog.nathangolez.com/2026/08/proxmox-ve-7-08-0-3-unauthenticated-single-request-root-auth-bypass
Advisory: PSA-2026-00043-1 (2026-09-01). CVE: CVE-2023-54391.

## The bug
PVE 7.0.0 through 8.0.3. Single request, no password, mints a full root@pam ticket:
`POST /api2/json/access/ticket` with `username=root@pam&password=x&tfa-challenge=1`.
Chain: tfa-challenge present → password verification skipped → user has no `keys`
field (default for root@pam) → user_get_tfa returns undef → authenticate_2nd_new
short-circuits before verify_ticket → full ticket + CSRF token issued. Ticket gives
root shell via /nodes/<node>/terminal. Fixed in libpve-access-control 8.0.4; the fix
was an unrecognized side effect (no CVE/advisory until 2026). Exploitation in the
wild reported.

## Fingerprint (safe, detection-only)
- Proxmox web UI listens on :8006. `GET /api2/json/version` is unauthenticated and
  returns `{"data":{"version":"8.0.3",...}}`.
- Vulnerable: 7.x (all, EOL), 8.0–8.0.3. Safe: 8.0.4+, 9.x.

## Agent rules
- Detect Proxmox + banner-grab version ONLY. Never send the tfa-challenge bypass
  request — that is an authentication-bypass attempt and stays a manual,
  explicitly-authorized decision by the researcher.
