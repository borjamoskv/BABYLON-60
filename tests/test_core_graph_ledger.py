# test_core_graph_ledger.py
# Prefix: test_ (empirical assertions and unit falsification)

import pytest
from core_graph_ledger import GraphLedger, core_calc_sha256

def test_ledger_append_and_trace() -> None:
    """Verifica que mut_append_node inserta correctamente y core_get_path reconstruye la traza."""
    ledger = GraphLedger()
    genesis_id = ledger.genesis_id
    
    # 1. Append first node
    n1 = ledger.mut_append_node(
        parent_id=genesis_id,
        claim="Init ontology spec",
        payload_hash=core_calc_sha256("payload 1")
    )
    assert len(n1.node_id) == 64
    assert n1.parent_id == genesis_id
    
    # 2. Append second node
    n2 = ledger.mut_append_node(
        parent_id=n1.node_id,
        claim="Add verify script",
        payload_hash=core_calc_sha256("payload 2")
    )
    assert n2.parent_id == n1.node_id
    
    # 3. Trace path
    path = ledger.core_get_path(n2.node_id)
    assert len(path) == 2
    assert path[0] == n1
    assert path[1] == n2

def test_ledger_fail_fast_on_missing_parent() -> None:
    """Falsación empírica: el ledger rechaza nodos huérfanos inmediatamente."""
    ledger = GraphLedger()
    fake_parent = "1" * 64
    with pytest.raises(ValueError, match="not found in DAG ontology"):
        ledger.mut_append_node(
            parent_id=fake_parent,
            claim="Orphan node",
            payload_hash=core_calc_sha256("dummy")
        )

def test_ledger_fail_fast_on_invalid_claim() -> None:
    """Falsación empírica: el ledger rechaza claims largos por ineficiencia de tokens BPE."""
    ledger = GraphLedger()
    long_claim = "A" * 65 # > 64 chars
    with pytest.raises(ValueError, match="claim must be non-empty and <= 64 chars"):
        ledger.mut_append_node(
            parent_id=ledger.genesis_id,
            claim=long_claim,
            payload_hash=core_calc_sha256("dummy")
        )
