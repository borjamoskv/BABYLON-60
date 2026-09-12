# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Curry-Howard & Bisimulation] Python / Rust Conformal Merkle Differential Test
"""test_merkle_cross_bisimulation.py - Certificación de Bisimulación Causal.

Demuestra matemáticamente que la implementación de ConformalMerkleTree en Python
y la implementación nativa en Rust (crates/babylon-attest) son estrictamente
bisimilares (isomórficas):
∀ leaves: Root_Python(leaves) == Root_Rust(leaves)
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from babylon60.attestation.conformal_tree import (
    ConformalMerkleTree as PyMerkleTree,
)


def _get_rust_binary_path() -> Path:
    target_bin = Path(__file__).resolve().parents[1] / "target" / "debug" / "babylon-attest"
    if not target_bin.exists():
        # Intentar compilar si no existe
        subprocess.run(["cargo", "build", "-p", "babylon-attest"], check=True, timeout=30)
    return target_bin


@pytest.mark.parametrize("leaf_count", [1, 2, 7, 16, 33, 64, 101])
def test_cross_language_merkle_bisimulation(tmp_path: Path, leaf_count: int) -> None:
    """Verifica equivalencia bit a bit entre árboles de Merkle en Python y Rust."""
    rust_bin = _get_rust_binary_path()

    # 1. Generar hojas sintéticas deterministas
    leaves = [hashlib.sha3_256(f"BISIM_LEAF_{i}".encode("utf-8")).hexdigest() for i in range(leaf_count)]

    # 2. Computar raíz en Python
    py_tree = PyMerkleTree(leaves)
    py_root = py_tree.root

    # 3. Computar raíz en Rust invocando 'build-tree'
    leaves_file = tmp_path / f"leaves_{leaf_count}.json"
    leaves_file.write_text(json.dumps(leaves), encoding="utf-8")

    res = subprocess.run(
        [str(rust_bin), "build-tree", "--leaves-file", str(leaves_file)],
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    )
    rust_data = json.loads(res.stdout.strip())
    rust_root = rust_data["root"]
    rust_depth = rust_data["depth"]

    # 4. Atestación de Bisimulación Causal
    assert py_root == rust_root, (
        f"Fractura de bisimulación para {leaf_count} hojas: Python={py_root} vs Rust={rust_root}"
    )
    assert len(py_tree.tree_levels) == rust_depth


def test_rust_binary_verifies_sealed_l1_manifest() -> None:
    """Verifica que el binario Rust valide directamente el artefacto L1 sellado."""
    rust_bin = _get_rust_binary_path()
    manifest = Path(__file__).resolve().parents[1] / "L1_sink" / "aeon_bounty_omega_10k.json"
    if not manifest.exists():
        pytest.skip("Manifiesto L1 Ω-10k no disponible localmente")

    res = subprocess.run(
        [str(rust_bin), "verify-aeon", "--manifest", str(manifest)],
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    )
    assert "AEÓN CONFORME VERIFICADO EXITOSAMENTE POR EL KERNEL RUST" in res.stdout
    assert "Firma Ed25519:    ✓ VÁLIDA (ed25519-dalek)" in res.stdout


@pytest.mark.parametrize("leaf_count", [3, 9, 31, 64])
def test_bidirectional_inclusion_proof_bisimulation(tmp_path: Path, leaf_count: int) -> None:
    """Certifica bisimulación bidireccional de pruebas de inclusión Merkle O(log2 N) entre Python y Rust."""
    rust_bin = _get_rust_binary_path()
    leaves = [hashlib.sha3_256(f"PROOF_BISIM_{i}".encode("utf-8")).hexdigest() for i in range(leaf_count)]

    leaves_file = tmp_path / f"leaves_proof_{leaf_count}.json"
    leaves_file.write_text(json.dumps(leaves), encoding="utf-8")

    py_tree = PyMerkleTree(leaves)
    py_root = py_tree.root

    for test_idx in [0, leaf_count // 2, leaf_count - 1]:
        leaf = leaves[test_idx]

        # 1. Dirección Python -> Rust: Python genera prueba, Rust la verifica
        py_proof = py_tree.get_inclusion_proof(test_idx)
        rust_proof_format = [{"position": pos, "sibling_hash": sib} for pos, sib in py_proof]
        proof_json_str = json.dumps(rust_proof_format)

        res_rust_verify = subprocess.run(
            [
                str(rust_bin),
                "verify-proof",
                "--leaf",
                leaf,
                "--proof",
                proof_json_str,
                "--root",
                py_root,
            ],
            capture_output=True,
            text=True,
        )
        assert res_rust_verify.returncode == 0, (
            f"Rust verify-proof falló para index {test_idx}: {res_rust_verify.stderr}"
        )
        verify_data = json.loads(res_rust_verify.stdout.strip())
        assert verify_data["valid"] is True

        # 2. Dirección Rust -> Python: Rust genera prueba, Python la verifica
        res_rust_get = subprocess.run(
            [
                str(rust_bin),
                "get-proof",
                "--leaves-file",
                str(leaves_file),
                "--index",
                str(test_idx),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        rust_get_data = json.loads(res_rust_get.stdout.strip())
        assert rust_get_data["root"] == py_root
        assert rust_get_data["leaf"] == leaf

        # Convertir prueba de Rust a formato tupla de Python y verificar
        py_reconstructed_proof = [(step["position"], step["sibling_hash"]) for step in rust_get_data["proof"]]
        assert PyMerkleTree.verify_inclusion_proof(leaf, py_reconstructed_proof, py_root) is True

        # 3. Falsación: Prueba con hoja adulterada debe ser rechazada por Rust
        tampered_leaf = hashlib.sha3_256(b"TAMPERED").hexdigest()
        res_tampered = subprocess.run(
            [
                str(rust_bin),
                "verify-proof",
                "--leaf",
                tampered_leaf,
                "--proof",
                proof_json_str,
                "--root",
                py_root,
            ],
            capture_output=True,
            text=True,
        )
        assert res_tampered.returncode != 0
        tampered_data = json.loads(res_tampered.stdout.strip())
        assert tampered_data["valid"] is False
