# C5-REAL EXERGY CERTIFIED
"""
C5-REAL Universal Algebraic Data Types (`babylon60.types`).
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
