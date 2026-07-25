import json
from typing import Any

def canonical_serialize(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')