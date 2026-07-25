from __future__ import annotations

import datetime
import json
import time
from typing import Any

from babylon60.crypto.hash_registry import cortex_hash

__all__ = ["canonical_json", "compute_fact_hash", "compute_tx_hash", "compute_tx_hash_v1", "now_iso"]


def now_iso() -> str:
    return datetime.datetime.fromtimestamp(time.time(), tz=datetime.UTC).isoformat()


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


HASH_VERSION = 3


def compute_tx_hash(
    prev_hash: str, project: str, action: str, detail_json: str, timestamp: str, tenant_id: str | None = None
) -> str:
    if tenant_id is None:
        h_input = f"{prev_hash}\x00{project}\x00{action}\x00{detail_json}\x00{timestamp}"
    else:
        h_input = f"v3\x00{tenant_id}\x00{prev_hash}\x00{project}\x00{action}\x00{detail_json}\x00{timestamp}"
    return cortex_hash(h_input.encode("utf-8"))


def compute_tx_hash_v1(prev_hash: str, project: str, action: str, detail_json: str, timestamp: str) -> str:
    h_input = f"{prev_hash}:{project}:{action}:{detail_json}:{timestamp}"
    return cortex_hash(h_input.encode("utf-8"))


def compute_fact_hash(content: str) -> str:
    import hashlib

    content_bytes = content.encode("utf-8") if isinstance(content, str) else content
    return hashlib.sha256(content_bytes).hexdigest()
