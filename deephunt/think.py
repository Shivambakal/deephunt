"""DEEPHUNT think — the developed brain. Seven thinking modes interrogate the
same evidence from different angles, the way a senior hunter does. This is
what "think different" means in code: the predator, the architect, the
accountant, the saboteur, the ghost, the scholar, and the oracle.

Resources fed to the brain:
  knowledge/techniques.yaml  (39 technique cards — scholar mode)
  knowledge/past_attacks.md  (bounty shapes that keep paying — oracle mode)
  intel/*.md                 (target-specific recon — all modes)
  data/brain/sessions/*.json (rejected hypotheses — never retried)
  proxy/logs/*/traffic.jsonl (tried paths)
  state/internet_<target>.json (fresh techniques from the web)
"""
from __future__ import annotations
import glob
import json
import os
import re

import learn  # noqa: E402
import train  # noqa: E402

BASE = os.path.dirname(os.path.abspath(__file__))
INTEL = os.path.join(BASE, "..", "intel")


def _blob(findings):
    return " ".join(
        f.get("title", "") + " " + f.get("detail", "") for f in findings)


def _endpoints(findings):
    eps = set()
    for f in findings:
        blob = f.get("title", "") + "\n" + f.get("detail", "")
        for m in re.finditer(r"(?<![/:])(/[A-Za-z0-9_\-./{}]{2,80})", blob):
            p = m.group(1)
            if p.startswith("//"):
                continue
            if "." not in p.split("/")[-1] or p.endswith((".json",)):
                eps.add(p)
    return sorted(eps)[:80]


def _intel_context(target):
    """Target-relevant passages from intel reports."""
    ctx = []
    for path in glob.glob(os.path.join(INTEL, "*.md")):
        try:
            text = open(path).read()
        except OSError:
            continue
        if target.lower() in text.lower():
            # keep hypothesis/finding-dense lines
            for line in text.splitlines():
                if re.search(r"hypothes|SH\d|finding|vuln|bypass|inject|idor|"
                             r"token|share|auth", line, re.I) and len(line) < 300:
                    ctx.append(line.strip())
                if len(ctx) > 40:
                    break
    return ctx


def _mk(statement, family, source, reasoning=""):
    return {"statement": statement, "family": family, "source": source,
            "reasoning": reasoning[:300]}


# ---------------------------------------------------------------- modes ---

def predator(findings, profile, mem, intel_ctx):
    """Thinks like the attacker: where is trust assumed? Cross every boundary."""
    out, eps = [], _endpoints(findings)
    for ep in eps[:25]:
        if re.search(r"\{|\bid\b|/user|/doc|/asset|/order|/invoice", ep, re.I):
            out.append(_mk(
                f"[predator] {ep}: trust boundary assumed on object identity — "
                f"request another user's object ID here as attacker (BOLA); "
                f"also try param-swapped and method-overridden variants",
                "authorization", "think:predator",
                "attackers don't read docs, they cross boundaries"))
        if re.search(r"share|invit|collab|space", ep, re.I):
            out.append(_mk(
                f"[predator] {ep}: sharing is a trust boundary — plant hostile "
                f"content/permissions on the attacker side, observe what the "
                f"victim's session trusts (content, instructions, cached data)",
                "ai-llm" if "ai" in profile.get("vuln_classes_text", "") else "authorization",
                "think:predator"))
    return out[:10]


