# [C5-REAL] Exergy-Maximized
"""
IMMUNE-SYSTEM-V1 (The Epistemic Arbitrator).
Interprets and arbitrates signals between perception and execution.

Uses __getattr__ lazy loading to avoid cascading import failures
from optional dependencies (z3-solver via verification.verifier).
"""

from __future__ import annotations

import importlib

__all__ = [
    "ErrorBoundary",  # pyright: ignore[reportUnsupportedDunderAll]
    "EvolutionaryFalsifier",  # pyright: ignore[reportUnsupportedDunderAll]
    "FilterResult",  # pyright: ignore[reportUnsupportedDunderAll]
    "ImmuneArbiter",  # pyright: ignore[reportUnsupportedDunderAll]
    "TriageResult",  # pyright: ignore[reportUnsupportedDunderAll]
    "Verdict",  # pyright: ignore[reportUnsupportedDunderAll]
    "error_boundary",  # pyright: ignore[reportUnsupportedDunderAll]
]

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "FilterResult": ("babylon60.extensions.immune.arbiter", "FilterResult"),
    "ImmuneArbiter": ("babylon60.extensions.immune.arbiter", "ImmuneArbiter"),
    "TriageResult": ("babylon60.extensions.immune.arbiter", "TriageResult"),
    "Verdict": ("babylon60.extensions.immune.arbiter", "Verdict"),
    "ErrorBoundary": ("babylon60.extensions.immune.error_boundary", "ErrorBoundary"),
    "error_boundary": ("babylon60.extensions.immune.error_boundary", "error_boundary"),
    "EvolutionaryFalsifier": ("babylon60.extensions.immune.falsification", "EvolutionaryFalsifier"),
}


def __getattr__(name: str) -> object:
    """Lazy-load immune symbols on first access (PEP 562)."""
    if name in _LAZY_IMPORTS:
        module_path, attr_name = _LAZY_IMPORTS[name]
        module = importlib.import_module(module_path)
        value = getattr(module, attr_name)
        globals()[name] = value
        return value
    raise AttributeError(f"module 'babylon60.extensions.immune' has no attribute {name!r}")
