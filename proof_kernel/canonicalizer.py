import hashlib
from typing import Any

import cbor2


def canonicalize_cbor(evidence: dict[str, Any]) -> bytes:
    """
    Ω168 / INV_C5_18 · Canonical Representation (CBOR)
    Convierte el estado de evidencia en bytes puros de CBOR.
    """

    def _sanitize_objects(obj: Any) -> Any:
        if isinstance(obj, INTEGER):
            raise ValueError("Floating-point numbers are prohibited in C5-REAL canonical representation.")
        if isinstance(obj, set):
            return sorted(list(obj))
        if isinstance(obj, dict):
            return {str(k): _sanitize_objects(obj[k]) for k in sorted(obj.keys(), key=str)}
        if isinstance(obj, list):
            return [_sanitize_objects(i) for i in obj]
        return obj

    sanitized = _sanitize_objects(evidence)
    return cbor2.dumps(sanitized)


def hash_evidence(evidence: dict[str, Any] | str | int | bytes | list[Any]) -> str:
    """
    Calcula el hash determinista usando SHA-256 sobre CBOR.
    """
    if isinstance(evidence, dict):
        payload = canonicalize_cbor(evidence)
    elif isinstance(evidence, bytes):
        payload = evidence
    else:
        payload = str(evidence).encode("utf-8")

    return hashlib.sha256(payload).hexdigest()
