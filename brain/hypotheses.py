"""HYPOTHESIS LOOP + ADVERSARIAL LOOP.

Generate 10+ hypotheses from violated assumptions, then make them fight:
ARCHITECT names the trust, ATTACKER violates it, DEFENDER defends it,
DEVIL'S ADVOCATE tries to kill it, INVESTIGATOR names the distinguishing test.
"""
from __future__ import annotations
from dataclasses import dataclass
import re


def _dedupe(hyps):
    """Kill duplicates: same violated idea restated under another assumption."""
    seen, out = set(), []
    for h in hyps:
        key = "".join(c for c in h.statement.lower() if c.isalnum() or c.isspace())
        key = " ".join(key.split())
        if key not in seen:
            seen.add(key)
            out.append(h)
    for i, h in enumerate(out, 1):  # renumber after kills
        h.id = f"H{i}"
    return out


def _specificity(h):
    """Concrete markers (paths, files, flags, versions) beat generic wording."""
    text = h.statement + " " + h.investigator_test
    markers = re.findall(r"/[a-z0-9_\-./]+|\b[a-z_]+\.[a-z]{2,4}\b|[A-Z][A-Z_]{3,}|v\d+/", text)
    return len(set(markers))


@dataclass
class Hypothesis:
    id: str
    statement: str
    violated_assumption: str
    attacker_view: str
    defender_view: str
    devil_view: str
    investigator_test: str
    killed_by: str = ""
    impact: int = 3
    novelty: int = 3
    testability: int = 3
    status: str = "live"

    @property
    def score(self):
        return self.impact * self.novelty * self.testability


def _mk(hid, violated, statement, attacker, defender, devil, test, killed_by,
        impact=3, novelty=3, testability=3):
    return Hypothesis(hid, statement, violated, attacker, defender, devil, test,
                      killed_by, impact, novelty, testability)


# ---- assumption-violation templates: (assumption, model) -> [Hypothesis] ----
def t_alternate_channel(a, m, n):
    objs = ", ".join(m.objects[:3]) or "the object"
    return [_mk(f"H{n}", a.id,
        f"Same object ({objs}) is reachable through a different verb, endpoint, or "
        f"content-type that skips the enforcement at '{a.enforcement}'.",
        f"Violate the assumption by leaving the guarded channel and entering an unguarded one.",
        "The alternate channel may enforce the same rule at a different layer, or the object may not exist there.",
        "The 'alternate channel' might require stronger auth, making this a downgrade that never reaches the check.",
        "Fire the same logical action through GET vs POST vs PUT vs PATCH vs a versioned path; compare outcomes.",
        "All channels enforce the check identically.",
        impact=4, novelty=4, testability=5)]


def t_cross_feature(a, m, n):
    return [_mk(f"H{n}", a.id,
        f"A value written in one feature is consumed/rendered in another without "
        f"re-running the validation done at '{a.enforcement}'.",
        "Write where validation is weak, execute where trust is high (stored XSS, formula injection, template render).",
        "The consuming feature may sanitize on render; writing is not exploiting.",
        "The two features may share the same validation pipeline, so nothing is skipped.",
        "Write a probe payload in the weakest input, then observe every surface that renders it (list, export, notification, API).",
        "Every renderer neutralizes the payload.",
        impact=4, novelty=5, testability=4)]


def t_state_desync(a, m, n):
    states = "; ".join(f"{k}: {' -> '.join(v)}" for k, v in list(m.state_machines.items())[:2])
    return [_mk(f"H{n}", a.id,
        f"A state transition ({states or 'e.g. publish/delete'}) leaves stale state: "
        f"the system believes the old state, another layer believes the new one.",
        "Act on the object in the window where two layers disagree (scheduled publish to a deleted board, cached public copy of a re-secreted object).",
        "Caches and schedules are eventually consistent; a brief stale window is not a vulnerability.",
        "The transition may be atomic across layers, so no window exists.",
        "Force the transition, then immediately probe every layer (API, unauthenticated cache, export, search index).",
        "All layers agree within the probe window.",
        impact=3, novelty=5, testability=4)]


def t_trust_mismatch(a, m, n):
    bounds = ", ".join(m.trust_boundaries[:3]) or ["browser->API"]
    return [_mk(f"H{n}", a.id,
        f"Upstream validates at '{a.enforcement}', but a downstream component across "
        f"a trust boundary ({bounds}) trusts the value under different rules.",
        "Find where validation and consumption disagree (client-side vs server-side, API vs webhook, SSO claim vs local session).",
        "Defense in depth may re-validate downstream; one layer's trust is not the system's trust.",
        "The boundary may carry a signed/verified token, so downstream trust is justified.",
        "Tamper the value at the boundary (proxy match/replace) and watch whether downstream re-validates.",
        "Downstream rejects the tampered value.",
        impact=4, novelty=4, testability=4)]


def t_type_confusion(a, m, n):
    return [_mk(f"H{n}", a.id,
        f"An identifier is normalized differently by the layer that checks '{a.enforcement}' "
        f"and the layer that uses it (case, encoding, numeric-vs-string, trailing slash, unicode).",
        "Supply two spellings of the same identity: one that passes the check, one that resolves to the target.",
        "Canonicalization may happen before the check, collapsing both spellings to the same value.",
        "The identifier may be an opaque UUID where normalization is a no-op.",
        "Send case/encoding/whitespace variants of a known-good and a known-bad identifier; compare accept/reject matrices.",
        "All variants behave identically.",
        impact=3, novelty=4, testability=5)]


