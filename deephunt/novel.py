"""DEEPHUNT novel hypothesis generator — update #2.

The 71 technique cards + 20 bias cards cover what is KNOWN. This module
covers what is NOT: it fires when observations don't fit existing patterns.

Two engines:
  1. anomaly-driven — observations the world model flagged as unexplained
     become "why is this happening?" hypotheses;
  2. combinatorial — technique x developer-bias x context produces attack
     ideas that exist in no card and no memory (checked for novelty).

This is the `heretic` thinking mode: it is REQUIRED to propose hypotheses
outside the catalogue.
"""
import itertools
import random

CONTEXTS = ["AI assistant/agent", "mobile API", "webhook handler",
            "file parser", "OAuth flow", "GraphQL", "websocket",
            "password reset", "share/invite link", "export/report",
            "admin panel", "third-party integration"]


def _mk(statement, reasoning):
    return {"statement": statement, "family": "novel", "source": "heretic",
            "reasoning": reasoning, "score": 5}


def from_anomalies(wm, mem, is_novel, limit=4):
    """Turn unexplained observations into why-questions."""
    out = []
    for a in wm.model.get("anomalies", [])[:6]:
        stmt = (f"[novel/anomaly] Unexplained observation: '{a[:120]}'. "
                f"Form three competing explanations (benign / misconfig / "
                f"vulnerability) and design ONE experiment that kills two.")
        ok, _ = is_novel(stmt, mem)
        if ok:
            out.append(_mk(stmt, "No card or bias explains this — reasoning "
                                 "from first principles."))
        if len(out) >= limit:
            break
    return out


def combinatorial(cards, biases, mem, is_novel, target, limit=6):
    """technique x bias x context — attacks nobody catalogued."""
    out, tried = [], 0
    combos = list(itertools.product(cards[:24], biases[:20], CONTEXTS))
    random.seed(hash(target) % (2 ** 32))
    random.shuffle(combos)
    for tech, bias, ctx in combos:
        tried += 1
        if tried > 60 or len(out) >= limit:
            break
        stmt = (f"[novel/combo] {tech['name']} x {bias['name']} on {ctx} "
                f"({target}): {bias['hunt'][:110]}")
        ok, _ = is_novel(stmt, mem)
        if ok:
            out.append(_mk(stmt,
                            f"Novel cross of '{tech['id']}' with '{bias['id']}' "
                            f"in a {ctx} context — outside every card."))
    return out


def from_chains(chains, mem, is_novel, limit=4):
    """Feature-graph chains become hypotheses by construction."""
    out = []
    for ch in chains[:6]:
        stmt = (f"[novel/chain] Privilege-crossing chain observed: {ch}. "
                f"Walk it with two owned identities (low-priv vs high-priv) "
                f"and find where the boundary actually holds.")
        ok, _ = is_novel(stmt, mem)
        if ok:
            out.append(_mk(stmt, "Chain crosses a trust boundary the model "
                                 "did not expect — no card needed."))
        if len(out) >= limit:
            break
    return out
