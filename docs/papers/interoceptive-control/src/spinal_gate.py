"""
L0 Interoceptive Telemetry Sensor & Spinal Interrupt Gate.
Provides closed-loop somatosensory feedback to autonomous agent loops.
"""

import time
import os
import psutil
from dataclasses import dataclass
from .theory_model import InteroceptiveState, InteroceptiveLyapunovController

class SpinalPainException(Exception):
    """Triggered when an internal bodily viability threshold is breached."""
    pass

@dataclass
class TelemetryReading:
    timestamp: float
    state: InteroceptiveState
    lyapunov_v: float
    is_viable: bool

class L0InteroceptiveSensor:
    """
    Simulates / captures real L0 hardware and execution metrics:
    - RAM utilization of current process tree
    - Token burn velocity (synthetic or instrumented)
    - IPC channel latency
    - Context window occupancy
    """
    def __init__(self, context_limit: int = 128000):
        self.process = psutil.Process(os.getpid())
        self.controller = InteroceptiveLyapunovController()
        self.context_limit = context_limit
        self.total_tokens_consumed = 0
        self.start_time = time.time()

    def sample(self, current_tokens: int, step_duration_s: float = 1.0, ipc_latency_ms: float = 0.5) -> TelemetryReading:
        self.total_tokens_consumed += current_tokens
        elapsed = max(time.time() - self.start_time, 0.5)
        # Token burn rate averaged over steps
        burn_rate = current_tokens / max(step_duration_s, 0.1)

        # Physical system memory
        mem_info = psutil.virtual_memory()
        ram_pct = mem_info.percent

        context_fill = min((self.total_tokens_consumed / self.context_limit) * 100.0, 100.0)

        state = InteroceptiveState(
            ram_usage_pct=ram_pct,
            token_burn_rate=burn_rate,
            ipc_latency_ms=ipc_latency_ms,
            context_fill_pct=context_fill
        )

        v = self.controller.lyapunov_energy(state)
        viable = self.controller.is_within_viability_kernel(state)

        return TelemetryReading(
            timestamp=time.time(),
            state=state,
            lyapunov_v=v,
            is_viable=viable
        )

    def generate_afferent_pulse(self, reading: TelemetryReading) -> str:
        """
        Emits the sensory pulse to be fed into the agent loop.
        Does not pollute long-term episodic memory.
        """
        s = reading.state
        return (
            f"[SOMATOSENSORY L0 PULSE] "
            f"RAM: {s.ram_usage_pct:.1f}% | "
            f"Burn: {s.token_burn_rate:.1f} tok/s | "
            f"Context: {s.context_fill_pct:.1f}% | "
            f"V_Lyapunov: {reading.lyapunov_v:.3f} | "
            f"Status: {'HOMEOSTATIC' if reading.is_viable else 'CRITICAL_DISRUPTION'}"
        )

class SpinalReflexGate:
    """
    Ring-0/L0 Spinal Reflex: Interrupts execution at O(1) without requiring
    cerebral / LLM deliberation when tissue/silicon limits are exceeded.
    """
    def __init__(self, sensor: L0InteroceptiveSensor):
        self.sensor = sensor

    def verify_action(self, proposed_token_cost: int, estimated_latency_ms: float = 1.0) -> TelemetryReading:
        reading = self.sensor.sample(proposed_token_cost, estimated_latency_ms)
        if not reading.is_viable:
            raise SpinalPainException(
                f"SPINAL_FAIL_STOP: Viability Kernel breached! "
                f"Lyapunov V={reading.lyapunov_v:.2f}, RAM={reading.state.ram_usage_pct}%, "
                f"Context={reading.state.context_fill_pct:.1f}%"
            )
        return reading
