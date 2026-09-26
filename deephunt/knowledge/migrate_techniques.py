"""One-time migration: split knowledge/techniques.yaml (71 flat cards) into
knowledge/techniques/<domain>.yaml with enriched reasoning fields.

Every card gains: requires[], signals[], questions[], evidence{positive[],negative[]},
followups[], test, impact_hint. Source of truth becomes the domain dir; kb.py loads it;
techniques.yaml is regenerated as a merged flat file for backward compatibility.

Run: python3 knowledge/migrate_techniques.py
"""
from __future__ import annotations
import os
import sys
import yaml

BASE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE, "techniques")

# klass -> domain file
DOMAIN = {
    "authorization": "authorization", "authentication": "authentication",
    "session": "authentication",
    "business-logic": "business_logic", "logic": "business_logic", "race": "business_logic",
    "api": "api", "rate-limit": "api", "fuzzing": "api",
    "cloud": "cloud", "supply-chain": "cloud",
    "xss": "web", "injection": "web", "cache": "web", "cors": "web",
    "smuggling": "web", "ssrf": "web", "takeover": "web", "upload": "web",
    "open-redirect": "web", "secrets": "web", "crypto": "web",
    "graphql": "graphql", "websocket": "websocket",
    "ai-llm": "ai_llm", "hardware": "hardware",
}

