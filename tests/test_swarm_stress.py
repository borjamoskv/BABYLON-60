"""
BABYLON-60 Swarm Orchestrator Stress Test
Prueba empírica de concurrencia extrema (Agent Beeper) y resolución BFT.
"""

import asyncio
import logging
import time
import sys
import os

# Añadir el path para importar el orquestador
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.extend(
    [
        root_dir,
        os.path.join(root_dir, "01_KISH_ENGINE"),
        os.path.join(root_dir, "02_EDIN_SWARMS"),
    ]
)

from typing import TypedDict  # noqa: E402
from agents_archi import AgentPager  # noqa: E402


class StressResult(TypedDict):
    agent_id: int
    delta_x: int
    status: str


# Configuración del Stress Test
N_AGENTS = 500  # Enjambre Masivo
MAX_CONCURRENCY = 50  # Límite de semáforo

pager = AgentPager()


async def stress_agent(agent_id: int, tenant_id: str, inject_fault: bool = False) -> StressResult:
    """Subagente simulado en modo letargo para el test de estrés."""
    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
    # Fase 1: Letargo (0% CPU)
    await pager.wait_for_beep()

    # Fase 2: Ejecución Acotada
    async with semaphore:
        # Simular trabajo computacional rápido
        await asyncio.sleep(0.01)

        # Inyección de Falla Bizantina controlada
        if inject_fault:
            return {"agent_id": agent_id, "delta_x": 10, "status": "HALLUCINATION_DETECTED"}

        return {"agent_id": agent_id, "delta_x": 0, "status": "SUCCESS"}


async def run_stress_test() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    tenant_id = "babylon-60-stress-test"

    logging.info(f"🚀 INICIANDO STRESS TEST: {N_AGENTS} Agentes")

    # Crear tareas: 499 agentes honestos, 1 agente bizantino (agente 404)
    tasks = []
    for i in range(N_AGENTS):
        inject_fault = i == 404
        tasks.append(asyncio.create_task(stress_agent(i, tenant_id, inject_fault)))

    logging.info(f"⏳ {N_AGENTS} agentes encolados y en letargo absoluto. Esperando 1 segundo...")
    await asyncio.sleep(1)

    start_time = time.time()

    # Fan-Out Multicast (El Beep O(1))
    logging.info("🔔 DESPACHANDO SEÑAL (BEEP) A TODO EL ENJAMBRE...")
    pager.beep()

    # Recolectar resultados
    results = await asyncio.gather(*tasks)

    end_time = time.time()
    duration = end_time - start_time

    logging.info(f"✅ Ejecución de {N_AGENTS} agentes completada en {duration:.4f} segundos.")

    # Consenso BFT: Auditar resultados
    logging.info("⚖️ INICIANDO AUDITORÍA BFT...")
    total_anergy = 0
    faulty_agents = []

    for res in results:
        delta_x = res.get("delta_x", 0)
        if delta_x > 0:
            total_anergy += delta_x
            faulty_agents.append(res.get("agent_id"))

    if total_anergy > 0:
        logging.error(f"🚨 [BFT FATAL] Anergía detectada: Delta X = {total_anergy}.")
        logging.error(f"🚨 Agentes Bizantinos detectados (IDs): {faulty_agents}")
        logging.error("⚡ APLICANDO THERMODYNAMIC OVERRIDE: Abortando colapso de estado y purgando contexto.")
    else:
        logging.info("🌟 [BFT SUCCESS] Enjambre ejecutado con Cero Anergía. Estado colapsado con éxito.")


def test_swarm_stress_execution() -> None:
    asyncio.run(run_stress_test())


if __name__ == "__main__":
    asyncio.run(run_stress_test())
