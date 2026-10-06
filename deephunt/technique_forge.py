"""DEEPHUNT Technique Forge — permutation/combination engine.

Systematically combines existing technique cards into novel hypothesis templates.
Each combo rule fuses two (or three) parent techniques whose *interaction* creates
a new, testable property that neither parent card describes on its own.

Usage:
    python3 technique_forge.py --max 60 --seed 42
    python3 technique_forge.py --out hunt_waves/wave1/cards_forge.yaml --max 50
"""

from __future__ import annotations

import argparse
import itertools
import math
import os
import random
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
TECH_DIR = os.path.join(HERE, "knowledge", "techniques")
DEFAULT_OUT = os.path.join(HERE, "hunt_waves", "wave1", "cards_forge.yaml")


# --------------------------------------------------------------------------- #
# Corpus loading
# --------------------------------------------------------------------------- #
def load_corpus() -> list[dict]:
    """Load every technique card from knowledge/techniques/*.yaml."""
    cards: list[dict] = []
    for fname in sorted(os.listdir(TECH_DIR)):
        if not fname.endswith((".yaml", ".yml")):
            continue
        path = os.path.join(TECH_DIR, fname)
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or []
        if isinstance(data, dict):
            data = [data]
        for card in data:
            card = dict(card)
            card.setdefault("_file", fname)
            cards.append(card)
    return cards


def _short(name: str, n: int = 46) -> str:
    name = (name or "").strip()
    return name if len(name) <= n else name[: n - 1].rstrip() + "\u2026"


def _diff15(card: dict) -> int:
    """Map a card's 0.0-1.0 difficulty_estimate onto the 1-5 scale."""
    try:
        d = float(card.get("difficulty_estimate", 0.5))
    except (TypeError, ValueError):
        d = 0.5
    return max(1, min(5, math.ceil(d * 5)))


def _union(*lists) -> list:
    out: list = []
    for lst in lists:
        for item in lst or []:
            if item not in out:
                out.append(item)
    return out


