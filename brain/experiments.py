"""EXPERIMENT LOOP: smallest experiment that maximizes information.

Every experiment is a discriminating A/B: two requests differing in exactly one
variable, with stated expectations for both outcomes. The spec is repeater-ready
(see ../proxy/repeater.py --send --method/--header/--param/--body).
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Experiment:
    id: str
    hypothesis_id: str
    goal: str
    variant_a: str            # control
    variant_b: str            # exactly one variable changed
    expect_if_true: str
    expect_if_false: str
    repeater_spec: dict = field(default_factory=dict)
    info_gain: int = 3

    def to_repeater_args(self, include_send=True):
        s = self.repeater_spec
        args = []
        if include_send:
            args.append("--send")
        if s.get("base_seq") is not None:
            args += ["--seq", str(s["base_seq"])]
        args += ["--method", s.get("method", "GET")]
        for k, v in s.get("headers", {}).items():
            args += ["--header", f"{k}: {v}"]
        for k, v in s.get("params", {}).items():
            args += ["--param", f"{k}={v}"]
        if s.get("body"):
            args += ["--body", s["body"]]
        if s.get("content_type"):
            args += ["--content-type", s["content_type"]]
        return args


# The 403/400 diagnosis ladder: when an experiment fails, the failure itself is
# an observation. Each rung names the distinguishing test.
CONTRADICTION_LADDER = [
    ("authorization check", "replay the identical request as the resource owner; if it succeeds, the rung is authz"),
    ("WAF / block", "replay with a benign payload of identical shape; if it succeeds, the rung is the WAF"),
    ("different backend", "compare response headers, timing, and error schema against a known-good route"),
    ("missing parameter", "replay adding one suspected parameter at a time until the error changes"),
    ("session state", "replay in a fresh session vs the current session; if fresh works, the rung is state"),
    ("API version difference", "replay against the other API version (v1/v2, web/v5) with the same credentials"),
    ("cache", "replay with cache-busters and after the TTL window; if it flips, the rung is cache"),
]


def discriminate(h, context=None):
    """Design the minimum experiment that kills or confirms one hypothesis.

    context (optional) makes the experiment concrete instead of generic:
      target_url, method, headers, params, body, content_type,
      control, variant, expect_if_true, expect_if_false
    """
    ctx = context or {}
    base = {
        "method": ctx.get("method", "GET"),
        "url": ctx.get("target_url", "<target-url>"),
        "base_seq": ctx.get("base_seq"),   # logged proxy request to mutate; None = plan only
        "headers": ctx.get("headers", {}),
        "params": ctx.get("params", {}),
        "body": ctx.get("body", ""),
        "content_type": ctx.get("content_type", ""),
    }
    if ctx.get("control") and ctx.get("variant"):
        a, b = ctx["control"], ctx["variant"]
        exp_true = ctx.get("expect_if_true",
                           f"Variants diverge: {h.violated_assumption} is violated as described.")
        exp_false = ctx.get("expect_if_false",
                            f"Variants behave identically: {h.killed_by or 'the check holds everywhere'}.")
    else:
        text = (h.statement + " " + h.investigator_test).lower()
        if "patch" in text or "verb" in text or "alternate channel" in text:
            base["method"] = "PATCH"
            a, b = "GET the object as owner (control: ownership enforced?)", \
                   "PATCH the same object as non-owner (one variable changed: verb + identity)"
        elif "error" in text or "oracle" in text or "distinguishable" in text:
            a, b = "probe a known-existing but forbidden target", \
                   "probe a known-nonexistent target (one variable changed: existence)"
        elif "state" in text or "stale" in text or "transition" in text:
            a, b = "probe the object before the transition", \
                   "probe the same object immediately after the transition (one variable changed: state)"
        elif "time" in text or "window" in text or "double" in text:
            a, b = "complete the action with no state change between check and use", \
                   "mutate the underlying state between check and use (one variable changed: timing)"
        else:
            a, b = "perform the action through the guarded channel as the low-privilege user", \
                   "perform the same logical action through the alternate channel (one variable changed: channel)"
        exp_true = f"Variants diverge: {h.violated_assumption} is violated as described."
        exp_false = f"Variants behave identically: {h.killed_by or 'the check holds everywhere'}."
    return Experiment(
        id=f"E-{h.id}", hypothesis_id=h.id,
        goal=f"Distinguish: {h.statement[:90]}...",
        variant_a=a, variant_b=b,
        expect_if_true=exp_true, expect_if_false=exp_false,
        repeater_spec=base, info_gain=h.testability)


def contradiction(expected, observed):
    """CONTRADICTION DETECTION: expected != observed. Return the ladder of
    alternative explanations, each with the experiment that distinguishes it."""
    out = []
    for i, (rung, test) in enumerate(CONTRADICTION_LADDER, 1):
        out.append({"rung": rung, "distinguishing_test": test, "order": i})
    return {"expected": expected, "observed": observed,
            "verdict": "CONTRADICTION -> investigate, do not retry blindly",
            "alternatives": out}


def select_experiment(hyps, context=None):
    """Pick the single smallest experiment with max information gain:
    highest testability first, then score. One experiment, not a battery."""
    ranked = sorted(hyps, key=lambda h: (h.testability, h.score), reverse=True)
    return discriminate(ranked[0], context) if ranked else None
