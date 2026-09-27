"""DEEPHUNT object pool — observed IDs/tokens/objects + lifecycle (blueprint P0-3).

The stateful API engine (apiseq.py) needs live values: the user_id that was
just created, the order_id in state PENDING, the cursor for page 2. This
pool stores them with inferred kinds and lifecycle states, and performs
dependency inference so a parameter named `order_id` automatically pulls
an observed order id.

Secret hygiene: values that look like real credentials (high-entropy
tokens, private keys, passwords) are stored only with sensitive=True and
are NEVER returned by get_for() for request building, and never rendered
by report.py. Test-owned session tokens are fine; the flag is about
accidental capture of real secrets.
"""
from __future__ import annotations

import json
import os
import re
import time
from typing import Dict, List, Optional

BASE = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.join(BASE, "state")

_UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
_INT_ID = re.compile(r"^\d{1,12}$")
_SLUG = re.compile(r"^[a-z0-9][a-z0-9\-_]{2,60}$", re.I)
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_JWT = re.compile(r"^eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$")
_SECRET = re.compile(r"password|passwd|pwd|secret|token|bearer|"
                       r"private[-_]?key|client[-_]?secret|api[-_]?key|"
                       r"aws_|xox[bap]-|ghp_|gho_|sk_live|sk_test", re.I)
_HIGH_ENTROPY = re.compile(r"^[A-Za-z0-9+/=_-]{32,}$")

# param-name -> kind hints for dependency inference
PARAM_KIND_HINTS = [
    (re.compile(r"(^|_)uuid|guid", re.I), "uuid"),
    (re.compile(r"token|jwt|bearer|session", re.I), "token"),
    (re.compile(r"cursor|page_token|next|offset", re.I), "cursor"),
    (re.compile(r"slug|handle|username", re.I), "slug"),
    (re.compile(r"email", re.I), "email"),
    (re.compile(r"(^|_)(id|_id)$|_id$", re.I), "id"),
]


def infer_kind(value: str, param_name: str = "") -> str:
    """Infer the kind of an observed value (value first, param name second)."""
    v = (value or "").strip()
    if not v:
        return "unknown"
    if _JWT.match(v):
        return "token"
    if _UUID.match(v):
        return "uuid"
    if _EMAIL.match(v):
        return "email"
    if _INT_ID.match(v):
        return "id"
    if _SLUG.match(v) and param_name:
        return "slug"
    if param_name:
        for pat, kind in PARAM_KIND_HINTS:
            if pat.search(param_name):
                return kind
    if _SLUG.match(v):
        return "slug"
    return "string"


_SECRET_VALUE_PREFIX = re.compile(r"^(sk_live|sk_test|ghp_|gho_|xox[bap]-|AKIA)", re.I)


def looks_sensitive(value: str, param_name: str = "") -> bool:
    if _SECRET.search(param_name or ""):
        return True
    v = value or ""
    if v.startswith("-----BEGIN"):
        return True
    if _SECRET_VALUE_PREFIX.match(v):
        return True
    if _HIGH_ENTROPY.match(v) and not _UUID.match(v) and not _INT_ID.match(v):
        # high-entropy blobs that are not plain ids/uuids: treat as sensitive
        # unless they are clearly JWT-shaped test tokens (still flagged)
        return True
    return False


