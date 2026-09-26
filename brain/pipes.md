# PIPES — the thinking architecture (2026-09-26)

Every hunt, every target, every test flows through these 8 pipes in order.
No stage is skipped. Thinking is written down at each pipe, not kept in the head.

## PIPE 1 — INTAKE
Pull everything relevant into working context before a single new thought:
ledger, past sessions, recon reports, playbook ideas, disclosed writeups, program scope.
Output: the raw material list. No conclusions yet.

## PIPE 2 — HYPOTHESIZE
Form concrete, falsifiable claims. Format: "I believe [endpoint/flow] violates
[invariant], because [reason]." Vague claims die here ("maybe auth is broken" is not a hypothesis).

## PIPE 3 — ADVERSARY
The red-team voice tries to kill every hypothesis before it costs a single request:
- What benign explanation fits the same evidence?
- Is it excluded by program scope?
- Is it a known/duplicate class on this target?
- Is there a cheaper test that settles it?
Survivors earn the right to be tested. Kills are recorded with the reason.

## PIPE 4 — DESIGN
The smallest safe experiment that distinguishes the hypothesis from its benign twin:
exact requests, exact expected observation, exact failure observation.
If the test can't distinguish, redesign — don't execute.

## PIPE 5 — AUTHORIZE
Scope check + session-minted TestAuthorization (brain/gate.py). No token, no execution.
This pipe is structural, not advisory.

## PIPE 6 — EXECUTE
Fire through the proxy tooling (logger → repeater → paced intruder), dry-run first,
in-scope hosts only, owned sessions only. Every request logged.

## PIPE 7 — OBSERVE
Record raw observations with zero interpretation. What the server returned,
what rendered, what changed state — facts first, theories later.

## PIPE 8 — LEARN
What died and why. What survived and what it needs next. Which future hypotheses
change because of this. Written to the session + ledger + cross-session knowledge.
A test that teaches nothing was a wasted test.

## Rules
- Thinking flows forward through the pipes; learning loops back to PIPE 1.
- Each pipe's output is written, not spoken — the hunt log is the memory.
- Speed comes from killing bad hypotheses in PIPE 3, not from skipping pipes.
- Human-style means: show the doubt, show the kill, show the reason — not just the survivor.
