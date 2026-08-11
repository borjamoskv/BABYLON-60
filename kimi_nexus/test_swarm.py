import asyncio
from swarm_orchestrator import run_swarm_orchestrator

async def main():
    print("🚀 Iniciando Test Cuántico del K3 Swarm Orchestrator...")
    prompt = "Resume en 3 puntos clave la importancia de la topología PxS para evitar thrashing en sistemas unificados."
    result = await run_swarm_orchestrator(prompt, p_cores=2, s_threads=1)
    print("\n\n✅ RESULTADO FINAL (Anergy Reducer):")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
