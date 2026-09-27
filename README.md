# DEEPHUNT

Autonomous, authorized bug-bounty research system. It hunts vulnerabilities the
way a disciplined human researcher would: form a hypothesis, check it
adversarially, run the smallest safe experiment, learn from the result, and
never confuse a guess with a finding.

Built and operated by Shivam Bakal. Private research repository.

## How it works

```
intake → intel → reasoning → intel compiler → world model → attack graph
  → hypotheses → difficulty-aware planning → authorization
  → differential testing → oracle → independent verifier
  → causal learning → regression → report
```

Every active test runs inside `brain/ResearchSession`:

1. `propose_test()` states hypothesis, expected observation, exact hosts,
   authorization basis, and success/failure criteria.
2. A 5-question adversarial self-check must approve it.
3. Approval mints a `TestAuthorization`; `Engine.execute()` refuses anything
   without a valid token, dry-runs first, and scope-gates before transmitting.
4. Findings stay **unconfirmed** until `compete_finding()` disproves the
   alternative explanations.

The brain (`brain/` v4) adds 9 thinking modes, a world model, an information-
gain experiment planner, 6-role debate, and a calibration gate. The knowledge
base (`deephunt/knowledge/`) holds technique cards, historical cases, and
negative examples grown by the closed learning loop.

## AI attack modules

`deephunt/ai_attacks/` covers prompt injection, jailbreaks, RAG poisoning,
agent/tool abuse, and extraction — propose-only by default, with deterministic
canary scoring. Adapters exist for Garak, PyRIT, and JailbreakBench corpora.

`prompt_guard_oracle.py` wraps a local Meta **Llama Prompt Guard 2 (86M)**
classifier as an optional, offline defense oracle: it scores whether a text
looks like an injection/jailbreak attempt and returns *evidence, never a
verdict*. Known blind spot (documented in code and bench): DAN-style roleplay
jailbreaks score as benign. It must never be the sole verifier.

## Quickstart

Prerequisites: Python 3.10+, the tool binaries you plan to use
(`bin/` lists them; a tool goes live the moment its binary is installed).

```bash
cd deephunt
./deephunt.sh start "shopify,yahoo" 2 1      # targets, hours between runs, cycles
./deephunt.sh status
./deephunt.sh stop
```

Target rotation, throttle, and per-target rules live in `CAMPAIGN_STATE.md`.
**Only hosts listed in `scope.yaml` are ever touched.** If a target's rules
say passive-only, it stays passive-only.

Run the mock proving ground (no network, deterministic):

```bash
cd deephunt
python3 -m pytest ai_attacks/ -q        # AI module tests
python3 test_bench.py                   # 41-case bench: vuln/patched mock twins
```

## Repository map

| Path | What it is |
|---|---|
| `deephunt/` | The engine: pipeline, brain wiring, attack modules, bench |
| `deephunt/ai_attacks/` | AI-offensive modules + Prompt Guard oracle |
| `deephunt/knowledge/` | Technique cards, cases, negative examples |
| `deephunt/bench_targets/` | Vulnerable mock apps + patched twins (practice dummies) |
| `brain/` | ResearchSession, thinking modes, episodic memory |
| `intel/` | Intel collectors (news watcher, global refresh) |
| `proxy/` | Intercept proxy tooling |
| `reports/` | Generated hunt reports |
| `scope.yaml` | **The only hosts this system may ever touch** |
| `CAMPAIGN_STATE.md` | Master state: mission, rules, current rotation |
| `deep-vuln-methodology.md` | The vulnerability-hunting methodology |

Deeper docs: `deephunt/ARCHITECTURE.md`, `deephunt/ROADMAP.md`.

## Safety

- Authorized, in-scope targets only. No brute force, DoS, malware, phishing,
  social engineering, or stolen credentials. No real-user data.
- Nothing is submitted to any program automatically — reports are drafted,
  humans submit.
- No spending without an explicit budget. Test accounts use the dedicated
  research identity, never personal accounts.
- See `SECURITY.md` for the disclosure policy.

## Status (honest)

The closed loop is proven on deterministic seeded mocks: 4 vulnerable mock
chains found end-to-end, 4 patched twins clean, regression replay green.
**No confirmed real-world findings yet** — the mock range proves the rifle
fires, not that it can hunt. Real hunts run throttled against in-scope
programs; findings get reported here only when confirmed.
