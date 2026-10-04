#!/usr/bin/env python3
"""DEEPHUNT takeover-fingerprint matcher + safe HTTP verifier.
Reads deephunt/state/recon-20261004/cname_map.txt, flags CNAMEs matching
known dangling-service fingerprints, then does ONE polite GET per candidate
(via egress proxy) checking for the service's 'unclaimed' page signature.
Detection only. NEVER attempts to claim/register anything.
Usage:
    python3 takeover_check.py                        # check existing cname_map.txt
    python3 takeover_check.py --rebuild hosts.txt --label shopify
        # rebuild cname_map.txt from a hosts file via DoH (passive, proxy-aware),
        # then run the fingerprint checks in one pipeline.
"""
import os, re, sys, time, subprocess

try:
    from doh_dns import build_cname_map
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from doh_dns import build_cname_map

R = os.environ.get('DH_STATE_DIR',
        os.path.expanduser('~/workspace/hacker-agent/deephunt/state/recon-20261004'))

# cname-substring -> (service, unclaimed-page signature regex)
FINGERPRINTS = [
    ('github.io', 'GitHub Pages', r"There isn't a GitHub Pages site here"),
    ('herokudns.com', 'Heroku', r'No such app'),
    ('herokuapp.com', 'Heroku', r'No such app'),
    ('s3.amazonaws.com', 'AWS S3', r'NoSuchBucket'),
    ('s3-website', 'AWS S3 website', r'NoSuchBucket|Code: NoSuchBucket'),
    ('cloudfront.net', 'CloudFront', r'ERROR: The request could not be satisfied'),
    ('azurewebsites.net', 'Azure Web Apps', r'404 Web Site not found'),
    ('trafficmanager.net', 'Azure TrafficMgr', r'404'),
    ('vercel.app', 'Vercel', r'DEPLOYMENT_NOT_FOUND'),
    ('netlify.app', 'Netlify', r'Not Found'),
    ('myshopify.com', 'Shopify', r'Sorry, this shop is currently unavailable'),
    ('zendesk.com', 'Zendesk', r'Help Center Closed|Oops'),
    ('statuspage.io', 'Statuspage', r'statuspage'),
    ('surge.sh', 'Surge.sh', r'project not found'),
    ('bitbucket.io', 'Bitbucket', r'Repository not found'),
    ('ghost.io', 'Ghost', r'404'),
    ('wordpress.com', 'WordPress.com', r'doesn.t exist'),
    ('pantheonsite.io', 'Pantheon', r'404'),
    ('readthedocs.io', 'ReadTheDocs', r'404'),
    ('unbouncepages.com', 'Unbounce', r'The requested URL was not found'),
    ('cargocollective.com', 'Cargo', r'404'),
    ('tumblr.com', 'Tumblr', r"There's nothing here"),
    ('helpjuice.com', 'Helpjuice', r'We could not find what'),
    ('helpscoutdocs.com', 'HelpScout', r'No such'),
    ('freshdesk.com', 'Freshdesk', r'Maybe the page'),
    ('smartjobboard.com', 'SmartJobBoard', r'Job board'),
    ('tictail.com', 'Tictail', r'not found'),
    ('wishpond.com', 'Wishpond', r'not found'),
    ('aftership.com', 'AfterShip', r'not found'),
    ('brightcove.com', 'Brightcove', r'not found'),
    ('hatenablog.com', 'HatenaBlog', r'404'),
    ('jindo', 'Jindo', r'not found'),
    ('mashery.com', 'Mashery', r'not found'),
    ('ngrok.io', 'ngrok', r'not found'),
    ('pingdom', 'Pingdom', r'not found'),
    ('s3-website', 'S3 website', r'NoSuchBucket'),
    ('vend', 'Vend', r'not found'),
    ('wordpress', 'WordPress', r'not found'),
]

def get_candidates():
    cands = []
    f = os.path.join(R, 'cname_map.txt')
    if not os.path.exists(f):
        print('no cname_map.txt yet'); return cands
    for line in open(f):
        line = line.strip()
        if '->' not in line: continue
        left, cnames = line.split('->', 1)
        parts = left.strip().split()
        if len(parts) < 2: continue
        target, host = parts[0], parts[1]
        for cname in cnames.split(','):
            cname = cname.strip().lower()
            for pat, svc, sig in FINGERPRINTS:
                if pat in cname:
                    cands.append((target, host, cname, svc, sig))
                    break
    return cands

def http_check(host, sig):
    """One polite GET via proxy. Returns (status, matched_bool, snippet)."""
    try:
        p = subprocess.run(
            ['curl', '-s', '-o', '/tmp/tk_body.html', '-w', '%{http_code}',
             '--max-time', '20', '-A', 'deephunt-recon/1.0 (bug-bounty research; shiva92)',
             f'http://{host}/'],
            capture_output=True, text=True, timeout=30)
        code = p.stdout.strip()
        body = open('/tmp/tk_body.html', errors='ignore').read()
        matched = bool(re.search(sig, body, re.I))
        return code, matched, body[:200].replace('\n', ' ')
    except Exception as e:
        return 'ERR', False, str(e)[:120]

def main():
    args = sys.argv[1:]
    if args and args[0] == '--rebuild':
        # python3 takeover_check.py --rebuild hosts.txt [--label X]
        hosts_file = args[1] if len(args) > 1 else None
        label = 'manual'
        if '--label' in args:
            label = args[args.index('--label') + 1]
        if not hosts_file or not os.path.exists(hosts_file):
            print('usage: takeover_check.py --rebuild HOSTS_FILE [--label X]')
            sys.exit(1)
        hosts = [l.strip() for l in open(hosts_file)
                 if l.strip() and not l.startswith('#')]
        print(f'rebuilding CNAME map for {len(hosts)} hosts via DoH '
              f'(label={label})...', flush=True)
        lines = build_cname_map(hosts, label)
        with open(os.path.join(R, 'cname_map.txt'), 'w') as f:
            f.write('\n'.join(lines) + '\n')
        print(f'wrote cname_map.txt ({len(lines)} chained records)')
        # fall through to the fingerprint checks below
    cands = get_candidates()
    print(f'candidates: {len(cands)}')
    out = open(os.path.join(R, 'takeover_leads.txt'), 'w')
    for target, host, cname, svc, sig in cands:
        code, matched, snip = http_check(host, sig)
        verdict = 'UNCLAIMED-SIGNATURE' if matched else f'http-{code}-no-signature'
        line = f'{target} | {host} | CNAME {cname} | {svc} | {verdict} | {snip[:120]}'
        print(line, flush=True)
        out.write(line + '\n')
        time.sleep(1.2)  # polite: <1 req/s
    out.close()
    print('wrote takeover_leads.txt')

if __name__ == '__main__':
    main()
