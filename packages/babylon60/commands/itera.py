# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# babylon60/commands/itera.py
"""
Itera Command - Anergy Purge Protocol Automation
"""
import subprocess
import logging

logger = logging.getLogger("CORTEX.ITERA")

def run_auto_purge() -> None:
    """
    Ejecuta el protocolo de purga de anergía (Fase 1 global) para eliminar
    archivos huérfanos y cachés residuales antes del commit.
    """
    logger.info("💀 [ITERA] Iniciando purga de anergía termodinámica...")
    try:
        subprocess.run(["find", ".", "-name", "*.db-shm", "-delete"], check=False)
        subprocess.run(["find", ".", "-name", "*.db-wal", "-delete"], check=False)
        subprocess.run(["find", ".", "-name", "__pycache__", "-type", "d", "-exec", "rm", "-rf", "{}", "+"], check=False)
        logger.info("✅ [ITERA] Anergía purgada con éxito. Exergía maximizada.")
    except Exception as e:
        logger.warning(f"⚠️ [ITERA] Fricción detectada durante la purga: {e}")

