# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
Causal-Determinist Universal Algebraic Data Types (`babylon60.c5_types`).
Enforces strict algebraic typing invariants:
- Product Types (`|A * B| = |A| * |B|`)
- Sum Types / Tagged Unions (`|A + B| = |A| + |B|`)
- Monadic Functors (`Result[T, E]`, `Option[T]`)
- Making illegal states physically unrepresentable at AST / compile time.
"""

from .algebraic import (
    Result,
    Ok,
    Err,
    Option,
    Some,
    Nothing,
    AlgebraicCardinality,
    make_illegal_states_unrepresentable,
)

__all__ = [
    "Result",
    "Ok",
    "Err",
    "Option",
    "Some",
    "Nothing",
    "AlgebraicCardinality",
    "make_illegal_states_unrepresentable",
]
