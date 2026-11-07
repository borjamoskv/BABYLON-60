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
import math
import time
import resource
import httpx
import os
from dataclasses import dataclass, field
from enum import Enum
from datetime import timezone
from email.utils import parsedate_to_datetime
from typing import Any, Callable, Optional
from urllib.parse import urlsplit


class SecurityError(Exception):
    pass


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


LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
PROVIDER_HOSTS = {
    InferenceBackend.MOONSHOT_REMOTE: "api.moonshot.cn",
    InferenceBackend.OPENROUTER_REMOTE: "openrouter.ai",
}


def _parse_backend(value: object) -> InferenceBackend:
    if isinstance(value, InferenceBackend):
        return value
    if isinstance(value, str):
        try:
            return InferenceBackend(value)
        except ValueError:
            pass
    raise SecurityError("Unknown inference backend; no provider selected")


def _validate_endpoint(url: str, backend: InferenceBackend) -> str:
    if (
        not isinstance(url, str)
        or not url
        or url != url.strip()
        or "\\" in url
        or any(ord(char) <= 32 or ord(char) == 127 for char in url)
    ):
        raise SecurityError("Invalid inference endpoint")
    backend = _parse_backend(backend)
    try:
        parts = urlsplit(url)
        host, port = parts.hostname, parts.port
        parsed = httpx.URL(url)
    except (ValueError, httpx.InvalidURL):
        raise SecurityError("Invalid inference endpoint") from None
    if (
        not host
        or not parts.netloc
        or parts.scheme not in ("http", "https")
        or parts.username is not None
        or parts.password is not None
        or parts.query
        or parts.fragment
        or "?" in url
        or "#" in url
        or parts.netloc.endswith(":")
        or (port is not None and not 1 <= port <= 65535)
    ):
        raise SecurityError("Invalid inference endpoint contract")
    if parsed.host != host or parsed.scheme != parts.scheme:
        raise SecurityError("Ambiguous inference endpoint")
    if host in LOOPBACK_HOSTS:
        # Preserve explicit loopback gateways from the original endpoint allowlist.
        return str(parsed)
    expected_host = PROVIDER_HOSTS.get(backend)
    if host != expected_host or parts.scheme != "https" or port not in (None, 443):
        raise SecurityError("Inference endpoint is outside the selected provider contract")
    return str(parsed)


def _get_default_moonshot_url() -> str:
    url = os.getenv("MOONSHOT_API_URL") or "https://api.moonshot.cn/v1/chat/completions"
    return _validate_endpoint(url, InferenceBackend.MOONSHOT_REMOTE)


def _get_default_moonshot_key() -> str:
    return os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY") or ""


def _get_default_openrouter_url() -> str:
    url = os.getenv("OPENROUTER_API_URL") or "https://openrouter.ai/api/v1/chat/completions"
    return _validate_endpoint(url, InferenceBackend.OPENROUTER_REMOTE)


def _get_default_openrouter_key() -> str:
    return os.getenv("OPENROUTER_API_KEY", "")


@dataclass(frozen=True)
class _RequestTarget:
    backend: InferenceBackend
    url: str = field(repr=False)
    key: str = field(repr=False)
    model: str
    timeout: float