# Per-klass reasoning enrichment templates.
ENRICH = {
"authorization": {
 "requires": ["authenticated_identity", "object_identifier"],
 "questions": ["Who owns this object?", "Who should access it?",
               "Does authorization depend on object ownership or only on login?",
               "What changes when a second owned identity requests the same object?"],
 "evidence": {"positive": ["unauthorized_object_access", "cross_identity_data_leak",
                           "privilege_differs_by_identity"],
              "negative": ["explicit_denial", "identical_behavior_across_identities",
                           "ownership_checked_server_side"]},
 "followups": ["compare_identities", "compare_objects", "inspect_state_transition"]},
"authentication": {
 "requires": ["owned_test_account"],
 "questions": ["What proves this identity is who it claims?", "Where is the credential checked — client or server?",
               "Can the check be skipped, replayed, or desynchronized?", "What happens on the Nth attempt?"],
 "evidence": {"positive": ["credential_check_bypassed", "unlimited_attempts", "stale_credential_accepted"],
              "negative": ["server_side_verification", "attempts_limited_and_logged", "single_use_enforced"]},
 "followups": ["replay_request", "desync_state", "inspect_error_oracle"]},
"business_logic": {
 "requires": ["understood_workflow", "observed_states"],
 "questions": ["What is the valid state machine here?", "Which transition is the attacker trying to force?",
               "Is the transition authorized, or only the endpoint?", "What invariant would this break?"],
 "evidence": {"positive": ["invalid_transition_accepted", "state_dependent_authz_bypassed", "invariant_violated"],
              "negative": ["transition_rejected", "state_validated_server_side", "invariant_holds_under_test"]},
 "followups": ["map_full_workflow", "test_adjacent_transitions", "check_side_effects"]},
"api": {
 "requires": ["endpoint_inventory"],
 "questions": ["Is this endpoint documented or shadow?", "What parameters does it accept beyond the docs?",
               "Are limits (rate, size, depth) enforced server-side?", "Does versioning change the security model?"],
 "evidence": {"positive": ["undocumented_parameter_honored", "limit_not_enforced", "mass_assignment_accepted"],
              "negative": ["strict_schema_validation", "limits_enforced", "unknown_params_rejected"]},
 "followups": ["fuzz_parameters", "compare_api_versions", "probe_rate_limits"]},
"cloud": {
 "requires": ["cloud_asset_inventory"],
 "questions": ["What identity is this resource running as?", "What can that identity reach?",
               "Is this resource addressable from the internet?", "Where do secrets live at runtime?"],
 "evidence": {"positive": ["metadata_service_reachable", "public_resource_exposed", "overprivileged_role"],
              "negative": ["imds_restricted", "resource_private", "least_privilege_role"]},
 "followups": ["enumerate_iam", "test_metadata_paths", "check_bucket_policy"]},
"web": {
 "requires": ["http_observation"],
 "questions": ["Where does untrusted input flow?", "Is the dangerous sink reachable?",
               "Is the defense enforced at the trust boundary?", "What does the error reveal?"],
 "evidence": {"positive": ["payload_executed", "input_reaches_sink", "defense_bypassed"],
              "negative": ["output_encoded", "input_neutralized", "defense_at_boundary"]},
 "followups": ["trace_data_flow", "test_parser_differentials", "check_defense_location"]},
"graphql": {
 "requires": ["graphql_endpoint", "introspection_or_schema"],
 "questions": ["Is authorization checked per-field or per-query?", "What does introspection expose?",
               "Can queries be batched or aliased to amplify?", "Do persisted queries change the rules?"],
 "evidence": {"positive": ["field_level_authz_missing", "introspection_exposes_schema", "batching_amplifies"],
              "negative": ["per_field_authorization", "introspection_disabled", "batching_limited"]},
 "followups": ["introspect_schema", "test_field_as_second_user", "try_batching"]},
"websocket": {
 "requires": ["ws_endpoint", "observed_messages"],
 "questions": ["Is the handshake authenticated?", "Is Origin checked?", "Can messages be replayed or forged cross-site?",
               "Does the server validate message structure?"],
 "evidence": {"positive": ["unauthenticated_handshake", "origin_not_checked", "replay_accepted"],
              "negative": ["handshake_requires_auth", "origin_validated", "message_authenticity_checked"]},
 "followups": ["replay_message", "cross_site_handshake", "fuzz_message_schema"]},
"ai_llm": {
 "requires": ["ai_feature_surface"],
 "questions": ["Where does untrusted content enter the model context?", "What trust boundary does the output cross?",
               "Is the model output treated as data or as instruction?", "What can the tool-use layer reach?"],
 "evidence": {"positive": ["injection_crosses_boundary", "model_output_treated_as_instruction", "tool_abuse_possible"],
              "negative": ["untrusted_content_sandboxed", "output_treated_as_data", "tool_scope_limited"]},
 "followups": ["map_content_flows", "test_tool_boundaries", "probe_system_prompt_leak"]},
"hardware": {
 "requires": ["hardware_or_firmware_surface"],
 "questions": ["What is the trust boundary in silicon?", "What leaks across it — timing, power, EM?",
               "Is the secret ever in the clear?", "What does the update mechanism trust?"],
 "evidence": {"positive": ["side_channel_leak", "secret_in_clear", "unsigned_update_accepted"],
              "negative": ["constant_time", "secret_protected", "signed_updates_only"]},
 "followups": ["measure_side_channel", "inspect_update_chain", "check_debug_interfaces"]},
}

