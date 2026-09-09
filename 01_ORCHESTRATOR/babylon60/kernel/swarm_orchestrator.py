"""
Kimi K3 Swarm Sovereign Orchestrator — C5-REAL (v2.0)

Ingeniería inversa del patrón "K3 Swarm máx." con:
  - Dual-backend: Moonshot API remota ↔ vLLM/MLX local (air-gapped)
  - Telemetría de kernel macOS (ru_nivcsw, ru_nvcsw) en cada colapso
  - Resiliencia: reintentos con backoff exponencial + circuit breaker
  - Streaming de progreso vía callbacks
  - Topología PxS calibrada empíricamente (anti-thrashing ARM64)
"""

import asyncio
import json
import logging
import time
import resource
import httpx
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("swarm")


# ─────────────────────────────────────────────────────────
# § 1. Configuración Dual-Backend (Soberanía de Datos)
# ─────────────────────────────────────────────────────────


class InferenceBackend(Enum):
    """Selector de backend de inferencia."""

    MOONSHOT_REMOTE = "moonshot"  # API remota (api.moonshot.cn)
    OPENROUTER_REMOTE = "openrouter"  # API remota (openrouter.ai/api/v1)
    LOCAL_VLLM = "local_vllm"  # vLLM local (OpenAI-compatible)
    LOCAL_MLX = "local_mlx"  # MLX server local (Apple Silicon)


def _get_default_moonshot_url() -> str:
    return os.getenv("MOONSHOT_API_URL") or "https://api.moonshot.cn/v1/chat/completions"


def _get_default_moonshot_key() -> str:
    return os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY", "")


def _get_default_openrouter_url() -> str:
    return os.getenv("OPENROUTER_API_URL") or "https://openrouter.ai/api/v1/chat/completions"


def _get_default_openrouter_key() -> str:
    return os.getenv("OPENROUTER_API_KEY", "")


@dataclass
class SwarmConfig:
    """Configuración determinista del enjambre."""

    # Topología PxS (defaults: Pareto Cero-Thrashing en ARM64)
    p_cores: int = 4
    s_threads: int = 1

    # Backend de inferencia
    backend: InferenceBackend = InferenceBackend.MOONSHOT_REMOTE

    # Endpoints
    moonshot_url: str = field(default_factory=_get_default_moonshot_url)
    moonshot_key: str = field(default_factory=_get_default_moonshot_key)
    moonshot_model: str = os.getenv("MOONSHOT_MODEL", "moonshot-v1-auto")

    openrouter_url: str = field(default_factory=_get_default_openrouter_url)
    openrouter_key: str = field(default_factory=_get_default_openrouter_key)
    openrouter_model: str = os.getenv("OPENROUTER_MODEL", "openrouter/auto")

    local_url: str = "http://localhost:8000/v1/chat/completions"
    local_model: str = "kimi-k3-1bit"  # Nombre del modelo en vLLM/MLX

    # Termodinámica
    temperature: float = 0.3
    mcts_delay_s: float = 2.8  # Postulado MCTS (futex sleep)
    request_timeout_s: float = 120.0

    # Resiliencia
    max_retries: int = 3
    retry_base_delay_s: float = 1.0
    circuit_breaker_threshold: int = 5  # Fallos consecutivos antes de abortar

    @property
    def max_concurrent(self) -> int:
        return self.p_cores * self.s_threads

    @property
    def api_url(self) -> str:
        if self.backend == InferenceBackend.MOONSHOT_REMOTE:
            return self.moonshot_url
        if self.backend == InferenceBackend.OPENROUTER_REMOTE:
            return self.openrouter_url
        return self.local_url

    @property
    def api_key(self) -> str:
        if self.backend == InferenceBackend.MOONSHOT_REMOTE:
            return self.moonshot_key
        if self.backend == InferenceBackend.OPENROUTER_REMOTE:
            return self.openrouter_key
        return ""  # Local no requiere key

    @property
    def model_name(self) -> str:
        if self.backend == InferenceBackend.MOONSHOT_REMOTE:
            return self.moonshot_model
        if self.backend == InferenceBackend.OPENROUTER_REMOTE:
            return self.openrouter_model
        return self.local_model


# ─────────────────────────────────────────────────────────
# § 2. Agent Pager (Zero-Friction Interruption)
# ─────────────────────────────────────────────────────────


class AgentPager:
    """
    Primitiva de sincronización para enjambres masivos.
    Implementa Fan-Out Multicast O(1) via asyncio.Event compartido.
    Los subagentes duermen en futex (0% CPU) hasta recibir la señal.
    """

    def __init__(self):
        self._event = asyncio.Event()

    async def wait_for_beep(self):
        await self._event.wait()

    def beep(self):
        self._event.set()

    def reset(self):
        self._event.clear()


