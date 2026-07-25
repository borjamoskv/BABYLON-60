# C5-REAL EXERGY CERTIFIED
"""C6.1 Checkpoint Hashing Unit Test."""

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from cortex.c6_harness.capture import generate_state_fingerprint

def test_canonical_schema_hashing() -> None:
    print("Running C6.1 Canonical Schema Hashing Test...")
    parent_hash = "0000000000000000000000000000000000000000000000000000000000000000"

    # State A and State B have different memory layouts (dict key order) but same meaning
    state_a = {"users": 5, "balance": 100}
    state_b = {"balance": 100, "users": 5}

    cp_a = generate_state_fingerprint(1, state_a, 100, parent_hash, 1)
    cp_b = generate_state_fingerprint(1, state_b, 100, parent_hash, 1)

    assert cp_a.state_hash == cp_b.state_hash, "Hash diverges based on layout! (Anergía)"
    print("✓ Canonical Schema Hashing: PASS")

if __name__ == "__main__":
    test_canonical_schema_hashing()
