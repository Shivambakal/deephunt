"""DEEPHUNT tool registry assembly."""
from .base import REGISTRY  # noqa: F401
from . import passive  # noqa: F401
from . import active  # noqa: F401
from . import operator  # noqa: F401
from . import t100  # noqa: F401  (tools-100 generic adapters)


def list_tools(phase=None):
    tools = [c() for c in REGISTRY.values()]
    if phase:
        tools = [t for t in tools if t.phase == phase]
    return sorted(tools, key=lambda t: (t.phase, t.name))


def get(name):
    cls = REGISTRY.get(name)
    return cls() if cls else None
