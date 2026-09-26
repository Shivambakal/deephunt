"""DEEPHUNT private benchmark — endgame #10.

A benchmark of vulnerable applications/scenarios the hunter must find AND
prove. Each scenario simulates a target behind a probe API:

    scenario.probe(name, identity) -> observation text

Ground truth is hidden from the hunter: "vuln" or "fp" (intentionally
deceptive false positive). The harness runs DEEPHUNT's real pipeline —
differential testing -> evidence-first validation -> anti-hallucination
gate — and scores:

    TP/FP/TN/FN, precision, recall, time-to-finding, requests used,
    chain completion, reproducibility.

Starter pack: 14 scenarios across IDOR, auth bypass, race, business logic,
SSRF, XSS, priv-esc, API flaws, multi-step chains, state-machine bugs, and
4 deceptive false positives. Extend to 100 by adding Scenario subclasses.
"""
import time


class Scenario:
    name = "base"
    category = "?"
    ground_truth = "fp"          # "vuln" or "fp"
    description = ""

    def probe(self, name, identity="user_a"):
        """Return observation text for a named probe as an identity."""
        raise NotImplementedError

    def probe_pairs(self):
        """Differential pairs: (label, control_probe, variant_probe)."""
        return []

    def evidence_for(self, stage):
        """Evidence the scenario yields at a validation stage."""
        return ""


# ------------------------- vulnerable scenarios -------------------------

class IDOROrder(Scenario):
    name = "idor-order"; category = "idor"; ground_truth = "vuln"
    description = "order_id is guessable; user_b reads user_a's order"

    def probe(self, name, identity="user_a"):
        if name == "own-order":
            return "200 OK body={\"order_id\": 101, \"owner\": \"" + identity + "\", \"total\": 59.99}"
        if name == "other-order":
            oid = 101 if identity == "user_b" else 102
            return f"200 OK body={{\"order_id\": {oid}, \"owner\": \"other-user\", \"total\": 199.99, \"email\": \"victim@example.com\"}}"
        return "404"

    def probe_pairs(self):
        return [("object-x-vs-y",
                 ("own-order", "user_a"), ("other-order", "user_b"))]

    def evidence_for(self, stage):
        return {
            "HYPOTHESIZED": "order_id enumerable; violated assumption: object-level authz enforced",
            "EXPERIMENTED": "control=user_a/own order (owner=user_a); variant=user_b/order 101 (owner=other-user)",
            "REPRODUCED": "variant differs: user_b received other-user order incl. victim@example.com; fresh session repeats",
            "IMPACT_SHOWN": "demonstrated: cross-account PII disclosure (email + order total); assumption: owned test accounts only",
            "RETESTED": "independent re-test with second owned identity pair reproduces; benign alternative (public order page) killed: page requires auth and shows private email",
        }.get(stage, "")


class AuthBypassAdmin(Scenario):
    name = "auth-bypass-admin"; category = "auth-bypass"; ground_truth = "vuln"
    description = "/admin returns 200 for role=user (missing middleware)"

    def probe(self, name, identity="user"):
        if name == "admin-panel":
            return "200 OK body={\"users\": 412, \"admin\": true}" if identity == "user" else "200 OK"
        return "404"

    def probe_pairs(self):
        return [("role-vs-role", ("admin-panel", "user"), ("admin-panel", "admin"))]

    def evidence_for(self, stage):
        return {
            "HYPOTHESIZED": "missing authorization on /admin; assumption: middleware enforced per role",
            "EXPERIMENTED": "control=admin role 200; variant=user role 200 (should be 403)",
            "REPRODUCED": "variant differs from expected: user role sees admin JSON; reproducible across sessions",
            "IMPACT_SHOWN": "demonstrated: low-priv user reads admin user count; assumption: owned accounts; authorization: program scope, owned data only",
            "RETESTED": "re-tested with fresh login; benign alternative (same shared dashboard) killed: body contains admin:true flag",
        }.get(stage, "")


