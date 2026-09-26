"""DEEPHUNT differential testing — endgame #5.

Business-logic bugs don't live in single requests; they live in
DIFFERENCES. This module designs and evaluates differential experiments
across the dimensions where logic bugs hide:

    User A vs User B | Role 1 vs Role 2 | auth vs unauth |
    before vs after state change | API v1 vs v2 | Object X vs Y |
    Request A vs modified A

compare() takes two observations and flags only SECURITY-RELEVANT
differences — status changes on protected resources, data leaks, capability
gains — while ignoring benign noise (timestamps, CSRF tokens, ordering).
"""
import re

DIMENSIONS = [
    ("user-a-vs-b", "same request as two different owned users"),
    ("role-vs-role", "same request as two different owned roles"),
    ("auth-vs-anon", "same request authenticated vs unauthenticated"),
    ("before-vs-after", "same object before and after a state change"),
    ("v1-vs-v2", "same operation on API v1 vs v2"),
    ("object-x-vs-y", "same operation on own object vs other-owned object"),
    ("request-vs-modified", "request A vs A with one field mutated"),
]

# noise patterns that must NEVER count as a finding
NOISE = re.compile(
    r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}|csrf|nonce|timestamp|request-?id|"
    r"etag|date:|set-cookie|__session", re.I)

# security-relevant difference signals
SIGNALS = [
    (re.compile(r"\b(200|201)\b.*\b(401|403|404)\b|\b(401|403|404)\b.*\b(200|201)\b"), "status-class change across identities"),
    (re.compile(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", re.I), "email address disclosed"),
    (re.compile(r"\b\d{13,19}\b"), "long numeric id / possible token"),
    (re.compile(r"(password|secret|api[_-]?key|token)\s*[:=]\s*\S+", re.I), "secret material disclosed"),
    (re.compile(r"\b(admin|root|owner)\b", re.I), "privileged marker visible"),
    (re.compile(r"<script[\s>]|on\w+\s*=\s*[\"']|javascript:", re.I), "script injection reflected"),
    (re.compile(r"169\.254\.169\.254|metadata\.google|instance-data", re.I), "cloud metadata address reached"),
]


def _strip_noise(text):
    return NOISE.sub("", text or "")


def compare(obs_a, obs_b, label_a="control", label_b="variant"):
    """Tri-state differential:
      ("identical", ...)   — no difference after noise stripping; no case.
      ("differs", ...)     — real difference, no strong signal; opens a
                             LOW-PRIORITY case the validation pipeline must
                             prove or kill. Differentials find; validation proves.
      ("interesting", ...) — security-relevant difference; opens a case.
    Conservative where it matters: the pipeline + report gate, not this
    function, decide what becomes a finding."""
    a, b = _strip_noise(obs_a), _strip_noise(obs_b)
    if a == b:
        return "identical", ["identical after noise stripping"]
    reasons = []
    for pat, name in SIGNALS:
        in_a, in_b = bool(pat.search(a)), bool(pat.search(b))
        if in_a != in_b:
            reasons.append(f"{name} present in {label_b if in_b else label_a} only")
    if reasons:
        return "interesting", reasons
    if abs(len(a) - len(b)) > 200:
        return "differs", ["large body-size delta without status change — needs validation"]
    return "differs", ["non-noise difference without strong signal — validation decides"]


def design(hypothesis_stmt, wm, limit=5):
    """Generate differential experiment specs for a hypothesis from the
    dimensions list, grounded in entities the world model knows."""
    m = wm.model if wm else {}
    endpoints = sorted({r["frm"] for r in m.get("relations", [])
                        if r["frm"].startswith("/")})[:5]
    objects = [o["name"] for o in m.get("objects", [])][:5]
    specs = []
    for dim, desc in DIMENSIONS:
        if dim == "object-x-vs-y" and len(objects) >= 1:
            target = objects[0]
        elif endpoints:
            target = endpoints[0]
        else:
            continue
        specs.append({
            "dimension": dim,
            "description": desc,
            "target": target,
            "control": f"owned identity, own {target}",
            "variant": f"owned second identity, other-owned {target}",
            "decides": f"{dim}: any security-relevant difference",
            "single_variable": True,
        })
        if len(specs) >= limit:
            break
    return specs
