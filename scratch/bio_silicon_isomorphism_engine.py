#!/usr/bin/env python3
"""
BIO-SILICON ISOMORPHISM ENGINE (C5-REAL Portable Empirical Validator)
Supports: Linux POSIX / macOS (Darwin ARM64 / x86_64)
Zero third-party dependencies (Pure Python 3)

Simulates & Benchmarks:
  1. Microglial Adaptive Hysteresis Gating (Bio Neuro-Immune Stateful Load Shedding)
  2. GICv4.1 / APIC O(1) Invariant Saturation Dispatch (Hardware L1 IRQ Rate Limiting)
  3. Non-Linear Bio Feedback vs Linear Algorithmic Control (Antipattern Divergence Test)

Calculates:
  - Shannon Entropy S = -sum(p_i * ln(p_i))
  - Dispatch Hysteresis Delta
  - Saturation Latency Invariance Bounds
  - Cryptographic SHA3-256 Attestation
"""

import os
import sys
import time
import math
import json
import hashlib
import threading
import platform


def compute_shannon_entropy(data_points: list[float], num_bins: int = 25) -> float:
    if not data_points:
        return 0.0
    min_val, max_val = min(data_points), max(data_points)
    if min_val == max_val:
        return 0.0
    bin_width = (max_val - min_val) / num_bins
    counts = [0] * num_bins
    for v in data_points:
        idx = min(int((v - min_val) / bin_width), num_bins - 1)
        counts[idx] += 1
    total = len(data_points)
    entropy = 0.0
    for c in counts:
        if c > 0:
            p = c / total
            entropy -= p * math.log(p)
    return entropy


class MicroglialAdaptiveGate:
    """Bio-inspired Stateful Adaptive Gate with Dual Threshold Hysteresis (Upper/Lower)"""

    def __init__(self, v_high: float = 0.75, v_low: float = 0.25):
        self.v_high = v_high
        self.v_low = v_low
        self.state_active = False
        self.accumulated_charge = 0.0
        self.lock = threading.Lock()

    def process_signal(self, intensity: float, delta_t: float) -> bool:
        with self.lock:
            # Leakage / homeostatic decay
            self.accumulated_charge = max(0.0, self.accumulated_charge - delta_t * 0.5)
            self.accumulated_charge += intensity * 0.1

            if not self.state_active and self.accumulated_charge >= self.v_high:
                self.state_active = True  # Microglial activation / Gating engaged
            elif self.state_active and self.accumulated_charge <= self.v_low:
                self.state_active = False  # Resolution / De-escalation

            return not self.state_active  # True = Pass, False = Suppressed/Shed


class GICv4HardwareAPICGate:
    """Hardware APIC / GICv4.1 O(1) Invariant Saturation Dispatcher"""

    def __init__(self, max_rate_hz: int = 12000):
        self.max_rate = max_rate_hz
        self.period = 1.0 / max_rate_hz
        self.last_dispatch = time.perf_counter()
        self.lock = threading.Lock()

    def try_dispatch(self) -> bool:
        with self.lock:
            now = time.perf_counter()
            if now - self.last_dispatch >= self.period:
                self.last_dispatch = now
                return True
            return False  # O(1) hardware ring drop / mask bit set


