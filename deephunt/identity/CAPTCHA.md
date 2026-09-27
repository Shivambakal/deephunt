# CAPTCHA strategy for DEEPHUNT signup/login automation

## Honest baseline

No tool "solves any type of captcha" reliably for free. What exists:

| CAPTCHA | Automated reality |
|---|---|
| reCAPTCHA v3 / Turnstile (invisible) | Usually passes with clean IP + real browser. The live browser task handles these. |
| reCAPTCHA v2 checkbox ("I'm not a robot") | Often one click. Image challenges are the wall. |
| reCAPTCHA v2 image grid | Needs a solving service or a human. |
| hCaptcha | Same as above. |
| Arkose / FunCaptcha (games) | Human or specialized solver. |
| Cloudflare "Verify you are human" | The runtime's saved CAPTCHA preference governs it. |

## How DEEPHUNT handles it

1. Every signup/login browser task carries the user's saved CAPTCHA preference:
   `solve` (runtime attempts it), `user_handles` (task pauses, user takes over
   the live browser for that step), or `ask` (default).
2. Playbooks record the exact CAPTCHA type observed on each target so the
   strategy is chosen per site, not guessed.
3. On `CAPTCHA_BLOCKED` the run pauses and notifies the user instead of
   retry-looping (loops burn the IP and the account).

## Paid solving services

Services like 2Captcha exist and can be wired in, but they cost money per
solve and need an API key. **This needs the user's explicit approval and a
spending cap first** — it is NOT enabled by default. Until then: the user
takes over that one step in the live browser, which takes ~10 seconds.

## Rules

- Never pay for a solve without a fresh explicit cap.
- Never loop a CAPTCHA more than twice — pause and escalate.
- A CAPTCHA on a login page is not a vulnerability; do not "test" it.
