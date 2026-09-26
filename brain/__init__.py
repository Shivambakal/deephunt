"""Brain: hypothesis engine above the proxy. Public surface."""
from .model import WorldModel, Assumption
from .engine import Engine
from . import hypotheses, experiments
from .ledger import Ledger
from .gate import GateRefused, TestAuthorization
from .session import ResearchSession

__all__ = ["WorldModel", "Assumption", "Engine", "hypotheses", "experiments",
           "Ledger", "GateRefused", "TestAuthorization", "ResearchSession"]
