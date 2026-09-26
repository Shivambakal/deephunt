"""DEEPHUNT dynamic world model — update #1.

The old model was built once per run from passive findings and then sat
still. This one is a living belief state:

    OBSERVE -> infer entities/relations -> update beliefs -> recalculate

Every experiment result flows back through update_from_observation(), which
extracts entities, relations, permissions, state transitions and trust
boundaries from raw observation text, then recalculates confidence in each
security invariant. The model is what the planner, debate, and synthesizer
all read — never a stale snapshot.
"""
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.join(BASE, "state")

_EP = re.compile(r"(?:^|[\s\"'(\[])(/[a-zA-Z0-9_\-./{}]+)")
_PARAM = re.compile(r"[?&]([a-zA-Z_][a-zA-Z0-9_\-]{1,40})=")
_STATUS = re.compile(r"\b([1-5][0-9]{2})\b")
_ROLE = re.compile(r"\b(admin|owner|member|guest|anonymous|service|system)\b", re.I)


class WorldModel:
    def __init__(self, target):
        self.target = target
        self.path = os.path.join(STATE_DIR, f"{target}_world.json")
        self.model = {
            "identities": [], "roles": [], "objects": [], "services": [],
            "trust_boundaries": [], "invariants": [],
            # --- dynamic layer (update #1) ---
            "relations": [],      # {frm, to, kind}
            "transitions": [],    # {object, frm_state, to_state, actor}
            "beliefs": {},        # invariant -> {confidence, supporting, contradicting}
            "anomalies": [],      # observations matching nothing known
        }
        self._load()

    def _load(self):
        if os.path.isfile(self.path):
            try:
                saved = json.load(open(self.path))
                self.model.update(saved)
            except (OSError, ValueError):
                pass

    def save(self):
        os.makedirs(STATE_DIR, exist_ok=True)
        json.dump(self.model, open(self.path, "w"), indent=1)

    # ---------- construction ----------
    def ingest(self, findings):
        for f in findings:
            tool, title = f.get("tool", ""), f.get("title", "")
            detail = f.get("detail", "") + " " + f.get("evidence", "")
            low = (title + " " + detail).lower()
            if tool == "httpx":
                for line in detail.splitlines():
                    if " x" in line:
                        self._add_service_tech(title, line.split(" x")[0].strip())
            for kw, ident in (("login", "user"), ("oauth", "user"),
                              ("admin", "admin"), ("api key", "service"),
                              ("anonymous", "anon"), ("guest", "anon")):
                if kw in low and ident not in [i["name"] for i in self.model["identities"]]:
                    self.model["identities"].append(
                        {"name": ident, "kind": ident, "seen_in": title[:80]})
            for marker in ("user_id", "account_id", "order_id", "doc_id",
                           "file_id", "invoice"):
                if marker in low:
                    self._add_object(marker, title)
            self.update_from_observation(detail, source=tool or "ingest")
        self._derive_invariants()
        self.recalculate_beliefs()
        self.save()
        # data-first: keep the structured target model in sync with the world model
        try:
            from target_model import Target
            Target.build_from_world_model(self)
        except Exception:
            pass

    def _add_service_tech(self, title, tech):
        host = title.split(" ")[0][:120]
        for s in self.model["services"]:
            if s["host"] == host:
                if tech and tech not in s["tech"]:
                    s["tech"].append(tech)
                return
        self.model["services"].append({"host": host, "tech": [tech] if tech else [], "apis": []})

    def _add_object(self, name, seen_in):
        if name not in [o["name"] for o in self.model["objects"]]:
            self.model["objects"].append({"name": name, "owner_role": "unknown",
                                          "readers": [], "writers": [],
                                          "seen_in": seen_in[:80]})

    def _derive_invariants(self):
        defaults = [
            "Only the owner role may modify an owned object.",
            "Authentication state must not leak across trust boundaries.",
            "An object readable by role R must not be enumerable by role < R.",
            "State transitions require the authority the transition claims.",
        ]
        have = {i["statement"] for i in self.model["invariants"]}
        for d in defaults:
            if d not in have:
                self.model["invariants"].append({"statement": d, "must_hold": True})
                self.model["beliefs"].setdefault(d, {"confidence": 0.5,
                                                     "supporting": 0, "contradicting": 0})

    # ---------- dynamic update (the active learning loop feeds this) ----------
    def update_from_observation(self, text, source="experiment"):
        """Fold one observation into entities, relations, permissions,
        transitions, and invariant beliefs. Called after EVERY experiment.
        Accepts free text OR a structured ExperimentObservation dict
        (see observation.py)."""
        if isinstance(text, dict):
            return self._update_from_record(text, source)
        if not text:
            return {"entities": 0, "relations": 0}
        added_e, added_r = 0, 0
        endpoints = {m.group(1) for m in _EP.finditer(text)} - {"/"}
        params = {m.group(1) for m in _PARAM.finditer(text)}
        roles = {m.group(1).lower() for m in _ROLE.finditer(text)}

        for ep in list(endpoints)[:20]:
            if self._add_relation("internet", ep, "exposes"):
                added_r += 1
            added_e += 1
        for p in list(params)[:20]:
            for ep in list(endpoints)[:5]:
                if self._add_relation(ep, p, "accepts-param"):
                    added_r += 1
            added_e += 1
        for r in roles:
            if r not in [x["name"] for x in self.model["roles"]]:
                self.model["roles"].append({"name": r, "capabilities": []})
                added_e += 1

        # permission signals: "X can read/write Y", "403", "401"
        low = text.lower()
        for verb, kind in (("can read", "reads"), ("can write", "writes"),
                           ("can modify", "writes"), ("can delete", "deletes")):
            if verb in low:
                for o in self.model["objects"]:
                    if o["name"] in low and self._add_relation("actor", o["name"], kind):
                        added_r += 1
        # denial signals support the invariants (boundary held)
        if "403" in text or "401" in text or "forbidden" in low or "denied" in low:
            self._belief_vote("Only the owner role may modify an owned object.", +1)
            self._belief_vote("An object readable by role R must not be enumerable by role < R.", +1)
        # disclosure signals contradict them (boundary may have failed)
        if any(k in low for k in ("leaked", "disclosed", "unauthorized", "bypassed", "escalat")):
            self._belief_vote("Only the owner role may modify an owned object.", -1)
            self._belief_vote("Authentication state must not leak across trust boundaries.", -1)

        # state transitions: "moved from X to Y", "changed ... to ..."
        tm = re.search(r"(?:moved|changed|transitioned|updated)\s+(?:from\s+)?(\w+)\s+to\s+(\w+)", low)
        if tm:
            self.model["transitions"].append({"frm_state": tm.group(1),
                                              "to_state": tm.group(2),
                                              "actor": source})
        self.recalculate_beliefs()
        return {"entities": added_e, "relations": added_r}

    def _update_from_record(self, rec, source="experiment"):
        """Fold a structured ExperimentObservation dict into the model."""
        parts = [rec.get("hypothesis", ""), rec.get("interpretation", ""),
                 rec.get("next_question", "")]
        blob = " ".join(p for p in parts if p)
        result = self.update_from_observation(blob, source=source)
        # preconditions carry identity/object_owner semantics
        pre = rec.get("preconditions") or {}
        ident, owner = pre.get("identity"), pre.get("object_owner")
        if ident and ident not in [i["name"] for i in self.model["identities"]]:
            self.model["identities"].append({"name": ident, "kind": "test",
                                             "seen_in": rec.get("experiment_id", "")})
            result["entities"] = result.get("entities", 0) + 1
        if ident and owner and ident != owner:
            self._add_relation(ident, owner, "tested-against")
            result["relations"] = result.get("relations", 0) + 1
        # observation flags drive belief votes
        obs = rec.get("observation") or {}
        if obs.get("object_changed") and ident and owner and ident != owner:
            self._belief_vote("Only the owner role may modify an owned object.", -1)
        if obs.get("status_changed") and not obs.get("object_changed"):
            self._belief_vote("Only the owner role may modify an owned object.", +1)
        conf = rec.get("confidence")
        self.recalculate_beliefs()
        self.save()
        return result

    def _add_relation(self, frm, to, kind):
        rel = {"frm": frm[:120], "to": to[:120], "kind": kind}
        if rel not in self.model["relations"]:
            self.model["relations"].append(rel)
            return True
        return False

    def _belief_vote(self, invariant, delta):
        b = self.model["beliefs"].setdefault(invariant, {"confidence": 0.5,
                                                         "supporting": 0, "contradicting": 0})
        if delta > 0:
            b["supporting"] += 1
        else:
            b["contradicting"] += 1

    def recalculate_beliefs(self):
        """Confidence in each invariant from evidence so far."""
        for inv, b in self.model["beliefs"].items():
            s, c = b["supporting"], b["contradicting"]
            b["confidence"] = round((s + 1) / (s + c + 2), 3)

    def weakest_invariant(self):
        """The invariant with the lowest confidence — the best place to probe."""
        if not self.model["beliefs"]:
            return None, 0.5
        inv = min(self.model["beliefs"], key=lambda k: self.model["beliefs"][k]["confidence"])
        return inv, self.model["beliefs"][inv]["confidence"]

    def record_anomaly(self, text):
        """An observation matching nothing known — fuel for the novel generator."""
        if text and text not in self.model["anomalies"]:
            self.model["anomalies"].append(text[:300])
            return True
        return False

    # ---------- queries ----------
    def open_questions(self):
        qs = []
        for o in self.model["objects"]:
            if o["owner_role"] == "unknown":
                qs.append(f"Who owns '{o['name']}' and who else can read/write it?")
        if not self.model["trust_boundaries"]:
            qs.append("Where are the trust boundaries? What mechanism enforces each?")
        for s in self.model["services"]:
            if not s["apis"]:
                qs.append(f"What APIs does {s['host']} expose, and which require authority?")
        inv, conf = self.weakest_invariant()
        if inv and conf < 0.6:
            qs.append(f"Weakest belief (conf {conf}): '{inv}' — probe it next.")
        return qs

    def summary(self):
        m = self.model
        return (f"world: {len(m['identities'])} identities, {len(m['objects'])} objects, "
                f"{len(m['services'])} services, {len(m['relations'])} relations, "
                f"{len(m['transitions'])} transitions, {len(m['anomalies'])} anomalies")
