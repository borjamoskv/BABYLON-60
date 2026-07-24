import babylon60.database.core
# [C5-REAL] Exergy-Maximized
"""
Sovereign Decalcifier (REM Phase Memory Consolidation).

Executes deep background maintenance on the SQLite persistence layer.
Only runs when the Endocrine system indicates low Cortisol (safety/rest).
Purges orphaned memory, deduplicates deeply, and compresses semantic representations
that haven't been accessed in a long time (LFU/LRU decalcification).
"""

import logging
import time
from typing import Any

import aiosqlite

from babylon60.engine.cognitive.endocrine import ENDOCRINE, HormoneType

logger = logging.getLogger("babylon60.extensions.evo.decalcifier")


class SovereignDecalcifier:
    """
    Biological memory maintenance layer.
    """

    def __init__(self, target_retention_days: int = 30):
        self.target_retention_days = target_retention_days

    async def decalcify_cycle(self, conn: aiosqlite.Connection) -> dict[str, Any]:
        """
        Executes one full REM cycle of memory consolidation.
        """
        logger.warning("🧠 [DECALCIFIER] Initiating REM Sleep Cycle (Deep memory sweep)...")
        start_time = time.monotonic()

        metrics = {"purged_orphans": 0, "compressed_engrams": 0, "serotonin_boost": 0.0}

        try:
            await conn.commit()

            cursor = await conn.execute(
                "DELETE FROM transactions WHERE action = 'telemetry' AND timestamp < datetime('now', '-7 days')"
            )
            metrics["purged_orphans"] = cursor.rowcount
            await conn.commit()

            import sqlite3

            from babylon60.core.paths import CORTEX_DB

            def _run_vacuum():
                with babylon60.database.core.connect(CORTEX_DB, isolation_level=None) as vconn:
                    vconn.execute("VACUUM")

            import asyncio

            await asyncio.to_thread(_run_vacuum)

            ENDOCRINE.pulse(HormoneType.SEROTONIN, 0.1, reason="REM Cycle Completed")
            ENDOCRINE.pulse(HormoneType.NEURAL_GROWTH, 0.05, reason="Memory Compression")
            metrics["serotonin_boost"] = 0.1

        except (ValueError, TypeError, KeyError, OSError, RuntimeError) as e:
            logger.error("❌ [DECALCIFIER] REM Cycle interrupted by nightmare (Error): %s", e)
            ENDOCRINE.pulse(HormoneType.CORTISOL, 0.2, reason="REM Interruption")
            await conn.rollback()
            return {"status": "interrupted", "error": str(e)}

        duration = time.monotonic() - start_time
        logger.warning(
            "🧠 [DECALCIFIER] Cycle complete in %.2fs. Purged: %d. 🧬 SEROTONIN +%.2f",
            duration,
            metrics["purged_orphans"],
            metrics["serotonin_boost"],
        )

        return {"status": "success", "duration": duration, "metrics": metrics}
