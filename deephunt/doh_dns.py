#!/usr/bin/env python3
"""DEEPHUNT proxy-aware DNS resolver via DNS-over-HTTPS (reference implementation).

Sandbox reality (2026-10-04): direct UDP/TCP DNS is SHIMMED (fake 198.18.x.x
answers) and raw sockets are blocked, so python `dns`/`socket` lookups are
UNUSABLE here. curl honors the authenticated egress-proxy env vars, so this
module queries DNS-over-HTTPS (dns.google primary, cloudflare-dns.com fallback)
through the proxy and parses the JSON answers.

PASSIVE ONLY: DoH queries never touch the queried name's own infrastructure --
they only ask public resolvers for public records. Safe against any target.

Usage:
    python3 doh_dns.py example.com A
    python3 doh_dns.py www.example.com --chain
    python3 doh_dns.py --bulk hosts.txt --type A --out results.json

Library:
    from doh_dns import resolve, resolve_cname_chain, resolve_bulk, build_cname_map
"""
import argparse, json, os, subprocess, sys, time, urllib.parse

UA = 'deephunt-recon/1.0 (bug-bounty research; shiva92)'

PROVIDERS = {
    'google':     ('https://dns.google/resolve', {}),
    'cloudflare': ('https://cloudflare-dns.com/dns-query',
                   {'Accept': 'application/dns-json'}),
}

STATUS_TEXT = {0: 'NOERROR', 1: 'FORMERR', 2: 'SERVFAIL', 3: 'NXDOMAIN',
               4: 'NOTIMP', 5: 'REFUSED', 9: 'NOTAUTH'}

# numeric type -> name (what the DoH JSON returns)
TYPES = {1: 'A', 2: 'NS', 5: 'CNAME', 6: 'SOA', 15: 'MX', 16: 'TXT',
         28: 'AAAA', 257: 'CAA', 255: 'ANY'}


def _doh_query(name, qtype, provider, timeout=20):
    """One DoH query. Returns (payload_dict, elapsed_ms, provider) or raises."""
    base, extra_hdrs = PROVIDERS[provider]
    q = urllib.parse.urlencode({'name': name, 'type': qtype})
    cmd = ['curl', '-s', '--max-time', str(timeout), '-A', UA,
           '-w', '\n%{http_code} %{time_total}']
    for k, v in extra_hdrs.items():
        cmd += ['-H', f'{k}: {v}']
    cmd.append(f'{base}?{q}')
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 15)
    body, sep, tail = p.stdout.rpartition('\n')
    if not sep:
        raise RuntimeError(f'{provider}: empty curl response')
    http_code = tail.split()[0] if tail.split() else '?'
    if http_code != '200':
        raise RuntimeError(f'{provider}: HTTP {http_code} for {name}/{qtype}')
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as e:
        raise RuntimeError(f'{provider}: bad JSON ({e})')
    elapsed_ms = int((time.time() - t0) * 1000)
    return payload, elapsed_ms, provider


def resolve(name, qtype='A', provider=None, retries=2, timeout=20):
    """Resolve one name/qtype via DoH. Never raises; error goes in the dict."""
    order = [provider] if provider else ['google', 'cloudflare']
    last_err = None
    for prov in order:
        for attempt in range(retries + 1):
            try:
                payload, elapsed_ms, used = _doh_query(name, qtype, prov, timeout)
                status = payload.get('Status', -1)
                answers = []
                for a in payload.get('Answer', []) or []:
                    tname = TYPES.get(a.get('type'), str(a.get('type')))
                    data = str(a.get('data', '')).rstrip('.')
                    if tname == 'TXT':
                        data = data.strip('"')
                    answers.append({'name': str(a.get('name', '')).rstrip('.'),
                                    'type': tname, 'ttl': a.get('TTL'),
                                    'data': data})
                return {'name': name, 'qtype': qtype, 'status': status,
                        'status_text': STATUS_TEXT.get(status, f'UNKNOWN({status})'),
                        'answers': answers, 'elapsed_ms': elapsed_ms,
                        'provider': used, 'error': None}
            except Exception as e:
                last_err = str(e)
                if attempt < retries:
                    time.sleep(1.5 * (attempt + 1))  # backoff, then retry
        # provider exhausted -> fall through to next provider
    return {'name': name, 'qtype': qtype, 'status': -1,
            'status_text': 'QUERY-FAILED', 'answers': [],
            'elapsed_ms': 0, 'provider': None, 'error': last_err}


