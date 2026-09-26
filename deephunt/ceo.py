"""DEEPHUNT CEO / JUDGE — the executive at the top of the hunt.

Implements Shivam's architecture:

    CEO / JUDGE
      WORLD MODEL + STRATEGY + MEMORY/LEARNING
                -> HYPOTHESIS ENGINE
                -> RECON / WEB-API / LOGIC AGENTS -> TOOL POOL (~1000)
                -> EVIDENCE ENGINE
                -> ADVERSARIAL REVIEW
                -> REPRODUCE / VERIFY
                -> FINDING / REPORT

The CEO sets strategy, runs the hypothesis engine, dispatches the three
agent teams over the shared tool pool, then judges every candidate through
evidence -> adversarial review -> independent verification. Nothing becomes
a finding without surviving all three gates, and nothing auto-submits.
"""
from __future__ import annotations
import json
import os
import time

try:
    from world_model import WorldModel
    from episodic import EpisodicMemory
    from toolpool import ToolPool
    from strategy import Strategy
    from agents import ReconAgent, WebAPIAgent, LogicAgent
    from validate import ValidationPipeline
    from report_gate import clear_for_report
    from recovery import RunState
    import think
    import debate as debate_mod
    import chain as chain_mod
except ImportError:  # pragma: no cover
    from .world_model import WorldModel
    from .episodic import EpisodicMemory
    from .toolpool import ToolPool
    from .strategy import Strategy
    from .agents import ReconAgent, WebAPIAgent, LogicAgent
    from .validate import ValidationPipeline
    from .report_gate import clear_for_report
    from .recovery import RunState
    from . import think
    from . import debate as debate_mod
    from . import chain as chain_mod


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class CEO:
    """Owns the hunt end to end. Judge of every finding."""

    def __init__(self, target, profile, max_cycles=2, log=None):
        self.target = target
        self.profile = profile
        self.max_cycles = max_cycles
        self.log = log or (lambda m: print(m, flush=True))
        self.wm = WorldModel(target)
        self.mem = EpisodicMemory(target)
        self.pool = ToolPool()
        self.strategy = Strategy()
        self.pipeline = ValidationPipeline()
        self.state = RunState(target, phase="ceo")

    # -- the run ------------------------------------------------------
    def run(self):
        self.log(f"[ceo] hunt opens on {self.target}")
        plan = self.strategy.choose(self.wm, self.mem, self.profile, self.pool)
        self.log(f"[ceo] strategy: {plan['rationale']}")
        self.state.checkpoint(phase="strategy", focus=plan["focus"])

        all_findings, judged = [], []
        for cycle in range(1, self.max_cycles + 1):
            self.log(f"[ceo] cycle {cycle}/{self.max_cycles}")
            self.state.checkpoint(phase=f"cycle-{cycle}-start", n=cycle)

            # 1. HYPOTHESIS ENGINE — council + chains over live model state
            seeds = self._hypothesize(all_findings)
            # 2. AGENT TEAMS over the tool pool
            findings = self._dispatch(seeds)
            all_findings.extend(findings)
            # 3. LEARNING — every observation folds into model + memory
            self._learn(findings)
            self.state.checkpoint(phase=f"cycle-{cycle}-done",
                                  findings=len(findings))
            if self._dry(all_findings):
                self.log("[ceo] dry cycle — no novel hypotheses; standing down")
                break

        # 4. EVIDENCE ENGINE — interesting -> validation cases
        cases = self._evidence(all_findings)
        # 5. ADVERSARIAL REVIEW — six-role debate on every case
        survivors = self._adversarial(cases, all_findings)
        # 6. REPRODUCE / VERIFY + 7. JUDGE -> findings ready for human
        report = self._judge(survivors)
        self.state.complete()
        return report

    # -- stages --------------------------------------------------------
    def _hypothesize(self, findings):
        seeds = []
        try:
            seeds += think.council(findings, self.profile, self.mem, limit=10)
        except Exception as e:  # noqa: BLE001
            self.log(f"[ceo] council failed: {e}")
        try:
            chains = chain_mod.build_chains(self.wm, limit=6)
            seeds += chain_mod.chains_as_hypotheses(
                chains, self.mem, lambda s: True, limit=4)
        except Exception as e:  # noqa: BLE001
            self.log(f"[ceo] chain hypotheses failed: {e}")
        return seeds

    def _dispatch(self, seeds):
        ctx = {"profile": self.profile, "wm": self.wm,
               "target": self.target, "state": {}}
        out = []
        for agent_cls in (ReconAgent, WebAPIAgent, LogicAgent):
            agent = agent_cls(self.pool, ctx)
            try:
                if agent.team == "logic":
                    out += agent.run(hypotheses=seeds)
                else:
                    out += agent.run()
            except Exception as e:  # noqa: BLE001
                self.log(f"[ceo] {agent.team} team crashed: {e}")
        self.log(f"[ceo] teams returned {len(out)} findings "
                 f"(recon/webapi/logic)")
        return out

    def _learn(self, findings):
        if not findings:
            return
        try:
            self.wm.ingest(findings)
            self.wm.save()
        except Exception as e:  # noqa: BLE001
            self.log(f"[ceo] world-model ingest failed: {e}")
        for f in findings[:25]:
            try:
                self.mem.record(
                    observation=f.get("title", "")[:300],
                    technique=f.get("tool", "unknown"),
                    evidence=f.get("evidence", "")[:500],
                    result=f.get("kind", ""),
                    lesson=f.get("detail", "")[:300])
            except Exception:
                continue

    def _dry(self, findings):
        anomalies = (self.wm.model.get("anomalies", []) if hasattr(
            self.wm, "model") else [])
        return len(anomalies) == 0 and not any(
            f.get("kind") in ("anomaly", "interesting") for f in findings[-20:])

    def _evidence(self, findings):
        cases = []
        for i, f in enumerate(findings):
            if f.get("kind") in ("error", "skipped"):
                continue
            title = (f.get("title") or "").lower()
            if not any(k in title for k in (
                    "vuln", "xss", "sqli", "idor", "bypass", "secret",
                    "inject", "ssrf", "takeover", "exposed", "interesting",
                    "anomaly", "misconfig")):
                continue
            cid = f"ceo-{self.target}-{i}"
            try:
                self.pipeline.open(cid, f.get("detail", "")[:2000])
                self.pipeline.advance(cid, {"tool": f.get("tool"),
                                            "evidence": f.get("evidence", "")})
                cases.append((cid, f))
            except Exception:
                continue
        self.log(f"[ceo] evidence engine opened {len(cases)} cases")
        return cases

    def _adversarial(self, cases, findings):
        survivors = []
        for cid, f in cases:
            seed = {"statement": f.get("title", ""),
                    "reasoning": f.get("detail", "")[:500]}
            try:
                judged = debate_mod.debate([seed], findings, self.wm,
                                           self.mem, top_n=1)
                verdict = (judged[0].get("debate", {}).get("verdict", "")
                           if judged else "")
            except Exception:
                verdict = ""
            if verdict.upper() == "PROCEED":
                survivors.append((cid, f))
            else:
                try:
                    self.pipeline.kill(cid, f"debate verdict: {verdict}")
                except Exception:
                    pass
        self.log(f"[ceo] adversarial review: {len(survivors)}/{len(cases)} "
                 "survive")
        return survivors

    def _judge(self, survivors):
        ready, held = [], []
        scope = self.profile.get("scope_hosts", [])
        for cid, f in survivors:
            case = {"id": cid, "stages": {}, "evidence": [f.get("evidence", "")],
                    "assumptions": ["tool output, not yet human-verified"],
                    "authorization": self.profile.get("auth_basis",
                                                      "authorized scope only")}
            ok, reasons = clear_for_report(case, scope_hosts=scope)
            if ok:
                ready.append({"case": cid, "title": f.get("title"),
                              "tool": f.get("tool")})
            else:
                held.append({"case": cid, "reasons": reasons})
        report = {
            "target": self.target, "ts": _now(),
            "strategy": self.strategy.choose(
                self.wm, self.mem, self.profile, self.pool)["rationale"],
            "ready_for_human": ready, "held": held,
            "pool": self.pool.stats(),
        }
        path = os.path.expanduser(
            f"~/workspace/hacker-agent/deephunt/logs/ceo-{self.target}-"
            f"{int(time.time())}.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            json.dump(report, fh, indent=2)
        self.log(f"[ceo] JUDGE: {len(ready)} ready for human, "
                 f"{len(held)} held. report -> {path}")
        return report
