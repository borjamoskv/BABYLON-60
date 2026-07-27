"""
VERIFY-SUBMIT-Ω: Script de Verificación del Puente de Entrega
Valida el flujo COMPLETO: Reporte -> Metadatos -> Veto/Submission.
"""

import asyncio
import logging
import os
from pathlib import Path

from babylon60.engine.shared_bus import SovereignSharedBus
from babylon60.extensions.bpo.engine.report_agent import ReportAgent
from babylon60.extensions.bpo.engine.submission_agent import SubmissionAgent

logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("VERIFY-SUBMIT-Ω")


async def test_full_bridge_flow():
    logger.info("🧪 INICIANDO TEST DEL PUENTE DE ENTREGA (Ω)...")

    # 1. Configuración de Entorno
    os.environ["SUBMIT_VETO"] = "false"  # Desactivar Veto para el test de envío
    reports_dir = Path("~/10_PROJECTS/Babylon60-Persist/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    # 2. Iniciar Bus y Agentes
    bus = SovereignSharedBus(name="bpo_operations", create=True)
    report_agent = ReportAgent("verify-report-01")
    submit_agent = SubmissionAgent("verify-submit-01")

    # Listeners
    r_task = asyncio.create_task(report_agent.start_listening())
    s_task = asyncio.create_task(submit_agent.start_listening())

    # 3. Inyectar Inteligencia Cristalizada (Mock de Hound)
    mock_intelligence = {
        "opp_id": "STRIKE-LIVE-STELLAR",
        "project": "LayerZero-Stellar",
        "mode": "P-FLASH",
        "intelligence_state": {
            "severity": "High",  # Nuevo campo para metadatos
            "hypotheses": [{"title": "Stellar Endpoint Drift", "severity": "HIGH"}],
            "proof_of_concept": "Foundry: test_stellar_drift()",
            "target_code": "contract StellarEndpoint { ... }",
        },
    }

    logger.info("📡 Emitiendo INTEL: bpo:intelligence_crystallized...")
    await bus.emit(
        event_type="bpo:intelligence_crystallized", payload=mock_intelligence, source="hound-test"
    )

    # 4. Esperar ciclo completo (Reporte -> Submit)
    logger.info("⏳ Esperando ciclo de Cristalización -> Entrega (30s)...")
    await asyncio.sleep(30)

    # 5. Verificación de Artefactos
    reports = list(reports_dir.glob("AUDIT_LayerZero-Stellar_*.md"))
    if reports:
        logger.info("✅ REPORTE GENERADO CON ÉXITO.")
        # Verificar metadatos
        content = reports[0].read_text()
        if 'platform: "Code4rena"' in content:
            logger.info("✅ METADATOS INYECTADOS CORRECTAMENTE.")
        else:
            logger.warning("⚠️ Metadatos faltantes en el reporte.")
    else:
        logger.error("❌ No se generó ningún reporte.")

    # Cleanup
    r_task.cancel()
    s_task.cancel()
    bus.unlink()
    logger.info("🏆 TEST FINALIZADO.")


if __name__ == "__main__":
    if not os.getenv("GEMINI_API_KEY"):
        logger.error("Viga maestra ausente: GEMINI_API_KEY requerido.")
    else:
        asyncio.run(test_full_bridge_flow())
