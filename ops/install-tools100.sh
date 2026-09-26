#!/bin/bash
# DEEPHUNT tools-100 installer — generated from deephunt/tools100.py
# Installs every missing binary. Review before running; some need sudo.
set -e

command -v amass >/dev/null 2>&1 && echo "OK   amass" || { echo "MISS amass -> go install github.com/owasp-amass/amass/v4/...@latest"; }
command -v assetfinder >/dev/null 2>&1 && echo "OK   assetfinder" || { echo "MISS assetfinder -> go install github.com/tomnomnom/assetfinder@latest"; }
command -v findomain >/dev/null 2>&1 && echo "OK   findomain" || { echo "MISS findomain -> curl -sL https://github.com/findomain/findomain/releases/latest/download/findomain-linux.zip"; }
command -v sublist3r >/dev/null 2>&1 && echo "OK   sublist3r" || { echo "MISS sublist3r -> pip install sublist3r / apt install sublist3r"; }
command -v sudomy >/dev/null 2>&1 && echo "OK   sudomy" || { echo "MISS sudomy -> go install github.com/c3l3si4n/sudomy@latest"; }
command -v shuffledns >/dev/null 2>&1 && echo "OK   shuffledns" || { echo "MISS shuffledns -> go install github.com/projectdiscovery/shuffledns/cmd/shuffledns@latest"; }
command -v puredns >/dev/null 2>&1 && echo "OK   puredns" || { echo "MISS puredns -> go install github.com/d3mondev/puredns/v2@latest"; }
command -v dnsgen >/dev/null 2>&1 && echo "OK   dnsgen" || { echo "MISS dnsgen -> pip install dnsgen"; }
command -v massdns >/dev/null 2>&1 && echo "OK   massdns" || { echo "MISS massdns -> apt install massdns / build from source"; }
command -v dnsx >/dev/null 2>&1 && echo "OK   dnsx" || { echo "MISS dnsx -> go install github.com/projectdiscovery/dnsx/cmd/dnsx@latest"; }
command -v asnmap >/dev/null 2>&1 && echo "OK   asnmap" || { echo "MISS asnmap -> go install github.com/projectdiscovery/asnmap/cmd/asnmap@latest"; }
command -v mapcidr >/dev/null 2>&1 && echo "OK   mapcidr" || { echo "MISS mapcidr -> go install github.com/projectdiscovery/mapcidr/cmd/mapcidr@latest"; }
command -v naabu >/dev/null 2>&1 && echo "OK   naabu" || { echo "MISS naabu -> go install github.com/projectdiscovery/naabu/v2/cmd/naabu@latest"; }
command -v masscan >/dev/null 2>&1 && echo "OK   masscan" || { echo "MISS masscan -> apt install masscan"; }
command -v unicornscan >/dev/null 2>&1 && echo "OK   unicornscan" || { echo "MISS unicornscan -> apt install unicornscan"; }
command -v fierce >/dev/null 2>&1 && echo "OK   fierce" || { echo "MISS fierce -> pip install fierce / apt install fierce"; }
command -v dnsrecon >/dev/null 2>&1 && echo "OK   dnsrecon" || { echo "MISS dnsrecon -> pip install dnsrecon / apt install dnsrecon"; }
command -v dnsenum >/dev/null 2>&1 && echo "OK   dnsenum" || { echo "MISS dnsenum -> apt install dnsenum"; }
command -v dnsmap >/dev/null 2>&1 && echo "OK   dnsmap" || { echo "MISS dnsmap -> apt install dnsmap"; }
command -v spiderfoot >/dev/null 2>&1 && echo "OK   spiderfoot" || { echo "MISS spiderfoot -> pip install spiderfoot / docker"; }
command -v gobuster >/dev/null 2>&1 && echo "OK   gobuster" || { echo "MISS gobuster -> go install github.com/OJ/gobuster/v3@latest / apt install gobuster"; }
command -v feroxbuster >/dev/null 2>&1 && echo "OK   feroxbuster" || { echo "MISS feroxbuster -> curl install from github.com/epi052/feroxbuster"; }
command -v dirsearch >/dev/null 2>&1 && echo "OK   dirsearch" || { echo "MISS dirsearch -> pip install dirsearch / git clone maurosoria/dirsearch"; }
# [dirbuster] manual — apt install dirbuster (GUI)
command -v hakrawler >/dev/null 2>&1 && echo "OK   hakrawler" || { echo "MISS hakrawler -> go install github.com/hakluke/hakrawler@latest"; }
command -v gospider >/dev/null 2>&1 && echo "OK   gospider" || { echo "MISS gospider -> go install github.com/jaeles-project/gospider@latest"; }
command -v kiterunner >/dev/null 2>&1 && echo "OK   kiterunner" || { echo "MISS kiterunner -> docker pull assetnote/kiterunner"; }
command -v arjun >/dev/null 2>&1 && echo "OK   arjun" || { echo "MISS arjun -> pip install arjun"; }
command -v paramspider >/dev/null 2>&1 && echo "OK   paramspider" || { echo "MISS paramspider -> pip install paramspider / git clone devanshbatham/paramspider"; }
# [paramminer] manual — Burp extension — human-driven
command -v x8 >/dev/null 2>&1 && echo "OK   x8" || { echo "MISS x8 -> cargo install x8 / github.com/Sh1Yo/x8"; }
command -v parameth >/dev/null 2>&1 && echo "OK   parameth" || { echo "MISS parameth -> go install github.com/maikthulhu/parameth@latest"; }
command -v linkfinder >/dev/null 2>&1 && echo "OK   linkfinder" || { echo "MISS linkfinder -> pip install linkfinder / git clone gerbenjavado/linkfinder"; }
command -v secretfinder >/dev/null 2>&1 && echo "OK   secretfinder" || { echo "MISS secretfinder -> git clone m4ll0k/SecretFinder"; }
command -v jsluice >/dev/null 2>&1 && echo "OK   jsluice" || { echo "MISS jsluice -> go install github.com/BishopFox/jsluice@latest"; }
command -v cariddi >/dev/null 2>&1 && echo "OK   cariddi" || { echo "MISS cariddi -> go install github.com/edoardottt/cariddi@latest"; }
command -v waymore >/dev/null 2>&1 && echo "OK   waymore" || { echo "MISS waymore -> pip install waymore / git clone xnl-h4ck3r/waymore"; }
command -v gauplus >/dev/null 2>&1 && echo "OK   gauplus" || { echo "MISS gauplus -> go install github.com/bp0lr/gauplus@latest"; }
command -v unfurl >/dev/null 2>&1 && echo "OK   unfurl" || { echo "MISS unfurl -> go install github.com/tomnomnom/unfurl@latest"; }
command -v zap.sh >/dev/null 2>&1 && echo "OK   zap" || { echo "MISS zap -> download from zaproxy.org (needs JVM)"; }
# [burp] manual — portswigger.net (GUI)
# [caido] manual — caido.io (GUI)
command -v wapiti >/dev/null 2>&1 && echo "OK   wapiti" || { echo "MISS wapiti -> pip install wapiti3 / apt install wapiti"; }
command -v nikto >/dev/null 2>&1 && echo "OK   nikto" || { echo "MISS nikto -> apt install nikto"; }
command -v arachni >/dev/null 2>&1 && echo "OK   arachni" || { echo "MISS arachni -> download from arachni-scanner.com"; }
command -v jaeles >/dev/null 2>&1 && echo "OK   jaeles" || { echo "MISS jaeles -> go install github.com/jaeles-project/jaeles@latest"; }
command -v dalfox >/dev/null 2>&1 && echo "OK   dalfox" || { echo "MISS dalfox -> go install github.com/hahwul/dalfox/v2@latest"; }
command -v xsstrike >/dev/null 2>&1 && echo "OK   xsstrike" || { echo "MISS xsstrike -> git clone s0md3v/XSStrike; pip install -r requirements"; }
command -v kxss >/dev/null 2>&1 && echo "OK   kxss" || { echo "MISS kxss -> go install github.com/tomnomnom/hacks/kxss@latest"; }
# [domdig] manual — chrome extension — human-driven
command -v domxssscanner >/dev/null 2>&1 && echo "OK   domxssscanner" || { echo "MISS domxssscanner -> npm i -g domxssscanner (if available)"; }
command -v xss-radar >/dev/null 2>&1 && echo "OK   xss-radar" || { echo "MISS xss-radar -> git clone bwatters/xss-radar"; }
command -v brutexss >/dev/null 2>&1 && echo "OK   brutexss" || { echo "MISS brutexss -> git clone ShawarKhanEth/BruteXSS"; }
command -v sstimap >/dev/null 2>&1 && echo "OK   sstimap" || { echo "MISS sstimap -> git clone vladko312/SSTImap"; }
command -v commix >/dev/null 2>&1 && echo "OK   commix" || { echo "MISS commix -> git clone commixproject/commix"; }
command -v sqlmap >/dev/null 2>&1 && echo "OK   sqlmap" || { echo "MISS sqlmap -> git clone sqlmapproject/sqlmap"; }
command -v ghauri >/dev/null 2>&1 && echo "OK   ghauri" || { echo "MISS ghauri -> pip install ghauri / git clone r0oth3x49/ghauri"; }
# [jsql] manual — github.com/ron190/jsql-injection (GUI)
command -v nosqli >/dev/null 2>&1 && echo "OK   nosqli" || { echo "MISS nosqli -> git clone nosqli scanners (various)"; }
command -v inql >/dev/null 2>&1 && echo "OK   inql" || { echo "MISS inql -> pip install inql / github.com/doyensec/inql"; }
# [graphql-voyager] manual — browser tool — human-driven
command -v graphw00f >/dev/null 2>&1 && echo "OK   graphw00f" || { echo "MISS graphw00f -> pip install graphw00f / github.com/dolevf/graphw00f"; }
# [postman] manual — postman.com (GUI)
# [insomnia] manual — insomnia.rest (GUI)
# [hoppscotch] manual — hoppscotch.io (web)
command -v dredd >/dev/null 2>&1 && echo "OK   dredd" || { echo "MISS dredd -> npm i -g dredd"; }
command -v schemathesis >/dev/null 2>&1 && echo "OK   schemathesis" || { echo "MISS schemathesis -> pip install schemathesis"; }
command -v restler >/dev/null 2>&1 && echo "OK   restler" || { echo "MISS restler -> dotnet tool / github.com/microsoft/restler-fuzzer"; }
command -v apiclarity >/dev/null 2>&1 && echo "OK   apiclarity" || { echo "MISS apiclarity -> github.com/openclarity/apiclarity"; }
command -v tinja >/dev/null 2>&1 && echo "OK   tinja" || { echo "MISS tinja -> pip install tinja / github.com/dolevf/tinja"; }
command -v graphql-cop >/dev/null 2>&1 && echo "OK   graphql-cop" || { echo "MISS graphql-cop -> pip install graphql-cop / github.com/dolevf/graphql-cop"; }
command -v clairvoyance >/dev/null 2>&1 && echo "OK   clairvoyance" || { echo "MISS clairvoyance -> pip install clairvoyance / github.com/nikn0laty/clairvoyance"; }
command -v smuggler >/dev/null 2>&1 && echo "OK   smuggler" || { echo "MISS smuggler -> git clone defparam/smuggler"; }
command -v smuggler >/dev/null 2>&1 && echo "OK   http-request-smuggler" || { echo "MISS http-request-smuggler -> git clone defparam/smuggler (variant flags)"; }
# [http-desync-scanner] manual — Burp extension — human-driven
command -v h2csmuggler >/dev/null 2>&1 && echo "OK   h2csmuggler" || { echo "MISS h2csmuggler -> pip install h2csmuggler / github.com/BishopFox/h2csmuggler"; }
command -v http2smugl >/dev/null 2>&1 && echo "OK   http2smugl" || { echo "MISS http2smugl -> github.com/neexemil/http2smugl"; }
# [turbo-intruder] manual — Burp extension — human-driven
# [active-scan-plus-plus] manual — Burp extension — human-driven
# [backslash-powered-scanner] manual — Burp extension — human-driven
# [autorize] manual — Burp extension — human-driven
# [authmatrix] manual — Burp extension — human-driven
command -v retire >/dev/null 2>&1 && echo "OK   retirejs" || { echo "MISS retirejs -> npm i -g retire"; }
command -v wafw00f >/dev/null 2>&1 && echo "OK   wafw00f" || { echo "MISS wafw00f -> pip install wafw00f / apt install wafw00f"; }
command -v testssl.sh >/dev/null 2>&1 && echo "OK   testssl" || { echo "MISS testssl -> git clone drwetter/testssl.sh"; }
# [aflpp] manual — apt install afl++
# [libfuzzer] manual — llvm toolchain
# [honggfuzz] manual — apt install honggfuzz / build
# [peach] manual — gitlab.com/gitlab-org/security-products/protocol-fuzzer-ce
# [boofuzz] manual — pip install boofuzz
# [sulley] manual — legacy (see boofuzz)
# [spike] manual — legacy SPIKE fuzzer
command -v wfuzz >/dev/null 2>&1 && echo "OK   wfuzz" || { echo "MISS wfuzz -> pip install wfuzz / apt install wfuzz"; }
# [fuzzdb] resource — git clone fuzzdb-project/fuzzdb
# [fuzzilli] manual — github.com/googleprojectzero/fuzzilli (build)
