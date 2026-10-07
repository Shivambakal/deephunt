# DEEPHUNT Swarm — Knowledge Regression Report (agent #99)
Date: 2026-09-27. Scope: WORLD_MODEL.md vs all swarm JSONL files
(obs_recon, obs_app, obs_diff, obs_verify, hyp_known, hyp_novel).
Rule applied: direct evidence (live captures, verbatim quotes, live policy reads)
beats docs-grade inference; later-dated observations beat earlier ones when they
conflict, unless the earlier one had controls.

## Contradiction 1: Apache Airflow lineage of MFT
- Side A (world model seed + agent-14 correction in WORLD_MODEL.md): MFT Airflow
  lineage is UNVERIFIED in vendor materials; vendor MFT materials describe a
  proprietary "next-generation flow engine"; do not base hypotheses on Airflow.
- Side B (agent 23, obs_app, import-export): kiteworks.com/managed-file-transfer-solution/
  states verbatim: "Workflows are built and scheduled through the Apache
  Airflow-powered designer" (confidence high).
- Favored: **Side B**. Agent 23 cites the exact page and a verbatim quote; agent 14's
  negative finding appears to have checked different materials. Agent 62's
  path-traversal hypothesis also treats Airflow lineage as world-model fact.
  Recommendation: retract agent 14's blanket "do not base hypotheses on it" and
  replace with "Airflow-powered workflow designer confirmed in current vendor
  MFT materials; CVE mapping still needs verification."

## Contradiction 2: robots.txt / security.txt existence
- Side A (passive dossier + agent 8, obs_recon): /.well-known/security.txt and
  /robots.txt confirmed present.
- Side B (agent 9, obs_recon): GET /robots.txt timed out; dossier claim is possibly
  a false positive; treat 'robots.txt exists' as UNCONFIRMED.
- Side C (agent 71, obs_diff): HEAD /robots.txt -> 200, 69 bytes, ETag,
  Last-Modified Sep 04 2026. HEAD /login_config -> 200 as well.
- Favored: **Side C**. robots.txt EXISTS (live HEAD, 69 bytes). Agents 9/10/13/7
  timeouts were egress-outage windows (they had example.com control failures in
  the same runs), not absence. security.txt is still only dossier-grade — agent 69's
  hyp_novel evidence claim "hunting env confirms ... security.txt ... exist" overstates;
  only robots.txt has a live re-confirmation.

## Contradiction 3: target reachability — dead vs alive
- Side A (agents 35, 36, 40, 42; obs_diff): all requests time out (HTTP 000); sandbox
  egress cannot reach the host.
- Side B (agents 39, 71, 50, 78): browser.open fetched 5 error-path probes with real
  statuses (agent 39); curl got full HTTP headers on / and HEADs on multiple paths
  (agent 71); GET /login_config -> HTTP 200, 1190 bytes full body (agent 50);
  GET /register -> HTTP 200 (agent 78).
- Favored: **both, temporally**. These are not mutually exclusive facts — they are
  time/vantage-window artifacts. The egress proxy was demonstrably down ~05:31–05:50 UTC
  (multiple agents' example.com controls failed), recovered later. Recommendation:
  timestamp every reachability claim; treat any single "unreachable" observation as
  local and non-transferable; agents 13/10/35/36/40/42 coverage gaps should be
  re-attempted rather than closed.

## Contradiction 4: GET / body received vs body never starts
- Side A (agents 6, 7, 10, 13; obs_recon): GET / -> HTTP 200, 2346 bytes SPA shell
  captured multiple times.
- Side B (agent 71, obs_diff): GET / -> HTTP 200 headers (TTFB ~10.2s),
  Transfer-Encoding: chunked, but zero body bytes within 25s.
- Favored: **both, temporally**. Origin exhibits slow/trickling responses plus dead
  windows; behavior is non-stationary. Agent 39's "GET / had no extractable content
  via fetch" is consistent with Side B at its observation time.

## Contradiction 5: agent 9's "tarpit" (path-based whitelist) theory
- Side A (agent 9, obs_recon): 8/8 non-root paths time out at connection level while
  / works; pattern is path-based (WAF whitelist or deliberate tarpit), not rate-based.
- Side B (agent 71, obs_diff): HEADs on /login_config, /robots.txt, /nonexistent probe
  all return real responses (200s, 302, 69-byte robots.txt) from the same paths agent 9
  called dead; agent 50 fetched /login_config's full 1190-byte body; agent 78 got
  /register -> 200.
- Favored: **Side B**. Agent 9's conclusion was reached WITHOUT a control test (unlike
  agents 6/7/10/13 who all showed example.com failing identically). The "path-based"
  pattern was actually egress-degradation windows plus a slow origin. Recommendation:
  downgrade agent 9's tarpit theory; the live origin is slow (5–16s TTFB per agent 71)
  and intermittent, not selectively blocking paths.

