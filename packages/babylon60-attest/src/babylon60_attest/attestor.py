# C5-REAL EXERGY CERTIFIED
"""
LLMAttestor: High-level API for attesting LLM interactions.

This is the primary user-facing class. It wraps receipt generation,
ledger persistence, and optional verification into a single call.

Example:
    from babylon60_attest import LLMAttestor

    attestor = LLMAttestor(operator_id="legal-dept.company.eu")

    receipt = attestor.attest(
        model="claude-4-sonnet",
        prompt="Draft a rental contract for...",
        output="RENTAL AGREEMENT\n\nThis agreement...",
        metadata={"department": "legal", "risk_level": "high"},
    )

    # Verify later
    result = attestor.verify(receipt, prompt="Draft a rental contract for...")
    assert result.valid
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from babylon60_attest.ledger import AppendOnlyLedger
from babylon60_attest.receipt import ScittReceipt, build_receipt
from babylon60_attest.verify import VerificationResult, verify_receipt


class LLMAttestor:
    """
    Attestation engine for LLM outputs.

    Binds model, prompt, output, and operator identity into a cryptographic
    SCITT receipt and optionally persists it to an append-only local ledger.

    Args:
        operator_id: Identity string of the operating entity (e.g., ENS domain,
                     company name, or EU AI Act operator identifier).
        ledger_path: Path to the SQLite ledger. Set to None to disable persistence.
    """

    def __init__(
        self,
        operator_id: str = "anonymous",
        ledger_path: Optional[str] = "attestations.db",
    ) -> None:
        self._operator_id = operator_id
        self._ledger: Optional[AppendOnlyLedger] = None
        if ledger_path is not None:
            self._ledger = AppendOnlyLedger(db_path=ledger_path)

    @property
    def operator_id(self) -> str:
        return self._operator_id

    def attest(
        self,
        *,
        model: str,
        prompt: str,
        output: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ScittReceipt:
        """
        Attest a single LLM interaction.

        Creates a SCITT receipt binding the prompt, output, model, and operator
        identity. If a ledger is configured, the receipt is persisted.

        Args:
            model:    Model identifier (e.g., "gpt-4o", "claude-4-sonnet").
            prompt:   The full prompt text sent to the model.
            output:   The full output text received from the model.
            metadata: Optional key-value metadata (department, risk level, etc.).

        Returns:
            A frozen ScittReceipt instance.
        """
        receipt = build_receipt(
            operator_id=self._operator_id,
            model=model,
            prompt=prompt,
            output=output,
            metadata=metadata,
        )

        if self._ledger is not None:
            self._ledger.append(receipt.to_dict())

        return receipt

    def verify(
        self,
        receipt: ScittReceipt | Dict[str, Any],
        *,
        prompt: Optional[str] = None,
        output: Optional[str] = None,
    ) -> VerificationResult:
        """
        Verify a receipt against its cryptographic invariants.

        Optionally provide the original prompt and/or output to verify
        content integrity (I2/I3 checks).
        """
        return verify_receipt(receipt, prompt=prompt, output=output)

    def close(self) -> None:
        """Close the underlying ledger connection."""
        if self._ledger is not None:
            self._ledger.close()

    def __enter__(self) -> "LLMAttestor":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()
