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
import base64
import hashlib
import json
import sqlite3
from collections.abc import AsyncIterator
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from nacl.signing import SigningKey, VerifyKey

from babylon60.bft import cortex_persist_ledger, ledger_actor
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


_REKOR_TEST_SEED = "19" * 32


@pytest.fixture(params=["cortex", "actor"])
async def rekor_ledger(
    tmp_path: Path, request: pytest.FixtureRequest
) -> AsyncIterator[tuple[CortexPersistLedger | BFTLedgerActor, Path, str, str]]:
    db_path = tmp_path / "rekor_test.db"
    event = CortexEvent(
        event_type="REKOR_EVENT",
        payload={"data": "transparency"},
        cortex_taint="TAINT_REKOR",
    )
    if request.param == "cortex":
        ledger = CortexPersistLedger(db_path)
        ledger.append_event(event)
        yield ledger, db_path, "cortex_ledger", "trg_cortex_no_update"
    else:
        actor = BFTLedgerActor(db_path)
        await actor.start()
        try:
            await actor.append_cortex_event(event)
            yield actor, db_path, "ledger_entries", "trg_ledger_immutable_update"
        finally:
            await actor.stop()


async def _anchor(
    ledger: CortexPersistLedger | BFTLedgerActor, client: MagicMock, seed_hex: str | None = None
) -> dict[str, Any] | None:
    if isinstance(ledger, BFTLedgerActor):
        return await ledger.anchor_to_rekor(rekor_client=client, seed_hex=seed_hex)
    return ledger.anchor_to_rekor(rekor_client=client, seed_hex=seed_hex)


@pytest.fixture
def rekor_client() -> MagicMock:
    mock_rekor = MagicMock(spec=RekorClient)
    mock_rekor.anchor_payload.return_value = {
        "uuid": "392095f9a72387a2139823489123849123849123849123849123849123849123",
        "logIndex": 42000,
        "integratedTime": 1726000000,
    }
    return mock_rekor


@pytest.mark.asyncio
@pytest.mark.parametrize("explicit_seed", [False, True], ids=["environment", "explicit"])
async def test_rekor_anchoring_mock_flow(
    rekor_ledger: tuple[CortexPersistLedger | BFTLedgerActor, Path, str, str],
    rekor_client: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    explicit_seed: bool,
) -> None:
    ledger, _, _, _ = rekor_ledger
    fixed_time = datetime(2026, 11, 13, tzinfo=timezone.utc)

    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_time

    monkeypatch.setattr(cortex_persist_ledger, "datetime", FixedDatetime)
    monkeypatch.setattr(ledger_actor, "datetime", FixedDatetime)
    monkeypatch.setenv("BABYLON60_SIGNING_SEED", "36" * 32 if explicit_seed else _REKOR_TEST_SEED)
    seed = _REKOR_TEST_SEED if explicit_seed else None

    attestation = (
        await ledger.get_state_attestation() if isinstance(ledger, BFTLedgerActor) else ledger.get_state_attestation()
    )
    assert attestation["integrity_verified"] is True
    head = {
        "merkle_root": attestation["merkle_root"],
        "max_lamport": 1,
        "total_entries": 1,
        "attested_at": fixed_time.isoformat(),
    }
    payload = json.dumps(head, sort_keys=True, separators=(",", ":")).encode()

    for _ in range(2):
        result = await _anchor(ledger, rekor_client, seed)
        assert result == rekor_client.anchor_payload.return_value
    assert rekor_client.anchor_payload.call_count == 2
    expected_key = SigningKey(bytes.fromhex(_REKOR_TEST_SEED)).verify_key.encode()
    for call in rekor_client.anchor_payload.call_args_list:
        payload_hash, signature, public_key = call.args
        assert payload_hash == hashlib.sha256(payload).hexdigest()
        assert base64.b64decode(public_key) == expected_key
        assert VerifyKey(expected_key).verify(payload, base64.b64decode(signature)) == payload


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("seed_hex", "env_seed"),
    [
        (None, None),
        (None, "not-hex"),
        ("19", None),
        ("", _REKOR_TEST_SEED),
        ("not-hex", _REKOR_TEST_SEED),
    ],
    ids=["missing", "malformed-environment", "wrong-length", "explicit-empty", "explicit-malformed"],
)
async def test_rekor_rejects_unconfigured_or_invalid_seed(
    rekor_ledger: tuple[CortexPersistLedger | BFTLedgerActor, Path, str, str],
    rekor_client: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    seed_hex: str | None,
    env_seed: str | None,
) -> None:
    ledger, _, _, _ = rekor_ledger
    if env_seed is None:
        monkeypatch.delenv("BABYLON60_SIGNING_SEED", raising=False)
    else:
        monkeypatch.setenv("BABYLON60_SIGNING_SEED", env_seed)
    result = await _anchor(ledger, rekor_client, seed_hex)
    rekor_client.anchor_payload.assert_not_called()
    assert result is None


@pytest.mark.asyncio
async def test_rekor_rejects_tampered_ledger(
    rekor_ledger: tuple[CortexPersistLedger | BFTLedgerActor, Path, str, str], rekor_client: MagicMock
) -> None:
    ledger, db_path, table, trigger = rekor_ledger
    with closing(sqlite3.connect(db_path)) as conn, conn:
        conn.execute(f"DROP TRIGGER {trigger}")
        conn.execute(f'UPDATE {table} SET payload_json = \'{{"data":"altered"}}\' WHERE seq = 1')

    attestation = (
        await ledger.get_state_attestation() if isinstance(ledger, BFTLedgerActor) else ledger.get_state_attestation()
    )
    assert attestation["integrity_verified"] is False
    result = await _anchor(ledger, rekor_client, _REKOR_TEST_SEED)
    rekor_client.anchor_payload.assert_not_called()
    assert result is None


@pytest.mark.asyncio
async def test_rekor_actor_verifies_the_snapshot_it_would_sign(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, rekor_client: MagicMock
) -> None:
    db_path = tmp_path / "actor_rekor_snapshot.db"
    actor = BFTLedgerActor(db_path)
    await actor.start()
    try:
        await actor.append_cortex_event(CortexEvent("REKOR_EVENT", {"data": "transparency"}, "TAINT_REKOR"))
    finally:
        await actor.stop()

    with closing(sqlite3.connect(db_path)) as conn, conn:
        entry_hash = conn.execute("SELECT entry_hash FROM ledger_entries WHERE seq = 1").fetchone()[0]
        conn.execute("DROP TRIGGER trg_ledger_immutable_update")
        conn.execute("UPDATE ledger_entries SET entry_hash = ? WHERE seq = 1", ("ab" * 32,))
    from babylon60.bft.cortex_crypto_kernel import build_merkle_tree

    def restore_after_read(leaves):
        with closing(sqlite3.connect(db_path)) as conn, conn:
            conn.execute("UPDATE ledger_entries SET entry_hash = ? WHERE seq = 1", (entry_hash,))
        return build_merkle_tree(leaves)

    monkeypatch.setattr(ledger_actor, "build_merkle_tree", restore_after_read)
    result = await actor.anchor_to_rekor(rekor_client=rekor_client, seed_hex=_REKOR_TEST_SEED)
    assert await actor.verify_chain() is True
    rekor_client.anchor_payload.assert_not_called()
    assert result is None


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