@dataclass
class SwarmConfig:
    """Configuración determinista del enjambre."""

    # Topología PxS (defaults: Pareto Cero-Thrashing en ARM64)
    p_cores: int = 4
    s_threads: int = 1

    # Backend de inferencia
    backend: InferenceBackend = InferenceBackend.MOONSHOT_REMOTE

    # Endpoints
    moonshot_url: str | None = field(default=None, repr=False)
    moonshot_key: str | None = field(default=None, repr=False)
    moonshot_model: str | None = None

    openrouter_url: str | None = field(default=None, repr=False)
    openrouter_key: str | None = field(default=None, repr=False)
    openrouter_model: str | None = None

    local_url: str = field(default="http://localhost:8000/v1/chat/completions", repr=False)
    local_model: str = "kimi-k3-1bit"  # Nombre del modelo en vLLM/MLX

    # Termodinámica
    temperature: float = 0.3
    mcts_delay_s: float = 2.8  # Postulado MCTS (futex sleep)
    request_timeout_s: float = 120.0

    # Resiliencia & Ring-0 Governance
    max_retries: int = 3
    retry_base_delay_s: float = 1.0
    circuit_breaker_threshold: int = 5  # Fallos consecutivos antes de abortar
    delegate_circuit_breaker: bool = False  # INV_C5_CB_SUBORDINATION: Delega el CB a Ring-0 / Gateway

    def __post_init__(self) -> None:
        self.backend = _parse_backend(self.backend)
        url = self._url_for(self.backend)
        if self.backend == InferenceBackend.MOONSHOT_REMOTE:
            self.moonshot_url = url
        elif self.backend == InferenceBackend.OPENROUTER_REMOTE:
            self.openrouter_url = url
        else:
            self.local_url = url

    def _url_for(self, backend: InferenceBackend) -> str:
        if backend == InferenceBackend.MOONSHOT_REMOTE:
            url = self.moonshot_url if self.moonshot_url is not None else _get_default_moonshot_url()
        elif backend == InferenceBackend.OPENROUTER_REMOTE:
            url = self.openrouter_url if self.openrouter_url is not None else _get_default_openrouter_url()
        else:
            url = self.local_url
        return _validate_endpoint(url, backend)

    def _key_for(self, backend: InferenceBackend) -> str:
        if backend == InferenceBackend.MOONSHOT_REMOTE:
            key = self.moonshot_key if self.moonshot_key is not None else _get_default_moonshot_key()
        elif backend == InferenceBackend.OPENROUTER_REMOTE:
            key = self.openrouter_key if self.openrouter_key is not None else _get_default_openrouter_key()
        else:
            return ""
        if not isinstance(key, str) or any(ord(char) < 32 or ord(char) == 127 for char in key):
            raise SecurityError("Invalid inference credential format")
        return key

    def _model_for(self, backend: InferenceBackend) -> str:
        if backend == InferenceBackend.MOONSHOT_REMOTE:
            model = (
                self.moonshot_model
                if self.moonshot_model is not None
                else os.getenv("MOONSHOT_MODEL", "moonshot-v1-auto")
            )
        elif backend == InferenceBackend.OPENROUTER_REMOTE:
            model = (
                self.openrouter_model
                if self.openrouter_model is not None
                else os.getenv("OPENROUTER_MODEL", "openrouter/auto")
            )
        else:
            model = self.local_model
        if not isinstance(model, str):
            raise SecurityError("Invalid inference model format")
        return model

    def _request_target(self, backend: InferenceBackend, url: str) -> _RequestTarget:
        return _RequestTarget(
            backend,
            _validate_endpoint(url, backend),
            self._key_for(backend),
            self._model_for(backend),
            self.request_timeout_s,
        )

    @property
    def max_concurrent(self) -> int:
        return self.p_cores * self.s_threads

    @property
    def api_url(self) -> str:
        return self._url_for(_parse_backend(self.backend))

    @property
    def api_key(self) -> str:
        backend = _parse_backend(self.backend)
        self._url_for(backend)  # Validate before resolving the selected credential.
        return self._key_for(backend)

    @property
    def model_name(self) -> str:
        backend = _parse_backend(self.backend)
        self._url_for(backend)
        return self._model_for(backend)


# ─────────────────────────────────────────────────────────
# § 2. Agent Pager (Zero-Friction Interruption)
# ─────────────────────────────────────────────────────────


class AgentPager:
    """
    Primitiva de sincronización para enjambres masivos.
    Implementa Fan-Out Multicast O(1) via asyncio.Event compartido.
    Los subagentes duermen en futex (0% CPU) hasta recibir la señal.
    """

    def __init__(self) -> None:
        self._event = asyncio.Event()

    async def wait_for_beep(self) -> None:
        await self._event.wait()

    def beep(self) -> None:
        self._event.set()

    def reset(self) -> None:
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

    def to_dict(self) -> dict[str, Any]:
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


def capture_kernel_snapshot() -> tuple[resource.struct_rusage, resource.struct_rusage]:
    """Captura snapshot de rusage (self + children)."""
    u_self = resource.getrusage(resource.RUSAGE_SELF)
    u_child = resource.getrusage(resource.RUSAGE_CHILDREN)
    return u_self, u_child


def compute_telemetry(
    t0: float,
    t1: float,
    before: tuple[resource.struct_rusage, resource.struct_rusage],
    after: tuple[resource.struct_rusage, resource.struct_rusage],
) -> KernelTelemetry:
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


async def _http_post_single_attempt(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    timeout: float,
    backend: InferenceBackend,
) -> dict[str, Any]:
    backend = _parse_backend(backend)
    url = _validate_endpoint(url, backend)
    for name, value in headers.items():
        if (
            not isinstance(name, str)
            or not isinstance(value, str)
            or any(ord(char) < 32 or ord(char) == 127 for char in name + value)
            or name.lower() in ("host", "proxy-authorization", "proxy-connection")
        ):
            raise SecurityError("Unsupported inference header")
        if backend not in PROVIDER_HOSTS and name.lower() == "authorization":
            raise SecurityError("Local inference does not accept an Authorization header")
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False, trust_env=False) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict):
            return data
        return {"response": data}


MAX_RATE_LIMIT_DELAY_S = 60.0


