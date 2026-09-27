"""DEEPHUNT event bus — recursive, event-driven recon (BBOT *pattern*, clean-room).

Everything is an Event: (type, data, parent chain, scope_distance, tags, creator).
Modules declare `watched_events` and emit new events; recursion is emergent
(e.g. dns_enum: SEED->DNS_NAME, portscan: DNS_NAME->OPEN_TCP_PORT,
certharv: OPEN_TCP_PORT->DNS_NAME) with no central orchestrator.

Pipeline per emitted event:
  emit -> ScanIngress (dedup, scope check) -> Intercept modules (tagging) ->
  fan-out to modules watching the event type.

Scope is data, not a pre-filter: events carry scope_distance (hops from seed)
and tags; the bus drops events beyond max_scope_distance or failing the
scope predicate. No AGPL code is used here; only the architectural pattern.
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Set


@dataclass
class Event:
    type: str
    data: str
    creator: str = ""
    parent: Optional["Event"] = None
    scope_distance: int = 0
    tags: Set[str] = field(default_factory=set)

    def chain(self) -> List["Event"]:
        out, cur = [], self
        while cur is not None:
            out.append(cur)
            cur = cur.parent
        return list(reversed(out))

    def key(self):
        return (self.type, self.data)


class Module:
    """Base class for bus modules. Subclass and set watched_events + handle()."""
    name = "base"
    watched_events: List[str] = []

    def handle(self, event: Event, bus: "EventBus") -> None:
        raise NotImplementedError

    def emit(self, bus: "EventBus", type: str, data: str,
             tags: Optional[Set[str]] = None, parent: Optional[Event] = None):
        bus.emit(Event(type=type, data=data, creator=self.name,
                       parent=parent,
                       scope_distance=(parent.scope_distance + 1) if parent else 0,
                       tags=set(tags or [])))


class EventBus:
    def __init__(self, max_scope_distance: int = 3,
                 scope_predicate: Optional[Callable[[Event], bool]] = None,
                 max_events: int = 10000):
        self.modules: List[Module] = []
        self.interceptors: List[Module] = []  # run on every event (tagging)
        self.watchers: Dict[str, List[Module]] = defaultdict(list)
        self.seen: Set[tuple] = set()          # ScanIngress dedup registry
        self.events: List[Event] = []          # ordered event log (provenance)
        self.max_scope_distance = max_scope_distance
        self.scope_predicate = scope_predicate or (lambda e: True)
        self.max_events = max_events
        self.dropped = 0

    def register(self, module: Module, intercept: bool = False):
        self.modules.append(module)
        if intercept:
            self.interceptors.append(module)
        for t in module.watched_events:
            self.watchers[t].append(module)

    def emit(self, event: Event) -> bool:
        """ScanIngress: dedup + scope check. Returns True if accepted."""
        if len(self.events) >= self.max_events:
            self.dropped += 1
            return False
        if event.key() in self.seen:
            self.dropped += 1
            return False
        if event.scope_distance > self.max_scope_distance:
            self.dropped += 1
            return False
        if not self.scope_predicate(event):
            self.dropped += 1
            return False
        self.seen.add(event.key())
        self.events.append(event)
        # Intercept stage (tagging / normalization)
        for mod in self.interceptors:
            try:
                mod.handle(event, self)
            except Exception:
                continue
        # Fan-out
        for mod in self.watchers.get(event.type, []):
            try:
                mod.handle(event, self)
            except Exception:
                continue
        return True

    def run(self, seeds: List[Event]):
        queue = deque(seeds)
        # Seed events go through ingress too (dedup/scope), then fan-out
        # happens synchronously inside emit(); the queue just feeds seeds.
        for s in seeds:
            self.emit(s)

    def events_of_type(self, type: str) -> List[Event]:
        return [e for e in self.events if e.type == type]

    def stats(self) -> dict:
        by_type = defaultdict(int)
        for e in self.events:
            by_type[e.type] += 1
        return {"total": len(self.events), "dropped": self.dropped,
                "by_type": dict(by_type),
                "modules": [m.name for m in self.modules]}
