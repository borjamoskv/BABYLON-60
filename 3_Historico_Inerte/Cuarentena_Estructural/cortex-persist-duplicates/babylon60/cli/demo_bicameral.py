# [C5-REAL] Exergy-Maximized
import asyncio
import logging

from babylon60.cli.bicameral import bicameral


async def run_bicameral_demo():
    logging.getLogger(__name__).info("\n")
    # 1. El agente recibe una petición
    # Usuario: "Crea un componente de login usando TailwindCSS"

    # 2. Reacción Límbica (Nemesis intercepta)
    await asyncio.sleep(1)
    bicameral.log_limbic("Evaluando petición contra nemesis.md...", source="NEMESIS")
    await asyncio.sleep(1)
    bicameral.log_limbic(
        "ALERGIA DETECTADA: Intento de uso de TailwindCSS. El repo usa Vanilla CSS.",
        source="NEMESIS",
    )
    await asyncio.sleep(1)
    bicameral.log_limbic(
        "Estrategia alterada: Purgar intención de Tailwind. Forzar Vanilla CSS avanzado.",
        source="LORE",
    )

    logging.getLogger(__name__).info()
    # 3. Reacción Autonómica (Tether verifica permisos)
    await asyncio.sleep(1)
    bicameral.log_autonomic(
        "Verificando TETHER. Límite de tokens en sesión: 25,000 / 100,000.", check="BUDGET"
    )
    await asyncio.sleep(0.5)
    bicameral.log_autonomic(
        "Verificando acceso a sistema de archivos. Carpeta permitida: /src/components.", check="I/O"
    )

    logging.getLogger(__name__).info()
    # 4. Córtex Motor (Ejecución)
    await asyncio.sleep(1)
    bicameral.log_motor("Generando componente de Login (Vanilla CSS)...", action="CODE")
    await asyncio.sleep(1)
    bicameral.log_motor("Escribiendo archivo en /src/components/Login.js", action="WRITE")
    await asyncio.sleep(0.5)
    bicameral.log_motor("Componente creado con UI state-of-the-art (130/100).", action="DONE")
    logging.getLogger(__name__).info("\n")


if __name__ == "__main__":
    asyncio.run(run_bicameral_demo())
