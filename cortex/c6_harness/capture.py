# C5-REAL EXERGY CERTIFIED
"""C6-REAL State Capture & Fingerprinting.
Provides cryptographically verifiable StateCheckpoints (S0 -> H0 -> event_1 -> H1)
based on canonical schema extraction, isolating the identity from internal layout.
"""

import hashlib
import json
from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass
class StateCheckpoint:
    sequence_id: int
    event_cursor_offset: int
    state_hash: str
    parent_hash: str
    canonical_schema_version: int

    def to_yaml_str(self) -> str:
        return json.dumps(asdict(self), indent=2)


def generate_state_fingerprint(
    sequence_id: int, canonical_state: Dict[str, Any], event_offset: int, parent_hash: str, schema_version: int = 1
) -> StateCheckpoint:
    """
    Generates an immutable causal fingerprint for a state transition.
    The hash is derived EXCLUSIVELY from the canonical state dictionary,
    ensuring that same meaning = same hash, regardless of memory layout.
    """
    canonical_json = json.dumps(canonical_state, sort_keys=True)

    m = hashlib.sha3_256()
    m.update(parent_hash.encode("utf-8"))
    m.update(sequence_id.to_bytes(8, "big"))
    m.update(canonical_json.encode("utf-8"))
    m.update(schema_version.to_bytes(4, "big"))

    state_hash = m.hexdigest()

    return StateCheckpoint(
        sequence_id=sequence_id,
        state_hash=state_hash,
        event_cursor_offset=event_offset,
        parent_hash=parent_hash,
        canonical_schema_version=schema_version,
    )
