import pytest

from core_graph_ledger import GraphLedger
from proof_kernel.canonicalizer import hash_evidence


def test_ledger_append_and_trace() -> None:
    ledger = GraphLedger()
    genesis_id = ledger.genesis_id
    n1 = ledger.mut_append_node(parent_id=genesis_id, claim='Init ontology spec', payload_hash=hash_evidence('payload 1'))
    assert len(n1.node_id) == 64
    assert n1.parent_id == genesis_id
    n2 = ledger.mut_append_node(parent_id=n1.node_id, claim='Add verify script', payload_hash=hash_evidence('payload 2'))
    assert n2.parent_id == n1.node_id
    path = ledger.core_get_path(n2.node_id)
    assert len(path) == 2
    assert path[0] == n1
    assert path[1] == n2

def test_ledger_fail_fast_on_missing_parent() -> None:
    ledger = GraphLedger()
    fake_parent = '1' * 64
    with pytest.raises(ValueError, match='not found in DAG ontology'):
        ledger.mut_append_node(parent_id=fake_parent, claim='Orphan node', payload_hash=hash_evidence('dummy'))

def test_ledger_fail_fast_on_invalid_claim() -> None:
    ledger = GraphLedger()
    long_claim = 'A' * 65
    with pytest.raises(ValueError, match='claim must be non-empty and <= 64 chars'):
        ledger.mut_append_node(parent_id=ledger.genesis_id, claim=long_claim, payload_hash=hash_evidence('dummy'))