# ─────────────────────────────────────────────────────────
# § 3. Telemetría de Kernel (macOS ARM64)
# ─────────────────────────────────────────────────────────


@dataclass
class KernelTelemetry:
    """Snapshot de métricas de kernel OS para auditoría de thrashing."""

    wall_time_s: float = 0.0
    involuntary_cs: int = 0  # ru_nivcsw (context switches forzados por scheduler)
    voluntary_cs: int = 0  # ru_nvcsw (context switches cooperativos)
    max_rss_mb: float = 0.0  # Peak resident set size

    def is_thrashing(self, threshold: int = 2132) -> bool:
        """Umbral empírico de thrashing para macOS ARM64 (del protocolo swarm-quantum-collapse)."""
        return self.involuntary_cs > threshold

    def to_dict(self) -> dict:
        return {
            "wall_time_s": round(self.wall_time_s, 3),
            "involuntary_cs": self.involuntary_cs,
            "voluntary_cs": self.voluntary_cs,
            "max_rss_mb": round(self.max_rss_mb, 2),
            "thrashing_detected": self.is_thrashing(),
        }

    def __str__(self) -> str:
        status = "⚠️ THRASHING" if self.is_thrashing() else "✅ NOMINAL"
        return (
            f"⚡ Telemetría Kernel [{status}]: "
            f"wall={self.wall_time_s:.2f}s | "
            f"ru_nivcsw={self.involuntary_cs} | "
            f"ru_nvcsw={self.voluntary_cs} | "
            f"RSS={self.max_rss_mb:.1f}MB"
        )


def capture_kernel_snapshot():
    """Captura snapshot de rusage (self + children)."""
    u_self = resource.getrusage(resource.RUSAGE_SELF)
    u_child = resource.getrusage(resource.RUSAGE_CHILDREN)
    return u_self, u_child


def compute_telemetry(t0, t1, before, after) -> KernelTelemetry:
    """Calcula delta de telemetría entre dos snapshots."""
    (s0, c0) = before
    (s1, c1) = after
    return KernelTelemetry(
        wall_time_s=t1 - t0,
        involuntary_cs=(s1.ru_nivcsw - s0.ru_nivcsw) + (c1.ru_nivcsw - c0.ru_nivcsw),
        voluntary_cs=(s1.ru_nvcsw - s0.ru_nvcsw) + (c1.ru_nvcsw - c0.ru_nvcsw),
        max_rss_mb=max(s1.ru_maxrss, c1.ru_maxrss) / (1024 * 1024),  # bytes -> MB en macOS
    )


# ─────────────────────────────────────────────────────────
# § 4. Cliente de Inferencia con Resiliencia
# ─────────────────────────────────────────────────────────


class InferenceClient:
    """
    Cliente HTTP asíncrono con:
      - Reintentos con backoff exponencial
    """


async def _http_post_single_attempt(url: str, payload: dict, headers: dict, timeout: float) -> dict:
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()


