import aiosqlite
import logging

logger = logging.getLogger("bft_db_async")


async def persist_bft_event(
    db_path: str, event_id: str, payload: str, lamport_t: int, cortex_taint: str, prev_hash: str | None = None
) -> None:
    """
    Persiste un colapso de estado BFT en cortex.db de manera asíncrona.
    """
    try:
        async with aiosqlite.connect(db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA synchronous=NORMAL;")
            await db.execute(
                "INSERT INTO events (id, payload, lamport_t, cortex_taint, prev_hash) VALUES (?, ?, ?, ?, ?)",
                (event_id, payload, lamport_t, cortex_taint, prev_hash),
            )
            await db.commit()
            logger.info(f"[BFT PERSIST] Evento {event_id} sellado en disco.")
    except Exception as e:
        logger.error(f"[BFT FATAL] Error persistiendo evento: {e}")
        raise
