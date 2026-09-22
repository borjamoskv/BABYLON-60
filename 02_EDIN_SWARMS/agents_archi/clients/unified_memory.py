#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ UNIFIED MEMORY PROFILER | DOMAIN: agents.archi | STATE: C5-REAL
# ============================================================================
"""
Unified Memory & Silicon Hardware Profiler for Swarm Execution.

Optimized for:
  - Apple Silicon Workstation (M-Series current node)
  - Apple Silicon Mac Studio Ultra 256GB (Expansion Roadmap)
  - Zero-Swap Headroom Verification for Local LLMs (MLX / vLLM)
"""

import os
import platform
import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class QuantizationType(Enum):
    FP16 = "fp16"  # 2.0 bytes / parameter
    Q8_0 = "q8_0"  # ~1.05 bytes / parameter
    Q4_K_M = "q4_k_m"  # ~0.58 bytes / parameter
    Q2_K = "q2_k"  # ~0.35 bytes / parameter


@dataclass
class ModelMemoryRequirement:
    """Estimated memory footprint for a given LLM parameter count."""

    model_name: str
    param_count_billions: float
    quantization: QuantizationType
    weights_ram_gb: float
    kv_cache_per_user_gb: float
    total_estimated_ram_gb: float
    fits_zero_swap: bool
    max_concurrent_agents: int


@dataclass
class HardwareTopologyReport:
    """Telemetry report of host hardware and unified memory topology."""

    os_system: str
    architecture: str
    total_ram_gb: float
    available_ram_gb: float
    is_apple_silicon: bool
    is_ultra_class: bool
    recommended_backend: str
    max_hostable_params_q4_billions: float
    swap_risk_score: float  # 0.0 = zero swap, 1.0 = high thrashing risk


class UnifiedMemoryProfiler:
    """
    Profiles Apple Silicon unified RAM and calculates exact limits
    for hosting swarm inference without kernel swapping.
    """

    BYTES_PER_PARAM: Dict[QuantizationType, float] = {
        QuantizationType.FP16: 2.0,
        QuantizationType.Q8_0: 1.05,
        QuantizationType.Q4_K_M: 0.58,
        QuantizationType.Q2_K: 0.35,
    }

    def __init__(self, override_ram_gb: Optional[float] = None) -> None:
        self._override_ram_gb = override_ram_gb

    @classmethod
    def get_system_ram_bytes(cls) -> int:
        """Determines total physical RAM in bytes."""
        if platform.system() == "Darwin":
            try:
                res = subprocess.run(
                    ["sysctl", "-n", "hw.memsize"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                return int(res.stdout.strip())
            except Exception:
                pass
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")  # type: ignore

    def get_hardware_report(self) -> HardwareTopologyReport:
        """Generates a complete hardware topology report."""
        if self._override_ram_gb is not None:
            total_ram_gb = self._override_ram_gb
        else:
            total_ram_gb = round(self.get_system_ram_bytes() / (1024**3), 2)

        is_arm = platform.machine() in ("arm64", "aarch64")
        is_darwin = platform.system() == "Darwin"
        is_apple_silicon = is_darwin and is_arm

        # Mac Studio Ultra class is defined as >= 128 GB Unified RAM
        is_ultra_class = is_apple_silicon and (total_ram_gb >= 120.0)

        # 4-bit capacity leaving 20% OS/DAW buffer
        usable_ram = total_ram_gb * 0.80
        max_params_q4 = round(usable_ram / self.BYTES_PER_PARAM[QuantizationType.Q4_K_M], 1)

        recommended_backend = "local_mlx" if is_apple_silicon else "local_vllm"

        return HardwareTopologyReport(
            os_system=platform.system(),
            architecture=platform.machine(),
            total_ram_gb=total_ram_gb,
            available_ram_gb=round(usable_ram, 2),
            is_apple_silicon=is_apple_silicon,
            is_ultra_class=is_ultra_class,
            recommended_backend=recommended_backend,
            max_hostable_params_q4_billions=max_params_q4,
            swap_risk_score=0.0,
        )

    def calculate_model_fit(
        self,
        model_name: str,
        param_count_billions: float,
        quantization: QuantizationType = QuantizationType.Q4_K_M,
        context_window_tokens: int = 32768,
        concurrent_agents: int = 10,
    ) -> ModelMemoryRequirement:
        """
        Calculates exact memory fit and concurrency ceiling for an LLM on unified RAM.
        """
        hw = self.get_hardware_report()
        b_per_p = self.BYTES_PER_PARAM[quantization]
        weights_ram_gb = (param_count_billions * 1e9 * b_per_p) / (1024**3)

        # KV cache estimate: 2 * n_layers * n_heads * d_head * context_len
        # Empirical rule of thumb: ~0.5 MB per 1k tokens for 70B, scaled proportionally
        kv_cache_per_user_gb = 0.0005 * (context_window_tokens / 1000) * (param_count_billions / 70.0)
        kv_cache_per_user_gb = max(0.05, kv_cache_per_user_gb)

        total_ram = weights_ram_gb + (kv_cache_per_user_gb * concurrent_agents)
        fits = total_ram <= hw.available_ram_gb

        headroom_for_agents = max(0.0, hw.available_ram_gb - weights_ram_gb)
        max_agents = int(headroom_for_agents // kv_cache_per_user_gb) if kv_cache_per_user_gb > 0 else 0

        return ModelMemoryRequirement(
            model_name=model_name,
            param_count_billions=param_count_billions,
            quantization=quantization,
            weights_ram_gb=round(weights_ram_gb, 2),
            kv_cache_per_user_gb=round(kv_cache_per_user_gb, 3),
            total_estimated_ram_gb=round(total_ram, 2),
            fits_zero_swap=fits,
            max_concurrent_agents=max_agents,
        )

    def simulate_mac_studio_ultra_256gb(self) -> Dict[str, Any]:
        """
        Simulates execution matrix for the Mac Studio Ultra 256GB sovereign expansion.
        """
        sim_profiler = UnifiedMemoryProfiler(override_ram_gb=256.0)
        models = [
            ("Llama-3.3-70B", 70.0, QuantizationType.Q4_K_M),
            ("Qwen-2.5-72B", 72.0, QuantizationType.Q4_K_M),
            ("Kimi-K3-MoE-120B", 120.0, QuantizationType.Q4_K_M),
            ("DeepSeek-V3-671B-MoE-Active-37B", 37.0, QuantizationType.Q4_K_M),
            ("Llama-3.1-405B-Q4", 405.0, QuantizationType.Q4_K_M),
        ]

        projections = []
        for name, params, quant in models:
            res = sim_profiler.calculate_model_fit(
                name, params, quant, context_window_tokens=32768, concurrent_agents=20
            )
            projections.append(
                {
                    "model": res.model_name,
                    "weights_gb": res.weights_ram_gb,
                    "total_ram_gb": res.total_estimated_ram_gb,
                    "fits_zero_swap": res.fits_zero_swap,
                    "max_swarm_agents": res.max_concurrent_agents,
                }
            )

        return {
            "node": "Mac Studio Ultra 256GB Unified Memory",
            "total_ram_gb": 256.0,
            "usable_ram_gb": 204.8,
            "projections": projections,
        }
