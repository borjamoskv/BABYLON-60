#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ SWARM ORCHESTRATOR CORE | DOMAIN: 02_EDIN_SWARMS (edin.swarms) | STATE: C5-REAL
# ============================================================================
"""
Sovereign Swarm Orchestration Engine — 02_EDIN_SWARMS (edin.swarms) (C5-REAL v4.0).

Core features:
  - Multi-Backend Inference: local vLLM (default) / Apple Silicon MLX / OpenRouter
  - macOS ARM64 Kernel Telemetry (ru_nivcsw, ru_nvcsw, RSS)
  - Zero-Friction Interruption via AgentPager (O(1) futex wait)
  - Circuit Breaker & Exponential Backoff
  - PxS Topological Scaling (Pareto Zero-Thrashing on Apple Silicon)
"""

import asyncio
import httpx
import logging
import os
import random
import resource
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, List, Dict, Any, Optional, Tuple

logger = logging.getLogger("02_EDIN_SWARMS.orchestrator.swarm")
"""Primary execution logger for 02_EDIN_SWARMS (edin.swarms)."""


class InferenceBackend(Enum):
    """Supported inference execution backends."""

    OPENROUTER_REMOTE = "openrouter"
    LOCAL_VLLM = "local_vllm"
    LOCAL_MLX = "local_mlx"


def _get_default_openrouter_url() -> str:
    return os.getenv("OPENROUTER_API_URL") or "https://openrouter.ai/api/v1/chat/completions"


def _get_default_openrouter_key() -> str:
    return os.getenv("OPENROUTER_API_KEY", "")


