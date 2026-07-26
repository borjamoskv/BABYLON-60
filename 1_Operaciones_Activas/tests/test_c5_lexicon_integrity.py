# C5-REAL EXERGY CERTIFIED
import pytest
import sqlite3
import asyncio
from pathlib import Path
from cortex.core.lexicon import LexiconEngine, LexiconLedgerActor

@pytest.mark.asyncio
async def test_bft_causal_invariant_corruption(tmp_path: Path):
    """
    C5-REAL EXERGY TEST:
    Verifica que el motor SQLite WAL repela instantáneamente cualquier mutación
    fuera del canal Single-Writer (UPDATE/DELETE).
    """
    db_path = tmp_path / "test_ledger.db"

    # 1. Inicializamos el transductor (vacío por falta de glosario, pero crea la DB)
    engine = LexiconEngine(root_dir=tmp_path, db_name="test_ledger.db")
    await engine.initialize_c5_substrate("test:bft_init")

    # Inyectamos una entrada sintética a través del actor
    envelope = await engine.actor.submit_mutation(
        term="Entropía",
        category="Física",
        description="Medida de desorden termodinámico.",
        taint="test:synthetic_inject"
    )

    await engine.close()

    # 2. Intento de Corrupción Directa (Simulación de Inyección C4-SIM)
    conn = sqlite3.connect(db_path)
    print("ROWS IN DB:", conn.execute("SELECT * FROM master_ledger").fetchall())

    # A. Intento de UPDATE (Debe ser repelido por el trigger abort_updates)
    with pytest.raises((sqlite3.OperationalError, sqlite3.IntegrityError, Exception), match="BFTCausalInvariantError"):
        conn.execute("UPDATE master_ledger SET payload_json = 'corrupted' WHERE seq = 1")

    # B. Intento de DELETE (Debe ser repelido por el trigger abort_deletes)
    with pytest.raises((sqlite3.OperationalError, sqlite3.IntegrityError), match="BFTCausalInvariantError"):
        conn.execute("DELETE FROM master_ledger WHERE seq = 1")

    # 3. Verificamos que la cadena original sigue inmutable
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM master_ledger")
    records = cursor.fetchall()
    assert len(records) == 1
    assert records[0][7] == envelope["entry_hash"]  # index 7 is entry_hash
    conn.close()
