#!/bin/bash
# pipeline.sh — parallel PASSIVE recon for one in-scope domain (proxy-safe edition).
# Uses only tools verified working behind the sandbox egress proxy:
#   crt.sh (curl) + waybackurls -> httpx
# Usage: pipeline.sh <domain>
set -u
BIN="$HOME/workspace/hacker-agent/bin"
DATA="$HOME/workspace/hacker-agent/data"
UA="Mozilla/5.0 (hackerone-shiva92)"
d="${1:?usage: pipeline.sh <domain>}"
OUT="$DATA/raw-$d"; mkdir -p "$OUT"; cd "$OUT" || exit 1

# --- phase 1: subdomains via crt.sh (curl, proxy-safe) ---
curl -s --max-time 40 "https://crt.sh/?q=%25.$d&output=json" 2>/dev/null | \
  python3 -c "
import json,sys
try: data=json.load(sys.stdin)
except Exception: data=[]
names=set()
for e in data:
    for n in str(e.get('name_value','')).split('\n'):
        n=n.strip().lower()
        if n and '*' not in n: names.add(n)
print('\n'.join(sorted(names)))" > crt.txt 2>/dev/null &

# --- phase 1b: wayback urls (proxy-safe) ---
echo "$d" | "$BIN/waybackurls" > wb.txt 2>/dev/null &
wait

# merge: crt.sh subs + subdomains extracted from wayback urls
cat crt.txt > subs.txt
grep -oE 'https?://[^/"]+' wb.txt 2>/dev/null | \
  python3 -c "
import sys,urllib.parse
hosts=set()
for line in sys.stdin:
    try: h=urllib.parse.urlparse(line.strip()).hostname
    except Exception: continue
    if h: hosts.add(h.lower())
print('\n'.join(sorted(hosts)))" >> subs.txt
sort -u subs.txt -o subs.txt

# --- phase 2: live probe (httpx verified working) ---
"$BIN/httpx" -l subs.txt -silent -H "User-Agent: $UA" -rl 20 -o live.txt >/dev/null 2>&1

echo "[+] $d: $(wc -l < subs.txt) subdomains, $(wc -l < live.txt) live hosts -> $OUT"