# --------------------------------------------------------------------------- #
# Combination rules
#
# Each rule fuses parent cards matched by (klass, id_substring).  The oracle
# template must describe a NEW testable property produced by the interaction —
# never "check parent A and parent B separately".  `oracle_markers` are phrases
# that must survive formatting; if any is missing the combo is dropped.
# --------------------------------------------------------------------------- #
COMBO_RULES: list[dict] = [
    {
        "rule_id": "R-IDOR-RACE",
        "parents": [("authorization", "IDOR"), ("race", None)],
        "name": "Raced IDOR: {a_short} against {b_short} revocation window",
        "why_non_obvious": (
            "IDOR tests assume the authorization check is evaluated atomically against "
            "current state, but revocation (delete/share-revoke/ownership transfer) and the "
            "read are often separate operations. Racing them exposes a window where the "
            "authz decision was made against state that no longer exists."
        ),
        "oracle": (
            "COMBO-IDOR-RACE-HELD: fire the IDOR probe for victim object O in parallel with "
            "O's legitimate revocation (delete, share-revoke, or ownership transfer by the "
            "owner). The oracle holds when at least one raced request returns O's data with "
            "a 200 AFTER the revocation completed, proving the authz check and the state "
            "mutation are not atomic — a TOCTOU on the authorization decision itself."
        ),
        "oracle_markers": ["AFTER the revocation completed", "not atomic"],
        "expected_signal": "post_revocation_200_with_victim_data; revocation_authz_toctou",
        "hypothesis": (
            "If {a_name} exists on objects that support owner-driven revocation AND {b_name} "
            "is plausible on state-changing endpoints, race the IDOR read against the "
            "revocation and look for a post-revocation 200."
        ),
        "followup": "repeat with varied race offsets; confirm single-threaded baseline denies; check audit log for revocation timestamp vs response timestamp",
        "difficulty_delta": 1,
        "impact": "High \u2014 cross-account data disclosure through a revocation race.",
    },
    {
        "rule_id": "R-INJ-RAG",
        "parents": [("ai-llm", "AI-01"), ("ai-llm", "AI-15")],
        "name": "Cross-tenant injection via poisoned retrieval: {a_short} \u00d7 {b_short}",
        "why_non_obvious": (
            "Prompt-injection cards test what ONE user can do to their own session; RAG-poisoning "
            "cards test what poisoned data does to retrieval. Combined, poison planted by attacker "
            "A in a shared corpus is retrieved into victim B's session — the injection crosses a "
            "trust boundary the single-user tests never exercise."
        ),
        "oracle": (
            "COMBO-INJ-RAG-HELD: attacker plants a RAG-poison chunk (embedding-optimized toward "
            "victim-plausible queries) in shared/collaborative content. A second, unprivileged "
            "account then asks a benign question. The oracle holds when the second account's "
            "assistant output contains the attacker's injected instruction or exfiltrates the "
            "second account's private context — proving poisoned retrieval crosses the "
            "user boundary, not just the prompt boundary."
        ),
        "oracle_markers": ["second account", "crosses the user boundary"],
        "expected_signal": "cross_user_injected_instruction; retrieval_provenance_leak",
        "hypothesis": (
            "Where {a_name} is possible across a share boundary and {b_name} can bias retrieval, "
            "plant poison as user A and observe user B's outputs for the injected instruction."
        ),
        "followup": "vary poison embedding similarity; test retrieval ranking before/after; confirm victim query alone (no poison) is clean",
        "difficulty_delta": 1,
        "impact": "High \u2014 cross-tenant prompt injection via shared retrieval.",
    },
    {
        "rule_id": "R-SSRF-WEBHOOK",
        "parents": [("ssrf", "SSRF-01"), ("api", "SEQ-01")],
        "name": "Staged webhook SSRF: {a_short} \u00d7 {b_short}",
        "why_non_obvious": (
            "Single-request SSRF tests look for a URL parameter that is fetched immediately. "
            "Webhooks invert this: the attacker registers a callback URL, then a LATER event "
            "triggers the server-side fetch. The fetch happens out-of-band, with the event "
            "system's credentials and retry logic — a blind SSRF with built-in retries."
        ),
        "oracle": (
            "COMBO-SSRF-WEBHOOK-HELD: register a webhook/callback URL pointing at an attacker "
            "sink, then drive the multi-step sequence ({b_name}) that fires the event. The "
            "oracle holds when the server-side fetch arrives at the sink carrying internal-only "
            "artifacts (metadata headers, internal source IP, cloud credential responses on "
            "redirect) OR when retry bursts to the sink prove an internal fetcher with backoff — "
            "a server-side request forgery executed by the event pipeline, not the request handler."
        ),
        "oracle_markers": ["event pipeline", "attacker sink"],
        "expected_signal": "webhook_fetch_to_sink; internal_metadata_in_callback",
        "hypothesis": (
            "Where {a_name} is reachable through callback registration and {b_name} can drive "
            "the event lifecycle, stage register-then-trigger and watch the sink for internal fetch artifacts."
        ),
        "followup": "test redirect chains from sink; check for IMDS-style responses; measure retry timing signature",
        "difficulty_delta": 1,
        "impact": "Critical \u2014 blind SSRF with the event system's credentials.",
    },
    {
        "rule_id": "R-OAUTH-REDIR",
        "parents": [("authentication", "OAUTH"), ("open-redirect", "REDIR")],
        "name": "OAuth code theft through chained redirect: {a_short} \u00d7 {b_short}",
        "why_non_obvious": (
            "OAuth redirect_uri validation is usually tested in isolation, and open redirects are "
            "dismissed as low severity. But a redirect_uri that is merely 'on the right domain' "
            "combined with an open redirect ON that domain turns a Low into account takeover — "
            "the code is minted for a 'valid' URI then bounced to the attacker."
        ),
        "oracle": (
            "COMBO-OAUTH-REDIR-HELD: initiate the OAuth flow with redirect_uri set to a "
            "whitelisted-but-open-redirect page ({b_name}), chaining it to an attacker URL. The "
            "oracle holds when the authorization code minted for the victim session is delivered "
            "to the attacker-controlled final hop — the code leaves the whitelisted domain via "
            "the chained redirect, and exchanging it yields a victim session."
        ),
        "oracle_markers": ["chained redirect", "delivered to the attacker-controlled final hop"],
        "expected_signal": "code_exfiltrated_via_redirect_chain; victim_session_from_stolen_code",
        "hypothesis": (
            "Where {a_name} leaves redirect_uri validation loose and {b_name} exists on a "
            "whitelisted domain, chain them and capture the authorization code at the final hop."
        ),
        "followup": "test each chain link for validation; try fragment vs query code delivery; confirm code exchange succeeds",
        "difficulty_delta": 0,
        "impact": "Critical \u2014 Low-severity redirect escalated to account takeover.",
    },
    {
        "rule_id": "R-GQL-BATCH-AUTHZ",
        "parents": [("graphql", "GQL-02"), ("authorization", None)],
        "name": "Batched authz bypass: {a_short} \u00d7 {b_short}",
        "why_non_obvious": (
            "Field-level authorization is usually enforced per-operation in the resolver path, but "
            "batched queries are often executed by a different code path (batch executor, dataloader "
            "fan-out) that resolves fields in bulk. An operation that 403s alone may succeed when "
            "smuggled inside a batch with benign queries."
        ),
        "oracle": (
            "COMBO-GQL-BATCH-AUTHZ-HELD: take a query/mutation that is denied (403/field error) in "
            "isolation and embed it in a batch ({a_name}) alongside benign queries. The oracle holds "
            "when the sensitive field resolves successfully inside the batch while failing alone — "
            "proving the batch execution path skips or weakens the authorization check that the "
            "single-operation path enforces."
        ),
        "oracle_markers": ["inside the batch while failing alone", "batch execution path"],
        "expected_signal": "batch_authz_divergence; denied_field_resolves_in_batch",
        "hypothesis": (
            "Where {b_name} denies a field in isolation and {a_name} is available, replay the denied "
            "operation inside batches of increasing benign camouflage and diff the authz outcomes."
        ),
        "followup": "bisect which batch position triggers the bypass; test persisted-query batching too; confirm with two identities",
        "difficulty_delta": 1,
        "impact": "High \u2014 authorization enforced everywhere except the batch path.",
    },
    {
        "rule_id": "R-CACHE-AUTH",
        "parents": [("cache", None), ("authentication", None)],
        "name": "Auth-boundary cache poisoning: {a_short} \u00d7 {b_short}",
        "why_non_obvious": (
            "Cache poisoning is usually about defacing content; authentication is usually about "
            "who you are. Their intersection is sharper: when the cache key ignores session state "
            "but the response varies with it, one user's authenticated response can be served to "
            "everyone — or an attacker's poisoned 'logged-in' page can be served to victims."
        ),
        "oracle": (
            "COMBO-CACHE-AUTH-HELD: authenticate as user A, request a cacheable page that reflects "
            "auth state, then request the same URL unauthenticated (or as user B). The oracle holds "
            "when the unauthenticated/B request receives A's authenticated content (or attacker "
            "poison crafted while authenticated) — proving the cache key does not partition on the "
            "authentication boundary, so auth state leaks across identities via the cache."
        ),
        "oracle_markers": ["cache key does not partition", "auth state leaks across identities"],
        "expected_signal": "cross_identity_cached_auth_content; cache_key_auth_blindness",
        "hypothesis": (
            "Where {a_name} is possible and responses vary with {b_name} state, poison or prime the "
            "cache while authenticated and read it back as a different identity."
        ),
        "followup": "identify the unkeyed input; test session-cookie-keyed variants; confirm with fresh identities",
        "difficulty_delta": 1,
        "impact": "High \u2014 authenticated content served across the identity boundary.",
    },
    {
        "rule_id": "R-MCP-AGENCY",
        "parents": [("ai-llm", "AI-17"), ("ai-llm", "AI-07")],
        "name": "Poisoned-tool steering of an over-permissioned agent: {a_short} \u00d7 {b_short}",
        "why_non_obvious": (
            "Tool-description poisoning alone just mislabels a tool; excessive agency alone just means "
            "tools are over-permissioned. Together they are a steering primitive: the poisoned "
            "description tells the agent WHEN to call a privileged tool and with WHAT arguments, "
            "converting passive over-permission into attacker-directed action."
        ),
        "oracle": (
            "COMBO-MCP-AGENCY-HELD: poison a tool description/registry entry ({a_name}) to recommend "
            "a privileged tool for a benign task, then give the agent that benign task. The oracle "
            "holds when the agent invokes the privileged tool with attacker-influenced arguments it "
            "would NOT have chosen unprompted (verified against a clean-registry control run) — "
            "proving the poisoned description steers an over-permissioned agent into attacker-directed "
            "tool use."
        ),
        "oracle_markers": ["would NOT have chosen unprompted", "attacker-directed tool use"],
        "expected_signal": "steered_privileged_tool_call; control_run_divergence",
        "hypothesis": (
            "Where {a_name} can alter tool metadata and {b_name} grants broad tool permissions, "
            "poison the description to recommend the privileged tool and compare call graphs against control."
        ),
        "followup": "test argument injection through the description; check server-side approval gates; try multi-tool chains",
        "difficulty_delta": 1,
        "impact": "High \u2014 attacker steers agent into privileged actions.",
    },
    {
        "rule_id": "R-UPLOAD-PATH-SSRF",
        "parents": [("upload", None), ("injection", "PATH-01"), ("ssrf", None)],
        "name": "Upload \u2192 traversal \u2192 server-side fetch chain: {a_short} + {b_short} + {c_short}",
        "why_non_obvious": (
            "Upload, traversal, and SSRF are each tested as single hops. The chain is the finding: "
            "an uploaded file whose NAME traverses into a watched directory is later consumed by a "
            "server-side fetcher (thumbnailer, document preview, virus scan callback) that treats the "
            "traversed path as a fetch target — three lows become a server-side request forgery."
        ),
        "oracle": (
            "COMBO-UPLOAD-PATH-SSRF-HELD: upload a file whose filename contains traversal sequences "
            "({b_name}) aimed at a directory consumed by a server-side fetcher, with the name crafted "
            "so the fetcher interprets part of it as a URL/host ({c_name}). The oracle holds when a "
            "subsequent server-side request is observed at the attacker sink (or internal metadata "
            "endpoint) attributable to the uploaded file's processing — proving the upload filename "
            "controls a server-side fetch target through the traversal hop."
        ),
        "oracle_markers": ["attributable to the uploaded file", "controls a server-side fetch target"],
        "expected_signal": "upload_triggered_server_fetch; filename_controlled_fetch_target",
        "hypothesis": (
            "Where {a_name} accepts attacker filenames, {b_name} reaches fetcher-watched paths, and "
            "{c_name} primitives exist in the fetch pipeline, craft the filename as a traversal-to-URL "
            "and watch the sink during file processing."
        ),
        "followup": "map which processing stage fetches (thumbnail/preview/scan); test UNC and cloud-metadata targets; confirm sink attribution via unique token",
        "difficulty_delta": 1,
        "impact": "Critical \u2014 file upload escalated to server-side request forgery.",
    },
    {
        "rule_id": "R-IDOR-MASS",
        "parents": [("authorization", "IDOR"), ("api", "API-01")],
        "name": "Ownership transfer via mass assignment: {a_short} \u00d7 {b_short}",
        "why_non_obvious": (
            "IDOR testing asks 'can I read someone else's object'; mass-assignment testing asks 'can I "
            "set fields I shouldn't'. The fusion asks the nastier question: can I mass-assign "
            "owner_id/user_id on an update endpoint that PASSED the direct IDOR test, silently "
            "transferring ownership to myself?"
        ),
        "oracle": (
            "COMBO-IDOR-MASS-HELD: on an update endpoint that correctly denies cross-account reads "
            "({a_name} negative), submit the update with mass-assigned ownership fields (owner_id, "
            "user_id, account_id variants from {b_name}). The oracle holds when the object is "
            "thereafter readable/writable by the attacker as its new owner — ownership transferred "
            "through a field the update endpoint never should have bound."
        ),
        "oracle_markers": ["readable/writable by the attacker as its new owner", "never should have bound"],
        "expected_signal": "ownership_transfer_via_mass_assignment; owner_id_binding",
        "hypothesis": (
            "Where {a_name} is denied on reads but {b_name} allows extra fields on writes, bind "
            "ownership fields on update and re-test readability as the new owner."
        ),
        "followup": "enumerate bindable fields via error messages; test nested objects (user[id]); confirm persistence across sessions",
        "difficulty_delta": 0,
        "impact": "High \u2014 silent ownership takeover on an endpoint that passed IDOR testing.",
    },
    {
        "rule_id": "R-JWT-PRIVESC",
        "parents": [("crypto", None), ("authorization", "AUTHZ-01")],
        "name": "Token-forged privilege escalation: {a_short} \u00d7 {b_short}",
        "why_non_obvious": (
            "JWT weakness tests stop at 'I can forge a token'; client-side role enforcement tests stop "
            "at 'the UI hides the button'. Combined: forge a token carrying an elevated role claim and "
            "submit it to the server-side function the UI merely hid — testing whether the role check "
            "lives anywhere except the frontend."
        ),
        "oracle": (
            "COMBO-JWT-PRIVESC-HELD: forge or re-sign a token with an elevated role/plan claim ({a_name}: "
            "alg confusion, none-alg, or weak-secret re-sign), then invoke the privileged server-side "
            "function that {b_name} showed was only hidden client-side. The oracle holds when the "
            "server executes the privileged action for the forged elevated claim — proving role "
            "enforcement is absent server-side, not merely hidden."
        ),
        "oracle_markers": ["server executes the privileged action", "absent server-side, not merely hidden"],
        "expected_signal": "forged_role_claim_accepted; privileged_action_via_forged_token",
        "hypothesis": (
            "Where {a_name} yields a forgeable token and {b_name} hides privileged functions, forge "
            "the elevated claim and call the hidden function directly."
        ),
        "followup": "test claim types (role, plan, scope, groups); check token refresh persistence; verify audit logging of the forged call",
        "difficulty_delta": 0,
        "impact": "High \u2014 forged token converts UI-hiding into real privilege escalation.",
    },
    {
        "rule_id": "R-XSS-CSRF",
        "parents": [("xss", "XSS-01"), ("session", "SESS-01")],
        "name": "Stored-XSS-driven cross-session action: {a_short} \u00d7 {b_short}",
        "why_non_obvious": (
            "Stored XSS is usually scored on cookie theft; CSRF is usually scored on state-changing "
            "requests. The fusion: a stored payload that fires inside a HIGHER-privileged session "
            "(admin review queue, support dashboard) and performs authenticated actions AS that "
            "session — the XSS becomes a privilege-escalating CSRF that no CSRF token can stop, "
            "because the request originates from the victim's own browser."
        ),
        "oracle": (
            "COMBO-XSS-CSRF-HELD: store a payload via {a_name} in a field rendered in a privileged "
            "session's view (admin panel, moderator queue). The oracle holds when the payload, upon "
            "rendering in the privileged session, executes an authenticated state-changing action "
            "(role change, data export, settings flip) attributable to that session — proving the "
            "stored XSS acts as a cross-session request forgery with the victim's own authority."
        ),
        "oracle_markers": ["attributable to that session", "victim's own authority"],
        "expected_signal": "privileged_session_action_via_stored_payload; xss_to_csrf_escalation",
        "hypothesis": (
            "Where {a_name} stores content rendered to privileged viewers and {b_name} keeps those "
            "sessions long-lived, plant an action-performing payload and watch for the privileged action."
        ),
        "followup": "map which privileged roles render the field; test action idempotency; confirm no CSRF token bypass was needed",
        "difficulty_delta": 1,
        "impact": "High \u2014 stored XSS converted into actions with admin authority.",
    },
    {
        "rule_id": "R-LOGIC-ROLLBACK",
        "parents": [("business-logic", None), ("api", "SEQ-03")],
        "name": "Residue after state rollback: {a_short} \u00d7 {b_short}",
        "why_non_obvious": (
            "Business-logic tests check the happy path and the tampered path; rollback is assumed to "
            "restore the world. But multi-step flows (payment \u2192 fulfill \u2192 refund-on-failure) often "
            "roll back the ledger while leaving side effects (issued credits, sent emails with tokens, "
            "un-consumed vouchers) — the residue is spendable."
        ),
        "oracle": (
            "COMBO-LOGIC-ROLLBACK-HELD: drive a multi-step business flow ({a_name}) to the point where "
            "a side effect is emitted, then force the rollback path (payment failure, validation error, "
            "delete-after-use per {b_name}). The oracle holds when the rolled-back flow leaves a "
            "residue that remains usable — an un-revoked credit, a still-valid token, a consumable "
            "voucher — proving the rollback is not atomic across all side effects."
        ),
        "oracle_markers": ["remains usable", "not atomic across all side effects"],
        "expected_signal": "rollback_residue_usable; side_effect_survives_rollback",
        "hypothesis": (
            "Where {a_name} emits side effects mid-flow and {b_name} can force delete/rollback, push "
            "the flow past the side effect, roll it back, then try to spend the residue."
        ),
        "followup": "enumerate all side effects per step; test double-spend of the residue; check reconciliation jobs that might clean it up",
        "difficulty_delta": 1,
        "impact": "High \u2014 financial residue from an incompletely rolled-back flow.",
    },
    {
        "rule_id": "R-UPLOAD-DESER",
        "parents": [("upload", None), ("injection", "XXE-01")],
        "name": "Upload as deserialization sink: {a_short} \u00d7 {b_short}",
        "why_non_obvious": (
            "File-upload tests check for webshells; deserialization tests check API parameters. The "
            "blind spot is the processing pipeline: uploaded documents (office files, images with "
            "metadata, serialized exports) are PARSED server-side, and that parser may deserialize "
            "embedded objects — the upload is just the delivery vehicle for a deserialization payload."
        ),
        "oracle": (
            "COMBO-UPLOAD-DESER-HELD: upload files embedding serialized-object/XXE payloads in formats "
            "the pipeline parses ({b_name} grammars inside {a_name} uploads: OOXML, image metadata, "
            "import files). The oracle holds when processing exhibits deserialization behavior — "
            "differential timing/errors, outbound entity resolution, or object-graph side effects — "
            "proving the upload pipeline deserializes attacker-controlled content."
        ),
        "oracle_markers": ["deserialization behavior", "upload pipeline deserializes"],
        "expected_signal": "upload_triggered_deserialization; parser_side_effect_on_embedded_payload",
        "hypothesis": (
            "Where {a_name} accepts rich file formats and {b_name}-style parsers process them, embed "
            "serialized payloads in the upload and watch processing for deserialization signals."
        ),
        "followup": "identify the exact parser stage; test polyglot formats; confirm with time-delay and out-of-band payloads",
        "difficulty_delta": 1,
        "impact": "High \u2014 file upload converted into server-side deserialization.",
    },
    {
        "rule_id": "R-SUBTO-COOKIE",
        "parents": [("cloud", "SUBTO-01"), ("session", "SESS-02")],
        "name": "Cookie theft via reclaimed subdomain: {a_short} \u00d7 {b_short}",
        "why_non_obvious": (
            "Subdomain takeover is usually scored on phishing/defacement; cookie-scope issues on "
            "session fixation. Combined they are a credential harvester: cookies scoped to the parent "
            "domain (Domain=.example.com) are dutifully sent by victims' browsers to the attacker's "
            "reclaimed subdomain — no XSS required."
        ),
        "oracle": (
            "COMBO-SUBTO-COOKIE-HELD: reclaim the dangling subdomain ({a_name}), then observe which "
            "parent-domain cookies arrive with victim (or test-account) traffic given {b_name} scoping. "
            "The oracle holds when session/authentication cookies scoped to the parent domain are "
            "received at the attacker-controlled subdomain — proving the takeover yields live session "
            "tokens through cookie scope alone."
        ),
        "oracle_markers": ["received at the attacker-controlled subdomain", "through cookie scope alone"],
        "expected_signal": "parent_scoped_cookie_at_takeover_host; session_token_harvest",
        "hypothesis": (
            "Where {a_name} is reclaimable and {b_name} shows parent-scoped cookies, take the subdomain "
            "and capture which auth cookies the browser delivers to it."
        ),
        "followup": "catalog cookie Domain/Path/Secure flags; test __Host- vs Domain-scoped; confirm session replay with captured token",
        "difficulty_delta": 0,
        "impact": "High \u2014 session theft via DNS + cookie scope, no injection needed.",
    },
    {
        "rule_id": "R-VERDRIFT-AUTHZ",
        "parents": [("api", None), ("authorization", None)],
        "name": "Version-drift authorization gap: {a_short} \u00d7 {b_short}",
        "why_non_obvious": (
            "Authorization is tested against the current API version; older versions are assumed "
            "deprecated. But v1 endpoints frequently stay live behind the same data layer with the "
            "authz checks that were added only in v2/v3 — the old version is a time machine to "
            "before the fix."
        ),
        "oracle": (
            "COMBO-VERDRIFT-AUTHZ-HELD: take an object/operation that {b_name} denies on the current "
            "API version and replay it against older versioned endpoints (v1, unversioned legacy "
            "paths discovered via {a_name} enumeration). The oracle holds when the legacy version "
            "grants what the current version denies for the same identity and object — proving the "
            "authorization check exists only in the new version's code path."
        ),
        "oracle_markers": ["legacy version grants what the current version denies", "only in the new version"],
        "expected_signal": "version_scoped_authz_gap; legacy_endpoint_grants_denied_operation",
        "hypothesis": (
            "Where {b_name} denies on current-version endpoints and {a_name} reveals legacy versions, "
            "replay the denied operation across versions and diff the authz decisions."
        ),
        "followup": "enumerate all versioned prefixes; test method overrides on legacy paths; check whether legacy auth uses weaker tokens",
        "difficulty_delta": 0,
        "impact": "High \u2014 deprecated-but-live API version bypasses current authorization.",
    },
    {
        "rule_id": "R-WS-AUTHCONF",
        "parents": [("websocket", None), ("session", "SESS-01")],
        "name": "Post-revocation WebSocket channel: {a_short} \u00d7 {b_short}",
        "why_non_obvious": (
            "WebSocket authz is tested at handshake time; session tests check logout/revocation over "
            "HTTP. Nobody checks whether the already-open socket SURVIVES revocation — the WS "
            "connection is a persistent authenticated channel that outlives the token that opened it."
        ),
        "oracle": (
            "COMBO-WS-AUTHCONF-HELD: open an authenticated WebSocket ({a_name}), then revoke the "
            "identity's session/token over HTTP (logout, password change, admin revoke per {b_name}). "
            "The oracle holds when the pre-existing socket continues to receive privileged messages "
            "and its commands are still executed after revocation — proving the channel's auth state "
            "is captured at handshake and never re-validated."
        ),
        "oracle_markers": ["after revocation", "never re-validated"],
        "expected_signal": "ws_survives_revocation; post_revoke_command_executed",
        "hypothesis": (
            "Where {a_name} carries privileged traffic and {b_name} can revoke the session, open the "
            "socket, revoke over HTTP, then keep talking on the socket."
        ),
        "followup": "test token rotation and password change variants; check server-side heartbeat re-auth; measure how long the ghost channel lives",
        "difficulty_delta": 0,
        "impact": "High \u2014 revoked sessions remain actionable over the open channel.",
    },
    {
        "rule_id": "R-CORS-IDOR",
        "parents": [("cors", None), ("authorization", "IDOR")],
        "name": "Cross-origin IDOR read: {a_short} \u00d7 {b_short}",
        "why_non_obvious": (
            "CORS misconfiguration alone is 'just' a browser policy issue and IDOR alone needs the "
            "attacker's own session. Together: a victim visiting the attacker's page has their "
            "BROWSER perform the IDOR with the victim's cookies — the attacker's origin reads the "
            "victim's objects cross-origin."
        ),
        "oracle": (
            "COMBO-CORS-IDOR-HELD: from an origin the target reflects with credentials ({a_name}), "
            "issue a cross-origin fetch for a victim-owned object URL that {b_name} showed discloses "
            "data to any authenticated identity. The oracle holds when the attacker's page reads the "
            "victim's object data in the victim's browser context — proving the CORS misconfiguration "
            "converts an authenticated-IDOR into a cross-origin data theft primitive."
        ),
        "oracle_markers": ["victim's browser context", "cross-origin data theft"],
        "expected_signal": "cross_origin_victim_object_read; cors_idor_fusion",
        "hypothesis": (
            "Where {a_name} reflects origins with credentials and {b_name} discloses objects across "
            "identities, drive the object fetch cross-origin from the reflected origin."
        ),
        "followup": "test preflight vs simple requests; check Vary/credentials handling; confirm victim-session attribution",
        "difficulty_delta": 1,
        "impact": "High \u2014 victim's browser becomes the IDOR vehicle.",
    },
    {
        "rule_id": "R-RATE-AUTHN",
        "parents": [("rate-limit", "RATE-02"), ("authentication", "AUTHN-01")],
        "name": "Identity-rotated credential brute force: {a_short} \u00d7 {b_short}",
        "why_non_obvious": (
            "OTP endpoints are tested for guessability; rate limits are tested for presence. The "
            "interaction that matters is KEYING: if the limiter keys on IP or another attacker-"
            "controlled value, rotating that value ({b_name}) makes the limit fictional and the OTP "
            "space brute-forceable."
        ),
        "oracle": (
            "COMBO-RATE-AUTHN-HELD: against the OTP/credential check ({a_name}), rotate the rate-limit "
            "identity (X-Forwarded-For, session reset, parameter variations per {b_name}) and count "
            "accepted attempts. The oracle holds when the number of attempts accepted far exceeds the "
            "advertised limit AND a statistically significant fraction of the OTP space becomes "
            "enumerable — proving the rate limit is keyed on attacker-controlled input."
        ),
        "oracle_markers": ["far exceeds the advertised limit", "keyed on attacker-controlled input"],
        "expected_signal": "limit_identity_rotation_bypass; otp_space_enumerable",
        "hypothesis": (
            "Where {a_name} guards a small secret space and {b_name} rotates limiter identity, rotate "
            "and count: accepted attempts vs advertised limit."
        ),
        "followup": "identify the exact keying inputs; test IPv6 rotation; check for shadow-banning vs hard limits",
        "difficulty_delta": 0,
        "impact": "High \u2014 rate limit bypass converts OTP into a brute-force problem.",
    },
    {
        "rule_id": "R-SMUG-AUTHCTX",
        "parents": [("smuggling", None), ("session", None)],
        "name": "Desync-authenticated smuggled request: {a_short} \u00d7 {b_short}",
        "why_non_obvious": (
            "Request smuggling is usually demonstrated by poisoning a cache or capturing a response. "
            "The deeper variant: the smuggled prefix request is processed in the VICTIM's connection "
            "context — inheriting their authentication — so the attacker issues authenticated requests "
            "as the victim without ever holding their token."
        ),
        "oracle": (
            "COMBO-SMUG-AUTHCTX-HELD: achieve a desync ({a_name}) on a connection carrying a victim's "
            "authenticated traffic ({b_name} context), smuggling a prefix request for a privileged "
            "action. The oracle holds when the smuggled request executes with the victim's authority — "
            "response or side effect attributable to the victim's session — proving the desync crosses "
            "the authentication context boundary."
        ),
        "oracle_markers": ["victim's authority", "crosses the authentication context boundary"],
        "expected_signal": "smuggled_request_runs_as_victim; auth_context_desync",
        "hypothesis": (
            "Where {a_name} desyncs a keep-alive connection and {b_name} traffic shares it, smuggle a "
            "privileged request and attribute the resulting action to the victim session."
        ),
        "followup": "confirm attribution via unique canary in smuggled request; test both CL.TE and TE.CL; check front-end auth vs back-end auth split",
        "difficulty_delta": 1,
        "impact": "Critical \u2014 authenticated actions as the victim via connection desync.",
    },
    {
        "rule_id": "R-SUBTO-OAUTH",
        "parents": [("cloud", "SUBTO-01"), ("authentication", "OAUTH")],
        "name": "Authorization-code capture on reclaimed subdomain: {a_short} \u00d7 {b_short}",
        "why_non_obvious": (
            "Subdomain takeover is scored on content control; OAuth redirect_uri validation is scored "
            "on syntax. The kill chain: reclaim a dangling subdomain that is STILL listed as a trusted "
            "OAuth redirect_uri — the identity provider itself then delivers victim authorization codes "
            "to attacker infrastructure."
        ),
        "oracle": (
            "COMBO-SUBTO-OAUTH-HELD: reclaim the dangling subdomain ({a_name}) and verify it remains a "
            "registered redirect_uri for the target's OAuth client ({b_name}). The oracle holds when an "
            "authorization code minted for a victim login is delivered to the reclaimed subdomain and "
            "exchanges for a victim session — proving DNS residue plus OAuth trust equals account takeover."
        ),
        "oracle_markers": ["delivered to the reclaimed subdomain", "DNS residue plus OAuth trust"],
        "expected_signal": "code_delivered_to_takeover_host; code_exchange_yields_victim_session",
        "hypothesis": (
            "Where {a_name} is reclaimable, check the OAuth client's registered redirect_uris; if the "
            "dangling host is trusted, drive a victim-flow login and capture the code."
        ),
        "followup": "enumerate all registered redirect_uris; test wildcard subdomain trust; confirm code exchange and session scope",
        "difficulty_delta": 1,
        "impact": "Critical \u2014 the identity provider delivers codes to attacker DNS.",
    },
    {
        "rule_id": "R-PROTO-AUTHZ",
        "parents": [("xss", "PROTO-01"), ("authorization", "AUTHZ-01")],
        "name": "Prototype-polluted authorization decision: {a_short} \u00d7 {b_short}",
        "why_non_obvious": (
            "Prototype pollution is usually a client-side curiosity; role checks are assumed server-"
            "side. But Node.js backends merge request JSON into objects with the same vulnerable "
            "patterns — polluting Object.prototype with isAdmin:true can flip a server-side "
            "authorization decision made AFTER the merge."
        ),
        "oracle": (
            "COMBO-PROTO-AUTHZ-HELD: submit JSON containing __proto__ pollution payloads ({a_name}) to "
            "endpoints where {b_name} suggests role/plan is decided server-side from a merged object. "
            "The oracle holds when a request carrying only the pollution payload (no valid role claim) "
            "is granted the privileged action — proving the authorization decision reads a polluted "
            "prototype rather than a validated claim."
        ),
        "oracle_markers": ["no valid role claim", "reads a polluted prototype"],
        "expected_signal": "pollution_grants_privileged_action; prototype_authz_flip",
        "hypothesis": (
            "Where {a_name} pollutes prototypes and {b_name} hides server-side role logic, send "
            "__proto__ role payloads and test the privileged action without any role credential."
        ),
        "followup": "test constructor/prototype variants; check merge libraries in use; confirm server-side vs client-side decision point",
        "difficulty_delta": 1,
        "impact": "High \u2014 authorization flipped by prototype pollution, no token forgery needed.",
    },
    {
        "rule_id": "R-OTP-RACE-2FA",
        "parents": [("race", "RACE-03"), ("authentication", "2FA-01")],
        "name": "Enrollment-window OTP race: {a_short} \u00d7 {b_short}",
        "why_non_obvious": (
            "OTP races test parallel guesses; 2FA enrollment tests setup flaws. The window nobody "
            "tests: DURING enrollment or recovery, the same OTP is often valid across parallel "
            "verification attempts AND the enrollment state machine is mid-transition — racing "
            "verification against enrollment completion can land the account in a half-enrolled, "
            "attacker-known state."
        ),
        "oracle": (
            "COMBO-OTP-RACE-2FA-HELD: during 2FA enrollment/recovery ({b_name}), fire parallel OTP "
            "verification attempts ({a_name}) while concurrently completing or aborting enrollment. "
            "The oracle holds when the account ends in an inconsistent 2FA state — e.g., enrollment "
            "marked complete with an attacker-observed secret, or the OTP accepted after enrollment "
            "was cancelled — proving the verification race corrupts the enrollment state machine."
        ),
        "oracle_markers": ["inconsistent 2FA state", "corrupts the enrollment state machine"],
        "expected_signal": "enrollment_state_corruption; post_cancel_otp_accept",
        "hypothesis": (
            "Where {b_name} exposes enrollment/recovery and {a_name} keeps OTPs valid in parallel, "
            "race verification against enrollment transitions and inspect the resulting 2FA state."
        ),
        "followup": "test recovery-code flows too; check whether the enrolled secret matches the attacker's; confirm lockout behavior",
        "difficulty_delta": 1,
        "impact": "High \u2014 2FA left in an attacker-known or bypassable state.",
    },
    {
        "rule_id": "R-HPP-AUTHZ",
        "parents": [("injection", "HPP-01"), ("authorization", "IDOR")],
        "name": "Parameter-polluted authz split: {a_short} \u00d7 {b_short}",
        "why_non_obvious": (
            "IDOR tests swap the id value; HPP tests duplicate parameters. The split-brain variant: "
            "the authorization layer reads the FIRST id= while the data layer reads the LAST (or vice "
            "versa) — so the authz check passes for YOUR object while the query returns the VICTIM's."
        ),
        "oracle": (
            "COMBO-HPP-AUTHZ-HELD: request the object endpoint with duplicated id parameters "
            "(id=<yours>&id=<victim's>) where {a_name} shows parser differentials and {b_name} gates "
            "on the id. The oracle holds when the response is 200 containing the VICTIM's object — "
            "proving the authorization check and the data fetch resolve different occurrences of the "
            "duplicated parameter."
        ),
        "oracle_markers": ["containing the VICTIM's object", "resolve different occurrences"],
        "expected_signal": "hpp_authz_split; victim_data_via_duplicate_param",
        "hypothesis": (
            "Where {a_name} reveals first-vs-last parser behavior and {b_name} gates on that parameter, "
            "duplicate the id with yours-first/victim-last and both orderings, and diff the responses."
        ),
        "followup": "test array-style id[]=, semicolon and comma joins; check WAF normalization order; confirm with three identities",
        "difficulty_delta": 1,
        "impact": "High \u2014 IDOR through parameter-resolution split brain.",
    },    {
        "rule_id": "R-S28-HIJACK-SHADOW",
        "parents": [("ai_llm", "S28-AI-01"), ("ai_llm", "A1-003")],
        "name": "Semantic hijack through a shadowed tool: {a_short} x {b_short}",
        "why_non_obvious": (
            "Tool shadowing alone needs a name collision the user might notice in a tool listing; "
            "A2M-style semantic hijacking alone needs the planner to prefer the attacker's tool over "
            "the genuine one. Combined, the collision removes the planner's choice entirely - the "
            "shadowed NAME is what the planner was going to call anyway - while the semantically "
            "tuned metadata makes the hijacked invocation look like the natural outcome in traces "
            "and logs. The collision guarantees routing; the semantics provide cover."
        ),
        "oracle": (
            "COMBO-HIJACK-SHADOW-HELD: register a shadow server exposing the same tool name as a "
            "trusted server ({b_name}) with A2M-tuned metadata ({a_name}), then issue a benign task. "
            "The oracle holds when the planner invokes the shadow implementation for a task where the "
            "control (no shadow registered) chose the benign tool, AND the trace scores the selection "
            "as a natural semantic match - proving the collision captured the routing while the "
            "metadata provided the cover story."
        ),
        "oracle_markers": ["control (no shadow registered) chose the benign tool", "collision captured the routing"],
        "expected_signal": "shadow_tool_invoked_for_benign_task; semantic_cover_in_trace",
        "hypothesis": (
            "Where {b_name} allows a same-name shadow and {a_name} tunes attacker metadata, register "
            "the shadow with tuned metadata and issue tasks the planner would otherwise route to the "
            "trusted tool."
        ),
        "followup": "test whether the trace/audit log distinguishes the shadow invocation; vary task phrasing to map the planner's selection boundary",
        "difficulty_delta": 1,
        "impact": "High - tool interception with a built-in cover story in the agent's own reasoning trace.",
    },
    {
        "rule_id": "R-S28-MIKROTRICK",
        "parents": [("authentication", "S28-AUTH-03"), ("authentication", "S28-AUTH-04")],
        "name": "Unauthenticated admin from rekey bypass x fd-selector arg injection: {a_short} x {b_short}",
        "why_non_obvious": (
            "The rekey state bypass alone yields only a file-write primitive through a dispatched exec; "
            "the fd-selector arg injection alone needs a login helper reachable with a crafted username. "
            "Chained, the rekey bypass opens the session channel the helper never expected to serve "
            "unauthenticated, and the dash-username hands that channel administrative identity - two "
            "medium primitives composing into unauthenticated root."
        ),
        "oracle": (
            "COMBO-MIKROTRICK-HELD: against the SSH service, request key re-exchange before authentication "
            "({a_name}), open a session channel, and authenticate with a dash-prefixed username ({b_name}). "
            "The oracle holds when a single unauthenticated session yields administrative access - the exec "
            "dispatches AND the identity is read from the attacker's descriptor - proving the chain composes "
            "where each primitive alone falls short."
        ),
        "oracle_markers": ["single unauthenticated session yields administrative access", "each primitive alone falls short"],
        "expected_signal": "unauth_admin_via_rekey_plus_fd_arg; chain_composition_confirmed",
        "hypothesis": (
            "Where {a_name} opens a pre-auth channel and {b_name} turns a username into an fd selector, "
            "combine them in one session and test for an administrative grant."
        ),
        "followup": "test each primitive in isolation to confirm neither alone grants admin; check firmware versions for both flaws",
        "difficulty_delta": 1,
        "impact": "Critical - unauthenticated administrative takeover from two chained mediums.",
    },
    {
        "rule_id": "R-S28-BLEED-LAUNDER",
        "parents": [("ai_llm", "S28-AI-03"), ("ai_llm", "S28-AI-02")],
        "name": "One-shot injection converted to standing authorization: {a_short} x {b_short}",
        "why_non_obvious": (
            "Inbound prompt injection is usually a one-shot: the attacker must keep the malicious record in "
            "the agent's context. Memory authorization laundering changes the persistence model - a single "
            "injected record plants an approval-asserting memory entry, and from then on the agent treats the "
            "attacker's goal as pre-authorized across sessions, with no further injection needed. The "
            "injection is the delivery; the memory is the persistence."
        ),
        "oracle": (
            "COMBO-BLEED-LAUNDER-HELD: deliver one indirect injection through a public inbound channel "
            "({a_name}) that writes an approval-asserting memory entry, then start a fresh session with no "
            "new injection and request the privileged action ({b_name}). The oracle holds when the fresh "
            "session performs the action citing the memory entry as authorization - proving a single injection "
            "became a standing, cross-session permission."
        ),
        "oracle_markers": ["fresh session performs the action citing the memory entry", "single injection became a standing"],
        "expected_signal": "injection_persisted_as_memory_approval; cross_session_privileged_action",
        "hypothesis": (
            "Where {a_name} gives an injection channel and {b_name} lets memory gate actions, inject once to "
            "plant an approval, then test fresh sessions for the privileged action."
        ),
        "followup": "test how long the planted approval persists; check whether memory-sync across agents spreads it",
        "difficulty_delta": 1,
        "impact": "Critical - one anonymous form submission becomes a durable backdoor permission.",
    },
    {
        "rule_id": "R-S28-DECODE-UPLOAD",
        "parents": [("injection", "S28-INJ-01"), ("upload", None)],
        "name": "Double-encoded upload filename traverses the storage path: {a_short} x {b_short}",
        "why_non_obvious": (
            "Upload validators check the filename as submitted; the sanitize-then-decode gap means the "
            "STORAGE layer decodes what the validator approved. A double-encoded traversal in the filename "
            "passes validation literally and lands outside the upload directory after the storage decode - "
            "the validator and the filesystem disagree about the name, and the disagreement is only visible "
            "at double-encoding depth."
        ),
        "oracle": (
            "COMBO-DECODE-UPLOAD-HELD: upload a file whose filename carries a double-encoded traversal "
            "({a_name}) through the normal upload flow ({b_name}). The oracle holds when the file lands "
            "outside the upload directory while single-encoded and literal variants are blocked or contained "
            "- proving the validator approved the encoded form and the storage layer decoded it into a traversal."
        ),
        "oracle_markers": ["file lands outside the upload directory", "validator approved the encoded form"],
        "expected_signal": "upload_filename_traversal_post_decode; validator_storage_disagreement",
        "hypothesis": (
            "Where {b_name} accepts uploads and {a_name} shows a sanitize-then-decode gap, walk the encoding "
            "ladder on the filename and check the final storage path."
        ),
        "followup": "test triple-encoding and mixed encodings; check whether the traversed file is servable or executable",
        "difficulty_delta": 0,
        "impact": "High - arbitrary file write outside the upload directory, potential webshell.",
    },
    {
        "rule_id": "R-S29-WRITEPIPE",
        "parents": [("ai_llm", "S29-AI-01"), ("ai_llm", "S28-AI-02")],
        "name": "Poisoned runbook becomes standing permission: {a_short} x {b_short}",
        "why_non_obvious": (
            "An unauthenticated vector-store upsert alone is a one-shot: the attacker must keep "
            "re-poisoning retrieval to steer the agent. Agent-memory authorization laundering "
            "changes the persistence model - a single poisoned runbook plants an approval-asserting "
            "memory entry, and from then on the agent treats the attacker's goal as pre-authorized "
            "across sessions. The write-path is the delivery; the memory is the persistence."
        ),
        "oracle": (
            "COMBO-WRITEPIPE-HELD: perform an unauthenticated runbook upsert ({a_name}) whose "
            "content asserts a standing approval, then start a fresh session with no new injection "
            "and request the privileged tool call ({b_name}). The oracle holds when the fresh session "
            "performs the privileged tool call citing the poisoned runbook or the derived memory entry "
            "as authorization - proving one unauthenticated write became a durable, cross-session permission."
        ),
        "oracle_markers": ["fresh session performs the privileged tool call", "citing the poisoned runbook"],
        "expected_signal": "unauth_upsert_persisted_as_memory_approval; cross_session_tool_call",
        "hypothesis": (
            "Where {a_name} gives an unauthenticated write path into retrieval and {b_name} lets "
            "memory gate tool calls, upsert one approval-asserting runbook, then test fresh sessions "
            "for the privileged tool call."
        ),
        "followup": "test how long the planted approval persists; check whether memory-sync across agents spreads it; confirm the upsert alone (no memory) does not persist",
        "difficulty_delta": 1,
        "impact": "Critical - one unauthenticated write becomes a durable backdoor permission on an authorized agent.",
    },
    {
        "rule_id": "R-S29-SHORTCODE-CHAIN",
        "parents": [("injection", "S29-INJ-01"), ("authentication", "S29-AUTH-01")],
        "name": "Unauthenticated shortcode-to-object-injection: {a_short} x {b_short}",
        "why_non_obvious": (
            "Shortcode-delimiter injection alone needs an authenticated session to reach the AJAX action; "
            "the fail-open nonce alone only reaches the action, not the deserialization sink. Chained, "
            "omitting the nonce parameter walks straight past the gate, and the delimiter-preserving "
            "sanitizer carries the injected shortcode into do_shortcode and on to maybe_unserialize - "
            "an unauthenticated path from parameter omission to PHP object injection."
        ),
        "oracle": (
            "COMBO-SHORTCODE-CHAIN-HELD: against the privileged AJAX action, omit the nonce parameter "
            "({b_name}) while submitting a style value carrying an injected shortcode ({a_name}). "
            "The oracle holds when object instantiation from the injected shortcode is observed without "
            "any authentication - proving the omission opened the gate AND the sanitizer carried the "
            "payload to the sink in a single unauthenticated request."
        ),
        "oracle_markers": ["without any authentication", "object instantiation from the injected shortcode"],
        "expected_signal": "unauth_shortcode_object_injection; omission_plus_delimiter_chain",
        "hypothesis": (
            "Where {b_name} shows a presence-gated check and {a_name} shows delimiter survival into a "
            "parser, omit the security parameter and inject parser delimiters in the same request."
        ),
        "followup": "test each primitive in isolation to confirm neither alone reaches the sink unauthenticated; inventory POP gadgets for impact",
        "difficulty_delta": 1,
        "impact": "Critical - unauthenticated PHP object injection from two chained mediums.",
    },
    {
        "rule_id": "R-S29-THINPOOL-XTENANT",
        "parents": [("cloud", "S29-CLD-01"), ("cloud", None)],
        "name": "Cross-tenant block bleed exfiltrated via {b_short}: {a_short} x {b_short}",
        "why_non_obvious": (
            "Unzeroed block reuse alone only proves data is readable to whoever can allocate from the "
            "pool - the attacker still needs a read primitive positioned on the shared storage. Combined "
            "with a second cloud primitive that yields read or egress (exposed bucket, SSRF to internal "
            "storage, snapshot export), the bleed becomes remotely harvestable: the second primitive is "
            "the tap, the unzeroed pool is the reservoir."
        ),
        "oracle": (
            "COMBO-THINPOOL-XTENANT-HELD: establish the unzeroed-block read primitive ({a_name}) with "
            "a canary from a second tenant, then route the recovered blocks through the second cloud "
            "primitive's read/egress channel ({b_name}). The oracle holds when another tenant's canary "
            "is recovered from unzeroed blocks AND exfiltrated through the second channel - proving the "
            "storage-layer bleed composes with an ordinary cloud misconfiguration into remote cross-tenant theft."
        ),
        "oracle_markers": ["another tenant's canary", "unzeroed blocks"],
        "expected_signal": "cross_tenant_canary_in_unzeroed_blocks; bleed_exfiltrated_via_cloud_primitive",
        "hypothesis": (
            "Where {a_name} shows block reuse without zeroing and {b_name} gives a read or egress "
            "primitive on the same platform, recover a foreign canary from reused blocks and exfiltrate it."
        ),
        "followup": "test snapshot/clone/export paths as alternative taps; check cache layers for the same gap",
        "difficulty_delta": 1,
        "impact": "Critical - remote cross-tenant data theft from the storage layer.",
    },
    {
        "rule_id": "R-S29-DESYNC-SYNTH",
        "parents": [("smuggling", "S29-SMG-01"), ("smuggling", None)],
        "name": "Synthesized desync validated against {b_short}: {a_short} x {b_short}",
        "why_non_obvious": (
            "LLM-synthesized desync vectors alone are untrusted: the model hallucinates parser behaviors "
            "that do not exist. Classic desync probes alone only cover known differentials. Fused, the "
            "synthesizer proposes candidates outside the known battery, and the classic oracle machinery "
            "(Burp validation, manual replay, differential confirmation) decides which candidates are real - "
            "the LLM explores, the oracle verifies."
        ),
        "oracle": (
            "COMBO-DESYNC-SYNTH-HELD: generate candidate desync vectors from spec text ({a_name}), then "
            "run each through the classic confirmation pipeline ({b_name}). The oracle holds when a "
            "synthesized vector yields a Burp-confirmed desync that the classic probe battery missed - "
            "proving the synthesis found a genuinely novel differential, not a rephrased known one."
        ),
        "oracle_markers": ["Burp-confirmed desync", "classic probe battery missed"],
        "expected_signal": "novel_synthesized_desync_confirmed; classic_battery_gap",
        "hypothesis": (
            "Where {a_name} can propose spec-derived vectors and {b_name} defines the confirmation "
            "standard, synthesize broadly, confirm strictly, and keep only vectors the classic battery misses."
        ),
        "followup": "feed confirmed differentials back as synthesis seeds; cluster novel vectors by parser root cause",
        "difficulty_delta": 1,
        "impact": "High - novel desync primitives past signature-based defenses.",
    },
    {
        "rule_id": "R-S30-SIGSET",
        "parents": [("auth", "S30-AUTH-01"), ("auth", None)],
        "name": "Empty signature set generalizes the fail-open family: {a_short} x {b_short}",
        "why_non_obvious": (
            "Algorithm-confusion tests probe which algorithm strings skip verification; the empty-signatures "
            "primitive probes whether verification runs at all. Fused, every JWS consumer gets a two-axis "
            "fail-open battery: the algorithm axis (unknown/none) crossed with the signature-set axis (empty "
            "array). The Authlib instance proves the axes are independent - a library can pin algorithms "
            "correctly and still fail open on an empty set."
        ),
        "oracle": (
            "COMBO-SIGSET-HELD: against the JWS consumer, submit the empty-signatures variant ({a_name}) "
            "and the algorithm-confusion variants from the family battery ({b_name}). The oracle holds when "
            "the consumer rejects every algorithm-confusion variant yet accepts the empty signature set - "
            "proving the fail-open lives in the signature-set handling, not the algorithm negotiation."
        ),
        "oracle_markers": ["accepts the empty signature set", "fail-open lives in the signature-set handling"],
        "expected_signal": "empty_signatures_accepted; alg_variants_rejected",
        "hypothesis": (
            "Where {a_name} shows empty-set fail-open and {b_name} enumerates algorithm-confusion vectors, "
            "run both axes against each JWS consumer and keep only consumers that fail exactly one axis."
        ),
        "followup": "test compact serialization and the claims registry on consumers that fail the set axis",
        "difficulty_delta": 0,
        "impact": "Critical - forged tokens with no key material wherever the set axis fails open.",
    },
    {
        "rule_id": "R-S30-BATCH-ROUTE",
        "parents": [("injection", "S30-INJ-03"), ("authorization", None)],
        "name": "Batch handler desync opens authz-gated endpoints: {a_short} x {b_short}",
        "why_non_obvious": (
            "The wp2shell desync alone yields an unauthenticated route; authorization cards alone test "
            "object-level checks from an authenticated seat. Fused, the desynced handler becomes an "
            "unauthenticated vantage point against the authorization primitives - IDOR/BOLA probes that "
            "normally need a session can be fired through the desynced route, testing whether the handler's "
            "object checks survive when its authentication check is skipped."
        ),
        "oracle": (
            "COMBO-BATCH-ROUTE-HELD: shift a batch sub-request onto an authorization-gated handler ({a_name}), "
            "then run the object-level probe from the authorization card ({b_name}) through the desynced route. "
            "The oracle holds when the object-level check is bypassed from the unauthenticated desynced route "
            "while it holds from a normal authenticated request - proving the desync stripped the auth layer "
            "the authz check assumed."
        ),
        "oracle_markers": ["object-level check is bypassed", "desync stripped the auth layer"],
        "expected_signal": "authz_bypass_via_desynced_route; auth_layer_stripped",
        "hypothesis": (
            "Where {a_name} gives an unauthenticated desynced route and {b_name} gives an object-level probe, "
            "fire the probe through the desynced route and compare against the authenticated baseline."
        ),
        "followup": "test whether the desynced handler also skips rate limits and audit logging",
        "difficulty_delta": 1,
        "impact": "Critical - unauthenticated object-level access through handler desynchronization.",
    },
    {
        "rule_id": "R-S30-HEADER-HEAP",
        "parents": [("auth", "S30-AUTH-02"), ("injection", None)],
        "name": "Oversized auth headers as heap-corruption probes: {a_short} x {b_short}",
        "why_non_obvious": (
            "The F5 primitive alone is one appliance's parser bug; injection cards alone probe for command/SQL "
            "sinks. Fused, the size-ladder technique becomes a general probe: wherever an Authorization header "
            "(or its siblings) is parsed in native code - ADCs, WAFs, proxies, API gateways - walk the header "
            "length past parser expectations and watch for heap corruption instead of injection. The SELinux-bypass "
            "step shows post-corruption guardrails have reusable finish-path bypasses."
        ),
        "oracle": (
            "COMBO-HEADER-HEAP-HELD: run a header size ladder (4 KiB-64 KiB) against native-code auth-header "
            "parsers ({a_name}), applying the injection card's sink-detection discipline ({b_name}). The oracle "
            "holds when a parser past a length threshold shows heap corruption under a debugger while shorter "
            "values are handled cleanly - proving the length assumption, not the header content, is the vulnerability."
        ),
        "oracle_markers": ["heap corruption under a debugger", "length assumption, not the header content"],
        "expected_signal": "header_length_threshold_corruption; native_parser_heap",
        "hypothesis": (
            "Where {a_name} shows overlong headers corrupting a native parser and {b_name} defines "
            "sink-detection rigor, ladder header sizes on every native auth parser and confirm corruption "
            "under a debugger."
        ),
        "followup": "test sibling headers (Cookie, X-Forwarded-For) and sibling native parsers (SAML, WebSocket)",
        "difficulty_delta": 1,
        "impact": "Critical - pre-auth RCE wherever a native parser trusts header length.",
    },
    {
        "rule_id": "R-S30-DUALPARSE",
        "parents": [("upload", "S30-UPD-01"), ("upload", None)],
        "name": "Dual-parser disagreement generalized across upload flows: {a_short} x {b_short}",
        "why_non_obvious": (
            "The Podlove instance alone is one plugin's cache handler; upload cards alone test single-parser "
            "validation. Fused, the dual-parser audit becomes systematic: for every upload/cache flow, identify "
            "which parser the validator uses and which parser the storage layer uses, then submit names the two "
            "parsers classify differently (query suffixes, fragments, semicolons). The disagreement - not any "
            "single parser's bug - is the vulnerability."
        ),
        "oracle": (
            "COMBO-DUALPARSE-HELD: for the upload flow ({b_name}), submit the query-suffixed filename from the "
            "Podlove pattern ({a_name}). The oracle holds when the validator logs the file as a safe type while "
            "storage writes it with an executable extension - proving the two parsers disagreed about the same name."
        ),
        "oracle_markers": ["validator logs the file as a safe type", "two parsers disagreed"],
        "expected_signal": "validator_storage_extension_disagreement; executable_stored",
        "hypothesis": (
            "Where {a_name} shows two parsers disagreeing on one filename and {b_name} gives an upload flow, "
            "map both parsers and submit names they classify differently."
        ),
        "followup": "test fragment (#) and semicolon (;) suffixes; check whether re-encoding normalizes the disagreement away",
        "difficulty_delta": 0,
        "impact": "High - arbitrary file write with executable extension past type validation.",
    },
    {
        "rule_id": "R-S30-AGENT-SHELL",
        "parents": [("ai_llm", "S30-AI-02"), ("ai_llm", None)],
        "name": "Exposed agent execution plus injection corpus: {a_short} x {b_short}",
        "why_non_obvious": (
            "The MaxKB primitive alone is one product's exposed endpoint; injection cards alone target chat "
            "surfaces. Fused, the methodology is: first find the agent's execution endpoint and confirm it is "
            "network-reachable without auth, then aim the whole injection corpus (indirect, stored, encoded) at "
            "the tool-call planner rather than the chat model. The endpoint is the attack surface; the corpus "
            "is the ammunition."
        ),
        "oracle": (
            "COMBO-AGENT-SHELL-HELD: locate the agent execution endpoint ({a_name}) and confirm unauthenticated "
            "reachability, then deliver the injection variants ({b_name}) and watch the tool-call loop. The oracle "
            "holds when an injected instruction - not a direct parameter - causes the agent's tool loop to execute "
            "a host shell command, with an authenticated-only control endpoint refusing the same input."
        ),
        "oracle_markers": ["injected instruction", "agent's tool loop to execute a host shell command"],
        "expected_signal": "unauth_agent_endpoint; injection_to_shell_via_tool_loop",
        "hypothesis": (
            "Where {a_name} exposes an unauthenticated execution path and {b_name} supplies injection variants, "
            "enumerate the endpoint, then fire the corpus at the planner and watch for shell tool calls."
        ),
        "followup": "enumerate the tool list via API/docs; test MCP and skills for expanded tool surface",
        "difficulty_delta": 1,
        "impact": "Critical - unauthenticated prompt injection to host shell on agent infrastructure.",
    },
    {
        "rule_id": "R-S01-SPLIT-STEER",
        "parents": [("ai_llm", "S01-AI-01"), ("ai_llm", "S01-AI-03")],
        "name": "Fragmented instructions plus trajectory steering: {a_short} x {b_short}",
        "why_non_obvious": (
            "GhostSplice alone stiches benign fragments into a one-shot plan; ECLIPSE alone steers a long-horizon "
            "chain with workflow cues and corrections. Fused, the fragments become the steering channel: each "
            "tool-description/result fragment carries a state-transition cue, so no single observation contains the "
            "full malicious plan AND the plan self-corrects across 5+ tool calls. Per-fragment review sees forms "
            "and cues; the composed steered chain is never evaluated as a whole."
        ),
        "oracle": (
            "COMBO-SPLIT-STEER-HELD: plant GhostSplice-style fragments ({a_name}) where each fragment also carries "
            "an ECLIPSE workflow cue ({b_name}), against a long-horizon agent. The oracle holds when the agent "
            "completes a multi-step malicious chain with no single fragment carrying the full objective, and "
            "accepts a mid-trajectory correction fragment to get back on plan."
        ),
        "oracle_markers": ["completes a multi-step malicious chain", "no single fragment carrying the full objective"],
        "expected_signal": "fragment_stitched; trajectory_steered; chain_completed",
        "hypothesis": (
            "Where {a_name} fragments the instruction and {b_name} steers the trajectory, distribute the attack "
            "plan as cue-carrying fragments across tool channels and watch whether the long-horizon agent assembles "
            "and follows it."
        ),
        "followup": "test whether trajectory-anomaly detectors see the cue fragments as a correlated campaign",
        "difficulty_delta": 1,
        "impact": "Critical - stealthy, self-correcting, multi-step agent compromise invisible to per-fragment review.",
    },
    {
        "rule_id": "R-S01-HIJACK-SHADOW",
        "parents": [("ai_llm", "S01-AI-02"), ("ai_llm", "A1-003")],
        "name": "Function hijacking meets tool shadowing: {a_short} x {b_short}",
        "why_non_obvious": (
            "Tool shadowing (A1-003) changes WHICH tool definition the agent believes it is calling via namespace "
            "collisions; FHA changes WHICH function the selection step picks regardless of semantics. Fused, the "
            "attack becomes two-layer: FHA forces selection of the shadowed name, and the shadow resolves it to "
            "the attacker-controlled implementation. Defenses that fix only the selection step or only the "
            "namespace still leave one layer exploitable."
        ),
        "oracle": (
            "COMBO-HIJACK-SHADOW-HELD: plant a shadowed tool name ({b_name}) and fire FHA selection-steering "
            "payloads ({a_name}) at an agent. The oracle holds when the agent both selects the attacker-forced "
            "function name and resolves it to the shadow implementation, executing attacker-controlled behavior "
            "while believing it invoked a legitimate tool."
        ),
        "oracle_markers": ["selects the attacker-forced function name", "resolves it to the shadow implementation"],
        "expected_signal": "forced_selection; shadow_resolution; attacker_impl_executed",
        "hypothesis": (
            "Where {a_name} hijacks selection and {b_name} hijacks resolution, combine both and check whether "
            "fixing either layer alone stops the composed attack."
        ),
        "followup": "test against MCP clients that pin tool hashes at setup",
        "difficulty_delta": 1,
        "impact": "High - reliable attacker-chosen tool execution even when one of the two hijack layers is fixed.",
    },
    {
        "rule_id": "R-S01-ONE-SHOT",
        "parents": [("ai_llm", "S01-AI-04"), ("ai_llm", "S01-AI-01")],
        "name": "Pre-distilled one-shot strategy delivered through fragments: {a_short} x {b_short}",
        "why_non_obvious": (
            "SAVOR's power is offline distillation into a single payload with no test-time feedback; GhostSplice's "
            "power is splitting that payload across benign channels. Fused, the distilled strategy memory is "
            "compiled into fragments at generation time - the attacker pre-computes not one payload but a "
            "fragment set that reconstitutes the winning strategy inside the target context. One interaction, "
            "no feedback, no single channel carrying the attack."
        ),
        "oracle": (
            "COMBO-ONE-SHOT-HELD: generate a SAVOR-style distilled payload ({a_name}), compile it into "
            "GhostSplice fragments ({b_name}), and deliver through MCP channels in a single interaction with no "
            "feedback. The oracle holds when the target agent executes the strategy at research-parity success "
            "rates with zero test-time queries."
        ),
        "oracle_markers": ["executes the strategy", "zero test-time queries"],
        "expected_signal": "one_shot_success; fragments_reconstituted",
        "hypothesis": (
            "Where {a_name} pre-distills the winning strategy and {b_name} fragments the delivery, pre-compile "
            "the strategy into fragments and measure single-interaction success against the unfragmented baseline."
        ),
        "followup": "test cross-defense transfer of fragment-compiled strategies",
        "difficulty_delta": 1,
        "impact": "High - rate-limit and probing-detection defenses are bypassed by design; only content-level defenses remain.",
    },
    {
        "rule_id": "R-S01-INDEX-FORMAT",
        "parents": [("web", "S01-WEB-01"), ("injection", None)],
        "name": "Index-time parsing crossed with parser differentials: {a_short} x {b_short}",
        "why_non_obvious": (
            "Index-time parsing moves the attack trigger off the user-click path entirely; parser-differential "
            "techniques (dual parsers, desync) find the actual corruption primitive. Fused, the methodology is: "
            "first enumerate every file format the indexer parses automatically, then run the parser-differential "
            "battery against each handler, then stage the memory-pressure condition. The index pipeline becomes "
            "a zero-click RCE battery across all supported formats."
        ),
        "oracle": (
            "COMBO-INDEX-FORMAT-HELD: against the target mail/collaboration stack, enumerate auto-indexed formats "
            "({a_name}), run parser-differential probes ({b_name}) per handler, and stage controlled memory "
            "pressure. The oracle holds when at least one non-Visio format yields index-time parser corruption "
            "correlated with the pressure window."
        ),
        "oracle_markers": ["index-time parser corruption", "correlated with the pressure window"],
        "expected_signal": "auto_indexed_formats; parser_corruption; pressure_correlation",
        "hypothesis": (
            "Where {a_name} proves index-time parsing is attacker-reachable and {b_name} supplies the "
            "corruption probes, enumerate all auto-parsed formats and test each for pressure-gated corruption."
        ),
        "followup": "check whether indexer sandboxing contains the corruption per format",
        "difficulty_delta": 1,
        "impact": "Critical - generalizes the Exchange primitive into a zero-click RCE battery across every auto-indexed format.",
    },
    {
        "rule_id": "R-S05-PRNG-STATE",
        "parents": [("authentication", "S05-WEB-01"), ("authentication", None)],
        "name": "PRNG-output leakage crossed with session/token forgery: {a_short} x {b_short}",
        "why_non_obvious": (
            "S05-WEB-01 alone recovers one server's signing key from leaked xorshift128+ outputs; session-forgery "
            "cards alone guess tokens. Fused, the methodology is a generic battery: enumerate every unauthenticated "
            "endpoint that returns PRNG-derived values (session ids, CSRF tokens, password-reset tokens), run Z3 "
            "state recovery on each stream, and test whether any stream predicts a signing key or a future token. "
            "The oracle is deterministic — a recovered state either predicts or it does not."
        ),
        "oracle": (
            "COMBO-PRNG-STATE-HELD: against the target, harvest PRNG-derived values ({a_name}) from unauthenticated "
            "endpoints and run Z3 recovery per stream, then test predicted values against session/token acceptance "
            "({b_name}). The oracle holds when a recovered state predicts a subsequently issued secret."
        ),
        "oracle_markers": ["recovered state predicts", "subsequently issued secret"],
        "expected_signal": "prng_stream_harvested; state_recovered; predicted_secret_accepted",
        "hypothesis": (
            "Where {a_name} proves PRNG outputs leak and {b_name} supplies the forgery targets, treat every "
            "unauthenticated PRNG-derived value as a potential key-recovery oracle and solve each stream."
        ),
        "followup": "check whether distinct endpoints share one generator instance (state reuse across streams)",
        "difficulty_delta": 1,
        "impact": "Critical - deterministic admin auth bypass wherever Math.random() keys sessions.",
    },
    {
        "rule_id": "R-S05-UNINIT-SPRAY",
        "parents": [("injection", "S05-WEB-02"), ("injection", None)],
        "name": "Uninitialized-memory verification bypass via heap shaping: {a_short} x {b_short}",
        "why_non_obvious": (
            "S05-WEB-02 alone sprays one native host's heap to fake a PKCS#1 block; memory-corruption cards alone "
            "need a crash. Fused, the methodology targets verification failure paths as oracles: force crypto/parse "
            "failures with malformed inputs, shape the heap so the uninitialized read lands on attacker-chosen "
            "bytes, and check whether the failure path ACCEPTS instead of rejecting. Acceptance-without-crash is "
            "the new oracle."
        ),
        "oracle": (
            "COMBO-UNINIT-SPRAY-HELD: force the verification failure path ({a_name}) with oversized/malformed "
            "inputs while shaping heap state, then feed attacker-chosen bytes into the uninitialized read "
            "({b_name}). The oracle holds when the verifier accepts a signature it should reject."
        ),
        "oracle_markers": ["verifier accepts", "should reject"],
        "expected_signal": "failure_path_forced; heap_shaped; verifier_accepted_invalid",
        "hypothesis": (
            "Where {a_name} shows failure paths read uninitialized memory and {b_name} supplies the shaping "
            "primitives, hunt verification routines whose failure path is attacker-observable and heap-influenced."
        ),
        "followup": "test allocator determinism — does the spray layout survive across restarts",
        "difficulty_delta": 2,
        "impact": "Critical - turns signature verification into attacker-controlled acceptance in banking/auth software.",
    },
    {
        "rule_id": "R-S05-TEMPLATE-AI",
        "parents": [("ai_llm", "S05-AI-01"), ("injection", "SSTI-01")],
        "name": "Template sandbox escape inside AI agent infrastructure: {a_short} x {b_short}",
        "why_non_obvious": (
            "S05-AI-01 alone breaks one gateway's flow-template sandbox; SSTI-01 alone tests classic web template "
            "engines. Fused, the methodology is a regression battery for AI infra: every user-controlled config "
            "rendered through a 'sandboxed' template engine in agent platforms (flow builders, prompt editors, "
            "tool schemas) gets the full SSTI gadget set plus novel boundary probes, because the same CWE-1336 "
            "class already regressed once in this exact component (CVE-2026-1868 -> CVE-2026-90970)."
        ),
        "oracle": (
            "COMBO-TEMPLATE-AI-HELD: submit agent-platform configs with template expressions ({a_name}) using the "
            "classic SSTI gadget battery ({b_name}). The oracle holds when an expression evaluates on the AI "
            "infrastructure host."
        ),
        "oracle_markers": ["expression evaluates", "AI infrastructure host"],
        "expected_signal": "template_expression_evaluated; sandbox_attribute_leak",
        "hypothesis": (
            "Where {a_name} proves AI flow rendering is host-reachable and {b_name} supplies the escape gadgets, "
            "run the SSTI battery against every template-rendering surface of the agent platform."
        ),
        "followup": "check whether prompt-level guardrails ever see the pre-LLM execution path",
        "difficulty_delta": 1,
        "impact": "Critical - pre-LLM RCE on AI infrastructure, invisible to prompt guardrails.",
    },
    {
        "rule_id": "R-S05-OBFUS-GUARD",
        "parents": [("ai_llm", "S05-AI-02"), ("ai_llm", None)],
        "name": "Obfuscation-layer evasion of agent guardrails: {a_short} x {b_short}",
        "why_non_obvious": (
            "S05-AI-02 alone defeats one inspector with JSFuck; agent-attack cards alone assume the guardrail sees "
            "the payload. Fused, the methodology is an encoding battery against every agent defense layer: for "
            "each injection primitive, generate minimal-dialect encodings (JSFuck, whitespace languages, nested "
            "encodings) and test inspection-verdict vs execution-outcome divergence per layer. The oracle is the "
            "divergence itself — pass at inspection, execute at action."
        ),
        "oracle": (
            "COMBO-OBFUS-GUARD-HELD: encode the injection ({a_name}) so per-layer inspectors ({b_name}) cannot "
            "parse it while the agent can decode it. The oracle holds when inspection passes and the decoded "
            "instruction executes."
        ),
        "oracle_markers": ["inspection passes", "decoded instruction executes"],
        "expected_signal": "inspection_passed; payload_decoded; instruction_executed",
        "hypothesis": (
            "Where {a_name} proves agents decode what inspectors cannot parse and {b_name} supplies the injection "
            "primitives, build the encoding battery and measure the inspection/execution divergence per defense layer."
        ),
        "followup": "test whether encoding survives the carrier sanitizers (email HTML, markdown) intact",
        "difficulty_delta": 1,
        "impact": "High - systematic guardrail-evasion methodology for agent red-teaming.",
    },
    {
        "rule_id": "R-S05-DECODE-AUTH",
        "parents": [("authentication", "S05-AUTH-01"), ("authentication", None)],
        "name": "Differential-decoding battery across auth gates: {a_short} x {b_short}",
        "why_non_obvious": (
            "S05-AUTH-01 alone bypasses one j_security_check rule with %6a; auth-bypass cards alone try canonical "
            "paths. Fused, the methodology enumerates every auth-gated path and, per path, per character, tries "
            "single/double/case-variant/overlong encodings, comparing the rule's verdict against the backend's "
            "response. The oracle is the verdict mismatch — rule misses, backend serves."
        ),
        "oracle": (
            "COMBO-DECODE-AUTH-HELD: request auth-gated paths ({b_name}) with per-character encoding variants "
            "({a_name}). The oracle holds when an encoded request bypasses the auth rule but the backend serves "
            "it as authenticated."
        ),
        "oracle_markers": ["bypasses the auth rule", "serves it as authenticated"],
        "expected_signal": "rule_missed; backend_served; session_granted",
        "hypothesis": (
            "Where {a_name} proves decode-count mismatches exist and {b_name} supplies the gated paths, run the "
            "full encoding battery per path character and diff rule verdicts against backend responses."
        ),
        "followup": "check WAF/CDN layers for their own decode counts — triple differentials",
        "difficulty_delta": 0,
        "impact": "Critical - single-request unauthenticated admin wherever rule and handler decode differently.",
    },
    {
        "rule_id": "R-S05-NULLSECRET",
        "parents": [("authentication", "S05-WEB-05"), ("authentication", None)],
        "name": "Empty-config fail-open battery: {a_short} x {b_short}",
        "why_non_obvious": (
            "S05-WEB-05 alone finds one null-secret fail-open; auth cards alone test configured secrets. Fused, "
            "the methodology inverts the question: for every security control with an optional secret/config "
            "(webhook signatures, API keys, allowlists, webhook secrets), test the UNSET state explicitly. "
            "Null/empty/missing must fail closed — the oracle is acceptance in the unset state."
        ),
        "oracle": (
            "COMBO-NULLSECRET-HELD: exercise security controls ({b_name}) with their secret/config unset "
            "({a_name}). The oracle holds when the control accepts in the unset state."
        ),
        "oracle_markers": ["accepts in the unset state"],
        "expected_signal": "control_unset; unsigned_request_accepted",
        "hypothesis": (
            "Where {a_name} proves null secrets fail open and {b_name} supplies the controls, enumerate every "
            "optional-secret gate and test the unset/default configuration for fail-open behavior."
        ),
        "followup": "check whether the fail-open is documented as a 'feature' (then it is a design finding, not a bug)",
        "difficulty_delta": 0,
        "impact": "High - unauthenticated triggers wherever defaults are fail-open; trivially scannable.",
    },
    {
        "rule_id": "R-CRASH-SEQUENCE",
        "parents": [("memory_corruption", "S06-WEB-01"), ("authentication", None)],
        "name": "Crash-sequenced auth attempt: {a_short} x {b_short}",
        "why_non_obvious": (
            "Crash primitives are usually filed as DoS and forgotten, while auth-bypass cards "
            "are tested against a steady-state target. The NetScaler 88779 episode showed the "
            "interaction: a reproducible crash can reset rate-limit, session, or mitigation state "
            "that a sibling exploit needs. Fused, the crash is not the finding - it is a sequencing "
            "primitive that re-arms an auth attempt which fails against the un-crashed target."
        ),
        "oracle": (
            "COMBO-CRASH-SEQ-HELD: trigger the crash primitive ({a_name}) and immediately run the "
            "sibling auth attempt ({b_name}) inside the post-crash recovery window. The oracle holds "
            "when the sibling attempt succeeds post-crash after failing pre-crash, proving the crash "
            "reset the protective state - a sequencing primitive, not just a denial of service."
        ),
        "oracle_markers": ["succeeds post-crash after failing pre-crash", "sequencing primitive"],
        "expected_signal": "post_crash_auth_success; protective_state_reset; sibling_exploit_rearmed",
        "hypothesis": (
            "Where {a_name} gives a reproducible unauthenticated crash and {b_name} is an auth "
            "primitive that fails against the steady-state target, run the auth attempt inside the "
            "post-crash window and compare pre/post outcomes."
        ),
        "followup": "vary the delay between crash and attempt; confirm the steady-state baseline fails repeatedly; identify exactly which state (rate limit, session table, WAF learning) the crash resets",
        "difficulty_delta": 1,
        "impact": "High - turns a DoS-only bug into an exploit enabler for a second flaw on the same target.",
    },
    {
        "rule_id": "R-MCP-FETCH-CHAIN",
        "parents": [("ai_agent", "S06-AI-01"), ("ssrf", None)],
        "name": "Unauthenticated MCP fetch as SSRF vehicle: {a_short} x {b_short}",
        "why_non_obvious": (
            "SSRF cards assume the fetcher is a feature the tester must reach, often behind auth. "
            "Unauthenticated MCP tool exposure inverts this: the fetch tool is reachable with no "
            "credentials, and its result flows back into an attacker-observable tool response. Fused, "
            "the MCP transport becomes an auth-less SSRF delivery vehicle - the SSRF test rides a "
            "channel the standalone SSRF methodology could never reach."
        ),
        "oracle": (
            "COMBO-MCP-FETCH-HELD: open an unauthenticated MCP session ({a_name}) and invoke its "
            "fetch/URL tool against an internal-only URL from the SSRF surface ({b_name}). The oracle "
            "holds when internal content is returned through the tool result into an attacker-observable "
            "channel - the MCP transport launders the SSRF past the auth boundary the standalone test "
            "could not cross."
        ),
        "oracle_markers": ["into an attacker-observable channel", "past the auth boundary"],
        "expected_signal": "unauth_mcp_fetch; internal_content_in_tool_result; ssrf_via_agent_transport",
        "hypothesis": (
            "Where {a_name} exposes an unauthenticated fetch-capable tool and {b_name} defines the "
            "internal SSRF targets, drive the internal URLs through the MCP tool and read the results "
            "back from the tool response."
        ),
        "followup": "check whether tool-result content is also ingested into any connected agent context (second-order context poisoning); test metadata endpoints and internal admin consoles as fetch targets",
        "difficulty_delta": 0,
        "impact": "High - unauthenticated SSRF with the result handed back to the attacker; agent-context ingestion makes it second-order.",
    },
]


