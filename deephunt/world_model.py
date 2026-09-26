"""DEEPHUNT world model — capability #1.

The target is not a bag of URLs. It is a SYSTEM:
    identities -> roles -> objects -> states -> services/APIs
                        -> trust boundaries -> security invariants

Built incrementally from passive findings; persisted per target in
state/<target>_world.json. The inference engine (inference.py) and the
inquisitor thinking mode read this model to generate invariant-based
hypotheses — bugs OUTSIDE the explicit vulnerability catalogue.
"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.join(BASE, "state")


class WorldModel:
    def __init__(self, target):
        self.target = target
        self.path = os.path.join(STATE_DIR, f"{target}_world.json")
        self.model = {
            "identities": [],   # {"name","kind": user/service/admin/anon}
            "roles": [],        # {"name","capabilities":[]}
            "objects": [],      # {"name","owner_role","readers":[],"writers":[]}
            "services": [],     # {"host","tech":[],"apis":[]}
            "trust_boundaries": [],  # {"between":[],"mechanism":""}
            "invariants": [],   # {"statement":"","must_hold":True}
        }
        self._load()

    def _load(self):
        if os.path.isfile(self.path):
            try:
                self.model.update(json.load(open(self.path)))
            except (OSError, ValueError):
                pass

    def save(self):
        os.makedirs(STATE_DIR, exist_ok=True)
        json.dump(self.model, open(self.path, "w"), indent=1)

    # ---- construction from findings ----
    def ingest(self, findings):
        """Fold passive findings into the system model."""
        for f in findings:
            tool, title = f.get("tool", ""), f.get("title", "")
            detail = f.get("detail", "") + " " + f.get("evidence", "")
            low = (title + " " + detail).lower()
            if tool == "httpx":
                for line in detail.splitlines():
                    if " x" in line:
                        tech = line.split(" x")[0].strip()
                        self._add_service_tech(title, tech)
            # identity signals
            for kw, ident in (("login", "user"), ("oauth", "user"),
                              ("admin", "admin"), ("api key", "service"),
                              ("anonymous", "anon"), ("guest", "anon")):
                if kw in low and ident not in [
                        i["name"] for i in self.model["identities"]]:
                    self.model["identities"].append(
                        {"name": ident, "kind": ident,
                         "seen_in": title[:80]})
            # object signals: ids in URLs/params imply objects with owners
            for marker in ("user_id", "account_id", "order_id", "doc_id",
                           "file_id", "invoice"):
                if marker in low:
                    self._add_object(marker, title)
        self._derive_invariants()
        self.save()

    def _add_service_tech(self, title, tech):
        host = title.split(" ")[0][:120]
        for s in self.model["services"]:
            if s["host"] == host:
                if tech and tech not in s["tech"]:
                    s["tech"].append(tech)
                return
        self.model["services"].append(
            {"host": host, "tech": [tech] if tech else [], "apis": []})

    def _add_object(self, name, seen_in):
        if name not in [o["name"] for o in self.model["objects"]]:
            self.model["objects"].append(
                {"name": name, "owner_role": "unknown",
                 "readers": [], "writers": [],
                 "seen_in": seen_in[:80]})

    def _derive_invariants(self):
        """Default security invariants every system should hold."""
        defaults = [
            "Only the owner role may modify an owned object.",
            "Authentication state must not leak across trust boundaries.",
            "An object readable by role R must not be enumerable by role < R.",
            "State transitions require the authority the transition claims.",
        ]
        have = {i["statement"] for i in self.model["invariants"]}
        for d in defaults:
            if d not in have:
                self.model["invariants"].append(
                    {"statement": d, "must_hold": True})

    # ---- queries for the inference engine ----
    def open_questions(self):
        """Unknowns in the model = the most valuable experiments."""
        qs = []
        for o in self.model["objects"]:
            if o["owner_role"] == "unknown":
                qs.append(f"Who owns '{o['name']}' and who else can "
                          f"read/write it?")
        if not self.model["trust_boundaries"]:
            qs.append("Where are the trust boundaries? "
                      "What mechanism enforces each?")
        for s in self.model["services"]:
            if not s["apis"]:
                qs.append(f"What APIs does {s['host']} expose, and which "
                          f"require authority?")
        return qs

    def summary(self):
        m = self.model
        return (f"world: {len(m['identities'])} identities, "
                f"{len(m['objects'])} objects, {len(m['services'])} services, "
                f"{len(m['trust_boundaries'])} boundaries, "
                f"{len(m['invariants'])} invariants")
