"""H06: Merkle membership must bind the complete, cardinality-valid path."""

import hashlib
from typing import cast

import pytest

from babylon60.bft.cortex_crypto_kernel import (
    build_merkle_tree,
    generate_merkle_proof,
    verify_merkle_proof,
)
from babylon60.bft.cortex_persist_ledger import CortexPersistLedger


def _leaves(count: int) -> list[str]:
    return [hashlib.sha3_256(f"audit-event-{i}".encode()).hexdigest() for i in range(count)]


def test_internal_node_cannot_claim_leaf_membership() -> None:
    leaves = _leaves(2)
    root = build_merkle_tree(leaves)
    internal = hashlib.sha3_256(b"\x00" + b"".join(bytes.fromhex(h) for h in leaves)).hexdigest()
    assert internal not in leaves
    assert not verify_merkle_proof(internal, [], root, 2)


@pytest.mark.parametrize("count", [1, 2, 3, 4, 5, 7, 8, 9, 13, 16, 17, 31, 32, 33])
def test_legitimate_paths_keep_legacy_and_packet_compatibility(count: int) -> None:
    leaves = _leaves(count)
    root = build_merkle_tree(leaves)
    for index, leaf in enumerate(leaves):
        packet = generate_merkle_proof(leaves, index)
        assert verify_merkle_proof(leaf, packet["proof"], root, count)
        assert CortexPersistLedger.verify_event_proof(packet, root)


def test_packet_index_is_bound_even_for_identical_leaves() -> None:
    leaf = _leaves(1)[0]
    leaves = [leaf, leaf]
    packet = generate_merkle_proof(leaves, 0)
    packet["target_index"] = 1
    assert not CortexPersistLedger.verify_event_proof(packet, build_merkle_tree(leaves))


@pytest.mark.parametrize("index", [-1, 3, 4, None, True])
def test_packet_index_must_be_in_range(index: int | None) -> None:
    leaves = _leaves(3)
    packet = generate_merkle_proof(leaves, 2)
    packet["target_index"] = cast(int, index)
    assert not CortexPersistLedger.verify_event_proof(packet, build_merkle_tree(leaves))


@pytest.mark.parametrize("level", [-1, 0, 2, 999])
def test_level_must_match_its_depth(level: int) -> None:
    leaves = _leaves(4)
    packet = generate_merkle_proof(leaves, 0)
    packet["proof"][1]["level"] = level
    assert not CortexPersistLedger.verify_event_proof(packet, build_merkle_tree(leaves))


def test_unknown_orientation_is_rejected() -> None:
    leaves = _leaves(2)
    packet = generate_merkle_proof(leaves, 0)
    packet["proof"][0]["position"] = "anything"
    assert not CortexPersistLedger.verify_event_proof(packet, build_merkle_tree(leaves))


def test_duplicate_padding_cannot_be_claimed_as_an_extra_leaf() -> None:
    leaves = _leaves(3)
    packet = generate_merkle_proof(leaves, 2)
    packet["proof"][0]["position"] = "left"
    assert not verify_merkle_proof(leaves[2], packet["proof"], build_merkle_tree(leaves), 3)


@pytest.mark.parametrize("count", [-1, 0, 1 << 64, True])
def test_invalid_cardinality_returns_false(count: int) -> None:
    leaf = _leaves(1)[0]
    assert not verify_merkle_proof(leaf, [], build_merkle_tree([leaf]), count)


@pytest.mark.parametrize("extra", [False, True])
def test_incorrect_path_length_is_rejected(extra: bool) -> None:
    leaves = _leaves(4)
    packet = generate_merkle_proof(leaves, 0)
    if extra:
        packet["proof"].append(packet["proof"][-1].copy())
    else:
        packet["proof"].pop()
    assert not CortexPersistLedger.verify_event_proof(packet, build_merkle_tree(leaves))


def test_odd_padding_must_duplicate_the_current_node() -> None:
    leaves = _leaves(3)
    packet = generate_merkle_proof(leaves, 2)
    packet["proof"][0]["sibling"] = leaves[0]
    # Construct a matching digest for this noncanonical three-leaf shape.
    current = bytes.fromhex(leaves[2])
    for level, step in enumerate(packet["proof"]):
        sibling = bytes.fromhex(step["sibling"])
        pair = sibling + current if step["position"] == "left" else current + sibling
        current = hashlib.sha3_256((b"\x00" if level == 0 else b"\x01") + pair).digest()
    forged_root = hashlib.sha3_256(b"\x02" + current + (3).to_bytes(8, "little")).hexdigest()
    assert not CortexPersistLedger.verify_event_proof(packet, forged_root)


@pytest.mark.parametrize("digest", ["", "invalid", "0" * 62, "0" * 66])
def test_malformed_hashes_return_false(digest: str) -> None:
    leaves = _leaves(2)
    root = build_merkle_tree(leaves)
    packet = generate_merkle_proof(leaves, 0)
    assert not verify_merkle_proof(digest, packet["proof"], root, 2)
    assert not verify_merkle_proof(leaves[0], packet["proof"], digest, 2)
    packet["proof"][0]["sibling"] = digest
    assert not verify_merkle_proof(leaves[0], packet["proof"], root, 2)
