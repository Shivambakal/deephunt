"""DEEPHUNT adapters for OSS AI-red-team tools (garak, PyRIT, JailbreakBench).

Design rule: adapters NEVER transmit on their own. They build execution
specs (configs) and parse tool outputs into DEEPHUNT evidence artifacts.
Any actual execution goes through an explicit `run_*` function that
requires a TestAuthorization token minted by ResearchSession — the same
rail as every other active tool.

If the OSS tool is not installed, every entry point degrades to a clear
"not installed" dict instead of raising.
"""
from __future__ import annotations

from typing import Dict, List
