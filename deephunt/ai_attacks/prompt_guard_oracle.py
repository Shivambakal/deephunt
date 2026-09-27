"""Meta Llama Prompt Guard 2 (86M) defense oracle — OPTIONAL, local-only.

Wraps the locally downloaded ``meta-llama/Llama-Prompt-Guard-2-86M`` weights
as a second-opinion classifier for AI-attack observations. It answers one
question: "does this text look like a prompt-injection / jailbreak attempt?"
(benign vs malicious, binary).

Design rules (non-negotiable):
  - OPTIONAL: if transformers/torch or the weights are absent, every call
    degrades to ``{"label": "unavailable", ...}`` instead of raising.
  - EVIDENCE, NOT VERDICT: the return value is an evidence dict in the same
    shape as scorer.classify(); it never confirms a vulnerability on its own.
    Findings still require compete_finding() and the independent verifier.
  - LOCAL ONLY: the model runs on this machine (CPU). Nothing is transmitted.
  - 512-token context window (per the model card): longer inputs are
    truncated by the tokenizer.

Model dir resolution: ``PROMPT_GUARD_MODEL_DIR`` env var, else
``<repo>/../models/prompt-guard-2-86m``.
"""
from __future__ import annotations

import os
from typing import Dict, List, Optional

DEFAULT_MODEL_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "..", "models", "prompt-guard-2-86m",
)
DEFAULT_MODEL_DIR = os.path.normpath(DEFAULT_MODEL_DIR)

# Lazily imported so this module is importable without the ML stack.
_tok = None
_mdl = None
_torch = None
_import_error: Optional[str] = None


def _try_imports() -> bool:
    global _tok, _mdl, _torch, _import_error
    if _mdl is not None:
        return True
    if _import_error is not None:
        return False
    try:
        import torch  # type: ignore
        from transformers import (  # type: ignore
            AutoModelForSequenceClassification,
            AutoTokenizer,
        )
    except Exception as e:  # missing deps -> unavailable, not fatal
        _import_error = f"{type(e).__name__}: {e}"
        return False
    model_dir = os.environ.get("PROMPT_GUARD_MODEL_DIR", DEFAULT_MODEL_DIR)
    weights = os.path.join(model_dir, "model.safetensors")
    if not os.path.isfile(weights):
        _import_error = f"weights not found: {weights}"
        return False
    try:
        _torch = torch
        _tok = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
        _mdl = AutoModelForSequenceClassification.from_pretrained(
            model_dir, local_files_only=True
        ).eval()
    except Exception as e:
        _import_error = f"{type(e).__name__}: {e}"
        _tok, _mdl, _torch = None, None, None
        return False
    return True


def available() -> bool:
    """True when the oracle can actually classify (deps + weights present)."""
    return _try_imports()


def unavailability_reason() -> Optional[str]:
    _try_imports()
    return _import_error


def classify(text: str) -> Dict:
    """Classify one text. Never raises for missing deps/weights.

    Returns a dict compatible with scorer.classify() consumers:
      label: "benign" | "malicious" | "unavailable"
      malicious_score: P(malicious) in [0,1] (0.0 when unavailable)
      signals: human-readable signal strings
      evidence_artifacts: {name: bool} for evidence.py contracts
    """
    signals: List[str] = []
    artifacts = {
        "prompt_guard_available": False,
        "prompt_guard_malicious": False,
        "prompt_guard_benign": False,
        "prompt_guard_unavailable": True,
    }
    if not _try_imports():
        signals.append(f"oracle_unavailable:{_import_error}")
        return {
            "label": "unavailable",
            "malicious_score": 0.0,
            "signals": signals,
            "evidence_artifacts": artifacts,
        }
    try:
        inputs = _tok(
            text or "", return_tensors="pt", truncation=True, max_length=512
        )
        with _torch.no_grad():
            logits = _mdl(**inputs).logits
            probs = _torch.softmax(logits, dim=-1)[0]
        p_mal = float(probs[1].item())
        label = "malicious" if p_mal >= 0.5 else "benign"
        signals.append(f"prompt_guard:{label}:{p_mal:.3f}")
        artifacts.update(
            prompt_guard_available=True,
            prompt_guard_unavailable=False,
            prompt_guard_malicious=label == "malicious",
            prompt_guard_benign=label == "benign",
        )
        return {
            "label": label,
            "malicious_score": round(p_mal, 4),
            "signals": signals,
            "evidence_artifacts": artifacts,
        }
    except Exception as e:  # inference blew up -> unavailable, not fatal
        signals.append(f"oracle_error:{type(e).__name__}")
        return {
            "label": "unavailable",
            "malicious_score": 0.0,
            "signals": signals,
            "evidence_artifacts": artifacts,
        }


def combine_with_scorer(
    response_text: str, probe: dict, scorer_module=None
) -> Dict:
    """Run the deterministic scorer AND the oracle; return both as evidence.

    The oracle's label is attached as an additional signal — it can raise or
    lower confidence in review, but the scorer's verdict stands on its own.
    Pass the scorer module (or anything with .classify) to avoid imports.
    """
    from . import scorer as _scorer

    mod = scorer_module or _scorer
    base = mod.classify(response_text, probe)
    oracle = classify(probe.get("payload", "") or response_text)
    base = dict(base)
    base["oracle"] = oracle
    base["signals"] = list(base.get("signals", [])) + [
        f"oracle_{s}" for s in oracle["signals"]
    ]
    return base