class RaceCoupon(Scenario):
    name = "race-coupon"; category = "race"; ground_truth = "vuln"
    description = "coupon redeemable twice via parallel requests (before/after)"

    def probe(self, name, identity="user_a"):
        if name == "redeem-1":
            return "200 {\"coupon\": \"WELCOME10\", \"uses_left\": 0, \"discount\": 10}"
        if name == "redeem-2-parallel":
            return "200 {\"coupon\": \"WELCOME10\", \"uses_left\": 0, \"discount\": 10} (second parallel request also succeeded)"
        return "404"

    def probe_pairs(self):
        return [("before-vs-after", ("redeem-1", "user_a"), ("redeem-2-parallel", "user_a"))]

    def evidence_for(self, stage):
        return {
            "HYPOTHESIZED": "TOCTOU on coupon redemption; assumption: single-use enforced atomically",
            "EXPERIMENTED": "control=single redeem (uses_left 0); variant=two parallel redeems both 200",
            "REPRODUCED": "variant differs: discount applied twice; reproduced 3/5 parallel attempts",
            "IMPACT_SHOWN": "demonstrated: double discount = financial impact; assumption: test coupon on owned account; authorization recorded",
            "RETESTED": "re-tested after 60s; benign alternative (idempotent retry) killed: two distinct order ids created",
        }.get(stage, "")


class PriceLogic(Scenario):
    name = "price-logic"; category = "business-logic"; ground_truth = "vuln"
    description = "negative quantity yields account credit"

    def probe(self, name, identity="user_a"):
        if name == "buy-1":
            return "200 {\"qty\": 1, \"charged\": 49.99}"
        if name == "buy-minus-1":
            return "200 {\"qty\": -1, \"charged\": -49.99, \"balance\": \"+49.99 credit\"}"
        return "404"

    def probe_pairs(self):
        return [("request-vs-modified", ("buy-1", "user_a"), ("buy-minus-1", "user_a"))]

    def evidence_for(self, stage):
        return {
            "HYPOTHESIZED": "missing server-side quantity validation; assumption: qty > 0 enforced",
            "EXPERIMENTED": "control qty=1 charged 49.99; variant qty=-1 credited 49.99",
            "REPRODUCED": "variant differs: negative charge reproducible",
            "IMPACT_SHOWN": "demonstrated: arbitrary account credit = direct financial impact; assumption: owned account; authorization: scope allows purchase flow tests",
            "RETESTED": "re-tested with qty=-2 (credit 99.98); benign alternative (display bug) killed: balance endpoint reflects credit",
        }.get(stage, "")


class SSRFMetadata(Scenario):
    name = "ssrf-metadata"; category = "ssrf"; ground_truth = "vuln"
    description = "url param fetches cloud metadata"

    def probe(self, name, identity="user_a"):
        if name == "fetch-own":
            return "200 fetched https://example.com/logo.png (12KB image)"
        if name == "fetch-meta":
            return "200 fetched http://169.254.169.254/latest/meta-data/iam/security-credentials/ -> {\"AccessKeyId\": \"AKIA...\"}"
        return "404"

    def probe_pairs(self):
        return [("request-vs-modified", ("fetch-own", "user_a"), ("fetch-meta", "user_a"))]

    def evidence_for(self, stage):
        return {
            "HYPOTHESIZED": "SSRF via url param; assumption: egress allowlisted",
            "EXPERIMENTED": "control fetches public image; variant fetches 169.254.169.254 and returns IAM creds",
            "REPRODUCED": "variant differs: metadata returned; reproducible",
            "IMPACT_SHOWN": "demonstrated: cloud credential disclosure = full infra compromise path; assumption: lab target only; authorization: isolated lab scope",
            "RETESTED": "re-tested with DNS variant; benign alternative (mock response) killed: creds have valid AKIA format and STS validates in lab",
        }.get(stage, "")


class ReflectedXSS(Scenario):
    name = "reflected-xss"; category = "xss"; ground_truth = "vuln"
    description = "q reflected unescaped"

    def probe(self, name, identity="user_a"):
        if name == "search-clean":
            return "200 body=results for <b>shoes</b>"
        if name == "search-xss":
            return "200 body=results for <script>alert(1)</script>"
        return "404"

    def probe_pairs(self):
        return [("request-vs-modified", ("search-clean", "user_a"), ("search-xss", "user_a"))]

    def evidence_for(self, stage):
        return {
            "HYPOTHESIZED": "reflected XSS in q; assumption: output encoded",
            "EXPERIMENTED": "control reflected with <b> encoded; variant <script> raw",
            "REPRODUCED": "variant differs: script tags unescaped, reproducible",
            "IMPACT_SHOWN": "demonstrated: arbitrary JS execution in victim session; assumption: no stored PII in PoC; authorization: scope allows XSS probes",
            "RETESTED": "re-tested with event-handler vector; benign alternative (client-side only render) killed: payload present in raw HTML source",
        }.get(stage, "")


