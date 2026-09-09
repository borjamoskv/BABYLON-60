#!/usr/bin/env python3
import asyncio
import os
import sys

# Ajustar PYTHONPATH para resolver 01_ORCHESTRATOR
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../01_ORCHESTRATOR')))

from babylon60.kernel.swarm_orchestrator import run_swarm_orchestrator

async def main():
    print("============================================================")
    print("🔥 C5-REAL | PoC: Falsación Termodinámica de OpenRouter Gateway")
    print("============================================================")
    
    # Inyectar la key para la prueba
    os.environ["OPENROUTER_API_KEY"] = "sk-or-v1-a6ab3545b6b1fcb4e3c983a483ff1c83ab4f2c009d94944d32029"
        
    print(f"🔑 Key detectada: {os.environ['OPENROUTER_API_KEY'][:12]}... (oculta por seguridad)")
    print("🚀 Disparando orquestador con backend = 'openrouter' y topología P=2 x S=1...\n")

    try:
        # Falsación Empírica del Gateway con un prompt sencillo
        result = await run_swarm_orchestrator(
            prompt="Dime un aforismo termodinámico C5-REAL en 1 frase corta.",
            p_cores=2,
            s_threads=1,
            backend="openrouter"
        )
        print("\n✅ [FALSACIÓN SUPERADA]: El gateway de OpenRouter respondió sin deadlocks.")
        print("--- RESULTADO DE SÍNTESIS ---")
        print(result)
        
    except Exception as e:
        print(f"\n❌ [ERROR DE BISIMULACIÓN]: El colapso cuántico falló: {e}")

if __name__ == "__main__":
    asyncio.run(main())