@dataclass
class SwarmConfig:
    """Deterministic configuration for Swarm execution."""

    p_cores: int = 4
    s_threads: int = 1
    # Local by default: an unconfigured swarm never resolves a remote
    # credential nor sends anything off loopback.
    backend: InferenceBackend = InferenceBackend.LOCAL_VLLM

    # Endpoints
    openrouter_url: str = field(default_factory=_get_default_openrouter_url)
    # None defers the OPENROUTER_API_KEY lookup until that backend is selected.
    openrouter_key: Optional[str] = field(default=None, repr=False)
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
    circuit_breaker_cooldown_s: float = 30.0
    delegate_circuit_breaker: bool = False  # INV_C5_CB_SUBORDINATION: Delega el CB a Ring-0 / Gateway
    strict_model_floor: bool = False  # Veto Flash/Mini/Small/XS/:free & force allow_fallbacks=False
    allow_provider_fallbacks: bool = True

    @property
    def max_concurrent(self) -> int:
        return max(1, self.p_cores * self.s_threads)

    @property
    def api_url(self) -> str:
        if self.backend == InferenceBackend.OPENROUTER_REMOTE:
            return self.openrouter_url
        return self.local_url

    @property
    def api_key(self) -> str:
        if self.backend == InferenceBackend.OPENROUTER_REMOTE:
            if self.openrouter_key is not None:
                return self.openrouter_key
            return _get_default_openrouter_key()
        return ""

    @property
    def model_name(self) -> str:
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

    @property
    def involuntary_cs_per_sec(self) -> float:
        """Rate of involuntary context switches per second (S4)."""
        if self.wall_time_s > 0:
            return self.involuntary_cs / self.wall_time_s
        return float(self.involuntary_cs)

    def is_thrashing(self, threshold: int = 2132, rate_threshold_per_s: float = 1500.0) -> bool:
        """Rate-based thrashing check (cs/s) when wall_time_s > 0; falls back to absolute threshold otherwise."""
        if self.wall_time_s > 0:
            return self.involuntary_cs_per_sec > rate_threshold_per_s
        return self.involuntary_cs > threshold

    def to_dict(self) -> Dict[str, Any]:
        return {
            "wall_time_s": round(self.wall_time_s, 3),
            "involuntary_cs": self.involuntary_cs,
            "involuntary_cs_per_sec": round(self.involuntary_cs_per_sec, 2),
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


class LLMCallError(str):
    """Typed failure preserving the public textual response contract."""


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
        self._cb_tripped_at: Optional[float] = None

    def reset_circuit_breaker(self) -> None:
        """Resetea el contador de fallos consecutivos en Python."""
        self._consecutive_failures = 0
        self._cb_tripped_at = None

    def _record_failure(self) -> None:
        self._consecutive_failures += 1
        if self._consecutive_failures >= self.config.circuit_breaker_threshold:
            self._cb_tripped_at = time.monotonic()

    @property
    def is_circuit_breaker_tripped(self) -> bool:
        """Indica si el circuit breaker local está abierto (con soporte half-open por cooldown, S2)."""
        if self.config.delegate_circuit_breaker:
            return False
        if self._consecutive_failures < self.config.circuit_breaker_threshold:
            return False
        if self._cb_tripped_at is not None and self.config.circuit_breaker_cooldown_s > 0:
            if (time.monotonic() - self._cb_tripped_at) >= self.config.circuit_breaker_cooldown_s:
                return False  # Half-open probe permitted
        return True

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

    def _backoff_delay(self, attempt: int) -> float:
        """Exponential backoff with equal jitter to prevent thundering herd (S2)."""
        base: float = self.config.retry_base_delay_s * float(2 ** (attempt - 1))
        if base <= 0:
            return 0.0
        return base * (0.5 + 0.5 * random.random())

    async def call(
        self,
        messages: List[Dict[str, str]],
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> str:
        if self.is_circuit_breaker_tripped:
            return LLMCallError(
                f"Circuit breaker open: {self._consecutive_failures} failures. Backend: {self.config.backend.value}"
            )

        from ..clients.openrouter import ModelFloorGuard, SubThresholdModelVetoError

        enforce_floor = self._is_strict_floor_required(messages)
        try:
            payload = self.build_request_payload(messages)
        except SubThresholdModelVetoError as veto_err:
            self._record_failure()
            return LLMCallError(str(veto_err))

        api_key = self.config.api_key
        if self.config.backend == InferenceBackend.OPENROUTER_REMOTE and not api_key.strip():
            self._record_failure()
            return LLMCallError("OpenRouter credentials unavailable: configure openrouter_key or OPENROUTER_API_KEY")

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        use_native_gateway_fallback = "models" in payload
        # When OpenRouter gateway native `models` fallback is active, avoid multiplying RPD consumption
        effective_retries = 1 if use_native_gateway_fallback else self.config.max_retries

        async def _execute_attempts(client: httpx.AsyncClient) -> str:
            for attempt in range(1, effective_retries + 1):
                try:
                    # Bound the whole attempt, including response streaming.
                    response = await asyncio.wait_for(
                        client.post(self.config.api_url, json=payload, headers=headers),
                        timeout=self.config.request_timeout_s,
                    )
                    response.raise_for_status()
                    res = response.json()
                    resolved_model = str(res.get("model", payload["model"]))
                    if enforce_floor and ModelFloorGuard.is_sub_threshold(resolved_model):
                        self._record_failure()
                        return LLMCallError(
                            f"SUB_THRESHOLD_MODEL_VETO [swarm_postflight]: Gateway silently downgraded "
                            f"from '{payload['model']}' to sub-threshold model '{resolved_model}'."
                        )
                    content = str(res["choices"][0]["message"]["content"])
                    self.reset_circuit_breaker()
                    return content
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429 and attempt < effective_retries:
                        await asyncio.sleep(self._backoff_delay(attempt))
                        continue
                    self._record_failure()
                    return LLMCallError(f"HTTP {e.response.status_code}: {e.response.text[:200]}")
                except Exception as e:
                    self._record_failure()
                    if attempt >= effective_retries:
                        return LLMCallError(f"Connection error: {e}")
                    await asyncio.sleep(self._backoff_delay(attempt))

            return LLMCallError("Error: Max retries exhausted.")

        if http_client is not None:
            return await _execute_attempts(http_client)

        # S1: Reuse a single AsyncClient across all retry attempts when no shared pool is passed
        async with httpx.AsyncClient(timeout=self.config.request_timeout_s) as owned_client:
            return await _execute_attempts(owned_client)


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
        Executes a collection of parallel tasks across the swarm with PxS concurrency bounds,
        a shared HTTP connection pool (S1), and bounded worker pool backpressure (S3).
        """
        self.pager.beep()  # Awaken waiting nodes

        t0 = time.perf_counter()
        snap_before = capture_kernel_snapshot()

        total = len(tasks)
        results: List[Dict[str, Any]] = [{} for _ in range(total)]
        next_idx = 0

        async def _run_task(task_id: int, desc: str, shared_client: Optional[httpx.AsyncClient]) -> Dict[str, Any]:
            await self.pager.wait_for_beep()
            sub_t0 = time.perf_counter()
            messages = [
                {
                    "role": "system",
                    "content": "You are a specialized swarm subagent. Provide direct, concise results.",
                },
                {"role": "user", "content": desc},
            ]
            output = await self.client.call(messages, http_client=shared_client)
            elapsed = time.perf_counter() - sub_t0
            status = "ERROR" if isinstance(output, LLMCallError) else "OK"
            if on_progress:
                on_progress(task_id, status, elapsed)
            return {
                "task_id": task_id,
                "desc": desc,
                "status": status,
                "result": output,
                "elapsed_s": round(elapsed, 3),
            }

        async def _worker_loop(shared_client: Optional[httpx.AsyncClient]) -> None:
            nonlocal next_idx
            while next_idx < total:
                idx = next_idx
                next_idx += 1
                # S3: Delay happens per-worker outside any shared semaphore contention
                if self.config.mcts_delay_s > 0:
                    await asyncio.sleep(self.config.mcts_delay_s)
                results[idx] = await _run_task(idx, tasks[idx], shared_client)

        pool_size = min(self.config.max_concurrent, total)
        if pool_size > 0:
            # S1: Share one pooled AsyncClient across all workers only when dispatch is permitted
            can_open_http = not self.client.is_circuit_breaker_tripped and (
                self.config.backend != InferenceBackend.OPENROUTER_REMOTE or bool(self.config.api_key.strip())
            )
            if not can_open_http:
                await asyncio.gather(*(_worker_loop(None) for _ in range(pool_size)))
            else:
                async with httpx.AsyncClient(timeout=self.config.request_timeout_s) as shared_client:
                    await asyncio.gather(*(_worker_loop(shared_client) for _ in range(pool_size)))

        t1 = time.perf_counter()
        snap_after = capture_kernel_snapshot()
        telemetry = compute_telemetry(t0, t1, snap_before, snap_after)

        return {
            "total_tasks": total,
            "concurrency_limit": self.config.max_concurrent,
            "results": results,
            "telemetry": telemetry.to_dict(),
        }
