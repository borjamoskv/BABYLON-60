# [C5-REAL] Exergy-Maximized
"""
Vector Apoptosis Engine (VEC-0 Garbage Collector).

Enforces Invariant 13 (I-068): vec0 virtual tables do not support Foreign Keys.
This engine sweeps `cortex_embeddings_text` and `cortex_embeddings_visual`
to destroy orphaned embeddings whose parent fact has been tombstoned or hard-deleted.
"""

import logging

import aiosqlite

logger = logging.getLogger("babylon60.engine.core.vec_apoptosis")


class VecApoptosisEngine:
    """Garbage collector for SQLite-Vec virtual tables."""

    VEC_TABLES = [
        "cortex_embeddings_text",
        "cortex_embeddings_visual",
        "cortex_embeddings",
    ]

    def __init__(self, conn: aiosqlite.Connection):
        self.conn = conn

    async def _table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        async with self.conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
        ) as cursor:
            return await cursor.fetchone() is not None

    async def run_apoptosis(self) -> dict[str, int]:
        """Sweep vector tables and destroy orphaned rows.

        Returns:
            Dict mapping table names to number of destroyed orphans.
        """
        results = {}
        for table in self.VEC_TABLES:
            if not await self._table_exists(table):
                continue

            try:
                # Find orphans: rowids in the vector table that do not exist in facts
                # or belong to facts that are tombstoned (is_tombstoned = 1).
                query = f"""
                    DELETE FROM {table}
                    WHERE rowid IN (
                        SELECT v.rowid
                        FROM {table} v
                        LEFT JOIN facts f ON v.rowid = f.id
                        WHERE f.id IS NULL OR f.is_tombstoned = 1
                    )
                """
                async with self.conn.execute(query) as cursor:
                    deleted_count = cursor.rowcount
                    results[table] = deleted_count
                    if deleted_count > 0:
                        logger.info(
                            "[VEC-0 Apoptosis] Destroyed %d orphaned embeddings in '%s'.",
                            deleted_count,
                            table,
                        )
            except Exception as e:  # noqa: BLE001
                logger.error("[VEC-0 Apoptosis] Failed to sweep '%s': %s", table, e)

        return results
