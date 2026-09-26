# OPS — weapons status board
War-room for the bug-bounty deep hunt. Updated 2026-09-27 (night IST).

## Arsenal
| Weapon | Status | Location / notes |
|---|---|---|
| Burp-equivalent intercept proxy (mitmproxy 12.2.3 + logger/modify addons, JSONL, secret redaction) | **LIVE** — HTTPS intercept validated 200 OK through egress chain | `proxy/start.sh [port]` (default 8080). Logs: `proxy/logs/<date>/traffic.jsonl`. Repeater: `proxy/repeater.py`, Intruder: `proxy/intruder.py` |
| nmap 7.94SVN | **LIVE** | system binary (`/usr/bin/nmap`) |
| nuclei v3.11.1 | **LIVE** | `ops/bin/nuclei` (templates not yet pulled — `nuclei -update-templates` on first authorized use) |
| subfinder v2.16.0 | **LIVE** | `ops/bin/subfinder` — passive subdomain enum |
| httpx v1.12.0 | **LIVE** | `ops/bin/httpx` — live-host probing (title/tech/status/TLS) |
| gau v2.2.4 | **LIVE** | `ops/bin/gau` — historic URL harvest |
| ffuf v2.3.0 | **LIVE** | `ops/bin/ffuf` — gated content discovery, rate-limited |
| katana | **LIVE** (installing/verify) | `ops/bin/katana` — gated JS-aware crawler |
| DEEPHUNT brain | **LIVE** | `deephunt/think.py` (7 thinking modes) + `deephunt/train.py` (41 technique cards) + `deephunt/knowledge/` |
| DEEPHUNT daemon | **LIVE** | `--daemon --interval-hours H` — runs until `state/STOP`; postmortem → `ROADMAP.md` every run |
| JS/API endpoint mapper (passive) | running (subagent) | → `intel/adobe-endpoint-funnel.md` |
| Browser (managed Chromium) | live | via browser tasks; NOTE: managed browser is NOT routed through our proxy — our own proxied traffic uses curl/python with `https_proxy=http://127.0.0.1:8080` |
| ResearchSession gate + brain loop | **ENFORCED** | `brain/` — no security test without minted TestAuthorization |

DEEPHUNT adapter count: **26** (17 passive, 8 gated active, 1 operator).

## Egress lesson (2026-09-26 — do not relearn)
This VM reaches the internet ONLY via `hatch-egress-proxy:3128` (auth in env).
mitmproxy must chain: `--mode upstream:http://hatch-egress-proxy:3128`
`--upstream-auth <from env>` `--set ssl_insecure=true` (egress does its own
TLS interception with a self-signed chain). `proxy/start.sh` encapsulates this.

## Rules of fire
- **PASSIVE tools** (curl page fetches, JS bundle reads, crt.sh, DNS): free to use
  on in-scope hosts any time — this is mapping, not attacking.
- **ACTIVE tools** (nmap scans, nuclei templates, intruder fuzzing, repeater
  replays): ONLY against in-scope hosts AND only after the program's test plan /
  policy is read AND the shot is authorized by a ResearchSession TestAuthorization.
- **NEVER**: DoS, brute force, real-user data, paid/trial activation, production
  customer environments, anything the test plan marks out-of-scope.
- Adobe specifically: test-plan attachment (Intigriti, login-gated) takes precedence
  over all general guidance — phase-1 browser task is extracting it now. No active
  scanning of Adobe until those rules are read.

## Kill chain for a target
1. `proxy/start.sh 8080` (background) → route own recon traffic via
   `https_proxy=http://127.0.0.1:8080`
2. Endpoint funnel: `intel/<target>-endpoint-funnel.md`
3. ResearchSession: hypothesis → adversarial → propose_test → authorization
4. Repeater/intruder for the single-variable experiment; record_result()
5. compete_finding() → draft report
