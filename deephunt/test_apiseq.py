"""Tests for deephunt/apiseq.py — fake specs + fake executor, no network."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from apiseq import (
    ObjectPool, Param, RequestSpec, checker_cross_identity_replay,
    checker_use_after_delete, infer_dependencies, plan_bfs_fast,
    plan_random_walk, prune_on_feedback, render_sequence,
)


def _specs():
    return [
        RequestSpec(id="create", method="POST", path_template="/projects",
                    params=[Param("name", "body", "string", True)],
                    response_fields=["id", "name"]),
        RequestSpec(id="get", method="GET", path_template="/projects/{id}",
                    params=[Param("id", "path", "string", True)],
                    response_fields=["id", "name", "owner_id"]),
        RequestSpec(id="delete", method="DELETE", path_template="/projects/{id}",
                    params=[Param("id", "path", "string", True)],
                    response_fields=[], destructive=True),
        RequestSpec(id="list", method="GET", path_template="/projects",
                    response_fields=["projects"]),
    ]


def test_dependency_inference():
    deps = infer_dependencies(_specs())
    # get consumes id -> produced by create
    producers = {p for p, _, _ in deps["get"]}
    assert "create" in producers, f"get should depend on create, got {deps['get']}"
    # list has no id params -> no deps
    assert deps["list"] == [], f"list should be dep-free, got {deps['list']}"
    print("PASS test_dependency_inference")


def test_bfs_fast_sequences_valid():
    specs = _specs()
    seqs = plan_bfs_fast(specs, max_len=3)
    by_id = {s.id: s for s in specs}
    assert seqs, "no sequences planned"
    for seq in seqs:
        assert len(seq) <= 3
        # every consumer's deps satisfied by earlier producers
        deps = infer_dependencies(specs)
        for i, rid in enumerate(seq):
            earlier = set(seq[:i])
            needed = {p for p, _, _ in deps[rid]}
            assert not needed or (needed & earlier), \
                f"unsatisfied dep in {seq}"
        # destructive excluded by default
        assert "delete" not in seq, f"destructive leaked into {seq}"
    # create->get chain exists (producer before consumer)
    assert any(s.index("create") < s.index("get") for s in seqs if "get" in s), \
        f"no create->get chain in {seqs}"
    print("PASS test_bfs_fast_sequences_valid")


def test_render_uses_pool():
    by_id = {s.id: s for s in _specs()}
    pool = ObjectPool()
    pool.add("id", "proj-42")
    rendered = render_sequence(["get"], by_id, pool)
    assert rendered[0]["path"] == "/projects/proj-42", rendered[0]
    print("PASS test_render_uses_pool")


def test_prune_on_4xx():
    assert prune_on_feedback(["a"], [{"status": 200}]) is False
    assert prune_on_feedback(["a"], [{"status": 404}]) is True
    assert prune_on_feedback(["a"], [{"status": 500}]) is True
    print("PASS test_prune_on_4xx")


def test_checkers_emit_hypotheses():
    by_id = {s.id: s for s in _specs()}
    uad = checker_use_after_delete(by_id)
    assert any(h["sequence"] == ["delete", "get"] for h in uad), uad
    bola = checker_cross_identity_replay(by_id)
    assert any(h["sequence"] == ["get"] for h in bola), bola
    assert all("basis" in h for h in uad + bola), "checkers need auth basis"
    print("PASS test_checkers_emit_hypotheses")


def test_random_walk_bounded():
    seqs = plan_random_walk(_specs(), max_len=4, n_walks=3, seed=1)
    assert len(seqs) == 3
    assert all(len(s) <= 4 for s in seqs)
    print("PASS test_random_walk_bounded")


if __name__ == "__main__":
    test_dependency_inference()
    test_bfs_fast_sequences_valid()
    test_render_uses_pool()
    test_prune_on_4xx()
    test_checkers_emit_hypotheses()
    test_random_walk_bounded()
    print("apiseq: 6/6 pass")