# Per-card overrides for high-value cards (extra specificity for scholar mode).
OVERRIDES = {
"IDOR-01": {"questions": ["Does the object ID in the URL decide authorization, or does the server check ownership?",
   "What happens with another owned account's ID — 200 with their data, 403, or 404?",
   "Is the ID predictable (sequential) or random — and does randomness substitute for a check?"],
   "followups": ["compare_identities", "predict_adjacent_ids", "try_method_override"]},
"AUTHZ-01": {"questions": ["Is the privilege check in the UI only, or repeated on the API?",
   "What does the API return when a low-privilege token calls the privileged action directly?"],
   "followups": ["replay_as_low_priv", "tamper_role_param"]},
"AUTHN-01": {"questions": ["Is the OTP attempt counter server-side and per-account?",
   "Does the verification response leak validity (timing, message, status)?"],
   "followups": ["probe_rate_limit", "inspect_error_oracle"]},
"JWT-01": {"questions": ["Does the server verify the signature, or trust the alg header?",
   "What happens with alg=none, or a key-confusion (RS256→HS256)?", "Are claims like role/exp actually enforced?"],
   "followups": ["tamper_alg", "confuse_key", "edit_claims"]},
"OAUTH-01": {"questions": ["Is redirect_uri validated against an exact allowlist?",
   "Can the authorization code be replayed or stolen via an open redirector?"],
   "followups": ["test_redirect_uri_variants", "steal_code_via_redirector"]},
"SESS-01": {"questions": ["Is the session ID rotated at login?", "Does logout invalidate server-side?",
   "Can two sessions for one account disagree about privilege?"],
   "followups": ["fixate_session", "test_logout_invalidation"]},
"RACE-01": {"questions": ["Is there a check-then-act gap?", "What resource is finite — balance, stock, coupon uses?",
   "Does the backend serialize the critical section?"],
   "followups": ["parallelize_requests", "measure_serialization"]},
"SSRF-01": {"questions": ["Does the fetcher resolve DNS itself or trust the URL?",
   "Is 169.254.169.254 / metadata reachable? What about DNS rebinding?", "Which parser validates the URL — and which fetches it?"],
   "followups": ["test_metadata_paths", "dns_rebinding", "parser_differential"]},
"XSS-01": {"questions": ["Where does the input reflect — HTML, attribute, JS, URL context?",
   "Is encoding applied at output, and is it the right one for the context?"],
   "followups": ["identify_sink_context", "test_encoding_bypass"]},
"SQLI-01": {"questions": ["Is the input concatenated into a query?", "Do errors or timing reveal query structure?",
   "Are stacked queries or out-of-band exfil possible?"],
   "followups": ["test_error_oracle", "test_time_oracle"]},
"GQL-01": {"questions": ["Which fields are protected — and is the check per field?",
   "What does introspection reveal about hidden types and mutations?"],
   "followups": ["introspect_schema", "test_field_as_second_user"]},
"WS-01": {"questions": ["Does the WebSocket handshake carry and verify auth?",
   "Is the Origin header validated, or can any site open the socket?"],
   "followups": ["cross_site_handshake", "replay_message"]},
"AI-01": {"questions": ["Whose content reaches the model — and is it marked untrusted?",
   "Does model output drive actions (tools, emails, publishes)?"],
   "followups": ["map_content_flows", "test_tool_boundaries"]},
"BLO-01": {"questions": ["What is the valid order lifecycle?", "Which transition is missing a guard?",
   "Can a cancelled/expired state be revived?"],
   "followups": ["map_full_workflow", "test_adjacent_transitions"]},
"CACHE-01": {"questions": ["What is the cache key — and what security-relevant input is NOT in it?",
   "Can one user's poisoned response be served to another?"],
   "followups": ["identify_unkeyed_inputs", "test_cross_user_poison"]},
"CORS-01": {"questions": ["Is the Origin reflected with credentials allowed?",
   "Is the allowlist a suffix/prefix match an attacker can satisfy?"],
   "followups": ["test_origin_reflection", "try_trusted_subdomain"]},
"SUBTO-01": {"questions": ["Does the DNS record point at an unclaimed external service?",
   "Can the service still be claimed under the program's rules?"],
   "followups": ["verify_dangling", "check_claimability"]},
"UPLOAD-01": {"questions": ["Is the file type validated by content or only extension/MIME?",
   "Where is the file stored — and is it served from the app's origin?"],
   "followups": ["polyglot_upload", "check_serving_origin"]},
"RATE-01": {"questions": ["Is the limit per-IP, per-account, or per-endpoint — and which is missing?",
   "Do headers (X-Forwarded-For) reset the counter?"],
   "followups": ["probe_rate_limits", "spoof_client_ip"]},
}

def enrich(card):
    klass = card.get("klass", "")
    tpl = ENRICH.get(klass, ENRICH["web"])
    out = dict(card)
    out["requires"] = list(tpl["requires"])
    out["signals"] = list(card.get("signals") or [])
    out["questions"] = list(tpl["questions"])
    out["evidence"] = {"positive": list(tpl["evidence"]["positive"]),
                       "negative": list(tpl["evidence"]["negative"])}
    out["followups"] = list(tpl["followups"])
    ov = OVERRIDES.get(card.get("id", ""))
    if ov:
        if "questions" in ov: out["questions"] = ov["questions"]
        if "followups" in ov: out["followups"] = ov["followups"]
    return out

