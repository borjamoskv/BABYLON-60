from __future__ import annotations

import asyncio
import hashlib
import logging

import aiosqlite

logger = logging.getLogger("bft_db_async")

_DB_LOCKS: dict[tuple[int, str], asyncio.Lock] = {}


def _get_db_lock(db_path: str) -> asyncio.Lock:
    try:
        loop_id = id(asyncio.get_running_loop())
    except RuntimeError:
        loop_id = 0
    key = (loop_id, db_path)
    lock = _DB_LOCKS.get(key)
    if lock is None:
        lock = asyncio.Lock()
        _DB_LOCKS[key] = lock
    return lock


def compute_bft_event_digest(
    event_id: str,
    payload: str,
    lamport_t: int,
    cortex_taint: str,
    prev_hash: str,
) -> str:
    """Calcula el digest determinista de un evento BFT a partir de su época lógica y predecesor."""
    canonical = f"{prev_hash}:{lamport_t}:{event_id}:{cortex_taint}:{payload}"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


async def persist_bft_event(
    db_path: str,
    event_id: str,
    payload: str,
    lamport_t: int,
    cortex_taint: str,
    prev_hash: str | None = None,
) -> str:
    """
    Persiste un colapso de estado BFT en cortex.db de manera asíncrona bajo serialización estricta:
    - Exige monotonía estricta de `lamport_t` (> máximo actual en `events`).
    - Verifica continuidad de `prev_hash` contra el digest del evento predecesor para impedir Split-Brain.
    - Retorna el `event_digest` SHA-256 calculado para encadenar el siguiente evento.
    """
    if type(lamport_t) is not int or lamport_t <= 0:
        raise ValueError("BFT lamport_t must be a positive integer")
    if not event_id or not isinstance(event_id, str):
        raise ValueError("BFT event_id must be a non-empty string")
    if not cortex_taint or not isinstance(cortex_taint, str):
        raise ValueError("BFT cortex_taint must be a non-empty string")

    lock = _get_db_lock(db_path)
    async with lock:
        try:
            async with aiosqlite.connect(db_path, isolation_level=None) as db:
                await db.execute("PRAGMA busy_timeout=5000;")
                await db.execute("PRAGMA journal_mode=WAL;")
                await db.execute("PRAGMA synchronous=FULL;")
                await db.execute("BEGIN IMMEDIATE;")
                try:
                    await db.execute(
                        """
                        CREATE TABLE IF NOT EXISTS events (
                            id TEXT PRIMARY KEY,
                            payload TEXT NOT NULL,
                            lamport_t INTEGER NOT NULL UNIQUE,
                            cortex_taint TEXT NOT NULL,
                            prev_hash TEXT NOT NULL
                        )
                        """
                    )
                    async with db.execute(
                        "SELECT id, payload, lamport_t, cortex_taint, prev_hash FROM events ORDER BY lamport_t DESC LIMIT 1"
                    ) as cur:
                        tip = await cur.fetchone()

                    if tip is None:
                        expected_prev = "0" * 64
                        if prev_hash is not None and prev_hash != expected_prev:
                            raise ValueError(
                                f"BFT Split-Brain rejected on genesis: prev_hash '{prev_hash}' != '{expected_prev}'"
                            )
                        effective_prev = expected_prev
                    else:
                        tip_id, tip_payload, tip_lamport, tip_taint, tip_prev_hash = tip
                        if lamport_t <= int(tip_lamport):
                            raise ValueError(
                                f"BFT Epoch Collision/Regression: incoming lamport_t={lamport_t} <= tip={tip_lamport}"
                            )
                        expected_prev = compute_bft_event_digest(
                            str(tip_id),
                            str(tip_payload),
                            int(tip_lamport),
                            str(tip_taint),
                            str(tip_prev_hash),
                        )
                        if prev_hash is not None and prev_hash != expected_prev:
                            raise ValueError(
                                f"BFT Split-Brain rejected: prev_hash '{prev_hash}' does not match tip digest '{expected_prev}'"
                            )
                        effective_prev = expected_prev

                    await db.execute(
                        "INSERT INTO events (id, payload, lamport_t, cortex_taint, prev_hash) VALUES (?, ?, ?, ?, ?)",
                        (event_id, payload, lamport_t, cortex_taint, effective_prev),
                    )
                    await db.execute("COMMIT;")
                    event_digest = compute_bft_event_digest(event_id, payload, lamport_t, cortex_taint, effective_prev)
                    logger.info(f"[BFT PERSIST] Evento {event_id} sellado en disco -> {event_digest[:12]}.")
                    return event_digest
                except BaseException:
                    await db.execute("ROLLBACK;")
                    raise
        except Exception as e:
            logger.error(f"[BFT FATAL] Error persistiendo evento: {e}")
            raise
