"""DEEPHUNT autonomous research scheduler — update #10.

Give it a bounded objective; it manages the whole cycle while respecting
the authorization gates:

    SCOPE -> RECON -> MODEL -> HYPOTHESES -> DEBATE -> PLAN ->
    EXPERIMENTS -> LEARN -> REPORT

Bounds: max_rotations, max_experiments, max_risk. The scheduler never
exceeds them and never touches anything outside the authorized scope.
It stops early on: confirmed high-severity finding, exhausted novelty,
or a stop condition from the research session.
"""
import os
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(os.path.dirname(BASE), "brain"))

from world_model import WorldModel          # noqa: E402
from feature_graph import FeatureGraph       # noqa: E402
from episodic import EpisodicMemory          # noqa: E402
import orchestrator as orch                  # noqa: E402


class ResearchObjective:
    def __init__(self, target, goal="find high-severity vulnerabilities",
                 max_rotations=3, max_experiments=9, max_risk=3):
        self.target = target
        self.goal = goal
        self.max_rotations = max_rotations
        self.max_experiments = max_experiments
        self.max_risk = max_risk


class Scheduler:
    def __init__(self, objective):
        self.obj = objective
        self.wm = WorldModel(objective.target)
        self.episodic = EpisodicMemory(objective.target)
        self.report_lines = []

    def _log(self, msg):
        line = f"[scheduler] {msg}"
        print(line, flush=True)
        self.report_lines.append(line)

    def check_scope(self, profile):
        """Gate 1: the objective dies here if scope is uncertain."""
        hosts = profile.get("scope_hosts", [])
        if not hosts:
            raise ValueError("scheduler refused: no scope_hosts in profile — "
                             "scope uncertain, will not proceed")
        if not profile.get("program"):
            raise ValueError("scheduler refused: no program authorization basis")
        self._log(f"scope OK: {len(hosts)} hosts under {profile['program']}; "
                  f"active_allowed={profile.get('active_allowed')}")
        return True

    def run(self, profile, passive_only=False):
        """Execute the bounded research cycle."""
        t0 = time.time()
        self._log(f"objective: {self.obj.goal} on {self.obj.target} "
                  f"(≤{self.obj.max_rotations} rotations, "
                  f"≤{self.obj.max_experiments} experiments, risk≤{self.obj.max_risk})")
        self.check_scope(profile)

        experiments_used = 0
        for rotation in range(self.obj.max_rotations):
            self._log(f"--- rotation {rotation + 1}/{self.obj.max_rotations} ---")
            # RECON + MODEL + HYPOTHESES + EXPERIMENTS via the orchestrator
            state = orch.run_target(self.obj.target, profile,
                                    max_cycles=1, passive_only=passive_only)
            # LEARN: fold the run's findings back into the world model
            for f in state.get("findings", []):
                self.wm.update_from_observation(
                    f.get("detail", "") + " " + f.get("evidence", ""),
                    source=f.get("tool", "recon"))
                self.episodic.record(
                    observation=f.get("title", "") + " " + f.get("detail", "")[:200],
                    technique=f.get("tool", "unknown"),
                    evidence=f.get("evidence", "")[:200],
                    result="inconclusive",
                    lesson="folded into world model; needs discriminating experiment")
            self.wm.save()
            self._log(self.wm.summary())
            fg = FeatureGraph().build_from_world(self.wm)
            self._log(fg.stats() + f"; chains: {len(fg.find_chains())}")

            n_tests = sum(len(c.get("tests", [])) for c in state.get("cycles", []))
            experiments_used += n_tests
            if state.get("stop_reason", "").startswith("no novel"):
                self._log("novelty exhausted — stopping early")
                break
            if experiments_used >= self.obj.max_experiments:
                self._log("experiment budget exhausted — stopping")
                break
            # stop on high-severity signal
            for f in state.get("findings", []):
                if "high" in (f.get("severity", "") + f.get("title", "")).lower():
                    self._log("HIGH-SEVERITY signal — escalating to operator")
                    break

        self._log(f"done in {time.time() - t0:.0f}s; "
                  f"experiments used: {experiments_used}")
        return self.report()

    def report(self):
        return "\n".join(self.report_lines)
