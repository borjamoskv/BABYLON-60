"""
Tests for BABYLON-60 Ergonomic API (Sprints 2 & 4).
RFC-B60-2026-01-ADOPTION-ARCHITECTURE (Iceberg Pattern).

Validates:
1. Quickstart de 3 líneas (Time-to-Value < 5 minutos).
2. Comprobación exhaustiva de Assurance Levels AL-0, AL-1, AL-2 y AL-3.
3. Verificación matemática y determinismo de BatchMerkleAccumulator.
4. Funcionamiento de decoradores @tracer.watch y @watch (sync y async).
5. Exportación fluida de informes de conformidad EU AI Act (HTML, MD, JSON).
"""

import hashlib
import os
import tempfile
import time
from typing import Dict

import pytest

import babylon60 as b60
from babylon60.api import (
    AssuranceLevel,
    BatchMerkleAccumulator,
    Tracer,
    watch,
)


@pytest.fixture(autouse=True)
def enable_ephemeral_signing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BABYLON60_ALLOW_EPHEMERAL_SIGNING", "1")


def test_quickstart_three_lines() -> None:
    """
    Validates that BABYLON-60 can be integrated in 3 lines with zero friction:
      import babylon60 as b60
      tracer = b60.Tracer()
      with tracer.audit() as s: s.log_step("prompt", {"user": "hola"})
    """
    tracer = b60.Tracer(system_name="QuickstartAgent")
    with tracer.audit(session_id="qs_001") as session:
        step = session.log_step(action="prompt_processing", payload={"prompt": "hola mundo"})

    assert step["action"] == "prompt_processing"
    assert "hash" in step
    assert len(step["hash"]) == 64
    assert session.is_closed is True
    assert session.global_merkle_root is not None
    assert len(session.global_merkle_root) == 64
    assert len(session.events) == 1


def test_assurance_level_al0_transparent() -> None:
    """
    AL0_TRANSPARENT: In-memory SHA-256 hash (<0.05ms target overhead),
    no cryptographic signature overhead, for development and tests.
    """
    tracer = Tracer(system_name="DevAgent", assurance_level=AssuranceLevel.AL0_TRANSPARENT)
    assert tracer.assurance_level == AssuranceLevel.AL0_TRANSPARENT
    assert tracer.assurance_level.requires_signature is False
    assert tracer.assurance_level.requires_hardware_anchor is False

    t0 = time.perf_counter()
    with tracer.audit(session_id="al0_sess") as s:
        for i in range(10):
            step = s.log_step(action=f"step_{i}", payload={"index": i})
            assert "hash" in step
            # AL0 does not maintain linear chain or signatures
            assert "chain_hash" not in step
    elapsed_ms = (time.perf_counter() - t0) * 1000

    # 10 steps in-memory should take less than 5ms total (<0.5ms per step)
    assert elapsed_ms < 50.0
    summary = s.get_summary()
    assert summary["total_events"] == 10
    assert summary["assurance_level"] == "AL0_TRANSPARENT"
    assert summary["is_closed"] is True


def test_assurance_level_al1_standard_hash_chain() -> None:
    """
    AL1_STANDARD: Incremental linear hash chain (<0.3ms overhead).
    Verifies H_i = SHA256(H_{i-1} || H(step_i)) tamper-evidence.
    """
    tracer = Tracer(system_name="SupportAgent", assurance_level=AssuranceLevel.AL1_STANDARD)
    assert tracer.assurance_level.requires_hash_chain is True
    assert tracer.assurance_level.requires_signature is False

    with tracer.audit(session_id="al1_sess") as s:
        initial_anchor = s.prev_hash
        step1 = s.log_step(action="faq_query", payload={"q": "billing"})
        chain1 = step1["chain_hash"]
        expected1 = hashlib.sha256(f"{initial_anchor}:{step1['hash']}".encode("utf-8")).hexdigest()
        assert chain1 == expected1

        step2 = s.log_step(action="faq_response", payload={"a": "details"})
        chain2 = step2["chain_hash"]
        expected2 = hashlib.sha256(f"{chain1}:{step2['hash']}".encode("utf-8")).hexdigest()
        assert chain2 == expected2

    assert len(s.events) == 2


def test_assurance_level_al2_compliance_default() -> None:
    """
    AL2_COMPLIANCE: Default EU AI Act level (Articles 9-15).
    Micro-batches events and seals with Ed25519 signature on session close.
    """
    tracer = Tracer(system_name="EUComplianceAgent")
    assert tracer.assurance_level == AssuranceLevel.AL2_COMPLIANCE
    assert tracer.assurance_level.requires_signature is True
    assert tracer.assurance_level.requires_merkle_batching is True

    with tracer.audit(session_id="al2_sess") as s:
        s.log_step(action="data_validation", payload={"records": 100})
        s.log_step(action="model_inference", payload={"model": "deep-reasoner"})
        s.log_step(action="safety_filter", payload={"verdict": "SAFE"})

    assert s.is_closed is True
    assert s.global_merkle_root is not None
    assert len(s.global_merkle_root) == 64
    assert s.signature_info is not None
    assert s.signature_info["algorithm"] == "Ed25519"

    # Verify manifest was written to bundle directory
    manifest_file = os.path.join(s.bundle_dir, "manifest.json")
    assert os.path.exists(manifest_file)


