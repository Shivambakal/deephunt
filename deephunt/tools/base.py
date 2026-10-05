"""DEEPHUNT tool adapter interface + shared helpers."""
from __future__ import annotations
import json
import re
import subprocess
import time


def sh(cmd, timeout=60):
    """Run a shell command, return (rc, stdout, stderr). Never raises."""
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except Exception as e:  # noqa: BLE001
        return 1, "", str(e)


def fetch(url, timeout=25, headers=None):
    """Passive HTTP GET via curl (respects proxy env). Returns (status, body)."""
    hdr = ""
    if headers:
        hdr = " ".join(f'-H "{k}: {v}"' for k, v in headers.items())
    rc, out, _ = sh(
        f'curl -sL {hdr} --max-time {timeout} -o /tmp/dh_body -w "%{{http_code}}" '
        f'"{url}"')
    body = ""
    try:
        with open("/tmp/dh_body", "rb") as f:
            raw = f.read(2_000_000)
        body = raw.decode("utf-8", "replace")
    except OSError:
        pass
    try:
        return int(rc == 0 and out.strip() or 0), body
    except ValueError:
        return 0, body


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


_EGRESS_PROFILE = None


def egress_profile(refresh=False):
    """Detect sandbox-egress reality once per process. Never raises.

    In the sandbox, the system resolver is SHIMMED (fake 198.18.x.x answers)
    while DNS-over-HTTPS through the egress proxy returns real data. Outside
    the sandbox the two agree and dns_shimmed stays False. Adapters use this
    to pick a working DNS path and to emit an explicit 'env' finding instead
    of silently producing garbage from shimmed answers.
    """
    global _EGRESS_PROFILE
    if _EGRESS_PROFILE is not None and not refresh:
        return _EGRESS_PROFILE
    prof = {"dns_shimmed": False, "system_answer": None,
            "doh_answer": None, "doh_provider": None}
    sys_a = None
    try:
        import socket as _s
        sys_a = _s.gethostbyname("example.com")
        prof["system_answer"] = sys_a
    except Exception:  # noqa: BLE001
        pass
    doh_a = []
    try:
        import doh_dns as _d
        r = _d.resolve("example.com", "A", timeout=15)
        doh_a = sorted(x["data"] for x in r["answers"] if x["type"] == "A")
        prof["doh_answer"] = ",".join(doh_a) or None
        prof["doh_provider"] = r.get("provider")
    except Exception:  # noqa: BLE001
        pass
    if sys_a and doh_a and sys_a not in doh_a:
        try:
            import ipaddress as _ip
            ip = _ip.ip_address(sys_a)
            if ip.is_private or ip.is_reserved or ip.is_loopback:
                prof["dns_shimmed"] = True
        except Exception:  # noqa: BLE001
            pass
    _EGRESS_PROFILE = prof
    return prof


class ToolAdapter:
    """One weapon. Subclass, set metadata, implement run(ctx) -> [finding]."""
    name = "base"
    phase = "passive"          # passive | active | operator
    description = ""
    needs_bins = ()            # binaries that must exist for available()

    def available(self):
        for b in self.needs_bins:
            rc, _, _ = sh(f"command -v {b}")
            if rc != 0:
                return False
        return True

    def run(self, ctx):
        raise NotImplementedError

    # -- helpers ---------------------------------------------------------
    def finding(self, kind, title, detail="", evidence="", severity_hint="info"):
        return {"tool": self.name, "phase": self.phase, "kind": kind,
                "title": title, "detail": detail, "evidence": evidence[:2000],
                "severity_hint": severity_hint, "ts": now()}


REGISTRY = {}


def register(cls):
    REGISTRY[cls.name] = cls
    return cls
