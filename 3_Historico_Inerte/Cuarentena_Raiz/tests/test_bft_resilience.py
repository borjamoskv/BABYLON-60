# C5-REAL EXERGY CERTIFIED — BFT Resilience Test Suite
# Invariantes: Ω11 (Immutable Ledger), Ω13 (Single Writer), Ω23 (Dynamic Resolution)
# Purga: INV_C5_THERMO_VALVE, INV_BFT_04 — CERO ANERGÍA

from __future__ import annotations

import asyncio
import hashlib
import importlib.util
import os
import sqlite3
import sys
import types
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

import pytest

# ---------------------------------------------------------------------------
# Entorno y rutas absolutas (Ω23 — Resolución Dinámica, CWD-immune)
# ---------------------------------------------------------------------------
os.environ.setdefault("CORTEX_BFT_KEY", "DUMMY_TEST_KEY")

_TESTS_DIR    = Path(__file__).resolve().parent
_REPO_ROOT    = _TESTS_DIR.parent
_INIT_LEDGER  = _REPO_ROOT / "1_Operaciones_Activas" / "scripts" / "00_init_ledger.py"
TEST_DB_PATH  = _REPO_ROOT / ".cortex" / "test_cortex_resilience.db"

# ---------------------------------------------------------------------------
# Carga determinista de 00_init_ledger (sin symlinks, sin caché heredado)
# ---------------------------------------------------------------------------
_MOD_KEY = "init_ledger_mod"


def _load_fresh_init_ledger(db_path: Path) -> types.ModuleType:
    """Carga 00_init_ledger con DB_PATH sobreescrito. Invalida sys.modules previo."""
    sys.modules.pop(_MOD_KEY, None)
    spec = importlib.util.spec_from_file_location(_MOD_KEY, str(_INIT_LEDGER))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No se pudo cargar spec: {_INIT_LEDGER}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[_MOD_KEY] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    mod.DB_PATH = str(db_path)   # override antes de cualquier llamada a init_ledger()
    return mod


# ---------------------------------------------------------------------------
# Fixtures de módulo (setup / teardown con semántica pytest correcta)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module", autouse=True)
def ledger_db() -> Generator[Path, None, None]:
    """Provisiona el DB BFT limpio para toda la suite de este módulo."""
    TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()

    mod = _load_fresh_init_ledger(TEST_DB_PATH)
    mod.init_ledger()

    yield TEST_DB_PATH

    # Teardown: limpiar artefactos WAL
    for suffix in ("", "-shm", "-wal"):
        p = Path(str(TEST_DB_PATH) + suffix)
        if p.exists():
            p.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Utilidades C5-REAL
# ---------------------------------------------------------------------------
def hash_payload(lamport_t: int, agent_id: str, prev_hash: str) -> str:
    data = f"{lamport_t}:{agent_id}:{prev_hash}".encode("utf-8")
    return hashlib.sha3_256(data).hexdigest()


@contextmanager
def bft_conn(db: Path = TEST_DB_PATH) -> Generator[sqlite3.Connection, None, None]:
    """Context-manager BFT: cierre garantizado incluso ante excepción. (INV_BFT_04)"""
    conn = sqlite3.connect(str(db), timeout=5.0)
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    try:
        yield conn
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# MasterLedgerWriter — escritor BFT de productor único (Ω13)
# ---------------------------------------------------------------------------
class MasterLedgerWriter:
    def __init__(self, db: Path) -> None:
        # INV_C5_THERMO_VALVE: cola acotada — prohibida la cola infinita
        self.queue: asyncio.Queue[Any] = asyncio.Queue(maxsize=1024)
        self.conn = sqlite3.connect(str(db), timeout=5.0)
        self.conn.execute("PRAGMA journal_mode = WAL;")
        self.conn.execute("PRAGMA busy_timeout = 5000;")
        self._errors: list[str] = []

    async def writer_loop(self) -> None:
        """Escritor serializado (Ω13). task_done() sólo tras commit exitoso."""
        while True:
            item = await self.queue.get()
            if item is None:
                self.queue.task_done()
                break
            agent_id, lamport_t, payload_hash, prev_hash, taint = item
            try:
                self.conn.execute(
                    "INSERT INTO bft_ledger "
                    "(agent_id, lamport_t, payload_hash, prev_hash, cortex_taint) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (agent_id, lamport_t, payload_hash, prev_hash, taint),
                )
                self.conn.commit()
            except sqlite3.Error as e:
                self.conn.rollback()
                self._errors.append(f"lamport_t={lamport_t}: {e}")
            finally:
                # INV_BFT_04: task_done siempre, para no bloquear queue.join()
                self.queue.task_done()

    def close(self) -> None:
        self.conn.close()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def test_genesis_block_integrity(ledger_db: Path) -> None:
    """Verifica que el bloque génesis (lamport_t=0) cumple el invariante hash."""
    with bft_conn(ledger_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT lamport_t, agent_id, payload_hash, prev_hash FROM bft_ledger WHERE lamport_t = 0"
        )
        row = cursor.fetchone()

    assert row is not None, "El génesis (lamport_t=0) debe existir tras init_ledger()"
    lamport_t, agent_id, payload_hash, prev_hash = row
    assert agent_id == "ROOT_OPERATOR_UID0", f"Agente génesis incorrecto: {agent_id}"
    assert prev_hash == "0" * 64, f"prev_hash génesis debe ser 64 ceros, got: {prev_hash}"
    expected = hash_payload(lamport_t, agent_id, prev_hash)
    assert payload_hash == expected, (
        f"Hash génesis inválido — posible corrupción de ancla.\n"
        f"  esperado: {expected}\n  obtenido: {payload_hash}"
    )


