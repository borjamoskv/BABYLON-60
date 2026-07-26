# C5-REAL EXERGY CERTIFIED
"""Simulador de Ataque Bizantino sobre el Sustrato C5-REAL (scripts/simulate_bft_collapse.py)"""

import asyncio
import sqlite3
import hashlib
import json
from pathlib import Path

class BFTCausalInvariantError(Exception):
    """Lanzada cuando se detecta una bifurcación bizantina o corrupción de hash-chain."""
    pass

def ejecutar_ataque_bizantino(db_path: Path):
    """
    Simula un atacante con acceso directo al sistema de archivos (Falla Bizantina).
    Intenta romper la cadena modificando un registro histórico o inyectando un update.
    """
    print("\n[🔥] INICIANDO PROTOCOLO ULTRADECIDE: OPCIÓN 3 (INYECCIÓN DE DATOS CORRUPTOS)")

    if not db_path.exists():
        print("[!] Error: No se detecta una base de datos activa para corromper.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Intento de evasión A: Mutación directa via UPDATE (Debería fallar por Triggers SQLite)
    print("[1] Intentando mutación disipativa via UPDATE directo en base de datos...")
    try:
        cursor.execute("UPDATE master_ledger SET cortex_taint = 'ATTACKER_CORRUPTION' WHERE seq = 1")
        conn.commit()
        print("[⚠️] Alerta: El trigger de inmutabilidad no detuvo el UPDATE.")
    except sqlite3.IntegrityError as e:
        print(f"[✅] Éxito Exergético: El motor SQLite abortó el ataque. Razón: {e}")

    # 2. Intento de evasión B: Manipulación física sin recalcular el hash (Romper Hash-Chain)
    print("\n[2] Evadiendo triggers mediante inserción forzada de bloque corrupto (Bifurcación Bizantina)...")
    try:
        cursor.execute("""
            INSERT INTO master_ledger
            (seq, event_id, stream, payload_json, cortex_taint, lamport_t, prev_hash, entry_hash, created_at)
            VALUES (999, 'corrupt-uuid-v5', 'cortex.ontology', '{"term":"Corrupto"}', 'ULTRADECIDE:ATTACK', 999, 'fake_prev_hash', 'FAKE_ENTRY_HASH_SHA3', '2026-07-26T00:00:00Z')
        """)
        conn.commit()
        print("[⚡] Registro corrupto inyectado en el disco con éxito.")
    except sqlite3.Error as e:
        print(f"[-] Error al inyectar el bloque: {e}")
    finally:
        conn.close()

def verificar_y_forzar_colapso(db_path: Path):
    """Audita el disco duro y fuerza el colapso inmediato al detectar la falla de integridad."""
    print("\n[3] Ejecutando verificación de lectura (Fail-Fast Audit)...")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM master_ledger ORDER BY seq ASC")
    records = [dict(row) for row in cursor.fetchall()]
    conn.close()

    expected_prev = "0" * 64
    for idx, env in enumerate(records):
        # Validación de secuencia contigua y sin saltos (Gap-Free Invariant)
        if env["seq"] != idx + 1:
            raise BFTCausalInvariantError(
                f"CRITICAL: Secuencia corrupta detectada en seq={env['seq']}. Esperado: {idx + 1}. Sistema detenido."
            )

        # Re-computación estricta del sobre SHA3-256
        envelope_data = f"{env['seq']}|{env['event_id']}|{env['payload_json']}|{env['cortex_taint']}|{env['lamport_t']}|{env['prev_hash']}|{env['created_at']}"
        calculated_hash = hashlib.sha3_256(envelope_data.encode('utf-8')).hexdigest()

        if env["entry_hash"] != calculated_hash:
            raise BFTCausalInvariantError(
                f"CRITICAL: Violación de enlace criptográfico en seq={env['seq']}.\n"
                f"Hash en Disco: {env['entry_hash']}\n"
                f"Hash Calculado: {calculated_hash}\n"
                f"¡COLAPSO DE RAMIFICACIÓN PROBABILÍSTICA DETECTADO!"
            )

        expected_prev = env["entry_hash"]

    print("[🟢] La cadena de bloques se mantiene íntegra.")

# --- SIMULACIÓN DEL ENTORNO DE FALLO ---
async def simular_entorno():
    db_test = Path("master_ledger_test.db")
    if db_test.exists():
        db_test.unlink()

    # Inicializamos usando la ontología C5-REAL para crear tablas, triggers y el archivo físico
    from cortex.core.lexicon import LexiconEngine
    engine = LexiconEngine(root_dir=Path.cwd(), db_name=db_test.name)
    await engine.initialize_c5_substrate("test:bft_simulation")

    # Inyectamos un bloque válido primero
    future = await engine.actor.submit_mutation("Valid", "Test", "This is valid", "test:valid")
    await future
    await engine.close()

    # Ejecutar la inyección maliciosa
    ejecutar_ataque_bizantino(db_test)

    # Forzar la lectura del sistema. Debería explotar de inmediato.
    try:
        verificar_y_forzar_colapso(db_test)
    except BFTCausalInvariantError as ex_bft:
        print(f"\n[💥][MÁXIMA EXERGÍA] COLAPSO EXITOSO:\n{ex_bft}")

if __name__ == "__main__":
    import sys
    sys.path.append(str(Path.cwd() / "1_Operaciones_Activas"))
    asyncio.run(simular_entorno())
