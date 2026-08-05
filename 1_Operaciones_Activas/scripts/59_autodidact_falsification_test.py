# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import os
import sys
import ctypes

lib_dir = os.path.join(os.path.dirname(__file__), "..", "verifiable_inference_suite")


def get_lib_path():
    dylib_path = os.path.join(lib_dir, "target", "release", "libverifiable_inference_engine.dylib")
    so_path = os.path.join(lib_dir, "target", "release", "libverifiable_inference_engine.so")
    if os.path.exists(dylib_path):
        return dylib_path
    if os.path.exists(so_path):
        return so_path
    return None


def main():
    lib_path = get_lib_path()
    if not lib_path:
        print("FAIL: FFI library missing.")
        sys.exit(1)

    lib = ctypes.CDLL(lib_path)
    lib.verify_inference_payload.argtypes = [ctypes.c_char_p, ctypes.c_uint64, ctypes.c_char_p]
    lib.verify_inference_payload.restype = ctypes.c_bool

    print("[*] TEST DE FALSACIÓN POPPERIANA (Ω22)")

    fake_payload = b"Este es un reporte incompleto generado por una alucinacion C4-SIM."
    nonce = 9999
    corrupted_proof = b"a1b2c3d4e5f60000000000000000000000000000000000000000000000000000"

    is_valid = lib.verify_inference_payload(fake_payload, nonce, corrupted_proof)

    if is_valid:
        print("[!] ERROR CRÍTICO: El auditor aceptó un artefacto incompleto. Vulneración Causal-Determinist.")
        sys.exit(1)
    else:
        print("[*] FAIL DETECTADO CORRECTAMENTE: El auditor rechazó el holograma sintáctico.")
        print("[*] El principio de falsación se mantiene (Ω22 Verified).")
        sys.exit(0)


if __name__ == "__main__":
    main()
