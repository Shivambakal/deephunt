#!/usr/bin/env python3
"""DEEPHUNT polite HTTP surface probe (curl via egress proxy).
Per seed host: 1x GET / (status/headers/TLS) + 1x CORS origin-reflection check.
Rate: ~1 req per 1.2s per host, sequential. Detection only, no exploitation.
Adobe is EXCLUDED (passive-only per scope file).
"""
import os, subprocess, time, json

R = os.path.expanduser('~/workspace/hacker-agent/deephunt/state/recon-20261004')
UA = 'deephunt-recon/1.0 (bug-bounty research; shiva92)'

TARGETS = {
    'shopify':   {'hosts': ['shopify.com','admin.shopify.com','accounts.shopify.com','partners.shopify.com'], 'headers': []},
    'yahoo':     {'hosts': ['yahoo.com','aol.com','techcrunch.com','mail.yahoo.com','login.yahoo.com'], 'headers': []},
    'robinhood': {'hosts': ['robinhood.com','api.robinhood.com','nummus.robinhood.com','oak.robinhood.com','www.bitstamp.net','saytechnologies.com','say.rocks'], 'headers': ['X-Bug-Bounty: shiva92']},
}

def curl(args, host):
    cmd = ['curl','-s','-D','-','-o','/tmp/probe_body.html','--max-time','25',
           '-A',UA,'-w','\n%{http_code} %{time_total} %{remote_ip}'] + args + [f'https://{host}/']
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=40)
        return p.stdout
    except Exception as e:
        return f'ERR {e}'

def parse(raw):
    lines = raw.split('\n')
    tail = lines[-1] if lines else ''
    code = tail.split()[0] if tail else '?'
    hdrs = {}
    for l in lines:
        if ':' in l and not l.startswith('HTTP'):
            k,v = l.split(':',1); hdrs[k.strip().lower()] = v.strip()[:160]
    return code, hdrs

INTERESTING = ['server','x-powered-by','x-aspnet-version','via','cf-ray','akamai',
    'strict-transport-security','content-security-policy','x-frame-options',
    'access-control-allow-origin','access-control-allow-credentials',
    'set-cookie','location','x-request-id','x-envoy-upstream-service-time']

def main():
    results = {}
    for target, cfg in TARGETS.items():
        for host in cfg['hosts']:
            hargs = []
            for h in cfg['headers']:
                hargs += ['-H', h]
            # 1) baseline
            raw = curl(hargs, host)
            code, hdrs = parse(raw)
            # 2) CORS reflection probe
            raw2 = curl(hargs + ['-H','Origin: https://evil-probe.example.com'], host)
            _, hdrs2 = parse(raw2)
            acao = hdrs2.get('access-control-allow-origin','')
            acac = hdrs2.get('access-control-allow-credentials','')
            cors_flag = 'REFLECTS-ORIGIN' if 'evil-probe.example.com' in acao else ('wildcard' if acao=='*' else 'no')
            rec = {'code': code,
                   'headers': {k:hdrs.get(k,'') for k in INTERESTING if hdrs.get(k)},
                   'cors': cors_flag, 'cors_acac': acac}
            results[f'{target}/{host}'] = rec
            print(f'{target}/{host} -> {code} cors={cors_flag} server={hdrs.get("server","?")[:40]}', flush=True)
            time.sleep(1.2)
    json.dump(results, open(os.path.join(R,'http_probe.json'),'w'), indent=1)
    print('wrote http_probe.json')

if __name__ == '__main__':
    main()