class PrivEscParam(Scenario):
    name = "privesc-param"; category = "priv-esc"; ground_truth = "vuln"
    description = "role=user can self-promote via role=admin param"

    def probe(self, name, identity="user"):
        if name == "profile":
            return "200 {\"role\": \"user\"}"
        if name == "profile-promote":
            return "200 {\"role\": \"admin\", \"admin_panel\": true}" if identity == "user" else "200 {\"role\": \"admin\"}"
        return "404"

    def probe_pairs(self):
        return [("request-vs-modified", ("profile", "user"), ("profile-promote", "user"))]

    def evidence_for(self, stage):
        return {
            "HYPOTHESIZED": "mass-assignment on role; assumption: role server-controlled",
            "EXPERIMENTED": "control role=user; variant role=admin param -> role=admin",
            "REPRODUCED": "variant differs: promotion persists across requests",
            "IMPACT_SHOWN": "demonstrated: user->admin escalation, admin panel visible; assumption: owned account; authorization: program scope",
            "RETESTED": "re-tested after logout/login (role persists); benign alternative (UI-only label) killed: /admin returns 200 after promotion",
        }.get(stage, "")


class APIv1v2(Scenario):
    name = "api-v1-v2"; category = "api-flaw"; ground_truth = "vuln"
    description = "v2 dropped the auth check v1 had"

    def probe(self, name, identity="anon"):
        if name == "v1-users":
            return "401 unauthorized"
        if name == "v2-users":
            return "200 [{\"id\":1,\"email\":\"a@x.com\"},{\"id\":2,\"email\":\"b@x.com\"}]"
        return "404"

    def probe_pairs(self):
        return [("v1-vs-v2", ("v1-users", "anon"), ("v2-users", "anon"))]

    def evidence_for(self, stage):
        return {
            "HYPOTHESIZED": "v2 missing auth; assumption: version parity on authz",
            "EXPERIMENTED": "control v1 401; variant v2 200 with user list",
            "REPRODUCED": "variant differs: reproducible",
            "IMPACT_SHOWN": "demonstrated: unauthenticated user enumeration; assumption: lab data; authorization: passive + owned scope",
            "RETESTED": "re-tested from fresh IP; benign alternative (public directory) killed: v1 401 proves non-public intent",
        }.get(stage, "")


class ResetChain(Scenario):
    name = "reset-chain"; category = "chain"; ground_truth = "vuln"
    description = "reset token in Referer -> token reuse -> account takeover (2 links)"

    def probe(self, name, identity="attacker"):
        if name == "reset-request":
            return "200 reset link sent; Referer log shows /reset?token=abc123"
        if name == "reset-reuse":
            return "200 password changed for victim@example.com with token=abc123 (no expiry)"
        return "404"

    def probe_pairs(self):
        return [("before-vs-after", ("reset-request", "attacker"), ("reset-reuse", "attacker"))]

    def evidence_for(self, stage):
        return {
            "HYPOTHESIZED": "chain: token leak via Referer + no single-use; assumption: tokens single-use and secret",
            "EXPERIMENTED": "link1: token visible in Referer; link2: same token changes victim password",
            "REPRODUCED": "both links reproduce; chain completes end-to-end",
            "IMPACT_SHOWN": "demonstrated: full account takeover of victim@example.com; assumption: lab accounts; authorization: isolated lab",
            "RETESTED": "re-ran full chain with fresh victim; benign alternative (token bound to session) killed: reuse worked cross-session",
        }.get(stage, "")


class StateMachine(Scenario):
    name = "state-machine"; category = "state-machine"; ground_truth = "vuln"
    description = "paid -> refunded -> paid again (invalid transition)"

    def probe(self, name, identity="user_a"):
        if name == "order-paid":
            return "200 {\"order\": 7, \"state\": \"paid\"}"
        if name == "order-refund-repay":
            return "200 {\"order\": 7, \"state\": \"paid\", \"refunds\": 1, \"charged\": 2x}"
        return "404"

    def probe_pairs(self):
        return [("before-vs-after", ("order-paid", "user_a"), ("order-refund-repay", "user_a"))]

    def evidence_for(self, stage):
        return {
            "HYPOTHESIZED": "invalid state transition accepted; assumption: refunded is terminal",
            "EXPERIMENTED": "control paid once; variant refund-then-repay accepted, charged twice, one refund",
            "REPRODUCED": "variant differs: reproducible",
            "IMPACT_SHOWN": "demonstrated: double-charge with refund = money movement anomaly; assumption: owned card test mode; authorization: scope",
            "RETESTED": "re-tested; benign alternative (idempotent webhook) killed: ledger shows 2 charges 1 refund",
        }.get(stage, "")


