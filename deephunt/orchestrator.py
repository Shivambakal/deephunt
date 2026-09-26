"""DEEPHUNT orchestrator — the loop that doesn't stop until it learns or wins.

Cycle: INTAKE -> INTERNET -> FUNNEL -> HYPOTHESIZE -> ADVERSARY/DESIGN ->
AUTHORIZE -> EXECUTE -> OBSERVE -> LEARN -> (repeat with novel hypotheses)

Stops on: validated finding | no novel hypotheses | max cycles | STOP file.
"""
from __future__ import annotations
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                ".."))

import learn  # noqa: E402
import internet as inet  # noqa: E402
import think  # noqa: E402
import train  # noqa: E402
from tools import list_tools  # noqa: E402
from tools.base import now  # noqa: E402

try:
    from brain.session import ResearchSession
except ImportError:
    ResearchSession = None

BASE = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.join(BASE, "state")
LOG_DIR = os.path.join(BASE, "logs")

# hypothesis families — the human hunter's lenses
FAMILIES = {
    "authz": "authorization comparison across users/roles/objects/actions",
    "logic": "business-logic violated assumption",
    "state": "state transition / race condition",
    "ai": "AI/LLM trust-boundary violation (prompt injection, data leakage)",
    "js": "hidden route/parameter exposed in client code",
}


def log(run_log, msg):
    line = f"[{now()}] {msg}"
    print(line, flush=True)
    run_log.write(line + "\n")
    run_log.flush()


def load_profile(target):
    import yaml
    path = os.path.join(BASE, "targets", f"{target}.yaml")
    if not os.path.isfile(path):
        # tiny yaml fallback without pyyaml
        raise FileNotFoundError(f"no target profile: {path}")
    try:
        import yaml as _y
        return _y.safe_load(open(path))
    except ImportError:
        return _mini_yaml(open(path).read())


def _mini_yaml(text):
    """Minimal YAML subset parser (maps, lists, scalars) — no dependency."""
    root, stack = {}, [(-1, root)]
    for raw in text.splitlines():
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        while stack and stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1]
        if line.startswith("- "):
            val = line[2:].strip().strip("'\"")
            if not isinstance(parent, list):
                raise ValueError("bad yaml")
            parent.append(val)
        elif ":" in line:
            k, v = line.split(":", 1)
            k, v = k.strip(), v.strip().strip("'\"")
            if v == "":
                # peek: list or map? assume list if next non-empty starts with -
                parent[k] = []
                stack.append((indent, parent[k]))
                # fix: if it turns out to be a map, convert lazily below
                parent[k + "_ismap"] = True
            elif v == "|":
                parent[k] = ""
                stack.append((indent, ("literal", k, parent)))
            else:
                parent[k] = v
        else:
            # literal block content
            if isinstance(parent, tuple) and parent[0] == "literal":
                _, k, grand = parent
                grand[k] += line + "\n"
    # cleanup map markers
    def clean(o):
        if isinstance(o, dict):
            return {k: clean(v) for k, v in o.items()
                    if not k.endswith("_ismap")}
        if isinstance(o, list):
            return [clean(v) for v in o]
        return o
    return clean(root)


def save_state(target, state):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(os.path.join(STATE_DIR, f"{target}.json"), "w") as f:
        json.dump(state, f, indent=1, default=str)


def funnel_findings(findings, mem):
    """10k -> 500 -> 50 -> 10: inventory -> interesting -> sensitive."""
    inventory = [f for f in findings if f["kind"] == "inventory"]
    sensitive = [f for f in findings if f["kind"] == "sensitive"]
    vuln = [f for f in findings if f["kind"] == "vuln-candidate"]
    # interesting = api-shaped, auth-shaped, or unseen paths
    interesting = []
    for f in findings:
        d = (f.get("detail", "") + " " + f.get("title", "")).lower()
        if any(k in d for k in ("api", "token", "auth", "share", "session",
                               "admin", "graphql", "upload", "export")):
            if f not in sensitive:
                interesting.append(f)
    return {"inventory": inventory, "interesting": interesting,
            "sensitive": sensitive, "vuln_candidates": vuln}


