# [C5-REAL] Exergy-Maximized
"""
Canonical serialization for cryptographic hashing.
"""

import json
from typing import Any


def canonical_serialize(payload: dict[str, Any]) -> bytes:
    """
    Serialización canónica para Hashes C5-REAL.
    - Claves ordenadas alfabéticamente.
    - Sin espacios superfluos.
    - UTF-8 garantizado.
    """
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
