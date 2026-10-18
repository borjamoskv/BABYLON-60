#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ SWARM ORCHESTRATOR CORE | DOMAIN: 02_EDIN_SWARMS (edin.swarms) | STATE: C5-REAL
# ============================================================================
"""
Sovereign Swarm Orchestration Engine — 02_EDIN_SWARMS (edin.swarms) (C5-REAL v4.0).

Core features:
  - Multi-Backend Inference: Moonshot / OpenRouter / local vLLM / Apple Silicon MLX
  - macOS ARM64 Kernel Telemetry (ru_nivcsw, ru_nvcsw, RSS)
  - Zero-Friction Interruption via AgentPager (O(1) futex wait)
  - Circuit Breaker & Exponential Backoff
  - PxS Topological Scaling (Pareto Zero-Thrashing on Apple Silicon)
"""

import asyncio
import json
import logging
import os
import resource
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, List, Dict, Any, Optional, Tuple

logger = logging.getLogger("02_EDIN_SWARMS.orchestrator.swarm")
"""Primary execution logger for 02_EDIN_SWARMS (edin.swarms)."""


class InferenceBackend(Enum):
    """Supported inference execution backends."""

    MOONSHOT_REMOTE = "moonshot"
    OPENROUTER_REMOTE = "openrouter"
    LOCAL_VLLM = "local_vllm"
    LOCAL_MLX = "local_mlx"


def _get_default_moonshot_url() -> str:
    return os.getenv("MOONSHOT_API_URL") or "https://api.moonshot.cn/v1/chat/completions"


def _get_default_moonshot_key() -> str:
    return os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY") or ""


def _get_default_openrouter_url() -> str:
    return os.getenv("OPENROUTER_API_URL") or "https://openrouter.ai/api/v1/chat/completions"


def _get_default_openrouter_key() -> str:
    return os.getenv("OPENROUTER_API_KEY", "")


@dataclass
class SwarmConfig:
    """Deterministic configuration for Swarm execution."""

    p_cores: int = 4
    s_threads: int = 1
    backend: InferenceBackend = InferenceBackend.MOONSHOT_REMOTE

    # Endpoints
    moonshot_url: str = field(default_factory=_get_default_moonshot_url)
    moonshot_key: str = field(default_factory=_get_default_moonshot_key)
    moonshot_model: str = os.getenv("MOONSHOT_MODEL", "moonshot-v1-auto")

    openrouter_url: str = field(default_factory=_get_default_openrouter_url)
    openrouter_key: str = field(default_factory=_get_default_openrouter_key)
    openrouter_model: str = os.getenv("OPENROUTER_MODEL", "thinkingmachines/inkling:free")
    openrouter_fallback_models: List[str] = field(
        default_factory=lambda: [
            "thinkingmachines/inkling:free",
            "poolside/laguna-s-2.1:free",
            "cohere/north-mini-code:free",
            "nvidia/nemotron-3-super-120b-a12b:free",
        ]
    )

    local_url: str = os.getenv("BABYLON_LOCAL_LLM_URL", "http://localhost:8000/v1/chat/completions")
    local_model: str = os.getenv("BABYLON_LOCAL_LLM_MODEL", "deepseek-r1-distill-qwen-32b")
    local_ollama_url: str = os.getenv("BABYLON_LOCAL_OLLAMA_URL", "http://127.0.0.1:11434/v1/chat/completions")
    local_ollama_model: str = os.getenv("BABYLON_LOCAL_OLLAMA_MODEL", "qwen3:1.7b")
    enable_local_failover: bool = True

    # Thermodynamics & Execution Parameters
    temperature: float = 0.3
    mcts_delay_s: float = 0.05
    request_timeout_s: float = 60.0

    # Resilience & Ring-0 Governance
    max_retries: int = 3
    retry_base_delay_s: float = 0.5
    circuit_breaker_threshold: int = 5
    delegate_circuit_breaker: bool = False  # INV_C5_CB_SUBORDINATION: Delega el CB a Ring-0 / Gateway
    strict_model_floor: bool = False  # Veto Flash/Mini/Small/XS/:free & force allow_fallbacks=False
    allow_provider_fallbacks: bool = True

    @property
    def max_concurrent(self) -> int:
        return max(1, self.p_cores * self.s_threads)

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
        return ""

    @property
    def model_name(self) -> str:
        if self.backend == InferenceBackend.MOONSHOT_REMOTE:
            return self.moonshot_model
        if self.backend == InferenceBackend.OPENROUTER_REMOTE:
            return self.openrouter_model
        return self.local_model


class AgentPager:
    """
    Synchronization primitive for massive swarms.
    Implements Fan-Out Multicast O(1) via shared asyncio.Event.
    Subagents sleep in zero-CPU wait until the signal is triggered.
    """

    def __init__(self) -> None:
        self._event = asyncio.Event()

    async def wait_for_beep(self) -> None:
        await self._event.wait()

    def beep(self) -> None:
        self._event.set()

    def reset(self) -> None:
        self._event.clear()