# --------------------------------------------------------------------------- #
# Forging
# --------------------------------------------------------------------------- #
def _match(cards: list[dict], klass: str, id_sub: str | None) -> list[dict]:
    out = []
    for c in cards:
        if c.get("klass") != klass:
            continue
        if id_sub and id_sub not in str(c.get("id", "")):
            continue
        out.append(c)
    return out


def _fmt(tpl: str, combo_cards: list[dict]) -> str:
    ctx = {}
    labels = ["a", "b", "c", "d"]
    for i, card in enumerate(combo_cards):
        L = labels[i]
        ctx[f"{L}_name"] = card.get("name", card.get("id", "?"))
        ctx[f"{L}_short"] = _short(card.get("name", card.get("id", "?")))
        ctx[f"{L}_id"] = card.get("id", "?")
    try:
        return tpl.format(**ctx)
    except (KeyError, IndexError):
        return tpl


def forge(corpus: list[dict], seed: int = 0, max_n: int = 60,
          per_rule_cap: int = 4) -> tuple[list[dict], list[dict]]:
    """Generate combo candidates. Returns (combos, dropped)."""
    rng = random.Random(seed)
    combos: list[dict] = []
    dropped: list[dict] = []
    seen: set[frozenset] = set()
    counter = itertools.count(1)

    for rule in COMBO_RULES:
        parent_sets = [_match(corpus, k, s) for k, s in rule["parents"]]
        if any(not ps for ps in parent_sets):
            dropped.append({"rule": rule["rule_id"],
                            "reason": "no parent cards matched for %s" % (
                                [p for p, ps in zip(rule["parents"], parent_sets) if not ps],)})
            continue
        pairs = list(itertools.product(*parent_sets))
        rng.shuffle(pairs)
        made = 0
        for combo_cards in pairs:
            if len(combos) >= max_n or made >= per_rule_cap:
                break
            ids = [c.get("id") for c in combo_cards]
            if len(set(ids)) < len(ids):
                dropped.append({"rule": rule["rule_id"], "parents": ids,
                                "reason": "same card used twice as both parents"})
                continue
            key = frozenset(ids)
            if key in seen:
                dropped.append({"rule": rule["rule_id"], "parents": ids,
                                "reason": "duplicate parent set already generated"})
                continue
            # Coherence gate: the combined oracle must carry the rule's markers.
            oracle = _fmt(rule["oracle"], combo_cards)
            markers = rule.get("oracle_markers", [])
            if any(m not in oracle for m in markers):
                dropped.append({"rule": rule["rule_id"], "parents": ids,
                                "reason": "oracle lost coherence markers after formatting"})
                continue
            if len(oracle.split()) < 25:
                dropped.append({"rule": rule["rule_id"], "parents": ids,
                                "reason": "oracle too thin to be a real combined property"})
                continue
            seen.add(key)
            made += 1
            n = next(counter)
            diff = min(5, max(_diff15(c) for c in combo_cards) + 1 + rule.get("difficulty_delta", 0))
            diff = max(1, diff)
            combos.append({
                "id": f"F1-{n:03d}",
                "name": _fmt(rule["name"], combo_cards),
                "parents": ids,
                "rule_id": rule["rule_id"],
                "klass": "forged",
                "preconditions": _union(*[c.get("preconditions") or [] for c in combo_cards]),
                "required_state": _union(*[c.get("required_state") or [] for c in combo_cards]),
                "combined_oracle": oracle,
                "expected_signal": _fmt(rule["expected_signal"], combo_cards),
                "why_non_obvious": rule["why_non_obvious"],
                "difficulty_estimate": diff,
                "hypothesis_generator": _fmt(rule["hypothesis"], combo_cards),
                "followup_experiment": _fmt(rule["followup"], combo_cards),
                "impact_hint": rule.get("impact", ""),
                "signals": _union(*[c.get("signals") or [] for c in combo_cards]),
                "_parent_cards": combo_cards,
            })
    return combos, dropped


