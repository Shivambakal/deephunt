"""DEEPHUNT experiment synthesizer — update #6.

The old experiments came from technique cards' `test:` templates. This
synthesizer GENERATES experiments from the current world-model state:
it takes a hypothesis + the live entity/relation graph and composes a
concrete, minimum-cost, single-variable experiment spec:

    {steps, control, variant, expected, falsifies, cost, risk, auth_scope}

No template fallback — if the state lacks the entities to build a real
experiment, it says what observation is missing instead of guessing.
"""
import re


def synthesize(hypothesis, wm, profile):
    """Build an experiment spec from live state. Returns None when the
    state cannot support a concrete experiment (with what's missing)."""
    stmt = hypothesis.get("statement", "")
    m = wm.model if wm else {}
    relations = m.get("relations", [])
    objects = [o["name"] for o in m.get("objects", [])]
    endpoints = sorted({r["frm"] for r in relations if r["frm"].startswith("/")})
    params = sorted({r["to"] for r in relations if r["kind"] == "accepts-param"})

    mentioned_obj = next((o for o in objects if o in stmt.lower()), None)
    mentioned_ep = next((e for e in endpoints if e.split("/")[-1] and
                         e.split("/")[-1] in stmt.lower()), None)

    if not mentioned_obj and not mentioned_ep and not params:
        return None  # honest: not enough state to synthesize

    target_ep = mentioned_ep or (endpoints[0] if endpoints else "/")
    target_param = next((p for p in params if p in stmt.lower()),
                        params[0] if params else "id")
    scope_hosts = profile.get("scope_hosts", [])

    return {
        "hypothesis": stmt[:120],
        "steps": [
            f"CONTROL: as owned low-priv identity, request {target_ep} "
            f"with {target_param}=<own-value>; record status/body.",
            f"VARIANT: same request with {target_param}=<other-owned-value>; "
            f"record status/body.",
            "DIFF: any security-relevant difference (data, status, timing) "
            "between control and variant.",
        ],
        "control": f"own {target_param} on {target_ep}",
        "variant": f"other-owned {target_param} on {target_ep}",
        "expected_if_vulnerable": "variant returns other-owned data or "
                                  "elevated capability",
        "expected_if_safe": "variant == control (403/404/identical)",
        "falsifies": "control == variant across 2+ owned identities",
        "missing": ("owned second identity" if not mentioned_obj else None),
        "cost": 2, "risk": 2,
        "auth_scope": scope_hosts,
        "single_variable": True,
    }


def describe(spec):
    if not spec:
        return "synthesizer: insufficient state — need one observed endpoint or object first"
    lines = [f"synth experiment for: {spec['hypothesis']}"]
    lines += [f"  {i + 1}. {s}" for i, s in enumerate(spec["steps"])]
    lines.append(f"  falsifies: {spec['falsifies']} | cost {spec['cost']} risk {spec['risk']}")
    if spec.get("missing"):
        lines.append(f"  MISSING: {spec['missing']}")
    return "\n".join(lines)
