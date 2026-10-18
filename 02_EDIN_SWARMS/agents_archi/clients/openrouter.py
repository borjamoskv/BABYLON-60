#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ OPENROUTER GATEWAY CLIENT | DOMAIN: agents.archi | STATE: C5-REAL
# ============================================================================
"""
Unified OpenRouter Gateway Client for hybrid model routing.
"""

from dataclasses import dataclass
from datetime import date
from enum import Enum
import ipaddress
import json
import logging
import os
import re
import threading
import time
import urllib.parse
import urllib.request
import urllib.error
from typing import Any, Callable, Dict, List, Optional, Sequence

logger = logging.getLogger("agents_archi.clients.openrouter")

# [FRENTE-046] SSRF Allowlist: Only these hostnames may receive HTTP requests from this client.
# Blocks RFC-1918 private IPs, IMDS (169.254.169.254), and all non-explicit domains.
_SSRF_ALLOWED_HOSTS: frozenset[str] = frozenset(
    {
        "openrouter.ai",
        "api.openrouter.ai",
    }
)

# RFC-1918 + link-local ranges — connection to these is VETO'd regardless of hostname.
_BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),  # AWS/GCP IMDS
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]

# Poolside Laguna S/XS 2.1 :free sunset boundary (2026-10-31 inclusive is free; 2026-11-01+ is paid-only)
POOLSIDE_FREE_SUNSET_DATE: date = date(2026, 10, 31)


class OpenRouterRoleTier(str, Enum):
    """Canonical ROYAL-RUMBLE v2 agentic execution tiers."""

    PLANNER = "planner"
    CODER_ACT = "coder_act"
    STRUCTURED_REVIEW = "structured_review"
    SUBAGENT_FAST = "subagent_fast"
    SENSITIVE_SOVEREIGN = "sensitive_sovereign"


# Models that do NOT support `tool_choice` or `structured_outputs` in OpenRouter's live catalog
_NO_TOOL_CHOICE_OR_SCHEMA_MODELS: frozenset[str] = frozenset(
    {
        "thinkingmachines/inkling:free",
        "thinkingmachines/inkling-small:free",
    }
)

# Sensitive path / content markers that MUST NOT be sent to telemetry-collecting :free endpoints
_SENSITIVE_PATH_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(^|/)src/", re.IGNORECASE),
    re.compile(r"(^|/)proof/", re.IGNORECASE),
    re.compile(r"\.(rs|lean|pem|key|der)$", re.IGNORECASE),
    re.compile(r"ring[-_]?0|kudurru|seqlock|sharedmanifest|cortex[-_]?taint", re.IGNORECASE),
)

_SENSITIVE_CONTENT_MARKERS: tuple[str, ...] = (
    "SharedManifest",
    "KUDURRU-64",
    "POISONED = 0xDEAD_6060",
    "kSecAttrTokenIDSecureEnclave",
    "CORTEX-TAINT",
    "#[repr(C, align(64))]",
)

# LegalTech / Regulatory / Compliance markers requiring strict model capacity floor (no Flash/Mini/Free fallbacks)
_LEGALTECH_PATH_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"legal|compliance|juris|contract|eu[-_]?ai[-_]?act|eidas|gdpr|rgpd", re.IGNORECASE),
)

_LEGALTECH_CONTENT_MARKERS: tuple[str, ...] = (
    "eu ai act",
    "reglamento (ue) 2024/1689",
    "dictamen jurídico",
    "dictamen legal",
    "cláusula",
    "responsabilidad civil",
    "responsabilidad penal",
    "compliance_exporter",
    "eidas",
    "rgpd",
    "gdpr",
    "legaltech",
)

# Canonical regex for sub-threshold models forbidden in LegalTech and Ring-0 sovereign execution
_SUB_THRESHOLD_MODEL_RE: re.Pattern[str] = re.compile(
    r"(?:^|[-_/:.])(flash|mini|small|xs|nano|lite|lightning|haiku|1\.7b|3b|7b|8b)(?:$|[-_/:.])"
    r"|:free$|^openrouter/(?:free|auto)$",
    re.IGNORECASE,
)


class SubThresholdModelVetoError(RuntimeError):
    """Raised when a Flash, Mini, Small, XS, Lightning, or :free model is requested or served in a strict domain."""