def seeds_from_funnel(funnel, profile, mem):
    """Turn funnel output + profile seeds + internet into hypothesis statements."""
    seeds = []
    for s in funnel["sensitive"][:10]:
        detail = s.get("detail", "").splitlines()
        ep = detail[0] if detail else s.get("title", "")
        for fam, lens in FAMILIES.items():
            if fam == "ai" and "ai" not in profile.get("vuln_classes_text", "ai").lower():
                continue
            stmt = (f"[{fam}] {ep}: {lens} may be exploitable — "
                    f"probe with two self-owned accounts/objects and compare "
                    f"responses across the trust boundary")
            seeds.append({"statement": stmt, "family": fam,
                          "source": f"funnel:{s['tool']}"})
    for ps in profile.get("hypothesis_seeds", []):
        seeds.append({"statement": ps, "family": "logic",
                      "source": "profile"})
    # dedupe against memory
    novel = []
    for sd in seeds:
        ok, dup = learn.is_novel(sd["statement"], mem)
        if ok:
            novel.append(sd)
    # cap: keep diverse families
    seen_fam, out = set(), []
    for sd in novel:
        if sd["family"] not in seen_fam or len(out) < 3:
            out.append(sd)
            seen_fam.add(sd["family"])
        if len(out) >= 6:
            break
    return out


