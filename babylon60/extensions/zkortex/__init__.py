# [C5-REAL] Exergy-Maximized
"""
ZKORTEX - Zero-Knowledge Proof Layer for CORTEX.
Epistemic sovereignty: proving without revealing.

Uses __getattr__ lazy loading to avoid cascading import failures
from optional dependencies (py_ecc via commitment/prover modules).

Exports:
    KnowledgeCommitment   - Pedersen-style commitment over a fact
    ZKMembershipProof     - Proof of membership in a set (Merkle)
    ZKRangeProof          - Proof that a value falls within a range
    ZKOrtexProver         - Sovereign orchestrator of proofs
    ZKOrtexVerifier       - Public verifier
    SovereignOpacityLayer - Integration with cortex.crypto.aes
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from babylon60.extensions.zkortex.commitment import KnowledgeCommitment
    from babylon60.extensions.zkortex.merkle import MerkleTree, ZKMembershipProof
    from babylon60.extensions.zkortex.opacity_layer import SovereignOpacityLayer
    from babylon60.extensions.zkortex.prover import ZKOrtexProver
    from babylon60.extensions.zkortex.range_proof import ZKRangeProof
    from babylon60.extensions.zkortex.verifier import ZKOrtexVerifier

__all__ = [
    "KnowledgeCommitment",
    "MerkleTree",
    "SovereignOpacityLayer",
    "ZKMembershipProof",
    "ZKOrtexProver",
    "ZKOrtexVerifier",
    "ZKRangeProof",
]

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "KnowledgeCommitment": ("babylon60.extensions.zkortex.commitment", "KnowledgeCommitment"),
    "MerkleTree": ("babylon60.extensions.zkortex.merkle", "MerkleTree"),
    "ZKMembershipProof": ("babylon60.extensions.zkortex.merkle", "ZKMembershipProof"),
    "SovereignOpacityLayer": (
        "babylon60.extensions.zkortex.opacity_layer",
        "SovereignOpacityLayer",
    ),
    "ZKOrtexProver": ("babylon60.extensions.zkortex.prover", "ZKOrtexProver"),
    "ZKRangeProof": ("babylon60.extensions.zkortex.range_proof", "ZKRangeProof"),
    "ZKOrtexVerifier": ("babylon60.extensions.zkortex.verifier", "ZKOrtexVerifier"),
}


def __getattr__(name: str) -> object:
    """Lazy-load zkortex symbols on first access (PEP 562)."""
    if name in _LAZY_IMPORTS:
        module_path, attr_name = _LAZY_IMPORTS[name]
        module = importlib.import_module(module_path)
        value = getattr(module, attr_name)
        globals()[name] = value
        return value
    raise AttributeError(f"module 'babylon60.extensions.zkortex' has no attribute {name!r}")
