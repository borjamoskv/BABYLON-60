import sqlite3
import time
import random
import logging
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

try:
    import babylon60

    _HAVE_RUST_KERNEL = True
except ImportError:
    _HAVE_RUST_KERNEL = False

logger = logging.getLogger("bft_sqlite")


class BFTDatabaseError(Exception):
    """Excepción termodinámica para fallos BFT irrecuperables en SQLite."""

    pass


class BFTSQLite:
    """
    Wrapper C5-REAL para SQLite.
    Mitigación determinista de SQLITE_BUSY usando Exponential Backoff y Jitter.
    Garantiza que la exergía de la base de datos se mantiene intacta bajo alta concurrencia.
    """

    def __init__(
        self, db_path: str = "cortex.db", max_retries: int = 5, base_delay: float = 0.1, max_delay: float = 2.0
    ) -> None:
        self.db_path = db_path
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

        if _HAVE_RUST_KERNEL and hasattr(babylon60, "kernel_status"):
            status_fn = getattr(babylon60, "kernel_status")
            logger.info(f"[BFT-KERNEL] {status_fn()}")

    @contextmanager
    def _connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Provee una conexión configurada para serialización estricta y WAL."""
        conn = sqlite3.connect(self.db_path, isolation_level="IMMEDIATE")
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.execute("PRAGMA busy_timeout=5000;")
            yield conn
        finally:
            conn.close()

    def execute_with_backoff(self, query: str, params: tuple[Any, ...] = ()) -> sqlite3.Cursor:
        """
        Ejecuta un query con mitigación de bloqueos vía Exponential Backoff.
        """
        retries = 0
        while retries <= self.max_retries:
            try:
                with self._connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    conn.commit()
                    return cursor
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e).lower() or "busy" in str(e).lower():
                    if retries == self.max_retries:
                        logger.error(f"[BFT-FAIL] Colapso inminente. Imposible adquirir lock en {self.db_path}.")
                        raise BFTDatabaseError(f"Max retries reached: {e}")

                    # Exponential Backoff with Jitter
                    delay = min(self.max_delay, self.base_delay * (2**retries))
                    jitter = random.uniform(0, delay * 0.1)
                    sleep_time = delay + jitter

                    logger.warning(
                        f"[BFT-RETRY] SQLITE_BUSY detectado. Intento {retries + 1}/{self.max_retries}. Esperando {sleep_time:.3f}s"
                    )
                    time.sleep(sleep_time)
                    retries += 1
                else:
                    raise e

        raise BFTDatabaseError(f"Max retries exceeded ({self.max_retries}) without acquiring lock on {self.db_path}.")
