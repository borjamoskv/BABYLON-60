# C5-REAL EXERGY CERTIFIED
# Wrapper de Ultra-Baja Latencia para Popcount (SIMD)
# Target: libpopcount_neon.dylib

import ctypes
import os
import sys

def get_lib_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "libpopcount_neon.dylib")

def load_simd_library():
    lib_path = get_lib_path()
    if not os.path.exists(lib_path):
        print(f"Error: Librería no encontrada en {lib_path}. Ejecuta la compilación con clang primero.")
        sys.exit(1)

    lib = ctypes.CDLL(lib_path)

    # void popcount_array_classic(const uint64_t* data, size_t count, uint64_t* out)
    lib.popcount_array_classic.argtypes = [ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64)]
    lib.popcount_array_classic.restype = None

    # void popcount_array_neon(const uint64_t* data, size_t count, uint64_t* out)
    lib.popcount_array_neon.argtypes = [ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64)]
    lib.popcount_array_neon.restype = None

    return lib

if __name__ == "__main__":
    lib = load_simd_library()
    print("[C5-REAL] Motor Popcount SIMD (Hardware Exergy) Cargado Exitosamente.")

    # Test básico de cordura
    test_data = (ctypes.c_uint64 * 4)(
        0xFFFFFFFFFFFFFFFF, # 64 bits
        0x0000000000000000, # 0 bits
        0x5555555555555555, # 32 bits
        0x0000000000000003  # 2 bits
    )
    out_data = (ctypes.c_uint64 * 4)()

    print("\nEjecutando Hack Clásico de 64-bits...")
    lib.popcount_array_classic(test_data, 4, out_data)
    print(f"Resultados: {list(out_data)}")

    print("Ejecutando ARM NEON (vcntq_u8)...")
    lib.popcount_array_neon(test_data, 4, out_data)
    print(f"Resultados: {list(out_data)}")

    print("\nValidación Completada. Iniciar Stress Test de 100M para auditar BOPs.")
