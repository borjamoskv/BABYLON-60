# C5-REAL EXERGY CERTIFIED
import asyncio
import nacl.signing
from pathlib import Path
import sys

# Import HalGuard
sys.path.append(str(Path(__file__).parent))
from importlib.util import spec_from_file_location, module_from_spec
spec_hal = spec_from_file_location("00_HAL_GUARD", str(Path(__file__).parent / "00_HAL_GUARD.py"))
hal_mod = module_from_spec(spec_hal)
spec_hal.loader.exec_module(hal_mod)
HalGuard = hal_mod.HalGuard
ViewChangeException = hal_mod.ViewChangeException

async def simulate_distributed_forks():
    print("[⚔️ SIMULACIÓN MASIVA BFT] Levantando bifurcaciones de prueba (Circuit Breaker / Alucinación)...")
    db_path = Path("test_hal_guard.db")
    if db_path.exists():
        db_path.unlink()

    sk = nacl.signing.SigningKey.generate()
    guard = HalGuard("NODE_ROOT", sk, db_path, "sk-or-dummy")

    # Simular que el disco (First Factor) está intacto pero el oráculo BFT detecta alucinación
    guard.checkers["TASK_X"] = lambda: asyncio.sleep(0, result=False)

    print("\n[🚀 INYECCIÓN BIZANTINA] Un nodo seguidor afirma falsamente haber finalizado.")

    try:
        # Esto disparará la One-Strike rule
        await guard.audit("TASK_X", "NODE_CORRUPT", "He finalizado la optimización L5.", 1)
        print("[💥 FATAL] El guardia no interceptó la alucinación.")
    except ViewChangeException as e:
        print(f"\n[✅ C5-REAL] Éxito. Excepción interceptada: {e}")

    print(f"[🔍 FORENSE L2] Score actual del nodo corrupto: {guard.scores.get('NODE_CORRUPT')}")

    # Limpiar test db
    if db_path.exists():
        db_path.unlink()

if __name__ == "__main__":
    asyncio.run(simulate_distributed_forks())