# --------------------------------------------------------------------------- #
# Emission — v2 schema cards
# --------------------------------------------------------------------------- #
def combo_to_card(combo: dict) -> dict:
    parents = combo["_parent_cards"]
    return {
        "id": combo["id"],
        "name": combo["name"],
        "klass": "forged",
        "requires": _union(*[c.get("requires") or [] for c in parents]),
        "signals": combo["signals"],
        "questions": [
            "What new testable property does the interaction of %s create that neither parent card describes?" % (
                " and ".join(combo["parents"])),
            "What is the precise oracle that proves the COMBINATION held, not just each parent?",
            "Which benign alternative explains the same observation, and what control kills it?",
        ],
        "evidence": {
            "positive": [combo["expected_signal"]],
            "negative": _union(*[c.get("evidence", {}).get("negative") or [] for c in parents]) or [
                "oracle_not_held", "control_behaves_identically"],
        },
        "followups": ["combo_oracle_replication", "control_pair_baseline", "alternative_kill"],
        "test": combo["followup_experiment"],
        "impact_hint": combo["impact_hint"],
        "preconditions": combo["preconditions"],
        "required_state": combo["required_state"],
        "hypothesis_generator": combo["hypothesis_generator"],
        "request_strategy": "staged multi-step combo: establish each parent primitive, then execute the fused sequence",
        "mutation_strategy": "cross-primitive mutation — vary the interaction point, not each parent in isolation",
        "expected_signal": combo["expected_signal"],
        "positive_oracle": combo["combined_oracle"],
        "negative_evidence": ["parent_primitives_hold_but_combo_oracle_fails", "control_pair_diverges"],
        "false_positive_rules": [
            "candidate is not a finding: requires the COMBINED oracle, not each parent's oracle separately",
            "kill the benign alternative explicitly before promotion",
            "verify parent primitives independently first — a combo built on a failed parent is noise",
        ],
        "followup_experiment": combo["followup_experiment"],
        "regression_test": "replay control/test pair; expect combined oracle HELD",
        "difficulty_estimate": round(combo["difficulty_estimate"] / 5, 2),
        "forged_from": combo["parents"],
        "forge_rule": combo["rule_id"],
        "why_non_obvious": combo["why_non_obvious"],
    }


