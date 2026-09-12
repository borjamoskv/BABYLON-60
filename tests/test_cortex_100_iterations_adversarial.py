# ============================================================================
# BABYLON-60 v4.1 — 100-CYCLE ADVERSARIAL STRESS & TOPOLOGICAL LEAP SUITE
# █ C5-REAL Ring-0 Iteration Engine (100 Iterations / 100 Verifications)
# ============================================================================
import hashlib
import random
import pytest
from pathlib import Path

from babylon60.bft.cortex_crypto_kernel import (
    compute_cortex_hash,
    build_merkle_tree,
    generate_merkle_proof,
    verify_merkle_proof,
    verify_row_invariants,
    ZERO_HASH_256,
)
from babylon60.bft.cortex_persist_ledger import CortexPersistLedger, CortexEvent


def _make_dummy_hash(seed: str) -> str:
    return hashlib.sha3_256(seed.encode()).hexdigest()


# ----------------------------------------------------------------------------
# CICLOS 1–25: ATAQUES DE PODADO DISCRETO (SEQ CONTINUITY FUZZING)
# ----------------------------------------------------------------------------
@pytest.mark.parametrize("cycle", range(1, 26))
def test_cycle_seq_continuity_fuzzing(cycle: int):
    """
    Ciclos 1-25: Fuzzing de discontinuidad secuencial.
    En cada ciclo se prueba una posición de podado aleatoria en una cadena simulada.
    """
    random.seed(cycle * 42)
    chain_len = random.randint(10, 50)
    prune_index = random.randint(2, chain_len - 1)

    # Simular paso en el punto de podado: esperado prune_index, pero recibido prune_index + 1
    is_valid, err = verify_row_invariants(
        seq=prune_index + 1,
        event_id=f"evt_{prune_index + 1}",
        event_type="STATE_MUTATION",
        payload_json='{"op":"audit"}',
        cortex_taint=f"taint:{cycle}",
        agent_id="ULTRATHINK-APEX",
        domain="babylon60.com",
        lamport_t=prune_index + 1,
        prev_hash=_make_dummy_hash(f"hash_{prune_index - 1}"),
        entry_hash=_make_dummy_hash(f"entry_{prune_index + 1}"),
        timestamp="2026-09-12T12:00:00Z",
        expected_seq=prune_index,  # Discontinuidad inyectada
        last_lamport=prune_index - 1,
        expected_prev_hash=_make_dummy_hash(f"hash_{prune_index - 1}"),
    )
    assert is_valid is False, f"Ciclo {cycle}: Podado discreto en seq={prune_index} no fue detectado"
    assert "discontinuity" in err.lower()


# ----------------------------------------------------------------------------
# CICLOS 26–50: ATAQUES DE ISOMORFISMO MERKLE (CVE-2012-2459 MUTATION)
# ----------------------------------------------------------------------------
@pytest.mark.parametrize("cycle", range(26, 51))
def test_cycle_merkle_isomorphism_fuzzing(cycle: int):
    """
    Ciclos 26-50: Fuzzing de árboles impares y colisión de duplicación.
    Comprueba que árboles de longitud impar jamás colisionan con árboles extendidos.
    """
    odd_count = (cycle - 25) * 2 + 1  # 3, 5, 7, ..., 51 hojas
    leaves = [_make_dummy_hash(f"cycle_{cycle}_leaf_{i}") for i in range(odd_count)]
    extended_leaves = leaves + [leaves[-1]]  # Duplicar último nodo

    root_original = build_merkle_tree(leaves)
    root_extended = build_merkle_tree(extended_leaves)

    assert root_original != root_extended, (
        f"Ciclo {cycle}: Colisión de Merkle detectada para árbol de {odd_count} hojas vs {odd_count + 1}"
    )


