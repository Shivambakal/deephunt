"""ResearchSession — the ENFORCED agent loop.

Every investigation runs inside a session. The loop is structural, not advisory:

  observe -> hypothesize -> ADVERSARIAL SELF-CHECK -> gate -> execute (token)
  -> record -> learn -> generate -> compete -> stop-check -> repeat

No security/tool action executes unless the agent first produced:
  hypothesis, expected observation, reason, scope/authorization check,
  success/failure criteria.

State persists after every mutation to data/brain/sessions/<id>.json, so
research survives across sessions. Secrets are never persisted.
"""
from __future__ import annotations
import json, os, re, time, uuid

from .gate import GateRefused, TestAuthorization
from . import hypotheses as H
from . import experiments as X
from .model import WorldModel
from .ledger import Ledger

BASE = os.path.expanduser("~/workspace/hacker-agent")
SESSIONS_DIR = os.path.join(BASE, "data", "brain", "sessions")
KNOWLEDGE_PATH = os.path.join(BASE, "data", "brain", "knowledge.json")

# heuristic, documented: blocks values shaped like credentials, not words like "token"
SECRET_PATTERNS = [
    re.compile(r"api[_-]?key\s*[:=]\s*\S{4,}", re.I),
    re.compile(r"secret\s*[:=]\s*\S{4,}", re.I),
    re.compile(r"password\s*[:=]\s*\S{4,}", re.I),
    re.compile(r"bearer\s+\S{10,}", re.I),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\b(ghp_|gho_|sk-live-|xox[bap]-|AKIA)[A-Za-z0-9]{8,}\b"),
]

STOPWORDS = set("the a an and or of to in on for with is are was were be by as at from that this it its they their we you your our".split())
MEANINGFUL_HINTS = ("contradict", "unexpected", "instead", "differs", "but ", "however",
                    "403", "401", "500", "diff", "stale", "cached", "race", "bypass",
                    "leak", "oracle", "desync", "changed", "transition")


def _ts():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _scrub(obj):
    text = json.dumps(obj, default=str)
    for pat in SECRET_PATTERNS:
        if pat.search(text):
            raise ValueError(f"refusing to persist secret-like content (matched {pat.pattern!r})")


def _words(text):
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOPWORDS and len(w) > 3]


def _overlap(a, b, minimum=2):
    return len(set(_words(a or "")) & set(_words(b or ""))) >= minimum


def _new_state(objective):
    return {
        "objective": objective, "created": _ts(), "updated": _ts(),
        "model": {"users": ["anonymous", "user_a", "user_b", "admin"],
                  "objects": [], "trust_boundaries": [], "state_machines": {}},
        "observations": [], "assumptions": [], "hypotheses": [],
        "tests": [], "results": [], "rejected_hypotheses": [],
        "confirmed_findings": [], "unconfirmed_findings": [],
        "facts": [], "lessons": [], "next_actions": [],
    }


