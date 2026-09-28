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
