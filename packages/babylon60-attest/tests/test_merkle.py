# C5-REAL EXERGY CERTIFIED
"""Tests for the Merkle tree module."""
from babylon60_attest.merkle import MerkleTree, sha3_256, sha3_256_str, BLOCK_SIZE


def test_sha3_256_deterministic():
    """Identical inputs produce identical digests."""
    assert sha3_256(b"hello") == sha3_256(b"hello")
    assert sha3_256(b"hello") != sha3_256(b"world")


def test_sha3_256_str_utf8():
    """String hashing uses UTF-8 encoding."""
    assert sha3_256_str("hello") == sha3_256("hello".encode("utf-8"))


def test_merkle_single_leaf():
    """A single-leaf tree has the leaf as root."""
    leaf = sha3_256(b"only leaf")
    tree = MerkleTree([leaf])
    assert tree.root == leaf
    assert tree.leaf_count == 1
    assert tree.depth == 0


def test_merkle_two_leaves():
    """Two leaves produce a single-level tree."""
    a = sha3_256(b"a")
    b = sha3_256(b"b")
    tree = MerkleTree([a, b])
    assert tree.leaf_count == 2
    assert tree.depth == 1
    expected_root = sha3_256((a + b).encode("ascii"))
    assert tree.root == expected_root


def test_merkle_odd_leaves():
    """Odd number of leaves: last leaf is duplicated for pairing."""
    a = sha3_256(b"a")
    b = sha3_256(b"b")
    c = sha3_256(b"c")
    tree = MerkleTree([a, b, c])
    assert tree.leaf_count == 3
    assert tree.depth == 2


def test_merkle_from_bytes():
    """from_bytes partitions data into blocks and builds the tree."""
    data = b"x" * (BLOCK_SIZE * 3 + 100)
    tree = MerkleTree.from_bytes(data)
    assert tree.leaf_count == 4  # 3 full blocks + 1 partial
    assert tree.root


def test_merkle_from_bytes_empty():
    """Empty bytes produce a valid single-leaf tree."""
    tree = MerkleTree.from_bytes(b"")
    assert tree.leaf_count == 1
    assert tree.root


def test_merkle_from_strings():
    """from_strings creates leaves from UTF-8 strings."""
    tree = MerkleTree.from_strings(["alpha", "beta", "gamma"])
    assert tree.leaf_count == 3


def test_merkle_deterministic():
    """Same input always produces same root."""
    tree1 = MerkleTree.from_bytes(b"deterministic test data")
    tree2 = MerkleTree.from_bytes(b"deterministic test data")
    assert tree1.root == tree2.root


def test_merkle_repr():
    tree = MerkleTree.from_bytes(b"test")
    r = repr(tree)
    assert "MerkleTree" in r
    assert "leaves=1" in r
