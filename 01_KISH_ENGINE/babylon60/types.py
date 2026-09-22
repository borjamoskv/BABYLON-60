#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.3 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
Universal Algebraic Types alias for babylon60 (`babylon60.types`).
Re-exports algebraic primitives from babylon60.c5_types.
Eliminates existence gaps and makes illegal states unrepresentable.
"""

from __future__ import annotations

from .c5_types.algebraic import (
    AlgebraicCardinality,
    Err,
    Nothing,
    Ok,
    Option,
    Result,
    Some,
    make_illegal_states_unrepresentable,
)

__all__ = [
    "AlgebraicCardinality",
    "Err",
    "Nothing",
    "Ok",
    "Option",
    "Result",
    "Some",
    "make_illegal_states_unrepresentable",
]