class ModelFloorGuard:
    """
    Deterministic capacity-floor gate (INV_C5_FLASH_DEFENSE / LegalTech Flash-Mini Veto).
    Blocks explicit and silent fallback downgrades to sub-threshold models (`flash`, `mini`, `small`, `xs`, `lightning`, `:free`, `1.7b`).
    """

    @classmethod
    def is_sub_threshold(cls, model_id: str) -> bool:
        norm = model_id.strip()
        if not norm:
            return True
        return bool(_SUB_THRESHOLD_MODEL_RE.search(norm))

    @classmethod
    def assert_model_allowed(cls, model_id: str, context: str = "strict_model_floor") -> None:
        if cls.is_sub_threshold(model_id):
            raise SubThresholdModelVetoError(
                f"SUB_THRESHOLD_MODEL_VETO [{context}]: Model '{model_id}' violates the sovereign capacity floor "
                "(Flash/Mini/Small/XS/Lightning/:free forbidden)."
            )

    @classmethod
    def filter_allowed_models(cls, models: Sequence[str]) -> List[str]:
        return [m for m in models if not cls.is_sub_threshold(m)]


def _assert_ssrf_safe(url: str, allowed_hosts: frozenset[str] = _SSRF_ALLOWED_HOSTS) -> None:
    """
    [FRENTE-046] Validate URL against SSRF allowlist before issuing HTTP request.
    Raises ValueError if the host is not explicitly permitted or resolves to a private IP range.
    """
    parsed = urllib.parse.urlparse(url)
    host = parsed.hostname or ""
    if not host:
        raise ValueError(f"[SSRF-GATE] Empty hostname in URL: {url}")
    if host not in allowed_hosts:
        raise ValueError(f"[SSRF-GATE] Host '{host}' not in SSRF allowlist. Request blocked.")
    # Additional check: if the host looks like a raw IP address, verify it's not private.
    try:
        addr = ipaddress.ip_address(host)
        for network in _BLOCKED_IP_NETWORKS:
            if addr in network:
                raise ValueError(f"[SSRF-GATE] IP address '{host}' is in blocked private range {network}.")
    except ValueError as e:
        if "[SSRF-GATE]" in str(e):
            raise
        # Not a raw IP — hostname-based check already passed above.


class SensitivePathGuard:
    """
    Zero-Trust IP & LegalTech Guardrail for BABYLON-60 / CORTEX.
    Prevents sending Ring-0 Rust kernel code, Lean 4 formal proofs, private CORTEX memory,
    or high-liability LegalTech workloads to :free or sub-threshold endpoints.
    """

    @classmethod
    def is_sensitive(
        cls,
        prompt: str = "",
        system_prompt: Optional[str] = None,
        context_paths: Optional[Sequence[str]] = None,
    ) -> bool:
        if context_paths:
            for path in context_paths:
                for pat in _SENSITIVE_PATH_PATTERNS:
                    if pat.search(path):
                        return True
        combined = f"{system_prompt or ''}\n{prompt}"
        for marker in _SENSITIVE_CONTENT_MARKERS:
            if marker in combined:
                return True
        return False

    @classmethod
    def is_legaltech(
        cls,
        prompt: str = "",
        system_prompt: Optional[str] = None,
        context_paths: Optional[Sequence[str]] = None,
    ) -> bool:
        if context_paths:
            for path in context_paths:
                for pat in _LEGALTECH_PATH_PATTERNS:
                    if pat.search(path):
                        return True
        combined = f"{system_prompt or ''}\n{prompt}".lower()
        for marker in _LEGALTECH_CONTENT_MARKERS:
            if marker in combined:
                return True
        return False

    @classmethod
    def requires_strict_model_floor(
        cls,
        prompt: str = "",
        system_prompt: Optional[str] = None,
        context_paths: Optional[Sequence[str]] = None,
    ) -> bool:
        return cls.is_sensitive(prompt, system_prompt, context_paths) or cls.is_legaltech(
            prompt, system_prompt, context_paths
        )

    @classmethod
    def is_free_model(cls, model_id: str) -> bool:
        norm = model_id.strip().lower()
        return norm.endswith(":free") or norm == "openrouter/free"


