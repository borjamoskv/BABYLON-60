# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
"""
61_q_rsqrt_ultra_exergy.py
==========================
Módulo Ultra-Exergía de Implementación Invariante del Algoritmo Fast Inverse Square Root.
V3.2 ULTRATHINK ENHANCED: Numba JIT + ARM NEON Native C-Extension + Vectorization.
"""

import math
import time
import ctypes
import os
import numpy as np
import numba

# -----------------------------------------------------------------------------
# 0. CARGAR EXTENSIÓN C NATIVA (ARM NEON)
# -----------------------------------------------------------------------------
neon_lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "libq_rsqrt_neon.dylib")
neon_available = False

try:
    neon_lib = ctypes.CDLL(neon_lib_path)
    # void neon_rsqrt_f32_array(const float* in, float* out, size_t n)
    neon_lib.neon_rsqrt_f32_array.argtypes = [
        np.ctypeslib.ndpointer(dtype=np.float32, ndim=1, flags='C_CONTIGUOUS'),
        np.ctypeslib.ndpointer(dtype=np.float32, ndim=1, flags='C_CONTIGUOUS'),
        ctypes.c_size_t
    ]
    neon_lib.neon_rsqrt_f32_array.restype = None
    neon_available = True
except Exception as e:
    print(f"[WARNING] ARM NEON extension not found or failed to load: {e}")


def q_rsqrt_neon(x_arr: np.ndarray) -> np.ndarray:
    """Ejecuta ARM NEON hardware rsqrt sobre un array."""
    if not neon_available:
        raise RuntimeError("ARM NEON native extension not loaded.")
    x_arr = np.ascontiguousarray(x_arr, dtype=np.float32)
    out_arr = np.empty_like(x_arr)
    neon_lib.neon_rsqrt_f32_array(x_arr, out_arr, x_arr.size)
    return out_arr

# -----------------------------------------------------------------------------
# 1. IMPLEMENTACIÓN FLOAT 32-BIT (NUMBA JIT + MINIMAX WALCZYK 0x5f375a86)
# -----------------------------------------------------------------------------
@numba.njit(fastmath=True)
def q_rsqrt_32_jit(x: float, iterations: int = 1, magic: int = 0x5f375a86) -> float:
    # Numba no soporta struct.unpack, usamos numpy view para type-pun!
    x_arr = np.array([x], dtype=np.float32)
    x2 = x_arr[0] * 0.5

    i = x_arr.view(np.int32)[0]
    i = magic - (i >> 1)

    y_arr = np.array([i], dtype=np.int32)
    y = y_arr.view(np.float32)[0]

    # 1st Newton step
    y = y * (1.5 - (x2 * y * y))

    # 2nd Newton step
    if iterations >= 2:
        y = y * (1.5 - (x2 * y * y))
    return y

@numba.njit(fastmath=True, parallel=True)
def q_rsqrt_vec32_numba(x_arr: np.ndarray, iterations: int = 2, magic: int = 0x5f375a86) -> np.ndarray:
    out = np.empty_like(x_arr)
    for k in numba.prange(x_arr.size):
        x = x_arr[k]
        x2 = x * 0.5

        # Array temporal para bypass de tipado estricto en Numba
        tmp = np.empty(1, dtype=np.float32)
        tmp[0] = x
        i = tmp.view(np.int32)[0]
        i = magic - (i >> 1)

        tmp2 = np.empty(1, dtype=np.int32)
        tmp2[0] = i
        y = tmp2.view(np.float32)[0]

        y = y * (1.5 - (x2 * y * y))
        if iterations >= 2:
            y = y * (1.5 - (x2 * y * y))
        out[k] = y
    return out

# -----------------------------------------------------------------------------
# 2. SUITE DE VERIFICACIÓN EMPÍRICA (TEST RUNNER)
# -----------------------------------------------------------------------------
def run_benchmarks():
    print("=== C5-REAL Q_RSQRT ULTRATHINK JIT/NEON BENCHMARK ===")

    # Warm up JIT
    _ = q_rsqrt_32_jit(123.456, 2)
    test_arr = np.random.uniform(0.1, 1000.0, 10).astype(np.float32)
    _ = q_rsqrt_vec32_numba(test_arr, 2)

    # Benchmark over 10 Million elements!
    N = 10_000_000
    print(f"Generando {N} números aleatorios en float32...")
    data = np.random.uniform(0.001, 100000.0, N).astype(np.float32)

    print("\n[1] NumPy Numpy Vectorized (1.0 / np.sqrt(x)) [BASELINE]")
    t0 = time.perf_counter()
    exact = 1.0 / np.sqrt(data)
    t1 = time.perf_counter()
    t_numpy = t1 - t0
    print(f"    -> {t_numpy:.5f} segundos")

    print("\n[2] Numba JIT Parallelized (Minimax + 2-Iter Newton)")
    t0 = time.perf_counter()
    numba_res = q_rsqrt_vec32_numba(data, iterations=2)
    t1 = time.perf_counter()
    t_numba = t1 - t0
    print(f"    -> {t_numba:.5f} segundos | Speedup vs Baseline: {t_numpy/t_numba:.2f}x")

    if neon_available:
        print("\n[3] ARM NEON Native Hardware (vrsqrteq_f32 + vrsqrtsq_f32)")
        t0 = time.perf_counter()
        neon_res = q_rsqrt_neon(data)
        t1 = time.perf_counter()
        t_neon = t1 - t0
        print(f"    -> {t_neon:.5f} segundos | Speedup vs Baseline: {t_numpy/t_neon:.2f}x")

        # Error check
        max_err_neon = np.max(np.abs(neon_res - exact) / exact) * 100
        print(f"    -> Max Relative Error (NEON): {max_err_neon:.6f}%")

    max_err_numba = np.max(np.abs(numba_res - exact) / exact) * 100
    print(f"    -> Max Relative Error (Numba): {max_err_numba:.6f}%")

    print("\n[C5-REAL] Benchmark de Ultra-Exergía Finalizado.")

if __name__ == "__main__":
    run_benchmarks()
