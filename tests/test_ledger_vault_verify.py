# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Falsación determinista de INV_C5_05 (verificador vivo) e INV_C5_07 (falla ruidosa).
# Génesis: AUDITORIA_CENTURIA §11.2 NEW-B (verify_chain roto bajo cifrado) + NEW-C (SIGKILL auto-necrosis).
from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import uuid

import aiosqlite
import pytest
from cryptography.fernet import Fernet

from babylon60.bft.ledger_actor import BFTCausalInvariantError, BFTLedgerActor, LedgerEvent


def _event(i: int) -> LedgerEvent:
    return LedgerEvent(
        stream="vault",
        entity_id=f"e{i}",
        event_type="CREATED",
        payload={"count": i, "secret": "materia-cifrada"},
        source_db="test",
        source_table="t",
        source_pk=str(i),
        cortex_taint=f"taint:test:{i}",
    )


@pytest.mark.asyncio
async def test_verify_chain_valida_ledger_cifrado(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """INV_C5_05: con CORTEX_VAULT_KEY activo, verify_chain DEBE validar la cadena que el INSERT escribió."""
    monkeypatch.setenv("CORTEX_VAULT_KEY", Fernet.generate_key().decode())
    actor = BFTLedgerActor(tmp_path / "vault.db")
    await actor.start()
    for i in range(3):
        await actor.append(_event(i))
    assert await actor.verify_chain() is True
    await actor.stop()


@pytest.mark.asyncio
async def test_verificador_vivo_sin_clave(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Historical V1 ciphertext remains verifiable without its key, before and after migration."""
    vault = Fernet(Fernet.generate_key())
    db = tmp_path / "vault.db"
    # Independent pre-versioning schema/hash oracle: no new actor write or legacy production flag.
    with sqlite3.connect(db) as conn:
        conn.execute("""CREATE TABLE ledger_entries (
            seq INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT NOT NULL UNIQUE,
            stream TEXT NOT NULL CHECK(length(stream)>0), entity_id TEXT NOT NULL CHECK(length(entity_id)>0),
            event_type TEXT NOT NULL CHECK(length(event_type)>0), payload_json TEXT NOT NULL CHECK(length(payload_json)>=2),
            source_db TEXT NOT NULL CHECK(length(source_db)>0), source_table TEXT NOT NULL CHECK(length(source_table)>0),
            source_pk TEXT NOT NULL CHECK(length(source_pk)>0), cortex_taint TEXT NOT NULL CHECK(length(cortex_taint)>0),
            lamport_t INTEGER NOT NULL CHECK(lamport_t>0), prev_hash TEXT NOT NULL CHECK(length(prev_hash)=64),
            entry_hash TEXT NOT NULL UNIQUE CHECK(length(entry_hash)=64), created_at TEXT NOT NULL,
            agent_id TEXT NOT NULL DEFAULT '', UNIQUE(lamport_t,agent_id))""")
        previous = "0" * 64
        for i in range(2):
            ev = _event(i)
            payload = json.dumps(ev.payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
            identity = f"test\x1ft\x1f{i}\x1f{payload}\x1f{ev.cortex_taint}"
            event_id = str(uuid.uuid5(uuid.UUID("9897d6fd-d6a7-4fe9-86bc-f0c312886d5d"), identity))
            stored = "C5ENC:" + vault.encrypt(payload.encode()).decode()
            body = dict(event_id=event_id, stream=ev.stream, entity_id=ev.entity_id, event_type=ev.event_type,
                        payload_json=stored, source_db=ev.source_db, source_table=ev.source_table,
                        source_pk=ev.source_pk, cortex_taint=ev.cortex_taint, lamport_t=i + 1,
                        prev_hash=previous, created_at="2020-01-01T00:00:00Z")
            encoded = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
            digest = hashlib.sha3_256(encoded.encode()).hexdigest()
            conn.execute("INSERT INTO ledger_entries VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                         (i + 1, event_id, ev.stream, ev.entity_id, ev.event_type, stored, ev.source_db,
                          ev.source_table, ev.source_pk, ev.cortex_taint, i + 1, previous, digest, body["created_at"], ""))
            previous = digest
    monkeypatch.delenv("CORTEX_VAULT_KEY", raising=False)
    monkeypatch.setitem(sys.modules, "strike_rs", None)
    actor = BFTLedgerActor(db)
    assert await actor.verify_chain() is True
    await actor.start()
    try:
        # Drain initialization without appending a V2 entry requiring a vault key.
        assert actor._task is not None
        stopping = asyncio.create_task(actor.stop())
        await asyncio.wait_for(stopping, timeout=5)
    finally:
        await actor.stop()
    assert await BFTLedgerActor(db).verify_chain() is True


@pytest.mark.asyncio
async def test_tamper_bajo_cifrado_sigue_detectandose(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """El fix no ciega al verificador: mutar una fila cifrada rompe la cadena (INV_BFT_LEAN_04)."""
    monkeypatch.setenv("CORTEX_VAULT_KEY", Fernet.generate_key().decode())
    db = tmp_path / "vault.db"
    actor = BFTLedgerActor(db)
    await actor.start()
    for i in range(3):
        await actor.append(_event(i))
    await actor.stop()
    async with aiosqlite.connect(db) as conn:
        await conn.execute("DROP TRIGGER trg_ledger_immutable_update")
        await conn.execute("UPDATE ledger_entries SET payload_json = 'C5ENC:forjado' WHERE seq = 2")
        await conn.commit()
    with pytest.raises(BFTCausalInvariantError, match="INV_BFT_LEAN_04"):
        await BFTLedgerActor(db).verify_chain()


@pytest.mark.asyncio
async def test_falla_ruidosa_sin_necrosis(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """INV_C5_07: un fallo no-ValueError del writer propaga la excepción al caller y mata al WORKER,
    nunca al proceso (cero os.kill/SIGKILL). El siguiente append detecta al actor zombi."""
    actor = BFTLedgerActor(tmp_path / "vault.db")
    await actor.start()

    async def _boom(*args: object, **kwargs: object) -> tuple[int, str]:
        raise RuntimeError("boom-causal")

    monkeypatch.setattr(actor, "_execute_insert_tx", _boom)
    with pytest.raises(RuntimeError):
        await actor.append(_event(0))
    await asyncio.sleep(0.05)
    with pytest.raises(RuntimeError, match="Zombie Actor Prevention"):
        actor.append(_event(1))
    await actor.stop()