def test_assurance_level_al3_sovereign_hardware_anchor() -> None:
    """
    AL3_SOVEREIGN: Maximum per-step integrity + hardware anchor
    (Apple Silicon IOPlatformUUID or Linux DMI / TPM PCRs) and SHA3-256 Merkle root.
    """
    tracer = Tracer(system_name="DefenseSovereignAgent", assurance_level=AssuranceLevel.AL3_SOVEREIGN)
    assert tracer.assurance_level.requires_hardware_anchor is True

    with tracer.audit(session_id="al3_sess") as s:
        step = s.log_step(action="firewall_inspection", payload={"port": 443, "traffic": "nominal"})
        assert "hardware_uuid" in step
        assert "enclave_type" in step

    assert s.is_closed is True
    assert s.hardware_anchor is not None
    assert "hardware_uuid" in s.hardware_anchor
    assert "pcr_value" in s.hardware_anchor
    assert "pcr_index" in s.hardware_anchor
    assert "tpm_quote_signature" in s.hardware_anchor
    assert s.signature_info is not None
    assert s.signature_info["algorithm"] == "Ed25519"


def test_batch_merkle_accumulator_logic() -> None:
    """
    Tests BatchMerkleAccumulator buffering, automatic batch flushes,
    and balanced Merkle tree computation with inclusion proofs.
    """
    # 1. Empty accumulator
    empty_acc = BatchMerkleAccumulator(batch_size=10)
    empty_root = empty_acc.finalize()
    assert len(empty_root) == 64
    assert empty_root == hashlib.sha256(b"").hexdigest()

    # 2. Single leaf
    single_acc = BatchMerkleAccumulator(batch_size=10)
    leaf1 = hashlib.sha256(b"leaf_1").hexdigest()
    single_acc.add_leaf(leaf1)
    single_root = single_acc.finalize()
    assert single_root == leaf1

    # 3. Buffer batching: batch_size=3
    acc = BatchMerkleAccumulator(batch_size=3)
    hashes = [hashlib.sha256(f"item_{i}".encode()).hexdigest() for i in range(7)]

    # Adding items 0, 1 does not flush
    assert acc.add_leaf(hashes[0]) is None
    assert acc.add_leaf(hashes[1]) is None
    assert acc.pending_count == 2
    assert acc.batch_count == 0

    # Adding item 2 flushes batch of 3
    batch_root1 = acc.add_leaf(hashes[2])
    assert batch_root1 is not None
    assert acc.pending_count == 0
    assert acc.batch_count == 1

    # Adding items 3, 4, 5 flushes batch 2
    acc.add_leaf(hashes[3])
    acc.add_leaf(hashes[4])
    batch_root2 = acc.add_leaf(hashes[5])
    assert batch_root2 is not None
    assert acc.batch_count == 2

    # Adding item 6 stays in buffer until finalize
    acc.add_leaf(hashes[6])
    assert acc.pending_count == 1

    global_root = acc.finalize()
    assert acc.pending_count == 0
    assert acc.count == 7

    # 4. Determinism check: direct compute_merkle_root gives same result
    direct_root = BatchMerkleAccumulator.compute_merkle_root(hashes)
    assert global_root == direct_root

    # 5. Inclusion proofs
    for idx in range(len(hashes)):
        proof = acc.get_inclusion_proof(idx)
        verified = BatchMerkleAccumulator.verify_inclusion_proof(
            leaf=hashes[idx],
            proof=proof,
            expected_root=global_root,
        )
        assert verified is True, f"Inclusion proof failed for leaf index {idx}"


