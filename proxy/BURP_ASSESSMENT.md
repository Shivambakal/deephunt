# Burp Suite assessment — 2026-09-27

## Verdict: NOT installable/runnable here

1. **Burp Suite Community Edition is a Java Swing GUI application.** There is
   no headless mode, no CLI scan mode, and no automation API in Community.
   (Burp Enterprise has a CLI driver, but it is a paid product.)
2. **No Java in this sandbox** (`java` not installed; installing a JRE +
   running a Swing GUI headless would still leave us with an interactive GUI
   that no agent can drive — Xvfb is present but Burp Community under Xvfb
   is still point-and-click).
3. Burp's own terms prohibit automated use of Community for this kind of
   pipeline anyway.

## What we did instead: Burp-workflow parity on the mitmproxy stack

| Burp workflow | Our equivalent |
|---|---|
| Target scope | `scope.yaml` allowlist + `addons/scope.py` tags every flow in/out of scope (tag-only; enforcement is default-deny in `intruder.py`) |
| HTTP history | `addons/logger.py` → `logs/<date>/traffic.jsonl` (secrets redacted) |
| Search history | `proxy/search.py` — by host, URL regex, status, method, header regex, body regex |
| Match & Replace | `addons/modify.py` + `rules.yaml` (add/remove/replace headers, set params; e.g. auto-injects `X-Bug-Bounty: shiva92` on Robinhood scope) |
| Repeater | `proxy/repeater.py` — tweak and resend single requests |
| Intruder: Sniper | `intruder.py --mode sniper` |
| Intruder: Battering ram | `intruder.py --mode battering-ram` |
| Intruder: Pitchfork | `intruder.py --mode pitchfork` (NEW 2026-09-27) |
| Intruder: Cluster bomb | `intruder.py --mode cluster-bomb` (NEW 2026-09-27) |
| Intruder: Grep-Match | `intruder.py --grep REGEX` (NEW 2026-09-27; body snippets scanned, never persisted) |
| Rate limiting | hard floor 1 req/sec in intruder.py; never exceeded |
| Default-deny scope | intruder.py refuses any host not in scope.yaml; BLOCKLIST for manual-only programs |

All intruder modes keep: baseline request first, response diffing
(status/length/timing), results JSON to `logs/intruder-<ts>.json`.
