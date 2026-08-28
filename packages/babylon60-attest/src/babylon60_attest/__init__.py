# C5-REAL EXERGY CERTIFIED
"""
babylon60-attest: Deterministic LLM Output Attestation under IETF SCITT (RFC 9943).

Zero external dependencies. stdlib only.

Usage:
    from babylon60_attest import LLMAttestor

    attestor = LLMAttestor(operator_id="company.eu")
    receipt = attestor.attest(
        model="claude-4-sonnet",
        prompt="Generate a rental contract...",
        output="RENTAL AGREEMENT...",
    )
"""
from babylon60_attest.attestor import LLMAttestor
from babylon60_attest.merkle import MerkleTree, sha3_256
from babylon60_attest.receipt import ScittReceipt
from babylon60_attest.ledger import AppendOnlyLedger
from babylon60_attest.verify import verify_receipt

__all__ = [
    "LLMAttestor",
    "MerkleTree",
    "sha3_256",
    "ScittReceipt",
    "AppendOnlyLedger",
    "verify_receipt",
]
__version__ = "0.1.0"