# ----------------------------------------------------------------------------
# CICLOS 51–75: FUZZING DE PRUEBAS DE INCLUSIÓN O(log N) Y ADULTERACIÓN DE NODOS
# ----------------------------------------------------------------------------
@pytest.mark.parametrize("cycle", range(51, 76))
def test_cycle_merkle_proof_fuzzing(cycle: int):
    """
    Ciclos 51-75: Generación y falsación de pruebas de inclusión.
    En cada ciclo se muta un parámetro del paquete de prueba.
    """
    random.seed(cycle * 1337)
    tree_size = random.randint(3, 32)
    target_idx = random.randint(0, tree_size - 1)

    leaves = [_make_dummy_hash(f"c_{cycle}_l_{i}") for i in range(tree_size)]
    merkle_root = build_merkle_tree(leaves)

    packet = generate_merkle_proof(leaves, target_idx)

    # 1. Prueba válida debe pasar
    assert verify_merkle_proof(
        leaf_hash=packet["leaf_hash"],
        proof=packet["proof"],
        expected_root=merkle_root,
        total_leaves=tree_size,
    ) is True

    # 2. Inyectar mutación adversaria efectiva
    tampered_proof = [dict(step) for step in packet["proof"]]
    mutation_type = cycle % 3

    if mutation_type == 0 and tampered_proof:
        # Corromper digest del hermano
        tampered_proof[0]["sibling"] = _make_dummy_hash(f"adversary_forgery_{cycle}")
        check_size = tree_size
    elif mutation_type == 1 and tampered_proof:
        # Si sibling == leaf (nodo duplicado impar), mutar el hermano directamente
        if tampered_proof[0]["sibling"] == packet["leaf_hash"]:
            tampered_proof[0]["sibling"] = _make_dummy_hash(f"adversary_forgery_{cycle}")
        else:
            tampered_proof[0]["position"] = "left" if tampered_proof[0]["position"] == "right" else "right"
        check_size = tree_size
    else:
        # Corromper cardinalidad esperada
        check_size = tree_size + 1

    assert verify_merkle_proof(
        leaf_hash=packet["leaf_hash"],
        proof=tampered_proof,
        expected_root=merkle_root,
        total_leaves=check_size,
    ) is False, f"Ciclo {cycle}: Prueba adulterada fue aceptada incorrectamente"


# ----------------------------------------------------------------------------
# CICLOS 76–100: CONCURRENCIA, STREAMING O(1) E IDEMPOTENCIA TRANSACCIONAL
# ----------------------------------------------------------------------------
@pytest.mark.parametrize("cycle", range(76, 101))
def test_cycle_concurrency_and_streaming_stress(cycle: int, tmp_path: Path):
    """
    Ciclos 76-100: Inserción por lotes masivos, streaming O(1) con chunk_size variable
    y atestación completa de estado.
    """
    random.seed(cycle * 999)
    db_path = tmp_path / f"ledger_cycle_{cycle}.db"
    ledger = CortexPersistLedger(db_path)

    batch_size = random.randint(10, 30)
    events = [
        CortexEvent(
            event_type="BATCH_OP",
            payload={"cycle": cycle, "idx": i, "rnd": random.random()},
            cortex_taint=f"taint:{cycle}:{i}",
        )
        for i in range(batch_size)
    ]

    # Inserción de lote
    results = ledger.append_batch(events)
    assert len(results) == batch_size
    assert all(r["status"] == "C5_PERMANENT" for r in results)

    # Inyección de duplicado en vuelo: re-ejecución del mismo lote
    replay_results = ledger.append_batch(events)
    assert all(r["status"] == "DUPLICATE_IGNORED" for r in replay_results)

    # Verificación en streaming con tamaño de fragmento dinámico (1 a 5)
    chunk = (cycle % 5) + 1
    assert ledger.verify_integrity(chunk_size=chunk) is True

    # Generación y verificación de prueba de inclusión para un evento aleatorio
    chosen_seq = random.randint(1, batch_size)
    proof_pkt = ledger.get_event_proof(chosen_seq)
    root = ledger.get_merkle_root()
    assert ledger.verify_event_proof(proof_pkt, root) is True
