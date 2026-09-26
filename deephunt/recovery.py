"""DEEPHUNT failure recovery — endgame #8.

Browser crashes. Proxy dies. Model API fails. Requests time out. Targets
change. Tools break. The investigation must NOT die with them.

    checkpoint -> recover -> continue

- RunState: JSON checkpoint of where a run is (target, cycle, phase,
  completed work) — saved after every phase, resumed on restart.
- resilient(): wraps any fallible call with bounded retries + backoff.
  Timeouts, connection errors, and tool crashes are retried; programming
  errors (TypeError etc.) fail fast — retrying a bug is not recovery.
- CircuitBreaker: a tool that fails N times in a row is quarantined for
  the rest of the run instead of poisoning every cycle.
"""
import json
import os
import time

BASE = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.join(BASE, "state")

RETRYABLE = (TimeoutError, ConnectionError, OSError)


class RunState:
    def __init__(self, target):
        self.target = target
        self.path = os.path.join(STATE_DIR, f"{target}_runstate.json")
        self.data = {"target": target, "cycle": 0, "phase": "start",
                     "done": [], "ts": time.time()}
        self._load()

    def _load(self):
        if os.path.isfile(self.path):
            try:
                self.data.update(json.load(open(self.path)))
            except (OSError, ValueError):
                pass

    def checkpoint(self, **kw):
        self.data.update(kw)
        self.data["ts"] = time.time()
        os.makedirs(STATE_DIR, exist_ok=True)
        json.dump(self.data, open(self.path, "w"), indent=1)

    def mark_done(self, item):
        if item not in self.data["done"]:
            self.data["done"].append(item)
        self.checkpoint()

    def resume_from(self):
        return self.data["cycle"], self.data["phase"]

    def clear(self):
        try:
            os.remove(self.path)
        except OSError:
            pass

    def complete(self):
        """Mark the run finished and remove the checkpoint file."""
        self.checkpoint(phase="done")
        self.clear()


def resilient(fn, *args, retries=3, base_delay=2, label="op", **kwargs):
    """Run fn with bounded retries on transient failures. Returns
    (ok, result_or_error). Programming errors fail fast."""
    last = None
    for attempt in range(retries + 1):
        try:
            return True, fn(*args, **kwargs)
        except RETRYABLE as e:
            last = e
            if attempt < retries:
                time.sleep(base_delay * (2 ** attempt))
        except Exception as e:  # bug in our code — do NOT retry
            return False, f"{label} failed fast (not transient): {e!r}"
    return False, f"{label} failed after {retries + 1} attempts: {last!r}"


class CircuitBreaker:
    def __init__(self, threshold=3):
        self.threshold = threshold
        self.failures = {}

    def record(self, name, ok):
        self.failures[name] = 0 if ok else self.failures.get(name, 0) + 1

    def quarantined(self, name):
        return self.failures.get(name, 0) >= self.threshold

    def report(self):
        return {n: c for n, c in self.failures.items() if c >= self.threshold}
