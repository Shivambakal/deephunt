"""DEEPHUNT apiseq — stateful REST API sequence engine (RESTler *ideas*, clean-room).

No RESTler code is used. The concepts reimplemented:
  1. Spec ingestion: OpenAPI dict OR requests synthesized from observed traffic.
  2. Dependency inference: PRODUCES(req) = dynamic-object types in the response
     schema; CONSUMES(req) = types required by params; matched by fuzzy
     field-name matching (id, *_id, uuid, slug, token), scored 0..1.
  3. Planning: BFS-Fast (each request appended to at most one sequence) +
     RandomWalk for longer chains; bounded length.
  4. Execution: dynamic-object pool memoizes created objects in creation order;
     RENDER concretizes from dictionaries (observed values + card payloads).
  5. Dynamic feedback pruning: reusing an object that yields 4xx/5xx discards
     the sequence.
  6. Checkers: pluggable security-property tests expressed as hypothesis dicts
     for the ResearchSession loop (use-after-delete, cross-identity replay).

Safety: sequences are bounded in length, non-destructive verbs are the
default; destructive sequences require an explicit authorization basis and
must pass through Engine.execute() gates. This module only PLANS and renders;
it never sends traffic itself — the caller supplies an executor callable.
"""
from __future__ import annotations

import itertools
import random
import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

# Field-name patterns that denote dynamic object identity, with match weight.
ID_PATTERNS = [
    (re.compile(r"^id$"), 1.0),
    (re.compile(r".*_id$"), 0.9),
    (re.compile(r"^uuid$|^guid$"), 0.9),
    (re.compile(r".*uuid.*|.*guid.*"), 0.7),
    (re.compile(r"^slug$"), 0.6),
    (re.compile(r".*token.*"), 0.5),
]


def _id_score(name: str) -> float:
    n = (name or "").lower()
    best = 0.0
    for pat, w in ID_PATTERNS:
        if pat.search(n):
            best = max(best, w)
    return best


@dataclass
class Param:
    name: str
    location: str  # path | query | body | header
    ptype: str = "string"  # string | int | bool | object
    required: bool = False


@dataclass
class RequestSpec:
    id: str
    method: str
    path_template: str  # e.g. /projects/{id}
    params: List[Param] = field(default_factory=list)
    response_fields: List[str] = field(default_factory=list)  # response schema field names
    destructive: bool = False  # DELETE / state-corrupting verbs


def infer_dependencies(specs: List[RequestSpec]) -> Dict[str, List[Tuple[str, str, float]]]:
    """Return {consumer_req_id: [(producer_req_id, field, score)]}.

    PRODUCES(req) = response fields with id-like names.
    CONSUMES(req) = params (path/body) with id-like names.
    A consumer param matches a producer field when names are equal or one
    contains the other (fuzzy), scored by _id_score.
    """
    produced: Dict[str, List[Tuple[str, float]]] = {}  # req_id -> [(field, score)]
    for s in specs:
        fields = [(f, _id_score(f)) for f in s.response_fields]
        produced[s.id] = [(f, sc) for f, sc in fields if sc > 0]

    deps: Dict[str, List[Tuple[str, str, float]]] = {s.id: [] for s in specs}
    for consumer in specs:
        for p in consumer.params:
            if p.location not in ("path", "body", "query"):
                continue
            ps = _id_score(p.name)
            if ps == 0:
                continue
            for producer in specs:
                if producer.id == consumer.id:
                    continue
                for f, fs in produced[producer.id]:
                    pn, fn = p.name.lower(), f.lower()
                    if pn == fn or pn in fn or fn in pn:
                        deps[consumer.id].append(
                            (producer.id, f, round(min(ps, fs) + 0.1, 2)))
        # best producer first
        deps[consumer.id].sort(key=lambda t: -t[2])
    return deps


def _satisfied(seq: List[str], consumer_id: str,
               deps: Dict[str, List[Tuple[str, str, float]]]) -> bool:
    """Every consumed type must have been produced earlier in the sequence."""
    if not deps.get(consumer_id):
        return True  # no deps -> always appendable
    producers = {p for p, _, _ in deps[consumer_id]}
    return bool(producers & set(seq))


