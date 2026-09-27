# Company Dossier: Example (example.com)

_Generated 2026-09-27T02:54:18Z by DEEPHUNT Company Hunter. Passive recon only — no active
testing was performed. People section: public data only, no contact._

## At a glance
- Subdomains found: 6 (24 live typo-squat candidates)
- Resolved IPs: 104.20.23.154, 172.66.147.243, 2606:4700:10::6814:179a, 2606:4700:10::ac42:93f3
- Technologies: Cloudflare
- Public breach records matched: 0
- News items (30d): 15 (surface signals: incident)
- Employees (public GitHub): 15 profiles, 8 repos

## Domain footprint
Top subdomains: dev.example.com, example.com, m.example.com, products.example.com, support.example.com, www.example.com
DNS: A=104.20.23.154, 172.66.147.243 MX=0 .
Email posture: SPF=True DMARC-hint=False

## Technology stack
Detected: Cloudflare
Versions: none
Third-party hosts: iana.org
Security-relevant headers: Server, CF-RAY
Public files found: none

## Breach / disclosure history
None matched in HIBP catalogue.

## News (surface-changing first)
- [incident] OpenAI says agents leaked 53 images from ChatGPT users in latest example of rogue activity (Fri, 25 Sep 2026)
- [general] Beyond the stadium: Bowser points to The Wharf as an example for former RFK’s future (Thu, 24 Sep 2026)
- [general] In Trumpeting His Ballroom Project, Trump Has Used China as an Example (Thu, 24 Sep 2026)
- [general] Xi recounts US teacher’s donation to fight desertification in China as example of Sino-US friendship (Fri, 25 Sep 2026)
- [general] High school football coach setting an example on how to overcome obstacles (Sat, 26 Sep 2026)
- [general] Carlos Alcaraz leads by example as Europe take early lead in Laver Cup (Fri, 25 Sep 2026)
- [general] Fiji church leaders told to lead by example, cut back on kava, quit smoking (Fri, 21 Aug 2026)
- [general] ‘Stark example of brutality’: Trump’s ICE used court orders in plan to force-feed at least 10 hunger strikers in detention (Mon, 03 Aug 2026)
- [general] Palestine ‘clearest example’ of international system’s ‘dysfunction,’ Egyptian PM tells UN (Sat, 26 Sep 2026)
- [general] Brice Cherry: Following Freeman's example, Baylor discovered much-needed fire - Waco Tribune (Sat, 26 Sep 2026)
- [general] St. Matthew an Example for Diplomats, Vatican Official Says at UN-Week Mass (Wed, 23 Sep 2026)
- [general] ‘A shining example’: Dorchester County detective remembered for character, service (Wed, 23 Sep 2026)

## People (public data only — DO NOT CONTACT)
- Sindre Sorhus (@sindresorhus): Full-Time Open-Sourcerer. Focused on Swift & JavaScript. Makes macOS apps, CLI tools, npm packages. https://github.com/sindresorhus
- Craig Davison (@davisonio):  https://github.com/davisonio
- Richard Littauer (@RichardLitt): Open source maintainer, birder, sailor, poet, linguist, flâneur, etc, etc, etc. https://github.com/RichardLitt
- Arthur Verschaeve (@arthurvr):  https://github.com/arthurvr
- Kevin Deldycke (@kdeldycke): Entrepreneur, VP, Engineering Manager, Founding Engineer - Billing, Payments & IAM.
 https://github.com/kdeldycke
- Matt Smith (@AllThingsSmitty): Build a better web. https://github.com/AllThingsSmitty
- PatrickJS (@PatrickJS): building Web Scale and Open-Source.

Currently: Engineering Director at PwC and Qwik core

Previ https://github.com/PatrickJS
- John Jago (@johnjago):  https://github.com/johnjago
- Raymond Berger (@RayBB): Maintainer @internetarchive OpenLibrary.  Urbanism, software engineer. Formerly: BuzzFeed, NYT, OOVA https://github.com/RayBB
- Steven Stockhamer (@stevestock):  https://github.com/stevestock
- Matheus Felipe (@matheusfelipeog): I'm observing 👁 https://github.com/matheusfelipeog
- Dave Machado (@davemachado): The generation of random numbers is too important to be left to chance. https://github.com/davemachado

## Suspicious changes since last run
- first snapshot — baseline established

## Ranked attack plan (top 10)
1. **AUTHN-03 Password reset email array injection (reset link to attacker)** (score 14.5) — klass authentication base 5; signal hits: forgot, application/x-www-form-urlencoded
   Hypothesis: Example: Password reset email array injection (reset link to attacker) — the dossier shows a matching surface (authentication); a controlled test with owned acc
2. **IDOR-01 BOLA on numeric/UUID object IDs** (score 13.5) — klass authorization base 5; signal hits: invoice, order
   Hypothesis: Example: BOLA on numeric/UUID object IDs — the dossier shows a matching surface (authorization); a controlled test with owned accounts/data would distinguish vu
3. **AUTHZ-01 Role/plan restriction enforced client-side only** (score 13.5) — klass authorization base 5; signal hits: plan, settings
   Hypothesis: Example: Role/plan restriction enforced client-side only — the dossier shows a matching surface (authorization); a controlled test with owned accounts/data woul
4. **AI-07 Excessive agency — over-permissioned tools, no server-side authz** (score 12) — klass ai-llm base 2; signal hits: function, agent, execute
   Hypothesis: Example: Excessive agency — over-permissioned tools, no server-side authz — the dossier shows a matching surface (ai-llm); a controlled test with owned accounts
5. **AUTHN-02 Password reset token leakage / host header poisoning** (score 11.5) — klass authentication base 5; signal hits: forgot
   Hypothesis: Example: Password reset token leakage / host header poisoning — the dossier shows a matching surface (authentication); a controlled test with owned accounts/dat
6. **OAUTH-01 OAuth redirect_uri / state validation gaps** (score 11.5) — klass authentication base 5; signal hits: callback
   Hypothesis: Example: OAuth redirect_uri / state validation gaps — the dossier shows a matching surface (authentication); a controlled test with owned accounts/data would di
7. **2FA-01 2FA enrollment bypass / recovery-code flaws** (score 11.5) — klass authentication base 5; signal hits: backup-code
   Hypothesis: Example: 2FA enrollment bypass / recovery-code flaws — the dossier shows a matching surface (authentication); a controlled test with owned accounts/data would d
8. **OAUTH-02 OAuth redirect_uri / state confusion** (score 11.5) — klass authentication base 5; signal hits: callback
   Hypothesis: Example: OAuth redirect_uri / state confusion — the dossier shows a matching surface (authentication); a controlled test with owned accounts/data would distingu
9. **INVITE-01 Invite/token reuse and privilege confusion in teams/orgs** (score 11.5) — klass authorization base 5; signal hits: org
   Hypothesis: Example: Invite/token reuse and privilege confusion in teams/orgs — the dossier shows a matching surface (authorization); a controlled test with owned accounts/
10. **EXPORT-01 Data export / bulk download authorization gaps** (score 11.5) — klass authorization base 5; signal hits: backup
   Hypothesis: Example: Data export / bulk download authorization gaps — the dossier shows a matching surface (authorization); a controlled test with owned accounts/data would

## Follow-ups
None.

## Active-testing handoff
passive mode — no active testing authorized. Re-run with --mode hunt --authorize-active once a bug-bounty scope is confirmed.

---
*Boundaries: passive recon only. Nothing here authorizes active testing.
Active work requires confirmed bug-bounty scope and goes through the
ResearchSession enforced loop (propose_test + TestAuthorization).*
