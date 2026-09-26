"""DEEPHUNT attack-chain engine — endgame #4.

Individual bugs are commodities; CHAINS win bounties. This engine composes
multi-step attack paths from the world model + feature graph:

    minor weakness -> privilege boundary -> another feature ->
    different identity/state -> unexpected capability -> real impact

Each link is independently testable (differential), and the chain only
"completes" when every link is evidenced. A chain with one unproven link
is a hypothesis, not a finding — this is what makes it hard to fool.
"""
from feature_graph import FeatureGraph, _PRIV

# impact sinks: capabilities that turn a chain into a real finding
IMPACT_SINKS = {
    "read-other-user-data": 5, "modify-other-user-data": 5,
    "privilege-escalation": 5, "auth-bypass": 4,
    "write-privileged-object": 4, "ssrf-internal": 4,
    "state-confusion": 3, "info-disclosure": 3,
}

# weak-link primitives the engine looks for at chain starts
WEAK_LINKS = [
    ("accepts-param", "attacker-controlled input"),
    ("exposes", "reachable surface"),
    ("reads", "data flow"),
    ("calls", "server-side request"),
]


class AttackChain:
    def __init__(self, links, sink):
        self.links = links          # [(frm, kind, to), ...]
        self.sink = sink            # impact sink name
        self.evidenced = [False] * len(links)
        self.impact = IMPACT_SINKS.get(sink, 1)

    def evidence_link(self, idx, evidence):
        self.evidenced[idx] = evidence[:200]

    @property
    def complete(self):
        return all(self.evidenced)

    @property
    def proven_prefix(self):
        n = 0
        for e in self.evidenced:
            if e:
                n += 1
            else:
                break
        return n

    def score(self):
        # shorter proven prefix + higher impact + boundary crossings rank up
        crossings = sum(1 for (_, k, _) in self.links if k in
                        ("accepts-param", "owns", "writes"))
        return round(self.impact * (1 + 0.3 * crossings) /
                     (1 + 0.2 * len(self.links)), 2)

    def describe(self):
        steps = " -> ".join(f"{a} --{k}--> {b}" for (a, k, b) in self.links)
        return f"[chain->{self.sink}] {steps}"

    def next_untested(self):
        for i, e in enumerate(self.evidenced):
            if not e:
                return i, self.links[i]
        return None, None


def build_chains(wm, limit=8):
    """Compose candidate chains from the live feature graph. Returns
    AttackChain objects ordered by score."""
    fg = FeatureGraph().build_from_world(wm)
    chains = []
    # start from every weak link, walk toward privilege boundaries
    for (frm, to, kind) in fg.edges:
        if kind not in [w[0] for w in WEAK_LINKS]:
            continue
        # walk up to 4 more hops looking for a boundary crossing
        for target in [n for n, a in fg.nodes.items()
                       if a["kind"] == "object"]:
            for path in fg._paths(to, target, 3):
                nodes = [p if isinstance(p, str) else p[0] for p in path]
                if fg._crosses_boundary([frm] + nodes):
                    links = [(frm, kind, to)]
                    for i in range(len(path) - 1):
                        a = path[i] if isinstance(path[i], str) else path[i][0]
                        b, k = path[i + 1] if isinstance(path[i + 1], tuple) \
                            else (path[i + 1], "?"), None
                        if isinstance(path[i + 1], tuple):
                            b, k = path[i + 1]
                        links.append((a, k or "reaches", b))
                    sink = _sink_for(target, fg)
                    chains.append(AttackChain(links, sink))
    # dedupe by description, keep best
    seen, uniq = set(), []
    for c in sorted(chains, key=lambda c: -c.score()):
        d = c.describe()
        if d not in seen:
            seen.add(d)
            uniq.append(c)
        if len(uniq) >= limit:
            break
    return uniq


def _sink_for(target, fg):
    attrs = fg.nodes.get(target, {})
    if attrs.get("kind") == "object":
        return "read-other-user-data"
    return "info-disclosure"


def chains_as_hypotheses(chains, mem, is_novel, limit=4):
    """Chains become hypotheses: test the next unproven link."""
    out = []
    for c in chains:
        idx, link = c.next_untested()
        if link is None:
            continue  # fully proven — handled as a finding, not hypothesis
        stmt = (f"[chain] {c.describe()}. NEXT UNPROVEN LINK #{idx + 1}: "
                f"prove '{link[0]} --{link[1]}--> {link[2]}' with a "
                f"differential test (control vs variant, owned identities).")
        ok, _ = is_novel(stmt, mem)
        if ok:
            out.append({"statement": stmt, "family": "chain",
                        "source": "chain-engine",
                        "reasoning": f"link {idx + 1}/{len(c.links)} unproven; "
                                     f"sink impact {c.impact}",
                        "score": 5, "_chain": c})
        if len(out) >= limit:
            break
    return out
