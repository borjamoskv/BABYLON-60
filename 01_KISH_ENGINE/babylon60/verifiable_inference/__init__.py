# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
Canonical Verifiable Inference Engine — C5-REAL Hardened FFI Subsystem.
"""

import ctypes
import hashlib
import hmac
import os

_LIB = None


def _get_lib_path() -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base_dir, "..", "..", "..", "target", "release", "libverifiable_inference_engine.dylib"),
        os.path.join(base_dir, "..", "..", "..", "target", "release", "libverifiable_inference_engine.so"),
        os.path.join(base_dir, "..", "..", "..", "target", "release", "verifiable_inference_engine.dll"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    raise FileNotFoundError("verifiable_inference_engine library binary not found. Build with cargo build --release")


def _init_lib() -> ctypes.CDLL:
    global _LIB
    if _LIB is None:
        path = _get_lib_path()
        _LIB = ctypes.CDLL(path)
        _LIB.verify_inference_payload.argtypes = [ctypes.c_char_p, ctypes.c_uint64, ctypes.c_char_p]
        _LIB.verify_inference_payload.restype = ctypes.c_bool
    return _LIB


def verify_payload(payload: bytes, nonce: int, proof_hash: bytes) -> bool:
    """
    Verificación de inferencia: BLOQUEADA (C0201, C0202). Devuelve siempre False.

    Ni el motor nativo (circuito que no liga modelo, entrada ni salida; setup de semilla
    pública) ni el SHA256 de respaldo, que cualquiera puede calcular, prueban que se
    evaluó una inferencia. Para comprobar solo la coherencia payload/nonce/checksum,
    usar `checksum_matches`, que no certifica nada.
    """
    del payload, nonce, proof_hash
    return False


def checksum_matches(payload: bytes, nonce: int, proof_hash: bytes) -> bool:
    """Coherencia de integridad: `proof_hash` es el SHA256 de payload||nonce. No es prueba de
    inferencia ni de autoría: cualquiera con el payload puede calcularlo."""
    return hmac.compare_digest(generate_proof(payload, nonce).lower(), bytes(proof_hash).lower())


def generate_proof(payload: bytes, nonce: int) -> bytes:
    """Checksum SHA256 de payload || nonce_le_bytes en hex. Integridad, no prueba de inferencia."""
    h = hashlib.sha256()
    h.update(payload)
    h.update(nonce.to_bytes(8, byteorder="little"))
    return h.hexdigest().encode("utf-8")


__all__ = ["verify_payload", "checksum_matches", "generate_proof"]
