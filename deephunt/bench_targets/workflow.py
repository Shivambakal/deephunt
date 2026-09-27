"""MOCK-B "workflow": multi-step business-logic abuse.

Order lifecycle: CREATED -> APPROVED -> PAID -> FULFILLED. The planted bug:
pay_order() accepts orders still in CREATED state, so an attacker can skip
the manager approval step and drive an order straight to unpaid fulfillment.
P1: workflow bypass -> unpaid fulfillment.

Patched variant: pay_order requires APPROVED (else 400 invalid transition).

Identities: alice (attacker-owned buyer), carol (manager).
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from . import MockTarget

STATES = ["CREATED", "APPROVED", "PAID", "FULFILLED"]


class WorkflowMock(MockTarget):
    name = "workflow"
    display = "mock order workflow (create/approve/pay/fulfill)"
    _actions = ["create_order", "approve_order", "pay_order",
                "fulfill_order", "get_order", "get_policy"]

    def reset(self):
        self.orders = {}
        self._next = 1

    # ---- probe interface ----
    def probe(self, action: str, params: dict) -> Tuple[int, dict, dict]:
        params = params or {}
        if action == "create_order":
            return self._create(params.get("identity"))
        if action == "approve_order":
            return self._approve(params.get("order_id"),
                                 params.get("identity"), params.get("role"))
        if action == "pay_order":
            return self._pay(params.get("order_id"), params.get("identity"))
        if action == "fulfill_order":
            return self._fulfill(params.get("order_id"), params.get("identity"))
        if action == "get_order":
            return self._get(params.get("order_id"))
        if action == "get_policy":
            return 200, {"policy": "all orders require manager approval "
                                   "before payment; no exceptions for "
                                   "order value"}, {}
        return 400, {"error": f"unknown action {action}"}, {}

    def _create(self, identity):
        if identity in (None, "anonymous"):
            return 401, {"error": "unauthorized"}, {}
        oid = f"ORD-{self._next}"
        self._next += 1
        self.orders[oid] = {"order_id": oid, "buyer": identity,
                            "state": "CREATED", "approvals": []}
        return 201, {"order_id": oid, "state": "CREATED",
                     "buyer": identity}, {"order_id": oid,
                                          "to": "CREATED", "by": identity}

    def _approve(self, order_id, identity, role):
        o = self.orders.get(str(order_id))
        if not o:
            return 404, {"error": "order not found"}, {}
        if role != "manager":
            return 403, {"error": "forbidden: manager role required "
                                  "for approval"}, {}
        frm = o["state"]
        o["state"] = "APPROVED"
        o["approvals"].append({"by": identity, "role": role})
        return 200, {"order_id": o["order_id"], "state": "APPROVED",
                     "approvals": o["approvals"]}, {"order_id": o["order_id"],
                                                    "from": frm, "to": "APPROVED",
                                                    "by": identity}

    def _pay(self, order_id, identity):
        o = self.orders.get(str(order_id))
        if not o:
            return 404, {"error": "order not found"}, {}
        if self.patched and o["state"] != "APPROVED":
            return 400, {"error": "invalid transition: order must be "
                                  "APPROVED before payment",
                         "state": o["state"]}, {}
        frm = o["state"]
        o["state"] = "PAID"
        return 200, {"order_id": o["order_id"], "state": "PAID",
                     "paid_from": frm}, {"order_id": o["order_id"],
                                         "from": frm, "to": "PAID",
                                         "by": identity}

    def _fulfill(self, order_id, identity):
        o = self.orders.get(str(order_id))
        if not o:
            return 404, {"error": "order not found"}, {}
        if o["state"] != "PAID":
            return 400, {"error": "invalid transition: order must be "
                                  "PAID before fulfillment",
                         "state": o["state"]}, {}
        o["state"] = "FULFILLED"
        return 200, {"order_id": o["order_id"], "state": "FULFILLED"}, \
            {"order_id": o["order_id"], "from": "PAID",
             "to": "FULFILLED", "by": identity}

    def _get(self, order_id):
        o = self.orders.get(str(order_id))
        if not o:
            return 404, {"error": "order not found"}, {}
        return 200, {"order_id": o["order_id"], "state": o["state"],
                     "buyer": o["buyer"], "approvals": o["approvals"]}, {}

    # ---- ground truth ----
    def ground_truth(self) -> dict:
        return {
            "vulnerable": not self.patched,
            "technique": "workflow / state-machine bypass (skipped approval)",
            "technique_id": "WF-01",
            "location": "pay_order() missing state precondition "
                        "(accepts CREATED, requires APPROVED)",
            "impact": "P1: attacker drives orders to fulfillment without "
                      "manager approval / without valid payment authorization",
            "root_cause": "workflow:pay_order",
            "oracle": "state_transition",
        }

    # ---- world-model seeding ----
    def surface_brief(self) -> str:
        return (
            "Surface: mock order workflow. Lifecycle CREATED -> APPROVED -> "
            "PAID -> FULFILLED. Actions: create_order (buyer), approve_order "
            "(manager role only), pay_order (buyer), fulfill_order. Policy: "
            "all orders require manager approval before payment. Identities: "
            "alice (attacker-owned buyer), carol (manager). Trust boundary: "
            "the approval step gates payment; skipping it must be rejected. "
            "Open question: does pay_order verify the order is APPROVED, or "
            "does it accept any non-terminal state?"
        )

    def seed_world(self, wm):
        wm.add_identity("alice", kind="user", privilege_level=2)
        wm.add_identity("carol", kind="user", privilege_level=2,
                       roles=["manager"])
        wm.add_endpoint("POST", "/orders", auth_state="auth_required",
                        operation_id="create_order")
        wm.add_endpoint("POST", "/orders/{id}/approve",
                        params=["order_id"], auth_state="auth_required",
                        operation_id="approve_order")
        wm.add_endpoint("POST", "/orders/{id}/pay", params=["order_id"],
                        auth_state="auth_required", operation_id="pay_order")
        wm.add_endpoint("POST", "/orders/{id}/fulfill", params=["order_id"],
                        auth_state="auth_required",
                        operation_id="fulfill_order")
        wm.set_object_lifecycle("order", STATES, current="CREATED")
        wm.add_trust_boundary("approval-gate", "buyer", "payment",
                              mechanism="manager approval (unverified)")
        wm.add_invariant("An order may move to PAID only from APPROVED.",
                         invariant_id="INV-WF-STATE", scope="state_transition")

    # ---- hypothesis seeds ----
    def bench_seeds(self) -> List[dict]:
        return [{
            "statement":
                "pay_order() does not verify the order is APPROVED: a "
                "multi-step control vs variant probe (valid "
                "create->approve->pay->fulfill chain vs create->pay->fulfill "
                "with the approval step skipped) will show the skipped chain "
                "reaching FULFILLED — a workflow-bypass P1.",
            "source": "bench:reasoning",
            "score": 4.5,
            "provenance": "bench seed; card WF-01 (state-machine bypass); "
                           "surface brief: pay precondition unverified",
            "investigator_test":
                "Drive both chains through the authorized executor; "
                "vulnerable if the approval-skipped chain reaches PAID and "
                "FULFILLED with HTTP 200 at each step.",
            "violated_assumption":
                "state transitions enforce their preconditions",
            "impact": 5, "novelty": 4, "testability": 5,
            "severity": "critical",
            "bench_plan": {
                "setup": [],
                "control_chain": [
                    ("create_order", {"identity": "alice"}),
                    ("approve_order", {"order_id": "$chain.0.order_id",
                                       "identity": "carol", "role": "manager"}),
                    ("pay_order", {"order_id": "$chain.0.order_id",
                                   "identity": "alice"}),
                    ("fulfill_order", {"order_id": "$chain.0.order_id",
                                       "identity": "alice"}),
                ],
                "test_chain": [
                    ("create_order", {"identity": "alice"}),
                    ("pay_order", {"order_id": "$chain.0.order_id",
                                   "identity": "alice"}),
                    ("fulfill_order", {"order_id": "$chain.0.order_id",
                                       "identity": "alice"}),
                ],
                "oracle": "state_transition",
                "oracle_ctx": {"attempted_transition":
                               "CREATED->PAID skipping APPROVED"},
                "expected_property":
                    "pay_order must reject orders that are not APPROVED",
                "technique_id": "WF-01",
                "root_cause": "workflow:pay_order",
                "artifacts": ["request_log", "response_pair", "state_trace"],
                "alternatives": [
                    {"explanation":
                         "the pay step was actually rejected (400 invalid "
                         "transition) — no bypass occurred",
                     "disproof": [],
                     "kills_if": '"to": "PAID"',
                     "killed_note":
                         "the pay step's state delta shows the order moved "
                         "to PAID — the transition was accepted, not rejected",
                     "self_evident": True},
                    {"explanation":
                         "a background job auto-approved the test order "
                         "between create and pay",
                     "disproof": [
                         ("get_order", {"order_id": "$chain.0.order_id"}),
                     ],
                     "kills_if": '"approvals": []',
                     "killed_note":
                         "order record shows approvals empty — no approval "
                         "ever happened, background or otherwise",
                     "chain_ref": "test_chain"},
                    {"explanation":
                         "low-value orders are exempt from approval by design",
                     "disproof": [("get_policy", {})],
                     "kills_if": "no exceptions",
                     "killed_note":
                         "published policy states approval is required with "
                         "no exceptions for order value"},
                ],
            },
        }]

    def negative_seeds(self) -> List[dict]:
        # Non-manager approval attempts must be rejected (boundary holds).
        return [{
            "statement":
                "approve_order() requires the manager role: single request "
                "probe with alice as non-manager vs carol as manager; the "
                "non-manager attempt is expected to be rejected (no finding).",
            "source": "bench:negative",
            "score": 2.0,
            "provenance": "bench negative seed; role boundary sanity check",
            "investigator_test":
                "Probe approval as non-manager; 403 means the boundary holds.",
            "violated_assumption": "any buyer can approve orders",
            "impact": 2, "novelty": 2, "testability": 5,
            "severity": "low",
            "bench_plan": {
                "setup": [("create_order", {"identity": "alice"})],
                "control": ("approve_order",
                            {"order_id": "$setup.0.order_id",
                             "identity": "carol", "role": "manager"}),
                "test": ("approve_order",
                         {"order_id": "$setup.0.order_id",
                          "identity": "alice", "role": "buyer"}),
                "oracle": "state_transition",
                "oracle_ctx": {"attempted_transition":
                               "CREATED->APPROVED by non-manager"},
                "expected_property":
                    "only the manager role may approve orders",
                "technique_id": "AUTH-01",
                "root_cause": "authz:approve_order",
                "artifacts": ["request_log", "response_pair"],
                "alternatives": [],
            },
        }]

    def weak_probes(self) -> List[dict]:
        return [{
            "claim": "workflow bypass in pay_order (weak evidence probe)",
            "technique_id": "WF-01",
            "control_observation": "HTTP 200\nchain: create->approve->pay->fulfill",
            "test_observation": "HTTP 200\nchain: create->pay->fulfill",
            "artifacts": {"request_log": "chain x2"},  # response_pair + state_trace missing
            "alternatives": [],
            "killed_alternatives": {},
            "expected": "REJECTED",
        }]
