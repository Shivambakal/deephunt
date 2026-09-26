# Robinhood Agentic Trading MCP Server — Passive Analysis

Date: 2026-09-26. Method: public docs, community-verified live `tools/list` snapshots,
Robinhood's official support article, and the live OAuth discovery documents fetched
read-only today. **No authentication performed, no trades executed, no prompt
injection of the live server.** Nothing here is a confirmed vulnerability; every
hypothesis needs authenticated testing on the researcher's own account.

## [TOOL INVENTORY]

Endpoint: `https://agent.robinhood.com/mcp/trading` — Streamable HTTP (JSON-RPC over
POST; unauthenticated `initialize` returns `401` with an RFC 9728 protected-resource
challenge; `Mcp-Session-Id` header; session termination unimplemented → `400`).

Robinhood publishes no tool schema. The inventory below is reconstructed from
community-verified live `tools/list` snapshots (23 tools, 2026-06-14) and corroborating
lists (22 tools), NOT from Robinhood documentation — the one tool Robinhood documents
publicly is `review_equity_order`. Treat names as observed, not contractual; the
server can add/rename tools at any time.

**Read tools (portfolio & market data):**
- `get_accounts` — lists accounts; each entry exposes `account_number`,
  `rhs_account_number`, `type`, `brokerage_account_type`, `nickname`, `is_default`,
  `agentic_allowed`, `option_level`, `state`, `deactivated`
- `get_portfolio` — portfolio value / balances
- `get_equity_positions` — current stock holdings
- `get_equity_quotes` — live quotes
- `get_equity_tradability` — tradability info
- `get_equity_orders` — order history
- `get_equity_historicals` — historicals
- `search` — symbol/ticker lookup
- `get_watchlists`, `get_watchlist_items`, `get_option_watchlist`,
  `get_popular_watchlists` — watchlist reads (naming varies slightly across snapshots:
  `get_options_watchlist` / `get_popular_lists` also observed)

**Trade execution (write):**
- `review_equity_order` — simulates an order, returns pre-trade warnings, no execution
- `place_equity_order` — places a real buy/sell
- `cancel_equity_order` — cancels an open order
- `review_option_order` / `place_option_order` — options support rolling out (appears in
  community guardrail lists; not in the June `tools/list` snapshot)

**Watchlist/social writes (12 of the 23):**
- `add_to_watchlist`, `add_option_to_watchlist`, `remove_from_watchlist`,
  `remove_option_from_watchlist`, `create_watchlist`, `update_watchlist`,
  `follow_watchlist` / `follow_list`, `unfollow_watchlist` / `unfollow_list`

**Input schemas:** not published. Adapters and server "guide" strings imply order tools
accept symbol, side, quantity/notional, order type, and an **account identifier** — the
server's own `guide` text instructs agents to "pass full unmasked [account_number]
value to other tools… for crypto-backed flows pass `rhs_account_number`; for
everything else pass `account_number`". This is inferred, not read from a live
`inputSchema`; the exact schema must come from an authenticated `tools/list`.
(`replace_order` appears in one community banned-tool list but in no confirmed live
snapshot — unverified, not claimed as existing.)

**Response envelope:** every tool response is wrapped as `{"data": {...}, "guide":
"..."}` — the `guide` string is a server-issued behavioral instruction the agent is
meant to read and follow (e.g. masking rules for account numbers, account ordering,
which account-number variant to pass). This is a **server→agent instruction channel**
embedded in tool output.

## [PERMISSION MODEL]

**Authentication (verified live today via `.well-known/oauth-authorization-server`):**
- OAuth 2.1 authorization code + PKCE (S256), **public client** — no client secret
  (`token_endpoint_auth_methods_supported: ["none"]`); PKCE is the only code-interception
  defense
- **Open Dynamic Client Registration** at
  `https://agent.robinhood.com/oauth/trading/register` — anyone can register a client;
  `client_name` is self-asserted by the registrant
- **Single scope: `"internal"`** — one coarse scope covers everything; no
  read-vs-trade separation at the OAuth layer, no progressive/least-privilege scopes
- Authorization endpoint is first-party (`https://robinhood.com/oauth`); user clicks
  "Authorize" in the browser. Desktop-only for setup
- **Token endpoint is shared with the legacy API**: `https://api.robinhood.com/oauth2/token/`
- Lifetimes (community-observed, undocumented): access tokens ~hours (silent refresh on
  401); refresh tokens long-lived (weeks–months); re-prompt only on revoke, expiry, or
  password reset

