# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""Merkle BLAKE3 versionado (INV_C5_ONWIRE_CANON: BLAKE3 como hash único de digests).

Especificación v1 (bisimilar con ``crates/babylon-attest/src/merkle_b3.rs``):

* hoja:  ``BLAKE3("B60-LEAF-v1\\0" || bytes)``
* nodo:  ``BLAKE3("B60-NODE-v1\\0" || izq || der)``; un nodo impar se empareja consigo mismo.
* raíz:  ``"b3:" + BLAKE3("B60-ROOT-v1\\0" || len_hojas_u64_LE || nodo_superior)``

La etiqueta de dominio separa hoja, nodo y raíz (una hoja no puede hacerse pasar por un nodo
interno) y la raíz compromete la cardinalidad, de modo que ``[a,b,c]`` y ``[a,b,c,c]`` no
colisionan. Las raíces legadas SHA-256/SHA3 siguen verificándose por su ruta original; este
módulo solo emite y verifica el esquema v1 etiquetado ``b3:``.
"""

from __future__ import annotations

import hmac
import struct
from typing import List, Sequence, Tuple

import blake3

ROOT_TAG = "b3:"
_LEAF = b"B60-LEAF-v1\x00"
_NODE = b"B60-NODE-v1\x00"
_ROOT = b"B60-ROOT-v1\x00"

Proof = List[Tuple[str, bytes]]


def leaf_hash(data: bytes) -> bytes:
    """Hash de hoja con separación de dominio."""
    return blake3.blake3(_LEAF + data).digest()


def node_hash(left: bytes, right: bytes) -> bytes:
    """Hash de nodo interno con separación de dominio."""
    return blake3.blake3(_NODE + left + right).digest()


def _levels(leaves: Sequence[bytes]) -> List[List[bytes]]:
    if not leaves:
        raise ValueError("El árbol de Merkle requiere al menos una hoja.")
    levels = [[leaf_hash(x) for x in leaves]]
    while len(levels[-1]) > 1:
        cur = levels[-1]
        levels.append([node_hash(cur[i], cur[i + 1] if i + 1 < len(cur) else cur[i]) for i in range(0, len(cur), 2)])
    return levels


def _seal(top: bytes, count: int) -> str:
    return ROOT_TAG + blake3.blake3(_ROOT + struct.pack("<Q", count) + top).hexdigest()


def build_root(leaves: Sequence[bytes]) -> str:
    """Raíz etiquetada ``b3:<hex>`` que compromete la cardinalidad."""
    return _seal(_levels(leaves)[-1][0], len(leaves))


def inclusion_proof(leaves: Sequence[bytes], index: int) -> Proof:
    """Prueba de inclusión O(log N): lista de ``("L"|"R", hash_hermano)``."""
    if index < 0 or index >= len(leaves):
        raise IndexError(f"Índice de hoja fuera de rango: {index} (total: {len(leaves)})")
    proof: Proof = []
    idx = index
    for level in _levels(leaves)[:-1]:
        if idx % 2 == 1:
            proof.append(("L", level[idx - 1]))
        else:
            proof.append(("R", level[idx + 1] if idx + 1 < len(level) else level[idx]))
        idx //= 2
    return proof


def verify_inclusion(leaf: bytes, proof: Proof, leaf_count: int, expected_root: str) -> bool:
    """Verifica la prueba contra la raíz y la cardinalidad declaradas (comparación constante)."""
    if leaf_count < 1:
        return False
    cur = leaf_hash(leaf)
    for pos, sibling in proof:
        if pos == "L":
            cur = node_hash(sibling, cur)
        elif pos == "R":
            cur = node_hash(cur, sibling)
        else:
            return False
    return hmac.compare_digest(_seal(cur, leaf_count), expected_root)
