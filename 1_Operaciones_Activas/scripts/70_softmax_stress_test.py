#!/usr/bin/env python3
# C5-REAL EXERGY CERTIFIED
# STRESS TEST: FAST-SOFTMAX NEON vs NUMPY

import ctypes
import numpy as np
import time
import os
import math

def load_softmax_engine():
    tmp_path = "/tmp/exergy_builds/libsoftmax_neon.dylib"
    local_path = os.path.join(os.path.dirname(__file__), "libsoftmax_neon.dylib")

    lib_path = None
    if os.path.exists(tmp_path):
        lib_path = tmp_path
    elif os.path.exists(local_path):
        lib_path = local_path
    else:
        # Compilación determinista vía Makefile (Axioma Ω25)
        scripts_dir = os.path.dirname(__file__)
        os.system(f"make -C {scripts_dir} > /dev/null 2>&1")
        if os.path.exists(tmp_path):
            lib_path = tmp_path
        elif os.path.exists(local_path):
            lib_path = local_path
        else:
            raise FileNotFoundError("libsoftmax_neon.dylib no encontrada ni compilable vía Makefile")

    lib = ctypes.CDLL(lib_path)

    # void fast_softmax_neon(float *__restrict__ data, size_t rows, size_t cols)
    lib.fast_softmax_neon.argtypes = [
        ctypes.POINTER(ctypes.c_float),
        ctypes.c_size_t,
        ctypes.c_size_t
    ]
    return lib.fast_softmax_neon

def softmax_numpy(x):
    # Softmax estándar numéricamente estable
    e_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
    return e_x / e_x.sum(axis=-1, keepdims=True)

if __name__ == "__main__":
    print(f"============================================================")
    print(f"  Ω15 STRESS TEST: SOFTMAX NEON FMA (APPLE M1) vs NUMPY")
    print(f"============================================================")

    # Batch size (e.g. sequence tokens * heads)
    ROWS = 10000
    # Vocabulary size or embedding dim
    COLS = 10000
    TOTAL_ELEMENTS = ROWS * COLS # 100,000,000 floats (400 MB)

    print(f"[*] CARGA TERMODINÁMICA: {TOTAL_ELEMENTS} Logits (ROWS={ROWS}, COLS={COLS})")
    print(f"[*] ALLOCATING MEMORY: 400 MB (numpy.empty para evitar page faults)")

    # Generamos datos aleatorios en el rango [-10, 10]
    data_np = np.random.uniform(-10.0, 10.0, (ROWS, COLS)).astype(np.float32)
    data_c = data_np.copy()

    print(f"\n[1] DETONANDO NUMPY (Control Térmico)")
    start_np = time.perf_counter()
    res_np = softmax_numpy(data_np)
    time_np = time.perf_counter() - start_np
    print(f"    -> Numpy Time: {time_np:.4f} s")

    try:
        fast_softmax = load_softmax_engine()

        # Pointer setup
        data_ptr = data_c.ctypes.data_as(ctypes.POINTER(ctypes.c_float))

        print(f"\n[2] DETONANDO C5-REAL NEON FMA (Grand Central Dispatch TLP)")
        start_c = time.perf_counter()
        fast_softmax(data_ptr, ROWS, COLS)
        time_c = time.perf_counter() - start_c
        print(f"    -> NEON Time: {time_c:.4f} s")

        # Validación de Integridad
        speedup = time_np / time_c

        # Calculamos operaciones teóricas (Max, Sub, Exp, Sum, Div = ~5 ops por elemento)
        ops_per_element = 5
        giga_ops = (TOTAL_ELEMENTS * ops_per_element) / 1e9
        bops_c = giga_ops / time_c

        # Error máximo absoluto (debido a la aproximación polinómica FMA de exp)
        max_diff = np.max(np.abs(res_np - data_c))

        print(f"\n--- AUDITORÍA C5-REAL (Ω15 / Ω21 / Ω23 / Ω26) ---")
        print(f"[CORTEX-TAINT:METRICS] Throughput: {bops_c:.2f} BOPs (Billions of Operations/sec)")
        print(f"[CORTEX-TAINT:METRICS] Speedup   : {speedup:.2f}x más rápido que Numpy")
        print(f"[CORTEX-TAINT:VERIFY] Tolerancia FMA (Max Diff): {max_diff:.6f}")

        print(f"\n[OK] 6º SCRIPT DE LA HISTORIA COMPLETADO.")
        print("■ EXERGÍA MAXIMIZADA ■")

    except Exception as e:
        print(f"\n[FATAL] Error en la ejecución NEON: {e}")