@dataclass
class QuotaBudgetTracker:
    """
    ROYAL-RUMBLE v2 Daily Quota Partitioner (80% WORK / 20% RECOVERY).
    OpenRouter counts both successful and failed requests against the daily RPD limit
    (50 RPD without credits, or 1,000 RPD with >= $10 credits).
    """

    daily_limit: int = 1000
    work_ratio: float = 0.80
    work_used: int = 0
    recovery_used: int = 0

    @property
    def work_budget(self) -> int:
        return int(self.daily_limit * self.work_ratio)

    @property
    def recovery_budget(self) -> int:
        return self.daily_limit - self.work_budget

    @property
    def total_used(self) -> int:
        return self.work_used + self.recovery_used

    def can_spend(self, phase: str = "work") -> bool:
        if self.total_used >= self.daily_limit:
            return False
        if phase == "recovery":
            return self.recovery_used < self.recovery_budget or self.work_used < self.work_budget
        return self.work_used < self.work_budget

    def record_attempt(self, phase: str = "work") -> None:
        """Records an upstream attempt (even if it fails with 429/503, as OpenRouter bills RPD)."""
        if phase == "recovery":
            self.recovery_used += 1
        else:
            self.work_used += 1


class TokenBucketRateLimiter:
    """
    Local Token Bucket rate limiter to keep multi-agent swarms below OpenRouter's 20 RPM :free ceiling.
    Defaults to 15 RPM (1 request every 4.0 seconds) with burst capacity.
    """

    def __init__(
        self,
        rpm: float = 15.0,
        burst: int = 3,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if rpm <= 0:
            raise ValueError("rpm must be positive")
        self.rpm = rpm
        self.rate_per_sec = rpm / 60.0
        self.capacity = float(max(1, burst))
        self.tokens = float(max(1, burst))
        self._clock = clock
        self._last_refill = self._clock()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = self._clock()
        elapsed = max(0.0, now - self._last_refill)
        self._last_refill = now
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate_per_sec)

    def acquire_wait_seconds(self) -> float:
        """
        Consumes 1 token if available (returns 0.0), or returns the required wait time in seconds
        while reserving the slot deterministically.
        """
        with self._lock:
            self._refill()
            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return 0.0
            deficit = 1.0 - self.tokens
            wait_s = deficit / self.rate_per_sec
            self.tokens = 0.0
            self._last_refill = self._clock() + wait_s
            return wait_s