class ResearchSession:
    """One investigation. Load by id to resume across sessions."""

    def __init__(self, objective="(untitled)", session_id=None):
        os.makedirs(SESSIONS_DIR, exist_ok=True)
        self.id = session_id or uuid.uuid4().hex[:12]
        self.path = os.path.join(SESSIONS_DIR, f"{self.id}.json")
        if os.path.exists(self.path):
            self.state = json.load(open(self.path))
        else:
            self.state = _new_state(objective)
            self.state["id"] = self.id
        self._engine = None
        self._ledger = Ledger()
        self._save()

    # ---------- persistence ----------
    def _save(self):
        self.state["updated"] = _ts()
        _scrub(self.state)
        tmp = self.path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.state, f, indent=1)
        os.replace(tmp, self.path)

    @staticmethod
    def list_sessions():
        if not os.path.isdir(SESSIONS_DIR):
            return []
        return sorted(f[:-5] for f in os.listdir(SESSIONS_DIR) if f.endswith(".json"))

    # ---------- model ----------
    def define_model(self, objects=None, users=None, boundaries=None, machines=None):
        m = self.state["model"]
        if objects: m["objects"] = objects
        if users: m["users"] = users
        if boundaries: m["trust_boundaries"] = boundaries
        if machines: m["state_machines"] = machines
        self._save()

    def assume(self, believes, enforcement, violated_if, confidence=0.8):
        aid = f"A{len(self.state['assumptions']) + 1}"
        self.state["assumptions"].append({
            "id": aid, "believes": believes, "enforcement": enforcement,
            "violated_if": violated_if, "confidence": confidence})
        self._save()
        return aid

    # ---------- observe + generate ----------
    def observe(self, text, kind="observation", force_generate=False):
        """Record an observation. Meaningful ones auto-generate new hypotheses."""
        obs = {"ts": _ts(), "kind": kind, "text": text}
        self.state["observations"].append(obs)
        new_hyps = []
        if force_generate or self._is_meaningful(text):
            new_hyps = self._generate_from_observation(text)
        self._refresh_next_actions()
        self._save()
        return new_hyps

    @staticmethod
    def _is_meaningful(text):
        t = text.lower()
        return any(h in t for h in MEANINGFUL_HINTS)

    def _world_model(self):
        m = self.state["model"]
        wm = WorldModel(name=self.state["objective"][:48],
                        users=m["users"], objects=m["objects"],
                        trust_boundaries=m["trust_boundaries"],
                        state_machines=m["state_machines"])
        for a in self.state["assumptions"]:
            wm.assume(a["id"], a["believes"], a["enforcement"], a["violated_if"],
                      a.get("confidence", 0.8))
        return wm

    def _generate_from_observation(self, text):
        """Hypotheses from contradictions, surprises, state changes, authz diffs,
        endpoint relations, failed hypotheses, feature interactions — via the
        violation templates, not a checklist."""
        wm = self._world_model()
        if not wm.assumptions:
            return []
        have = {h["statement"] for h in self.state["hypotheses"]}
        fresh = []
        for h in H.rank(H.generate(wm)):
            if h.statement not in have and h.status == "live":
                fresh.append(self._store_hypothesis(h, source=f"generated:{text[:60]}"))
                have.add(h.statement)
            if len(fresh) >= 6:
                break
        return fresh

    def add_hypothesis(self, statement, violated_assumption="", attacker_view="",
                       defender_view="", devil_view="", investigator_test="",
                       killed_by="", impact=3, novelty=3, testability=3):
        h = H._mk(f"H{len(self.state['hypotheses']) + 1}", violated_assumption,
                  statement, attacker_view, defender_view, devil_view,
                  investigator_test, killed_by, impact, novelty, testability)
        return self._store_hypothesis(h, source="manual")

    def _store_hypothesis(self, h, source=""):
        rec = {"id": h.id, "statement": h.statement,
               "violated_assumption": h.violated_assumption,
               "attacker_view": h.attacker_view, "defender_view": h.defender_view,
               "devil_view": h.devil_view, "investigator_test": h.investigator_test,
               "killed_by": h.killed_by, "impact": h.impact, "novelty": h.novelty,
               "testability": h.testability, "score": h.score,
               "status": "live", "source": source, "ts": _ts()}
        self.state["hypotheses"].append(rec)
        return rec

    def _hyp(self, hypothesis_id):
        for h in self.state["hypotheses"]:
            if h["id"] == hypothesis_id:
                return h
        return None

    # ---------- adversarial self-check + gate ----------
    def propose_test(self, hypothesis_id, expected_observation, reason,
                     scope_hosts, auth_basis, success_criteria, failure_criteria,
                     single_variable=True, repeater_spec=None):
        """THE GATE. Raises GateRefused unless every requirement is met AND the
        adversarial second pass approves the experiment."""
        hyp = self._hyp(hypothesis_id)
        if hyp is None:
            raise GateRefused(f"unknown hypothesis {hypothesis_id}: produce the hypothesis first")
        missing = [name for name, val in [
            ("expected_observation", expected_observation), ("reason", reason),
            ("scope_hosts", scope_hosts), ("auth_basis", auth_basis),
            ("success_criteria", success_criteria), ("failure_criteria", failure_criteria)] if not val]
        if missing:
            raise GateRefused(f"gate requirements missing: {', '.join(missing)}")
        if hyp["status"] != "live":
            raise GateRefused(f"hypothesis {hypothesis_id} is {hyp['status']}, not live")

        spec = {"expected_observation": expected_observation, "reason": reason,
                "scope_hosts": list(scope_hosts), "auth_basis": auth_basis,
                "success_criteria": success_criteria, "failure_criteria": failure_criteria,
                "single_variable": single_variable,
                "repeater_spec": repeater_spec or {}}
        approved, review = self._adversarial_review(hyp, spec)
        test_id = f"T{len(self.state['tests']) + 1}"
        test = {"id": test_id, "hypothesis_id": hypothesis_id, "spec": spec,
                "adversarial_review": review,
                "status": "approved" if approved else "rejected",
                "authorization": None, "ts": _ts()}
        if approved:
            test["authorization"] = TestAuthorization(
                test_id=test_id, hypothesis_id=hypothesis_id,
                session_id=self.id, scope_hosts=list(scope_hosts)).__dict__
        self.state["tests"].append(test)
        self._refresh_next_actions()
        self._save()
        if not approved:
            raise GateRefused(f"adversarial self-check rejected the experiment: "
                              f"{'; '.join(review['rejections'])}")
        return test

    def _adversarial_review(self, hyp, spec):
        """Second reasoning pass. Five questions; weak experiments die here."""
        review = {"rejections": [], "warnings": [], "answers": {}}
        ans = review["answers"]

        supporting = [o["text"][:160] for o in self.state["observations"]
                      if _overlap(o["text"], hyp["statement"])]
        ans["supporting_evidence"] = supporting or ["none found in observations"]
        contradicting = [o["text"][:160] for o in self.state["observations"]
                         if hyp.get("killed_by") and _overlap(o["text"], hyp["killed_by"])]
        ans["contradicting_evidence"] = contradicting or ["none found"]
        ans["benign_explanation"] = hyp.get("defender_view") or "no benign explanation recorded"
        ans["smallest_safe_experiment"] = ("single declared variable"
                                           if spec["single_variable"]
                                           else "NOT single-variable: control and variant differ in more than one declared variable")
        already = [r["id"] for r in self.state["results"]
                   if _overlap(r.get("observed", ""), spec["expected_observation"])]
        ans["already_answered_by"] = already or ["no prior result answers this"]

        if already:
            review["rejections"].append(
                f"test is unnecessary: already answered by result(s) {already}")
        if not spec["single_variable"]:
            review["rejections"].append(
                "not the smallest safe experiment: declare exactly one variable changed between control and variant")
        if contradicting and not supporting:
            review["warnings"].append(
                "contradicting evidence exists with no supporting evidence: experiment must be discriminating")
        if not supporting and not contradicting:
            review["warnings"].append(
                "no evidence either way: low prior, keep the experiment minimal")
        info_value = 5 if contradicting else (3 if supporting else 1)
        review["info_value"] = info_value
        if info_value <= 1 and not spec.get("cheap", True):
            review["rejections"].append("information value too low for a non-trivial test")
        return (not review["rejections"]), review

    # ---------- execution (gated) ----------
    def _get_engine(self):
        if self._engine is None:
            from .engine import Engine
            self._engine = Engine(self._world_model())
        return self._engine

    def run_test(self, test_id):
        """Execute ONLY an approved test. The authorization token is what the
        execution layer checks — no token, no packets."""
        test = next((t for t in self.state["tests"] if t["id"] == test_id), None)
        if test is None:
            raise GateRefused(f"unknown test {test_id}")
        if test["status"] != "approved" or not test.get("authorization"):
            raise GateRefused(f"test {test_id} is {test['status']}: gate did not approve it")
        auth_d = test["authorization"]
        auth = TestAuthorization(test_id=auth_d["test_id"], hypothesis_id=auth_d["hypothesis_id"],
                                 session_id=auth_d["session_id"], scope_hosts=auth_d["scope_hosts"],
                                 issued_at=auth_d["issued_at"], minted_by=auth_d["minted_by"],
                                 revoked=auth_d["revoked"], ttl_seconds=auth_d["ttl_seconds"])
        exp = X.discriminate(self._as_hypothesis_obj(test["hypothesis_id"]),
                             context=test["spec"]["repeater_spec"] or None)
        result = self._get_engine().execute(exp, scope_hosts=test["spec"]["scope_hosts"],
                                            authorization=auth)
        test["status"] = "executed"
        test["executed_at"] = _ts()
        self._refresh_next_actions()
        self._save()
        return result

    def _as_hypothesis_obj(self, hypothesis_id):
        h = self._hyp(hypothesis_id)
        class O: pass
        o = O()
        o.id, o.statement, o.violated_assumption = h["id"], h["statement"], h["violated_assumption"]
        o.investigator_test, o.killed_by, o.testability = h["investigator_test"], h["killed_by"], h["testability"]
        return o

    # ---------- record + failure learning ----------
    def record_result(self, test_id, outcome, observed, why_failed="",
                      learned="", false_explanation="", environment="",
                      technology="", preconditions=""):
        """outcome: confirmed | rejected | inconclusive. Rejections MUST carry
        why_failed and learned — failure is stored, never discarded.
        The 10-field lesson format lets future runs retrieve:
        'last time this signal appeared, it was caused by X'."""
        if outcome not in ("confirmed", "rejected", "inconclusive"):
            raise ValueError("outcome must be confirmed|rejected|inconclusive")
        if outcome == "rejected" and not (why_failed and learned):
            raise ValueError("rejected results require why_failed and learned")
        test = next(t for t in self.state["tests"] if t["id"] == test_id)
        hyp = self._hyp(test["hypothesis_id"])
        result = {"id": f"R{len(self.state['results']) + 1}", "test_id": test_id,
                  "hypothesis_id": hyp["id"], "outcome": outcome,
                  "observed": observed, "why_failed": why_failed,
                  "learned": learned, "false_explanation": false_explanation,
                  "environment": environment, "technology": technology,
                  "preconditions": preconditions, "ts": _ts()}
        self.state["results"].append(result)
        self._ledger.record(self._as_hypothesis_obj(hyp["id"]), None, outcome,
                            observed, why_failed)

        followups = []
        if outcome == "rejected":
            hyp["status"] = "rejected"
            entry = {"id": hyp["id"], "statement": hyp["statement"],
                     "believed": hyp["statement"],
                     "tested": test["spec"]["reason"],
                     "observed_result": observed, "why_failed": why_failed,
                     "learned": learned,
                     "false_explanation": false_explanation,
                     "environment": environment, "technology": technology,
                     "preconditions": preconditions,
                     "changes_future": [f["statement"] for f in
                                        self._ledger.derive_followups(
                                            {"hypothesis_id": hyp["id"],
                                             "why_failed": why_failed,
                                             "observation": observed})]}
            self.state["rejected_hypotheses"].append(entry)
            for f in self._ledger.derive_followups(
                    {"hypothesis_id": hyp["id"], "why_failed": why_failed,
                     "observation": observed}):
                followups.append(self.add_hypothesis(
                    f["statement"], violated_assumption=hyp["violated_assumption"],
                    investigator_test=f["investigator_test"]))
            lesson = f"{hyp['id']} rejected: {why_failed} -> learned: {learned}"
            self.state["lessons"].append({"ts": _ts(), "text": lesson})
        elif outcome == "confirmed":
            hyp["status"] = "supported"
            self.state["unconfirmed_findings"].append(
                {"hypothesis_id": hyp["id"], "claim": hyp["statement"],
                 "evidence": observed, "ts": _ts()})
        self._refresh_next_actions()
        self._save()
        return result, followups

    # ---------- calibration gate (update #9) ----------
    def calibrate_finding(self, unconfirmed_idx=0, evidence_for="",
                          best_alternative="", falsifying_experiment="",
                          assumptions=""):
        """Self-evaluation before CONFIRMED is allowed. The researcher must
        answer four questions; empty answers refuse confirmation.

            1. What evidence proves it?
            2. What alternative best explains it?
            3. What experiment would falsify it?
            4. What am I assuming?

        Returns the calibration record; the finding may only be confirmed
        when compete_finding() has disproven every surviving alternative
        AND this calibration is complete.
        """
        if unconfirmed_idx >= len(self.state["unconfirmed_findings"]):
            raise ValueError("no unconfirmed finding at that index")
        answers = {"evidence_for": evidence_for,
                   "best_alternative": best_alternative,
                   "falsifying_experiment": falsifying_experiment,
                   "assumptions": assumptions}
        missing = [k for k, v in answers.items() if not v.strip()]
        if missing:
            raise ValueError(f"calibration refused: unanswered {missing}")
        finding = self.state["unconfirmed_findings"][unconfirmed_idx]
        finding["calibration"] = {**answers, "ts": _ts()}
        self._save()
        return finding["calibration"]

    def confirm_finding(self, unconfirmed_idx=0):
        """CONFIRMED only when: competition killed every alternative AND
        the 4-question calibration is on record."""
        if unconfirmed_idx >= len(self.state["unconfirmed_findings"]):
            raise ValueError("no unconfirmed finding at that index")
        finding = self.state["unconfirmed_findings"][unconfirmed_idx]
        comp = finding.get("competition", {})
        if comp.get("surviving"):
            raise ValueError(f"cannot confirm: {len(comp['surviving'])} "
                             f"alternatives still survive — disprove them first")
        if "calibration" not in finding:
            raise ValueError("cannot confirm: calibration questions unanswered — "
                             "call calibrate_finding() first")
        finding["status"] = "confirmed"
        self.state["confirmed_findings"].append(finding)
        self.state["unconfirmed_findings"].pop(unconfirmed_idx)
        self._refresh_next_actions()
        self._save()
        return finding

    # ---------- hypothesis competition ----------
    def compete_finding(self, unconfirmed_idx=0):
        """For a supported finding, generate competing explanations and try to
        disprove each before it may become confirmed."""
        if unconfirmed_idx >= len(self.state["unconfirmed_findings"]):
            raise ValueError("no unconfirmed finding at that index")
        finding = self.state["unconfirmed_findings"][unconfirmed_idx]
        claim = finding["claim"]
        alternatives = [
            f"Benign: the observed behavior is legitimate ({claim[:60]}... has a non-security explanation).",
            f"Artifact: the observation is a test artifact — cache, stale session, wrong account, or timing noise.",
            f"Misattribution: the effect is real but caused by a different component than hypothesized.",
            f"Scope error: the test crossed an authorization boundary it should not have.",
        ]
        facts = " ".join(self.state["facts"] + [o["text"] for o in self.state["observations"]])
        disproven, surviving = [], []
        for alt in alternatives:
            if _overlap(alt, facts) and "not" in facts.lower():
                disproven.append({"explanation": alt, "disproven_by": "existing facts/observations"})
            else:
                surviving.append({"explanation": alt,
                                  "disproof_test_needed": True})
        finding["competition"] = {"alternatives": alternatives, "disproven": disproven,
                                  "surviving": surviving, "ts": _ts()}
        if not surviving:
            # competition won — but CONFIRMED still requires the calibration
            # gate (update #9): answer the 4 questions, then confirm_finding()
            finding["status"] = "awaiting-calibration"
            self.state["next_actions"].append(
                f"calibrate '{finding['claim'][:60]}...': evidence? alternative? "
                f"falsifier? assumptions? then confirm_finding()")
        else:
            finding["status"] = "awaiting-disproof"
            for s in surviving:
                self.state["next_actions"].append(
                    f"disproof test needed for '{finding['claim'][:50]}...': {s['explanation'][:80]}")
        self._refresh_next_actions()
        self._save()
        return finding

    # ---------- stop conditions ----------
    def should_stop(self):
        """Stop when: disproven / sufficient evidence / low info value /
        scope uncertain / unsafe validation."""
        live = [h for h in self.state["hypotheses"] if h["status"] == "live"]
        if self.state["hypotheses"] and not live and not self.state["unconfirmed_findings"]:
            return True, "hypothesis disproven: no live hypotheses and nothing awaiting disproof"
        if self.state["confirmed_findings"] and not self.state["unconfirmed_findings"]:
            pending = [t for t in self.state["tests"] if t["status"] == "approved"]
            if not pending:
                return True, "evidence sufficient: finding confirmed, no pending tests"
        approved_unrun = [t for t in self.state["tests"] if t["status"] == "approved"]
        if approved_unrun and all(
                t.get("adversarial_review", {}).get("info_value", 3) <= 1 for t in approved_unrun):
            return True, "next tests have low information value"
        for t in self.state["tests"]:
            if t["status"] in ("approved", "executed") and not t["spec"].get("scope_hosts"):
                return True, f"scope/authorization uncertain on {t['id']}: halt"
        return False, ""

    # ---------- next actions ----------
    def _refresh_next_actions(self):
        actions = []
        for t in self.state["tests"]:
            if t["status"] == "approved":
                actions.append(f"run {t['id']} (hypothesis {t['hypothesis_id']})")
        for h in self.state["hypotheses"]:
            if h["status"] == "live" and not any(
                    t["hypothesis_id"] == h["id"] for t in self.state["tests"]):
                actions.append(f"design test for {h['id']}: {h['statement'][:70]}...")
        for f in self.state["unconfirmed_findings"]:
            if f.get("status") == "awaiting-disproof":
                actions.append(f"disprove alternatives for '{f['claim'][:60]}...'")
        # keep user-added disproof actions, drop stale auto ones
        keep = [a for a in self.state["next_actions"]
                if a.startswith("disproof test needed") or a.startswith("USER:")]
        self.state["next_actions"] = keep + actions

    # ---------- cross-session knowledge ----------
    def export_knowledge(self):
        """Merge durable facts/lessons/confirmed findings into knowledge.json."""
        kb = {"facts": [], "lessons": [], "confirmed_findings": []}
        if os.path.exists(KNOWLEDGE_PATH):
            kb = json.load(open(KNOWLEDGE_PATH))
        for section in ("facts", "lessons"):
            seen = {json.dumps(x, sort_keys=True) for x in kb[section]}
            for x in self.state[section]:
                key = json.dumps(x, sort_keys=True)
                if key not in seen:
                    kb[section].append(x)
                    seen.add(key)
        seen = {f["claim"] for f in kb["confirmed_findings"]}
        for f in self.state["confirmed_findings"]:
            if f["claim"] not in seen:
                kb["confirmed_findings"].append(
                    {"claim": f["claim"], "evidence": f["evidence"],
                     "session": self.id, "ts": f["ts"]})
                seen.add(f["claim"])
        _scrub(kb)
        tmp = KNOWLEDGE_PATH + ".tmp"
        json.dump(kb, open(tmp, "w"), indent=1)
        os.replace(tmp, KNOWLEDGE_PATH)
        return kb
