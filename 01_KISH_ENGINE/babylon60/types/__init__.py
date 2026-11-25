"""
Universal Algebraic Data Types (ADT) re-exports for babylon60.types.
Preserves backwards compatibility with C5 verifiers.
"""

from babylon60.c5_types.algebraic import (
    Ok,
    Err,
    Result,
    Some,
    Nothing,
    Option,
    AlgebraicCardinality,
    make_illegal_states_unrepresentable,
)

__all__ = [
    "Ok",
    "Err",
    "Result",
    "Some",
    "Nothing",
    "Option",
    "AlgebraicCardinality",
    "make_illegal_states_unrepresentable",
]
