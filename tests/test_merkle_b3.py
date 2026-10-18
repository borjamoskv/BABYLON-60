"""Tests del Merkle BLAKE3 versionado (D5): propiedades, falsación y bisimulación con Rust."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from babylon60.attestation.merkle_b3 import (
    ROOT_TAG,
    build_root,
    inclusion_proof,
    leaf_hash,
    node_hash,
    verify_inclusion,
)

REPO = Path(__file__).resolve().parents[1]
RUST_BIN = REPO / "target" / "debug" / "babylon-attest"


def _leaves(n: int) -> list[bytes]:
    return [f"BISIM_LEAF_{i}".encode() for i in range(n)]


def test_root_is_tagged_and_deterministic() -> None:
    root = build_root(_leaves(5))
    assert root.startswith(ROOT_TAG)
    assert len(root) == len(ROOT_TAG) + 64
    assert root == build_root(_leaves(5))


def test_empty_tree_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_root([])


def test_cardinality_is_committed() -> None:
    # Con el emparejamiento del nodo impar consigo mismo, [a,b,c] y [a,b,c,c] colisionaban.
    assert build_root([b"a", b"b", b"c"]) != build_root([b"a", b"b", b"c", b"c"])


def test_leaf_cannot_masquerade_as_internal_node() -> None:
    forged = leaf_hash(b"a") + leaf_hash(b"b")
    assert build_root([forged]) != build_root([b"a", b"b"])
    assert leaf_hash(b"x") != node_hash(leaf_hash(b"x"), leaf_hash(b"x"))


@pytest.mark.parametrize("n", [1, 2, 3, 7, 8, 13])
def test_inclusion_proofs_and_mutations(n: int) -> None:
    leaves = [f"L{i}".encode() for i in range(n)]
    root = build_root(leaves)
    for i, leaf in enumerate(leaves):
        proof = inclusion_proof(leaves, i)
        assert verify_inclusion(leaf, proof, n, root)
        assert not verify_inclusion(leaf + b"x", proof, n, root)
        assert not verify_inclusion(leaf, proof, n + 1, root)
        assert not verify_inclusion(leaves[(i + 1) % n] + b"!", proof, n, root)
        assert not verify_inclusion(leaf, proof, n, root[:-1] + ("0" if root[-1] != "0" else "1"))


def test_position_flip_is_rejected_when_sibling_differs() -> None:
    leaves = [f"L{i}".encode() for i in range(13)]
    root = build_root(leaves)
    flips = 0
    for i, leaf in enumerate(leaves):
        proof = inclusion_proof(leaves, i)
        cur = leaf_hash(leaf)
        for k, (pos, sib) in enumerate(proof):
            if sib != cur:  # con auto-emparejamiento la posición es simétrica por construcción
                mutated = list(proof)
                mutated[k] = ("R" if pos == "L" else "L", sib)
                assert not verify_inclusion(leaf, mutated, len(leaves), root)
                flips += 1
            cur = node_hash(sib, cur) if pos == "L" else node_hash(cur, sib)
    assert flips > 10


def test_proof_index_out_of_range() -> None:
    with pytest.raises(IndexError):
        inclusion_proof([b"a"], 1)


def _rust_root(leaves: list[bytes]) -> subprocess.CompletedProcess[str]:
    if not RUST_BIN.exists():
        subprocess.run(["cargo", "build", "-q", "-p", "babylon-attest"], check=True, cwd=REPO, timeout=600)
    payload = "\n".join(x.decode() for x in leaves)
    return subprocess.run(
        [str(RUST_BIN), "merkle-b3-root"], input=payload, capture_output=True, text=True, cwd=REPO, timeout=60
    )


@pytest.mark.parametrize("n", list(range(1, 34)) + [64, 101])
def test_python_rust_bisimulation(n: int) -> None:
    leaves = _leaves(n)
    res = _rust_root(leaves)
    assert res.returncode == 0, res.stderr
    assert res.stdout.strip() == build_root(leaves)


def test_rust_rejects_empty_tree() -> None:
    res = _rust_root([])
    assert res.returncode == 2
    assert "EMPTY_TREE" in res.stderr
