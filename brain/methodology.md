# Hunter Methodology — the funnel (adopted 2026-09-26, from Shivam)

Source: Intigriti + PortSwigger + Bugcrowd researcher guidance, via Shivam.
This is now the standing shape of every deep hunt. The brain loop
(hypothesis → adversarial → smallest test → observe → learn) is the
*predict → probe → prove* core; this file is the *funnel* around it.

## The funnel
10,000 possible endpoints → 500 interesting → 50 security-sensitive →
10 unusual behaviors → 3 strong hypotheses → 1 validated vulnerability.

Someone finding a bug in 30 minutes spent years building the mental model
that tells them where NOT to waste those 30 minutes. There is no shortcut
to the funnel — only to running it faster.

## The five hunting grounds (in order)
1. **Business logic** — learn how the product is supposed to work, then ask
   "what assumption can I violate?" Scanners can't do this; it needs
   human/domain knowledge.
2. **Authorization / access control** — systematically compare users, roles,
   objects, actions. Two-account differential testing is the workhorse.
3. **APIs + JavaScript** — mine JS bundles and API docs for hidden routes,
   parameters, methods, functionality the UI never exposes.
4. **Weird state transitions / races** — operations that collide or pass
   through temporary states. Predict → probe → prove.
5. **Target familiarity** — stay on ONE target long enough to learn its
   architecture, workflows, and changes. Intigriti's explicit advice:
   extended focus beats constant switching.

## Toolchain (in order of use)
Burp-equivalent interception + browser DevTools → subdomain/HTTP discovery →
crawling/URL collection → targeted fuzzing → Nuclei/scanners → HEAVY manual
analysis. Automation finds the 500; humans find the 1.

## Operating rules derived from this
- Recon WIDE (many targets), then hunt DEEP (one target at a time).
- No hypothesis without endpoint inventory behind it — the funnel feeds
  the brain loop, never the reverse.
- Every hunt ends with: endpoints mapped, unusual behaviors listed,
  hypotheses ranked, one validated or killed with evidence.
- Change monitoring: re-run discovery on the deep target periodically;
  new JS bundles and new routes are where regressions live.
