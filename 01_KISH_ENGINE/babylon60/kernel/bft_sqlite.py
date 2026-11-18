import sqlite3
import time
import random
import logging
from collections.abc import Generator, Iterator
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


class MaterializedCursor:
    """Cursor desacoplado que conserva las filas leídas tras el cierre seguro de la conexión."""

    def __init__(
        self,
        rows: list[Any],
        description: Any = None,
        rowcount: int = -1,
        lastrowid: int | None = None,
    ) -> None:
        self._rows = list(rows)
        self._pos = 0
        self.description = description
        self.rowcount = rowcount
        self.lastrowid = lastrowid

    def fetchone(self) -> Any:
        if self._pos >= len(self._rows):
            return None
        row = self._rows[self._pos]
        self._pos += 1
        return row

    def fetchall(self) -> list[Any]:
        if self._pos >= len(self._rows):
            return []
        rows = self._rows[self._pos :]
        self._pos = len(self._rows)
        return rows

    def fetchmany(self, size: int = 1) -> list[Any]:
        if size <= 0 or self._pos >= len(self._rows):
            return []
        end = min(self._pos + size, len(self._rows))
        rows = self._rows[self._pos : end]
        self._pos = end
        return rows

    def close(self) -> None:
        self._pos = len(self._rows)

    def __iter__(self) -> Iterator[Any]:
        while self._pos < len(self._rows):
            yield self._rows[self._pos]
            self._pos += 1


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
        conn = sqlite3.connect(self.db_path, timeout=5.0, isolation_level="IMMEDIATE")
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA busy_timeout=5000;")
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=FULL;")
            yield conn
        finally:
            conn.close()

    def execute_with_backoff(self, query: str, params: tuple[Any, ...] = ()) -> MaterializedCursor:
        """
        Ejecuta un query con mitigación de bloqueos vía Exponential Backoff
        y materializa las filas antes de cerrar la conexión para evitar cursores huérfanos.
        """
        retries = 0
        while retries <= self.max_retries:
            try:
                with self._connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    rows = cursor.fetchall() if cursor.description is not None else []
                    result = MaterializedCursor(
                        rows=rows,
                        description=cursor.description,
                        rowcount=cursor.rowcount,
                        lastrowid=cursor.lastrowid,
                    )
                    conn.commit()
                    return result
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

    def executemany_with_backoff(self, query: str, seq_of_params: list[tuple[Any, ...]]) -> MaterializedCursor:
        """
        Ejecuta un query por lotes con mitigación de bloqueos vía Exponential Backoff.
        """
        if not seq_of_params:
            return MaterializedCursor(rows=[], rowcount=0)

        retries = 0
        while retries <= self.max_retries:
            try:
                with self._connection() as conn:
                    cursor = conn.cursor()
                    cursor.executemany(query, seq_of_params)
                    rows = cursor.fetchall() if cursor.description is not None else []
                    result = MaterializedCursor(
                        rows=rows,
                        description=cursor.description,
                        rowcount=cursor.rowcount,
                        lastrowid=cursor.lastrowid,
                    )
                    conn.commit()
                    return result
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e).lower() or "busy" in str(e).lower():
                    if retries == self.max_retries:
                        logger.error(f"[BFT-FAIL] Colapso inminente. Imposible adquirir lock en {self.db_path}.")
                        raise BFTDatabaseError(f"Max retries reached: {e}")

                    delay = min(self.max_delay, self.base_delay * (2**retries))
                    jitter = random.uniform(0, delay * 0.1)
                    sleep_time = delay + jitter

                    logger.warning(
                        f"[BFT-RETRY] SQLITE_BUSY detectado en batch. Intento {retries + 1}/{self.max_retries}. Esperando {sleep_time:.3f}s"
                    )
                    time.sleep(sleep_time)
                    retries += 1
                else:
                    raise e

        raise BFTDatabaseError(f"Max retries exceeded ({self.max_retries}) without acquiring lock on {self.db_path}.")
