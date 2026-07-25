from __future__ import annotations

import asyncio
from pathlib import Path

import aiosqlite
import pytest
from cryptography.fernet import Fernet

from babylon60.bft.ledger_actor import BFTCausalInvariantError, BFTLedgerActor, LedgerEvent


def _event(i: int) -> LedgerEvent:
    return LedgerEvent(stream='vault', entity_id=f'e{i}', event_type='CREATED', payload={'count': i, 'secret': 'materia-cifrada'}, source_db='test', source_table='t', source_pk=str(i), cortex_taint=f'taint:test:{i}')

@pytest.mark.asyncio
async def test_verify_chain_valida_ledger_cifrado(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('CORTEX_VAULT_KEY', Fernet.generate_key().decode())
    actor = BFTLedgerActor(tmp_path / 'vault.db')
    await actor.start()
    for i in range(3):
        await actor.append(_event(i))
    assert await actor.verify_chain() is True
    await actor.stop()

@pytest.mark.asyncio
async def test_verificador_vivo_sin_clave(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('CORTEX_VAULT_KEY', Fernet.generate_key().decode())
    db = tmp_path / 'vault.db'
    actor = BFTLedgerActor(db)
    await actor.start()
    for i in range(2):
        await actor.append(_event(i))
    await actor.stop()
    monkeypatch.delenv('CORTEX_VAULT_KEY')
    assert await BFTLedgerActor(db).verify_chain() is True

@pytest.mark.asyncio
async def test_tamper_bajo_cifrado_sigue_detectandose(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('CORTEX_VAULT_KEY', Fernet.generate_key().decode())
    db = tmp_path / 'vault.db'
    actor = BFTLedgerActor(db)
    await actor.start()
    for i in range(3):
        await actor.append(_event(i))
    await actor.stop()
    async with aiosqlite.connect(db) as conn:
        await conn.execute('DROP TRIGGER trg_ledger_immutable_update')
        await conn.execute("UPDATE ledger_entries SET payload_json = 'C5ENC:forjado' WHERE seq = 2")
        await conn.commit()
    with pytest.raises(BFTCausalInvariantError, match='INV_BFT_LEAN_04'):
        await BFTLedgerActor(db).verify_chain()

@pytest.mark.asyncio
async def test_falla_ruidosa_sin_necrosis(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    actor = BFTLedgerActor(tmp_path / 'vault.db')
    await actor.start()

    async def _boom(*args: object, **kwargs: object) -> tuple[int, str]:
        raise RuntimeError('boom-causal')
    monkeypatch.setattr(actor, '_execute_insert_tx', _boom)
    with pytest.raises(RuntimeError):
        await actor.append(_event(0))
    await asyncio.sleep(0.05)
    with pytest.raises(RuntimeError, match='Zombie Actor Prevention'):
        actor.append(_event(1))
    await actor.stop()