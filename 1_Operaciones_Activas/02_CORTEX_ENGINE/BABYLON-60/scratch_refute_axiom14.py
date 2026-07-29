"""
C5-REAL EXERGY CERTIFIED
scratch_refute_axiom14.py
Asedio Termodinámico contra la Invariante Single-Writer (BFTLedgerActor).
Vector de Ataque: Concurrencia masiva y superación de tamaño de payload.
"""
import sys
import asyncio
import logging
from pathlib import Path

BABYLON_ROOT = Path(__file__).resolve().parent
if str(BABYLON_ROOT) not in sys.path:
    sys.path.insert(0, str(BABYLON_ROOT))

from babylon60.bft.ledger_actor import BFTLedgerActor, LedgerEvent

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("falsabiliza_axiom14")

async def attack_ledger():
    db_path = Path("falsabiliza_test.db")
    if db_path.exists():
        db_path.unlink()

    actor = BFTLedgerActor(db_path)
    await actor.start()

    log.info("[ATTACK] Iniciando inyección de concurrencia hostil...")

    # 1. Intentar colisión de inserciones concurrentes extremas sin Semaphore
    async def inject_poison(idx: int):
        # Payload masivo para forzar latencia o corrupción (10MB)
        poison_payload = {"data": "X" * (1024 * 1024), "intent": f"attack-{idx}"}
        event = LedgerEvent(
            stream="scheduler_attack",
            entity_id=f"poison-{idx}",
            event_type="CORRUPTION_ATTEMPT",
            payload=poison_payload,
            cortex_taint="[CORTEX-TAINT:refutation]",
            source_db="falsabiliza",
            source_table="attack",
            source_pk=str(idx)
        )
        try:
            await actor.append(event)
            return True
        except Exception as e:
            log.warning(f"Ataque interceptado: {e}")
            return False

    # Lanzamos 500 tareas de 1MB simultáneamente sin back-off
    tasks = [asyncio.create_task(inject_poison(i)) for i in range(200)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    successes = sum(1 for r in results if r is True)
    log.info(f"[ATTACK RESULT] Operaciones procesadas (o colapsadas): {successes}/200")

    # Verificamos la integridad de la cadena
    try:
        is_valid = await actor.verify_chain()
        if is_valid:
            log.info("[FALSABILIZA FAILED] El actor resistió el asedio. Cadena Causal Inmuta.")
            log.info("El estado del Axioma 14 permanece válido (O_R: Delta S = 0).")
        else:
            log.error("[FALSABILIZA SUCCESS] COLAPSO EPISTÉMICO: La cadena se corrompió.")
    except Exception as e:
         log.error(f"[FALSABILIZA SUCCESS] COLAPSO SINTÁCTICO / EPISTÉMICO: {e}")

    await actor.stop()

if __name__ == "__main__":
    asyncio.run(attack_ledger())
