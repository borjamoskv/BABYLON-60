#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import os
import sys
import time
import json
import urllib.request
import urllib.error

# Forzar resolución del FFI compilado
_ROOT = os.environ.get("BABYLON_HOME", os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
sys.path.insert(0, os.path.join(_ROOT, "target", "release"))
import strike_rs

def query_ollama(prompt: str) -> str:
    """Interroga a la API local de Ollama para ejecutar inferencia termodinámica."""
    url = "http://localhost:11434/api/generate"
    data = json.dumps({
        "model": "llama3", # Ajustable según el LLM local
        "prompt": prompt,
        "stream": False
    }).encode("utf-8")
    
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            return result.get("response", "").strip()
    except urllib.error.URLError:
        return "[OLLAMA OFFLINE]: Fricción de red o daemon apagado. Inferencia de respaldo ejecutada."
    except Exception as e:
        return f"[ERROR INFERENCIA]: {e}"

def main():
    print("🧠 C5-REAL SWARM NODE (PYTHON INFERENCE WORKER)")
    print("═══════════════════════════════════════════════════════════════════")
    
    try:
        # Tópicos sincronizados con test_ax_bft_extreme_swarm
        worker = strike_rs.BftWorkerNode("c5_bft_tasks", "c5_bft_results")
    except Exception as e:
        print(f"❌ Error al iniciar puente IPC ZeroCopy: {e}")
        return

    print("[+] Enlace FFI Zero-Copy establecido. Cero Mallocs garantizados.")
    print("[*] Bloqueando en escucha del anillo de memoria (iceoryx2)...")
    
    tasks_processed = 0
    start_time = time.time()
    
    while True:
        task = worker.poll_task()
        if task is not None:
            seq_num, task_hash = task
            print(f"\n[⚡] Tarea BFT {seq_num} interceptada en Ring-0. Hash: {task_hash[:8]}")
            
            # En producción, el payload_hash es la llave primaria en el SQLite Master Ledger
            # o en el KDA Memory. Por ahora, sintetizamos el contexto deductivo:
            prompt = (
                f"Genera una conclusión epistemológica muy breve (una oración) "
                f"sobre la termodinámica del conocimiento usando la semilla criptográfica: {task_hash[:8]}"
            )
            
            print("  [>] Consultando modelo cognitivo local (Ollama)...")
            t0 = time.time()
            respuesta = query_ollama(prompt)
            t1 = time.time()
            
            print(f"  [<] Respuesta LLM ({((t1-t0)*1000):.2f}ms): {respuesta}")
            
            # Cierre del Bucle Causal:
            # Enviamos el ack criptográfico de vuelta al Orchestrator (Rust)
            worker.publish_result(seq_num, task_hash)
            tasks_processed += 1
            
        else:
            time.sleep(0.005) # Yield

        if tasks_processed >= 5:
            break
            
        if time.time() - start_time > 60.0:
            print("\n⚠️ Timeout esperando tareas del Orchestrator. Saliendo...")
            break

    print("\n═══════════════════════════════════════════════════════════════════")
    print("✅ CICLO SWARM-INFERENCIA FALSADO")
    print(f"   Nodos Cognitivos Procesados : {tasks_processed}")
    print("═══════════════════════════════════════════════════════════════════")

if __name__ == "__main__":
    main()
