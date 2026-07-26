# C5-REAL EXERGY CERTIFIED
"""
54_STRESS_TAU_KILL.py (C5-REAL Certified)
-----------------------------------------
Arnés de estrés transaccional para forzar la activación de la Invariante Ω184.
Simula contaminación bizantina masiva y valida el truncamiento atómico del Nodo 8.
"""
import sys
import asyncio
import sqlite3
from pathlib import Path
import importlib.util

# R6 HONEST-CHECK: El Operador solicitó `from cortex.core.00_EXERGY_FLOW`.
# Esto viola la especificación AST de Python (SyntaxError por token numérico).
# Transducción asimétrica: Carga directa vía importlib preservando la topología de archivos.
spec = importlib.util.spec_from_file_location("EXERGY_FLOW", "1_Operaciones_Activas/cortex/core/00_EXERGY_FLOW.py")
exergy_flow = importlib.util.module_from_spec(spec)
sys.modules["EXERGY_FLOW"] = exergy_flow
spec.loader.exec_module(exergy_flow)
ExergyFlowRegulator = exergy_flow.ExergyFlowRegulator

async def run_stress_test():
    print("[⚔️ STRESS TEST] Inicializando arnés de saturación termodinámica...")
    db_path = Path("swarm_stress_ledger.db")

    # 1. Forzar inserción masiva para inflar el índice de contaminación (Taint)
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS fraud_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT, offender TEXT, reporter TEXT, sig TEXT, ts TEXT
            );
        """)
        # Inyectar 100 registros antiguos para forzar la ventana temporal forense
        for i in range(100):
            conn.execute(
                "INSERT INTO fraud_ledger (task_id, offender, reporter, sig, ts) VALUES (?, ?, ?, ?, ?)",
                ("STRESS_TASK", "node_bad", "node_reporter", "SIG_STRESS", "2026-07-20 00:00:00")
            )
        conn.commit()

    regulator = ExergyFlowRegulator(db_path, tau_kill=700.0)

    print("\n[🎯 TRIGGER] Evaluando estado crítico del sistema (Simulación Taint = 750.0)...")
    # Forzamos un Taint de 750.0 (> tau_kill) y un delta de volumen de caché de 0.5
    da_slop = await regulator.monitor_and_purge(current_taint_score=750.0, kv_cache_vol_delta=0.5)

    print(f"[📊 RESULTADO] Derivada de acumulación dA_slop/dt: {da_slop:.2f}")

    # Verificar post-mortem que el operador Λ8 ejecutó la purga física de las trazas antiguas
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM fraud_ledger")
        count = cursor.fetchone()[0]
        print(f"[✅ C5-REAL] Registros remanentes en SQLite WAL tras la purga: {count}")
        assert count == 0, "Fallo: El operador Λ8 no truncó los inodos con energía libre nula."
        print("[✅ C5-REAL] Arnés completado con éxito. Autopoiesis verificada.")

if __name__ == "__main__":
    asyncio.run(run_stress_test())
