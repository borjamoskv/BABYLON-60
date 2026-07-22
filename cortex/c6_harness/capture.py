"""C6-REAL State Capture & Fingerprinting.
Provides cryptographically verifiable StateCheckpoints (S0 -> H0 -> event_1 -> H1).
"""
import hashlib
import time
import json
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class StateCheckpoint:
    sequence_id: int
    timestamp_ns: int
    state_hash: str
    wal_position_frame: int
    event_cursor_offset: int
    parent_hash: str

    def to_yaml_str(self) -> str:
        # A simple JSON/YAML representation for the auditor
        return json.dumps(asdict(self), indent=2)

def generate_state_fingerprint(
    sequence_id: int, 
    payload: bytes, 
    wal_frame: int, 
    event_offset: int, 
    parent_hash: str
) -> StateCheckpoint:
    """Generates an immutable causal fingerprint for a state transition."""
    m = hashlib.sha3_256()
    m.update(parent_hash.encode('utf-8'))
    m.update(sequence_id.to_bytes(8, 'big'))
    m.update(payload)
    
    state_hash = m.hexdigest()
    
    return StateCheckpoint(
        sequence_id=sequence_id,
        timestamp_ns=time.perf_counter_ns(),
        state_hash=state_hash,
        wal_position_frame=wal_frame,
        event_cursor_offset=event_offset,
        parent_hash=parent_hash
    )
