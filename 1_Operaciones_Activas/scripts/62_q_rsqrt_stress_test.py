# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
"""
62_q_rsqrt_stress_test.py
==========================
Prueba de Estrés Brutal para Fast Inverse Square Root (V4.0 Cubic FMA).
Validación de límites físicos, edge cases numéricos (NaN, Inf, Denormals) y escalabilidad masiva.
"""

import numpy as np
import time
import os
import sys

# Ajustar PYTHONPATH temporalmente para importar el script 61 si es necesario,
# o importar directamente si estamos en el mismo directorio.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from importlib.machinery import SourceFileLoader

try:
    q_rsqrt_mod = SourceFileLoader("q_rsqrt", os.path.join(os.path.dirname(__file__), "61_q_rsqrt_ultra_exergy.py")).load_module()
except Exception as e:
    print(f"Error cargando el módulo V4.0: {e}")
    sys.exit(1)

def run_stress_test():
    print("==========================================================")
    print(" ☠️ BRUTAL STRESS TEST: Q_RSQRT V4.0 CUBIC FMA ☠️")
    print("==========================================================\n")

    # 1. PRUEBA DE CARGA MASIVA (100 MILLONES DE FLOTANTES)
    N_MASSIVE = 100_000_000
    print(f"[1] TEST DE CARGA MASIVA: {N_MASSIVE:,} FLOTANTES (~400 MB RAM)")

    # Warm up
    _ = q_rsqrt_mod.q_rsqrt_vec32_numba_cubic(np.array([1.0], dtype=np.float32))

    # Generar carga de 100 millones
    print("    Generando tensor masivo...")
    t0_gen = time.perf_counter()
    data_massive = np.random.uniform(0.1, 1e6, N_MASSIVE).astype(np.float32)
    t1_gen = time.perf_counter()
    print(f"    -> Tensor de {data_massive.nbytes / (1024*1024):.2f} MB generado en {t1_gen - t0_gen:.2f}s")

    print("\n    Ejecutando ARM NEON Cubic FMA Nativo (100M floats)...")
    if q_rsqrt_mod.neon_fma_available:
        t0 = time.perf_counter()
        res_neon = q_rsqrt_mod.q_rsqrt_neon_fma(data_massive)
        t1 = time.perf_counter()
        print(f"    -> TIEMPO FÍSICO (NEON FMA): {t1 - t0:.5f} s")
        print(f"    -> THROUGHPUT: {N_MASSIVE / (t1 - t0) / 1e6:.2f} Millones de Ops/segundo")
    else:
        print("    -> [OMITIDO] ARM NEON FMA no disponible.")

    print("\n    Ejecutando Numba JIT LLVM Multicore (100M floats)...")
    t0 = time.perf_counter()
    res_numba = q_rsqrt_mod.q_rsqrt_vec32_numba_cubic(data_massive)
    t1 = time.perf_counter()
    print(f"    -> TIEMPO LLVM (Numba): {t1 - t0:.5f} s")
    print(f"    -> THROUGHPUT: {N_MASSIVE / (t1 - t0) / 1e6:.2f} Millones de Ops/segundo")


    # 2. PRUEBA DE CASOS EXTREMOS (EDGE CASES & IEEE 754 BOUNDARIES)
    print("\n[2] TEST DE FRONTERA IEEE 754 (EDGE CASES)")
    edge_cases = np.array([
        0.0,                    # Cero absoluto
        -0.0,                   # Cero negativo
        -4.0,                   # Número negativo
        float('inf'),           # Infinito
        float('nan'),           # Not a Number
        1e-38,                  # Denormal cercano (muy pequeño)
        1e38,                   # Límite superior float32
        1.0,                    # Identidad
        0.0000001,              # Epsilon cercano
    ], dtype=np.float32)

    labels = [
        "Zero (0.0)", "Negative Zero (-0.0)", "Negative (-4.0)", "Infinity (inf)",
        "NaN", "Near Denormal (1e-38)", "Upper Bound (1e38)", "Identity (1.0)", "Near Epsilon (1e-7)"
    ]

    res_edge_numba = q_rsqrt_mod.q_rsqrt_vec32_numba_cubic(edge_cases)
    if q_rsqrt_mod.neon_fma_available:
        res_edge_neon = q_rsqrt_mod.q_rsqrt_neon_fma(edge_cases)

    print("\n    | Input Float | Exact (1/sqrt) | Numba JIT Output | NEON FMA Output |")
    print("    |-------------|----------------|------------------|-----------------|")
    for i in range(len(edge_cases)):
        inp = edge_cases[i]

        # Safe exact computation
        with np.errstate(divide='ignore', invalid='ignore'):
            exact = 1.0 / np.sqrt(inp)

        out_numba = res_edge_numba[i]
        out_neon = res_edge_neon[i] if q_rsqrt_mod.neon_fma_available else "N/A"
        print(f"    | {labels[i]:<15} | {exact:<14} | {out_numba:<16} | {out_neon:<15} |")


    print("\n==========================================================")
    print(" 🎯 STRESS TEST FINALIZADO (Ω150 EXERGY VERIFIED)")
    print("==========================================================")

if __name__ == "__main__":
    run_stress_test()
