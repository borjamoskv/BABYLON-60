# C5-REAL EXERGY CERTIFIED
import sqlite3
from pathlib import Path
import importlib.util

spec_l5 = importlib.util.spec_from_file_location("01_L5_ANCHOR", str(Path(__file__).parent / "01_L5_ANCHOR.py"))
l5_anchor = importlib.util.module_from_spec(spec_l5)
spec_l5.loader.exec_module(l5_anchor)

def test_atomic_recovery():
    print("[⚡ TEST] Verificando recuperación atómica L5 ante caída de energía...")
    db_path = Path("atomic_recovery_test.db")
    if db_path.exists():
        db_path.unlink()

    engine = l5_anchor.L5AnchorEngine(Path("cortex_inertial_proofs"), db_path)

    # 1. Inyectar 3 fraudes iniciales
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS fraud_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT, offender TEXT, reporter TEXT, sig TEXT, ts TEXT
            );
        """)
        for i in range(1, 4):
            conn.execute(
                "INSERT INTO fraud_ledger (task_id, offender, reporter, sig, ts) VALUES (?, ?, ?, ?, ?)",
                ("TASK", "O", "R", f"SIG{i}", "TS")
            )

    # 2. Ejecutar sweep normal
    engine.autonomous_sqlite_sweep()

    # El marker debe estar en 3
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute("SELECT last_anchored_id FROM l5_anchor_state WHERE marker = 'GLOBAL_SYNC'")
        assert c.fetchone()[0] == 3, "El puntero no se movió a 3."

    print("[✅ C5-REAL] Puntero inicial validado en 3.")

    # 3. Inyectar 2 fraudes más (total 5)
    with sqlite3.connect(db_path) as conn:
        for i in range(4, 6):
            conn.execute(
                "INSERT INTO fraud_ledger (task_id, offender, reporter, sig, ts) VALUES (?, ?, ?, ?, ?)",
                ("TASK", "O", "R", f"SIG{i}", "TS")
            )

    # 4. SIMULAR APAGÓN (Power Failure) durante el Sweep
    original_connect = l5_anchor.sqlite3.connect

    class FaultyConnection:
        def __init__(self, path, **kwargs):
            self.conn = original_connect(path, **kwargs)
        def __enter__(self):
            self.conn.__enter__()
            return self
        def __exit__(self, ext, exv, trb):
            raise sqlite3.OperationalError("Simulated hardware failure")
        def cursor(self):
            return self.conn.cursor()
        def execute(self, *args, **kwargs):
            return self.conn.execute(*args, **kwargs)
        def commit(self):
            print("[💥 APAGÓN CATASTRÓFICO] Fallo de hardware en medio de la transacción ACID.")
            raise sqlite3.OperationalError("Simulated hardware failure")

    l5_anchor.sqlite3.connect = lambda *args, **kwargs: FaultyConnection(*args, **kwargs)

    try:
        engine.autonomous_sqlite_sweep()
    except sqlite3.OperationalError:
        pass
    finally:
        l5_anchor.sqlite3.connect = original_connect

    # 5. VERIFICACIÓN POST-MORTEM (El Rollback ACID debería haber dejado el puntero en 3)
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute("SELECT last_anchored_id FROM l5_anchor_state WHERE marker = 'GLOBAL_SYNC'")
        marker = c.fetchone()[0]
        assert marker == 3, f"FALLO: El puntero es {marker}, debía haber hecho rollback a 3."

    print("[✅ C5-REAL] Recuperación Atómica verificada. El puntero retrocedió de forma segura tras el fallo eléctrico.")

if __name__ == "__main__":
    test_atomic_recovery()