def architect(findings, profile, mem, intel_ctx):
    """Thinks like the dev who built it: what shortcuts did they take?"""
    out, blob = [], _blob(findings).lower()
    shortcuts = [
        ("v2" in blob or "v1" in blob,
         "newer API version tested less than the old one — hunt v2/v3 first"),
        ("debug" in blob or "internal" in blob,
         "debug/internal endpoints shipped to prod — forced-browse them"),
        ("graphql" in blob, "graphQL schema exposes more than REST — introspect"),
        ("mobile" in blob or "sdk" in blob,
         "mobile/SDK surface duplicates web with weaker checks"),
        ("staging" in blob or "dev." in blob,
         "staging/dev hosts with prod data or weaker auth"),
    ]
    for cond, idea in shortcuts:
        if cond:
            out.append(_mk(f"[architect] {idea}", "logic", "think:architect",
                           "devs ship shortcuts; hunters collect them"))
    for line in intel_ctx[:6]:
        if re.search(r"discrepancy|ambiguous|unclear|contradict", line, re.I):
            out.append(_mk(
                f"[architect] doc/behavior discrepancy is a bug smell: {line[:160]}",
                "logic", "think:architect"))
    return out[:8]


def accountant(findings, profile, mem, intel_ctx):
    """Thinks like the accountant: where does value change hands?"""
    out, blob = [], _blob(findings).lower()
    value_words = ["price", "credit", "coupon", "balance", "refund", "quota",
                   "trial", "subscription", "export", "invite", "share"]
    hits = [w for w in value_words if w in blob]
    for w in hits[:6]:
        out.append(_mk(
            f"[accountant] '{w}' moves value — tamper it client-side, race it, "
            f"skip the step before it, replay it; prove with ledger math on "
            f"owned accounts", "business-logic", "think:accountant",
            "follow the money/data; scanners can't"))
    return out[:8]


def saboteur(findings, profile, mem, intel_ctx):
    """Thinks like the saboteur: what breaks if two things happen at once?"""
    out, eps = [], _endpoints(findings)
    stateful = [e for e in eps if re.search(
        r"redeem|revoke|share|invite|verify|reset|upload|delete|update|create",
        e, re.I)]
    for ep in stateful[:8]:
        out.append(_mk(
            f"[saboteur] {ep}: state transition — race it (parallel requests), "
            f"overlap it with its own revoke/undo, reorder the workflow steps "
            f"around it; predict the ledger first, then prove",
            "race", "think:saboteur",
            "time is an attack surface"))
    return out[:8]


def ghost(findings, profile, mem, intel_ctx):
    """Thinks like the ghost: what identifies the user, and where is it NOT checked?"""
    out, blob = [], _blob(findings).lower()
    id_signals = ["token", "session", "jwt", "cookie", "api_key", "sub=",
                  "user_id", "account_id"]
    hits = [s for s in id_signals if s in blob]
    for s in hits[:6]:
        out.append(_mk(
            f"[ghost] identity signal '{s}' observed — map every place it is "
            f"established vs every place it is (not) re-validated: replay "
            f"across users, tamper claims, drop it and see what still works",
            "authentication", "think:ghost",
            "identity is a rumor until re-checked"))
    return out[:8]


def scholar(findings, profile, mem, intel_ctx):
    """The scholar: match evidence against the 39 technique cards."""
    return train.recommend(findings, profile, mem, limit=10)


def oracle(findings, profile, mem, intel_ctx):
    """The oracle: past bounty shapes that keep paying, mapped to this target."""
    out = []
    try:
        text = open(os.path.join(BASE, "knowledge", "past_attacks.md")).read()
    except OSError:
        return out
    blob = _blob(findings).lower()
    shapes = [
        (["api/v2", "v3", "/api"], "new API versions repeat old bugs — test the newest surface first"),
        (["share", "link", "token="], "share-link token shapes — enumerate, replay after revoke"),
        (["graphql"], "GraphQL field-level authz — introspect then test per-field as two users"),
        (["ai", "assistant", "prompt"], "AI trust boundary — indirect injection via shared content"),
        (["webhook", "url=", "import"], "URL-fetch features — SSRF via parser differentials"),
        (["cdn", "cloudflare", "akamai"], "CDN layer — cache poisoning via unkeyed inputs"),
        (["cname"], "dangling DNS — takeover screen already ran; claim per program rules"),
    ]
    for keys, shape in shapes:
        if any(k in blob for k in keys):
            stmt = f"[oracle] {shape}"
            ok, _ = learn.is_novel(stmt, mem)
            if ok:
                out.append(_mk(stmt, "logic", "think:oracle",
                               "vendors fix instances, not classes"))
    for line in intel_ctx[:4]:
        stmt = f"[oracle] intel says: {line[:160]}"
        ok, _ = learn.is_novel(stmt, mem)
        if ok:
            out.append(_mk(stmt, "logic", "think:oracle"))
    return out[:8]


