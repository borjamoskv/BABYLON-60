# C5-REAL EXERGY CERTIFIED
import asyncio
import nacl.signing
from pathlib import Path
import os
import sys

# Add current dir to path to import 00_HAL_GUARD and 01_L5_ANCHOR
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import importlib.util

spec = importlib.util.spec_from_file_location("00_HAL_GUARD", str(Path(__file__).parent / "00_HAL_GUARD.py"))
hal_guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hal_guard)

spec_l5 = importlib.util.spec_from_file_location("01_L5_ANCHOR", str(Path(__file__).parent / "01_L5_ANCHOR.py"))
l5_anchor = importlib.util.module_from_spec(spec_l5)
spec_l5.loader.exec_module(l5_anchor)

async def unified_pipeline_execution():
    print("[🛡️] KERNEL M12: INICIANDO PIPELINE UNIFICADO L4-L5 (ENTROPÍA CERO)")
    sk = nacl.signing.SigningKey.generate()
    db_path = Path("unified_ledger.db")
    if db_path.exists():
        db_path.unlink()

    guard = hal_guard.HalGuard("NODE_FOLLOWER_01", sk, db_path, openrouter_key=os.getenv("OPENROUTER_KEY", "sk-cortex-dummy"))
    engine = l5_anchor.L5AnchorEngine(Path("cortex_inertial_proofs"), db_path)

    async def always_fail_checker():
        return False

    guard.checkers["TASK_CRITICAL_DB"] = always_fail_checker

    hallucination_claim = "he completado la inserción de la base de datos maestra"

    try:
        # Simulamos la auditoría de un líder bizantino.
        await guard.audit("TASK_CRITICAL_DB", "NODE_LEADER_00", hallucination_claim, 0)
    except hal_guard.ViewChangeException as e:
        print(f"\n[💥 INTERCEPCIÓN L4] {e}")
        print("[⚡ TRIGGER] Auto-Sweep L5 soberano ejecutado internamente por HalGuard.")

    print("\n[✅ C5-REAL] Ciclo unificado completado. El fraude ha sido purgado localmente y anclado cosmológicamente.")

if __name__ == "__main__":
    asyncio.run(unified_pipeline_execution())