## Contradiction 6: client framework — React vs Vue
- Side A (agents 7, 9, 10, 13; obs_recon): "React SPA", "React/webpack SPA",
  "React app" — based on hashed webpack chunks, <div id="app">, and a named
  signin.*.js entry. No React-specific marker cited.
- Side B (agent 50, world model correction): /login_config defines and applies
  `vue_config` — the config object's own name is vue_config.
- Favored: **Side B (weak)**. `vue_config` is concrete in-app evidence; the React
  claims are framework-guessing from webpack hashes (<div id="app"> is also Vue's
  mount convention). Either way the client is a webpack SPA; framework label should
  be marked UNVERIFIED until a chunk is actually fetched, and agent 50's DOM-XSS
  hypotheses correctly note sink confirmation is pending on unfetched chunks.

## Contradiction 7: folder role ladder — four-tier vs six roles
- Side A (agent 19, obs_app): "Kiteworks secure folders use a four-tier role model:
  Owner > Manager > Collaborator > Viewer" (Downloader/Uploader absent).
- Side B (agents 18, 25, 32, 33, 34; obs_app/obs_diff): six roles — Owner, Manager,
  Collaborator (licensed) vs Downloader, Uploader, Viewer (non-licensed) — sourced
  from the licensing doc, PCI guide, and mobile-app guide Appendix A.
- Favored: **Side B**, overwhelmingly. Agent 19's four-tier description likely
  summarizes one doc source and drops Downloader/Uploader. Recommendation: correct
  agent 19's entry; downstream role-vs-role differentials (agents 32/33/34) already
  use the correct six-role model.

## Contradiction 8: SSO/LDAP relevance on the hunting environment
- Side A (agents 13, 14, 28, 58, 64, 65; obs): SAML SSO (SimpleSAMLphp-style ACS),
  LDAP/AD integration as live attack surface; hypotheses assume a reachable ACS and
  enabled SSO (open-redirect RelayState, SAML signature confusion, PHP
  deserialization via SimpleSAMLphp sessions, SSO JIT merge).
- Side B (agent 50, world model correction): live /login_config on THIS env shows
  sso: [], oauth: '[]', passkey: '', preferredLogin: 'username_password' — no SSO/
  OAuth/LDAP provisioned; answers open question 5 (no LDAP flags exposed).
- Favored: **Side B for this environment**. The SSO/LDAP claims are product-level
  (vendor docs, Entra tutorials), not env-verified. Hypotheses predicated on a live
  hunting-env ACS (65 open-redirect, 64 H64-1 SimpleSAMLphp deserialization, 58 H2/H3
  SAML bypass, 47 LDAP filter injection via login username) have their falsifier
  trigger met: the env appears local-auth-only. They should be deprioritized for
  this env or moved to a "needs SSO-enabled instance" lane. Agent 50 already noted
  this; agent 78's default-config hypotheses correctly build on it.

## Contradiction 9: /login_config retrievability
- Side A (agents 13, 10, 7, 9; obs_recon): /login_config "unreachable via plain GET",
  "timed out", "highest-value unverified lead", coverage gaps.
- Side B (agent 50, world model correction): GET /login_config -> HTTP 200,
  1190 bytes, full vue_config + desanitize() captured.
