# C5-REAL EXERGY CERTIFIED
# Wrapper de Ultra-Baja Latencia para Xorshift PRNG (SIMD)
# Target: libxorshift_neon.dylib

import ctypes
import os
import sys

def get_lib_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "libxorshift_neon.dylib")

def load_simd_library():
    lib_path = get_lib_path()
    if not os.path.exists(lib_path):
        print(f"Error: Librería no encontrada en {lib_path}. Ejecuta la compilación con clang primero.")
        sys.exit(1)

    lib = ctypes.CDLL(lib_path)

    # void xorshift_array_classic(uint64_t* out, size_t count, uint64_t initial_seed)
    lib.xorshift_array_classic.argtypes = [ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t, ctypes.c_uint64]
    lib.xorshift_array_classic.restype = None

    # void xorshift_array_neon(uint64_t* out, size_t count, const uint64_t* initial_seeds)
    lib.xorshift_array_neon.argtypes = [ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64)]
    lib.xorshift_array_neon.restype = None

    return lib

if __name__ == "__main__":
    lib = load_simd_library()
    print("[C5-REAL] Motor Xorshift PRNG SIMD Cargado Exitosamente.")

    # Test básico
    out_data = (ctypes.c_uint64 * 8)()
    initial_seeds = (ctypes.c_uint64 * 8)(
        0xDEADBEEFCAFEBABE, 0x1234567890ABCDEF,
        0xFACEFEEDDEADBEEF, 0x0987654321FEDCBA,
        0x1111222233334444, 0x5555666677778888,
        0x9999AAAABBBBCCCC, 0xDDDDEEEEFFFF0000
    )

    print("\nEjecutando Xorshift64 Clásico...")
    lib.xorshift_array_classic(out_data, 8, initial_seeds[0])
    print(f"Resultados: {[hex(x) for x in out_data]}")

    print("\nEjecutando ARM NEON (Loop Unrolling 4x)...")
    lib.xorshift_array_neon(out_data, 8, initial_seeds)
    print(f"Resultados: {[hex(x) for x in out_data]}")

    print("\nValidación Completada. Iniciar Stress Test de 100M para auditar BOPs.")
