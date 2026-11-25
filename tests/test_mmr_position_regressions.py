"""Position binding and malformed packets; no persistent files or services."""

from copy import deepcopy
from typing import cast

import pytest
from babylon60.bft.cortex_crypto_kernel import MerkleMountainRange, MMRProofPacket


def fixture(size: int = 7) -> tuple[MerkleMountainRange, list[str]]:
    # Synthetic opaque 32-byte leaves, independent of any hash algorithm.
    leaves = [f"{index + 1:064x}" for index in range(size)]
    mmr = MerkleMountainRange()
    for leaf in leaves:
        mmr.append(leaf)
    return mmr, leaves


@pytest.mark.parametrize("size", [1, 2, 3, 4, 7, 8, 13, 31, 32, 63, 64])
def test_all_positions_verify(size: int) -> None:
    mmr, leaves = fixture(size)
    root = mmr.get_root()
    for index, leaf in enumerate(leaves):
        assert MerkleMountainRange.verify_proof(leaf, mmr.generate_proof(index), root)


@pytest.mark.parametrize("index", [-1, 0, 1, 3, 4, 6, 7, 999999, True])
def test_position_tampering_rejects(index: int) -> None:
    mmr, leaves = fixture()
    packet = mmr.generate_proof(2)
    packet["leaf_index"] = index
    assert not MerkleMountainRange.verify_proof(leaves[2], packet, mmr.get_root())


@pytest.mark.parametrize(
    "field,value",
    [
        ("leaf_index", "2"),
        ("total_leaves", 0),
        ("total_leaves", -1),
        ("total_leaves", True),
        ("total_leaves", 1 << 64),
        ("peak_index", -1),
        ("peak_index", 1),
        ("peak_index", True),
        ("mmr_root", "00" * 32),
        ("inner_proof", []),
        ("other_peaks", []),
    ],
)
def test_packet_shape_rejects(field: str, value: object) -> None:
    mmr, leaves = fixture()
    malformed: dict[str, object] = dict(mmr.generate_proof(2))
    malformed[field] = value
    assert not MerkleMountainRange.verify_proof(leaves[2], cast(MMRProofPacket, malformed), mmr.get_root())


@pytest.mark.parametrize(
    "field,value",
    [
        ("position", "unknown"),
        ("position", "left"),
        ("level", -1),
        ("level", 1),
        ("level", False),
        ("sibling", "xyz"),
        ("sibling", "00" * 31),
        ("sibling", "00" * 33),
    ],
)
def test_path_shape_rejects(field: str, value: object) -> None:
    mmr, leaves = fixture()
    packet = mmr.generate_proof(2)
    cast(dict[str, object], packet["inner_proof"][0])[field] = value
    assert not MerkleMountainRange.verify_proof(leaves[2], packet, mmr.get_root())


def test_bad_hashes_and_missing_fields_fail_closed() -> None:
    mmr, leaves = fixture()
    packet = mmr.generate_proof(2)
    for value in ["", "xyz", "00" * 31, "00" * 33]:
        assert not MerkleMountainRange.verify_proof(value, packet, mmr.get_root())
        assert not MerkleMountainRange.verify_proof(leaves[2], packet, value)
        malformed = deepcopy(packet)
        malformed["other_peaks"][0] = value
        assert not MerkleMountainRange.verify_proof(leaves[2], malformed, mmr.get_root())
    for field in packet:
        missing: dict[str, object] = dict(packet)
        del missing[field]
        assert not MerkleMountainRange.verify_proof(leaves[2], cast(MMRProofPacket, missing), mmr.get_root())


def test_rejection_stress_after_warmup() -> None:
    mmr, leaves = fixture(31)
    root = mmr.get_root()
    for _ in range(64):
        assert MerkleMountainRange.verify_proof(leaves[2], mmr.generate_proof(2), root)
    for iteration in range(512):
        index = iteration % len(leaves)
        packet = mmr.generate_proof(index)
        assert MerkleMountainRange.verify_proof(leaves[index], packet, root)
        packet["leaf_index"] = (index + 1) % len(leaves)
        assert not MerkleMountainRange.verify_proof(leaves[index], packet, root)
