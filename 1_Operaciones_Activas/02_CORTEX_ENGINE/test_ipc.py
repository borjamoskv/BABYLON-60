# C5-REAL EXERGY CERTIFIED
import sys
import os

# Asegurar que el modulo cortex esté en el PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cortex.core.orchestrator import CortexOrchestrator

def main():
    print("[TEST] Iniciando secuencia IPC Zero-Anergía...")
    try:
        with CortexOrchestrator() as orchestrator:
            print("[TEST] Orquestador inicializado correctamente.")
            epoch, ts = orchestrator.get_active_epoch()
            print(f"[TEST] Epoch Inicial Leído: {epoch} (Timestamp: {ts})")
            assert epoch == 0, "El epoch inicial debería ser 0"
            assert ts == 0, "El timestamp inicial debería ser 0"
            print("[TEST] ¡Falsación superada! El puente FFI funciona en Ring-0.")
    except Exception as e:
        print(f"[TEST ERROR] Fallo crítico: {e}")

if __name__ == "__main__":
    main()
