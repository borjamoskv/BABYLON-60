# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
"""
61_q_rsqrt_ultra_exergy.py
==========================
Módulo Ultra-Exergía de Implementación Invariante del Algoritmo Fast Inverse Square Root.
V4.0 ULTRATHINK ENHANCED: Cubic Householder Iteration + ARM NEON FMA (Fused Multiply-Add).
"""

import math
import time
import ctypes
import os
import numpy as np
import numba

# -----------------------------------------------------------------------------
# 0. CARGAR EXTENSIÓN C NATIVA (ARM NEON FMA)
# -----------------------------------------------------------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
neon_fma_lib_path = os.path.join(script_dir, "libq_rsqrt_neon_fma.dylib")
neon_fma_available = False

try:
    neon_fma_lib = ctypes.CDLL(neon_fma_lib_path)
    # void neon_rsqrt_cubic_fma_array(const float* in, float* out, size_t n)
    neon_fma_lib.neon_rsqrt_cubic_fma_array.argtypes = [
        np.ctypeslib.ndpointer(dtype=np.float32, ndim=1, flags='C_CONTIGUOUS'),
        np.ctypeslib.ndpointer(dtype=np.float32, ndim=1, flags='C_CONTIGUOUS'),
        ctypes.c_size_t
    ]
    neon_fma_lib.neon_rsqrt_cubic_fma_array.restype = None
    neon_fma_available = True
except Exception as e:
    print(f"[WARNING] ARM NEON FMA extension not found or failed to load: {e}")

def q_rsqrt_neon_fma(x_arr: np.ndarray) -> np.ndarray:
    """Ejecuta ARM NEON FMA Cubic Householder hardware rsqrt sobre un array."""
    if not neon_fma_available:
        raise RuntimeError("ARM NEON FMA native extension not loaded.")
    x_arr = np.ascontiguousarray(x_arr, dtype=np.float32)
    out_arr = np.empty_like(x_arr)
    neon_fma_lib.neon_rsqrt_cubic_fma_array(x_arr, out_arr, x_arr.size)
    return out_arr


# -----------------------------------------------------------------------------
# 1. IMPLEMENTACIÓN FLOAT 32-BIT (NUMBA JIT + CUBIC HOUSEHOLDER FMA)
# -----------------------------------------------------------------------------
@numba.njit(fastmath=True, parallel=True)
def q_rsqrt_vec32_numba_cubic(x_arr: np.ndarray, magic: int = 0x5f375a86) -> np.ndarray:
    out = np.empty_like(x_arr)
    for k in numba.prange(x_arr.size):
        x = x_arr[k]

        tmp = np.empty(1, dtype=np.float32)
        tmp[0] = x
        i = tmp.view(np.int32)[0]
        i = magic - (i >> 1)

        tmp2 = np.empty(1, dtype=np.int32)
        tmp2[0] = i
        y = tmp2.view(np.float32)[0]

        # Cubic Householder Step (FMA-friendly)
        r = 1.0 - x * y * y
        y = y + y * r * (0.5 + 0.375 * r)

        out[k] = y
    return out

# -----------------------------------------------------------------------------
# 2. SUITE DE VERIFICACIÓN EMPÍRICA (TEST RUNNER)
# -----------------------------------------------------------------------------
def run_benchmarks():
    print("=== C5-REAL Q_RSQRT ULTRATHINK CUBIC FMA BENCHMARK ===")

    # Warm up JIT
    test_arr = np.random.uniform(0.1, 1000.0, 10).astype(np.float32)
    _ = q_rsqrt_vec32_numba_cubic(test_arr)

    N = 10_000_000
    print(f"Generando {N} números aleatorios en float32...")
    data = np.random.uniform(0.001, 100000.0, N).astype(np.float32)

    print("\n[1] NumPy Numpy Vectorized (1.0 / np.sqrt(x)) [BASELINE]")
    t0 = time.perf_counter()
    exact = 1.0 / np.sqrt(data)
    t1 = time.perf_counter()
    t_numpy = t1 - t0
    print(f"    -> {t_numpy:.5f} segundos")

    print("\n[2] Numba JIT Parallelized (Minimax + Cubic Householder)")
    t0 = time.perf_counter()
    numba_res = q_rsqrt_vec32_numba_cubic(data)
    t1 = time.perf_counter()
    t_numba = t1 - t0
    print(f"    -> {t_numba:.5f} segundos | Speedup vs Baseline: {t_numpy/t_numba:.2f}x")
    max_err_numba = np.max(np.abs(numba_res - exact) / exact) * 100
    print(f"    -> Max Relative Error (Numba Cubic): {max_err_numba:.6f}%")

    if neon_fma_available:
        print("\n[3] ARM NEON FMA Native Hardware (vrsqrteq_f32 + Cubic vfmaq_f32)")
        t0 = time.perf_counter()
        neon_fma_res = q_rsqrt_neon_fma(data)
        t1 = time.perf_counter()
        t_neon = t1 - t0
        print(f"    -> {t_neon:.5f} segundos | Speedup vs Baseline: {t_numpy/t_neon:.2f}x")

        max_err_neon = np.max(np.abs(neon_fma_res - exact) / exact) * 100
        print(f"    -> Max Relative Error (NEON Cubic FMA): {max_err_neon:.6f}%")

    print("\n[C5-REAL] Benchmark de Ultra-Exergía Finalizado.")

if __name__ == "__main__":
    run_benchmarks()
