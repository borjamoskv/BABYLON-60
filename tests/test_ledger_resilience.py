from collections.abc import AsyncGenerator
from pathlib import Path

import aiosqlite
import pytest

from babylon60.bft.ledger_actor import BFTLedgerActor, LedgerEvent


@pytest.fixture
async def ephemeral_ledger(tmp_path: Path) -> AsyncGenerator[BFTLedgerActor, None]:
    db_path = tmp_path / 'test_resilience.db'
    actor = BFTLedgerActor(db_path)
    await actor.start()
    yield actor
    await actor.stop()

@pytest.mark.asyncio
async def test_idempotent_writes(ephemeral_ledger: BFTLedgerActor) -> None:
    event = LedgerEvent(stream='test', entity_id='test_entity_1', event_type='CREATED', payload={'data': 'test_data'}, source_db='test', source_table='test_table', source_pk='1', cortex_taint='C5_REAL_TEST')
    res1 = await ephemeral_ledger.append(event)
    res2 = await ephemeral_ledger.append(event)
    assert res1['event_id'] == res2['event_id']
    assert res1['seq'] == res2['seq']
    assert res1['entry_hash'] == res2['entry_hash']
    chain_valid = await ephemeral_ledger.verify_chain()
    assert chain_valid is True
    async with aiosqlite.connect(ephemeral_ledger._db_path) as db:
        cursor = await db.execute('SELECT COUNT(*) FROM ledger_entries')
        row = await cursor.fetchone()
        assert row is not None
        assert row[0] == 1

@pytest.mark.asyncio
async def test_hash_chain_corruption_detection(ephemeral_ledger: BFTLedgerActor) -> None:
    for i in range(3):
        await ephemeral_ledger.append(LedgerEvent(stream='test', entity_id=f'test_entity_{i}', event_type='CREATED', payload={'count': i}, source_db='test', source_table='test_table', source_pk=str(i), cortex_taint='C5_REAL_TEST'))
    chain_valid = await ephemeral_ledger.verify_chain()
    assert chain_valid is True
    async with aiosqlite.connect(ephemeral_ledger._db_path) as db:
        await db.execute('DROP TRIGGER trg_ledger_immutable_update')
        await db.execute('UPDATE ledger_entries SET payload_json = \'{"count": 99}\' WHERE seq = 2')
        await db.commit()
    from babylon60.bft.ledger_actor import BFTCausalInvariantError
    with pytest.raises(BFTCausalInvariantError, match='INV_BFT_LEAN_04'):
        await ephemeral_ledger.verify_chain()

@pytest.mark.asyncio
async def test_cascading_rollback_defense(ephemeral_ledger: BFTLedgerActor) -> None:
    res1 = await ephemeral_ledger.append(LedgerEvent(stream='test', entity_id='1', event_type='CREATED', payload={}, source_db='a', source_table='b', source_pk='c', cortex_taint='valid_taint'))
    assert res1['seq'] == 1
    with pytest.raises(ValueError, match='INV_BFT_03: cortex_taint must be a non-empty string'):
        await ephemeral_ledger.append(LedgerEvent(stream='test', entity_id='2', event_type='CREATED', payload={}, source_db='a', source_table='b', source_pk='c', cortex_taint=''))
    res3 = await ephemeral_ledger.append(LedgerEvent(stream='test', entity_id='3', event_type='CREATED', payload={}, source_db='a', source_table='b', source_pk='c', cortex_taint='valid_taint_2'))
    assert res3['seq'] == 2
    chain_valid = await ephemeral_ledger.verify_chain()
    assert chain_valid is True