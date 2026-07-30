# [C5-REAL] Exergy-Maximized
"""Tests for VecApoptosisEngine."""

import pytest
import aiosqlite
from babylon60.engine.core.vec_apoptosis import VecApoptosisEngine


@pytest.fixture
async def mock_db():
    async with aiosqlite.connect(":memory:") as db:
        # Create a mock facts table
        await db.execute(
            "CREATE TABLE facts (id INTEGER PRIMARY KEY, is_tombstoned INTEGER DEFAULT 0)"
        )
        # Create a mock vec0 table (regular table for test purposes)
        await db.execute(
            "CREATE TABLE cortex_embeddings_text (rowid INTEGER PRIMARY KEY, embedding BLOB)"
        )

        # Insert test facts
        await db.execute("INSERT INTO facts (id, is_tombstoned) VALUES (1, 0)")  # Valid
        await db.execute("INSERT INTO facts (id, is_tombstoned) VALUES (2, 1)")  # Tombstoned

        # Insert embeddings
        await db.execute(
            "INSERT INTO cortex_embeddings_text (rowid, embedding) VALUES (1, x'00')"
        )  # Matches valid
        await db.execute(
            "INSERT INTO cortex_embeddings_text (rowid, embedding) VALUES (2, x'00')"
        )  # Matches tombstoned
        await db.execute(
            "INSERT INTO cortex_embeddings_text (rowid, embedding) VALUES (3, x'00')"
        )  # Orphan (no fact)

        await db.commit()
        yield db


@pytest.mark.asyncio
async def test_vec_apoptosis_sweeps_orphans(mock_db):
    engine = VecApoptosisEngine(mock_db)

    # Run apoptosis
    results = await engine.run_apoptosis()

    # Verify results
    assert "cortex_embeddings_text" in results
    assert results["cortex_embeddings_text"] == 2  # Row 2 (tombstoned) and Row 3 (orphan)

    # Verify DB state
    async with mock_db.execute("SELECT rowid FROM cortex_embeddings_text") as cursor:
        rows = await cursor.fetchall()

    assert len(rows) == 1
    assert rows[0][0] == 1  # Only the valid fact embedding remains


@pytest.mark.asyncio
async def test_vec_apoptosis_ignores_missing_tables(mock_db):
    engine = VecApoptosisEngine(mock_db)
    results = await engine.run_apoptosis()
    # It shouldn't crash on missing 'cortex_embeddings_visual'
    assert "cortex_embeddings_visual" not in results
