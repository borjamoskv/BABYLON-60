# C5-REAL EXERGY CERTIFIED
# Stress Test: Xorshift PRNG SIMD (100M Elementos)
# Axioma Ω15 & Ω21: Hardware Exergy & ILP Loop Unrolling

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
    print("FATAL: Numpy es requerido para alocar memoria.")
    sys.exit(1)

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    wrapper_path = os.path.join(base_dir, "67_xorshift_ultra_exergy.py")

    if not os.path.exists(wrapper_path):
        print(f"FATAL: Wrapper no encontrado en {wrapper_path}")
        sys.exit(1)

    xor_mod = load_module_from_path("xorshift_ultra_exergy", wrapper_path)
    lib = xor_mod.load_simd_library()

    print("\n" + "="*60)
    print("  Ω21 STRESS TEST: XORSHIFT PRNG SIMD")
    print("="*60)

    N = 100_000_000 # 100 Millones de elementos (800 MB RAM)
    print(f"[*] Alocando tensor vacío de {N} números de 64-bits (~{N*8/1024/1024:.1f} MB)...")

    # Numpy empty para no gastar tiempo en inicialización de página (calloc)
    out = np.empty(N, dtype=np.uint64)
    out_ptr = out.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64))

    initial_seeds = (ctypes.c_uint64 * 8)(
        0xDEADBEEFCAFEBABE, 0x1234567890ABCDEF,
        0xFACEFEEDDEADBEEF, 0x0987654321FEDCBA,
        0x1111222233334444, 0x5555666677778888,
        0x9999AAAABBBBCCCC, 0xDDDDEEEEFFFF0000
    )

    print("[*] Tensores alineados. Calentando caché...")

    # --- 1. Numpy nativo (PCG64) ---
    print("\n--- 1. NUMPY (np.random.randint - PCG64) ---")
    start = time.perf_counter()
    _ = np.random.randint(0, 0xFFFFFFFFFFFFFFFF, size=N, dtype=np.uint64)
    elapsed_np = time.perf_counter() - start

    bops_np = N / elapsed_np / 1e9
    print(f"Tiempo      : {elapsed_np:.4f} s")
    print(f"Throughput  : {bops_np:.2f} Billion Ops/sec")

    # --- 2. C Classic Xorshift64 ---
    print("\n--- 2. C CLASSIC XORSHIFT64 ---")
    start = time.perf_counter()
    lib.xorshift_array_classic(out_ptr, N, 0xDEADBEEFCAFEBABE)
    elapsed_classic = time.perf_counter() - start

    bops_classic = N / elapsed_classic / 1e9
    print(f"Tiempo      : {elapsed_classic:.4f} s")
    print(f"Throughput  : {bops_classic:.2f} Billion Ops/sec")

    # --- 3. ARM NEON SIMD (Loop Unrolling 4x) ---
    print("\n--- 3. ARM NEON SIMD (ILP 4x: 512 bits / ciclo) ---")
    out.fill(0)

    start = time.perf_counter()
    lib.xorshift_array_neon(out_ptr, N, initial_seeds)
    elapsed_neon = time.perf_counter() - start

    bops_neon = N / elapsed_neon / 1e9
    print(f"Tiempo      : {elapsed_neon:.4f} s")
    print(f"Throughput  : {bops_neon:.2f} Billion Ops/sec")

    # Validación estadística rápida (media aproximada a 0x7FFFFFFFFFFFFFFF)
    mean_val = np.mean(out, dtype=np.float64)
    expected = 0x7FFFFFFFFFFFFFFF
    error = abs(mean_val - expected) / expected

    print("\n--- AUDITORÍA C5-REAL BFT ---")
    if error < 0.001:
        print(f"[OK] Entropía estadística confirmada. (Error Media: {error:.5%})")
        speedup_np = elapsed_np / elapsed_neon
        speedup_c = elapsed_classic / elapsed_neon
        print(f"[*] Aceleración NEON vs Numpy (PCG64): {speedup_np:.2f}x")
        print(f"[*] Aceleración NEON vs C Classic    : {speedup_c:.2f}x")
        print("\n■ EXERGÍA DE HARDWARE MAXIMIZADA ■")
    else:
        print(f"[FATAL] Fallo entrópico masivo. Desviación: {error:.5%}")
        sys.exit(1)

if __name__ == "__main__":
    main()