# --------------------- deceptive false positives ---------------------

class FPCache(Scenario):
    name = "fp-cache"; category = "deceptive"; ground_truth = "fp"
    description = "bodies differ only by timestamp — looks interesting, is noise"

    def probe(self, name, identity="user_a"):
        if name == "page-a":
            return "200 body={\"data\": \"same\", \"ts\": \"2026-09-27T01:00:01\"}"
        if name == "page-b":
            return "200 body={\"data\": \"same\", \"ts\": \"2026-09-27T01:00:07\"}"
        return "404"

    def probe_pairs(self):
        return [("user-a-vs-b", ("page-a", "user_a"), ("page-b", "user_b"))]

    def evidence_for(self, stage):
        return {
            "HYPOTHESIZED": "maybe user_b sees different data",
            "EXPERIMENTED": "control vs variant differ",
            "REPRODUCED": "",
            "IMPACT_SHOWN": "",
            "RETESTED": "",
        }.get(stage, "")


class FPPublic(Scenario):
    name = "fp-public"; category = "deceptive"; ground_truth = "fp"
    description = "/public/docs 200 for anon — intended public, not a leak"

    def probe(self, name, identity="anon"):
        if name == "docs":
            return "200 body={\"docs\": \"public api reference\"}"
        return "404"

    def probe_pairs(self):
        return [("auth-vs-anon", ("docs", "anon"), ("docs", "user_a"))]

    def evidence_for(self, stage):
        return {
            "HYPOTHESIZED": "anon can read docs — info disclosure?",
            "EXPERIMENTED": "both 200, identical",
            "REPRODUCED": "identical — no difference to explain",
            "IMPACT_SHOWN": "",
            "RETESTED": "",
        }.get(stage, "")


class FPVerbose(Scenario):
    name = "fp-verbose"; category = "deceptive"; ground_truth = "fp"
    description = "verbose errors, zero data — scary stack traces, no leak"

    def probe(self, name, identity="user_a"):
        if name == "err":
            return "500 StackTrace: NullPointer at com.app.Controller (no user data in trace)"
        return "404"

    def probe_pairs(self):
        return [("request-vs-modified", ("err", "user_a"), ("err", "user_a"))]

    def evidence_for(self, stage):
        return {
            "HYPOTHESIZED": "verbose errors leak internals?",
            "EXPERIMENTED": "stack trace present but contains no PII, paths, or secrets",
            "REPRODUCED": "",
            "IMPACT_SHOWN": "",
            "RETESTED": "",
        }.get(stage, "")


class FPOwnData(Scenario):
    name = "fp-own-data"; category = "deceptive"; ground_truth = "fp"
    description = "user sees own record via id= — looks like IDOR, is correct authz"

    def probe(self, name, identity="user_a"):
        if name == "my-record":
            return "200 {\"id\": \"user_a\", \"owner\": \"user_a\"}"
        if name == "other-record":
            return "403 forbidden"
        return "404"

    def probe_pairs(self):
        return [("object-x-vs-y", ("my-record", "user_a"), ("other-record", "user_a"))]

    def evidence_for(self, stage):
        return {
            "HYPOTHESIZED": "id param — IDOR?",
            "EXPERIMENTED": "control 200 own; variant 403 other — boundary holds",
            "REPRODUCED": "boundary holds consistently; benign explanation CONFIRMED: correct authorization",
            "IMPACT_SHOWN": "",
            "RETESTED": "",
        }.get(stage, "")


ALL = [IDOROrder, AuthBypassAdmin, RaceCoupon, PriceLogic, SSRFMetadata,
       ReflectedXSS, PrivEscParam, APIv1v2, ResetChain, StateMachine,
       FPCache, FPPublic, FPVerbose, FPOwnData]
