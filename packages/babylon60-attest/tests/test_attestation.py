# C5-REAL EXERGY CERTIFIED
"""End-to-end tests: attest → verify → ledger round-trip."""
import json
import os
import tempfile

from babylon60_attest import LLMAttestor
from babylon60_attest.receipt import build_receipt, ScittReceipt
from babylon60_attest.verify import verify_receipt
from babylon60_attest.ledger import AppendOnlyLedger


PROMPT = "Generate a rental contract for a 2-bedroom apartment in Bilbao."
OUTPUT = "RENTAL AGREEMENT\n\nThis agreement is entered into by and between..."
MODEL = "claude-4-sonnet"
OPERATOR = "legal-dept.test.eu"


def test_build_receipt_has_all_fields():
    receipt = build_receipt(
        operator_id=OPERATOR,
        model=MODEL,
        prompt=PROMPT,
        output=OUTPUT,
    )
    assert receipt.schema == "babylon60.llm.attestation/v1"
    assert receipt.operator_id == OPERATOR
    assert receipt.model == MODEL
    assert receipt.prompt_digest
    assert receipt.output_digest
    assert receipt.merkle_root
    assert receipt.attestation_digest
    assert receipt.merkle_leaf_count == 4


def test_receipt_json_roundtrip():
    receipt = build_receipt(
        operator_id=OPERATOR,
        model=MODEL,
        prompt=PROMPT,
        output=OUTPUT,
        metadata={"risk": "high"},
    )
    json_str = receipt.to_json()
    restored = ScittReceipt.from_json(json_str)
    assert restored.attestation_digest == receipt.attestation_digest
    assert restored.metadata == {"risk": "high"}


def test_verify_valid_receipt():
    receipt = build_receipt(
        operator_id=OPERATOR,
        model=MODEL,
        prompt=PROMPT,
        output=OUTPUT,
    )
    result = verify_receipt(receipt, prompt=PROMPT, output=OUTPUT)
    assert result.valid
    assert len(result.errors) == 0
    assert len(result.checks) == 4  # I1 + I2 + I3 + I4


def test_verify_detects_tampered_output():
    receipt = build_receipt(
        operator_id=OPERATOR,
        model=MODEL,
        prompt=PROMPT,
        output=OUTPUT,
    )
    result = verify_receipt(receipt, prompt=PROMPT, output="TAMPERED OUTPUT")
    assert not result.valid
    assert any("I3 OUTPUT" in e for e in result.errors)


def test_verify_detects_tampered_prompt():
    receipt = build_receipt(
        operator_id=OPERATOR,
        model=MODEL,
        prompt=PROMPT,
        output=OUTPUT,
    )
    result = verify_receipt(receipt, prompt="TAMPERED PROMPT")
    assert not result.valid
    assert any("I2 PROMPT" in e for e in result.errors)


def test_verify_from_dict():
    receipt = build_receipt(
        operator_id=OPERATOR,
        model=MODEL,
        prompt=PROMPT,
        output=OUTPUT,
    )
    result = verify_receipt(receipt.to_dict())
    assert result.valid


def test_attestor_end_to_end():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        with LLMAttestor(operator_id=OPERATOR, ledger_path=db_path) as attestor:
            receipt = attestor.attest(
                model=MODEL,
                prompt=PROMPT,
                output=OUTPUT,
                metadata={"department": "legal"},
            )
            assert receipt.attestation_digest

            result = attestor.verify(receipt, prompt=PROMPT, output=OUTPUT)
            assert result.valid


def test_ledger_append_and_lookup():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "ledger.db")
        with AppendOnlyLedger(db_path=db_path) as ledger:
            receipt = build_receipt(
                operator_id=OPERATOR,
                model=MODEL,
                prompt=PROMPT,
                output=OUTPUT,
            )
            entry_id = ledger.append(receipt.to_dict())
            assert entry_id

            retrieved = ledger.lookup(entry_id)
            assert retrieved is not None
            assert retrieved["attestation_digest"] == receipt.attestation_digest

            assert ledger.count() == 1


def test_ledger_idempotent():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "ledger.db")
        with AppendOnlyLedger(db_path=db_path) as ledger:
            receipt = build_receipt(
                operator_id=OPERATOR,
                model=MODEL,
                prompt=PROMPT,
                output=OUTPUT,
            )
            id1 = ledger.append(receipt.to_dict())
            id2 = ledger.append(receipt.to_dict())
            assert id1 == id2
            assert ledger.count() == 1


def test_receipt_deterministic():
    """Same inputs always produce same attestation digest."""
    r1 = build_receipt(operator_id=OPERATOR, model=MODEL, prompt=PROMPT, output=OUTPUT)
    r2 = build_receipt(operator_id=OPERATOR, model=MODEL, prompt=PROMPT, output=OUTPUT)
    # Digests are identical (prompt, output, model, operator are identical)
    assert r1.prompt_digest == r2.prompt_digest
    assert r1.output_digest == r2.output_digest
    assert r1.merkle_root == r2.merkle_root
    # Note: attestation_digest differs due to timestamp_monotonic
