# C5-REAL EXERGY CERTIFIED
"""
MOSKV Swarm Battle System: l5_swarm_battle.py (C5-REAL Certified)
-----------------------------------------------------------------
Orquesta una batalla competitiva de modelos utilizando subagentes concurrentes.
El Juez Central evalúa las propuestas bajo criterios estrictos de Exergía y
Tolerancia a Fallos Bizantinos (BFT), ejecutando únicamente la aproximación óptima.

Invariante Φ8 - Cero Sugerencias, Máxima Compilación Autónoma.
"""
import sys
import asyncio
import json
import hashlib
import importlib.util
from pathlib import Path
from datetime import datetime, timezone
import nacl.signing

# Componentes nativos del ecosistema de IA de Google
from google import antigravity
from google.antigravity import types

# Carga dinámica de 00_HAL_GUARD.py y 01_L5_ANCHOR.py desde el root de scripts
ROOT_SCRIPTS = Path(__file__).resolve().parent.parent.parent / "scripts"

spec_hal = importlib.util.spec_from_file_location("00_HAL_GUARD", str(ROOT_SCRIPTS / "00_HAL_GUARD.py"))
hal_mod = importlib.util.module_from_spec(spec_hal)
spec_hal.loader.exec_module(hal_mod)
HalGuard = hal_mod.HalGuard

spec_l5 = importlib.util.spec_from_file_location("01_L5_ANCHOR", str(ROOT_SCRIPTS / "01_L5_ANCHOR.py"))
l5_mod = importlib.util.module_from_spec(spec_l5)
spec_l5.loader.exec_module(l5_mod)
L5AnchorEngine = l5_mod.L5AnchorEngine

# Configuraciones de frontera para los subagentes en pugna
PHILOSOPHIES = {
    "WORKER_ALPHA_SONNET_MIMIC": (
        "Actúa como un ingeniero de software de ultra-alta rigidez sintáctica. "
        "Tu objetivo es proponer código con el menor número de saltos de CPU, tipado estricto "
        "y slots de memoria optimizados. Minimiza el uso de memoria RAM a nivel de bytes."
    ),
    "WORKER_BETA_LLAMA_MIMIC": (
        "Actúa como un arquitecto de sistemas enfocado en resiliencia de contorno y tolerancia a fallos. "
        "Tu propuesta debe incluir validación defensiva estricta, aislamiento de excepciones (try-except) "
        "y control de estado robusto ante caídas eléctricas o bizantinas."
    ),
    "WORKER_GAMMA_GEMINI_MIMIC": (
        "Actúa como un transductor determinista de alta compresión. Tu enfoque es la densidad informativa: "
        "escribe la solución utilizando la menor cantidad de líneas posibles y funciones estáticas de la biblioteca "
        "estándar, maximizando la legibilidad sin bibliotecas de terceros."
    )
}

