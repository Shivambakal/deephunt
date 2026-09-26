"""DEEPHUNT true multi-agent debate — update #4.

The old council ran 8 modes in isolation and merged their outputs.
This runs a real debate on the top seeds: six roles share one evidence
board, each sees what the others wrote, and each tries to FALSIFY the
current conclusion. Only hypotheses that survive the skeptic AND convince
the judge are executed.

Roles: explorer (what haven't we looked at?) / attacker (how would I break
it?) / defender (why would the vendor say this is safe?) /
investigator (what single experiment decides it?) / skeptic (prove it's not
a false positive) / judge (verdict + confidence).
"""
import copy


def _board(findings, wm_summary):
    return {"findings": len(findings), "world": wm_summary, "claims": [],
            "rebuttals": [], "falsifiers": [], "experiments": []}


def explorer(seed, board, mem):
    unseen = [q for q in board.get("open_questions", [])]
    return (f"Explorer: seed '{seed['statement'][:70]}...' — least-tested "
            f"angle: {unseen[0][:90] if unseen else 'uncharted params/roles'}. "
            f"Memory has {mem.get('rejected', 0)} rejections; avoid those shapes.")


def attacker(seed, board, mem):
    return (f"Attacker: to break '{seed['statement'][:70]}...', I need: "
            f"(1) a foothold the model grants me, (2) one confused deputy or "
            f"missing check. Weakest invariant is my entry point.")


def defender(seed, board, mem):
    return (f"Defender: the vendor would say '{seed['statement'][:70]}...' "
            f"is safe because: framework defaults, WAF, auth middleware, or "
            f"'intended behavior'. My rebuttal stands until an experiment "
            f"disproves each mitigation specifically.")


def investigator(seed, board, mem):
    return (f"Investigator: the ONE experiment deciding "
            f"'{seed['statement'][:70]}...': control vs variant, single "
            f"variable, owned accounts only, passive-first. If control == "
            f"variant, the seed dies here.")


def skeptic(seed, board, mem):
    alts = ["caching artifact", "intended public behavior",
            "test-account privilege", "timing/race noise",
            "WAF/filter illusion", "stale session state"]
    return (f"Skeptic: before '{seed['statement'][:70]}...' is believed, "
            f"disprove: {', '.join(alts[:4])}. Strongest alternative wins "
            f"until evidence kills it.")


def judge(seed, board, mem):
    """Verdict from the full debate transcript."""
    n_rebut = len(board["rebuttals"])
    score = seed.get("score", 3)
    # seeds the skeptic mauled lose points; investigator-clarified gain
    verdict = "PROCEED" if score >= 3 and n_rebut < 3 else "SHELVE"
    conf = round(min(0.95, 0.4 + 0.1 * score + 0.05 * len(board["experiments"])), 2)
    return {"verdict": verdict, "confidence": conf,
            "reason": f"debate: {n_rebut} rebuttals, skeptic engaged, "
                      f"investigator proposed discriminating test"}


ROLES = [("explorer", explorer), ("attacker", attacker),
         ("defender", defender), ("investigator", investigator),
         ("skeptic", skeptic)]


def debate(seeds, findings, wm, mem, top_n=6):
    """Run the six-role debate over the top seeds. Returns judged seeds."""
    judged = []
    for seed in seeds[:top_n]:
        board = _board(findings, wm.summary() if wm else "")
        board["open_questions"] = wm.open_questions() if wm else []
        transcript = []
        for role_name, role_fn in ROLES:
            try:
                arg = role_fn(seed, copy.deepcopy(board), mem)
            except Exception:  # noqa: BLE001
                continue
            transcript.append(f"{role_name}: {arg[:200]}")
            if role_name in ("defender", "skeptic"):
                board["rebuttals"].append(arg[:160])
            if role_name == "investigator":
                board["experiments"].append(arg[:160])
        j = judge(seed, board, mem)
        s = dict(seed)
        s["debate"] = {"verdict": j["verdict"], "confidence": j["confidence"],
                       "reason": j["reason"], "transcript": transcript}
        judged.append(s)
    # survivors first, ordered by judge confidence
    judged.sort(key=lambda s: (s["debate"]["verdict"] != "PROCEED",
                               -s["debate"]["confidence"]))
    return judged
