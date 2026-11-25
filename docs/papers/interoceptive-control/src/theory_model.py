"""
Formalization of Computational Interoception and Homeostatic Control in Autonomous Silicon Agents.
Part of the BABYLON-60 / CORTEX theoretical foundation.

Mathematical Model:
- State space S = S_ext x S_int
- S_int: Internal somatosensory metrics <RAM_pct, Token_burn, IPC_latency_ms, Context_fill_pct>
- Viability Kernel K_v: Set of internal states where resource expenditure remains bounded.
- Lyapunov Candidate Function V(s_int): Quadratic distance to the homeostatic setpoint s*.
"""

from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class InteroceptiveState:
    ram_usage_pct: float       # [0.0, 100.0]
    token_burn_rate: float     # tokens / second
    ipc_latency_ms: float      # milliseconds
    context_fill_pct: float    # [0.0, 100.0]

    def to_vector(self) -> np.ndarray:
        return np.array([
            self.ram_usage_pct / 100.0,
            min(self.token_burn_rate / 1000.0, 1.0),
            min(self.ipc_latency_ms / 100.0, 1.0),
            self.context_fill_pct / 100.0
        ], dtype=np.float64)

@dataclass(frozen=True)
class HomeostaticSafeThresholds:
    max_safe_ram_pct: float = 80.0
    max_safe_token_burn: float = 2500.0     # tokens / second
    max_safe_ipc_latency_ms: float = 20.0   # milliseconds
    max_safe_context_fill: float = 70.0     # % of context capacity

class InteroceptiveLyapunovController:
    """
    Evaluates whether the agent trajectory remains within the viability kernel K_v.
    Uses a Control Barrier Function (CBF) / one-sided quadratic penalty (Aubin Viability Theory).
    Only states that exceed safe physiological thresholds generate stress energy V(s).
    """
    def __init__(self, weights: np.ndarray | None = None):
        # Weights: [RAM, TokenBurn, IPCLatency, ContextFill]
        self.weights = weights if weights is not None else np.array([3.0, 1.5, 1.0, 4.0], dtype=np.float64)
        self.thresholds = HomeostaticSafeThresholds()

    def lyapunov_energy(self, state: InteroceptiveState) -> float:
        """
        One-sided quadratic barrier:
        V(s) = sum_i w_i * max(0, (s_i - theta_i) / normalizer_i)^2
        """
        ram_excess = max(0.0, (state.ram_usage_pct - self.thresholds.max_safe_ram_pct) / 20.0)
        burn_excess = max(0.0, (state.token_burn_rate - self.thresholds.max_safe_token_burn) / 1000.0)
        ipc_excess = max(0.0, (state.ipc_latency_ms - self.thresholds.max_safe_ipc_latency_ms) / 50.0)
        context_excess = max(0.0, (state.context_fill_pct - self.thresholds.max_safe_context_fill) / 30.0)

        excess_vector = np.array([ram_excess, burn_excess, ipc_excess, context_excess], dtype=np.float64)
        return float(np.sum(self.weights * (excess_vector ** 2)))

    def is_within_viability_kernel(self, state: InteroceptiveState, max_v: float = 1.0) -> bool:
        """
        Checks if state is within viability boundaries K_v.
        Hard bounds:
        - RAM < 92%
        - Context < 95%
        - Barrier energy V(s) < max_v
        """
        if state.ram_usage_pct >= 92.0 or state.context_fill_pct >= 95.0:
            return False
        return self.lyapunov_energy(state) < max_v
