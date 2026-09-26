# From IDOR to Admin: Full Platform Takeover — Pankaj Kumar Yadav
Source: https://medium.com/@pankaj_73968/from-idor-to-admin-how-a-simple-id-parameter-led-to-full-platform-takeover-cdc21b989a21
Date saved: 2026-09-26 (via browser task; Medium blocked direct fetch)

## Summary
Real-estate web app, $4,500 bounty, CVSS 9.8 Critical. Chain:
1. Profile-update endpoint took `user_id` in request body with NO server-side ownership check.
2. Set `user_id: 1` (admin) and changed the admin's email to attacker-controlled address — 200 OK, role revealed as "administrator".
3. Triggered Forgot Password — reset link went to attacker's inbox, password changed, no extra verification.
4. Logged in as admin: JWT with id:1, role:administrator, membership:pro, permissions:["all"].
5. JS check `user.role === "administrator"` revealed hidden "Control Panel" -> undocumented `/admin/panel`.
6. Admin dashboard: 4,12,847 users, 45,231 listings, $2.4M revenue data, role modification, impersonation.

## Key lessons
- IDOR is never "just" IDOR — email-change on another user's account = account takeover via password reset.
- Low IDs (1, 2) are often admins/test/service accounts — prime targets.
- Client-side role hiding is not security; verify RBAC server-side on every admin endpoint.
- Email changes must require verification of the NEW address before taking effect.

## Agent relevance
- IDOR playbook updated with the escalation chain: read-IDOR -> write-IDOR on email field -> password-reset takeover.
- Detection: profile/account endpoints accepting user_id/account_id in body — flag for manual testing (own accounts only).
