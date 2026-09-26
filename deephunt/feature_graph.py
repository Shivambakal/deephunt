"""DEEPHUNT cross-feature reasoning graph — update #7.

The technique graph (knowledge/graph.json) says what bug classes exist.
THIS graph says how the TARGET is wired: endpoints, parameters, identities,
objects, roles, APIs, caches, webhooks, mobile clients — and the relations
between them. The hunter then searches for unexpected CHAINS:

    low-priv identity -> endpoint -> param -> object -> admin-only role

A chain that crosses a trust boundary is a hypothesis by construction,
even when no technique card describes it.
"""
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))

_PRIV = {"anonymous": 0, "anon": 0, "guest": 1, "user": 2, "member": 2,
         "service": 2, "admin": 3, "owner": 3, "system": 4}


class FeatureGraph:
    def __init__(self):
        self.nodes = {}   # name -> {kind, ...}
        self.edges = []   # (frm, to, kind)

    def add_node(self, name, kind, **attrs):
        name = name[:160]
        if name not in self.nodes:
            self.nodes[name] = {"kind": kind, **attrs}
        return name

    def add_edge(self, frm, to, kind):
        e = (frm[:160], to[:160], kind)
        if e not in self.edges:
            self.edges.append(e)

    def build_from_world(self, wm):
        """Project the world model's relations into a typed feature graph."""
        m = wm.model
        for r in m["relations"]:
            fk = self._kind(r["frm"], m)
            tk = self._kind(r["to"], m)
            self.add_node(r["frm"], fk)
            self.add_node(r["to"], tk)
            self.add_edge(r["frm"], r["to"], r["kind"])
        for o in m["objects"]:
            n = self.add_node(o["name"], "object", owner=o["owner_role"])
            if o["owner_role"] != "unknown":
                self.add_node(o["owner_role"], "role")
                self.add_edge(o["owner_role"], n, "owns")
        for s in m["services"]:
            n = self.add_node(s["host"], "service", tech=",".join(s["tech"][:3]))
            for t in s["tech"][:3]:
                tn = self.add_node(t, "tech")
                self.add_edge(n, tn, "runs")
        for i in m["identities"]:
            self.add_node(i["name"], "identity")
        for r in m["roles"]:
            self.add_node(r["name"], "role")
        return self

    def _kind(self, name, m):
        if name.startswith("/"):
            return "endpoint"
        if name in [o["name"] for o in m["objects"]]:
            return "object"
        if name in [r["name"] for r in m["roles"]]:
            return "role"
        if name in [i["name"] for i in m["identities"]]:
            return "identity"
        if "." in name and " " not in name:
            return "service"
        return "param" if re.match(r"^[a-zA-Z_][\w\-]*$", name) else "entity"

    # ---------- chain search ----------
    def neighbors(self, node):
        return [(to, k) for (frm, to, k) in self.edges if frm == node]

    def find_chains(self, max_depth=4):
        """Find paths from low-privilege nodes to high-value objects/roles
        that cross a privilege boundary — each is a hypothesis seed."""
        chains = []
        starts = [n for n, a in self.nodes.items()
                  if a["kind"] in ("identity", "role")
                  and _PRIV.get(n, 2) <= 2]
        targets = [n for n, a in self.nodes.items()
                   if a["kind"] == "object"
                   or (a["kind"] == "role" and _PRIV.get(n, 0) >= 3)]
        for s in starts:
            for t in targets:
                for path in self._paths(s, t, max_depth):
                    if self._crosses_boundary(path):
                        chains.append(path)
        return chains[:10]

    def _paths(self, src, dst, depth, path=None):
        path = path or [src]
        if src == dst:
            return [path]
        if depth == 0:
            return []
        out = []
        for nxt, kind in self.neighbors(src):
            if nxt not in path:
                out += self._paths(nxt, dst, depth - 1, path + [(nxt, kind)])
        return out

    def _crosses_boundary(self, path):
        """True if the path reaches a node whose privilege exceeds the start."""
        nodes_only = [p if isinstance(p, str) else p[0] for p in path]
        start_priv = _PRIV.get(nodes_only[0], 2)
        for n in nodes_only[1:]:
            if _PRIV.get(n, 0) > start_priv and self.nodes.get(n, {}).get("kind") in ("role", "object"):
                return True
        return False

    def describe_chain(self, path):
        nodes_only = [p if isinstance(p, str) else p[0] for p in path]
        return " -> ".join(nodes_only)

    def stats(self):
        return f"feature-graph: {len(self.nodes)} nodes, {len(self.edges)} edges"