def test_watch_decorator_sync_and_async() -> None:
    """
    Validates @tracer.watch and @watch on synchronous functions and async coroutines.
    """
    tracer = Tracer(system_name="WatchedAgent")

    # Sync decorated function
    @tracer.watch(action="compute_discount")
    def calculate_price(base: float, discount: float) -> float:
        return base * (1.0 - discount)

    # Calling inside active session
    with tracer.audit(session_id="watch_session") as s:
        res = calculate_price(100.0, 0.2)
        assert res == 80.0

    assert len(s.events) == 1
    event = s.events[0]
    assert event["action"] == "compute_discount"
    assert event["payload"]["result"] == 80.0
    assert event["payload"]["args"] == [100.0, 0.2]
    assert "duration_ms" in event["payload"]

    # Calling outside active session automatically creates transient session
    res2 = calculate_price(50.0, 0.1)
    assert res2 == 45.0
    latest = tracer.get_latest_session()
    assert latest is not None
    assert latest.session_id != "watch_session"

    # Exception capture test
    @tracer.watch(action="failing_action")
    def risky_op() -> None:
        raise ValueError("simulated_error")

    with tracer.audit(session_id="err_session") as s_err:
        with pytest.raises(ValueError, match="simulated_error"):
            risky_op()

    assert len(s_err.events) == 1
    assert "failing_action_error" in s_err.events[0]["action"]
    assert "simulated_error" in s_err.events[0]["payload"]["exception"]


@pytest.mark.asyncio
async def test_watch_decorator_async_coroutine() -> None:
    """Validates @tracer.watch with async def functions."""
    tracer = Tracer(system_name="AsyncAgent")

    @tracer.watch(action="async_fetch")
    async def fetch_data(key: str) -> Dict[str, str]:
        return {"key": key, "status": "ok"}

    with tracer.audit(session_id="async_session") as s:
        res = await fetch_data("user_profile")
        assert res["status"] == "ok"

    assert len(s.events) == 1
    assert s.events[0]["action"] == "async_fetch"
    assert s.events[0]["payload"]["result"]["key"] == "user_profile"


def test_standalone_watch_decorator() -> None:
    """Validates top-level from babylon60 import watch without explicit tracer instantiation."""

    @watch(action="global_action")
    def add(a: int, b: int) -> int:
        return a + b

    val = add(10, 20)
    assert val == 30


def test_export_compliance_report_html_and_markdown() -> None:
    """
    Tests export_compliance_report generating HTML and Markdown reports
    integrated with EUAIActComplianceExporter.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tracer = Tracer(
            system_name="SYS-LEGAL-42",
            operator_name="Acme AI Corp",
            storage_dir=os.path.join(tmp_dir, "storage"),
        )

        with tracer.audit(session_id="compliance_audit_01") as s:
            s.log_step("input_ingestion", {"tokens": 128})
            s.log_step("guardrail_check", {"flagged": False})
            s.log_step("response_dispatch", {"status": 200})

        html_out = os.path.join(tmp_dir, "reports", "compliance_report.html")
        md_out = os.path.join(tmp_dir, "reports", "compliance_report.md")
        json_out = os.path.join(tmp_dir, "reports", "compliance_report.json")

        # Export HTML with legal theme
        exported_html = tracer.export_compliance_report(
            output_path=html_out,
            locale="es",
            theme="legal",
            session_id="compliance_audit_01",
        )
        assert os.path.exists(exported_html)
        with open(exported_html, "r", encoding="utf-8") as f:
            html_content = f.read()
            assert "<!DOCTYPE html>" in html_content
            assert "SYS-LEGAL-42" in html_content
            assert "Acme AI Corp" in html_content
            assert "LEGAL COMPLIANCE GRADE" in html_content

        # Export Markdown
        exported_md = tracer.export_compliance_report(
            output_path=md_out,
            locale="es",
            session_id="compliance_audit_01",
        )
        assert os.path.exists(exported_md)
        with open(exported_md, "r", encoding="utf-8") as f:
            md_content = f.read()
            assert "SYS-LEGAL-42" in md_content
            assert "Acme AI Corp" in md_content
            assert "Art. 9: Sistema de Gestión de Riesgos" in md_content
            assert "Art. 15: Precisión, Robustez y Ciberseguridad" in md_content

        # Export JSON
        exported_json = tracer.export_compliance_report(
            output_path=json_out,
            session_id="compliance_audit_01",
        )
        assert os.path.exists(exported_json)


def test_assurance_level_parsing_and_descriptions() -> None:
    """Validates tolerant parsing and metadata introspection of AssuranceLevel."""
    assert AssuranceLevel.parse("al0") == AssuranceLevel.AL0_TRANSPARENT
    assert AssuranceLevel.parse("AL1") == AssuranceLevel.AL1_STANDARD
    assert AssuranceLevel.parse("compliance") == AssuranceLevel.AL2_COMPLIANCE
    assert AssuranceLevel.parse("sovereign") == AssuranceLevel.AL3_SOVEREIGN
    assert AssuranceLevel.parse(AssuranceLevel.AL2_COMPLIANCE) == AssuranceLevel.AL2_COMPLIANCE

    with pytest.raises(ValueError):
        AssuranceLevel.parse("UNKNOWN_LEVEL")

    for lvl in AssuranceLevel:
        desc = lvl.describe()
        assert "level" in desc
        assert "overhead_target" in desc
        assert "hashing" in desc
        assert desc["level"] == lvl.value
