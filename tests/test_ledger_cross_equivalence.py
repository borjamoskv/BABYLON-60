# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# Regression & Equivalence Tests for Issue #13 (R-8)
# - Consolidación de ledgers (CortexPersistLedger ↔ BFTLedgerActor)
# - Verificación de PRAGMA synchronous = FULL (INV_C5_WAL_SYNCHRONOUS_FULL)
# - Anclaje externo Rekor-style de ledger-heads
# ============================================================================

from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from babylon60.bft.cortex_persist_ledger import CortexEvent, CortexPersistFacade, CortexPersistLedger
from babylon60.bft.ledger_actor import BFTLedgerActor, cortex_event_to_ledger_event
from babylon60.compliance_exporter.eu_ai_act import EUAIActComplianceExporter
from babylon60.crypto.rekor_client import RekorClient


@pytest.mark.asyncio
async def test_synchronous_full_invariant_on_both_ledgers(tmp_path: Path) -> None:
    """Verifica que ambos ledgers aplican estrictamente PRAGMA synchronous = FULL."""
    # 1. CortexPersistLedger
    sync_db = tmp_path / "sync_durability.db"
    cortex_ledger = CortexPersistLedger(sync_db)
    ev = CortexEvent(
        event_type="TEST_DURABILITY",
        payload={"msg": "test"},
        cortex_taint="C5_TAINT_DURABILITY",
    )
    cortex_ledger.append_event(ev)

    conn = sqlite3.connect(sync_db)
    cur = conn.cursor()
    cur.execute("PRAGMA synchronous;")
    sync_mode = cur.fetchone()[0]
    conn.close()
    # En SQLite, synchronous = FULL se reporta como 2
    assert sync_mode == 2, f"CortexPersistLedger PRAGMA synchronous debe ser 2 (FULL), recibido {sync_mode}"

    # 2. BFTLedgerActor
    async_db = tmp_path / "async_durability.db"
    actor = BFTLedgerActor(async_db)
    await actor.start()
    try:
        fut = actor.append_cortex_event(ev)
        await fut
    finally:
        await actor.stop()

    conn = sqlite3.connect(async_db)
    cur = conn.cursor()
    cur.execute("PRAGMA synchronous;")
    async_sync_mode = cur.fetchone()[0]
    conn.close()
    assert async_sync_mode == 2, f"BFTLedgerActor PRAGMA synchronous debe ser 2 (FULL), recibido {async_sync_mode}"


@pytest.mark.asyncio
async def test_bft_actor_cortex_event_ingestion_and_state_attestation(tmp_path: Path) -> None:
    """Prueba la ingestión de CortexEvent en BFTLedgerActor y la generación de StateAttestation con Merkle root."""
    db_path = tmp_path / "actor_attestation.db"
    actor = BFTLedgerActor(db_path)
    await actor.start()

    events = [
        CortexEvent(
            event_type="ACTION_1",
            payload={"step": 1},
            cortex_taint="TAINT_1",
            agent_id="AGENT_A",
        ),
        CortexEvent(
            event_type="ACTION_2",
            payload={"step": 2},
            cortex_taint="TAINT_2",
            agent_id="AGENT_B",
        ),
        CortexEvent(
            event_type="ACTION_3",
            payload={"step": 3},
            cortex_taint="TAINT_3",
            agent_id="AGENT_C",
        ),
    ]

    for ev in events:
        res = await actor.append_cortex_event(ev)
        assert res["seq"] > 0
        assert len(res["entry_hash"]) == 64

    attestation = await actor.get_state_attestation()
    assert attestation["total_entries"] == 3
    assert attestation["max_seq"] == 3
    assert attestation["max_lamport"] == 3
    assert attestation["integrity_verified"] is True
    assert len(attestation["merkle_root"]) == 64
    assert len(attestation["mmr_root"]) == 64

    # Verificar que el Merkle root calculado coincide exactamente con build_merkle_tree
    merkle_direct = await actor.get_merkle_root()
    assert merkle_direct == attestation["merkle_root"]

    await actor.stop()


def test_cortex_event_to_ledger_event_mapping() -> None:
    """Verifica que el mapper preserves invariantes semánticos."""
    c_ev = CortexEvent(
        event_type="INFERENCE_DONE",
        payload={"tokens": 42},
        cortex_taint="TAINT_MOSKV",
        agent_id="AGENT_MOSKV_1",
        domain="babylon60.test",
    )
    l_ev = cortex_event_to_ledger_event(c_ev)
    assert l_ev.stream == "cortex"
    assert l_ev.entity_id == "AGENT_MOSKV_1"
    assert l_ev.event_type == "INFERENCE_DONE"
    assert l_ev.payload == {"tokens": 42}
    assert l_ev.cortex_taint == "TAINT_MOSKV"
    assert l_ev.source_db == "babylon60.test"
    assert l_ev.source_table == "cortex_ledger"
    assert l_ev.agent_id == "AGENT_MOSKV_1"

    # Método de conveniencia en CortexEvent
    l_ev2 = c_ev.to_ledger_event()
    assert l_ev2 == l_ev