def t_time_window(a, m, n):
    return [_mk(f"H{n}", a.id,
        f"Check-then-use gap: authorization is verified at time T1 at '{a.enforcement}', "
        f"but the action executes at T2 against state that changed between.",
        "Change the state (ownership, role, allowlist, token scope) between the check and the use; double-submit destructive actions.",
        "The check and the use may be in one atomic transaction.",
        "Rate limits or idempotency keys may collapse the window.",
        "Perform check, mutate the underlying state, then complete the action; also double-submit the destructive step.",
        "The action fails or re-checks after the state change.",
        impact=4, novelty=3, testability=3)]


def t_error_oracle(a, m, n):
    objs = ", ".join(m.objects[:3]) or "the object"
    return [_mk(f"H{n}", a.id,
        f"Distinguishable errors/timings around '{a.enforcement}' leak existence or state of {objs} to an unauthorized user.",
        "Probe existing-but-forbidden vs nonexistent and build a differential oracle (status, message, timing).",
        "Error messages may be uniform; timing may be noise.",
        "The endpoint may not be reachable by the probing user at all.",
        "Probe a known-existing-forbidden, a known-nonexistent, and an unknown target; diff status/message/timing.",
        "All three probes are indistinguishable.",
        impact=2, novelty=3, testability=5)]


def t_arithmetic_drift(a, m, n):
    return [_mk(f"H{n}", a.id,
        f"Client-visible arithmetic (credits, quotas, counts) can be desynced from the "
        f"server's bookkeeping that '{a.enforcement}' relies on.",
        "Drive the counter through lifecycle events (create/delete empty objects, retries, back-button resubmits) and watch for drift.",
        "Counters are server-computed; the client display is cosmetic.",
        "Idempotency may prevent double-counting.",
        "Cycle the lifecycle event repeatedly and compare the counter before/after against the expected delta.",
        "The counter always matches the expected arithmetic.",
        impact=3, novelty=4, testability=4)]


TEMPLATES = [t_alternate_channel, t_cross_feature, t_state_desync, t_trust_mismatch,
             t_type_confusion, t_time_window, t_error_oracle, t_arithmetic_drift]


def generate(model, min_count=10, max_count=24):
    """Generate hypotheses by violating every assumption through every template."""
    hyps, n = [], 1
    for a in model.assumptions:
        for t in TEMPLATES:
            for h in t(a, model, n):
                hyps.append(h)
                n += 1
                if len(hyps) >= max_count:
                    return _dedupe(hyps)
    # ensure 10+: if few assumptions, cross templates with users x objects
    while len(hyps) < min_count and model.assumptions:
        a = model.assumptions[len(hyps) % len(model.assumptions)]
        for u in model.users:
            if len(hyps) >= min_count:
                break
            hyps.append(_mk(f"H{n}", a.id,
                f"User '{u}' reaches past '{a.enforcement}' by replaying another user's "
                f"flow step out of order (session fixation, token reuse, step-skipping).",
                "Violate the assumption that identity is re-bound at every step.",
                "Sessions may be bound to device/IP and re-validated per step.",
                "The flow may be strictly server-driven with no client-controlled step to skip.",
                f"As '{u}', replay/interleave the flow steps of a completed session and diff the outcome.",
                "Every replay is rejected or re-bound.",
                impact=3, novelty=3, testability=4))
            n += 1
    return _dedupe(hyps)


def compete(hyps):
    """ADVERSARIAL LOOP: every hypothesis must survive its defender and its devil.
    Returns (survivors, killed) — killed ones carry the observation that would kill them."""
    survivors, killed = [], []
    for h in hyps:
        # a hypothesis dies in competition only if its own kill-condition is trivially true
        # (i.e. the defender's explanation is already confirmed). Otherwise it stays live
        # but carries its devil + kill-condition into the experiment plan.
        if h.defender_view.startswith("CONFIRMED:"):
            h.status = "killed"
            killed.append(h)
        else:
            survivors.append(h)
    return survivors, killed


def _family(h):
    """Which violation template produced this hypothesis (inferred from shape)."""
    s = h.statement.lower()
    if s.startswith("same object"): return "alternate_channel"
    if s.startswith("a value written"): return "cross_feature"
    if s.startswith("a state transition"): return "state_desync"
    if s.startswith("upstream validates"): return "trust_mismatch"
    if s.startswith("an identifier"): return "type_confusion"
    if s.startswith("check-then-use"): return "time_window"
    if s.startswith("distinguishable"): return "error_oracle"
    if s.startswith("client-visible arithmetic"): return "arithmetic_drift"
    return "session_replay"


def rank(hyps, diversify=True):
    """Rank by (impact x novelty x testability) + specificity bonus for concrete
    hypotheses; ties break toward most testable. Diversified: the top of the list
    covers different violation families before repeating one, so 10 hypotheses
    don't read as the same idea 10 times."""
    ordered = sorted(hyps,
                     key=lambda h: (h.score + 2 * _specificity(h), h.testability, h.novelty),
                     reverse=True)
    if not diversify:
        return ordered
    picked, seen, rest = [], set(), []
    for h in ordered:
        fam = _family(h)
        if fam not in seen:
            picked.append(h)
            seen.add(fam)
        else:
            rest.append(h)
    return picked + rest
