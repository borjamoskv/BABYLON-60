# C5-REAL EXERGY CERTIFIED
# test_io_persist_ledger.py
# Prefix: test_ (empirical falsification for the persistence layer)

import pytest
from core_graph_ledger import GraphLedger, StateNode, core_calc_sha256
from io_persist_ledger import LedgerPersist


def test_roundtrip_persist_and_reload(tmp_path: object) -> None:
    """
    Verifica que el ledger sobrevive al ciclo:
    create in-memory -> persist to disk -> destroy RAM -> reload from disk -> assert path identity.
    """
    db_file = str(tmp_path) + "/test_ledger.db"  # type: ignore[operator]

    # Phase 1: Build in-memory DAG and persist
    ledger = GraphLedger()
    n1 = ledger.mut_append_node(
        parent_id=ledger.genesis_id, claim="Genesis node", payload_hash=core_calc_sha256("payload_genesis")
    )
    n2 = ledger.mut_append_node(
        parent_id=n1.node_id, claim="Second node", payload_hash=core_calc_sha256("payload_second")
    )
    n3 = ledger.mut_append_node(
        parent_id=n2.node_id, claim="Third node", payload_hash=core_calc_sha256("payload_third")
    )

    persist = LedgerPersist(db_file)
    inserted = persist.io_persist_ledger(ledger)
    assert inserted == 3
    assert persist.io_node_count() == 3
    persist.close()

    # Phase 2: Destroy RAM state completely
    del ledger
    del persist

    # Phase 3: Reload from disk into a fresh GraphLedger
    persist2 = LedgerPersist(db_file)
    restored = persist2.io_load_ledger()

    assert len(restored.nodes) == 3

    # Verify path integrity: trace from n3 back to genesis
    path = restored.core_get_path(n3.node_id)
    assert len(path) == 3
    assert path[0].node_id == n1.node_id
    assert path[1].node_id == n2.node_id
    assert path[2].node_id == n3.node_id
    assert path[0].claim_summary == "Genesis node"
    assert path[2].claim_summary == "Third node"

    persist2.close()


def test_idempotent_persist(tmp_path: object) -> None:
    """Verifica que persistir dos veces el mismo ledger no duplica filas (INSERT OR IGNORE)."""
    db_file = str(tmp_path) + "/test_idempotent.db"  # type: ignore[operator]

    ledger = GraphLedger()
    ledger.mut_append_node(parent_id=ledger.genesis_id, claim="Only node", payload_hash=core_calc_sha256("data"))

    persist = LedgerPersist(db_file)
    first = persist.io_persist_ledger(ledger)
    second = persist.io_persist_ledger(ledger)

    assert first == 1
    assert second == 0  # No new rows on second persist
    assert persist.io_node_count() == 1
    persist.close()


def test_orphan_detection(tmp_path: object) -> None:
    """Verifica que io_load_ledger rechaza un DAG con nodos huérfanos (parent inexistente)."""
    db_file = str(tmp_path) + "/test_orphan.db"  # type: ignore[operator]

    conn_raw = __import__("sqlite3").connect(db_file)
    conn_raw.execute("PRAGMA journal_mode=WAL")
    conn_raw.execute("""
        CREATE TABLE dag_nodes (
            node_id TEXT PRIMARY KEY,
            parent_id TEXT NOT NULL,
            claim TEXT NOT NULL,
            payload_hash TEXT NOT NULL
        )
    """)
    # Insert a node whose parent doesn't exist and isn't genesis
    fake_parent = "f" * 64
    conn_raw.execute("INSERT INTO dag_nodes VALUES (?, ?, ?, ?)", ("a" * 64, fake_parent, "orphan", "b" * 64))
    conn_raw.commit()
    conn_raw.close()

    persist = LedgerPersist(db_file)
    with pytest.raises(ValueError, match="orphan nodes detected"):
        persist.io_load_ledger()
    persist.close()


def test_inv_bft_04_collision_fails_fast(tmp_path: object) -> None:
    """Verifica que io_persist_ledger lanza ValueError (INV_BFT_04) ante una colisión de node_id con distinto payload_hash."""
    db_file = str(tmp_path) + "/test_collision.db"  # type: ignore[operator]

    hash1 = "a" * 64
    hash2 = "b" * 64

    ledger1 = GraphLedger()
    node1 = ledger1.mut_append_node(parent_id=ledger1.genesis_id, claim="Audit passed", payload_hash=hash1)

    persist = LedgerPersist(db_file)
    persist.io_persist_ledger(ledger1)

    # Crear un segundo ledger con el MISMO node_id pero DISTINTO payload_hash
    ledger2 = GraphLedger()
    colliding_node = StateNode(
        node_id=node1.node_id,
        parent_id=ledger1.genesis_id,
        claim_summary="Audit FAILED",
        payload_hash=hash2
    )
    ledger2.nodes[node1.node_id] = colliding_node

    with pytest.raises(ValueError, match="INV_BFT_04 Collision"):
        persist.io_persist_ledger(ledger2)

    # Verificar que no hubo escrituras corruptas
    assert persist.io_node_count() == 1
    persist.close()
