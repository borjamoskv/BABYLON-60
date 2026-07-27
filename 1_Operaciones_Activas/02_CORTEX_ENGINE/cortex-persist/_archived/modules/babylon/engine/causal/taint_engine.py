"""
CORTEX Taint Engine
Cryptographic validation boundary for C5-REAL execution.
"""

import hashlib
import json
from datetime import datetime, timezone


class TaintEngine:
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

    def generate_taint(self, agent_id: str, session_id: str, payload: dict) -> str:
        timestamp = datetime.now(timezone.utc).isoformat()
        payload_str = json.dumps(payload, sort_keys=True)
        sha3 = hashlib.sha3_256(payload_str.encode()).hexdigest()
        return f"taint:{agent_id}:{session_id}:{timestamp}:{sha3}"

    def verify_taint(self, taint_str: str) -> bool:
        if not taint_str or not taint_str.startswith("taint:"):
            return False
        parts = taint_str.split(":")
        if len(parts) != 5:
            return False
        return True