def test_wal_contention(ledger_db: Path) -> None:
    """Ω13: productor serial de 100 entradas con escritor único asíncrono (WAL contention)."""
    async def run_contention() -> None:
        writer = MasterLedgerWriter(ledger_db)
        writer_task = asyncio.create_task(writer.writer_loop())

        with bft_conn(ledger_db) as c:
            c.execute("SELECT payload_hash FROM bft_ledger WHERE lamport_t = 0")
            genesis_hash = c.execute(
                "SELECT payload_hash FROM bft_ledger WHERE lamport_t = 0"
            ).fetchone()[0]

        prev = genesis_hash
        for i in range(1, 101):
            agent_id = f"AGENT_{i % 3}"
            phash    = hash_payload(i, agent_id, prev)
            taint    = f"CORTEX-TAINT:test:{i}"
            await writer.queue.put((agent_id, i, phash, prev, taint))
            prev = phash

        await writer.queue.join()
        await writer.queue.put(None)   # señal de parada
        await writer_task
        writer.close()

        assert not writer._errors, f"Errores BFT durante escritura: {writer._errors}"

    asyncio.run(run_contention())

    # Verificar total fuera del loop async (conexión independiente)
    with bft_conn(ledger_db) as conn:
        count = conn.execute("SELECT COUNT(*) FROM bft_ledger").fetchone()[0]
    assert count == 101, f"Esperados 101 registros (génesis + 100), encontrados: {count}"


def test_chain_integrity(ledger_db: Path) -> None:
    """Verifica la cadena hash completa: cada bloque enlaza correctamente al anterior."""
    with bft_conn(ledger_db) as conn:
        rows = conn.execute(
            "SELECT lamport_t, agent_id, payload_hash, prev_hash FROM bft_ledger ORDER BY lamport_t ASC"
        ).fetchall()

    assert len(rows) > 0, "El ledger no debe estar vacío"

    # Verificar génesis
    g_lamport, g_agent, g_hash, g_prev = rows[0]
    assert g_lamport == 0,                      "El primer registro debe ser el bloque génesis (lamport_t=0)"
    assert g_agent   == "ROOT_OPERATOR_UID0",   f"Agente génesis incorrecto: {g_agent}"
    assert g_prev    == "0" * 64,               "prev_hash del génesis debe ser 64 ceros"
    assert g_hash    == hash_payload(g_lamport, g_agent, g_prev), "Hash génesis inválido"

    # Verificar cadena completa
    prev_expected = g_hash
    for lamport_t, agent_id, payload_hash, prev_hash in rows[1:]:
        assert prev_hash == prev_expected, (
            f"Rotura de cadena en lamport_t={lamport_t}: "
            f"prev_hash={prev_hash!r} != esperado={prev_expected!r}"
        )
        expected = hash_payload(lamport_t, agent_id, prev_hash)
        assert payload_hash == expected, (
            f"Hash inválido en lamport_t={lamport_t}: "
            f"obtenido={payload_hash!r}, esperado={expected!r}"
        )
        prev_expected = payload_hash


def test_intentional_corruption_prevention(ledger_db: Path) -> None:
    """Ω11: los triggers de inmutabilidad impiden UPDATE y DELETE sobre el ledger."""
    # UPDATE trigger
    with bft_conn(ledger_db) as conn:
        with pytest.raises(sqlite3.IntegrityError) as exc_update:
            conn.execute("UPDATE bft_ledger SET payload_hash = 'CORRUPT' WHERE lamport_t = 0")
    assert "Modificación de ledger inmutable prohibida" in str(exc_update.value), (
        f"Trigger UPDATE no lanzó el mensaje esperado: {exc_update.value}"
    )

    # DELETE trigger — conexión separada para evitar estado sucio
    with bft_conn(ledger_db) as conn:
        with pytest.raises(sqlite3.IntegrityError) as exc_delete:
            conn.execute("DELETE FROM bft_ledger WHERE lamport_t = 0")
    assert "Borrado de ledger inmutable prohibido" in str(exc_delete.value), (
        f"Trigger DELETE no lanzó el mensaje esperado: {exc_delete.value}"
    )
