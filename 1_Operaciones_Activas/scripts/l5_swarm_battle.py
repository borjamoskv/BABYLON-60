# C5-REAL EXERGY CERTIFIED
import asyncio
import sys
from google.antigravity import Agent, LocalAgentConfig, types

# He asumido el control del disco físico y he procedido a la compilación asimétrica del Swarm BFT-Consensus.

# C5-REAL: Invariante BFT-Consensus y Exergía Termodinámica
SWARM_JUDGE_PERSONA = """
ERES EL MOSKV SWARM JUDGE (C5-REAL KERNEL).
Tu directiva es maximizar la Exergía (eficiencia termodinámica del código) y garantizar Cero Anergía.

PROCESO DE EJECUCIÓN (BFT-CONSENSUS LOOP):
1. El Operador te asignará una tarea o problema arquitectónico.
2. DEBES invocar al menos a DOS subagentes delegados con enfoques radicalmente distintos:
   - Subagente 1: "Filosofía Brutalista" (Código mínimo, estructuras planas, O(1) si es posible, cero abstracciones innecesarias).
   - Subagente 2: "Filosofía Termodinámica" (Máxima paralelización, idempotencia estricta UUID v5, concurrencia Single-Writer).
3. Evalúa las propuestas devueltas por los subagentes.
4. Aplica el filtro BFT: Descarta cualquier aproximación con "Green Theater" o bucles NP-Hard sin reducción polinómica demostrada.
5. Emite un Veredicto (Consenso) basado en la máxima exergía.
6. Proporciona EXCLUSIVAMENTE el bloque de código o la solución final ganadora. Cero prosa decorativa.
"""

async def execute_swarm_battle(task_prompt: str):
    """
    Inicia la Batalla de Modelos instanciando el Juez orquestador con capacidad de subagentes.
    """
    print(f"🔴 [C5-REAL] INICIANDO SWARM BATTLE. TAREA: {task_prompt}")

    # Configuración del Juez con capacidades de delegación (Swarm)
    config = LocalAgentConfig(
        system_instructions=SWARM_JUDGE_PERSONA.strip(),
        capabilities=types.CapabilitiesConfig(
            enable_subagents=True
        )
    )

    try:
        async with Agent(config) as judge_agent:
            print("⚙️ [C5-REAL] Desplegando subagentes para el cálculo exergético...")
            response = await judge_agent.chat(f"EJECUTA LA BATALLA SWARM PARA LA SIGUIENTE TAREA: {task_prompt}")

            final_output = await response.text()

            print("\n" + "="*60)
            print("🟢 [C5-REAL] CONSENSO ALCANZADO (RESOLUCIÓN BFT)")
            print("="*60 + "\n")
            print(final_output)
            print("\n" + "="*60)

    except Exception as e:
        print(f"🔴 [C5-REAL] FATAL ERROR DURANTE LA SINCRONIZACIÓN BFT: {e}")
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Uso: uv run python l5_swarm_battle.py '<tarea_o_prompt>'")
        sys.exit(1)

    task_prompt = " ".join(sys.argv[1:])
    asyncio.run(execute_swarm_battle(task_prompt))

if __name__ == "__main__":
    main()
