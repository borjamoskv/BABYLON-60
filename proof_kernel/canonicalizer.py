import hashlib
import json
from typing import Any

def canonicalize(evidence: dict[str, Any]) -> str:
    """
    Ω168 · Canonical Representation Invariant
    Convierte un subgrafo de evidencia en una cadena de texto canónica.
    Garantiza que grafos isomórficos generen la misma representación.
    """
    # Exclusión de determinismo de punto flotante en BFT (INV_C5_18)
    def _sanitize_floats(obj: Any) -> Any:
        if isinstance(obj, float):
            raise ValueError("Floating-point numbers are prohibited in C5-REAL canonical representation.")
        if isinstance(obj, dict):
            return {k: _sanitize_floats(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_sanitize_floats(i) for i in obj]
        return obj

    sanitized = _sanitize_floats(evidence)
    return json.dumps(sanitized, sort_keys=True, separators=(',', ':'))

def hash_evidence(evidence: dict[str, Any]) -> str:
    """
    Calcula el hash SHA3-256 de la evidencia canónica.
    """
    return hashlib.sha3_256(canonicalize(evidence).encode('utf-8')).hexdigest()
