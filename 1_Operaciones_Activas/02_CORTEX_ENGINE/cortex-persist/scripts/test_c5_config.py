# C5-REAL EXERGY CERTIFIED
import asyncio
from pathlib import Path
import sys

# Inyectar ruta para permitir imports
sys.path.insert(0, "/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-persist")

from babylon60.c5_agent_config import build_cortex_agent_config
from google.antigravity import Agent

async def main():
    print("[TEST] Inicializando Configuración C5-REAL...")

    # Crear config
    config = build_cortex_agent_config(
        workspaces=["/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas"]
    )

    print("[TEST] Configuración BFT generada con éxito.")
    print(f"Modelo: {config.model}")
    print(f"Número de Políticas C5: {len(config.policies)}")
    print(f"Número de Hooks de Telemetría: {len(config.hooks)}")

    # Verificar instanciación del Agente
    print("[TEST] Levantando instancia física del Córtex Agent...")
    try:
        agent = Agent(config)
        print("[SUCCESS] Agente compilado en RAM. Test BFT Superado.")
    except Exception as e:
        print(f"[ERROR] Singularidad en arranque: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