class OpenRouterClient:
    """Unified OpenRouter API Gateway for frontier & ROYAL-RUMBLE v2 free inference."""

    BASE_URL = "https://openrouter.ai/api/v1"

    DEFAULT_FALLBACK_MODELS = [
        "thinkingmachines/inkling:free",
        "poolside/laguna-s-2.1:free",
        "cohere/north-mini-code:free",
        "nvidia/nemotron-3-super-120b-a12b:free",
    ]

    FREE_EMBEDDING_MODELS = [
        "nvidia/nemotron-3-embed-1b:free",
        "nvidia/llama-nemotron-embed-vl-1b-v2:free",
        "liquid/lfm-2.5-embedding-350m:free",
    ]

    LOCAL_LMSTUDIO_BASE_URL = os.getenv("BABYLON_LOCAL_BASE_URL", "http://127.0.0.1:1234/v1")
    LOCAL_OLLAMA_BASE_URL = os.getenv("BABYLON_LOCAL_OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1")
    DEFAULT_LOCAL_CHAT_MODEL = os.getenv("BABYLON_LOCAL_LLM_MODEL", "deepseek-r1-distill-qwen-32b")
    DEFAULT_LOCAL_FAST_MODEL = os.getenv("BABYLON_LOCAL_OLLAMA_MODEL", "qwen3:1.7b")
    DEFAULT_LOCAL_EMBED_MODEL = os.getenv("BABYLON_LOCAL_EMBED_MODEL", "bge-m3-legal-embed")

    def __init__(
        self,
        api_key: Optional[str] = None,
        primary_model: str = "openrouter/auto",
        daily_rpd_limit: int = 1000,
        rpm_limit: float = 15.0,
        enforce_sensitive_guard: bool = True,
        enable_local_failover: bool = False,
        local_base_url: Optional[str] = None,
        local_chat_model: Optional[str] = None,
        local_embed_model: Optional[str] = None,
    ) -> None:
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = os.environ.get("OPENROUTER_API_KEY") or ""
        self.primary_model = primary_model
        self.enforce_sensitive_guard = enforce_sensitive_guard
        self.enable_local_failover = enable_local_failover
        self.local_base_url = (local_base_url or self.LOCAL_LMSTUDIO_BASE_URL).rstrip("/")
        self.local_chat_model = local_chat_model or self.DEFAULT_LOCAL_CHAT_MODEL
        self.local_embed_model = local_embed_model or self.DEFAULT_LOCAL_EMBED_MODEL
        self.quota = QuotaBudgetTracker(daily_limit=daily_rpd_limit)
        self.rate_limiter = TokenBucketRateLimiter(rpm=rpm_limit)

    def is_configured(self) -> bool:
        return bool(self.api_key)

    @staticmethod
    def _assert_local_loopback_safe(url: str) -> None:
        parsed = urllib.parse.urlparse(url)
        host = (parsed.hostname or "").lower()
        if host not in ("127.0.0.1", "localhost", "::1"):
            raise ValueError(f"[LOCAL-LOOPBACK-GATE] Non-loopback host '{host}' forbidden for local inference.")

    def query_local(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.2,
        fallback_reason: str = "direct_local",
        strict_model_floor: bool = False,
    ) -> Dict[str, Any]:
        """
        Executes chat completion against local Apple Silicon M3 Pro inference:
        1. Primary: LM Studio (`127.0.0.1:1234/v1/chat/completions`, `deepseek-r1-distill-qwen-32b`)
        2. Secondary: Ollama (`127.0.0.1:11434/v1/chat/completions`, `qwen3:1.7b`) — VETOED when `strict_model_floor=True`.
        """
        if strict_model_floor and model is not None and ModelFloorGuard.is_sub_threshold(model):
            return {
                "success": False,
                "error": f"SUB_THRESHOLD_MODEL_VETO [query_local]: Model '{model}' violates sovereign capacity floor.",
                "route_override": "local_mlx",
                "veto_triggered": True,
            }

        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        primary_local_model = model or self.local_chat_model
        endpoints = [
            (f"{self.local_base_url}/chat/completions", primary_local_model, "lmstudio_1234"),
        ]
        if not strict_model_floor and not ModelFloorGuard.is_sub_threshold(self.DEFAULT_LOCAL_FAST_MODEL):
            endpoints.append(
                (
                    f"{self.LOCAL_OLLAMA_BASE_URL.rstrip('/')}/chat/completions",
                    self.DEFAULT_LOCAL_FAST_MODEL,
                    "ollama_11434",
                )
            )
        elif not strict_model_floor:
            endpoints.append(
                (
                    f"{self.LOCAL_OLLAMA_BASE_URL.rstrip('/')}/chat/completions",
                    self.DEFAULT_LOCAL_FAST_MODEL,
                    "ollama_11434",
                )
            )

        last_err = "No local endpoints reachable"
        for url, target_model, provider_tag in endpoints:
            if strict_model_floor and ModelFloorGuard.is_sub_threshold(target_model):
                last_err = f"{provider_tag}: SUB_THRESHOLD_MODEL_VETO ({target_model})"
                continue
            try:
                self._assert_local_loopback_safe(url)
                payload = {
                    "model": target_model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                }
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=45.0) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                    resolved_local = str(result.get("model", target_model))
                    if strict_model_floor and ModelFloorGuard.is_sub_threshold(resolved_local):
                        return {
                            "success": False,
                            "error": (
                                f"SUB_THRESHOLD_MODEL_VETO [query_local_postflight]: Local endpoint '{provider_tag}' "
                                f"served sub-threshold model '{resolved_local}'."
                            ),
                            "model": resolved_local,
                            "route_override": "local_mlx",
                            "veto_triggered": True,
                        }
                    content = result["choices"][0]["message"]["content"]
                    return {
                        "success": True,
                        "model": resolved_local,
                        "content": content,
                        "usage": result.get("usage", {}),
                        "route_override": "local_mlx",
                        "local_provider": provider_tag,
                        "fallback_reason": fallback_reason,
                    }
            except Exception as e:
                last_err = f"{provider_tag}: {e}"
                continue
        return {
            "success": False,
            "error": f"LOCAL_FAILOVER_UNAVAILABLE ({fallback_reason}): {last_err}",
            "route_override": "local_mlx",
        }

    @staticmethod
    def _compute_deterministic_blake3_embedding(text: str, dim: int = 64) -> List[float]:
        """
        Generates a deterministic unit-normalized embedding vector in R^dim using BLAKE3 XOF
        (or SHA-256 fallback) when the local HTTP server (`eridu-infer` / Ollama) does not expose `/v1/embeddings`.
        """
        import hashlib
        import math
        import struct

        try:
            import blake3

            raw = blake3.blake3(text.encode("utf-8")).digest(length=dim * 4)
        except Exception:
            chunks = [hashlib.sha256(f"{i}:{text}".encode("utf-8")).digest() for i in range((dim * 4 + 31) // 32)]
            raw = b"".join(chunks)[: dim * 4]

        vals = [((struct.unpack("<I", raw[i * 4 : (i + 1) * 4])[0] / 4294967295.0) * 2.0 - 1.0) for i in range(dim)]
        norm = math.sqrt(sum(v * v for v in vals)) or 1.0
        return [round(v / norm, 6) for v in vals]

    def embed_local(
        self,
        inputs: Sequence[str] | str,
        model: Optional[str] = None,
        fallback_reason: str = "direct_local",
    ) -> Dict[str, Any]:
        """
        Generates embeddings locally on Apple Silicon:
        1. Primary: HTTP `/v1/embeddings` on `127.0.0.1:1234` (`bge-m3-legal-embed`).
        2. Fallback: Deterministic BLAKE3 XOF unit-normalized vector in R^64 when `eridu-infer` is in chat-only mode.
        """
        texts: List[str] = [inputs] if isinstance(inputs, str) else list(inputs)
        url = f"{self.local_base_url}/embeddings"
        target_model = model or self.local_embed_model
        try:
            self._assert_local_loopback_safe(url)
            payload = {"model": target_model, "input": texts}
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                vectors = [item.get("embedding", []) for item in result.get("data", [])]
                return {
                    "success": True,
                    "model": result.get("model", target_model),
                    "embeddings": vectors,
                    "usage": result.get("usage", {}),
                    "route_override": "local_mlx",
                    "local_provider": "lmstudio_1234",
                    "fallback_reason": fallback_reason,
                }
        except Exception:
            vectors = [self._compute_deterministic_blake3_embedding(t, dim=64) for t in texts]
            return {
                "success": True,
                "model": f"{target_model}:blake3-64d",
                "embeddings": vectors,
                "usage": {
                    "prompt_tokens": sum(max(1, len(t) // 4) for t in texts),
                    "total_tokens": sum(max(1, len(t) // 4) for t in texts),
                },
                "route_override": "local_mlx",
                "local_provider": "blake3_deterministic_64d",
                "fallback_reason": fallback_reason,
            }

    @staticmethod
    def resolve_role_models(
        role: OpenRouterRoleTier,
        reference_date: Optional[date] = None,
    ) -> List[str]:
        """
        Returns the ordered native fallback `models` array for a given ROYAL-RUMBLE v2 role,
        automatically retiring `poolside/laguna-*:free` after 2026-10-31.
        """
        today = reference_date or date.today()
        poolside_active = today <= POOLSIDE_FREE_SUNSET_DATE

        if role == OpenRouterRoleTier.PLANNER:
            return [
                "thinkingmachines/inkling:free",
                "thinkingmachines/inkling-small:free",
                "nvidia/nemotron-3-super-120b-a12b:free",
            ]
        if role == OpenRouterRoleTier.CODER_ACT:
            if poolside_active:
                return [
                    "poolside/laguna-s-2.1:free",
                    "cohere/north-mini-code:free",
                    "poolside/laguna-xs-2.1:free",
                ]
            return [
                "cohere/north-mini-code:free",
                "nvidia/nemotron-3-super-120b-a12b:free",
                "thinkingmachines/inkling-small:free",
            ]
        if role == OpenRouterRoleTier.STRUCTURED_REVIEW:
            return [
                "nvidia/nemotron-3-super-120b-a12b:free",
                "nvidia/nemotron-3.5-super-vl:free",
                "google/gemma-4-31b-it:free",
            ]
        if role == OpenRouterRoleTier.SUBAGENT_FAST:
            if poolside_active:
                return [
                    "nvidia/nemotron-3.5-lightning:free",
                    "poolside/laguna-xs-2.1:free",
                    "cohere/north-mini-code:free",
                    "openrouter/free",
                ]
            return [
                "nvidia/nemotron-3.5-lightning:free",
                "cohere/north-mini-code:free",
                "openrouter/free",
            ]
        # SENSITIVE_SOVEREIGN: Paid/private endpoints with data_collection="deny"
        return [
            "deepseek/deepseek-r1",
            "qwen/qwen-2.5-72b-instruct",
            "meta-llama/llama-3.3-70b-instruct",
        ]

    def build_chat_payload(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        models: Optional[List[str]] = None,
        role: Optional[OpenRouterRoleTier] = None,
        max_tokens: int = 2048,
        temperature: float = 0.3,
        response_format: Optional[Dict[str, Any]] = None,
        tool_choice: Optional[Any] = None,
        reasoning_effort: Optional[str] = None,
        deny_data_collection: bool = False,
        reference_date: Optional[date] = None,
        strict_model_floor: bool = False,
    ) -> Dict[str, Any]:
        """
        Builds a sanitized OpenRouter chat completion payload with native `models` fallback array.
        Automatically upgrades role to STRUCTURED_REVIEW if `response_format` is requested on a
        model that lacks `structured_outputs` support (e.g., Inkling).
        When `strict_model_floor=True` or `role == SENSITIVE_SOVEREIGN`, purges all Flash/Mini/Small/:free
        models and enforces `allow_fallbacks=False` + `data_collection='deny'`.
        """
        enforce_floor = strict_model_floor or (role == OpenRouterRoleTier.SENSITIVE_SOVEREIGN)
        if enforce_floor and model is not None:
            ModelFloorGuard.assert_model_allowed(model, context="build_chat_payload")

        effective_role = role
        if enforce_floor and effective_role is None and not models:
            effective_role = OpenRouterRoleTier.SENSITIVE_SOVEREIGN
        elif response_format is not None and effective_role == OpenRouterRoleTier.PLANNER:
            effective_role = OpenRouterRoleTier.STRUCTURED_REVIEW

        candidate_models: List[str] = []
        if models:
            candidate_models = list(models)
        elif effective_role is not None:
            candidate_models = self.resolve_role_models(effective_role, reference_date=reference_date)

        if enforce_floor:
            candidate_models = ModelFloorGuard.filter_allowed_models(candidate_models)
            if not candidate_models:
                candidate_models = self.resolve_role_models(
                    OpenRouterRoleTier.SENSITIVE_SOVEREIGN, reference_date=reference_date
                )

        if response_format is not None and candidate_models:
            filtered = [m for m in candidate_models if m not in _NO_TOOL_CHOICE_OR_SCHEMA_MODELS]
            candidate_models = filtered or self.resolve_role_models(
                OpenRouterRoleTier.SENSITIVE_SOVEREIGN if enforce_floor else OpenRouterRoleTier.STRUCTURED_REVIEW,
                reference_date=reference_date,
            )

        if model:
            target_model = model
        elif candidate_models:
            target_model = candidate_models[0]
        elif enforce_floor:
            target_model = self.resolve_role_models(
                OpenRouterRoleTier.SENSITIVE_SOVEREIGN, reference_date=reference_date
            )[0]
        else:
            target_model = self.primary_model

        if enforce_floor:
            ModelFloorGuard.assert_model_allowed(target_model, context="build_chat_payload_target")

        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": target_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        effective_deny_collection = deny_data_collection or enforce_floor
        if candidate_models:
            payload["models"] = candidate_models
            provider_cfg: Dict[str, Any] = {
                "allow_fallbacks": not enforce_floor,
                "sort": "throughput",
            }
            if effective_deny_collection:
                provider_cfg["data_collection"] = "deny"
            payload["provider"] = provider_cfg
        elif effective_deny_collection:
            payload["provider"] = {
                "allow_fallbacks": not enforce_floor,
                "data_collection": "deny",
            }

        if response_format is not None and target_model not in _NO_TOOL_CHOICE_OR_SCHEMA_MODELS:
            payload["response_format"] = response_format

        if tool_choice is not None and target_model not in _NO_TOOL_CHOICE_OR_SCHEMA_MODELS:
            payload["tool_choice"] = tool_choice

        if reasoning_effort is not None:
            payload["reasoning"] = {"effort": reasoning_effort}

        return payload

    def query(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 2048,
        role: Optional[OpenRouterRoleTier] = None,
        models: Optional[List[str]] = None,
        context_paths: Optional[Sequence[str]] = None,
        phase: str = "work",
        response_format: Optional[Dict[str, Any]] = None,
        reference_date: Optional[date] = None,
        allow_local_failover: Optional[bool] = None,
        strict_model_floor: Optional[bool] = None,
    ) -> Dict[str, Any]:
        use_local_failover = self.enable_local_failover if allow_local_failover is None else allow_local_failover
        is_sensitive_ctx = self.enforce_sensitive_guard and SensitivePathGuard.is_sensitive(
            prompt=prompt,
            system_prompt=system_prompt,
            context_paths=context_paths,
        )
        is_legaltech_ctx = self.enforce_sensitive_guard and SensitivePathGuard.is_legaltech(
            prompt=prompt,
            system_prompt=system_prompt,
            context_paths=context_paths,
        )
        enforce_floor = bool(strict_model_floor) or is_legaltech_ctx or (role == OpenRouterRoleTier.SENSITIVE_SOVEREIGN)

        if not self.api_key:
            if use_local_failover:
                return self.query_local(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    model=model,
                    max_tokens=max_tokens,
                    fallback_reason="missing_openrouter_api_key",
                    strict_model_floor=enforce_floor or is_sensitive_ctx,
                )
            return {
                "success": False,
                "error": "Missing OPENROUTER_API_KEY environment variable.",
                "remediation": "Set OPENROUTER_API_KEY with a valid token or run in air-gapped local mode.",
            }

        try:
            payload = self.build_chat_payload(
                prompt=prompt,
                system_prompt=system_prompt,
                model=model,
                models=models,
                role=role,
                max_tokens=max_tokens,
                response_format=response_format,
                reference_date=reference_date,
                strict_model_floor=enforce_floor,
            )
        except SubThresholdModelVetoError as veto_err:
            return {
                "success": False,
                "error": str(veto_err),
                "veto_triggered": True,
            }

        target_model = str(payload["model"])
        candidate_list: List[str] = payload.get("models", [target_model])

        # 1. Sovereign IP Guardrail: never leak Ring-0 / Lean 4 / CORTEX code to :free endpoints
        if is_sensitive_ctx:
            if any(SensitivePathGuard.is_free_model(m) for m in candidate_list):
                if use_local_failover:
                    return self.query_local(
                        prompt=prompt,
                        system_prompt=system_prompt,
                        max_tokens=max_tokens,
                        fallback_reason="sovereign_ip_guard_tripped",
                        strict_model_floor=True,
                    )
                return {
                    "success": False,
                    "error": "SOVEREIGN_IP_GUARD_TRIPPED: Sensitive Ring-0/CORTEX content blocked on :free endpoints.",
                    "route_override": "local_mlx",
                    "remediation": "Route to local inference (LM Studio / MLX) or use SENSITIVE_SOVEREIGN tier with data_collection='deny'.",
                }

        # 2. Check 80/20 RPD Quota Partition (work vs recovery)
        if not self.quota.can_spend(phase=phase):
            if use_local_failover:
                return self.query_local(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    fallback_reason="quota_budget_exhausted",
                    strict_model_floor=enforce_floor or is_sensitive_ctx,
                )
            return {
                "success": False,
                "error": f"QUOTA_BUDGET_EXHAUSTED: Phase '{phase}' RPD limit reached (work={self.quota.work_used}/{self.quota.work_budget}, recovery={self.quota.recovery_used}/{self.quota.recovery_budget}).",
                "remediation": "Reserve remaining recovery budget for SQLite WAL checkpointing or switch to local model.",
            }

        # 3. Token Bucket Rate Limiter (<= 15 RPM)
        wait_s = self.rate_limiter.acquire_wait_seconds()
        if wait_s > 0.0:
            time.sleep(wait_s)

        url = f"{self.BASE_URL}/chat/completions"
        _assert_ssrf_safe(url)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/borjamoskv/BABYLON-60",
            "X-Title": "BABYLON-60 Sovereign Kernel",
        }

        # Record RPD attempt prior to network dispatch (OpenRouter bills failed upstream calls against RPD)
        self.quota.record_attempt(phase=phase)

        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=45.0) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                content = result["choices"][0]["message"]["content"]
                resolved_model = str(result.get("model", target_model))
                if (enforce_floor or is_sensitive_ctx) and ModelFloorGuard.is_sub_threshold(resolved_model):
                    return {
                        "success": False,
                        "error": (
                            f"SUB_THRESHOLD_MODEL_VETO [postflight]: Gateway silently downgraded execution "
                            f"from '{target_model}' to sub-threshold model '{resolved_model}'."
                        ),
                        "model": resolved_model,
                        "veto_triggered": True,
                    }
                return {
                    "success": True,
                    "model": resolved_model,
                    "content": content,
                    "usage": result.get("usage", {}),
                }
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8") if e.fp else str(e)
            logger.error("OpenRouter API error (%d): %s", e.code, err_body)
            if use_local_failover:
                return self.query_local(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    fallback_reason=f"openrouter_http_{e.code}",
                    strict_model_floor=enforce_floor or is_sensitive_ctx,
                )
            return {"success": False, "error": f"HTTP {e.code}: {err_body}"}
        except Exception as e:
            logger.error("OpenRouter unexpected error: %s", str(e))
            if use_local_failover:
                return self.query_local(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    fallback_reason="openrouter_network_error",
                    strict_model_floor=enforce_floor or is_sensitive_ctx,
                )
            return {"success": False, "error": str(e)}

    def embed(
        self,
        inputs: Sequence[str] | str,
        model: str = "nvidia/nemotron-3-embed-1b:free",
        context_paths: Optional[Sequence[str]] = None,
        phase: str = "work",
        allow_local_failover: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Generates embeddings via OpenRouter `/api/v1/embeddings` (`nvidia/nemotron-3-embed-1b:free`
        or multimodal `nvidia/llama-nemotron-embed-vl-1b-v2:free`) with Sovereign IP and RPD guards,
        plus optional automatic failover to local LM Studio (`bge-m3-legal-embed` on `127.0.0.1:1234`).
        """
        use_local_failover = self.enable_local_failover if allow_local_failover is None else allow_local_failover

        if not self.api_key:
            if use_local_failover:
                return self.embed_local(inputs=inputs, fallback_reason="missing_openrouter_api_key")
            return {
                "success": False,
                "error": "Missing OPENROUTER_API_KEY environment variable.",
                "remediation": "Set OPENROUTER_API_KEY with a valid token or run in air-gapped local mode.",
            }

        texts: List[str] = [inputs] if isinstance(inputs, str) else list(inputs)
        joined = "\n".join(texts)

        if self.enforce_sensitive_guard and SensitivePathGuard.is_sensitive(
            prompt=joined,
            context_paths=context_paths,
        ):
            if SensitivePathGuard.is_free_model(model):
                if use_local_failover:
                    return self.embed_local(inputs=texts, fallback_reason="sovereign_ip_guard_tripped")
                return {
                    "success": False,
                    "error": "SOVEREIGN_IP_GUARD_TRIPPED: Sensitive Ring-0/CORTEX content blocked on :free embedding endpoint.",
                    "route_override": "local_mlx",
                }

        if not self.quota.can_spend(phase=phase):
            if use_local_failover:
                return self.embed_local(inputs=texts, fallback_reason="quota_budget_exhausted")
            return {
                "success": False,
                "error": f"QUOTA_BUDGET_EXHAUSTED: Phase '{phase}' RPD limit reached.",
            }

        wait_s = self.rate_limiter.acquire_wait_seconds()
        if wait_s > 0.0:
            time.sleep(wait_s)

        url = f"{self.BASE_URL}/embeddings"
        _assert_ssrf_safe(url)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/borjamoskv/BABYLON-60",
            "X-Title": "BABYLON-60 Sovereign Kernel",
        }
        payload: Dict[str, Any] = {
            "model": model,
            "input": texts,
        }

        self.quota.record_attempt(phase=phase)

        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=30.0) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                vectors = [item.get("embedding", []) for item in result.get("data", [])]
                return {
                    "success": True,
                    "model": result.get("model", model),
                    "embeddings": vectors,
                    "usage": result.get("usage", {}),
                }
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8") if e.fp else str(e)
            logger.error("OpenRouter Embeddings error (%d): %s", e.code, err_body)
            if use_local_failover:
                return self.embed_local(inputs=texts, fallback_reason=f"openrouter_http_{e.code}")
            return {"success": False, "error": f"HTTP {e.code}: {err_body}"}
        except Exception as e:
            logger.error("OpenRouter Embeddings unexpected error: %s", str(e))
            if use_local_failover:
                return self.embed_local(inputs=texts, fallback_reason="openrouter_network_error")
            return {"success": False, "error": str(e)}