def _rate_limit_delay(response: httpx.Response, fallback: float) -> float:
    """Honor delta-seconds or HTTP-date Retry-After within a bounded wait."""
    delay = fallback
    value = response.headers.get("Retry-After")
    if value is not None:
        try:
            delay = float(value)
        except ValueError:
            try:
                retry_at = parsedate_to_datetime(value)
                if retry_at.tzinfo is None:
                    retry_at = retry_at.replace(tzinfo=timezone.utc)
                delay = retry_at.timestamp() - time.time()
            except (ValueError, TypeError, OverflowError):
                delay = fallback
    if not math.isfinite(delay):
        delay = fallback
    return min(MAX_RATE_LIMIT_DELAY_S, max(0.0, delay))


class RobustLLMClient:
    """Cliente HTTP resiliente con circuit breaker y retries."""

    def __init__(self, config: SwarmConfig) -> None:
        config._url_for(_parse_backend(config.backend))
        self.config = config
        self._consecutive_failures = 0

    def reset_circuit_breaker(self) -> None:
        """Resetea el contador de fallos consecutivos en Python."""
        self._consecutive_failures = 0

    @property
    def is_circuit_breaker_tripped(self) -> bool:
        """Indica si el circuit breaker local está abierto (anulado si está subordinado a Ring-0)."""
        if self.config.delegate_circuit_breaker:
            return False
        return self._consecutive_failures >= self.config.circuit_breaker_threshold

    async def call(self, messages: list[dict[str, Any]]) -> str:
        backend = _parse_backend(self.config.backend)
        url = self.config._url_for(backend)
        if self.is_circuit_breaker_tripped:
            return f"🔴 Circuit breaker abierto: {self._consecutive_failures} fallos consecutivos. Backend: {backend.value}"
        target = self.config._request_target(backend, url)
        headers = {"Content-Type": "application/json"}
        if target.key:
            headers["Authorization"] = f"Bearer {target.key}"
        payload = {"model": target.model, "messages": messages, "temperature": self.config.temperature}
        max_retries = self.config.max_retries
        base_delay = self.config.retry_base_delay_s
        for attempt in range(1, max_retries + 1):
            try:
                data = await _http_post_single_attempt(target.url, payload, headers, target.timeout, target.backend)
                self._consecutive_failures = 0
                content = data["choices"][0]["message"]["content"]
                return str(content) if content is not None else ""
            except httpx.HTTPStatusError as error:
                if error.response.status_code != 429:
                    self._consecutive_failures += 1
                    return f"Error HTTP {error.response.status_code}"
                if attempt >= max_retries:
                    self._consecutive_failures += 1
                    return "Error HTTP 429: Máximo de reintentos agotado."
                delay = _rate_limit_delay(error.response, base_delay * (2 ** (attempt - 1)))
                log.warning("Rate limit (429). Reintento %s/%s en %.1fs", attempt, max_retries, delay)
                await asyncio.sleep(delay)
            except (httpx.ConnectError, httpx.ReadTimeout) as error:
                self._consecutive_failures += 1
                if attempt >= max_retries:
                    return f"Error de conexión tras {max_retries} reintentos ({type(error).__name__})"
                delay = base_delay * (2 ** (attempt - 1))
                log.warning("Conexión fallida. Reintento %s/%s en %.1fs", attempt, max_retries, delay)
                await asyncio.sleep(delay)
            except SecurityError:
                raise
            except Exception as error:
                self._consecutive_failures += 1
                return f"Error inesperado ({type(error).__name__})"
        return "Error: Máximo de reintentos agotado."


# ─────────────────────────────────────────────────────────
# § 5. Fases del Enjambre
# ─────────────────────────────────────────────────────────


async def task_decomposer(client: RobustLLMClient, prompt: str, max_tasks: int) -> list[str]:
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

    log.info("Planner: descomponiendo tarea")
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
    on_progress: Optional[Callable[[int, str, float], None]] = None,
) -> dict[str, Any]:
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

        log.info("Subagente %s: ejecutando tarea", task_id)
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


async def anergy_reducer(client: RobustLLMClient, original_prompt: str, results: list[dict[str, Any]]) -> str:
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
    subtask_results: list[dict[str, Any]]
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
    prompt: str,
    p_cores: int = 4,
    s_threads: int = 1,
    backend: str = "moonshot",
    on_progress: Optional[Callable[[int, str, float], None]] = None,
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
    backend_enum = _parse_backend(backend)

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
    clean_results: list[dict[str, Any]] = []
    for i, r in enumerate(results):
        if isinstance(r, BaseException):
            clean_results.append(
                {
                    "task_id": i,
                    "task_desc": subtasks[i] if i < len(subtasks) else "?",
                    "status": "ERROR",
                    "result": str(r),
                    "elapsed_s": 0.0,
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
