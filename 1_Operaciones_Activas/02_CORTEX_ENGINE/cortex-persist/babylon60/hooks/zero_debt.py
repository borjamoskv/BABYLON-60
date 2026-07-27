#!/usr/bin/env python3
# [C5-REAL] Exergy-Maximized
"""ENTROPY-0: El Guardián de la Deuda Técnica.
Este hook de pre-commit aborta el commit si la puntuación de MEJORAlo cae por debajo de 90.
"""

import logging
import sqlite3
import subprocess
import sys
from pathlib import Path

__all__ = ["main"]


def main():
    logging.getLogger(__name__).info("🛡️  ENTROPY-0: Validando entropía del código...")

    # Comprobar si hay archivos Python modificados en staging
    try:
        staged_files = subprocess.check_output(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"], text=True
        ).splitlines()
    except subprocess.CalledProcessError:
        logging.getLogger(__name__).info("❌ Error al obtener archivos cacheados.")
        sys.exit(1)

    python_files = [f for f in staged_files if f.endswith(".py")]

    if not python_files:
        logging.getLogger(__name__).info("⏭️  No hay archivos Python en staging. Omitiendo X-Ray 13D.")
        sys.exit(0)

    # Solo necesitamos el nombre del proyecto, que suele ser el nombre del directorio actual
    project_name = Path.cwd().name

    # Ejecutar cortex mejoralo scan
    logging.getLogger(__name__).info(f"🔍 Ejecutando X-Ray 13D en '{project_name}'...")
    try:
        from babylon60.cli import DEFAULT_DB, get_engine  # type: ignore
        from babylon60.mejoralo import MejoraloEngine

        engine = get_engine(DEFAULT_DB)
        m = MejoraloEngine(engine)

        # Ocultar temporalmente el stdout normal para no saturar, o dejarlo si falla.
        # Mejoralo.scan devuelve un ScoreTracker u objeto con .score
        # Escaneamos el directorio raíz completo para asegurar integridad.
        result = m.scan(project_name, str(Path.cwd()), deep=False)
        import asyncio

        asyncio.run(engine.close())

    except ImportError:
        logging.getLogger(__name__).info("⚠️  Advertencia: Cortex no está disponible en este entorno. Omitiendo.")
        sys.exit(0)
    except (RuntimeError, ValueError, sqlite3.Error) as e:
        logging.getLogger(__name__).info(f"❌ Error al ejecutar MEJORAlo: {e}")
        sys.exit(1)

    score = result.score

    if score < 90:
        logging.getLogger(__name__).info("\n%s", "=" * 50)
        logging.getLogger(__name__).info("🚨 ALERTA DE ENTROPÍA: COMMIT RECHAZADO 🚨")
        logging.getLogger(__name__).info("=" * 50)
        logging.getLogger(__name__).info("La regla soberana ENTROPY-0 exige una puntuación MEJORAlo >= 90.")
        logging.getLogger(__name__).info(f"Puntuación actual: {score}/100")
        logging.getLogger(__name__).info("La mediocridad es crimen. Por favor, usa:")
        logging.getLogger(__name__).info("  cortex mejoralo scan <proyecto> .")
        logging.getLogger(__name__).info("  cortex mejoralo --brutal (si es necesario)")
        logging.getLogger(__name__).info("%s\n", "=" * 50)
        sys.exit(1)

    logging.getLogger(__name__).info(f"✅ Entropía controlada (Score: {score}). Commit permitido.")
    sys.exit(0)


if __name__ == "__main__":
    main()