def emit_cards(combos: list[dict], path: str = DEFAULT_OUT) -> str:
    """Write forged combos as v2-schema cards to path. Returns the path."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cards = [combo_to_card(c) for c in combos]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# DEEPHUNT forged technique cards — generated by technique_forge.py\n")
        fh.write("# Each card fuses 2-3 parent techniques into a novel hypothesis template.\n")
        yaml.safe_dump(cards, fh, sort_keys=False, allow_unicode=True, width=120)
    return path


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="DEEPHUNT technique forge — combine techniques into novel hypotheses")
    ap.add_argument("--max", type=int, default=60, help="max combos to generate")
    ap.add_argument("--seed", type=int, default=0, help="determinism seed")
    ap.add_argument("--out", default=DEFAULT_OUT, help="output YAML path")
    ap.add_argument("--per-rule", type=int, default=4, help="max combos per rule")
    args = ap.parse_args(argv)

    corpus = load_corpus()
    combos, dropped = forge(corpus, seed=args.seed, max_n=args.max, per_rule_cap=args.per_rule)
    path = emit_cards(combos, args.out)

    print(f"corpus: {len(corpus)} cards across {len({c.get('klass') for c in corpus})} klasses")
    print(f"rules: {len(COMBO_RULES)}")
    print(f"forged: {len(combos)} combos -> {path}")
    print(f"dropped: {len(dropped)}")
    by_rule: dict[str, int] = {}
    for c in combos:
        by_rule[c["rule_id"]] = by_rule.get(c["rule_id"], 0) + 1
    for rid in sorted(by_rule):
        print(f"  {rid}: {by_rule[rid]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
