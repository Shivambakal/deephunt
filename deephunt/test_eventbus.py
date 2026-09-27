"""Tests for deephunt/eventbus.py — fake modules only, no network."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from eventbus import Event, EventBus, Module


class FakeDNSEnum(Module):
    name = "fake_dns"
    watched_events = ["SEED"]

    def handle(self, event, bus):
        for sub in ("a", "b"):
            self.emit(bus, "DNS_NAME", f"{sub}.{event.data}", parent=event)


class FakePortScan(Module):
    name = "fake_portscan"
    watched_events = ["DNS_NAME"]

    def handle(self, event, bus):
        self.emit(bus, "OPEN_TCP_PORT", f"{event.data}:443", parent=event)


class FakeCertHarvest(Module):
    name = "fake_certharv"
    watched_events = ["OPEN_TCP_PORT"]

    def handle(self, event, bus):
        host = event.data.split(":")[0]
        # emergent recursion: cert harvest finds a new name for a known host
        if not host.startswith("alt."):
            self.emit(bus, "DNS_NAME", f"alt.{host}", parent=event)


class FakeTagger(Module):
    name = "fake_tagger"
    watched_events = []

    def handle(self, event, bus):
        if event.data.endswith(".example.com"):
            event.tags.add("in-scope")


def test_recursion_and_dedup():
    bus = EventBus(max_scope_distance=4)
    for m in (FakeDNSEnum(), FakePortScan(), FakeCertHarvest(), FakeTagger()):
        bus.register(m, intercept=(m.name == "fake_tagger"))
    bus.run([Event(type="SEED", data="example.com")])
    dns = bus.events_of_type("DNS_NAME")
    ports = bus.events_of_type("OPEN_TCP_PORT")
    assert len(dns) >= 2, f"expected recursion-produced DNS_NAMEs, got {len(dns)}"
    assert len(ports) >= 2, f"expected ports, got {len(ports)}"
    # dedup: no duplicate (type, data) pairs
    keys = [e.key() for e in bus.events]
    assert len(keys) == len(set(keys)), "dedup registry failed"
    # scope distance increments along the chain
    for e in dns:
        assert e.scope_distance >= 1
    # interceptor tagged in-scope events
    assert any("in-scope" in e.tags for e in dns), "interceptor tagging failed"
    print("PASS test_recursion_and_dedup")


def test_scope_distance_cap():
    bus = EventBus(max_scope_distance=1)
    bus.register(FakeDNSEnum())
    bus.register(FakePortScan())
    bus.run([Event(type="SEED", data="example.com")])
    assert len(bus.events_of_type("DNS_NAME")) == 2
    assert len(bus.events_of_type("OPEN_TCP_PORT")) == 0, \
        "events beyond max_scope_distance must be dropped"
    print("PASS test_scope_distance_cap")


def test_scope_predicate():
    bus = EventBus(scope_predicate=lambda e: "evil" not in e.data)
    bus.register(FakeDNSEnum())
    bus.run([Event(type="SEED", data="evil.example.com")])
    assert all("evil" not in e.data for e in bus.events[1:]), \
        "scope predicate failed"
    print("PASS test_scope_predicate")


def test_provenance_chain():
    bus = EventBus()
    bus.register(FakeDNSEnum())
    bus.register(FakePortScan())
    bus.run([Event(type="SEED", data="example.com")])
    port = bus.events_of_type("OPEN_TCP_PORT")[0]
    chain = port.chain()
    types = [e.type for e in chain]
    assert types == ["SEED", "DNS_NAME", "OPEN_TCP_PORT"], f"bad chain {types}"
    assert all(e.creator for e in chain[1:]), "creator provenance missing"
    print("PASS test_provenance_chain")


if __name__ == "__main__":
    test_recursion_and_dedup()
    test_scope_distance_cap()
    test_scope_predicate()
    test_provenance_chain()
    print("eventbus: 4/4 pass")