def plan_bfs_fast(specs: List[RequestSpec], max_len: int = 3,
                  allow_destructive: bool = False) -> List[List[str]]:
    """BFS-Fast: each request appended to at most one sequence (small set,
    full request coverage)."""
    deps = infer_dependencies(specs)
    pool = [s for s in specs if not s.destructive or allow_destructive]
    seqs: List[List[str]] = [[s.id] for s in pool if not deps[s.id]]
    if not seqs:  # everything has deps: seed with dep-free producers
        seqs = [[s.id] for s in pool]
    used_extend = set()
    changed = True
    while changed:
        changed = False
        for seq in list(seqs):
            if len(seq) >= max_len:
                continue
            for s in pool:
                if s.id in seq or s.id in used_extend:
                    continue
                if _satisfied(seq, s.id, deps):
                    seq.append(s.id)
                    used_extend.add(s.id)
                    changed = True
                    break
    return seqs


def plan_random_walk(specs: List[RequestSpec], max_len: int = 4,
                     n_walks: int = 5, seed: int = 0,
                     allow_destructive: bool = False) -> List[List[str]]:
    rng = random.Random(seed)
    deps = infer_dependencies(specs)
    pool = [s for s in specs if not s.destructive or allow_destructive]
    walks = []
    for _ in range(n_walks):
        seq = [rng.choice(pool).id]
        for _ in range(max_len - 1):
            cands = [s for s in pool
                     if s.id not in seq and _satisfied(seq, s.id, deps)]
            if not cands:
                break
            seq.append(rng.choice(cands).id)
        walks.append(seq)
    return walks


class ObjectPool:
    """Memoizes dynamic objects produced during a sequence, in creation order."""

    def __init__(self):
        self.by_type: Dict[str, List[str]] = {}
        self.order: List[Tuple[str, str]] = []

    def add(self, field: str, value: str):
        self.by_type.setdefault(field.lower(), []).append(value)
        self.order.append((field, value))

    def get(self, field: str) -> Optional[str]:
        vals = self.by_type.get(field.lower())
        return vals[-1] if vals else None


def render_sequence(seq: List[str], specs: Dict[str, RequestSpec],
                    pool: ObjectPool,
                    dictionaries: Optional[Dict[str, List[str]]] = None
                    ) -> List[Dict]:
    """Concretize a planned sequence into request dicts.

    Value sources (priority): object pool (producer-consumer) -> dictionaries
    (observed values / card payloads) -> path-template placeholder kept.
    Returns list of {method, path, params} dicts.
    """
    dictionaries = dictionaries or {}
    rendered = []
    for rid in seq:
        spec = specs[rid]
        path = spec.path_template
        params = {}
        for p in spec.params:
            val = pool.get(p.name)
            if val is None:
                cands = dictionaries.get(p.name) or dictionaries.get(p.ptype) or []
                val = cands[0] if cands else f"{{{p.name}}}"
            params[p.name] = val
            if p.location == "path":
                path = path.replace("{" + p.name + "}", str(val))
        rendered.append({"id": rid, "method": spec.method,
                         "path": path, "params": params})
    return rendered


def prune_on_feedback(seq_ids: List[str], results: List[Dict]) -> bool:
    """Dynamic feedback pruning: if reusing a pooled object yields 4xx/5xx,
    the sequence is discarded. results[i] = {'status': int}."""
    for r in results:
        if r.get("status", 0) >= 400:
            return True  # prune
    return False


# -- Checkers: security properties expressed as hypothesis dicts --------

def checker_use_after_delete(specs: Dict[str, RequestSpec]) -> List[Dict]:
    """DELETE -> GET should 404. Returns hypothesis dicts for the session loop."""
    hyps = []
    for s in specs.values():
        if s.method == "DELETE":
            # find a GET on the same path template family
            base = s.path_template.split("{")[0]
            getters = [g for g in specs.values()
                       if g.method == "GET" and g.path_template.startswith(base)]
            for g in getters:
                hyps.append({
                    "technique": "API-05",
                    "name": "use-after-delete",
                    "sequence": [s.id, g.id],
                    "expected": "GET after DELETE returns 404; 200 with body = use-after-free",
                    "basis": "owned test objects only",
                })
    return hyps


def checker_cross_identity_replay(specs: Dict[str, RequestSpec]) -> List[Dict]:
    """Replay identity-A's object IDs under identity-B's session (BOLA)."""
    hyps = []
    deps = infer_dependencies(list(specs.values()))
    for s in specs.values():
        if deps.get(s.id) and s.method in ("GET", "PUT", "PATCH", "DELETE"):
            hyps.append({
                "technique": "API-06",
                "name": "cross-identity object replay",
                "sequence": [s.id],
                "expected": "403/404 under identity B; 200 with A's data = BOLA",
                "basis": "two owned test accounts; Engine.execute() differential",
            })
    return hyps