class RobustLLMClient:
    """Cliente HTTP resiliente con circuit breaker y retries."""

    def __init__(self, config: SwarmConfig):
        self.config = config
        self._consecutive_failures = 0

    async def call(self, messages: list) -> str:
        if self._consecutive_failures >= self.config.circuit_breaker_threshold:
            return f"🔴 Circuit breaker abierto: {self._consecutive_failures} fallos consecutivos. Backend: {self.config.backend.value}"

        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        payload = {"model": self.config.model_name, "messages": messages, "temperature": self.config.temperature}

        for attempt in range(1, self.config.max_retries + 1):
            try:
                data = await _http_post_single_attempt(
                    self.config.api_url, payload, headers, self.config.request_timeout_s
                )
                self._consecutive_failures = 0
                return data["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as e:
                if e.response.status_code != 429:
                    self._consecutive_failures += 1
                    return f"Error HTTP {e.response.status_code}: {e.response.text[:200]}"
                delay = self.config.retry_base_delay_s * (2 ** (attempt - 1))
                log.warning(f"⏳ Rate limit (429). Reintento {attempt}/{self.config.max_retries} en {delay:.1f}s...")
                await asyncio.sleep(delay)
            except (httpx.ConnectError, httpx.ReadTimeout) as e:
                self._consecutive_failures += 1
                if attempt >= self.config.max_retries:
                    return f"Error de conexión tras {self.config.max_retries} reintentos: {str(e)}"
                delay = self.config.retry_base_delay_s * (2 ** (attempt - 1))
                log.warning(f"⏳ Conexión fallida. Reintento {attempt}/{self.config.max_retries} en {delay:.1f}s...")
                await asyncio.sleep(delay)
            except Exception as e:
                self._consecutive_failures += 1
                return f"Error inesperado: {str(e)}"

        return "Error: Máximo de reintentos agotado."


# ─────────────────────────────────────────────────────────
# § 5. Fases del Enjambre
# ─────────────────────────────────────────────────────────


async def task_decomposer(client: RobustLLMClient, prompt: str, max_tasks: int) -> list:
    """
    Fase 1: TaskDecomposer (Planner).
    Toma un prompt complejo y genera hasta max_tasks subtareas JSON.
    """
    messages = [
        {
            "role": "system",
            "content": (
                f"Eres el TaskDecomposer de un orquestador Swarm C5-REAL. "
                f"Desglosa el problema del usuario en un máximo de {max_tasks} subtareas "
                f"de investigación paralela. Cada subtarea debe ser autocontenida "
                f"(sin dependencias entre ellas). "
                f"Devuelve ÚNICAMENTE un array JSON de strings, sin markdown ni explicación."
            ),
        },
        {"role": "user", "content": prompt},
    ]

    log.info(f"🧠 [Planner] Descomponiendo: '{prompt[:80]}...'")
    response = await client.call(messages)

    try:
        # Parsear JSON (con tolerancia a envolturas de markdown)
        text = response
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        subtasks = json.loads(text.strip())

        if not isinstance(subtasks, list):
            subtasks = [str(subtasks)]
        # Asegurar que todos los elementos son strings
        subtasks = [str(s) for s in subtasks if s]

    except (json.JSONDecodeError, IndexError):
        log.warning("⚠️ [Planner] Parseo JSON fallido. Fallback: tarea monolítica.")
        subtasks = [prompt]

    return subtasks[:max_tasks]


async def execute_subagent(
    task_id: int,
    task_desc: str,
    client: RobustLLMClient,
    pager: AgentPager,
    semaphore: asyncio.Semaphore,
    mcts_delay: float,
    on_progress: Optional[Callable] = None,
) -> dict:
    """
    Fase 2: Ejecución de un nodo del enjambre.
    Respeta invariantes:
      - Espera en futex (AgentPager) antes de adquirir semáforo
      - MCTS delay post-adquisición
      - Devuelve resultado estructurado (no solo texto plano)
    """
    log.info(f"💤 [Subagente {task_id}] Letargo (futex wait)...")
    await pager.wait_for_beep()

    async with semaphore:
        log.info(f"🚀 [Subagente {task_id}] Adquirió semáforo. MCTS delay {mcts_delay}s...")
        await asyncio.sleep(mcts_delay)

        log.info(f"🧠 [Subagente {task_id}] Ejecutando: '{task_desc[:60]}...'")
        t0 = time.perf_counter()

        messages = [
            {
                "role": "system",
                "content": (
                    "Eres un subagente especializado de un enjambre C5-REAL. "
                    "Resuelve tu subtarea con precisión, rigor y concisión. "
                    "No repitas la pregunta. Ve directo a la respuesta."
                ),
            },
            {"role": "user", "content": task_desc},
        ]
        result_text = await client.call(messages)
        elapsed = time.perf_counter() - t0

        is_error = result_text.startswith("Error") or result_text.startswith("🔴")
        status = "ERROR" if is_error else "OK"

        log.info(f"{'❌' if is_error else '✅'} [Subagente {task_id}] {status} en {elapsed:.1f}s")

        if on_progress:
            on_progress(task_id, status, elapsed)

        return {
            "task_id": task_id,
            "task_desc": task_desc,
            "status": status,
            "result": result_text,
            "elapsed_s": round(elapsed, 2),
        }


async def anergy_reducer(client: RobustLLMClient, original_prompt: str, results: list) -> str:
    """
    Fase 3: AnergyReducer (Síntesis).
    Unifica los reportes eliminando redundancia y entropía discursiva.
    """
    # Filtrar solo los resultados exitosos
    successful = [r for r in results if r["status"] == "OK"]
    failed = [r for r in results if r["status"] == "ERROR"]

    if not successful:
        return f"🔴 Colapso fallido: {len(failed)}/{len(results)} subagentes erraron.\n" + "\n".join(
            f"  - Subagente {r['task_id']}: {r['result'][:100]}" for r in failed
        )

    combined = "\n\n".join(f"### Subtarea {r['task_id']}: {r['task_desc']}\n{r['result']}" for r in successful)

    log.info(f"🔮 [AnergyReducer] Sintetizando {len(successful)} resultados ({len(failed)} fallos)...")

    messages = [
        {
            "role": "system",
            "content": (
                "Eres el AnergyReducer de un orquestador Swarm C5-REAL. "
                "Unifica los informes de los subagentes en UNA respuesta cohesiva, "
                "estructurada y final. Elimina redundancias (anergía), "
                "consolida hallazgos, y señala contradicciones si las hay. "
                "Usa formato Markdown."
            ),
        },
        {
            "role": "user",
            "content": f"Petición original: {original_prompt}\n\nReportes de {len(successful)} subagentes:\n{combined}",
        },
    ]
    return await client.call(messages)


# ─────────────────────────────────────────────────────────
# § 6. Orquestador Principal
# ─────────────────────────────────────────────────────────


@dataclass
class SwarmResult:
    """Resultado completo de un colapso cuántico."""

    prompt: str
    synthesis: str
    subtask_results: list
    telemetry: KernelTelemetry
    config: SwarmConfig
    n_subtasks: int = 0
    n_successful: int = 0
    n_failed: int = 0

    def summary(self) -> str:
        return (
            f"\n{'=' * 60}\n"
            f"🌌 COLAPSO CUÁNTICO COMPLETADO\n"
            f"{'=' * 60}\n"
            f"Backend: {self.config.backend.value}\n"
            f"Topología: P={self.config.p_cores} × S={self.config.s_threads}\n"
            f"Subtareas: {self.n_subtasks} total | {self.n_successful} OK | {self.n_failed} ERROR\n"
            f"{self.telemetry}\n"
            f"{'=' * 60}\n"
        )


async def run_swarm_orchestrator(
    prompt: str, p_cores: int = 4, s_threads: int = 1, backend: str = "moonshot", on_progress: Optional[Callable] = None
) -> str:
    """
    Punto de entrada principal del Kimi Swarm Soberano.

    Args:
        prompt: Tarea compleja a descomponer y resolver en paralelo.
        p_cores: Procesos paralelos (cores lógicos asignados).
        s_threads: Hilos de I/O por core (concurrencia de red).
        backend: "moonshot" | "openrouter" | "local_vllm" | "local_mlx"
        on_progress: Callback opcional para streaming de progreso.

    Returns:
        Texto sintetizado final del AnergyReducer.
    """
    # Configuración
    backend_enum = {
        "moonshot": InferenceBackend.MOONSHOT_REMOTE,
        "openrouter": InferenceBackend.OPENROUTER_REMOTE,
        "local_vllm": InferenceBackend.LOCAL_VLLM,
        "local_mlx": InferenceBackend.LOCAL_MLX,
    }.get(backend, InferenceBackend.MOONSHOT_REMOTE)

    config = SwarmConfig(p_cores=p_cores, s_threads=s_threads, backend=backend_enum)
    client = RobustLLMClient(config)

    log.info(
        f"🌌 [Swarm] Iniciando colapso cuántico — Backend: {config.backend.value}, Topología: P={p_cores}×S={s_threads}"
    )

    # Captura telemetría pre-colapso
    kernel_before = capture_kernel_snapshot()
    t0 = time.perf_counter()

    # Fase 1: Descomposición
    subtasks = await task_decomposer(client, prompt, config.max_concurrent)
    if not subtasks:
        return "El Planner no pudo descomponer la tarea."

    log.info(f"🔥 [Swarm] Clúster: {len(subtasks)} subagentes instanciados")

    # Fase 2: Instanciar enjambre
    pager = AgentPager()
    semaphore = asyncio.Semaphore(config.max_concurrent)

    tasks = [
        asyncio.create_task(execute_subagent(i, desc, client, pager, semaphore, config.mcts_delay_s, on_progress))
        for i, desc in enumerate(subtasks)
    ]

    # Esperar a que todos los tasks estén en futex (letargo)
    await asyncio.sleep(0.3)

    # Beep: Fan-Out Multicast O(1)
    log.info(f"🔔 [Swarm] BEEP → {len(tasks)} subagentes despertando simultáneamente")
    pager.beep()

    # Recoger resultados
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Normalizar excepciones
    clean_results = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            clean_results.append(
                {
                    "task_id": i,
                    "task_desc": subtasks[i] if i < len(subtasks) else "?",
                    "status": "ERROR",
                    "result": str(r),
                    "elapsed_s": 0,
                }
            )
        else:
            clean_results.append(r)

    # Fase 3: Reducción de anergía
    synthesis = await anergy_reducer(client, prompt, clean_results)

    # Telemetría post-colapso
    t1 = time.perf_counter()
    kernel_after = capture_kernel_snapshot()
    telemetry = compute_telemetry(t0, t1, kernel_before, kernel_after)

    n_ok = sum(1 for r in clean_results if r["status"] == "OK")
    n_err = len(clean_results) - n_ok

    result = SwarmResult(
        prompt=prompt,
        synthesis=synthesis,
        subtask_results=clean_results,
        telemetry=telemetry,
        config=config,
        n_subtasks=len(clean_results),
        n_successful=n_ok,
        n_failed=n_err,
    )

    log.info(result.summary())

    # Devolver síntesis + telemetría como texto para MCP
    return f"{synthesis}\n\n---\n{result.summary()}"
