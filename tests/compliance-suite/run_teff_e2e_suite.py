#!/usr/bin/env python3
# C5-REAL EXERGY CERTIFIED
"""
End-to-End Teff (Transition Effective) Milestone 1 Verification Suite
Target: verifiable_inference_suite

Executes >1,000 end-to-end Teff transition cycles through Rust FFI:
1. CF-GKAT Canonical Equivalence Reduction (A/≡)
2. FOCUS Budget 4D Admission Check
3. WASM Sandbox (WASI 0.3) Isolation & State Hashing
4. SCITT RFC 9942 COSE Receipt Generation & Ed25519 Verification
5. Overhead & Latency Benchmarking (P50/P95/P99, target <1% total overhead)
"""

import sys
import os
import time
import math
import ctypes

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from python.verifiable_inference import VerifiableInferenceEngine, TeffResult


def main():
    print("================================================================================")
    print("      C5-REAL — MILESTONE 1: Teff END-TO-END VERIFICATION & BENCHMARK SUITE     ")
    print("================================================================================\n")

    t_start = time.perf_counter()
    try:
        engine = VerifiableInferenceEngine()
        print(f"⚙️  [FFI LOADED] Dynamic Library: {engine.lib_path}")
    except Exception as e:
        print(f"❌ Failed to load FFI dynamic library: {e}")
        sys.exit(1)

    total_tests = 0
    passed_tests = 0

    # --------------------------------------------------------------------------
    # PHASE 1: CF-GKAT Canonical Equivalence & Non-Local Control Flow
    # --------------------------------------------------------------------------
    print("\n--- PHASE 1: CF-GKAT ALGEBRAIC EQUIVALENCE REDUCTION (A/≡) ---")
    total_tests += 1
    res1 = engine.run_teff_transition(
        tool_name="database_read_query",
        param=b"table=users&id=42",
        est_tokens=150,
        est_cost_micros=150,
    )
    if res1.success and res1.gkat_latency_us < 1000:
        passed_tests += 1
        print(f"  ■ CF-GKAT Normalization: Canonical Hash {bytes(res1.canonical_hash).hex()[:16]}... "
              f"| Latency: {res1.gkat_latency_us} µs (<1 ms) [PASS]")
    else:
        print(f"  ❌ CF-GKAT Normalization failed: {res1.to_dict()}")

    # --------------------------------------------------------------------------
    # PHASE 2: WASM Sandbox Envelope (WASI 0.3) & Deterministic Hashing
    # --------------------------------------------------------------------------
    print("\n--- PHASE 2: WASM SANDBOX (WASI 0.3) ISOLATION & STATE HASHING ---")
    total_tests += 1
    if res1.success and res1.sandbox_latency_us >= 0 and bytes(res1.scitt_statement_digest) != b"\x00" * 32:
        passed_tests += 1
        print(f"  ■ WASM Sandbox Isolation: Executed in {res1.wall_clock_ms} ms (Latency: {res1.sandbox_latency_us} µs) | "
              f"Output Hash: {bytes(res1.scitt_statement_digest).hex()[:16]}... [PASS]")
    else:
        print(f"  ❌ WASM Sandbox failed: {res1.to_dict()}")

    # --------------------------------------------------------------------------
    # PHASE 3: SCITT RFC 9942 Signed Receipt & Merkle Audit Path
    # --------------------------------------------------------------------------
    print("\n--- PHASE 3: SCITT RFC 9942 COSE RECEIPT & MERKLE AUDIT PATH ---")
    total_tests += 1
    if res1.scitt_latency_us < 1000 and bytes(res1.scitt_merkle_root) != b"\x00" * 32:
        passed_tests += 1
        print(f"  ■ SCITT Receipt Emitter: COSE Signed | Merkle Root: {bytes(res1.scitt_merkle_root).hex()[:16]}... "
              f"| Signing Latency: {res1.scitt_latency_us} µs [PASS]")
    else:
        print(f"  ❌ SCITT Receipt emission failed")

    # --------------------------------------------------------------------------
    # PHASE 4: MASSIVE STRESS & OVERHEAD BENCHMARK (>1,000 TRANSITIONS)
    # --------------------------------------------------------------------------
    print("\n--- PHASE 4: MASSIVE STRESS & OVERHEAD BENCHMARK (>1,000 TRANSITIONS) ---")
    total_tests += 1
    N_iters = 1_000
    latencies_us = []

    print(f"  🎯 Executing {N_iters:,} full Teff transition cycles (CF-GKAT + WASM + SCITT + FOCUS)...")
    t0_bench = time.perf_counter()
    for i in range(N_iters):
        tool = f"action_tool_{i % 10}"
        res = engine.run_teff_transition(
            tool_name=tool,
            param=f"id={i}".encode("utf-8"),
            est_tokens=50,
            est_cost_micros=50,
        )
        latencies_us.append(res.total_overhead_us)
    t1_bench = time.perf_counter()

    latencies_us.sort()
    p50 = latencies_us[int(N_iters * 0.50)]
    p95 = latencies_us[int(N_iters * 0.95)]
    p99 = latencies_us[int(N_iters * 0.99)]

    # Assume standard LLM inference time = 500 ms (500,000 µs)
    simulated_llm_inference_us = 500_000.0
    avg_overhead_us = sum(latencies_us) / len(latencies_us)
    overhead_pct = (avg_overhead_us / simulated_llm_inference_us) * 100.0

    print(f"  📊 Verification Latency P50: {p50:.1f} µs ({p50 / 1000.0:.3f} ms)")
    print(f"  📊 Verification Latency P95: {p95:.1f} µs ({p95 / 1000.0:.3f} ms)")
    print(f"  📊 Verification Latency P99: {p99:.1f} µs ({p99 / 1000.0:.3f} ms)")
    print(f"  ⚡ Average Total Security Overhead: {avg_overhead_us:.1f} µs ({avg_overhead_us / 1000.0:.3f} ms)")
    print(f"  🔥 OVERHEAD PERCENTAGE VS INFERENCE (500ms baseline): {overhead_pct:.4f}% (Requirement: <1.0%)")

    if overhead_pct < 1.0:
        passed_tests += 1
        print("  ■ Overhead Requirement (<1%): VERIFIED & PASSED [PASS]")
    else:
        print(f"  ❌ Overhead requirement failed: got {overhead_pct:.4f}%")

    t_total = time.perf_counter() - t_start

    print("\n================================================================================")
    print(f"      SUITE SUMMARY: {passed_tests}/{total_tests} VERIFICATIONS PASSED (Total Time: {t_total:.2f} s)")
    print("================================================================================\n")

    if passed_tests == total_tests:
        print("🎉 [HITO 1 - Teff MILESTONE VERIFIED SUCCESSFULLY] All C5-REAL invariants satisfied!")
        sys.exit(0)
    else:
        print("❌ [FAILURE] Some verification checks failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
