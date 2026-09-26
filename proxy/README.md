# Headless Burp-Suite-equivalent proxy harness

Authorized security research only. Human-paced, read-only validation traffic.
Secrets are redacted in logs (Authorization/Cookie/Set-Cookie values, secret
query params, credential-looking bodies).

## Layout

```
proxy/
  venv/            mitmproxy 12.2.3 virtualenv
  addons/
    logger.py      JSONL traffic log -> logs/<date>/traffic.jsonl
    modify.py      match-and-replace rules engine (rules.yaml)
  repeater.py      Burp Repeater: resend a logged request, tweak, diff
  intruder.py      Burp Intruder: constrained payload fuzzer (sniper/battering-ram)
  scope.yaml       default-DENY target allowlist
  rules.yaml       modify rules
  logs/            traffic + intruder results
  README.md
```

## 1. Start the proxy

```bash
cd ~/workspace/hacker-agent/proxy
./venv/bin/mitmdump -p 8080 \
  -s addons/logger.py \
  -s addons/modify.py
```

For a visible UI instead: `./venv/bin/mitmweb -p 8080 -s addons/logger.py -s addons/modify.py`
then open http://127.0.0.1:8081.

Traffic logs land in `logs/<YYYY-MM-DD>/traffic.jsonl`. Each record carries a
`seq` number — repeater addresses requests by `seq`.

## 2. Route traffic through it

**curl:**
```bash
curl -x http://127.0.0.1:8080 https://example.com -k
```
(The `-k` is needed only until the mitmproxy CA is trusted; install
`~/.mitmproxy/mitmproxy-ca-cert.pem` into the system store to avoid it.)

**python-requests:**
```python
import requests
proxies = {"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"}
r = requests.get("https://example.com", proxies=proxies, verify=False)
```

**requests via env (applies to most tools):**
```bash
export http_proxy=http://127.0.0.1:8080 https_proxy=http://127.0.0.1:8080
```

## 3. Repeater (resend + diff)

```bash
./venv/bin/python repeater.py --list --n 20
./venv/bin/python repeater.py --seq 42 --send                  # baseline resend
./venv/bin/python repeater.py --seq 42 --send \
  --method POST --header "X-Test: 1" --param "debug=1" --body '{"a":1}'
```

The diff report covers status, length, added/removed/changed headers, and a
unified body diff vs the originally logged response — the differential core
of methodology §4.

## 4. Intruder (constrained fuzzer)

Base request JSON with `§markers§` (Burp style):

```json
{
  "method": "GET",
  "url": "https://api.pinterest.com/v3/§endpoint§?x=1",
  "headers": {"User-Agent": "ResearchBot/1.0"},
  "body": ""
}
```

```bash
./venv/bin/python intruder.py --request base.json --payloads payloads.txt \
  --mode sniper --rate 2.0 --max 25
```

Safety rails (non-negotiable):
- **Default-deny allowlist** (`scope.yaml`): any host not listed is refused.
- **Hard blocklist**: FDJ/Kindred brands, Booking.com, Okta/Auth0, Superbank,
  CoinDCX, Oda, Basecamp, Aptible, Artsy — automation is prohibited there,
  always refused.
- **Rate limit**: default 1 req / 2 s, floor 1 req / s, plus `--max` cap.
- Flags responses that differ from baseline in status, length (>10% or 50B),
  or timing (>3x + 2s).

## 5. Modify rules

Edit `rules.yaml`, restart mitmdump. Rule match fields: `host` (regex),
`path` (regex), `method`, `direction` (request/response). Actions:
`add_header`, `remove_header`, `replace_header`, `set_param`,
`remove_param`, `set_body`, `drop`.

## Rules of engagement

- Human-paced, minimal requests. The intruder's rate floor exists for a reason.
- scope.yaml is the authorization boundary. Manual-only programs stay manual.
- Logs redact secrets — but never paste real credentials into payloads or rules.
- Validate differentials (method, version, auth state), never brute-force.

## 4. Sandbox egress chaining (2026-09-26 lesson)
This VM only reaches the internet via `hatch-egress-proxy:3128` (auth from env).
Plain `mitmdump -p 8080` will fail upstream. Always start via:
```bash
./start.sh [port]   # chains correctly; auth read from environment, never hardcoded
```
Equivalent flags: `--mode upstream:http://hatch-egress-proxy:3128 --upstream-auth "$AUTH" --set ssl_insecure=true`
(`ssl_insecure` because the egress proxy does its own TLS interception.)
Then route tools: `export https_proxy=http://127.0.0.1:8080 http_proxy=http://127.0.0.1:8080`