def run_target(target, max_cycles=3, passive_only=False, run_log=None):
    profile = load_profile(target)
    mem = learn.load_memory(target)
    state_path = os.path.join(STATE_DIR, f"{target}.json")
    state = {"target": target, "cycles": [], "findings": [],
             "operator_tasks": [], "stop_reason": None,
             "profile_snapshot": {k: profile.get(k) for k in
                                  ("scope_hosts", "program", "active_allowed")}}
    if os.path.isfile(state_path):
        try:
            old = json.load(open(state_path))
            state["previous"] = {"cycles": len(old.get("cycles", [])),
                                 "stop_reason": old.get("stop_reason")}
        except (OSError, json.JSONDecodeError):
            pass

    os.makedirs(LOG_DIR, exist_ok=True)
    rl = run_log or open(os.path.join(
        LOG_DIR, f"{target}_{time.strftime('%Y%m%d-%H%M%S')}.log"), "w")

    log(rl, f"DEEPHUNT starting: target={target} program={profile.get('program')}")
    log(rl, f"memory: {mem['sessions']} sessions, {len(mem['rejected'])} "
            f"rejected hypotheses loaded — will not retry them")

    session = None
    if ResearchSession:
        session = ResearchSession(
            objective=f"DEEPHUNT autonomous hunt: {target} "
                      f"({profile.get('program')})")
        log(rl, f"ResearchSession {session.id} opened")

    ctx = {"target": target, "profile": profile, "state": state,
           "state_dir": STATE_DIR, "session": session,
           "authorization": None}

    # ---- INTAKE: passive tools ------------------------------------------------
    log(rl, "PHASE: INTAKE (passive tools)")
    for tool in list_tools("passive"):
        if not tool.available():
            log(rl, f"  [skip] {tool.name} not installed")
            continue
        try:
            findings = tool.run(ctx) or []
        except Exception as e:  # noqa: BLE001
            findings = [{"tool": tool.name, "phase": "passive",
                         "kind": "error", "title": f"{tool.name} crashed",
                         "detail": str(e)[:300]}]
        state["findings"].extend(findings)
        log(rl, f"  [{tool.name}] {len(findings)} findings")
        if session:
            for f in findings[:6]:
                session.observe(f"{f['tool']}: {f['title']} — "
                                f"{f.get('evidence', '')[:160]}", kind="fact")

    # ---- INTERNET: fresh techniques -------------------------------------------
    log(rl, "PHASE: INTERNET (fresh techniques)")
    try:
        intel, ipath = inet.collect(profile, STATE_DIR)
        log(rl, f"  {len(intel['seeds'])} technique seeds ({ipath})")
        if session:
            for sd in intel["seeds"][:8]:
                session.observe(f"internet seed: {sd['technique']} "
                                f"({sd['source']})", kind="fact")
    except Exception as e:  # noqa: BLE001
        intel = {"seeds": []}
        log(rl, f"  internet phase failed: {e}")

    cycles_without_novel = 0
    for cycle in range(max_cycles):
        if os.path.isfile(os.path.join(STATE_DIR, "STOP")):
            state["stop_reason"] = "STOP file present"
            break
        log(rl, f"===== CYCLE {cycle + 1}/{max_cycles} =====")

        # ---- FUNNEL ----
        funnel = funnel_findings(state["findings"], mem)
        log(rl, f"FUNNEL: {len(funnel['inventory'])} inventory / "
                f"{len(funnel['interesting'])} interesting / "
                f"{len(funnel['sensitive'])} sensitive / "
                f"{len(funnel['vuln_candidates'])} vuln-candidates")

        # internet seeds join the pool
        extra = [{"statement": f"[internet] {s['technique']} — test whether "
                               f"this technique class applies to {target}",
                  "family": "logic", "source": s["source"]}
                 for s in intel.get("seeds", [])[:6]]
        # THE BRAIN: seven thinking modes interrogate the evidence
        try:
            brain_seeds = think.council(state["findings"], profile, mem,
                                        limit=12)
        except Exception as e:  # noqa: BLE001
            log(rl, f"  think.council failed ({e}); falling back to funnel")
            brain_seeds = []
        seeds = (brain_seeds +
                 seeds_from_funnel(funnel, profile, mem) + extra)
        # dedupe internet seeds too, then rank by information-gain-per-cost
        # (experiment designer: cheapest discriminating experiment first)
        seeds = [s for s in seeds
                 if learn.is_novel(s["statement"], mem)[0]]
        try:
            import experiment as _exp
            seeds = _exp.rank(seeds)
        except Exception:  # noqa: BLE001
            pass
        seeds = seeds[:14]
        modes = {}
        for s in seeds:
            modes[s.get("mode", s.get("source", "?"))] = \
                modes.get(s.get("mode", s.get("source", "?")), 0) + 1
        log(rl, f"HYPOTHESIZE: {len(seeds)} novel seeds "
                f"(memory killed the retreads) modes={modes}")
        log(rl, f"  brain: {train.technique_report()}")

        cyc = {"n": cycle + 1, "seeds": len(seeds), "tests": []}
        if not seeds:
            cycles_without_novel += 1
            log(rl, "no novel hypotheses — learning, not looping blind")
            if cycles_without_novel >= 2:
                state["stop_reason"] = "no novel hypotheses for 2 cycles"
                break
            # still try operator task once per target
            seeds = [{"statement": "operator sweep", "family": "logic",
                      "source": "fallback"}]

        # ---- HYPOTHESIZE -> ADVERSARY/DESIGN -> AUTHORIZE ----
        # active testing only when the TARGET PROFILE allows it
        # (per-program rules live in targets/<name>.yaml)
        active_ok = (not passive_only) and profile.get("active_allowed",
                                                       False)
        if session and active_ok:
            for sd in seeds[:3]:
                try:
                    h = session.add_hypothesis(
                        statement=sd["statement"],
                        violated_assumption="A1",
                        attacker_view=f"seed from {sd['source']}",
                        defender_view="vendor has standard mitigations; "
                                      "assume filtered until proven otherwise",
                        devil_view="most similar past attempts were rejected — "
                                   "the discriminating test must be "
                                   "single-variable with a control",
                        investigator_test="minimum controlled experiment with "
                                          "owned accounts/data only",
                        killed_by="control and variant behave identically, or "
                                  "mitigation demonstrably neutralizes it",
                        impact=4, novelty=3, testability=3)
                except Exception as e:  # noqa: BLE001
                    log(rl, f"  hypothesis rejected by gate: {e}")
                    continue
                log(rl, f"  H {h['id']} score={h.get('score')} "
                        f"[{sd['family']}]")
                try:
                    t = session.propose_test(
                        hypothesis_id=h["id"],
                        expected_observation="variant differs from control in "
                                             "a security-relevant way",
                        reason=f"deephunt cycle {cycle + 1} top seed",
                        scope_hosts=profile.get("scope_hosts", []),
                        auth_basis=profile.get("auth_basis", "program scope; "
                                               "owned accounts/data only"),
                        success_criteria="unauthorized disclosure/action across "
                                         "the trust boundary",
                        failure_criteria="control == variant, or demonstrable "
                                         "neutralization",
                        single_variable=True)
                except Exception as e:  # noqa: BLE001
                    log(rl, f"  test refused: {e}")
                    cyc["tests"].append({"h": h["id"], "refused": str(e)[:200]})
                    continue
                auth = t.get("authorization") if isinstance(t, dict) else None
                if auth:
                    ctx["authorization"] = auth
                    log(rl, f"  T authorized: scope={auth.get('scope_hosts')}")
                cyc["tests"].append({"h": h["id"],
                                     "t": t.get("id") if isinstance(t, dict)
                                     else None,
                                     "authorized": bool(auth)})

        # ---- EXECUTE ----
        log(rl, "PHASE: EXECUTE")
        if passive_only or not profile.get("active_allowed", False):
            log(rl, "  active tools skipped (passive-only run or "
                    "active_allowed=false in profile)")
        for tool in list_tools("active"):
            if not tool.available():
                log(rl, f"  [skip] {tool.name} not installed")
                continue
            try:
                findings = tool.run(ctx) or []
            except Exception as e:  # noqa: BLE001
                findings = [{"tool": tool.name, "phase": "active",
                             "kind": "error", "title": f"{tool.name} crashed",
                             "detail": str(e)[:300]}]
            gated = [f for f in findings if f["kind"] == "gated"]
            real = [f for f in findings if f["kind"] != "gated"]
            state["findings"].extend(findings)
            for g in gated:
                log(rl, f"  [gated] {tool.name}: {g['detail'][:100]}")
            for f in real:
                log(rl, f"  [{tool.name}] {f['kind']}: {f['title'][:100]}")
                if f["kind"] == "vuln-candidate" and f.get(
                        "severity_hint") in ("critical", "high"):
                    state["stop_reason"] = (
                        f"vuln candidate: {f['title'][:120]}")
                    log(rl, "*** HIGH-SEVERITY CANDIDATE — stopping for "
                            "human validation ***")
        for tool in list_tools("operator"):
            try:
                findings = tool.run(ctx) or []
            except Exception as e:  # noqa: BLE001
                findings = []
            for f in findings:
                if f["kind"] == "operator-task":
                    state["operator_tasks"].append(f["evidence"])
                    log(rl, f"  [operator] {f['title'][:100]}")

        # ---- OBSERVE / LEARN ----
        if session:
            for f in state["findings"][-10:]:
                if f["kind"] in ("vuln-candidate", "sensitive", "clean"):
                    try:
                        session.observe(
                            f"{f['tool']}: {f['title'][:200]}", kind="fact")
                    except Exception:  # noqa: BLE001
                        pass
        state["cycles"].append(cyc)
        save_state(target, state)
        if state["stop_reason"]:
            break

    if not state["stop_reason"]:
        state["stop_reason"] = f"completed {max_cycles} cycles"
    save_state(target, state)
    write_postmortem(target, state, mem)
    log(rl, f"DEEPHUNT done: {state['stop_reason']}")
    log(rl, f"findings={len(state['findings'])} "
            f"operator_tasks={len(state['operator_tasks'])}")
    if not run_log:
        rl.close()
    return state


