# [C5-REAL] Exergy-Maximized
"""
from babylon60.extensions.training.moskv1_core import MOSKV1Core
MOSKV-1 Daemon Execution Entry Point.
Launches the nocturnal training loop with proper SQLite concurrency configurations.
"""

import asyncio
import logging
import sys
from pathlib import Path

from babylon60.database.core import connect_async  # type: ignore[attr-defined]
from babylon60.extensions.episodic.main import EpisodicMemory

log_dir = Path.home() / ".babylon60" / "training"
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_dir / "daemon.log", mode="a", encoding="utf-8"),
    ],
)

from babylon60.extensions.training.daemon import AutonomousTrainingDaemon


async def main():
    db_path = Path.home() / ".cortex" / "cortex.db"
    logging.info("🚀 Initializing MOSKV-1 Autonomous Training Daemon...")
    logging.info("   Database: %s", db_path)

    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = await connect_async(str(db_path), read_only=True)
    try:
        async with conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='episodes'"
        ) as cursor:
            if not await cursor.fetchone():
                logging.warning("⚠️ Table 'episodes' does not exist in the database.")

        episodic_memory = EpisodicMemory(conn)
        daemon = AutonomousTrainingDaemon(
            episodic_memory=episodic_memory,
            interval_seconds=3600,  # Run training check every hour
        )

        try:
            from babylon60.extensions.training.moskv1_core import MOSKV1Core

            core = MOSKV1Core()
            await core.warmup()
        except (ValueError, TypeError, KeyError, RuntimeError, OSError, AssertionError) as e:  # noqa: BLE001
            logging.warning("Pre-warmup skipped or failed: %s", e)

        await daemon.start()
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit, asyncio.CancelledError):
        pass
    finally:
        await daemon.stop()
        await conn.close()
        logging.info("🛑 Daemon stopped and database connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