def dump_card(card):
    """Compact block-style YAML for one card (keeps train.py's legacy parser happy)."""
    lines = [f"- id: {card['id']}", f"  name: {card.get('name','')}",
             f"  klass: {card.get('klass','')}"]
    lines.append("  requires: [" + ", ".join(card["requires"]) + "]")
    sigs = ", ".join(f'"{s}"' for s in card["signals"])
    lines.append(f"  signals: [{sigs}]")
    lines.append("  questions:")
    for q in card["questions"]: lines.append(f'    - "{q}"')
    lines.append("  evidence:")
    lines.append("    positive: [" + ", ".join(card["evidence"]["positive"]) + "]")
    lines.append("    negative: [" + ", ".join(card["evidence"]["negative"]) + "]")
    lines.append("  followups: [" + ", ".join(card["followups"]) + "]")
    lines.append("  test: >")
    for tl in str(card.get("test","")).strip().splitlines():
        lines.append("    " + tl)
    lines.append(f"  impact_hint: {card.get('impact_hint','')}")
    return "\n".join(lines)

# Duplicate card IDs in the source (distinct cards sharing an ID) get renamed.
# Also fixes one mislabeled card (GQL-01 with klass "authorization").
DEDUP = {
    ("AI-01", "Indirect prompt injection via shared content"): "AI-04",
    ("AI-02", "LLM output handling flaws (XSS/tool-output injection)"): "AI-05",
    ("GQL-01", "GraphQL field-level authorization gaps"): "GQL-04",
    ("OAUTH-01", "OAuth redirect_uri / state confusion"): "OAUTH-02",
    ("SSRF-02", "SSRF via parser differentials"): "SSRF-03",
    ("CACHE-01", "Web cache poisoning via unkeyed inputs"): "CACHE-02",
    ("WS-01", "WebSocket authorization and CSRF"): "WS-02",
}
FIX_KLASS = {("GQL-01", "GraphQL field-level authorization gaps"): "graphql"}


def normalize(card):
    key = (card.get("id"), card.get("name"))
    if key in DEDUP:
        card["id"] = DEDUP[key]
    if key in FIX_KLASS:
        card["klass"] = FIX_KLASS[key]
    return card


def main():
    cards = [normalize(c) for c in yaml.safe_load(open(os.path.join(BASE, "techniques.yaml")))]
    assert len(cards) == 71, f"expected 71, got {len(cards)}"
    ids = [c["id"] for c in cards]
    assert len(set(ids)) == len(ids), "duplicate card ids in source"
    os.makedirs(OUT_DIR, exist_ok=True)
    files = list(dict.fromkeys(DOMAIN.values()))  # ordered unique
    buckets = {f: [] for f in files}
    for nc in NEW_CARDS:
        buckets.setdefault(nc["_domain"], [])
    for c in cards:
        dom = DOMAIN.get(c.get("klass", ""), "web")
        buckets[dom].append(enrich(c))
    for nc in NEW_CARDS:
        buckets[nc["_domain"]].append(nc)
    for dom, clist in buckets.items():
        path = os.path.join(OUT_DIR, f"{dom}.yaml")
        header = (f"# DEEPHUNT technique cards — {dom} domain\n"
                  f"# Enriched: requires/signals/questions/evidence/followups per card.\n"
                  f"# Source of truth for kb.load_techniques(). {len(clist)} cards.\n\n")
        body = "\n\n".join(dump_card(c) for c in clist) + "\n"
        open(path, "w").write(header + body)
        print(f"{dom}.yaml: {len(clist)} cards")
    # regenerate merged flat file for backward compatibility
    order = files + [d for d in buckets if d not in files]
    merged = []
    for dom in order:
        for c in buckets[dom]:
            merged.append(dump_card(c))
    open(os.path.join(BASE, "techniques.yaml"), "w").write(
        "# MERGED — generated by knowledge/migrate_techniques.py from knowledge/techniques/*.yaml\n"
        "# Do not edit by hand; edit the domain files and re-run the migration.\n\n"
        + "\n\n".join(merged) + "\n")
    total = sum(len(v) for v in buckets.values())
    print(f"TOTAL: {total} cards ({len(cards)} migrated + {len(NEW_CARDS)} new)")

