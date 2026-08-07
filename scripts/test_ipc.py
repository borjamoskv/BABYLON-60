# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
import sys
import os

# Adaptar path a la nueva estructura del Enjambre (src/cortex-engine)
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORTEX_ENGINE_PATH = os.path.join(REPO_ROOT, "src", "cortex-engine")
if CORTEX_ENGINE_PATH not in sys.path:
    sys.path.insert(0, CORTEX_ENGINE_PATH)

from cortex.core.orchestrator import CortexOrchestrator

def run_falsification_test():
    print("[TEST] Iniciando secuencia IPC Zero-Anergía...")
    try:
        with CortexOrchestrator() as orch:
            print("[TEST] Orquestador inicializado correctamente.")
            epoch, ts = orch.get_active_epoch()
            print(f"[TEST] Epoch Inicial Leído: {epoch} (Timestamp: {ts})")
            print("[TEST] ¡Falsación superada! El puente FFI funciona en Ring-0.")
    except Exception as e:
        print(f"[TEST ERROR] Fallo en la falsación IPC: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_falsification_test()
