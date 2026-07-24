# causal_isomorphism — C5-REAL AST Transmutation Engine
"""
Causal Isomorphism Transpiler.

Defines F# as the central ontological assertion language and compiles
strict execution subsets to target environments via controlled AST
transmutation, obeying the Trilingual Regime directive.

Layers:
  - F# (Domain Kernel): Ontological types, state machines, validation
  - Rust (strike_rs): Causal poset DAGs, BLAKE3 taint, zero-cost execution
  - Solidity (Anvil/Yung): BFT consensus anchoring, event emission, state storage
"""

from causal_isomorphism.ir import (
    IRDiscriminatedUnion,
    IRFunction,
    IRModule,
    IRRecordType,
    RegimeLayer,
)

__all__ = [
    "IRModule",
    "IRDiscriminatedUnion",
    "IRRecordType",
    "IRFunction",
    "RegimeLayer",
]