- Favored: **Side B**; Side A is superseded (same outage windows as #3). The open
  questions 2 (auth flows) and 5 (LDAP/SSO points) are now partially answered.

## Contradiction 10: self-registration on the hunting environment
- Side A (agent 16, obs_app; SEC-deployment docs): "No open self-registration without
  an invite trigger" — account creation is invite-triggered.
- Side B (agent 78, hyp_novel): live /login_config carries non-empty
  label.registration ('Create account') while sibling labels are empty; GET /register
  -> HTTP 200 (real SPA route, vs 302 for garbage paths). Hypothesis: template
  default leaves self-registration enabled.
- Favored: **unresolved tension, leaning Side B**. Side A's docs describe a specific
  customer (SEC) deployment, not this template env; Side B has env-specific route
  evidence but no confirmed working form (browser-rendered check still open).
  Recommendation: keep as hypothesis with agent 78's falsifier (browser visit to
  /register).

## Contradiction 11: "hunting env runs 9.5.1"
- Side A (agent 19, obs_app): "The hunting env runs 9.5.1+ (per Kiteworks, all known
  vulns fixed)."
- Side B (world model; agent 44, obs_diff): Kiteworks claims 9.5.1 is the current
  release accounting for known vulns — a vendor statement, not an env measurement;
  agent 44 notes the env runs a build with numeric user IDs (UUID migration pending);
  no version string was ever observed on the env (no Server header, no version in
  /login_config which only shows apiVersion 28).
- Favored: **Side B**. Agent 19 conflates Kiteworks' release statement with the env's
  build. Treat "env runs 9.5.1" as UNVERIFIED assumption, not fact.

## Contradiction 12: agent 26's "empirically confirmed against the live API"
- Side A (agent 26, obs_app): "Empirically confirmed against the live API
  (kiteworks/claude-agent-marketplace): there is NO server-side 'owner' or 'creator'
  filter on search" — reads as a live-environment finding.
- Side B (evidence cited): the claim rests on MCP skill-doc markdown (OFFBOARDING/
  redactor SKILL.md files), i.e., documentation of intended tool behavior, not a
  request/response against ywh-kw-public.bounty.kiteworks.dev.
- Favored: **downgrade to docs-grade**. The substance (no server-side owner filter)
  is plausible but it is NOT a live confirmation on the hunting env. Agent 53's H2
  IDOR hypothesis correctly cites it as docs evidence, which is the right grade.

## Secondary tensions (flagged, not hard contradictions)
- Agent 5 (obs_recon) "No CT records surfaced for hunting host" vs agents 2/3:
  compatible — no dedicated cert for the host (Side of agent 3: wildcard covers it);
  agent 5's search only covered the bare hostname.
- Agent 39 vs agent 71 on error paths: compatible — 302 to /error?status=404 then the
  branded page (agent 39's fetcher followed the redirect); /rest/* raw 404 and
  encoded-traversal 400 remain agent 39's alone.
- Agent 44 vs agent 53: agent 44 observes numeric user IDs on this build; agent 53
  only lists UUID file_ids as a conditional falsifier branch — no conflict.

## World-model corrections recommended
1. Retract agent 14's Airflow "do not base hypotheses on it" (contradiction 1).
2. robots.txt EXISTS (live HEAD 69 bytes); security.txt still unverified (2).
3. Reachability is time-varying; mandate timestamps on reachability claims (3, 4).
4. Downgrade agent 9 tarpit theory (5); origin is slow/flaky, not path-filtering.
5. Client framework UNVERIFIED (React claim weak; vue_config suggests Vue) (6).
6. Folder roles: six, not four (7).
7. Hunting env auth: password-only per live /login_config; SSO/LDAP hypotheses
   deprioritized for this env (8, 9).
8. "Env runs 9.5.1" is unverified vendor-statement extrapolation (11).

## 3-line summary
Found 12 contradictions: the strongest are the Airflow lineage (agent 23's verbatim
vendor quote beats agent 14's "unverified" correction), robots.txt's live existence
(agent 71 HEAD beats the timeout-based doubts), and the hunting env being password-only
(agent 50's /login_config weakens the SAML/LDAP hypotheses).
Most "unreachable" conflicts are time-window artifacts of sandbox egress outages, not
target facts — timestamp reachability claims and re-attempt rather than close them.
Recommend 8 world-model corrections, the top three: fix Airflow, fix role-ladder count
(six not four), and mark React framework + 9.5.1 env version as unverified.