class ObjectPool:
    """Per-target pool of observed values with lifecycle states."""

    def __init__(self, target: str):
        self.target = target
        self.path = os.path.join(STATE_DIR, f"{target}_objects.json")
        self.items: Dict[str, Dict] = {}  # fingerprint -> record
        self._load()

    # ---------- persistence ----------
    def _load(self):
        if os.path.isfile(self.path):
            try:
                self.items = json.load(open(self.path))
            except (OSError, ValueError):
                self.items = {}

    def save(self):
        os.makedirs(STATE_DIR, exist_ok=True)
        json.dump(self.items, open(self.path, "w"), indent=1)

    # ---------- observation ----------
    def observe(self, value, param_name: str = "", context: str = "",
                object_type: str = "", state: str = "",
                owner: str = "") -> Dict:
        """Record one observed value. Returns the record."""
        v = str(value or "").strip()
        if not v:
            return {}
        kind = infer_kind(v, param_name)
        sensitive = looks_sensitive(v, param_name)
        fp = f"{kind}:{v[:64]}"
        rec = self.items.get(fp, {
            "kind": kind, "param_name": param_name, "sensitive": sensitive,
            "first_seen": time.time(), "seen_count": 0, "contexts": [],
            "object_type": object_type, "state": state or "unknown",
            "owner": owner, "state_history": [],
        })
        rec["seen_count"] += 1
        rec["last_seen"] = time.time()
        if context and context[:120] not in rec["contexts"]:
            rec["contexts"].append(context[:120])
        if object_type:
            rec["object_type"] = object_type
        if owner:
            rec["owner"] = owner
        # keep the raw value OUT of the record when sensitive; keep a
        # prefix only so the pool stays useful without storing secrets
        rec["value"] = None if sensitive else v
        rec["value_prefix"] = v[:8] if sensitive else v
        self.items[fp] = rec
        return rec

    def observe_many(self, mapping: Dict, context: str = "", **kw):
        for k, v in (mapping or {}).items():
            if isinstance(v, (str, int)):
                self.observe(v, param_name=str(k), context=context, **kw)

    # ---------- lifecycle ----------
    def transition(self, value: str, to_state: str, actor: str = "") -> bool:
        for rec in self.items.values():
            if rec.get("value") == str(value) or rec.get("value_prefix") == str(value)[:8]:
                frm = rec.get("state", "unknown")
                rec["state_history"].append(
                    {"from": frm, "to": to_state, "actor": actor,
                     "ts": time.time()})
                rec["state"] = to_state
                return True
        return False

    # ---------- dependency inference (feeds the API sequencer) ----------
    def get_for(self, param_name: str, kind_hint: str = "",
                exclude_sensitive: bool = True,
                state: str = "") -> Optional[str]:
        """Pick a pool value suitable for a parameter. Dependency inference:
        `order_id` -> an observed id whose context mentions 'order'."""
        pname = (param_name or "").lower()
        cands = []
        for rec in self.items.values():
            if exclude_sensitive and rec.get("sensitive"):
                continue
            if not rec.get("value"):
                continue
            if state and rec.get("state") != state:
                continue
            score = 0
            if kind_hint and rec["kind"] == kind_hint:
                score += 3
            for pat, kind in PARAM_KIND_HINTS:
                if pat.search(pname) and rec["kind"] == kind:
                    score += 3
            # context affinity: param "order_id" matches values seen near "order"
            stem = re.sub(r"_id$", "", pname)
            if stem and any(stem in c.lower() for c in rec["contexts"]):
                score += 2
            if rec["param_name"].lower() == pname:
                score += 4
            if score:
                cands.append((score, rec["seen_count"], rec["value"]))
        if not cands:
            return None
        cands.sort(key=lambda c: (-c[0], -c[1]))
        return cands[0][2]

    def get(self, field: str) -> Optional[str]:
        """apiseq-compatible accessor: latest usable value for a parameter."""
        return self.get_for(field)

    def values_of_kind(self, kind: str, include_sensitive: bool = False) -> List[str]:
        return [r["value"] for r in self.items.values()
                if r["kind"] == kind and r.get("value")
                and (include_sensitive or not r.get("sensitive"))]

    def summary(self) -> Dict:
        by_kind: Dict[str, int] = {}
        for r in self.items.values():
            by_kind[r["kind"]] = by_kind.get(r["kind"], 0) + 1
        return {"target": self.target, "values": len(self.items),
                "by_kind": by_kind,
                "sensitive_held": sum(1 for r in self.items.values()
                                      if r.get("sensitive"))}