@dataclass
class KernelTelemetry:
    """Operating system telemetry snapshot for thrashing detection."""

    wall_time_s: float = 0.0
    involuntary_cs: int = 0
    voluntary_cs: int = 0
    max_rss_mb: float = 0.0

    def is_thrashing(self, threshold: int = 2132) -> bool:
        """Mac OS ARM64 empirical threshold for involuntary context switches."""
        return self.involuntary_cs > threshold

    def to_dict(self) -> Dict[str, Any]:
        return {
            "wall_time_s": round(self.wall_time_s, 3),
            "involuntary_cs": self.involuntary_cs,
            "voluntary_cs": self.voluntary_cs,
            "max_rss_mb": round(self.max_rss_mb, 2),
            "thrashing_detected": self.is_thrashing(),
        }


def capture_kernel_snapshot() -> Tuple[resource.struct_rusage, resource.struct_rusage]:
    """Captures rusage for self and children."""
    u_self = resource.getrusage(resource.RUSAGE_SELF)
    u_child = resource.getrusage(resource.RUSAGE_CHILDREN)
    return u_self, u_child


def compute_telemetry(
    t0: float,
    t1: float,
    before: Tuple[resource.struct_rusage, resource.struct_rusage],
    after: Tuple[resource.struct_rusage, resource.struct_rusage],
) -> KernelTelemetry:
    """Computes telemetry delta between snapshots."""
    (s0, c0) = before
    (s1, c1) = after
    return KernelTelemetry(
        wall_time_s=t1 - t0,
        involuntary_cs=(s1.ru_nivcsw - s0.ru_nivcsw) + (c1.ru_nivcsw - c0.ru_nivcsw),
        voluntary_cs=(s1.ru_nvcsw - s0.ru_nvcsw) + (c1.ru_nvcsw - c0.ru_nvcsw),
        max_rss_mb=max(s1.ru_maxrss, c1.ru_maxrss) / (1024 * 1024),
    )