def resolve_cname_chain(name, max_hops=8):
    """Follow the CNAME chain for `name` via explicit CNAME-type DoH queries.

    Returns {'chain': [n0, n1, ...], 'terminal': <last name>,
             'A': [...], 'AAAA': [...], 'error': None|str}.
    A records are taken from the terminal node's A/AAAA answers.
    """
    chain = [name]
    seen = {name.lower()}
    for _ in range(max_hops):
        r = resolve(chain[-1], 'CNAME')
        if r['error']:
            return {'chain': chain, 'terminal': chain[-1], 'A': [], 'AAAA': [],
                    'error': r['error']}
        cnames = [a['data'] for a in r['answers'] if a['type'] == 'CNAME']
        if not cnames:
            break
        nxt = cnames[0].rstrip('.')
        if nxt.lower() in seen:
            return {'chain': chain, 'terminal': chain[-1], 'A': [], 'AAAA': [],
                    'error': f'CNAME loop at {nxt}'}
        seen.add(nxt.lower())
        chain.append(nxt)
    else:
        return {'chain': chain, 'terminal': chain[-1], 'A': [], 'AAAA': [],
                'error': f'chain exceeded {max_hops} hops'}
    terminal = chain[-1]
    a = resolve(terminal, 'A')
    aaaa = resolve(terminal, 'AAAA')
    err = a['error'] or aaaa['error']
    return {'chain': chain, 'terminal': terminal,
            'A': [x['data'] for x in a['answers'] if x['type'] == 'A'],
            'AAAA': [x['data'] for x in aaaa['answers'] if x['type'] == 'AAAA'],
            'error': err}


def resolve_bulk(entries, qtype='A', delay=0.5, progress=False):
    """Sequential polite bulk resolve. entries: list of names or (name, qtype).

    ~2 queries/sec default -- well within public DoH resolver courtesy limits.
    Returns list of resolve() dicts in input order.
    """
    results = []
    for e in entries:
        n, t = (e if isinstance(e, (list, tuple)) else (e, qtype))
        r = resolve(n, t)
        results.append(r)
        if progress:
            print(f'{n}/{t} -> {r["status_text"]} '
                  f'{len(r["answers"])} ans via {r["provider"]} '
                  f'{r["elapsed_ms"]}ms' + (f' ERR {r["error"]}' if r["error"] else ''),
                  flush=True)
        time.sleep(delay)
    return results


def build_cname_map(hosts, label='manual'):
    """Resolve CNAME chains for hosts; return lines in cname_map.txt format.

    hosts: iterable of 'host' or 'target host' strings (matches recon state format).
    Line format: '<target> <host> -> <cname1>,<cname2>,...'  (only hosts with a
    real CNAME chain are emitted -- plain A-record hosts are skipped).
    """
    lines = []
    for h in hosts:
        h = h.strip()
        if not h or h.startswith('#'):
            continue
        parts = h.split()
        target, host = (parts[0], parts[1]) if len(parts) >= 2 else (label, parts[0])
        try:
            c = resolve_cname_chain(host)
        except Exception as e:  # pragma: no cover - resolve() never raises
            print(f'{host}: UNEXPECTED {e}', flush=True)
            continue
        if c['error']:
            print(f'{host}: chain-error {c["error"]}', flush=True)
            continue
        if len(c['chain']) > 1:
            cnames = ','.join(c['chain'][1:])
            lines.append(f'{target} {host} -> {cnames}')
            print(f'{host} -> {cnames}  (terminal A: {",".join(c["A"]) or "?"})',
                  flush=True)
        time.sleep(0.5)
    return lines


def _read_hosts_file(path):
    with open(path) as f:
        return [l.strip() for l in f if l.strip() and not l.startswith('#')]


def main(argv=None):
    ap = argparse.ArgumentParser(description='DoH DNS resolver (proxy-aware)')
    ap.add_argument('name', nargs='?', help='hostname to resolve')
    ap.add_argument('qtype', nargs='?', default='A', help='record type (default A)')
    ap.add_argument('--chain', action='store_true', help='follow CNAME chain')
    ap.add_argument('--provider', choices=list(PROVIDERS),
                    help='force one DoH provider')
    ap.add_argument('--bulk', metavar='HOSTS_FILE',
                    help='resolve one host per line (TYPE from --type)')
    ap.add_argument('--type', dest='bulk_type', default='A',
                    help='record type for --bulk (default A)')
    ap.add_argument('--out', help='write bulk results as JSON to file')
    ap.add_argument('--cname-map', metavar='HOSTS_FILE',
                    help='build cname_map.txt lines for hosts file')
    ap.add_argument('--label', default='manual', help='target label for cname map')
    a = ap.parse_args(argv)

    if a.cname_map:
        for line in build_cname_map(_read_hosts_file(a.cname_map), a.label):
            print(line)
        return 0
    if a.bulk:
        res = resolve_bulk(_read_hosts_file(a.bulk), a.bulk_type, progress=True)
        if a.out:
            json.dump(res, open(a.out, 'w'), indent=1)
            print(f'wrote {a.out} ({len(res)} results)')
        else:
            print(json.dumps(res, indent=1))
        return 0 if all(r['error'] is None for r in res) else 2
    if not a.name:
        ap.print_help()
        return 1
    if a.chain:
        c = resolve_cname_chain(a.name)
        print(json.dumps(c, indent=1))
        return 0 if c['error'] is None else 2
    r = resolve(a.name, a.qtype, provider=a.provider)
    print(json.dumps(r, indent=1))
    return 0 if r['error'] is None else 2


if __name__ == '__main__':
    sys.exit(main())