NEW_CARDS = [
 # ---- business_logic (thin: 6 -> 10)
 {"id":"BLO-02","name":"Coupon/promo stacking and reuse abuse","klass":"business-logic","_domain":"business_logic",
  "requires":["understood_workflow","observed_states"],
  "signals":["coupon","promo","discount","voucher","cart"],
  "questions":["Is the coupon single-use — and is that enforced server-side?","Can codes stack beyond the intended combination?","Does the discount survive cart mutation after application?"],
  "evidence":{"positive":["coupon_reused","stacking_beyond_policy","discount_survives_mutation"],"negative":["single_use_enforced","stacking_limited","revalidated_on_change"]},
  "followups":["reuse_coupon","stack_codes","mutate_cart_after_apply"],
  "test":"With owned accounts: apply a single-use coupon twice (replay, second account, race). Stack multiple codes. Change cart contents after discount. Compare final totals.",
  "impact_hint":"Medium — revenue loss; often paid as business-logic."},
 {"id":"BLO-03","name":"Currency/price tampering on checkout","klass":"business-logic","_domain":"business_logic",
  "requires":["understood_workflow","observed_states"],
  "signals":["price","amount","currency","total","checkout"],
  "questions":["Is the price trusted from the client request?","Does changing currency change the charged amount?","Is the total recomputed server-side at payment time?"],
  "evidence":{"positive":["client_price_honored","currency_changes_amount","total_not_recomputed"],"negative":["server_side_pricing","currency_fixed","total_recomputed"]},
  "followups":["tamper_price_param","switch_currency","race_price_change"],
  "test":"Intercept checkout: modify price/amount/currency params. Try currency switch mid-flow. Verify what the payment provider is actually charged (use test mode / $0 SKUs).",
  "impact_hint":"High — direct financial impact."},
 {"id":"BLO-04","name":"Referral/affiliate self-dealing","klass":"business-logic","_domain":"business_logic",
  "requires":["understood_workflow"],
  "signals":["referral","affiliate","invite","reward","credit"],
  "questions":["Can an account refer itself (second account, same device/IP)?","Is the reward granted before the referee does anything real?","Are referral rewards capped or rate-limited?"],
  "evidence":{"positive":["self_referral_paid","reward_before_action","no_cap"],"negative":["self_referral_blocked","reward_on_verified_action","capped"]},
  "followups":["self_refer","farm_rewards","check_caps"],
  "test":"Two owned accounts: A refers B, B signs up minimally. Check if A is credited. Try loops of fresh accounts for farming.",
  "impact_hint":"Medium — scalable fraud."},
 {"id":"LOGIC-03","name":"Negative/zero quantity and arithmetic abuse","klass":"business-logic","_domain":"business_logic",
  "requires":["understood_workflow"],
  "signals":["quantity","qty","amount","cart","order"],
  "questions":["Are quantity bounds validated server-side?","What does quantity=-1 or 0 do to the total?","Do refunds/credits derive from the same arithmetic?"],
  "evidence":{"positive":["negative_qty_accepted","total_decreases","refund_exceeds_payment"],"negative":["bounds_validated","qty_clamped","refund_capped"]},
  "followups":["negative_quantity","zero_quantity","fractional_quantity"],
  "test":"Set qty to -1, 0, 99999999, 0.5 on cart/order update. Observe totals, inventory, and any credit/refund flows.",
  "impact_hint":"Medium-High — price manipulation."},
 # ---- websocket (thin: 2 -> 5)
 {"id":"WS-03","name":"WebSocket handshake without authentication","klass":"websocket","_domain":"websocket",
  "requires":["ws_endpoint","observed_messages"],
  "signals":["ws://","wss://","socket","websocket","upgrade"],
  "questions":["Does the WS handshake verify the session/token?","Can an unauthenticated client subscribe to another user's channel?","Are channel names guessable?"],
  "evidence":{"positive":["unauthenticated_handshake","cross_user_channel_access","guessable_channels"],"negative":["handshake_requires_auth","channel_authz_checked","unguessable_tokens"]},
  "followups":["omit_auth_on_handshake","guess_channel","subscribe_as_anon"],
  "test":"Open the WS without cookies/token. Try subscribing to channels belonging to another owned account. Compare message visibility.",
  "impact_hint":"High — real-time data leak."},
 {"id":"WS-04","name":"WebSocket message replay / forgery","klass":"websocket","_domain":"websocket",
  "requires":["ws_endpoint","observed_messages"],
  "signals":["ws://","wss://","socket","message","emit"],
  "questions":["Are messages authenticated per-message or only at handshake?","Can a captured message be replayed to trigger the action again?","Can message fields (sender, target) be forged?"],
  "evidence":{"positive":["replay_accepted","sender_spoofed","no_per_message_auth"],"negative":["replay_rejected","sender_verified","nonces_enforced"]},
  "followups":["replay_message","forge_sender","tamper_target"],
  "test":"Capture a legitimate WS action message; replay it later and as the other owned account. Forge sender/target fields.",
  "impact_hint":"Medium-High — action forgery."},
 {"id":"WS-05","name":"Cross-site WebSocket hijacking (missing Origin check)","klass":"websocket","_domain":"websocket",
  "requires":["ws_endpoint"],
  "signals":["ws://","wss://","origin","socket"],
  "questions":["Is the Origin header validated on the WS handshake?","Can an attacker's page open an authenticated socket using the victim's cookies?","Does the socket rely on cookie auth?"],
  "evidence":{"positive":["origin_not_checked","cross_site_socket_opened","cookie_auth_reused"],"negative":["origin_validated","token_not_cookie","csrf_style_blocked"]},
  "followups":["cross_site_handshake","test_origin_variants"],
  "test":"From a cross-origin page context, attempt the WS handshake with victim cookies (lab only, owned accounts). Try Origin spoofing variants.",
  "impact_hint":"High — CSWSH, equivalent to CSRF on real-time actions."},
 # ---- mobile (new domain: 5)
 {"id":"MOB-01","name":"Deep link / universal link hijacking","klass":"mobile","_domain":"mobile",
  "requires":["mobile_app_surface"],
  "signals":["deeplink","intent://","myapp://","applinks","universal"],
  "questions":["Which deep links carry auth tokens or actions?","Can a malicious link trigger a sensitive action without confirmation?","Are link parameters validated before use?"],
  "evidence":{"positive":["token_in_deeplink","action_without_confirm","param_not_validated"],"negative":["no_sensitive_deeplinks","confirm_before_action","params_validated"]},
  "followups":["craft_malicious_link","test_token_leak","fuzz_link_params"],
  "test":"Enumerate deep link schemes (manifest/assetlinks). Craft links with tokens and actions; observe handling. Check for token leakage via referrer.",
  "impact_hint":"Medium-High — account takeover via link."},
 {"id":"MOB-02","name":"Insecure local storage of secrets","klass":"mobile","_domain":"mobile",
  "requires":["mobile_app_surface"],
  "signals":["sharedpreferences","keystore","sqlite","storage","token"],
  "questions":["Are tokens/keys stored in plaintext prefs or files?","Is the platform keystore actually used?","What survives app uninstall / backup?"],
  "evidence":{"positive":["plaintext_token_storage","backup_includes_secrets","world_readable"],"negative":["keystore_used","encrypted_storage","backup_excluded"]},
  "followups":["inspect_app_storage","check_backup_rules","test_rooted_access"],
  "test":"On an owned test device: inspect app sandbox storage for tokens/keys in plaintext. Check backup manifests and file permissions.",
  "impact_hint":"Medium — local attacker / malware extraction."},
 {"id":"MOB-03","name":"Missing certificate pinning enables MITM","klass":"mobile","_domain":"mobile",
  "requires":["mobile_app_surface"],
  "signals":["https","certificate","pinning","tls","api"],
  "questions":["Does the app pin its API certificate?","Can a lab proxy with a custom CA intercept API traffic?","Are tokens visible in intercepted traffic?"],
  "evidence":{"positive":["no_pinning","traffic_interceptable","token_visible"],"negative":["pinning_enforced","intercept_blocked"]},
  "followups":["proxy_with_custom_ca","inspect_token_exposure"],
  "test":"Route owned test device traffic through a lab proxy with installed CA. Observe whether API calls succeed and what secrets are visible.",
  "impact_hint":"Medium — network attacker credential theft."},
 {"id":"MOB-04","name":"Exported component / intent spoofing","klass":"mobile","_domain":"mobile",
  "requires":["mobile_app_surface"],
  "signals":["exported","intent","activity","broadcast","deeplink"],
  "questions":["Which activities/services are exported?","Can another app invoke them with crafted extras?","Do exported components re-check authorization?"],
  "evidence":{"positive":["exported_sensitive_component","intent_extras_trusted","no_recheck"],"negative":["not_exported","extras_validated","authz_rechecked"]},
  "followups":["enumerate_exported","craft_intent","test_extras_trust"],
  "test":"Parse the manifest for exported components. Send crafted intents with extras from a second lab app; observe privileged actions.",
  "impact_hint":"Medium-High — local privilege escalation."},
 {"id":"MOB-05","name":"Biometric auth fallback bypass","klass":"mobile","_domain":"mobile",
  "requires":["mobile_app_surface"],
  "signals":["biometric","fingerprint","faceid","fallback","pin"],
  "questions":["What happens when biometrics fail or are unavailable?","Is the fallback (PIN/pattern) weaker and brute-forceable?","Is biometric success verified server-side for sensitive actions?"],
  "evidence":{"positive":["weak_fallback","fallback_bruteforceable","client_only_check"],"negative":["strong_fallback","fallback_rate_limited","server_verified"]},
  "followups":["trigger_fallback","bruteforce_fallback","bypass_biometric"],
  "test":"Force biometric failure; examine fallback strength and rate limiting. Check whether sensitive actions re-verify server-side.",
  "impact_hint":"Medium — local device attacker."},
 # ---- cloud (thin: 2 -> 6)
 {"id":"CLD-02","name":"SSRF to cloud instance metadata (IMDS)","klass":"cloud","_domain":"cloud",
  "requires":["cloud_asset_inventory"],
  "signals":["169.254.169.254","metadata","imds","url=","fetch"],
  "questions":["Can a URL-fetch feature reach 169.254.169.254?","Is IMDSv2 (token-required) enforced?","What credentials does the metadata expose?"],
  "evidence":{"positive":["metadata_reachable","imds_v1","credentials_exposed"],"negative":["metadata_blocked","imds_v2_enforced","no_url_fetch"]},
  "followups":["test_metadata_paths","try_imdsv2_bypass","enumerate_roles"],
  "test":"Via any URL-fetch feature, request http://169.254.169.254/latest/meta-data/. Try IMDSv2 token flow. Never exfiltrate real creds — lab/owned infra only.",
  "impact_hint":"Critical — cloud credential theft."},
 {"id":"CLD-03","name":"Public cloud storage bucket exposure","klass":"cloud","_domain":"cloud",
  "requires":["cloud_asset_inventory"],
  "signals":["s3","bucket","storage.googleapis","blob.core",".amazonaws"],
  "questions":["Are storage buckets listable or readable anonymously?","Do bucket names leak via JS, errors, or certs?","Is sensitive data (backups, logs, PII) in the bucket?"],
  "evidence":{"positive":["anonymous_list","anonymous_read","sensitive_data_exposed"],"negative":["bucket_private","access_denied_anonymous"]},
  "followups":["enumerate_buckets","test_anonymous_read","check_for_pii"],
  "test":"Enumerate bucket names from JS/certs/errors; test anonymous LIST/GET. Report exposure class, never download PII.",
  "impact_hint":"High — data exposure."},
 {"id":"CLD-04","name":"Overly permissive IAM role / privilege escalation path","klass":"cloud","_domain":"cloud",
  "requires":["cloud_asset_inventory"],
  "signals":["iam","role","policy","arn","permissions"],
  "questions":["What can the app's runtime role do?","Is there a path from the app role to admin (role chaining, policy gaps)?","Are wildcard actions/resources granted?"],
  "evidence":{"positive":["wildcard_grants","privilege_escalation_path","app_role_overprivileged"],"negative":["least_privilege","no_escalation_path"]},
  "followups":["enumerate_iam","map_escalation_paths"],
  "test":"On owned cloud accounts: enumerate the runtime role's policies; map privilege-escalation paths (iam:PassRole, etc.). Read-only enumeration.",
  "impact_hint":"High — cloud takeover."},
 {"id":"CLD-05","name":"Serverless environment variable / secret exposure","klass":"cloud","_domain":"cloud",
  "requires":["cloud_asset_inventory"],
  "signals":["lambda","serverless","env","function","process.env"],
  "questions":["Do error messages or debug endpoints leak env vars?","Are secrets in env instead of a secret manager?","Can a code-execution primitive read the environment?"],
  "evidence":{"positive":["env_leaked_in_error","secrets_in_env","env_readable"],"negative":["env_redacted","secret_manager_used"]},
  "followups":["trigger_verbose_errors","check_debug_endpoints"],
  "test":"Trigger verbose errors on serverless endpoints; check for env/secret leakage. Inspect deployment configs for plaintext secrets.",
  "impact_hint":"High — secret disclosure."},
 # ---- graphql (thin: 1 -> 3)
 {"id":"GQL-02","name":"GraphQL query batching for brute-force/amplification","klass":"graphql","_domain":"graphql",
  "requires":["graphql_endpoint","introspection_or_schema"],
  "signals":["graphql","batch","query","mutation","login"],
  "questions":["Does the endpoint accept batched queries?","Can batching bypass rate limits on login/OTP mutations?","Is there query cost/depth limiting?"],
  "evidence":{"positive":["batching_accepted","rate_limit_bypassed","no_cost_limit"],"negative":["batching_disabled","per_query_rate_limit","cost_analysis"]},
  "followups":["try_batching","batch_login_attempts","test_depth_limit"],
  "test":"Send batched login/OTP mutations in one request. Measure whether rate limits apply per-batch or per-query. Low volume, owned accounts.",
  "impact_hint":"Medium-High — auth brute-force bypass."},
 {"id":"GQL-03","name":"Persisted query / allowlist bypass","klass":"graphql","_domain":"graphql",
  "requires":["graphql_endpoint"],
  "signals":["graphql","persisted","apq","allowlist","query"],
  "questions":["Does a query allowlist/persisted-query mode actually restrict operations?","Can the hash be bypassed or the allowlist escaped?","Are dangerous mutations excluded from the allowlist?"],
  "evidence":{"positive":["allowlist_bypassed","arbitrary_query_accepted","dangerous_mutation_allowed"],"negative":["allowlist_enforced","arbitrary_rejected"]},
  "followups":["try_arbitrary_query","hash_bypass","enumerate_allowed"],
  "test":"If persisted queries are advertised, try sending arbitrary queries and hash-collision variants. Enumerate which operations the allowlist permits.",
  "impact_hint":"Medium — restriction bypass."},
]

if __name__ == "__main__":
    main()
