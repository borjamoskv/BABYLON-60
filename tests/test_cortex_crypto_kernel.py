# ============================================================================
# BABYLON-60 v4.1 Sovereign Hardened
# █ CORTEX CRYPTO KERNEL TEST SUITE & MERKLE INCLUSION PROOFS
# ============================================================================
import hashlib
import pytest
from pathlib import Path

from babylon60.bft.cortex_crypto_kernel import (
    build_merkle_tree,
    generate_merkle_proof,
    verify_merkle_proof,
    verify_row_invariants,
    ZERO_HASH_256,
    MerkleMountainRange,
)
from babylon60.bft.cortex_persist_ledger import CortexPersistLedger, CortexEvent, MMREventProof


def _make_dummy_hash(i: int) -> str:
    return hashlib.sha3_256(f"leaf_{i}".encode()).hexdigest()


def test_empty_merkle_tree() -> None:
    assert build_merkle_tree([]) == ZERO_HASH_256


def test_single_leaf_merkle_tree() -> None:
    h0 = _make_dummy_hash(0)
    root = build_merkle_tree([h0])
    assert len(root) == 64
    # Proof for single leaf
    proof_packet = generate_merkle_proof([h0], 0)
    assert verify_merkle_proof(h0, proof_packet["proof"], root, 1) is True


def test_cve_2012_2459_merkle_isomorphism_prevention() -> None:
    """
    Verifica que la vulnerabilidad de colisión de hojas impares (CVE-2012-2459)
    está matemáticamente neutralizada.
    [h0, h1, h2] DEBE producir un hash de raíz DISTINTO a [h0, h1, h2, h2].
    """
    leaves_3 = [_make_dummy_hash(i) for i in range(3)]
    leaves_4 = leaves_3 + [leaves_3[-1]]  # Duplicar el último nodo artificialmente

    root_3 = build_merkle_tree(leaves_3)
    root_4 = build_merkle_tree(leaves_4)

    assert root_3 != root_4, "CVE-2012-2459 regresión: árbol impar colisionó con árbol duplicado"


@pytest.mark.parametrize("tree_size", [1, 2, 3, 5, 8, 13])
def test_merkle_inclusion_proofs_exhaustive(tree_size: int) -> None:
    """
    Verifica que toda hoja en árboles de cualquier tamaño (par e impar)
    posee una prueba de inclusión verificable O(log N).
    """
    leaves = [_make_dummy_hash(i) for i in range(tree_size)]
    root = build_merkle_tree(leaves)

    for idx in range(tree_size):
        packet = generate_merkle_proof(leaves, idx)
        assert packet["target_index"] == idx
        assert packet["leaf_hash"] == leaves[idx]
        assert packet["total_leaves"] == tree_size

        # Verificación positiva
        valid = verify_merkle_proof(
            leaf_hash=packet["leaf_hash"],
            proof=packet["proof"],
            expected_root=root,
            total_leaves=tree_size,
        )
        assert valid is True, f"Fallo al verificar prueba de inclusión para idx {idx} en árbol tamaño {tree_size}"

        # Verificación negativa 1: alteración de la hoja
        tampered_leaf = _make_dummy_hash(9999)
        assert verify_merkle_proof(tampered_leaf, packet["proof"], root, tree_size) is False

        # Verificación negativa 2: cardinalidad falsa
        assert verify_merkle_proof(packet["leaf_hash"], packet["proof"], root, tree_size + 1) is False


def test_verify_row_invariants_seq_continuity() -> None:
    """FIX C5-04: Detección de podado discreto."""
    # seq esperado = 2, pero seq = 3
    is_valid, err = verify_row_invariants(
        seq=3,
        event_id="evt_3",
        event_type="DECISION",
        payload_json="{}",
        cortex_taint="taint:1",
        agent_id="ULTRATHINK-APEX",
        domain="babylon60.com",
        lamport_t=3,
        prev_hash="prev_hash_1",
        entry_hash="abc",
        timestamp="2026-09-12T12:00:00Z",
        expected_seq=2,  # Discontinuidad intencional
        last_lamport=1,
        expected_prev_hash="prev_hash_1",
    )
    assert is_valid is False
    assert "discontinuity" in err.lower()


def test_verify_row_invariants_lamport_monotonicity() -> None:
    """Detección de violación en el reloj de Lamport."""
    is_valid, err = verify_row_invariants(
        seq=2,
        event_id="evt_2",
        event_type="DECISION",
        payload_json="{}",
        cortex_taint="taint:1",
        agent_id="ULTRATHINK-APEX",
        domain="babylon60.com",
        lamport_t=5,
        prev_hash="prev_hash",
        entry_hash="abc",
        timestamp="2026-09-12T12:00:00Z",
        expected_seq=2,
        last_lamport=5,  # Lamport no aumentó
        expected_prev_hash="prev_hash",
    )
    assert is_valid is False
    assert "lamport" in err.lower()


