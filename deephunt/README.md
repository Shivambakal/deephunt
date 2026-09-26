# DEEPHUNT — the autonomous hunter

Give it a target name. It deploys every weapon, maps the surface, pulls fresh
techniques from the internet, learns from every past mistake, and loops with
novel hypotheses until it finds the vuln or proves the ground is exhausted.

```
python3 deephunt.py --target adobe
```

## The loop

```
INTAKE (passive tools) → INTERNET (fresh techniques) → FUNNEL (10k→500→50→10)
→ HYPOTHESIZE (novel only — memory kills retreads)
→ ADVERSARY/DESIGN → AUTHORIZE → EXECUTE → OBSERVE → LEARN → repeat
```

Stops on: validated high-severity candidate · no novel hypotheses for 2 cycles ·
max cycles · `state/STOP` file.

## Commands

| Command | What it does |
|---|---|
| `--target NAME` | Hunt `targets/NAME.yaml` (default 3 cycles) |
| `--max-cycles N` | Cycle cap |
| `--passive-only` | Mapping only — no test proposals, no active tools |
| `--list-tools [--phase X]` | Arsenal inventory with availability |
| `--learn [--target X]` | Print the memory: rejected hypotheses, lessons, tried paths |
| `--daemon --interval-hours H` | **100-year mode**: run, learn, sleep H hours, repeat until `state/STOP` exists. Crashes are caught, logged, survived |

## Weapons (26 wired, registry built for 50)

- **passive (17)**: crtsh, subfinder, httpx, headers, robots_sitemap, js_extract,
  js_secrets, wayback, gau, urlscan, github_recon, tech_detect, takeover,
  cors_probe, tls_info, param_miner, proxy_route
- **active (gated, 8)**: nuclei, nmap, ffuf, katana, graphql_probe, dns_axfr,
  repeater, intruder
- **operator**: browser_probe — emits a precise browser-task brief when a step
  needs the agent/browser instead of silently skipping it

## The brain (think.py + train.py + knowledge/)

- `knowledge/techniques.yaml` — 41 technique cards across 21 vuln classes,
  distilled from disclosed bounty history (IDOR shapes, races, JWT, SSRF,
  AI injection, cache poisoning, subdomain takeover...)
- `knowledge/past_attacks.md` — bounty shapes that keep paying (vendors fix
  instances, not classes — hunt the class)
- `train.py` — matches funnel signals against technique cards, ranked by
  evidence
- `think.py` — **seven thinking modes** interrogate the same evidence:
  predator (cross trust boundaries), architect (dev shortcuts), accountant
  (follow the value), saboteur (race the state), ghost (where is identity
  NOT re-checked), scholar (technique cards), oracle (past bounty shapes +
  intel). The council dedupes against memory, diversifies across modes,
  and returns ranked novel seeds.

## Self-improvement

Every run ends with `write_postmortem()`: `state/<target>_postmortem_<ts>.md`
records tool hit rates, gaps, and lessons; gaps accumulate in `ROADMAP.md`.
The program upgrades itself run after run — more tools, more techniques,
fewer repeated mistakes.

New tool = subclass `tools/base.py:ToolAdapter`, decorate with `@register`,
implement `run(ctx) -> [finding]`. It appears in `--list-tools` automatically.

## Safety rails (non-negotiable)

- **Active tools are gated**: they run ONLY when the target profile has
  `active_allowed: true` AND a ResearchSession `TestAuthorization` is minted
  for the current test with matching `scope_hosts`. Otherwise they log
  `BLOCKED` with the reason. Adobe ships with `active_allowed: false` until
  the Intigriti test plan is read.
- No DoS flags, no brute force, rate-limited, owned accounts/data only.
- Secrets never logged (proxy logger redacts auth-shaped values).

## Learning

`learn.py` reads `data/brain/sessions/*.json` (rejected hypotheses + lessons),
`intel/*-novel-attacks.md`, `intel/*-endpoint-funnel.md`, and
`proxy/logs/*/traffic.jsonl` (tried paths). `is_novel()` refuses to re-test a
killed idea — the loop learns instead of looping blind.

`internet.py` builds queries from the target profile (`tech_terms`,
`vuln_classes`), pulls recent writeups, and converts technique-shaped hits
into hypothesis seeds. Queries are always saved to
`state/internet_<target>.json` so the agent can enrich them with deeper
research.

## State

- `state/<target>.json` — cycles, findings, operator tasks, stop reason
- `logs/<target>_<ts>.log` — full run log
- `state/operator_task_*.md` — browser briefs for app-layer steps
- `state/STOP` — create to halt the loop gracefully

## Adding a target

Copy `targets/_template.yaml` → `targets/<name>.yaml`. Fill scope, program,
`hypothesis_seeds`, and `operator_brief`. Keep `active_allowed: false` until
you've read the program's test plan.
