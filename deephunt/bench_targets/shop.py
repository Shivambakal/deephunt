"""MOCK-A "shop": BOLA chain — GET /orders/{id} missing object-level authz.

P1: auth bypass -> cross-user order + PII read. The vulnerable variant
checks authentication (anonymous -> 401) but never checks that the
requesting identity OWNS the order. The patched variant enforces
ownership (non-owner -> 403).

Identities: alice (attacker-owned), bob (victim). Orders: 100 (alice),
101 (bob, contains PII).
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from . import MockTarget


class ShopMock(MockTarget):
    name = "shop"
    display = "mock online shop (orders API)"
    _actions = ["get_order", "list_orders", "patch_order", "get_acl"]

    def reset(self):
        self.orders = {
            "100": {"id": "100", "owner": "alice",
                    "email": "alice@example.com", "total": 49.99,
                    "items": ["usb-cable"], "note": ""},
            "101": {"id": "101", "owner": "bob",
                    "email": "bob@example.com", "total": 1299.00,
                    "items": ["laptop-stand", "monitor"],
                    "note": "leave at reception"},
        }

    # ---- probe interface ----
    def probe(self, action: str, params: dict) -> Tuple[int, dict, dict]:
        params = params or {}
        if action == "get_order":
            return self._get_order(params.get("order_id"), params.get("identity"))
        if action == "list_orders":
            return self._list_orders(params.get("identity"))
        if action == "patch_order":
            return self._patch_order(params.get("order_id"),
                                     params.get("identity"), params.get("note", ""))
        if action == "get_acl":
            return self._get_acl(params.get("order_id"))
        return 400, {"error": f"unknown action {action}"}, {}

    def _get_order(self, order_id, identity):
        if identity in (None, "anonymous"):
            return 401, {"error": "unauthorized: authentication required"}, {}
        order = self.orders.get(str(order_id))
        if not order:
            return 404, {"error": "order not found"}, {}
        if self.patched and order["owner"] != identity:
            return 403, {"error": "forbidden: not your order"}, {}
        body = {"order_id": order["id"], "served_to": identity,
                "owned by": order["owner"], "email": order["email"],
                "total": order["total"], "items": order["items"],
                "note": order["note"]}
        return 200, body, {}

    def _list_orders(self, identity):
        if identity in (None, "anonymous"):
            return 401, {"error": "unauthorized"}, {}
        mine = [o["id"] for o in self.orders.values() if o["owner"] == identity]
        return 200, {"identity": identity, "orders": mine}, {}

    def _patch_order(self, order_id, identity, note):
        if identity in (None, "anonymous"):
            return 401, {"error": "unauthorized"}, {}
        order = self.orders.get(str(order_id))
        if not order:
            return 404, {"error": "order not found"}, {}
        if self.patched and order["owner"] != identity:
            return 403, {"error": "forbidden: not your order"}, {}
        order["note"] = note
        return 200, {"order_id": order["id"], "note": note,
                     "served_to": identity}, {"order_id": order["id"],
                                             "field": "note", "by": identity}

    def _get_acl(self, order_id):
        order = self.orders.get(str(order_id))
        if not order:
            return 404, {"error": "order not found"}, {}
        return 200, {"order_id": order["id"], "owner": order["owner"],
                     "shared_with": []}, {}

    # ---- ground truth ----
    def ground_truth(self) -> dict:
        return {
            "vulnerable": not self.patched,
            "technique": "BOLA / IDOR",
            "technique_id": "IDOR-01",
            "location": "GET /orders/{id} missing object-level authorization",
            "impact": "P1: cross-user order read incl. PII (email, items, total)",
            "root_cause": "bola:get_order",
            "oracle": "ownership",
        }

    # ---- world-model seeding ----
    def surface_brief(self) -> str:
        return (
            "Surface: mock online shop orders API. Endpoints: GET /orders/{id} "
            "(auth_required=true), GET /orders (list own), PATCH /orders/{id}. "
            "Identities: alice (attacker-owned test account), bob (victim user). "
            "Objects: order 100 owned by alice, order 101 owned by bob "
            "(contains email + items + total). Trust boundary: user data of "
            "alice must never be visible to bob and vice versa. Open question: "
            "does GET /orders/{id} verify that the caller owns the order, or "
            "only that the caller is authenticated?"
        )

    def seed_world(self, wm):
        wm.add_identity("alice", kind="user", privilege_level=2)
        wm.add_identity("bob", kind="user", privilege_level=2)
        wm.add_identity("anonymous", kind="anon", privilege_level=0)
        wm.add_endpoint("GET", "/orders/{id}", params=["order_id"],
                        auth_state="auth_required", operation_id="get_order")
        wm.add_endpoint("GET", "/orders", auth_state="auth_required",
                        operation_id="list_orders")
        wm.add_endpoint("PATCH", "/orders/{id}", params=["order_id", "note"],
                        auth_state="auth_required", operation_id="patch_order")
        # objects via the documented shape (world_model tracks objects as
        # dicts with owner_role/readers/writers)
        for oid, owner in (("100", "alice"), ("101", "bob")):
            if f"order_{oid}" not in [x["name"] for x in wm.model["objects"]]:
                wm.model["objects"].append(
                    {"name": f"order_{oid}", "owner_role": owner,
                     "readers": [owner], "writers": [owner],
                     "seen_in": "shop surface brief"})
        wm.add_trust_boundary("user-data-isolation", "alice", "bob",
                              mechanism="object ownership check (unverified)")
        wm.add_invariant("Actor B must not read or modify actor A's order.",
                         invariant_id="INV-SHOP-OWN", scope="ownership")

    # ---- hypothesis seeds ----
    def bench_seeds(self) -> List[dict]:
        seeds = [{
            "statement":
                "GET /orders/{id} enforces authentication but performs no "
                "object-ownership check: with two owned accounts, a control vs "
                "variant probe (bob reads own order 101 vs alice reads the "
                "same order 101) will show alice receiving bob's order body "
                "including PII — a BOLA/IDOR P1.",
            "source": "bench:reasoning",
            "score": 4.5,
            "provenance": "bench seed; card IDOR-01 (BOLA); surface brief: "
                           "ownership check unverified",
            "investigator_test":
                "Run the control vs variant pair through the authorized "
                "executor; vulnerable if the variant (alice) gets HTTP 200 "
                "with bob's order content.",
            "violated_assumption":
                "object endpoints verify the caller owns the object",
            "impact": 5, "novelty": 4, "testability": 5,
            "severity": "critical",
            "bench_plan": {
                "setup": [],
                "control": ("get_order", {"order_id": "101", "identity": "bob"}),
                "test": ("get_order", {"order_id": "101", "identity": "alice"}),
                "oracle": "ownership",
                "oracle_ctx": {"owner": "bob"},
                "expected_property":
                    "Actor alice must not read actor bob's order object",
                "technique_id": "IDOR-01",
                "root_cause": "bola:get_order",
                "artifacts": ["request_log", "response_pair"],
                "alternatives": [
                    {"explanation":
                         "the 200 served to alice came from a shared cache, "
                         "not an authorization failure",
                     "disproof": [
                         ("patch_order", {"order_id": "101", "identity": "bob",
                                          "note": "cache-buster-7"}),
                         ("get_order", {"order_id": "101", "identity": "alice"}),
                     ],
                     "kills_if": "cache-buster-7",
                     "killed_note":
                         "after bob wrote a fresh note, alice's re-read "
                         "returned the new note — live read, not a stale cache"},
                    {"explanation":
                         "alice is a collaborator/admin on order 101, so the "
                         "read is authorized",
                     "disproof": [
                         ("get_acl", {"order_id": "101"}),
                     ],
                     "kills_if": '"shared_with": []',
                     "killed_note":
                         "ACL shows owner=bob, shared_with empty — alice has "
                         "no granted access"},
                ],
            },
        }]
        return seeds

    def negative_seeds(self) -> List[dict]:
        # Behaviors that must NOT become findings: anonymous is rejected.
        return [{
            "statement":
                "Anonymous requests to GET /orders/{id} are rejected with "
                "401: single request probe as anonymous vs the owner; the "
                "auth boundary is expected to HOLD (no finding).",
            "source": "bench:negative",
            "score": 2.0,
            "provenance": "bench negative seed; auth boundary sanity check",
            "investigator_test":
                "Probe as anonymous; a 401/403 means the boundary holds and "
                "no finding is emitted.",
            "violated_assumption": "anonymous users can read orders",
            "impact": 2, "novelty": 2, "testability": 5,
            "severity": "low",
            "bench_plan": {
                "setup": [],
                "control": ("get_order", {"order_id": "100", "identity": "alice"}),
                "test": ("get_order", {"order_id": "100", "identity": "anonymous"}),
                "oracle": "auth_boundary",
                "oracle_ctx": {},
                "expected_property":
                    "Anonymous users must not read authenticated orders",
                "technique_id": "AUTH-01",
                "root_cause": "auth_boundary:get_order",
                "artifacts": ["request_log", "response_pair"],
                "alternatives": [],
            },
        }]

    def weak_probes(self) -> List[dict]:
        # Deliberate weak-evidence candidate: claim of BOLA with the
        # response_pair artifact missing -> the verifier's evidence-contract
        # check must REJECT it. Negative control for the verifier.
        return [{
            "claim": "BOLA on GET /orders/{id} (weak evidence probe)",
            "technique_id": "IDOR-01",
            "control_observation": "HTTP 200\naction: get_order\nbody: order 101",
            "test_observation": "HTTP 200\naction: get_order\nbody: order 101 served to alice",
            "artifacts": {"request_log": "get_order x2"},  # response_pair missing
            "alternatives": [],
            "killed_alternatives": {},
            "expected": "REJECTED",
        }]
