#!/usr/bin/env python3
"""
METABOLIC DEAD MAN SWITCH: WETWARE THERMOSTAT (Reality Level: #C6-ABSOLUTE)
Layer: Ring -3 (Bare-Metal Electromechanical Actuation)

Monitors biophysical fatigue via keyboard typing jitter (stochastic variance of inter-keystroke intervals).
If operator jitter exceeds critical threshold, executes hard thermodynamic shutdown via GPIO / SSR Relay.
Cuts physical 220V power to monitors to save operator from biological burnout.

Dual-Mode Runtime:
1. MicroPython bare-metal execution on RP2040 microcontroller (machine.Pin).
2. POSIX emulation mode for CI/CD testing and dry-run validation.
"""

import math
import time
from typing import List, Optional, Any

# Hardware abstraction layer: MicroPython vs POSIX fallback
try:
    from machine import Pin

    IS_MICROPYTHON = True
except ImportError:
    IS_MICROPYTHON = False

    class MockPin:
        OUT = 1
        IN = 0
        IRQ_FALLING = 2

        def __init__(self, pin_num: int, mode: int = 1):
            self.pin_num = pin_num
            self.mode = mode
            self.current_value = 0

        def value(self, val: Optional[int] = None) -> int:
            if val is not None:
                self.current_value = int(val)
            return self.current_value

        def irq(self, trigger: int, handler: Any) -> None:
            return None

    Pin = MockPin


class WetwareThermostat:
    """Biophysical Thermodynamic Brake. Measures stochastic keystroke jitter."""

    def __init__(self, variance_threshold_ms: float = 120.0, ssr_pin_id: int = 15) -> None:
        self.ssr_pin_id: int = ssr_pin_id
        self.SSR_RELAY = Pin(ssr_pin_id, Pin.OUT)
        self.SSR_RELAY.value(1)  # 1 = Circuit Closed (Power ON)
        self.variance_threshold: float = float(variance_threshold_ms)
        self.keystroke_deltas: List[float] = []
        self.last_press: float = self._get_time_ms()
        self.is_halted: bool = False
        self.last_computed_jitter: float = 0.0

    def _get_time_ms(self) -> float:
        if hasattr(time, "ticks_ms"):
            return float(getattr(time, "ticks_ms")())
        return float(time.time() * 1000.0)

    def register_biometric_event(self, delta_ms: Optional[float] = None) -> None:
        """Processes keystroke delta interval and updates circular buffer."""
        if self.is_halted:
            return

        now = self._get_time_ms()
        if delta_ms is None:
            if hasattr(time, "ticks_diff"):
                delta = float(getattr(time, "ticks_diff")(int(now), int(self.last_press)))
            else:
                delta = now - self.last_press
            self.last_press = now
        else:
            delta = float(delta_ms)

        # Filter out multi-second idle pauses or microsecond switch debounce bounces
        if 50.0 < delta < 1500.0:
            self.keystroke_deltas.append(delta)

        if len(self.keystroke_deltas) > 25:
            self.keystroke_deltas.pop(0)
            self._evaluate_biological_burnout()

    def _evaluate_biological_burnout(self) -> None:
        """Calculates standard deviation of intervals (jitter)."""
        n = len(self.keystroke_deltas)
        if n < 10:
            return

        mean = sum(self.keystroke_deltas) / n
        variance = sum((x - mean) ** 2 for x in self.keystroke_deltas) / n
        self.last_computed_jitter = math.sqrt(variance)

        if self.last_computed_jitter > self.variance_threshold:
            self._execute_hard_halt()

    def _execute_hard_halt(self) -> None:
        """Zero confirmation. Zero disk flush. Hard 220V physical power cutoff."""
        self.is_halted = True
        self.SSR_RELAY.value(0)  # 0 = Open Circuit (Power OFF)


def run_emulation(threshold_ms: float = 120.0, inject_burnout: bool = False) -> bool:
    import random

    thermostat = WetwareThermostat(variance_threshold_ms=threshold_ms)

    print(f"[C6-EMULATOR] Wetware Thermostat initialised. Relay pin 15 value: {thermostat.SSR_RELAY.value()} (ON)")
    print(
        f"[C6-EMULATOR] Target Jitter Threshold: {threshold_ms}ms | Mode: {'BURNOUT INJECTION' if inject_burnout else 'NORMAL RHYTHM'}"
    )

    for i in range(35):
        if inject_burnout and i >= 20:
            # High-jitter fatigued typing (shaky erratic pauses)
            delta = random.uniform(80.0, 750.0)
        else:
            # Steady focused rhythm (low variance around 180ms)
            delta = random.gauss(180.0, 15.0)

        thermostat.register_biometric_event(delta_ms=delta)
        if thermostat.is_halted:
            print(f"[{i:02d}] HARD HALT TRIGGERED! Jitter: {thermostat.last_computed_jitter:.2f}ms > {threshold_ms}ms")
            print(f"[C6-EMULATOR] SSR Relay set to: {thermostat.SSR_RELAY.value()} (POWER CUT TO 0V)")
            return True

    print(
        f"[C6-EMULATOR] Session completed without burnout. Jitter: {thermostat.last_computed_jitter:.2f}ms | Relay: {thermostat.SSR_RELAY.value()}"
    )
    return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Wetware Dead Man Switch (C6-ABSOLUTE)")
    parser.add_argument("--threshold", type=float, default=120.0, help="Jitter cutoff threshold in ms.")
    parser.add_argument("--burnout", action="store_true", help="Simulate human metabolic exhaustion.")
    args = parser.parse_args()

    run_emulation(threshold_ms=args.threshold, inject_burnout=args.burnout)
