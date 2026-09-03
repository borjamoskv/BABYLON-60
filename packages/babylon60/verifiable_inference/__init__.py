# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
Canonical Verifiable Inference Engine — C5-REAL Hardened FFI Subsystem.
"""

import ctypes
import hashlib
import os
import sys

_LIB = None


def _get_lib_path() -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base_dir, "target", "release", "libverifiable_inference_engine.dylib"),
        os.path.join(base_dir, "target", "release", "libverifiable_inference_engine.so"),
        os.path.join(base_dir, "target", "release", "verifiable_inference_engine.dll"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    raise FileNotFoundError("verifiable_inference_engine library binary not found. Build with cargo build --release")


def _init_lib():
    global _LIB
    if _LIB is None:
        path = _get_lib_path()
        _LIB = ctypes.CDLL(path)
        _LIB.verify_inference_payload.argtypes = [ctypes.c_char_p, ctypes.c_uint64, ctypes.c_char_p]
        _LIB.verify_inference_payload.restype = ctypes.c_bool
    return _LIB


def verify_payload(payload: bytes, nonce: int, proof_hash: bytes) -> bool:
    """
    Verifica un payload contra su nonce y su hash de prueba mediante el motor nativo FFI.
    Si la biblioteca nativa FFI no se encuentra compilada, aplica fallback determinista en Python.

    Args:
        payload: Bytes del contenido estocástico.
        nonce: Nonce entero de 64 bits.
        proof_hash: Hash de prueba esperado (bytes hex utf-8).

    Returns:
        bool: True si la verificación fue exitosa, False en caso contrario.
    """
    try:
        lib = _init_lib()
        return bool(lib.verify_inference_payload(payload, nonce, proof_hash))
    except (FileNotFoundError, OSError):
        expected = generate_proof(payload, nonce)
        return expected.lower() == proof_hash.lower()


def generate_proof(payload: bytes, nonce: int) -> bytes:
    """Genera la prueba SHA256 canonical (payload || nonce_le_bytes) en formato hex bytes."""
    h = hashlib.sha256()
    h.update(payload)
    h.update(nonce.to_bytes(8, byteorder="little"))
    return h.hexdigest().encode("utf-8")


__all__ = ["verify_payload", "generate_proof"]
