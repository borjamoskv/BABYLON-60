import os
from pathlib import Path

import pytest

from babylon60.bft.master_ledger_queue import MasterLedgerQueue


@pytest.mark.asyncio
async def test_master_ledger_queue_single_writer(tmp_path: Path) -> None:
    db_file = os.path.join(tmp_path, "test_bft_queue.db")
    queue = MasterLedgerQueue(db_file)
    await queue.initialize()
    try:
        await queue.submit_transaction("CREATE TABLE IF NOT EXISTS test_items (id int PRIMARY KEY, val TEXT);", ())
        for i in range(50):
            await queue.submit_transaction("INSERT INTO test_items (id, val) VALUES (?, ?);", (i, f"item_{i}"))
        await queue.queue.join()
        assert queue.db is not None
        async with queue.db.execute("SELECT COUNT(*) FROM test_items;") as cursor:
            row = await cursor.fetchone()
            assert row is not None
            assert row[0] == 50
    finally:
        await queue.shutdown()
