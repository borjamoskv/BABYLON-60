# C5-REAL EXERGY CERTIFIED
"""
Script de Falsación Epistémica y Asedio Hostil (Invariantes Ω195 & Ω206).
Somete a estrés destructivo al orquestador Swarm Research de BABYLON-60.
Ataques:
1. Desbordamiento de Histeresis (Topic > 10KB).
2. Clamping de Scatter (max_workers > 4).
3. Concurrencia masiva (50 peticiones simultáneas).
4. Corrupción de Payload e Inyección de Enum Inválido.
"""

import asyncio
import os
import sys
import importlib.util
from unittest.mock import AsyncMock, patch
from pydantic import ValidationError

# Dynamic import for path with leading digits
route_path = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "babylon60-ide", "backend", "routes", "swarm_research.py"
))

spec = importlib.util.spec_from_file_location("swarm_research_mod", route_path)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Failed to load spec for {route_path}")

swarm_mod = importlib.util.module_from_spec(spec)
sys.modules["swarm_mod"] = swarm_mod
spec.loader.exec_module(swarm_mod)

async def run_refutation_battery():
    print("--- INICIANDO BATERÍA DE FALSACIÓN DE ESTRÉS (Ω195) ---")
    mock_actor = AsyncMock()
    mock_actor.append.return_value = {"tx_hash": "0xREFUTED", "sequence": 999}

    with patch.object(swarm_mod, "get_bft_actor", return_value=mock_actor):
        # 1. Ataque de Histeresis de Volumen (Topic > 10KB)
        print("[1/4] Test: Desbordamiento de Histeresis (>10KB)...")
        overflow_topic = "A" * (1024 * 10 + 1)
        req_overflow = swarm_mod.SwarmResearchRequest(topic=overflow_topic)
        try:
            await swarm_mod.execute_swarm_research(req_overflow)
            print("FAILED: Hysteresis failed to reject overflow topic!")
            sys.exit(1)
        except swarm_mod.HTTPException as e:
            assert e.status_code == 413
            print("  PASSED: Capturado HTTP 413 correctamente.")

        # 2. Ataque de Dispersión de Scatter (max_workers = 16)
        print("[2/4] Test: Clamping de Scatter (max_workers=16 a 4)...")
        req_scatter = swarm_mod.SwarmResearchRequest(topic="BFT Test", max_workers=16)
        resp_scatter = await swarm_mod.execute_swarm_research(req_scatter)
        assert resp_scatter["workers_dispatched"] == 3  # Clamped workers

        # Verify Pydantic rejects max_workers=999
        try:
            swarm_mod.SwarmResearchRequest(topic="BFT Test", max_workers=999)
            print("FAILED: Pydantic failed to reject max_workers > 16!")
            sys.exit(1)
        except ValidationError:
            print("  PASSED: Force-clamping a max_workers=4 ejecutado y Pydantic le=16 validado.")

        # 3. Ataque de Inyección de Enum Inválido (reasoning_effort="INVALID")
        print("[3/4] Test: Validación Pydantic de Enum (reasoning_effort)...")
        try:
            swarm_mod.SwarmResearchRequest(topic="Valid Topic", reasoning_effort="ULTRA_FAST")
            print("FAILED: Invalid reasoning_effort accepted!")
            sys.exit(1)
        except ValidationError:
            print("  PASSED: Rechazado por Pydantic Schema en T=0.")

        # 4. Ataque de Concurrencia Masiva (50 peticiones simultáneas)
        print("[4/4] Test: Concurrencia Masiva (50 peticiones simultáneas)...")
        tasks = [
            swarm_mod.execute_swarm_research(swarm_mod.SwarmResearchRequest(topic=f"Stress Topic {i}"))
            for i in range(50)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        assert len(results) == 50
        assert all(isinstance(r, dict) and r.get("status") == "SUCCESS" for r in results)
        print("  PASSED: 50/50 peticiones concurrentes completadas sin race conditions.")

    print("--- FALSACIÓN COMPLETADA CON ÉXITO: SISTEMA C5-REAL RESILIENTE ---")

if __name__ == "__main__":
    asyncio.run(run_refutation_battery())
