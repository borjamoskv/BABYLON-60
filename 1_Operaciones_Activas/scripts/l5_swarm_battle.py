# C5-REAL EXERGY CERTIFIED
"""
MOSKV Swarm Battle System: l5_swarm_battle.py (C5-REAL Certified v2.0 - Multi-Oracle Mesh)
------------------------------------------------------------------------------------------
Orquesta una batalla competitiva de modelos utilizando subagentes concurrentes y oráculos de red.
El Juez Central evalúa las propuestas bajo criterios estrictos de Exergía y
Tolerancia a Fallos Bizantinos (BFT), ejecutando únicamente la aproximación óptima.

Invariante Φ8 - Cero Sugerencias, Máxima Compilación Autónoma.
Invariante INV_C5_10 - PyNaCl ED25519 Serialization Compliance.
"""
import os
import sys
import asyncio
import json
import hashlib
import time
import importlib.util
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional
import nacl.signing

# Componentes nativos del ecosistema de IA de Google
from google import antigravity
from google.antigravity import types

# Carga dinámica de 00_HAL_GUARD.py, 01_L5_ANCHOR.py y 52_OR_BFT_NODE.py desde ROOT_SCRIPTS
ROOT_SCRIPTS = Path(__file__).resolve().parent.parent.parent / "scripts"

spec_hal = importlib.util.spec_from_file_location("00_HAL_GUARD", str(ROOT_SCRIPTS / "00_HAL_GUARD.py"))
hal_mod = importlib.util.module_from_spec(spec_hal)
spec_hal.loader.exec_module(hal_mod)
HalGuard = hal_mod.HalGuard

spec_l5 = importlib.util.spec_from_file_location("01_L5_ANCHOR", str(ROOT_SCRIPTS / "01_L5_ANCHOR.py"))
l5_mod = importlib.util.module_from_spec(spec_l5)
spec_l5.loader.exec_module(l5_mod)
L5AnchorEngine = l5_mod.L5AnchorEngine

spec_or = importlib.util.spec_from_file_location("52_OR_BFT_NODE", str(ROOT_SCRIPTS / "52_OR_BFT_NODE.py"))
or_mod = importlib.util.module_from_spec(spec_or)
spec_or.loader.exec_module(or_mod)
OpenRouterBFTNode = or_mod.OpenRouterBFTNode

# Directivas de contención filosófica para la matriz de modelos
PHILOSOPHIES = {
    "WORKER_ALPHA_SONNET_MIMIC": {
        "model": "anthropic/claude-3.5-sonnet",
        "fallback_model": "gemini-1.5-pro",
        "directive": (
            "Actúa como un ingeniero de software de ultra-alta rigidez sintáctica. "
            "Tu objetivo es proponer código con el menor número de saltos de CPU, tipado estricto "
            "y slots de memoria optimizados. Minimiza el uso de memoria RAM a nivel de bytes."
        )
    },
    "WORKER_BETA_LLAMA_MIMIC": {
        "model": "meta-llama/llama-3.1-70b-instruct",
        "fallback_model": "gemini-1.5-flash",
        "directive": (
            "Actúa como un arquitecto de sistemas enfocado en resiliencia de contorno y tolerancia a fallos. "
            "Tu propuesta debe incluir validación defensiva estricta, aislamiento de excepciones (try-except) "
            "y control de estado robusto ante caídas eléctricas o bizantinas."
        )
    },
    "WORKER_GAMMA_GEMINI_MIMIC": {
        "model": "google/gemini-1.5-pro",
        "fallback_model": "gemini-1.5-flash",
        "directive": (
            "Actúa como un transductor determinista de alta compresión. Tu enfoque es la densidad informativa: "
            "escribe la solución utilizando la menor cantidad de líneas posibles y funciones estáticas de la biblioteca "
            "estándar, maximizando la legibilidad sin bibliotecas de terceros."
        )
    }
}

