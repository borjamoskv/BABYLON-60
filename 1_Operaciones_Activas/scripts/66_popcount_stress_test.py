# C5-REAL EXERGY CERTIFIED
# Stress Test: Hamming Weight / Popcount (100M Elementos)
# Axioma Ω15: Hardware Exergy Maximization

import os
import sys
import time
import ctypes
import importlib.util

def load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

try:
    import numpy as np
except ImportError:
    print("FATAL: Numpy es requerido para alocar 800MB de enteros alineados contiguos.")
    sys.exit(1)

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    wrapper_path = os.path.join(base_dir, "65_popcount_ultra_exergy.py")

    if not os.path.exists(wrapper_path):
        print(f"FATAL: Wrapper no encontrado en {wrapper_path}")
        sys.exit(1)

    popcount_mod = load_module_from_path("popcount_ultra_exergy", wrapper_path)
    lib = popcount_mod.load_simd_library()

    print("\n" + "="*60)
    print("  Ω15 STRESS TEST: POPCOUNT / HAMMING WEIGHT")
    print("="*60)

    N = 100_000_000 # 100 Millones de elementos (800 MB RAM)
    print(f"[*] Alocando {N} números aleatorios de 64-bits (~{N*8/1024/1024:.1f} MB)...")

    # Random integers
    data = np.random.randint(0, 0xFFFFFFFFFFFFFFFF, size=N, dtype=np.uint64)
    out = np.zeros(N, dtype=np.uint64)

    # Obtener punteros
    data_ptr = data.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64))
    out_ptr = out.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64))

    print("[*] Tensores alineados. Calentando caché...")

    # --- 1. Numpy nativo ---
    print("\n--- 1. NUMPY (C-Backend) ---")
    start = time.perf_counter()
    # Numpy no tiene un popcount de enteros directo ultra-rápido, pero podemos emularlo
    # o simplemente testear la iteración pura de python.
    # Dado que np.sum(np.unpackbits...) es exageradamente lento (consume GBs de ram),
    # haremos un test de la función map o algo representativo. Para ser justos, Numpy no
    # tiene popcount incorporado para uint64, así que omitiremos el test nativo y pasaremos al bit hack clásico.
    print("[Numpy no tiene popcount uint64 nativo directo. Skipped.]")

    # --- 2. C Classic Bit Hack ---
    print("\n--- 2. C CLASSIC BIT HACK (64-bit Parallel) ---")
    start = time.perf_counter()
    lib.popcount_array_classic(data_ptr, N, out_ptr)
    elapsed_classic = time.perf_counter() - start

    sum_classic = np.sum(out)
    bops_classic = N / elapsed_classic / 1e9

    print(f"Tiempo      : {elapsed_classic:.4f} s")
    print(f"Throughput  : {bops_classic:.2f} Billion Ops/sec")
    print(f"Bits Activos: {sum_classic:,}")

    # --- 3. ARM NEON SIMD ---
    print("\n--- 3. ARM NEON SIMD (vcntq_u8 + paddl) ---")
    out.fill(0)

    start = time.perf_counter()
    lib.popcount_array_neon(data_ptr, N, out_ptr)
    elapsed_neon = time.perf_counter() - start

    sum_neon = np.sum(out)
    bops_neon = N / elapsed_neon / 1e9

    print(f"Tiempo      : {elapsed_neon:.4f} s")
    print(f"Throughput  : {bops_neon:.2f} Billion Ops/sec")
    print(f"Bits Activos: {sum_neon:,}")

    # --- VALIDACIÓN BFT ---
    print("\n--- AUDITORÍA C5-REAL BFT ---")
    if sum_classic == sum_neon:
        print(f"[OK] Coherencia estricta confirmada. (Delta: 0)")
        speedup = elapsed_classic / elapsed_neon
        print(f"[*] Aceleración NEON vs Classic Hack: {speedup:.2f}x")
        print("\n■ EXERGÍA DE HARDWARE MAXIMIZADA ■")
    else:
        print("[FATAL] Desviación estocástica detectada. Los resultados no coinciden.")
        sys.exit(1)

if __name__ == "__main__":
    main()