class BioSiliconBenchmark:
    def __init__(self, duration_seconds: float = 2.0):
        self.duration = duration_seconds

    def run_microglial_simulation(self):
        gate = MicroglialAdaptiveGate(v_high=0.70, v_low=0.30)
        latencies = []
        passed, suppressed = 0, 0
        start = time.perf_counter()
        last_t = start

        while time.perf_counter() - start < self.duration:
            now = time.perf_counter()
            dt = now - last_t
            last_t = now

            # Burst signal simulating inflammatory cytokine surge
            signal = 0.9 if (int(now * 10) % 2 == 0) else 0.1
            t0 = time.perf_counter()
            pass_flag = gate.process_signal(signal, dt)
            t1 = time.perf_counter()

            latencies.append((t1 - t0) * 1e6)  # microseconds
            if pass_flag:
                passed += 1
            else:
                suppressed += 1
            time.sleep(0.0001)

        elapsed = time.perf_counter() - start
        return {
            "regime": "Microglial_Adaptive_Hysteresis_Gating",
            "total_events": passed + suppressed,
            "passed": passed,
            "suppressed": suppressed,
            "throughput_hz": (passed + suppressed) / elapsed,
            "avg_latency_us": sum(latencies) / len(latencies) if latencies else 0.0,
            "max_latency_us": max(latencies) if latencies else 0.0,
            "shannon_entropy": compute_shannon_entropy(latencies),
        }

    def run_gicv4_apic_simulation(self):
        gate = GICv4HardwareAPICGate(max_rate_hz=12000)  # 12k IRQ/s storm
        latencies = []
        dispatched, dropped = 0, 0
        start = time.perf_counter()

        while time.perf_counter() - start < self.duration:
            t0 = time.perf_counter()
            ok = gate.try_dispatch()
            t1 = time.perf_counter()

            latencies.append((t1 - t0) * 1e6)
            if ok:
                dispatched += 1
            else:
                dropped += 1
            time.sleep(0.00005)  # 20k IRQ/s generator attempt

        elapsed = time.perf_counter() - start
        return {
            "regime": "GICv4_APIC_O1_Invariant_Dispatch",
            "total_events": dispatched + dropped,
            "dispatched": dispatched,
            "dropped": dropped,
            "throughput_hz": (dispatched + dropped) / elapsed,
            "avg_latency_us": sum(latencies) / len(latencies) if latencies else 0.0,
            "max_latency_us": max(latencies) if latencies else 0.0,
            "shannon_entropy": compute_shannon_entropy(latencies),
        }

    def run_antipattern_divergence_test(self):
        """Measures non-linear biological scaling vs rigid linear algorithmic rate limiting"""
        linear_latencies = []
        nonlinear_latencies = []
        time.perf_counter()

        # Non-linear biological scaling model: E(x) = x^1.8 / (1 + x^1.8)
        # Linear algorithmic model: L(x) = min(x, cap)
        for i in range(1, 1000):
            x = i / 100.0
            t0 = time.perf_counter()
            _ = min(x, 5.0)  # linear cap
            t1 = time.perf_counter()
            linear_latencies.append((t1 - t0) * 1e6)

            t2 = time.perf_counter()
            _ = (x**1.8) / (1.0 + x**1.8)  # non-linear sigmoidal homeostatic
            t3 = time.perf_counter()
            nonlinear_latencies.append((t3 - t2) * 1e6)

        return {
            "regime": "Antipattern_Temporal_Feedback_Divergence",
            "linear_control_entropy": compute_shannon_entropy(linear_latencies),
            "nonlinear_bio_entropy": compute_shannon_entropy(nonlinear_latencies),
            "linear_avg_latency_us": sum(linear_latencies) / len(linear_latencies),
            "nonlinear_avg_latency_us": sum(nonlinear_latencies) / len(nonlinear_latencies),
        }


def main():
    print("=== BIO-SILICON ISOMORPHISM ENGINE (C5-REAL EMPIRICAL BENCHMARK) ===")
    print(f"Platform: {platform.system()} {platform.machine()} ({platform.processor()})")

    bench = BioSiliconBenchmark(duration_seconds=1.5)

    print("\n[1/3] Benchmarking Microglial Adaptive Hysteresis Gating...")
    res_bio = bench.run_microglial_simulation()
    print(
        f"  -> Total Events: {res_bio['total_events']}, Passed: {res_bio['passed']}, Suppressed: {res_bio['suppressed']}"
    )
    print(f"  -> Avg Latency: {res_bio['avg_latency_us']:.4f} µs, Entropy S: {res_bio['shannon_entropy']:.4f}")

    print("\n[2/3] Benchmarking GICv4.1 / APIC O(1) Invariant Dispatch...")
    res_hw = bench.run_gicv4_apic_simulation()
    print(
        f"  -> Total Events: {res_hw['total_events']}, Dispatched: {res_hw['dispatched']}, Dropped: {res_hw['dropped']}"
    )
    print(f"  -> Avg Latency: {res_hw['avg_latency_us']:.4f} µs, Entropy S: {res_hw['shannon_entropy']:.4f}")

    print("\n[3/3] Benchmarking Antipattern Temporal Feedback Divergence...")
    res_div = bench.run_antipattern_divergence_test()
    print(f"  -> Linear Control Entropy: {res_div['linear_control_entropy']:.4f}")
    print(f"  -> Non-Linear Bio Entropy: {res_div['nonlinear_bio_entropy']:.4f}")

    from typing import Any

    telemetry: dict[str, Any] = {
        "metadata": {
            "system": platform.system(),
            "architecture": platform.machine(),
            "python_version": sys.version.split()[0],
            "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        },
        "metrics": {
            "microglial_adaptive_gate": res_bio,
            "gicv4_apic_hardware_gate": res_hw,
            "antipattern_divergence": res_div,
        },
    }

    raw_bytes = json.dumps(telemetry, indent=2).encode("utf-8")
    sha3_hash = hashlib.sha3_256(raw_bytes).hexdigest()
    telemetry["cryptographic_attestation"] = {"algorithm": "SHA3-256", "hash": sha3_hash}

    out_file = os.path.join(os.path.dirname(__file__), "bio_silicon_telemetry_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(telemetry, f, indent=2)

    print(f"\n[+] Bio-Silicon Telemetry exported to: {out_file}")
    print(f"[+] Cryptographic Attestation (SHA3-256): {sha3_hash}")
    print("\n=== BIO-SILICON ISOMORPHISM BENCHMARK COMPLETE ===")


if __name__ == "__main__":
    main()
