"""DEEPHUNT target model — structured knowledge about ONE authorized target.

Not a URL list: a semantic model of what the target IS —
assets, endpoints (with meaning), identities, roles, workflows, parameters,
API specs, frontend routes, and observations.

Persisted per-target at state/<target>/target.json.

The model powers:
  authz_matrix()   -> ROLE x OBJECT x ACTION x STATE table (drives BOLA/FLA testing)
  workflow_gaps()  -> missing/invalid/unexpected/repeated transitions vs observed
  authz_questions()-> prioritized authorization questions from the matrix
  workflow_anomalies() -> observed transitions that violate the declared workflow
"""
from __future__ import annotations
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.join(BASE, "state")


class Target:
    def __init__(self, name):
        self.name = name
        self.path = os.path.join(STATE_DIR, name, "target.json")
        self.data = {
            "assets": [],          # {"host","kind","notes"}
            "endpoints": [],       # semantic endpoint records (see add_endpoint)
            "technologies": [],    # {"name","evidence"}
            "identities": [],      # {"name","role","owns":[]}
            "roles": [],           # {"name","capabilities":[]}
            "workflows": [],       # {"name","states":[],"transitions":[[a,b],..]}
            "parameters": [],      # {"name","seen_in","user_controlled":bool}
            "api_specs": [],       # {"url","kind"}
            "frontend_routes": [], # {"route","component_hint"}
            "observations": [],    # free-form observation strings
        }
        self._load()

    # ---------- persistence ----------
    def _load(self):
        if os.path.isfile(self.path):
            try:
                saved = json.load(open(self.path))
                if isinstance(saved, dict):
                    self.data.update(saved)
            except (OSError, ValueError):
                pass

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        json.dump(self.data, open(self.path, "w"), indent=1)

    # ---------- builders ----------
    def add_asset(self, host, kind="", notes=""):
        if host not in [a["host"] for a in self.data["assets"]]:
            self.data["assets"].append({"host": host, "kind": kind, "notes": notes})

    def add_endpoint(self, endpoint, method="GET", authentication="unknown",
                     roles=None, object=None, owner_required=False,
                     parameters=None, observed_states=None):
        """Semantic endpoint record — what the URL MEANS, not just the URL."""
        rec = {"endpoint": endpoint, "method": method.upper(),
               "authentication": authentication,
               "roles": list(roles or []),
               "object": object, "owner_required": bool(owner_required),
               "parameters": list(parameters or []),
               "observed_states": list(observed_states or [])}
        key = (rec["endpoint"], rec["method"])
        for i, e in enumerate(self.data["endpoints"]):
            if (e["endpoint"], e["method"]) == key:
                # merge: keep the richer record
                for k, v in rec.items():
                    if v and not e.get(k):
                        e[k] = v
                return
        self.data["endpoints"].append(rec)

    def add_identity(self, name, role="user", owns=None):
        if name not in [i["name"] for i in self.data["identities"]]:
            self.data["identities"].append(
                {"name": name, "role": role, "owns": list(owns or [])})
        if role not in [r["name"] for r in self.data["roles"]]:
            self.data["roles"].append({"name": role, "capabilities": []})

    def add_workflow(self, name, states, transitions):
        """transitions: list of [from_state, to_state]."""
        for w in self.data["workflows"]:
            if w["name"] == name:
                w["states"] = sorted(set(w["states"]) | set(states))
                have = {tuple(t) for t in w["transitions"]}
                for t in transitions:
                    if tuple(t) not in have:
                        w["transitions"].append(list(t))
                return
        self.data["workflows"].append(
            {"name": name, "states": list(states),
             "transitions": [list(t) for t in transitions]})

    def add_parameter(self, name, seen_in="", user_controlled=True):
        if name not in [p["name"] for p in self.data["parameters"]]:
            self.data["parameters"].append(
                {"name": name, "seen_in": seen_in,
                 "user_controlled": bool(user_controlled)})

    def add_observation(self, text):
        if text and text not in self.data["observations"]:
            self.data["observations"].append(text)

    @classmethod
    def build_from_world_model(cls, world):
        """Construct/refresh a Target from a WorldModel instance."""
        t = cls(world.target)
        m = world.model
        for s in m.get("services", []):
            t.add_asset(s.get("host", ""), kind="service",
                        notes=",".join(s.get("tech", [])))
            for tech in s.get("tech", []):
                if tech not in [x["name"] for x in t.data["technologies"]]:
                    t.data["technologies"].append(
                        {"name": tech, "evidence": s.get("host", "")})
        for ident in m.get("identities", []):
            t.add_identity(ident.get("name", "unknown"))
        for role in m.get("roles", []):
            rname = role.get("name") if isinstance(role, dict) else role
            if rname and rname not in [r["name"] for r in t.data["roles"]]:
                t.data["roles"].append({"name": rname, "capabilities": []})
        for obj in m.get("objects", []):
            oname = obj.get("name") if isinstance(obj, dict) else obj
            if oname:
                t.add_parameter(oname, seen_in="world_model",
                                user_controlled=True)
        for rel in m.get("relations", []):
            if rel.get("kind") == "exposes":
                t.add_endpoint(rel.get("to", ""), authentication="unknown")
        # workflow skeletons from observed transitions
        by_obj = {}
        for tr in m.get("transitions", []):
            by_obj.setdefault(tr.get("object", "unknown"), []).append(
                [tr.get("frm_state", "?"), tr.get("to_state", "?")])
        for obj, trans in by_obj.items():
            states = sorted({s for pair in trans for s in pair})
            t.add_workflow(obj, states, trans)
        t.save()
        return t

    # ---------- reasoning ----------
    def authz_matrix(self):
        """ROLE x OBJECT x ACTION x STATE table.

        Returns list of rows: {role, object, action, states, endpoint,
        owner_required, authentication, risk} where risk flags cells worth
        testing (object endpoints reachable by a role without ownership proof).
        """
        rows = []
        for e in self.data["endpoints"]:
            obj = e.get("object") or _guess_object(e["endpoint"])
            action = _method_to_action(e.get("method", "GET"))
            roles = e.get("roles") or ["any"]
            for role in roles:
                risk = "test" if (e.get("owner_required")
                                  and e.get("authentication") not in ("none",)) else "low"
                if e.get("authentication") in ("none", "unknown") and obj:
                    risk = "test"  # unauthenticated object access: always worth a probe
                rows.append({
                    "role": role, "object": obj, "action": action,
                    "states": e.get("observed_states") or [],
                    "endpoint": f"{e.get('method')} {e['endpoint']}",
                    "owner_required": e.get("owner_required", False),
                    "authentication": e.get("authentication"),
                    "risk": risk,
                })
        return rows

    def authz_questions(self, limit=12):
        """Prioritized authorization questions derived from the matrix."""
        qs = []
        for row in self.authz_matrix():
            if row["risk"] != "test":
                continue
            obj, action, role = row["object"], row["action"], row["role"]
            if row["owner_required"]:
                qs.append(f"Can role '{role}' {action} {obj} owned by someone else? "
                          f"({row['endpoint']})")
            elif row["authentication"] in ("none", "unknown") and obj:
                qs.append(f"Is {obj} reachable with {row['authentication']} auth? "
                          f"({row['endpoint']}) — unauthenticated object access?")
        # dedupe, keep order
        seen, out = set(), []
        for q in qs:
            if q not in seen:
                seen.add(q)
                out.append(q)
        return out[:limit]

    def record_transition(self, workflow, frm, to, actor="unknown", note=""):
        """Log an OBSERVED transition (from experiments), not a declared one."""
        for w in self.data["workflows"]:
            if w["name"] == workflow:
                w.setdefault("observed", []).append(
                    {"from": frm, "to": to, "actor": actor, "note": note})
                return
        self.add_workflow(workflow, [frm, to], [])
        self.data["workflows"][-1]["observed"] = [
            {"from": frm, "to": to, "actor": actor, "note": note}]

    def workflow_gaps(self):
        """Compare observed transitions against declared workflows.

        Returns dicts: {workflow, kind, detail} where kind in
        missing | invalid | unexpected | repeated.
          missing    — declared transition never observed
          invalid    — observed transition not in declared set
          unexpected — observed transition from/to unknown states
          repeated   — same transition observed 3+ times (possible replay/race surface)
        """
        gaps = []
        for w in self.data["workflows"]:
            declared = {tuple(t) for t in w.get("transitions", [])}
            states = set(w.get("states", []))
            observed = w.get("observed", [])
            seen_counts = {}
            for o in observed:
                pair = (o.get("from"), o.get("to"))
                seen_counts[pair] = seen_counts.get(pair, 0) + 1
                if pair not in declared:
                    if o.get("from") not in states or o.get("to") not in states:
                        kind = "unexpected"
                    else:
                        kind = "invalid"
                    gaps.append({"workflow": w["name"], "kind": kind,
                                 "detail": f"observed {pair[0]} -> {pair[1]} "
                                           f"(actor={o.get('actor')}) not in declared transitions"})
                elif seen_counts[pair] >= 3:
                    gaps.append({"workflow": w["name"], "kind": "repeated",
                                 "detail": f"{pair[0]} -> {pair[1]} observed "
                                           f"{seen_counts[pair]}x — replay/race surface?"})
            for d in declared - set(seen_counts):
                gaps.append({"workflow": w["name"], "kind": "missing",
                             "detail": f"declared transition {d[0]} -> {d[1]} never observed"})
        return gaps

    def workflow_anomalies(self):
        """Observed transitions that violate the declared workflow (invalid + unexpected)."""
        return [g for g in self.workflow_gaps()
                if g["kind"] in ("invalid", "unexpected")]

    def summary(self):
        d = self.data
        return (f"target={self.name} assets={len(d['assets'])} "
                f"endpoints={len(d['endpoints'])} identities={len(d['identities'])} "
                f"roles={len(d['roles'])} workflows={len(d['workflows'])} "
                f"params={len(d['parameters'])} observations={len(d['observations'])}")


def _guess_object(endpoint):
    parts = [p for p in endpoint.split("/") if p and not p.startswith("{")
             and p not in ("api", "v1", "v2", "v3")]
    return parts[-1] if parts else None


def _method_to_action(method):
    return {"GET": "read", "POST": "create", "PUT": "update",
            "PATCH": "update", "DELETE": "delete"}.get(method.upper(), "invoke")


def load_target(name):
    return Target(name)