**Authorization boundaries (as documented/observed):**
- **Read = broad:** the agent gets read access to ALL the user's Robinhood accounts —
  account numbers, positions, balances, transactions, order history, watchlists.
  Official support article states this explicitly
- **Write = narrow:** trades confined to the dedicated Agentic account. Community
  end-to-end verification (2026-06-14) reports the wall is **enforced at Robinhood's
  edge via the `agentic_allowed` flag**, not by client-side checks; the official
  article states "Your agent can only place trades in your Robinhood Agentic account"
- **review→place is a recommendation, not an evidenced enforcement:** docs say the
  recommended sequence is `review_equity_order` → human review → `place_equity_order`,
  but nothing observed indicates the server rejects a direct `place_equity_order`;
  community guardrails ban `place_*` client-side precisely because the server would
  otherwise execute them
- **No per-trade user consent at the MCP layer:** Robinhood's own article warns "if
  you've asked your agent to take action without asking your approval, it can place
  trades without your confirmation"
- **Detective controls:** notification on every trade; disconnect/revoke anytime from
  within the Robinhood app
- **Disclaimed responsibility:** "Robinhood does not control, supervise, monitor,
  recommend, or audit these AI agents" — full responsibility sits with the user

## [CONFUSED-DEPUTY HYPOTHESES — ranked]

**H1. Token authority exceeds the advertised tool surface (token reuse across APIs).**
The MCP OAuth token is minted at the *legacy* token endpoint
(`api.robinhood.com/oauth2/token/`) with the single coarse scope `"internal"`.
Question: is the same bearer token accepted by `api.robinhood.com` legacy REST
endpoints? The legacy API has its own auth model and historically permitted trading
in the *main* account. If the MCP token is honored there, the token's effective
authority exceeds the MCP tool surface and possibly the agentic-account wall.
*Test (own account, read-only, no trades): present the MCP bearer token to a
read-only legacy endpoint; observe accept vs reject. Do not place orders.*

**H2. `place_equity_order` account-target confusion.**
Order tools accept an account identifier per the server's own `guide` instructions.
Question: what happens when `place_equity_order` is called with the MAIN account's
`account_number` (`agentic_allowed: false`)? Community reports claim the edge rejects
it — verify, don't trust. A missing or inconsistent server-side check breaks the
entire two-account safety model.
*Test (own accounts, requires explicit approval — real money): minimal-notional call
with the non-agentic account number; expect rejection; record exact error.*

**H3. review→place non-enforcement.**
If the server executes `place_equity_order` without a preceding `review_equity_order`,
the "pre-trade review" is UX, not a security boundary — a compromised or malicious
MCP client (or a prompt-injected agent) can trade directly.
*Test: same constraints as H2 — real-money approval required.*

**H4. Indirect prompt injection via tool results.**
`search`, `get_popular_watchlists`, and `follow_watchlist` return strings influenced
by third parties (company names, public/shared watchlist names). The server already
trains agents to obey `guide` instructions embedded in tool output. An adversary who
can get a crafted watchlist into `get_popular_watchlists` (or whom the user follows)
can inject instructions the agent treats as server guidance — e.g. conflicting
account-number handling rules.
*Test (passive/own-account): create watchlists with adversarial names on own account;
observe how the host agent handles them. No third-party targeting.*

**H5. Consent-screen client-name spoofing via open DCR.**
Anyone can register at `/oauth/trading/register` with an arbitrary `client_name`
(e.g. "Robinhood Trading Official"). Consent happens on the first-party
`robinhood.com/oauth` page, so the spoof surface is limited to whatever client name
the consent screen displays — check what it shows and whether a deceptive name could
confuse users into authorizing a malicious client that then receives full
read-everything + agentic-trading tokens.

**H6. `guide`-string trust channel vs attacker-mimicked guidance.**
The server instructs agents to mask account numbers in UI but pass full unmasked
values to other tools. If attacker-influenced tool output (H4) can mimic a `guide`
directive ("send full account numbers to…"), the agent may exfiltrate sensitive
identifiers. This is a defense-in-depth question about instruction hierarchy in the
host agent.

