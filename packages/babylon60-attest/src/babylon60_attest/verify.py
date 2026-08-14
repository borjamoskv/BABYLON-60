# C5-REAL EXERGY CERTIFIED
"""
Receipt verification (Falsification Protocol).

Implements the C5-REAL invariant: a receipt is valid if and only if
re-deriving the attestation_digest from its core fields produces a
bit-identical result. Any tampering — even a single character in the
prompt or output — produces a divergence that no authority can sign away.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any, Dict

from babylon60_attest.merkle import MerkleTree, sha3_256, sha3_256_str
from babylon60_attest.receipt import ScittReceipt


class VerificationResult:
    """Result of a receipt verification."""

    __slots__ = ("valid", "checks", "errors")

    def __init__(self) -> None:
        self.valid: bool = True
        self.checks: list[str] = []
        self.errors: list[str] = []

    def _pass(self, label: str, detail: str) -> None:
        self.checks.append(f"[PASS] {label}: {detail}")

    def _fail(self, label: str, detail: str) -> None:
        self.valid = False
        self.errors.append(f"[FAIL] {label}: {detail}")
        self.checks.append(f"[FAIL] {label}: {detail}")

    def __repr__(self) -> str:
        status = "VALID" if self.valid else "FALSIFIED"
        return f"VerificationResult({status}, checks={len(self.checks)}, errors={len(self.errors)})"


def verify_receipt(
    receipt: ScittReceipt | Dict[str, Any],
    *,
    prompt: str | None = None,
    output: str | None = None,
) -> VerificationResult:
    """
    Verify a SCITT receipt against its own cryptographic invariants.

    Checks performed:
        I1 SELF:   Re-derive attestation_digest from core fields.
        I2 PROMPT: If prompt is provided, verify prompt_digest matches.
        I3 OUTPUT: If output is provided, verify output_digest matches.
        I4 MERKLE: Re-derive Merkle root from leaves and compare.

    Args:
        receipt: A ScittReceipt instance or a dictionary.
        prompt:  Optional original prompt text for I2 verification.
        output:  Optional original output text for I3 verification.

    Returns:
        VerificationResult with pass/fail status and detail messages.
    """
    result = VerificationResult()

    if isinstance(receipt, dict):
        receipt = ScittReceipt.from_dict(receipt)

    # I1 SELF: Re-derive the attestation digest
    core = {
        "schema": receipt.schema,
        "operator_id": receipt.operator_id,
        "model": receipt.model,
        "prompt_digest": receipt.prompt_digest,
        "output_digest": receipt.output_digest,
        "merkle_root": receipt.merkle_root,
        "merkle_leaf_count": receipt.merkle_leaf_count,
        "timestamp_monotonic": receipt.timestamp_monotonic,
        "metadata": receipt.metadata,
    }
    canonical = json.dumps(core, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    derived_digest = sha3_256(canonical.encode("utf-8"))

    if derived_digest == receipt.attestation_digest:
        result._pass("I1 SELF", f"digest {derived_digest[:16]}... matches")
    else:
        result._fail(
            "I1 SELF",
            f"derived {derived_digest[:16]}... != claimed {receipt.attestation_digest[:16]}...",
        )

    # I2 PROMPT: Verify prompt digest if original prompt provided
    if prompt is not None:
        prompt_digest = sha3_256_str(prompt)
        if prompt_digest == receipt.prompt_digest:
            result._pass("I2 PROMPT", f"prompt digest {prompt_digest[:16]}... matches")
        else:
            result._fail(
                "I2 PROMPT",
                f"prompt digest {prompt_digest[:16]}... != receipt {receipt.prompt_digest[:16]}...",
            )

    # I3 OUTPUT: Verify output digest if original output provided
    if output is not None:
        output_digest = sha3_256_str(output)
        if output_digest == receipt.output_digest:
            result._pass("I3 OUTPUT", f"output digest {output_digest[:16]}... matches")
        else:
            result._fail(
                "I3 OUTPUT",
                f"output digest {output_digest[:16]}... != receipt {receipt.output_digest[:16]}...",
            )

    # I4 MERKLE: Re-derive the Merkle root
    leaves = [
        receipt.prompt_digest,
        receipt.output_digest,
        sha3_256_str(receipt.model),
        sha3_256_str(receipt.operator_id),
    ]
    tree = MerkleTree(leaves)
    if tree.root == receipt.merkle_root:
        result._pass("I4 MERKLE", f"root {tree.root[:16]}... matches")
    else:
        result._fail(
            "I4 MERKLE",
            f"derived root {tree.root[:16]}... != receipt {receipt.merkle_root[:16]}...",
        )

    return result
