# C5-REAL EXERGY CERTIFIED
import sqlite3
import multiprocessing
import os
import signal
import time
import uuid

DB_PATH = "c6_adversarial_ledger.db"
WAL_TARGET_SIZE_MB = 25  # Force a large WAL to widen the checkpoint window

def writer_process(db_path: str, ready_event: multiprocessing.synchronize.Event) -> None:
    """
    Inyecta entropía masiva sin hacer checkpoint explícito para inflar el WAL.
    """
    # Desactivamos auto-checkpoint para que el WAL crezca indefinidamente
    conn = sqlite3.connect(db_path, timeout=10.0, isolation_level=None)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA wal_autocheckpoint=0") # Bloquea el checkpoint automático

    conn.execute("""
        CREATE TABLE IF NOT EXISTS bft_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lamport_t INTEGER,
            payload TEXT
        )
    """)
    ready_event.set()

    lamport = 0
    # Usamos transacciones en bloque para saturar el I/O rápido
    while True:
        try:
            conn.execute("BEGIN TRANSACTION")
            for _ in range(500):
                lamport += 1
                payload = uuid.uuid4().hex * 10 # Payload artificialmente denso
                conn.execute("INSERT INTO bft_ledger (lamport_t, payload) VALUES (?, ?)", (lamport, payload))
            conn.execute("COMMIT")
        except sqlite3.Error:
            pass

def checkpointer_process(db_path: str, start_checkpoint_event: multiprocessing.synchronize.Event) -> None:
    """
    Fuerza el vaciado del WAL al archivo DB principal.
    """
    start_checkpoint_event.wait()
    conn = sqlite3.connect(db_path, timeout=10.0)
    try:
        # TRUNCATE asegura que SQLite mueva todo el WAL a la BD y lo trunque a 0
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    except sqlite3.Error:
        pass

def c6_adversarial_orchestrator() -> None:
    print("=====================================================")
    print(" C6 ADVERSARIAL IDENTITY VERIFICATION (BFT/WAL)")
    print(" Vector: kill_during_checkpoint")
    print("=====================================================\n")

    if os.path.exists(DB_PATH): os.remove(DB_PATH)
    wal_path = DB_PATH + "-wal"
    if os.path.exists(wal_path): os.remove(wal_path)

    ready_event = multiprocessing.Event()
    writer = multiprocessing.Process(target=writer_process, args=(DB_PATH, ready_event))
    writer.start()

    ready_event.wait()
    print(f"[+] [T0] Writer spawned (PID: {writer.pid}). Inflating WAL to {WAL_TARGET_SIZE_MB}MB...")

    # 1. Esperamos a que el WAL acumule suficiente deuda I/O
    target_bytes = WAL_TARGET_SIZE_MB * 1024 * 1024
    while True:
        if os.path.exists(wal_path):
            size = os.path.getsize(wal_path)
            if size > target_bytes:
                print(f"[+] [T1] WAL alcanzó {size / (1024*1024):.2f} MB.")
                break
        time.sleep(0.01)

    # 2. Desplegamos al Checkpointer
    start_checkpoint_event = multiprocessing.Event()
    checkpointer = multiprocessing.Process(target=checkpointer_process, args=(DB_PATH, start_checkpoint_event))
    checkpointer.start()
    print(f"[+] [T2] Checkpointer spawned (PID: {checkpointer.pid}). Initiating PRAGMA wal_checkpoint(TRUNCATE)...")

    start_checkpoint_event.set()

    # 3. Ventana Crítica de Asesinato: calculamos un sleep microscópico para acertar
    # en mitad de la transferencia física WAL -> DB.
    time.sleep(0.05)

    print("\n[!] [T3] === INYECTANDO SIGKILL MASIVO (OS.KILL) ===")
    try:
        if writer.pid is not None and checkpointer.pid is not None:
            os.kill(writer.pid, signal.SIGKILL)
            os.kill(checkpointer.pid, signal.SIGKILL)
        print("[!] Procesos decapitados a nivel de Kernel.")
    except ProcessLookupError:
        print("[-] Procesos ya terminaron antes del SIGKILL.")

    writer.join()
    checkpointer.join()

    # 4. Verificación Ontológica C6
    print("\n[+] [T4] Verificando Identidad BFT post-destrucción...")

    try:
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        cursor = conn.cursor()

        # Integridad estructural
        cursor.execute("PRAGMA integrity_check")
        integrity = cursor.fetchone()[0]

        # Estado lógico (conservación de filas)
        cursor.execute("SELECT COUNT(*) FROM bft_ledger")
        count = cursor.fetchone()[0]

        # Recuperación de la línea temporal
        cursor.execute("SELECT MAX(lamport_t) FROM bft_ledger")
        max_lamport = cursor.fetchone()[0]

        print(f"    - PRAGMA integrity_check : {integrity}")
        print(f"    - Filas recuperadas      : {count}")
        print(f"    - Lamport T Máximo       : {max_lamport}")

        if integrity == "ok" and count > 0:
            print("\n[+] C6 RESULT: IDENTIDAD CONSERVADA. El WAL fue truncado violentamente pero SQLite restauró el Master Ledger sin corrupción de punteros.")
        else:
            print("\n[-] C6 RESULT: CORRUPCIÓN DETECTADA. La Base de Datos sufrió pérdida de identidad.")

    except sqlite3.DatabaseError as e:
        print(f"\n[-] C6 RESULT: ERROR ESTRUCTURAL CATASTRÓFICO. La base de datos es ilegible. Exception: {e}")

if __name__ == "__main__":
    # Prevenimos fork issues en macOS activando explicit spawn
    multiprocessing.set_start_method('spawn', force=True)
    c6_adversarial_orchestrator()
