import asyncio
import sqlite3
import os
import signal
import sys
import multiprocessing
import time
import json

LEDGER_PATH = "master_ledger.db"

# We must import the Jetsam daemon logic
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from cortex.agents.jetsam_episodic_daemon import init_jetsam_ledger, anchor_and_execute, hydrate_episodic_state
except ImportError as e:
    print(f"FATAL: C5-REAL Daemon not found in python path. {e}")
    sys.exit(1)

async def vulnerable_llm_call():
    # Simulamos una llamada de red de larga duración (ej. inference_l3)
    await asyncio.sleep(10)
    return "LLM_RESPONSE_OK"

def worker_process(task_id: str, agent_id: str):
    """
    Este worker simulará el proceso asíncrono que será aniquilado por Jetsam (SIGKILL).
    """
    init_jetsam_ledger()
    # Ejecutamos el bucle de eventos
    async def run():
        await anchor_and_execute(task_id, agent_id, {"prompt": "Generar matriz de exergía"}, vulnerable_llm_call)
    
    asyncio.run(run())

def run_falsification():
    print("[-] Igniting Jetsam Chaos Falsification (Empirical Test)...")
    init_jetsam_ledger()
    
    # 1. Limpiar tareas de prueba previas
    conn = sqlite3.connect(LEDGER_PATH, timeout=5.0)
    conn.execute("DELETE FROM jetsam_async_ledger WHERE agent_id = 'test_agent_001'")
    conn.commit()
    conn.close()

    task_id = "task_jetsam_test_001"
    agent_id = "test_agent_001"
    
    # 2. Iniciar el proceso worker
    p = multiprocessing.Process(target=worker_process, args=(task_id, agent_id))
    p.start()
    
    print(f"[*] Worker started (PID {p.pid}). Waiting for ledger anchoring...")
    time.sleep(1.0) # Dar tiempo para que el worker ancle al disco
    
    # 3. Comprobar que está en el ledger
    conn = sqlite3.connect(LEDGER_PATH, timeout=5.0)
    cursor = conn.execute("SELECT state FROM jetsam_async_ledger WHERE task_id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row or row[0] != 'AWAITING_WAKEUP':
        print(f"[!] FAILED: Tarea no anclada. Estado actual: {row}")
        if p.is_alive():
            p.kill()
        sys.exit(1)
        
    print("[+] Tarea anclada (AWAITING_WAKEUP). Simulando purga Jetsam (SIGKILL)...")
    
    # 4. Asesinato físico (SIGKILL - No puede ser interceptado por try/except)
    os.kill(p.pid, signal.SIGKILL)
    p.join()
    
    print("[*] Worker aniquilado. Iniciando Protocolo de Hidratación (Ψ2)...")
    
    # 5. Hidratación
    recovered = hydrate_episodic_state(agent_id)
    
    if len(recovered) == 1 and recovered[0]['task_id'] == task_id:
        print("[+] EMPIRICAL FALSIFICATION PASSED: La tarea sobrevivió a la purga de memoria (Jetsam) y el payload está intacto.")
        print(f"[+] Payload recuperado: {json.dumps(recovered[0]['payload'])}")
    else:
        print(f"[!] FAILED: Hidratación fallida. Tareas recuperadas: {len(recovered)}")
        sys.exit(1)

if __name__ == "__main__":
    run_falsification()