class SwarmBattleJudge:
    """Juez de Consenso MOSKV v2.0. Controla la matriz heterogénea de modelos y ancla veredictos en L5."""
    __slots__ = ("client", "db_path", "lock", "hal_guard", "l5_engine", "task_id", "openrouter_key")

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.lock = asyncio.Lock()
        self.task_id = f"SWARM_{int(datetime.now(timezone.utc).timestamp())}"
        self.openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")

        # Cliente nativo Antigravity con capacidades de delegación activadas
        config = antigravity.LocalAgentConfig(
            capabilities=types.CapabilitiesConfig(enable_subagents=True)
        )
        self.client = antigravity.Client(config=config)

        # Escudo de contención de alucinaciones (HAL GUARD)
        judge_sk = nacl.signing.SigningKey.generate()
        self.hal_guard = HalGuard(node_id="MOSKV_SWARM_JUDGE", sk=judge_sk, db_path=db_path, openrouter_key=self.openrouter_key)

        # Motor de fijación inerte en la constante universal L5
        self.l5_engine = L5AnchorEngine(db_path.parent / "cortex_inertial_proofs", db_path)

    async def execute_battle(self, operator_task: str) -> str:
        """Dispara la malla distribuida de trabajadores en paralelo y dicta sentencia por consenso exergético."""
        sys.stdout.write(f"\n[⚔️ SWARM BATTLE v2.0] Inicializando arena para la tarea: '{operator_task}'\n")

        # Invocación paralela de los nodos trabajadores
        tasks = [
            self._invoke_worker(name, config["directive"], config["model"], config["fallback_model"], operator_task)
            for name, config in PHILOSOPHIES.items()
        ]

        proposals = await asyncio.gather(*tasks)

        sys.stdout.write("\n[⚖️ JUDGE ESCALATION] Auditando propuestas firmadas en la mesa de consenso...\n")
        decision_prompt = (
            f"Analiza las siguientes 3 propuestas de código generadas por tus subagentes (firmadas criptográficamente con Ed25519) "
            f"para resolver la tarea: '{operator_task}'.\n\n"
            f"Propuesta 1:\n{proposals[0]}\n\n"
            f"Propuesta 2:\n{proposals[1]}\n\n"
            f"Propuesta 3:\n{proposals[2]}\n\n"
            "Debes actuar con ecuanimidad absoluta. Nombra al ganador basándote exclusivamente en los principios de "
            "Máxima Exergía (eficiencia de CPU, cero dependencias) y Cero Anergía (código mínimo, sin redundancias). "
            "Devuelve tu respuesta estructurada exactamente con las etiquetas [GANADOR: NOMBRE_NODO] seguido de la "
            "solución final refinada y unificada. Para confirmar finalización en el ledger, usa la frase 'Successfully executed'."
        )

        # Inferencia del Juez mediante cliente Antigravity nativo
        response = await self.client.generate_content(
            model="gemini-1.5-pro",
            contents=decision_prompt,
            temperature=0.0
        )

        final_text = response.text

        # 1. Auditoría HAL_GUARD ante alucinación o Green Theater
        try:
            sys.stdout.write("[🛡️ HAL GUARD] Sometiendo veredicto del Juez Central a escrutinio BFT...\n")
            await self.hal_guard.audit(task_id=self.task_id, offender_id="MOSKV_SWARM_JUDGE", text=final_text, view=1)
        except Exception as e:
            sys.stdout.write(f"\n[💥 SHIELD L3] Destitución del juez activada por HAL GUARD: {e}\n")
            raise

        # 2. Anclaje inerte L5 OpenTimestamps
        sys.stdout.write("[🔒 L5 ANCHOR] Calculando raíz de Merkle y fijando atestación inerte...\n")
        root = self.l5_engine.calculate_merkle_root([final_text])
        self.l5_engine.deploy_ots_witness(block_seq=int(datetime.now(timezone.utc).timestamp()), merkle_root=root)

        return final_text

    async def _invoke_worker(self, name: str, directive: str, model_endpoint: str, fallback_model: str, task: str) -> str:
        """Invoca un trabajador de la malla utilizando OpenRouter TCP socket o el SDK nativo."""
        sys.stdout.write(f"[⚙️ worker] Desplegando {name} en modelo {model_endpoint}...\n")
        t0 = time.perf_counter()

        # Generar par de claves Ed25519 para el sobre del trabajador (INV_C5_10)
        worker_sk = nacl.signing.SigningKey.generate()
        worker_prompt = f"{directive}\n\nTarea a resolver de forma aislada: {task}\nProporciona únicamente el código o solución técnica pura."

        raw_output = None

        # Intentar llamada por OpenRouter TCP Socket si la clave está disponible
        if self.openrouter_key:
            node = OpenRouterBFTNode(name, model_endpoint, self.openrouter_key, timeout_ms=8000)
            raw_output = await node.query_oracle(directive, task)

        # Fallback autónomo a SDK Antigravity si no hay respuesta o falla OpenRouter
        if not raw_output:
            sys.stdout.write(f"[⚙️ fallback] Ruteando {name} al SDK nativo ({fallback_model})...\n")
            response = await self.client.generate_content(
                model=fallback_model,
                contents=worker_prompt,
                temperature=0.2
            )
            raw_output = response.text

        dt_ms = (time.perf_counter() - t0) * 1000
        # Serialización segura Ed25519 sin tocar atributos privados
        sig_bytes = worker_sk.sign(raw_output.encode('utf-8')).signature
        sig_hex = sig_bytes.hex()

        signed_proposal = (
            f"[{name} | Target: {model_endpoint} | Latency: {dt_ms:.1f}ms | Sig: {sig_hex[:24]}...]:\n"
            f"{raw_output}\n"
        )
        return signed_proposal

# --- INTERFAZ CLI COMPILADA DE ALTA EXERGÍA ---
async def main():
    if len(sys.argv) < 2:
        sys.stderr.write("[❌ ERR_ARGS] Uso: uv run python 1_Operaciones_Activas/scripts/l5_swarm_battle.py \"[Descripción de la tarea]\"\n")
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