def inquisitor(findings, profile, mem, intel_ctx):
    """The inquisitor: security inference engine. Asks who owns/reads/
    modifies each object and what invariant must hold — finds bugs outside
    the explicit vulnerability catalogue."""
    try:
        from inference import infer
        seeds, summary = infer(findings, profile, mem)
        out = []
        for s in seeds:
            ok, _ = learn.is_novel(s["statement"], mem)
            if ok:
                out.append(_mk(s["statement"], s["family"], "think:inquisitor",
                               s.get("reasoning", "")))
        return out[:8]
    except Exception:  # noqa: BLE001
        return []


def heretic(findings, profile, mem, intel_ctx):
    """The heretic: novel hypothesis generator (update #2). Proposes ONLY
    hypotheses outside the 71 technique cards — from anomalies, combinatorial
    crosses, and feature-graph chains."""
    out = []
    try:
        import novel
        from world_model import WorldModel
        from feature_graph import FeatureGraph
        wm = WorldModel(profile.get("name", "unknown"))
        # anomaly-driven
        out += novel.from_anomalies(wm, mem, learn.is_novel)
        # combinatorial: technique x bias x context
        try:
            import yaml
            biases = yaml.safe_load(open(
                os.path.join(BASE, "knowledge", "biases.yaml"))) or []
        except Exception:  # noqa: BLE001
            biases = []
        out += novel.combinatorial(train.load_techniques(), biases, mem,
                                   learn.is_novel, profile.get("name", ""),
                                   limit=5)
        # chain-driven
        fg = FeatureGraph().build_from_world(wm)
        chains = [fg.describe_chain(c) for c in fg.find_chains()]
        out += novel.from_chains(chains, mem, learn.is_novel)
    except Exception:  # noqa: BLE001
        pass
    return out[:10]


MODES = {
    "predator": predator,
    "architect": architect,
    "accountant": accountant,
    "saboteur": saboteur,
    "ghost": ghost,
    "scholar": scholar,
    "oracle": oracle,
    "inquisitor": inquisitor,
    "heretic": heretic,
}


def council(findings, profile, mem, limit=12):
    """Run all nine modes, kill retreads, diversify, rank. Returns seeds."""
    intel_ctx = _intel_context(profile.get("name", ""))
    pool = []
    for mode_name, mode_fn in MODES.items():
        try:
            for h in mode_fn(findings, profile, mem, intel_ctx) or []:
                h["mode"] = mode_name
                pool.append(h)
        except Exception:  # noqa: BLE001
            continue
    # dedupe against memory AND against each other
    novel, seen = [], []
    for h in pool:
        ok, _ = learn.is_novel(h["statement"], mem)
        if not ok:
            continue
        if any(learn._overlap(h["statement"], s["statement"], 4) for s in seen):
            continue
        novel.append(h)
        seen.append(h)
    # diversify: round-robin across modes, scholar/oracle first (evidence-backed)
    order = {"scholar": 0, "oracle": 1, "inquisitor": 2, "heretic": 3,
             "predator": 4, "ghost": 5, "architect": 6, "accountant": 7,
             "saboteur": 8}
    novel.sort(key=lambda h: (order.get(h.get("mode"), 9),
                              -h.get("score", 0)))
    picked, used_modes = [], set()
    for h in novel:  # first pass: one per mode
        if h["mode"] not in used_modes:
            picked.append(h)
            used_modes.add(h["mode"])
        if len(picked) >= limit:
            break
    for h in novel:  # second pass: fill
        if h not in picked:
            picked.append(h)
        if len(picked) >= limit:
            break
    return picked