def test_ledger_streaming_verification_and_event_proof(tmp_path: Path) -> None:
    """
    Prueba integral de streaming O(1) y generación de pruebas de evidencia
    para el cumplimiento del EU AI Act.
    """
    db_path = tmp_path / "streaming_test.db"
    ledger = CortexPersistLedger(db_path)

    # Insertar 25 eventos en lotes
    events = [
        CortexEvent(
            event_type="AUDIT_ACTION",
            payload={"index": i, "data": f"payload_{i}"},
            cortex_taint=f"session:batch_{i}",
        )
        for i in range(25)
    ]
    results = ledger.append_batch(events)
    assert len(results) == 25

    # Verificación en streaming con chunk pequeño (chunk_size=7) para forzar múltiples lecturas
    assert ledger.verify_integrity(chunk_size=7) is True

    # Obtener Merkle Root
    merkle_root = ledger.get_merkle_root()
    assert len(merkle_root) == 64

    # Generar prueba de inclusión para el evento seq=14
    proof_14 = ledger.get_event_proof(seq=14)
    assert proof_14["target_index"] == 13
    assert proof_14["total_leaves"] == 25

    # Validar prueba de inclusión O(log N) de forma autónoma
    is_proven = CortexPersistLedger.verify_event_proof(proof_14, merkle_root)
    assert is_proven is True

    # Validar manifiesto de atestación
    attestation = ledger.get_state_attestation()
    assert attestation["total_entries"] == 25
    assert attestation["integrity_verified"] is True
    assert attestation["merkle_root"] == merkle_root


# =============================================================================
# SUITE DE PRUEBAS PARA MERKLE MOUNTAIN RANGE (MMR) & O(LOG N) PROOFS
# =============================================================================


def test_mmr_empty() -> None:
    mmr = MerkleMountainRange()
    assert mmr.get_root() == ZERO_HASH_256
    assert mmr.get_peaks() == []


def test_mmr_single_leaf() -> None:
    mmr = MerkleMountainRange()
    h0 = _make_dummy_hash(0)
    pos = mmr.append(h0)
    assert pos == 0
    root = mmr.get_root()
    assert len(root) == 64
    proof = mmr.generate_proof(0)
    assert MerkleMountainRange.verify_proof(h0, proof, root) is True


@pytest.mark.parametrize("n_leaves", [2, 3, 5, 8, 13, 21, 34, 60])
def test_mmr_arbitrary_sizes_inclusion(n_leaves: int) -> None:
    """
    Verifica que para cualquier número de hojas (incluyendo números de Fibonacci
    y el número sexagesimal 60), toda hoja genera una prueba verificable O(log N).
    """
    mmr = MerkleMountainRange()
    leaves = [_make_dummy_hash(i) for i in range(n_leaves)]
    for h in leaves:
        mmr.append(h)

    root = mmr.get_root()
    assert len(root) == 64

    # Verificar cada hoja individualmente
    for i, h in enumerate(leaves):
        proof = mmr.generate_proof(i)
        assert proof["total_leaves"] == n_leaves
        # Cota logarítmica: inner_proof + other_peaks <= 2 * log2(n) + 1
        proof_size = len(proof["inner_proof"]) + len(proof["other_peaks"])
        assert proof_size <= 16, f"Prueba excedió la cota logarítmica: {proof_size}"
        assert MerkleMountainRange.verify_proof(h, proof, root) is True


def test_mmr_tamper_detection() -> None:
    mmr = MerkleMountainRange()
    leaves = [_make_dummy_hash(i) for i in range(7)]
    for h in leaves:
        mmr.append(h)
    root = mmr.get_root()

    proof_2 = mmr.generate_proof(2)
    tampered_hash = _make_dummy_hash(999)
    assert MerkleMountainRange.verify_proof(tampered_hash, proof_2, root) is False

    # Alterar un nodo de la prueba
    if proof_2["inner_proof"]:
        proof_2["inner_proof"][0]["sibling"] = ZERO_HASH_256
        assert MerkleMountainRange.verify_proof(leaves[2], proof_2, root) is False


def test_cortex_ledger_mmr_integration(tmp_path: Path) -> None:
    db_file = tmp_path / "test_ledger_mmr.db"
    ledger = CortexPersistLedger(db_file)

    for i in range(1, 16):
        event = CortexEvent(
            event_type=f"AGY_MMR_OP_{i}",
            payload={"step": i, "weight": i * 60},
            cortex_taint="SOVEREIGN_AUDIT",
        )
        ledger.append_event(event)

    mmr_root = ledger.get_mmr_root()
    assert len(mmr_root) == 64

    attestation = ledger.get_state_attestation()
    assert attestation["total_entries"] == 15
    assert attestation["mmr_root"] == mmr_root
    assert attestation["integrity_verified"] is True

    # Generar prueba de inclusión MMR para el evento seq=7
    proof_7 = ledger.get_mmr_event_proof(7)
    assert proof_7["leaf_index"] == 6
    assert proof_7["total_leaves"] == 15

    # Verificar autónomamente
    is_valid = CortexPersistLedger.verify_mmr_event_proof(proof_7, mmr_root)
    assert is_valid is True

    # Falsación por manipulación
    tampered: MMREventProof = {**proof_7, "leaf_hash": ZERO_HASH_256}
    assert CortexPersistLedger.verify_mmr_event_proof(tampered, mmr_root) is False
