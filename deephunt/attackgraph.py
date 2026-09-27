#!/usr/bin/env python3
"""DEEPHUNT attack/trust graph — the ATTACK / TRUST GRAPH stage.

Two graphs, one builder:

  ATTACK GRAPH: who-can-reach-what. Nodes = identities, roles, endpoints,
  objects, params. Edges = world-model relations + authz-matrix cells.
  A PATH is a chain low-priv identity -> endpoint -> object where at least
  one hop crosses a trust boundary or hits a low-confidence belief.
  Paths are hypotheses by construction — even with no technique card.

  TRUST GRAPH: what the target claims to enforce. Nodes = trust boundaries
  declared in the world model; each carries the confidence of the beliefs
  that depend on it. The weakest boundary is where probing starts.

Built from: world_model.WorldModel + target_model.Target (+ FeatureGraph
for the typed projection). Pure function of the models — no network.
"""
from __future__ import annotations

import os
import sys
from collections import deque

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from feature_graph import FeatureGraph  # noqa: E402

_PRIV = {"anonymous": 0, "anon": 0, "guest": 1, "user": 2, "member": 2,
         "service": 2, "user_a": 2, "user_b": 2, "admin": 3, "owner": 3,
         "system": 4}


def _priv(name: str) -> int:
    return _PRIV.get((name or "").lower(), 2)


def build(world_model, target, max_paths: int = 12) -> dict:
    """world_model: deephunt world_model.WorldModel; target: Target."""
    fg = FeatureGraph()
    try:
        fg.build_from_world(world_model)
    except Exception:
        pass

    m = world_model.model
    # --- enrich the feature graph with authz-matrix edges ---
    for row in target.authz_matrix():
        if row["risk"] != "test":
            continue
        role_n = fg.add_node(f"role:{row['role']}", "role")
        ep_n = fg.add_node(row["endpoint"], "endpoint",
                           auth=row["authentication"])
        fg.add_edge(role_n, ep_n, "may-reach")
        if row["object"]:
            obj_n = fg.add_node(f"obj:{row['object']}", "object")
            fg.add_edge(ep_n, obj_n, f"action:{row['action']}")

    # --- trust graph: boundaries with dependent-belief confidence ---
    trust = []
    for b in m.get("trust_boundaries", []):
        name = b if isinstance(b, str) else b.get("name", str(b))
        confs = [v["confidence"] for k, v in m.get("beliefs", {}).items()
                 if name.lower() in k.lower()]
        trust.append({"boundary": name,
                      "confidence": round(sum(confs) / len(confs), 3) if confs
                      else 0.5})
    trust.sort(key=lambda x: x["confidence"])

    # --- attack paths: BFS from low-priv identities to objects ---
    starts = [n for n, d in fg.nodes.items()
              if d.get("kind") in ("identity", "role")
              and _priv(n.split(":", 1)[-1]) <= 2]
    goals = {n for n, d in fg.nodes.items() if d.get("kind") == "object"}
    adj = {}
    for frm, to, kind in fg.edges:
        adj.setdefault(frm, []).append((to, kind))

    weakest_inv, weakest_conf = world_model.weakest_invariant()
    paths = []
    for s in starts[:8]:
        # BFS with path tracking, depth cap 5
        q = deque([(s, [s], [])])
        seen = {s}
        while q and len(paths) < max_paths * 3:
            node, path, ekinds = q.popleft()
            if node in goals and len(path) > 1:
                paths.append((path, ekinds))
                continue
            if len(path) >= 6:
                continue
            for nxt, kind in adj.get(node, []):
                if nxt not in seen:
                    seen.add(nxt)
                    q.append((nxt, path + [nxt], ekinds + [kind]))

    ranked = []
    for path, ekinds in paths:
        crosses = sum(1 for k in ekinds
                      if k in ("may-reach", "exposes") or k.startswith("action:"))
        # privilege escalation along the path?
        privs = [_priv(p.split(":", 1)[-1]) for p in path
                 if fg.nodes.get(p, {}).get("kind") in ("identity", "role")]
        esc = max(privs) - min(privs) if privs else 0
        score = crosses * 2 + esc * 3
        if weakest_inv and any(weakest_inv.split()[0].lower() in p.lower()
                               for p in path):
            score += 2
        ranked.append({"path": path, "edges": ekinds,
                       "boundary_crossings": crosses,
                       "privilege_escalation": esc,
                       "score": score,
                       "why": f"{crosses} boundary crossings, "
                              f"privilege delta {esc}"})
    ranked.sort(key=lambda p: -p["score"])
    ranked = ranked[:max_paths]

    return {"paths": ranked,
            "trust": trust,
            "weakest_boundary": trust[0] if trust else None,
            "weakest_invariant": {"statement": weakest_inv,
                                  "confidence": weakest_conf},
            "node_count": len(fg.nodes), "edge_count": len(fg.edges),
            "hypothesis_seeds": [
                {"statement": f"attack path: {' -> '.join(p['path'][:4])}"
                              f"{' ...' if len(p['path']) > 4 else ''} "
                              f"({p['why']}) — verify each hop with owned "
                              f"identities; a hop that shouldn't work is a finding.",
                 "source": "attack-graph", "score": min(5, 2 + p["score"] // 2),
                 "provenance": f"graph path score {p['score']}"}
                for p in ranked[:6]]}
