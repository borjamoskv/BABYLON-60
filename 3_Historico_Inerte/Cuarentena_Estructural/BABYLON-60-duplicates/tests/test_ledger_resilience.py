# C5-REAL EXERGY CERTIFIED
import pytest
import aiosqlite
from pathlib import Path
from babylon60.bft.ledger_actor import BFTLedgerActor, LedgerEvent
from typing import AsyncGenerator


@pytest.fixture
async def ephemeral_ledger(tmp_path: Path) -> AsyncGenerator[BFTLedgerActor, None]:
    db_path = tmp_path / "test_resilience.db"
    actor = BFTLedgerActor(db_path)
    await actor.start()
    yield actor
    await actor.stop()


@pytest.mark.asyncio
async def test_idempotent_writes(ephemeral_ledger: BFTLedgerActor) -> None:
    """
    Validation of split-brain prevention (Idempotency).
    Injecting the exact same payload should yield the exact same event_id and hash without duplication.
    """
    event = LedgerEvent(
        stream="test",
        entity_id="test_entity_1",
        event_type="CREATED",
        payload={"data": "test_data"},
        source_db="test",
        source_table="test_table",
        source_pk="1",
        cortex_taint="C5_REAL_TEST",
    )

    # First insertion
    res1 = await ephemeral_ledger.append(event)

    # Second insertion (should hit ON CONFLICT DO NOTHING and return the existing record)
    res2 = await ephemeral_ledger.append(event)

    assert res1["event_id"] == res2["event_id"]
    assert res1["seq"] == res2["seq"]
    assert res1["entry_hash"] == res2["entry_hash"]

    # Verify the chain is valid
    chain_valid = await ephemeral_ledger.verify_chain()
    assert chain_valid is True

    # Verify that only 1 record exists in the DB
    async with aiosqlite.connect(ephemeral_ledger._db_path) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM ledger_entries")
        row = await cursor.fetchone()
        assert row is not None
        assert row[0] == 1


@pytest.mark.asyncio
async def test_hash_chain_corruption_detection(ephemeral_ledger: BFTLedgerActor) -> None:
    """
    Validation of tamper-evident properties.
    A manual tampering of a ledger entry must instantly invalidate the chain.
    """
    # Write valid entries
    for i in range(3):
        await ephemeral_ledger.append(
            LedgerEvent(
                stream="test",
                entity_id=f"test_entity_{i}",
                event_type="CREATED",
                payload={"count": i},
                source_db="test",
                source_table="test_table",
                source_pk=str(i),
                cortex_taint="C5_REAL_TEST",
            )
        )

    chain_valid = await ephemeral_ledger.verify_chain()
    assert chain_valid is True

    # Force corruption: Bypass the IMMUTABLE triggers and mutate data
    async with aiosqlite.connect(ephemeral_ledger._db_path) as db:
        # Drop trigger to allow tampering
        await db.execute("DROP TRIGGER trg_ledger_immutable_update")
        # Tamper with entry #2
        await db.execute("UPDATE ledger_entries SET payload_json = '{\"count\": 99}' WHERE seq = 2")
        await db.commit()

    # Verification should now fail
    from babylon60.bft.ledger_actor import BFTCausalInvariantError

    with pytest.raises(BFTCausalInvariantError, match="INV_BFT_LEAN_04"):
        await ephemeral_ledger.verify_chain()


@pytest.mark.asyncio
async def test_cascading_rollback_defense(ephemeral_ledger: BFTLedgerActor) -> None:
    """
    Validation of crash recovery/rollback.
    If an insertion fails midway (e.g. invalid taint), the actor rejects it and rolls back,
    without corrupting the ledger state for subsequent valid writes.
    """
    # 1. Valid write
    res1 = await ephemeral_ledger.append(
        LedgerEvent(
            stream="test",
            entity_id="1",
            event_type="CREATED",
            payload={},
            source_db="a",
            source_table="b",
            source_pk="c",
            cortex_taint="valid_taint",
        )
    )
    assert res1["seq"] == 1

    # 2. Invalid write (Missing taint will raise ValueError in _process)
    with pytest.raises(ValueError, match="INV_BFT_03: cortex_taint must be a non-empty string"):
        await ephemeral_ledger.append(
            LedgerEvent(
                stream="test",
                entity_id="2",
                event_type="CREATED",
                payload={},
                source_db="a",
                source_table="b",
                source_pk="c",
                cortex_taint="",  # This breaks INV_BFT_03
            )
        )

    # 3. Subsequent valid write should proceed sequentially without deadlocks
    res3 = await ephemeral_ledger.append(
        LedgerEvent(
            stream="test",
            entity_id="3",
            event_type="CREATED",
            payload={},
            source_db="a",
            source_table="b",
            source_pk="c",
            cortex_taint="valid_taint_2",
        )
    )
    assert res3["seq"] == 2  # Sequences continue correctly

    chain_valid = await ephemeral_ledger.verify_chain()
    assert chain_valid is True
