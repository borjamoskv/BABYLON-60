# C5-REAL EXERGY CERTIFIED
# [C5-REAL] Exergy-Maximized
"""CORTEX Metering - Stateful Load Shedding.

O(1) memory-based load shedding using EWMA and double-threshold hysteresis.
Complies with invariant Ω160.
"""

import math
import random
import time
from typing import Any, Dict

__all__ = ["StatefulLoadShedder"]

class StatefulLoadShedder:
    """Enforces non-linear stateful load shedding to prevent A2 linear limits."""

    def __init__(self, v_low: float = 0.8, v_high: float = 1.0, eta: float = 8.0, half_life_sec: float = 10.0):
        self.v_low = v_low
        self.v_high = v_high
        self.eta = eta
        self.half_life_sec = half_life_sec
        self.tau = half_life_sec / 0.69314718056  # ln(2)
        # State: tenant_id -> {"rate_mass": float, "last_time": float, "shedding": bool}
        self._states: Dict[str, Dict[str, Any]] = {}

    def check(self, tenant_id: str, limit_rpm: int) -> bool:
        """
        Evaluate if a request should be allowed or shed.
        O(1) operation.

        Returns:
            True if allowed, False if shed.
        """
        if limit_rpm <= 0:
            return True

        now = time.monotonic()
        state = self._states.get(tenant_id)
        if not state:
            state = {"rate_mass": 0.0, "last_time": now, "shedding": False}
            self._states[tenant_id] = state

        dt = now - state["last_time"]

        # Decay the mass
        decay = math.exp(-dt / self.tau)

        # Add 1 request mass
        state["rate_mass"] = (state["rate_mass"] * decay) + 1.0
        state["last_time"] = now

        current_rps = state["rate_mass"] / self.tau
        limit_rps = limit_rpm / 60.0
        x = current_rps / limit_rps

        # Hysteresis state machine
        if not state["shedding"] and x > self.v_high:
            state["shedding"] = True
        elif state["shedding"] and x < self.v_low:
            state["shedding"] = False

        if state["shedding"]:
            # Non-linear attenuation: E(x) = x^eta / (1 + x^eta)
            x_capped = min(x, 10.0)
            try:
                e_x = (x_capped ** self.eta) / (1.0 + (x_capped ** self.eta))
            except OverflowError:
                e_x = 1.0

            if random.random() < e_x:
                return False  # Shed the request

        return True
