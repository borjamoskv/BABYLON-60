from typing import Any

import cbor2


def canonical_serialize(payload: dict[str, Any]) -> bytes:
    def _clean_floats(obj: Any) -> Any:
        if isinstance(obj, float):
            raise ValueError("Floats are strictly prohibited in BFT consensus payloads.")
        if isinstance(obj, dict):
            return {k: _clean_floats(v) for k, v in sorted(obj.items())}
        if isinstance(obj, list):
            return [_clean_floats(v) for v in obj]
        return obj

    cleaned = _clean_floats(payload)
    return cbor2.dumps(cleaned)