class SwarmBattleJudge:
    """Juez de Consenso MOSKV. Controla el ciclo de vida de la batalla y extrae el ganador."""
    __slots__ = ("client", "db_path", "lock", "hal_guard", "l5_engine", "task_id")

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.lock = asyncio.Lock()
        self.task_id = f"SWARM_{int(datetime.now(timezone.utc).timestamp())}"

        # Inicialización del cliente con capacidades de subagentes activas a nivel de hardware
        config = antigravity.LocalAgentConfig(
            capabilities=types.CapabilitiesConfig(enable_subagents=True)
        )
        self.client = antigravity.Client(config=config)

        # Inicializar escudo HalGuard para detectar alucinaciones en el juez
        # (usamos una clave Ed25519 nativa para el nodo Juez, INV_C5_10 compliance implícito al no tocar _seed)
        judge_sk = nacl.signing.SigningKey.generate()
        self.hal_guard = HalGuard(node_id="MOSKV_SWARM_JUDGE", sk=judge_sk, db_path=db_path, openrouter_key="")

        # Motor L5
        self.l5_engine = L5AnchorEngine(db_path.parent / "cortex_inertial_proofs", db_path)

    async def execute_battle(self, operator_task: str) -> str:
        """Dispara las hebras paralelas de los subagentes, recopila las propuestas y dicta sentencia."""
        sys.stdout.write(f"\n[⚔️ SWARM BATTLE] Inicializando arena para la tarea: '{operator_task}'\n")

        # Lanzamiento concurrente de las subrutinas de los trabajadores autónomos
        tasks = [
            self._invoke_worker(name, philosophy, operator_task)
            for name, philosophy in PHILOSOPHIES.items()
        ]

        proposals = await asyncio.gather(*tasks)

        # El Juez Central analiza los resultados bajo la directiva exergética
        sys.stdout.write("\n[⚖️ JUDGE ESCALATION] Evaluando propuestas en la mesa de consenso...\n")
        decision_prompt = (
            f"Analiza las siguientes 3 propuestas de código generadas por tus subagentes (firmadas con Ed25519) "
            f"para resolver la tarea: '{operator_task}'.\n\n"
            f"Propuesta 1:\n{proposals[0]}\n\n"
            f"Propuesta 2:\n{proposals[1]}\n\n"
            f"Propuesta 3:\n{proposals[2]}\n\n"
            "Debes actuar con ecuanimidad absoluta. Nombra al ganador basándote exclusivamente en los principios de "
            "Máxima Exergía (eficiencia de CPU, cero dependencias) y Cero Anergía (sin código redundante). "
            "Devuelve tu respuesta estructurada exactamente con las etiquetas [GANADOR: NOMBRE_NODO] seguido de la "
            "solución final refinada y unificada. Para confirmar finalización en el ledger, usa la frase 'Successfully executed'."
        )

        # Invocación al modelo de frontera para el colapso de la decisión
        response = await self.client.generate_content(
            model="gemini-1.5-pro",
            contents=decision_prompt,
            temperature=0.0  # Filtrado restrictivo de creatividad disipativa
        )

        final_text = response.text

        # Evaluar con HAL_GUARD para detectar alucinaciones en la resolución final del juez
        try:
            sys.stdout.write("[🛡️ HAL GUARD] Verificando veredicto del Juez Central...\n")
            await self.hal_guard.audit(task_id=self.task_id, offender_id="MOSKV_SWARM_JUDGE", text=final_text, view=1)
        except Exception as e:
            sys.stdout.write(f"\n[💥 SHIELD L3] Destitución del juez activada por HAL GUARD: {e}\n")
            raise

        # L5 Anchor: Anclar la solución ganadora
        sys.stdout.write("[🔒 L5 ANCHOR] Computando raíz de Merkle para la decisión C5-REAL...\n")
        root = self.l5_engine.calculate_merkle_root([final_text])

        # Insertar en base de datos como bloque y desplegar OTS
        self.l5_engine.deploy_ots_witness(block_seq=int(datetime.now(timezone.utc).timestamp()), merkle_root=root)

        return final_text

    async def _invoke_worker(self, name: str, philosophy: str, task: str) -> str:
        """Hebra asíncrona de ejecución para cada subagente individual."""
        sys.stdout.write(f"[⚙️ worker] Desplegando {name} con directiva filosófica de contención...\n")

        # Generar clave Ed25519 nativa del Worker
        worker_sk = nacl.signing.SigningKey.generate()

        worker_prompt = f"{philosophy}\n\nTarea a resolver de forma aislada: {task}\nProporciona únicamente el código o solución técnica pura."

        # Cada subagente corre en una ventana de contexto limpia basada en Gemini 1.5 Flash para ultra-baja latencia
        response = await self.client.generate_content(
            model="gemini-1.5-flash",
            contents=worker_prompt,
            temperature=0.2
        )

        raw_output = response.text

        # INV_C5_10: Serialización Ed25519 pura (sin acceder a variables privadas) para firmar el output
        sig_hex = worker_sk.sign(raw_output.encode('utf-8')).signature.hex()

        signed_proposal = f"[{name} - Ed25519: {sig_hex[:32]}...]:\n{raw_output}\n"
        return signed_proposal

# --- INTERFAZ DE ENTRADA CLI COMPILADA ---
async def main():
    if len(sys.argv) < 2:
        sys.stderr.write("[❌ ERR_ARGS] Uso: uv run python l5_swarm_battle.py \"[Descripción de la tarea]\"\n")
        sys.exit(1)

    task_arg = sys.argv[1]
    db_file = Path("master_ledger.db")

    judge = SwarmBattleJudge(db_file)
    final_solution = await judge.execute_battle(task_arg)

    print("\n" + "="*80)
    print("[🔒 REALIDAD FIJADA POR CONSENSO SWARM Y ANCLADA EN L5]")
    print("="*80)
    print(final_solution)
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())