def test_cortex_persist_facade_sync_execution(tmp_path: Path) -> None:
    """Valida la fachada síncrona CortexPersistFacade sobre BFTLedgerActor."""
    db_path = tmp_path / "facade.db"
    facade = CortexPersistFacade(db_path)

    ev1 = CortexEvent(
        event_type="SYNC_STEP_1",
        payload={"val": 100},
        cortex_taint="FACADE_TAINT",
    )
    res1 = facade.append_event(ev1)
    assert res1["seq"] == 1
    assert res1["status"] == "C5_PERMANENT"
    assert len(res1["entry_hash"]) == 64

    ev2 = CortexEvent(
        event_type="SYNC_STEP_2",
        payload={"val": 200},
        cortex_taint="FACADE_TAINT",
    )
    res2 = facade.append_event(ev2)
    assert res2["seq"] == 2

    is_valid, msg = facade.verify_integrity()
    assert is_valid is True
    assert msg == "CADENA_INTEGRA"

    attestation = facade.get_state_attestation()
    assert attestation["total_entries"] == 2
    assert attestation["integrity_verified"] is True


@pytest.mark.asyncio
async def test_rekor_anchoring_mock_flow(tmp_path: Path) -> None:
    """Verifica el flujo de anclaje Rekor-style para ledger-heads."""
    db_path = tmp_path / "rekor_test.db"
    actor = BFTLedgerActor(db_path)
    await actor.start()

    ev = CortexEvent(
        event_type="REKOR_EVENT",
        payload={"data": "transparency"},
        cortex_taint="TAINT_REKOR",
    )
    await actor.append_cortex_event(ev)

    mock_rekor = MagicMock(spec=RekorClient)
    mock_rekor.anchor_payload.return_value = {
        "uuid": "392095f9a72387a2139823489123849123849123849123849123849123849123",
        "logIndex": 42000,
        "integratedTime": 1726000000,
    }

    result = await actor.anchor_to_rekor(rekor_client=mock_rekor)
    assert result is not None
    assert str(result["uuid"]).startswith("392095f9")
    assert result["logIndex"] == 42000
    assert mock_rekor.anchor_payload.called

    await actor.stop()

    # Probar también en CortexPersistLedger
    sync_db = tmp_path / "sync_rekor.db"
    sync_ledger = CortexPersistLedger(sync_db)
    sync_ledger.append_event(ev)
    sync_result = sync_ledger.anchor_to_rekor(rekor_client=mock_rekor)
    assert sync_result is not None
    assert sync_result["logIndex"] == 42000


def test_eu_ai_act_compliance_dual_schema_verification(tmp_path: Path) -> None:
    """Verifica que verify_evidence del exportador EU AI Act valida tanto BFTLedgerActor como CortexPersistLedger."""
    exporter = EUAIActComplianceExporter()

    # 1. Base de datos generada por BFTLedgerActor (tabla ledger_entries)
    actor_db = tmp_path / "actor_compliance.db"
    actor = BFTLedgerActor(actor_db)

    async def _init_actor() -> str:
        await actor.start()
        await actor.append_cortex_event(
            CortexEvent(
                event_type="COMPLIANCE_EV",
                payload={"check": True},
                cortex_taint="TAINT_COMPLIANCE",
            )
        )
        att = await actor.get_state_attestation()
        await actor.stop()
        return str(att["merkle_root"])

    merkle_root_actor = asyncio.run(_init_actor())

    manifest_actor = {"global_hash": merkle_root_actor}
    v_actor = exporter.verify_evidence(manifest_actor, str(actor_db))
    assert v_actor["ledger_present"] is True
    assert v_actor["integrity_verified"] is True
    assert v_actor["evidence_match"] is True
    assert v_actor["verified"] is True
    assert v_actor["ledger_total_entries"] == 1

    # 2. Base de datos generada por CortexPersistLedger (tabla cortex_ledger)
    cortex_db = tmp_path / "cortex_compliance.db"
    c_ledger = CortexPersistLedger(cortex_db)
    c_ledger.append_event(
        CortexEvent(
            event_type="COMPLIANCE_EV",
            payload={"check": True},
            cortex_taint="TAINT_COMPLIANCE",
        )
    )
    att_cortex = c_ledger.get_state_attestation()
    manifest_cortex = {"global_hash": att_cortex["merkle_root"]}

    v_cortex = exporter.verify_evidence(manifest_cortex, str(cortex_db))
    assert v_cortex["ledger_present"] is True
    assert v_cortex["integrity_verified"] is True
    assert v_cortex["evidence_match"] is True
    assert v_cortex["verified"] is True