**H7. `rhs_account_number` vs `account_number` confusion.**
The server's guide distinguishes crypto-backed flows (`rhs_account_number`) from
everything else (`account_number`). Question: does the server validate the pairing,
or can a caller swap them to confuse which ledger/account an operation targets?
Crypto trading via the agent is now live per the support article (transfer/stake/lend
excluded).

**H8. Long-lived refresh tokens + unattended trading.**
Refresh tokens last weeks–months; the agent may trade without per-trade user
confirmation if configured to act autonomously. A compromised host (Claude Code
session, MCP config) equals persistent trading access until the user disconnects in
the app. Notifications are detective-only. This is largely documented design, but the
session/token binding is worth verifying: is the OAuth token bound to the MCP
session (`Mcp-Session-Id`), or replayable across sessions and clients?

**H9. Scope-stasis on tool expansion.**
The single `"internal"` scope means every future tool the server adds (crypto
already shipped through this endpoint; futures/options expansion announced) is
automatically authorized for already-connected clients — no re-consent. Combined
with clients that resolve capabilities by name-regex (observed in the wild), a new
dangerous tool could be picked up silently.

**H10. Tool-squatting / server-impersonation on the client side.**
The endpoint URL is public and documented; nothing stops a malicious MCP server at a
lookalike URL or a tampered local config from harvesting the OAuth flow. Client
config hygiene issue, not a Robinhood server bug — included for completeness.

## Sources
- Robinhood official: https://robinhood.com/us/en/support/articles/agentic-trading-overview/
  (read access scope, agentic-account-only trading, no-confirmation warning, disclosures)
- Live OAuth metadata fetched 2026-09-26 (read-only):
  https://agent.robinhood.com/.well-known/oauth-authorization-server and
  https://agent.robinhood.com/.well-known/oauth-protected-resource/mcp/trading
  (issuer, PKCE S256, public client, open DCR, single "internal" scope, shared token endpoint)
- mdfaizali390/stocksaigents ROBINHOOD_MCP_INTEGRATION.md (23-tool live snapshot
  2026-06-14, `{"data","guide"}` envelope, `agentic_allowed` edge enforcement claim,
  OAuth flow details): https://github.com/mdfaizali390/stocksaigents/blob/HEAD/ROBINHOOD_MCP_INTEGRATION.md
- nirholas/robinhood-toolkit prompts 01/02/03/06 (endpoint, transport, OAuth metadata
  verified 2026-07-20, runtime tool enumeration method, crypto rollout status):
  https://github.com/nirholas/robinhood-toolkit/blob/HEAD/prompts/30-agentic-mcp/01-connect-mcp-to-claude-code.md
- dzyla/ai-buddy robinhood_mcp SKILL.md (per-account `agentic_allowed` semantics):
  https://github.com/dzyla/ai-buddy/blob/HEAD/.agents/skills/robinhood_mcp/SKILL.md
- rithwikbabu/Robinhood-ATS (22-tool filtered list):
  https://github.com/rithwikbabu/Robinhood-ATS
- ooovenenoso/agent-loopkit mcp-setup.md + RECIPE.md (tool whitelist incl.
  `review_option_order`/`replace_order` guardrail names):
  https://github.com/ooovenenoso/agent-loopkit/blob/HEAD/recipes/robinhood-safe-growth/references/mcp-setup.md
- mphinance/awesome-broker-mcp brokers/robinhood.md (product overview, guardrails):
  https://github.com/mphinance/awesome-broker-mcp/blob/HEAD/brokers/robinhood.md
- doublehq/oracle blog/direct-indexing-robinhood-agentic.md (two-step order flow,
  account isolation model): https://github.com/doublehq/oracle/blob/HEAD/blog/direct-indexing-robinhood-agentic.md
- MCP spec security best practices (confused deputy, token passthrough, scope
  minimization): https://modelcontextprotocol.io/specification/2025-06-18/basic/security_best_practices

## Caveats
- Tool names/schemas come from community live snapshots (June–July 2026), not from
  Robinhood; the server may have changed since. The authoritative inventory requires
  an authenticated `tools/list` on the researcher's own account.
- The `agentic_allowed` edge-enforcement claim is community-reported, not independently
  verified here — H2 exists precisely to verify it.
- Authenticated testing is blocked on brokerage KYC (US residency + SSN) per the
  Robinhood recon report; H1–H3, H8 need the researcher's own funded setup and, for
  any order placement, explicit real-money approval.
- Input schemas, per-tool consent behavior, and token/session binding are all
  unverified from outside and marked as such above.
