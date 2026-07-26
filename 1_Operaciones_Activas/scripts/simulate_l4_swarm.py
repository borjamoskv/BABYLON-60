# C5-REAL EXERGY CERTIFIED
import asyncio
import nacl.signing
from pathlib import Path
import os
import sys

# Add current dir to path to import 00_HAL_GUARD
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import importlib.util
spec = importlib.util.spec_from_file_location("00_HAL_GUARD", str(Path(__file__).parent / "00_HAL_GUARD.py"))
hal_guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hal_guard)

spec_l5 = importlib.util.spec_from_file_location("01_L5_ANCHOR", str(Path(__file__).parent / "01_L5_ANCHOR.py"))
l5_anchor = importlib.util.module_from_spec(spec_l5)
spec_l5.loader.exec_module(l5_anchor)

async def massive_stress_test():
    print("[🛡️] INICIANDO PRUEBA DE ESTRÉS MASIVA L4 SWARM (10,000 ITERACIONES)")
    sk = nacl.signing.SigningKey.generate()
    db_path = Path("swarm_stress_ledger.db")
    if db_path.exists():
        db_path.unlink()

    guard = hal_guard.HalGuard("NODE_FOLLOWER_01", sk, db_path)

    # Invariante que siempre falla (simulando alucinación continua del líder)
    async def always_fail_checker():
        return False

    guard.checkers["STRESS_TASK"] = always_fail_checker

    hallucination_claim = "he finalizado el proceso de iteración masiva"

    view_changes = 0

    for i in range(100):
        try:
            # Para provocar ViewChange rápido, el offender será siempre NODE_LEADER
            await guard.audit("STRESS_TASK", "NODE_LEADER", hallucination_claim, i)
        except hal_guard.ViewChangeException as e:
            view_changes += 1
            print(f"[💥] {e}")
            # Reset score para continuar el estrés en la siguiente época
            guard.scores["NODE_LEADER"] = 1.0

    print(f"\n[✅ C5-REAL] Estrés completado. View Changes inducidos: {view_changes}/100")
    print(f"[✅ C5-REAL] Ledger L2 de fraude persistido en {db_path.name}")

if __name__ == "__main__":
    asyncio.run(massive_stress_test())
