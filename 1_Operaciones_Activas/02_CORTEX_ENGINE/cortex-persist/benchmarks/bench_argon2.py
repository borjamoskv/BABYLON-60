# [C5-REAL] Exergy-Maximized Benchmark for Argon2id Hashing
import logging
import time

import argon2
import cortex_rs
import numpy as np


def run_benchmarks(iterations=50):
    pass_word = "Sovereign_Agent_Passphrase_2026!"

    # Initialize Hasher for argon2-cffi with matching parameters:
    # m_cost = 65536, t_cost = 2, p_cost = 1, output length = 32
    ph = argon2.PasswordHasher(time_cost=2, memory_cost=65536, parallelism=1, hash_len=32)

    # --- 1. Hashing Benchmark ---
    cffi_hash_times = []
    rs_hash_times = []

    cffi_hashes = []
    rs_hashes = []

    logging.getLogger(__name__).info(f"🚀 Running Hashing Benchmarks ({iterations} iterations)...")
    for _ in range(iterations):
        # argon2-cffi
        t0 = time.perf_counter()
        h_cffi = ph.hash(pass_word)
        t1 = time.perf_counter()
        cffi_hash_times.append((t1 - t0) * 1000.0)  # in ms
        cffi_hashes.append(h_cffi)

        # cortex_rs
        t0 = time.perf_counter()
        h_rs = cortex_rs.hash_password(pass_word)
        t1 = time.perf_counter()
        rs_hash_times.append((t1 - t0) * 1000.0)  # in ms
        rs_hashes.append(h_rs)

    # --- 2. Verification Benchmark ---
    cffi_verify_times = []
    rs_verify_times = []

    logging.getLogger(__name__).info(f"🚀 Running Verification Benchmarks ({iterations} iterations)...")
    for i in range(iterations):
        # argon2-cffi
        t0 = time.perf_counter()
        ph.verify(cffi_hashes[i], pass_word)
        t1 = time.perf_counter()
        cffi_verify_times.append((t1 - t0) * 1000.0)

        # cortex_rs
        t0 = time.perf_counter()
        cortex_rs.verify_password(pass_word, rs_hashes[i])
        t1 = time.perf_counter()
        rs_verify_times.append((t1 - t0) * 1000.0)

    # --- Calculations ---
    def get_metrics(times):
        return {
            "min": np.min(times),
            "p50": np.percentile(times, 50),
            "p95": np.percentile(times, 95),
            "p99": np.percentile(times, 99),
            "max": np.max(times),
            "mean": np.mean(times),
            "std": np.std(times),
        }

    cffi_hash_metrics = get_metrics(cffi_hash_times)
    rs_hash_metrics = get_metrics(rs_hash_times)
    cffi_verify_metrics = get_metrics(cffi_verify_times)
    rs_verify_metrics = get_metrics(rs_verify_times)

    logging.getLogger(__name__).info("\n# Argon2id Performance Comparison (in milliseconds)")
    logging.getLogger(__name__).info("\n## 1. Hashing (`hash_password`)")
    logging.getLogger(__name__).info(
        "| Implementation | Min (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Max (ms) | Mean (ms) | Std (ms) |"
    )
    logging.getLogger(__name__).info("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
    logging.getLogger(__name__).info(
        f"| `argon2-cffi` | {cffi_hash_metrics['min']:.2f} | {cffi_hash_metrics['p50']:.2f} | {cffi_hash_metrics['p95']:.2f} | {cffi_hash_metrics['p99']:.2f} | {cffi_hash_metrics['max']:.2f} | {cffi_hash_metrics['mean']:.2f} | {cffi_hash_metrics['std']:.2f} |"
    )
    logging.getLogger(__name__).info(
        f"| `cortex_rs`   | {rs_hash_metrics['min']:.2f} | {rs_hash_metrics['p50']:.2f} | {rs_hash_metrics['p95']:.2f} | {rs_hash_metrics['p99']:.2f} | {rs_hash_metrics['max']:.2f} | {rs_hash_metrics['mean']:.2f} | {rs_hash_metrics['std']:.2f} |"
    )

    logging.getLogger(__name__).info("\n## 2. Verification (`verify_password`)")
    logging.getLogger(__name__).info(
        "| Implementation | Min (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Max (ms) | Mean (ms) | Std (ms) |"
    )
    logging.getLogger(__name__).info("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
    logging.getLogger(__name__).info(
        f"| `argon2-cffi` | {cffi_verify_metrics['min']:.2f} | {cffi_verify_metrics['p50']:.2f} | {cffi_verify_metrics['p95']:.2f} | {cffi_verify_metrics['p99']:.2f} | {cffi_verify_metrics['max']:.2f} | {cffi_verify_metrics['mean']:.2f} | {cffi_verify_metrics['std']:.2f} |"
    )
    logging.getLogger(__name__).info(
        f"| `cortex_rs`   | {rs_verify_metrics['min']:.2f} | {rs_verify_metrics['p50']:.2f} | {rs_verify_metrics['p95']:.2f} | {rs_verify_metrics['p99']:.2f} | {rs_verify_metrics['max']:.2f} | {rs_verify_metrics['mean']:.2f} | {rs_verify_metrics['std']:.2f} |"
    )

    improvement_hash = (
        (cffi_hash_metrics["p50"] - rs_hash_metrics["p50"]) / cffi_hash_metrics["p50"] * 100
    )
    improvement_verify = (
        (cffi_verify_metrics["p50"] - rs_verify_metrics["p50"]) / cffi_verify_metrics["p50"] * 100
    )
    logging.getLogger(__name__).info(
        f"\n🚀 **Speedup (p50):** Hashing is {cffi_hash_metrics['p50'] / rs_hash_metrics['p50']:.1f}x faster ({improvement_hash:.1f}% reduction in latency)."
    )
    logging.getLogger(__name__).info(
        f"🚀 **Speedup (p50):** Verification is {cffi_verify_metrics['p50'] / rs_verify_metrics['p50']:.1f}x faster ({improvement_verify:.1f}% reduction in latency)."
    )


if __name__ == "__main__":
    run_benchmarks()
