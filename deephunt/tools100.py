"""DEEPHUNT tools-100 registry — every tool Shivam listed, as data.

95 unique tools (5 dupes in the original 100 merged: hakrawler, arjun,
kiterunner, param-miner, inql). Each entry:

    name, category, phase, binary, takes, args, install, description

phase: passive | active | manual (GUI/human-driven, never auto-run) |
       resource (wordlist/corpus, not a runner)
takes: domain | url | host | none — what the args template needs.
args: template with {domain} {url} {host} {bin_dir} placeholders.

Covered-by: tools that already have a hand-built adapter are marked
covered_by and skipped by the generic adapter factory (no duplicates).
"""
from __future__ import annotations

# (name, category, phase, binary, takes, args-template, install-hint, description, covered_by)
TOOLS100 = [
    # ---- recon / assets (passive) ----
    ("amass", "recon", "passive", "amass", "domain", "enum -passive -d {domain}", "go install github.com/owasp-amass/amass/v4/...@latest", "OWASP attack-surface mapping", "amass"),
    ("assetfinder", "recon", "passive", "assetfinder", "domain", "--subs-only {domain}", "go install github.com/tomnomnom/assetfinder@latest", "subdomain discovery via public sources"),
    ("findomain", "recon", "passive", "findomain", "domain", "-t {domain} -q", "curl -sL https://github.com/findomain/findomain/releases/latest/download/findomain-linux.zip", "fast cross-platform subdomain enumerator"),
    ("sublist3r", "recon", "passive", "sublist3r", "domain", "-d {domain} -o /tmp/dh_sublist3r.txt", "pip install sublist3r / apt install sublist3r", "subdomain enumeration via OSINT"),
    ("sudomy", "recon", "passive", "sudomy", "domain", "-d {domain} -p", "go install github.com/c3l3si4n/sudomy@latest", "subdomain enumeration + takeover checks"),
    ("shuffledns", "recon", "passive", "shuffledns", "domain", "-d {domain} -r resolvers.txt", "go install github.com/projectdiscovery/shuffledns/cmd/shuffledns@latest", "massdns-backed bruteforce wrapper"),
    ("puredns", "recon", "passive", "puredns", "domain", "bruteforce wordlist.txt {domain} -r resolvers.txt", "go install github.com/d3mondev/puredns/v2@latest", "fast domain resolver/bruteforcer"),
    ("dnsgen", "recon", "passive", "dnsgen", "none", "--help", "pip install dnsgen", "subdomain permutation generator (feeds resolvers)"),
    ("massdns", "recon", "passive", "massdns", "domain", "-r resolvers.txt -t A -o S -w /tmp/dh_massdns.txt", "apt install massdns / build from source", "high-performance DNS stub resolver"),
    ("dnsx", "recon", "passive", "dnsx", "domain", "-d {domain} -silent -a -cname", "go install github.com/projectdiscovery/dnsx/cmd/dnsx@latest", "fast multipurpose DNS toolkit", "dnsx"),
    ("asnmap", "recon", "passive", "asnmap", "domain", "-d {domain} -silent", "go install github.com/projectdiscovery/asnmap/cmd/asnmap@latest", "ASN/CIDR expansion for a target org"),
    ("mapcidr", "recon", "passive", "mapcidr", "none", "--help", "go install github.com/projectdiscovery/mapcidr/cmd/mapcidr@latest", "CIDR math for attack-surface expansion"),
    ("naabu", "recon", "passive", "naabu", "host", "-host {host} -top-ports 100 -silent", "go install github.com/projectdiscovery/naabu/v2/cmd/naabu@latest", "fast port scanner", "naabu"),
    ("masscan", "recon", "active", "masscan", "host", "{host} -p1-1000 --rate 1000 -oL /tmp/dh_masscan.txt", "apt install masscan", "internet-scale port scanner (throttle on scope!)"),
    ("unicornscan", "recon", "active", "unicornscan", "host", "{host}:1-1000", "apt install unicornscan", "async port scanner with OS fingerprinting"),
    ("fierce", "recon", "passive", "fierce", "domain", "--domain {domain} --subdomains", "pip install fierce / apt install fierce", "DNS recon incl. zone-transfer attempts"),
    ("dnsrecon", "recon", "passive", "dnsrecon", "domain", "-d {domain} -t std", "pip install dnsrecon / apt install dnsrecon", "DNS enumeration script"),
    ("dnsenum", "recon", "passive", "dnsenum", "domain", "{domain}", "apt install dnsenum", "multithreaded DNS enumeration perl script"),
    ("dnsmap", "recon", "passive", "dnsmap", "domain", "{domain}", "apt install dnsmap", "subdomain bruteforcer with built-in wordlist"),
    ("spiderfoot", "recon", "passive", "spiderfoot", "domain", "-s {domain} -t all -q", "pip install spiderfoot / docker", "OSINT automation framework"),
    # ---- web discovery ----
    ("gobuster", "discovery", "active", "gobuster", "url", "dir -u {url} -w wordlist.txt -t 40 -q", "go install github.com/OJ/gobuster/v3@latest / apt install gobuster", "fast directory/DNS brute-forcer"),
    ("feroxbuster", "discovery", "active", "feroxbuster", "url", "-u {url} -w wordlist.txt -q", "curl install from github.com/epi052/feroxbuster", "recursive content discovery (rust)"),
    ("dirsearch", "discovery", "active", "dirsearch", "url", "-u {url} -q", "pip install dirsearch / git clone maurosoria/dirsearch", "web path scanner"),
    ("dirbuster", "discovery", "manual", "dirbuster", "url", "", "apt install dirbuster (GUI)", "GUI content brute-forcer — human-driven"),
    ("hakrawler", "discovery", "active", "hakrawler", "url", "-url {url} -depth 2 -plain", "go install github.com/hakluke/hakrawler@latest", "fast endpoint/URL crawler"),
    ("gospider", "discovery", "active", "gospider", "url", "-s {url} -d 2 -q", "go install github.com/jaeles-project/gospider@latest", "fast web spider"),
    ("kiterunner", "discovery", "active", "kiterunner", "url", "brute {url} -w routes.kite -q", "docker pull assetnote/kiterunner", "API route brute-forcer (OpenAPI-aware)", "kiterunner"),
    ("arjun", "discovery", "active", "arjun", "url", "-u {url} --stable", "pip install arjun", "HTTP parameter discovery"),
    ("paramspider", "discovery", "active", "paramspider", "domain", "-d {domain} -o /tmp/dh_paramspider.txt", "pip install paramspider / git clone devanshbatham/paramspider", "parameter mining from web archives"),
    ("paramminer", "discovery", "manual", "paramminer", "url", "", "Burp extension — human-driven", "cache-poisoning oriented param discovery — human-driven"),
    ("x8", "discovery", "active", "x8", "url", "-u {url} -w params.txt -q", "cargo install x8 / github.com/Sh1Yo/x8", "hidden parameter discovery (rust)"),
    ("parameth", "discovery", "active", "parameth", "url", "-u {url}", "go install github.com/maikthulhu/parameth@latest", "parameter brute-forcer"),
    ("linkfinder", "discovery", "passive", "linkfinder", "url", "-i {url} -o cli", "pip install linkfinder / git clone gerbenjavado/linkfinder", "endpoint discovery in JS files"),
    ("secretfinder", "discovery", "passive", "secretfinder", "url", "-i {url} -o cli", "git clone m4ll0k/SecretFinder", "secret/API-key discovery in JS"),
    ("jsluice", "discovery", "passive", "jsluice", "url", "urls <(curl -s {url})", "go install github.com/BishopFox/jsluice@latest", "JS analysis: URLs, secrets, interesting strings"),
    ("cariddi", "discovery", "passive", "cariddi", "url", "-intensive -target {url}", "go install github.com/edoardottt/cariddi@latest", "endpoint/secret/error crawler"),
    ("waymore", "discovery", "passive", "waymore", "domain", "-i {domain} -mode U -oU /tmp/dh_waymore.txt", "pip install waymore / git clone xnl-h4ck3r/waymore", "wayback-machine URL harvester"),
    ("gauplus", "discovery", "passive", "gauplus", "domain", "-t 5 --o /tmp/dh_gauplus.txt {domain}", "go install github.com/bp0lr/gauplus@latest", "open-threat-exchange URL fetcher"),
    ("unfurl", "discovery", "passive", "unfurl", "url", "--unique url {url}", "go install github.com/tomnomnom/unfurl@latest", "URL deconstruction for analysis pipelines"),
    # ---- web vulnerability research ----
    ("zap", "vuln", "active", "zap.sh", "url", "-quickurl {url} -quickout /tmp/dh_zap.html", "download from zaproxy.org (needs JVM)", "OWASP ZAP baseline scan", "zap"),
    ("burp", "vuln", "manual", "burp", "url", "", "portswigger.net (GUI)", "Burp Suite — human-driven proxy/intruder"),
    ("caido", "vuln", "manual", "caido", "url", "", "caido.io (GUI)", "Caido — human-driven proxy alternative"),
    ("wapiti", "vuln", "active", "wapiti", "url", "-u {url} -f json -o /tmp/dh_wapiti", "pip install wapiti3 / apt install wapiti", "web vulnerability scanner"),
    ("nikto", "vuln", "active", "nikto", "url", "-h {url} -Tuning 1234567890abc", "apt install nikto", "web server scanner"),
    ("arachni", "vuln", "active", "arachni", "url", "{url} --report-save-path=/tmp/dh_arachni.afr", "download from arachni-scanner.com", "ruby web app scanner"),
    ("jaeles", "vuln", "active", "jaeles", "url", "scan -s /tmp/jaeles-sigs -u {url}", "go install github.com/jaeles-project/jaeles@latest", "signature-based scanner"),
    ("dalfox", "vuln", "active", "dalfox", "url", "url {url} --skip-mining -S", "go install github.com/hahwul/dalfox/v2@latest", "XSS scanner", "dalfox"),
    ("xsstrike", "vuln", "active", "xsstrike", "url", "-u {url}", "git clone s0md3v/XSStrike; pip install -r requirements", "XSS fuzzer with context analysis"),
    ("kxss", "vuln", "active", "kxss", "url", "curl -s {url} | kxss", "go install github.com/tomnomnom/hacks/kxss@latest", "XSS reflection detector (piped)"),
    ("domdig", "vuln", "manual", "domdig", "url", "", "chrome extension — human-driven", "DOM XSS browser helper — human-driven"),
    ("domxssscanner", "vuln", "active", "domxssscanner", "url", "{url}", "npm i -g domxssscanner (if available)", "DOM XSS scanner CLI"),
    ("xss-radar", "vuln", "active", "xss-radar", "url", "-u {url}", "git clone bwatters/xss-radar", "blind XSS callback listener/scan helper"),
    ("brutexss", "vuln", "active", "brutexss", "url", "-u {url} -w wordlist.txt", "git clone ShawarKhanEth/BruteXSS", "bulk reflected-XSS brute forcer (throttle!)"),
    ("sstimap", "vuln", "active", "sstimap", "url", "-u {url}", "git clone vladko312/SSTImap", "SSTI detection/exploitation tester"),
    ("commix", "vuln", "active", "commix", "url", "--url={url} --batch", "git clone commixproject/commix", "command injection tester"),
    ("sqlmap", "vuln", "active", "sqlmap", "url", "-u {url} --batch --level 1 --risk 1", "git clone sqlmapproject/sqlmap", "SQL injection exploitation toolkit"),
    ("ghauri", "vuln", "active", "ghauri", "url", "-u {url} --batch", "pip install ghauri / git clone r0oth3x49/ghauri", "fast SQLi exploitation tool"),
    ("jsql", "vuln", "manual", "jsql", "url", "", "github.com/ron190/jsql-injection (GUI)", "Java SQLi tool — human-driven"),
    ("nosqli", "vuln", "active", "nosqli", "url", "-u {url}", "git clone nosqli scanners (various)", "NoSQL injection scanner"),
    # ---- API / GraphQL ----
    ("inql", "api", "active", "inql", "url", "-t {url} -o /tmp/dh_inql", "pip install inql / github.com/doyensec/inql", "GraphQL security auditor"),
    ("graphql-voyager", "api", "manual", "graphql-voyager", "url", "", "browser tool — human-driven", "GraphQL schema visual explorer — human-driven"),
    ("graphw00f", "api", "active", "graphw00f", "url", "-d -t {url}", "pip install graphw00f / github.com/dolevf/graphw00f", "GraphQL engine fingerprinting"),
    ("postman", "api", "manual", "postman", "url", "", "postman.com (GUI)", "API client — human-driven"),
    ("insomnia", "api", "manual", "insomnia", "url", "", "insomnia.rest (GUI)", "API client — human-driven"),
    ("hoppscotch", "api", "manual", "hoppscotch", "url", "", "hoppscotch.io (web)", "API client — human-driven"),
    ("dredd", "api", "active", "dredd", "url", "api-description.yml {url}", "npm i -g dredd", "API blueprint/spec testing"),
    ("schemathesis", "api", "active", "schemathesis", "url", "run {url}/openapi.json", "pip install schemathesis", "property-based API testing from OpenAPI"),
    ("restler", "api", "active", "restler", "url", "fuzz --restler_grammar grammar.py", "dotnet tool / github.com/microsoft/restler-fuzzer", "stateful REST API fuzzer (needs grammar)"),
    ("apiclarity", "api", "passive", "apiclarity", "none", "--help", "github.com/openclarity/apiclarity", "API traffic visibility (k8s)"),
    ("tinja", "api", "active", "tinja", "url", "-u {url}", "pip install tinja / github.com/dolevf/tinja", "GraphQL CSRF/explorer probe"),
    ("graphql-cop", "api", "active", "graphql-cop", "url", "-t {url}", "pip install graphql-cop / github.com/dolevf/graphql-cop", "GraphQL misconfiguration auditor"),
    ("clairvoyance", "api", "active", "clairvoyance", "url", "-o /tmp/dh_clair {url}", "pip install clairvoyance / github.com/nikn0laty/clairvoyance", "GraphQL schema recon via suggestions"),
    # ---- request / protocol research ----
    ("smuggler", "protocol", "active", "smuggler", "url", "-u {url}", "git clone defparam/smuggler", "HTTP request smuggling detector"),
    ("http-request-smuggler", "protocol", "active", "smuggler", "url", "-u {url} -x", "git clone defparam/smuggler (variant flags)", "smuggling variant matrix"),
    ("http-desync-scanner", "protocol", "manual", "http-desync", "url", "", "Burp extension — human-driven", "desync scanner — human-driven"),
    ("h2csmuggler", "protocol", "active", "h2csmuggler", "url", "-x {url}", "pip install h2csmuggler / github.com/BishopFox/h2csmuggler", "HTTP/2 -> HTTP/1 smuggling tester"),
    ("http2smugl", "protocol", "active", "http2smugl", "url", "{url}", "github.com/neexemil/http2smugl", "HTTP/2 smuggling PoCs"),
    ("turbo-intruder", "protocol", "manual", "turbo", "url", "", "Burp extension — human-driven", "HTTP pipelining race tester — human-driven"),
    ("active-scan-plus-plus", "protocol", "manual", "asp", "url", "", "Burp extension — human-driven", "ActiveScan++ — human-driven"),
    ("backslash-powered-scanner", "protocol", "manual", "bps", "url", "", "Burp extension — human-driven", "unescaped-backslash scanner — human-driven"),
    ("autorize", "protocol", "manual", "autorize", "url", "", "Burp extension — human-driven", "authorization tester — human-driven"),
    ("authmatrix", "protocol", "manual", "authmatrix", "url", "", "Burp extension — human-driven", "role-based access matrix — human-driven"),
    ("retirejs", "protocol", "passive", "retire", "url", "--js {url}", "npm i -g retire", "vulnerable JS library detector"),
    ("wafw00f", "protocol", "passive", "wafw00f", "url", "{url}", "pip install wafw00f / apt install wafw00f", "WAF fingerprinting"),
    ("testssl", "protocol", "passive", "testssl.sh", "host", "--fast {host}", "git clone drwetter/testssl.sh", "TLS/SSL configuration tester"),
    # ---- fuzzing ----
    ("aflpp", "fuzz", "manual", "afl-fuzz", "none", "--help", "apt install afl++", "coverage-guided fuzzer — lab binaries, human setup"),
    ("libfuzzer", "fuzz", "manual", "clang", "none", "--help", "llvm toolchain", "in-process fuzzer — human setup"),
    ("honggfuzz", "fuzz", "manual", "honggfuzz", "none", "--help", "apt install honggfuzz / build", "fuzzer with persistent mode — human setup"),
    ("peach", "fuzz", "manual", "peach", "none", "--help", "gitlab.com/gitlab-org/security-products/protocol-fuzzer-ce", "smart protocol fuzzer — human setup"),
    ("boofuzz", "fuzz", "manual", "boofuzz", "none", "--help", "pip install boofuzz", "network protocol fuzzer — human setup"),
    ("sulley", "fuzz", "manual", "sulley", "none", "--help", "legacy (see boofuzz)", "original protocol fuzzer — superseded by boofuzz"),
    ("spike", "fuzz", "manual", "spike", "none", "--help", "legacy SPIKE fuzzer", "block-based fuzzer — historical"),
    ("wfuzz", "fuzz", "active", "wfuzz", "url", "-u {url}FUZZ -w wordlist.txt -q", "pip install wfuzz / apt install wfuzz", "web fuzzer (params, headers, paths)"),
    ("fuzzdb", "fuzz", "resource", "fuzzdb", "none", "", "git clone fuzzdb-project/fuzzdb", "attack-pattern wordlist corpus (resource, not a runner)"),
    ("fuzzilli", "fuzz", "manual", "fuzzilli", "none", "--help", "github.com/googleprojectzero/fuzzilli (build)", "JS engine fuzzer — human setup"),
]


def dedupe_report():
    seen, dupes = set(), []
    for t in TOOLS100:
        if t[0] in seen:
            dupes.append(t[0])
        seen.add(t[0])
    return len(TOOLS100), dupes
