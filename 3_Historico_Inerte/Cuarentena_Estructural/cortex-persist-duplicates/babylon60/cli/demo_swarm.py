# [C5-REAL] Exergy-Maximized
from __future__ import annotations

import asyncio
import logging

from babylon60.cli.bicameral import bicameral


async def run_swarm_demo():
    logging.getLogger(__name__).info("\n")
    # 1. El Orquestador evalúa la magnitud
    await asyncio.sleep(1)
    bicameral.log_motor(
        "Petición: Refactor masivo de 50 archivos (Arquitectura Hexagonal).", action="SCOPE"
    )
    await asyncio.sleep(1)
    bicameral.log_autonomic(
        "Evaluación de recursos: Requiere Enjambre (>10 archivos).", check="CAPACITY"
    )

    logging.getLogger(__name__).info("\n%s", "═" * 80)
    logging.getLogger(__name__).info(" ⧖ PROTOCOLO LEGION-1 INICIADO: CLONACIÓN DE LINAJE")
    logging.getLogger(__name__).info("%s\n", "═" * 80)

    # 2. Síntesis del Linaje
    await asyncio.sleep(1)
    bicameral.log_limbic("Sintetizando soul.md, lore.md y nemesis.md...", source="GENESIS")
    await asyncio.sleep(1)
    bicameral.log_limbic(
        "Empaquetando 14 alergias operativas y 3 cicatrices críticas.", source="GENESIS"
    )
    await asyncio.sleep(0.5)
    bicameral.log_motor("Exportando -> cortex_bloodline_091.json", action="BUILD")

    logging.getLogger(__name__).info("\n%s", "─" * 40)
    # 3. Despliegue del Enjambre (Workers naciendo con contexto)
    await asyncio.sleep(1)
    for i in range(1, 4):
        logging.getLogger(__name__).info(f"[⚡] Instanciando Worker-0{i} [Modelo: Flash] [Contexto: Bloodline_091]")
        await asyncio.sleep(0.2)

    logging.getLogger(__name__).info("%s\n", "─" * 40)

    # 4. Prueba del Linaje Heredeado
    await asyncio.sleep(1)
    bicameral.log_limbic(
        "Worker-02 reporta: Detectada inyección de dependencias errónea. Abortando por regla Nemesis-04.",
        source="SWARM",
    )
    await asyncio.sleep(1)
    bicameral.log_limbic(
        "Worker-03 reporta: Refactor completado esquivando error de concurrencia gracias a Cicatriz ep_0042.",
        source="SWARM",
    )

    logging.getLogger(__name__).info("\n%s", "═" * 80)
    logging.getLogger(__name__).info(" ⧖ CONSENSO BIZANTINO ALCANZADO | ENJAMBRE DISUELTO")
    logging.getLogger(__name__).info("%s\n", "═" * 80)

    # 5. Cierre Motor
    await asyncio.sleep(1)
    bicameral.log_motor("Merge final completado con éxito. Ninguna regla rota.", action="DONE")
    logging.getLogger(__name__).info("\n")


if __name__ == "__main__":
    asyncio.run(run_swarm_demo())