class RobustLLMClient:
    """Resilient HTTP client for LLMs with circuit breaker, retry logic, and Flash/Mini capacity floor gate."""

    _SOVEREIGN_FALLBACK_FLOOR: Tuple[str, ...] = (
        "deepseek/deepseek-r1",
        "qwen/qwen-2.5-72b-instruct",
        "meta-llama/llama-3.3-70b-instruct",
    )

    def __init__(self, config: SwarmConfig):
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

    def _is_strict_floor_required(self, messages: List[Dict[str, str]]) -> bool:
        if self.config.strict_model_floor:
            return True
        from ..clients.openrouter import SensitivePathGuard

        combined = "\n".join(str(m.get("content", "")) for m in messages)
        return SensitivePathGuard.requires_strict_model_floor(prompt=combined)

    def build_request_payload(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Builds the outbound LLM request payload, enforcing ModelFloorGuard (`allow_fallbacks: False`
        and purging `mini`/`flash`/`small`/`xs`/`:free` models) when `strict_model_floor` or
        LegalTech/Ring-0 content is active.
        """
        from ..clients.openrouter import ModelFloorGuard

        enforce_floor = self._is_strict_floor_required(messages)
        target_model = self.config.model_name

        use_native_gateway_fallback = self.config.backend == InferenceBackend.OPENROUTER_REMOTE and bool(
            self.config.openrouter_fallback_models
        )

        if enforce_floor:
            if self.config.backend == InferenceBackend.OPENROUTER_REMOTE:
                filtered_fallbacks = ModelFloorGuard.filter_allowed_models(self.config.openrouter_fallback_models)
                if not filtered_fallbacks:
                    filtered_fallbacks = list(self._SOVEREIGN_FALLBACK_FLOOR)
                if ModelFloorGuard.is_sub_threshold(target_model):
                    # If user explicitly set a non-default sub-threshold model (e.g., gemini-2.5-flash or gpt-4o-mini), veto it
                    if target_model != "thinkingmachines/inkling:free":
                        ModelFloorGuard.assert_model_allowed(target_model, context="swarm_strict_model_floor")
                    target_model = filtered_fallbacks[0]
            else:
                ModelFloorGuard.assert_model_allowed(target_model, context="swarm_strict_model_floor")
        else:
            filtered_fallbacks = list(self.config.openrouter_fallback_models)

        payload: Dict[str, Any] = {
            "model": target_model,
            "messages": messages,
            "temperature": self.config.temperature,
        }
        if use_native_gateway_fallback:
            payload["models"] = filtered_fallbacks
            allow_fb = bool(self.config.allow_provider_fallbacks and not enforce_floor)
            provider_cfg: Dict[str, Any] = {
                "allow_fallbacks": allow_fb,
                "sort": "throughput",
            }
            if enforce_floor:
                provider_cfg["data_collection"] = "deny"
            payload["provider"] = provider_cfg
        elif enforce_floor and self.config.backend == InferenceBackend.OPENROUTER_REMOTE:
            payload["provider"] = {
                "allow_fallbacks": False,
                "data_collection": "deny",
            }

        return payload

    async def call(self, messages: List[Dict[str, str]]) -> str:
        if self.is_circuit_breaker_tripped:
            return f"Circuit breaker open: {self._consecutive_failures} failures. Backend: {self.config.backend.value}"

        from ..clients.openrouter import ModelFloorGuard, SubThresholdModelVetoError

        enforce_floor = self._is_strict_floor_required(messages)
        try:
            payload = self.build_request_payload(messages)
        except SubThresholdModelVetoError as veto_err:
            self._consecutive_failures += 1
            return str(veto_err)

        # If air-gapped / unconfigured, return deterministic mock output in tests
        if not self.config.api_key and self.config.backend in (
            InferenceBackend.MOONSHOT_REMOTE,
            InferenceBackend.OPENROUTER_REMOTE,
        ):
            return "[AIR-GAP MOCK] Deterministic response for swarm execution"

        import urllib.request
        import urllib.error

        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        use_native_gateway_fallback = "models" in payload
        data_bytes = json.dumps(payload).encode("utf-8")
        # When OpenRouter gateway native `models` fallback is active, avoid multiplying RPD consumption
        effective_retries = 1 if use_native_gateway_fallback else self.config.max_retries

        for attempt in range(1, effective_retries + 1):
            try:
                req = urllib.request.Request(self.config.api_url, data=data_bytes, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=self.config.request_timeout_s) as resp:
                    res = json.loads(resp.read().decode("utf-8"))
                    resolved_model = str(res.get("model", payload["model"]))
                    if enforce_floor and ModelFloorGuard.is_sub_threshold(resolved_model):
                        self._consecutive_failures += 1
                        return (
                            f"SUB_THRESHOLD_MODEL_VETO [swarm_postflight]: Gateway silently downgraded "
                            f"from '{payload['model']}' to sub-threshold model '{resolved_model}'."
                        )
                    self._consecutive_failures = 0
                    return str(res["choices"][0]["message"]["content"])
            except urllib.error.HTTPError as e:
                err_text = e.read().decode("utf-8") if e.fp else str(e)
                if e.code == 429 and attempt < effective_retries:
                    delay = self.config.retry_base_delay_s * (2 ** (attempt - 1))
                    await asyncio.sleep(delay)
                    continue
                self._consecutive_failures += 1
                return f"HTTP {e.code}: {err_text[:200]}"
            except Exception as e:
                self._consecutive_failures += 1
                if attempt >= effective_retries:
                    return f"Connection error: {e}"
                delay = self.config.retry_base_delay_s * (2 ** (attempt - 1))
                await asyncio.sleep(delay)

        return "Error: Max retries exhausted."


class SwarmOrchestrator:
    """Central Swarm Execution Engine for 02_EDIN_SWARMS (edin.swarms)."""

    def __init__(self, config: Optional[SwarmConfig] = None):
        self.config = config or SwarmConfig()
        self.client = RobustLLMClient(self.config)
        self.pager = AgentPager()

    async def execute_dag(
        self,
        tasks: List[str],
        on_progress: Optional[Callable[[int, str, float], None]] = None,
    ) -> Dict[str, Any]:
        """
        Executes a collection of parallel tasks across the swarm with PxS concurrency bounds.
        """
        semaphore = asyncio.Semaphore(self.config.max_concurrent)
        self.pager.beep()  # Awaken waiting nodes

        t0 = time.perf_counter()
        snap_before = capture_kernel_snapshot()

        async def _run_single(task_id: int, desc: str) -> Dict[str, Any]:
            await self.pager.wait_for_beep()
            async with semaphore:
                if self.config.mcts_delay_s > 0:
                    await asyncio.sleep(self.config.mcts_delay_s)
                sub_t0 = time.perf_counter()
                messages = [
                    {
                        "role": "system",
                        "content": "You are a specialized swarm subagent. Provide direct, concise results.",
                    },
                    {"role": "user", "content": desc},
                ]
                output = await self.client.call(messages)
                elapsed = time.perf_counter() - sub_t0
                status = "ERROR" if output.startswith("Error") or output.startswith("Circuit breaker") else "OK"
                if on_progress:
                    on_progress(task_id, status, elapsed)
                return {
                    "task_id": task_id,
                    "desc": desc,
                    "status": status,
                    "result": output,
                    "elapsed_s": round(elapsed, 3),
                }

        task_coros = [_run_single(i, t) for i, t in enumerate(tasks)]
        results = await asyncio.gather(*task_coros)

        t1 = time.perf_counter()
        snap_after = capture_kernel_snapshot()
        telemetry = compute_telemetry(t0, t1, snap_before, snap_after)

        return {
            "total_tasks": len(tasks),
            "concurrency_limit": self.config.max_concurrent,
            "results": results,
            "telemetry": telemetry.to_dict(),
        }
