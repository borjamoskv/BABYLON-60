"""
VERIFY-REPORT-Ω: Script de Verificación de Cristalización
Simula la llegada de inteligencia desde Hound-Omega y verifica la generación del reporte.
"""

import asyncio
import logging
import os
from pathlib import Path

from babylon60.engine.shared_bus import SovereignSharedBus
from babylon60.extensions.bpo.engine.report_agent import ReportAgent

logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("VERIFY-REPORT-Ω")


async def test_report_synthesis():
    logger.info("🧪 INICIANDO TEST DE CRISTALIZACIÓN DE REPORTE...")

    # 1. Limpiar entorno de test
    reports_dir = Path("~/10_PROJECTS/Babylon60-Persist/reports")

    # 2. Iniciar el bus y el agente
    bus = SovereignSharedBus(name="bpo_operations", create=True)
    agent = ReportAgent("verify-agent-01")

    # Iniciar listener en background
    listen_task = asyncio.create_task(agent.start_listening())

    # 3. Emitir señal mock de Inteligencia Cristalizada (C4 -> C5 Bridge)
    mock_payload = {
        "opp_id": "TEST-STRIKE-001",
        "project": "Ouroboros-Protocol",
        "mode": "P-FLASH",
        "intelligence_state": {
            "hypotheses": [
                {
                    "title": "Transient accounting drift in settlement layer",
                    "severity": "HIGH",
                    "description": "The logic fails to verify the timestamp of the last settlement when applying rewards.",
                }
            ],
            "proof_of_concept": "1. Deploy OuroborosPoC\n2. Call trigger_drift(100)\n3. Observe unauthorized reward minting.",
            "target_code": "function applyReward(address user) public {\n    uint delta = now - lastSettled[user];\n    _mint(user, delta * rate); // VULNERABILITY: No check for stale metadata\n}",
        },
    }

    logger.info("📡 Emitiendo señal bpo:intelligence_crystallized...")
    await bus.emit(
        event_type="bpo:intelligence_crystallized", payload=mock_payload, source="mock-auditor"
    )

    # 4. Esperar síntesis (Gemini 3 Flash)
    logger.info("⏳ Esperando síntesis del LLM (Gemini 3 Flash)...")
    await asyncio.sleep(15)  # Tiempo para el roundtrip del LLM

    # 5. Verificar resultado
    found = False
    for f in reports_dir.glob("AUDIT_Ouroboros-Protocol_*.md"):
        logger.info("✨ REPORTE ENCONTRADO: %s", f.name)
        # logger.info("Contenido:\n%s", f.read_text()[:500])
        found = True
        break

    if found:
        logger.info("✅ TEST EXITOSO: Pipeline de Reporte Operativo.")
    else:
        logger.error("❌ TEST FALLIDO: No se generó el reporte.")

    # Cleanup
    listen_task.cancel()
    bus.unlink()


if __name__ == "__main__":
    if not os.getenv("GEMINI_API_KEY"):
        logger.error("Viga maestra ausente: GEMINI_API_KEY no detectado. El test fallará.")
    else:
        asyncio.run(test_report_synthesis())
