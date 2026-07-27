# C5-REAL EXERGY CERTIFIED
# [C5-REAL] Exergy-Maximized
"""
cat_id: test-deployment
cat_type: script
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P2
"""

import asyncio
import logging

from babylon60.engine.core.cortex_engine import CortexEngine
from babylon60.extensions.llm import _telemetry as llm_telemetry
from babylon60.extensions.llm._models import CascadeEvent, CascadeTier, IntentProfile
from babylon60.observability.telemetry import telemetry


async def main():
    logging.getLogger(__name__).info("Iniciando CortexEngine (Despliegue)...")
    engine = CortexEngine()
    await engine.start()

    logging.getLogger(__name__).info("Inyectando telemetría asíncrona de prueba (System Health)...")
    telemetry.log_event("deploy-test", "call-01", "DeploymentTest", "system_health_check", duration_ms=10)

    logging.getLogger(__name__).info("Inyectando telemetría LLM asíncrona...")
    llm_telemetry_inst = llm_telemetry.CascadeTelemetry()
    event = CascadeEvent(
        intent=IntentProfile.CODE,
        resolved_by="gemini-3.5-flash",
        tier=CascadeTier.FAST,
        depth=1,
        latency_ms=120.5
    )
    llm_telemetry_inst.emit(event)

    # Wait to allow async tasks to process
    await asyncio.sleep(0.5)
    logging.getLogger(__name__).info("Telemetría enrutada exitosamente.")

if __name__ == "__main__":
    asyncio.run(main())
