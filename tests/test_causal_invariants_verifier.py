"""Regression test for the Robinson-Moskv & Cortex Persist causal invariants verifier."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def test_verify_causal_invariants_passes() -> None:
    repo_root = Path(__file__).absolute().parent.parent
    verifier_path = repo_root / "scripts" / "c5_verifiers" / "verify_causal_invariants.py"
    spec = importlib.util.spec_from_file_location("verify_causal_invariants", verifier_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.verify_causal_invariants() is True
