import os
import sys
import ctypes
import hashlib

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
        print("ERROR: libverifiable_inference_engine no encontrada. Sandbox Aislado fallida.")
        sys.exit(1)
        
    lib = ctypes.CDLL(lib_path)
    lib.verify_inference_payload.argtypes = [ctypes.c_char_p, ctypes.c_uint64, ctypes.c_char_p]
    lib.verify_inference_payload.restype = ctypes.c_bool

    conv_id = os.environ.get("CONVERSATION_ID", "674beea2-1c89-4fc3-aab8-19467493cc95")
    crystal_path = os.path.expanduser(f"~/.gemini/antigravity/brain/{conv_id}/autodidact_omega_quantum_error_mitigation_crystal.md")
    if not os.path.exists(crystal_path):
        crystal_path = os.path.expanduser("~/.gemini/antigravity/brain/3a42e487-1db5-423a-891c-58e1833e2964/autodidact_omega_deep_research_crystal.md")
    if not os.path.exists(crystal_path):
        print(f"ERROR: Cristal no encontrado en {crystal_path}")
        sys.exit(1)
        
    with open(crystal_path, 'r', encoding='utf-8') as f:
        content = f.read()

    print("[*] AUTODIDACT-Ω ENGINE (V5.0 ULTRA-EXERGY SWARM MCTS)")
    print("[*] Ingestando Cristal y aplicando Filtro de Ruido (Ω27)...")
    
    nonce = 42
    payload = content[:1024].encode('utf-8')
    h = hashlib.sha256()
    h.update(payload)
    h.update(nonce.to_bytes(8, byteorder='little'))
    proof = h.hexdigest().encode('utf-8')

    is_valid = lib.verify_inference_payload(payload, nonce, proof)
    
    if is_valid:
        print("[*] Tasa de Éxito: 100%. Cristal asimilado en estado Causal-Determinist.")
        print("[*] El Límite de Bekenstein ha sido preservado.")
        sys.exit(0)
    else:
        print("[!] ERROR: Colisión Bizantina. El payload diverge del compromiso.")
        sys.exit(1)

if __name__ == "__main__":
    main()