def write_postmortem(target, state, mem):
    """Self-improvement: after every run, write what worked, what failed,
    and what to build next. The program upgrades itself run after run."""
    ts = now().replace(":", "-")
    pm = [f"# DEEPHUNT postmortem — {target} @ {now()}",
          f"stop_reason: {state['stop_reason']}",
          f"findings: {len(state['findings'])}  "
          f"cycles: {len(state['cycles'])}",
          "",
          "## Tool hit rates"]
    by_tool = {}
    for f in state["findings"]:
        by_tool[f.get("tool", "?")] = by_tool.get(f.get("tool", "?"), 0) + 1
    for tool, n in sorted(by_tool.items(), key=lambda x: -x[1]):
        pm.append(f"- {tool}: {n} findings")
    pm.append("")
    pm.append("## Gaps to build (ROADMAP)")
    gaps = []
    try:
        for t in list_tools():
            if not t.available():
                gaps.append(f"- MISS tool: {t.name} ({t.description})")
    except Exception:  # noqa: BLE001
        pass
    if len(state["cycles"]) >= 2:
        last_two = [c.get("novel", 0) for c in state["cycles"][-2:]]
        if sum(last_two) == 0:
            gaps.append("- hypothesis engine stalled: add technique cards "
                        "or new funnel signals")
    pm.extend(gaps or ["- none observed this run"])
    pm.append("")
    pm.append("## Lessons (from memory)")
    pm.append(learn.mistakes_report(mem)[:2000])
    path = os.path.join(BASE, "state", f"{target}_postmortem_{ts}.md")
    open(path, "w").write("\n".join(pm) + "\n")
    # feed gaps into the standing roadmap
    rp = os.path.join(BASE, "ROADMAP.md")
    with open(rp, "a") as f:
        f.write(f"\n## {now()} — {target}\n")
        f.write("\n".join(gaps or ["- no new gaps"]) + "\n")
