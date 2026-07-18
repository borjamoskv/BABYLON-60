# core_graph_ledger.py
# Execution Protocol: Exergy-Optimized Ontology & DAG Ledger
# Prefix: core_ (pure primitive, zero I/O, deterministic)

import hashlib
from dataclasses import dataclass
from typing import Dict, List

@dataclass(frozen=True)
class StateNode:
    """Strict schema for a content-addressable state transition node in the Poset/DAG."""
    node_id: str          # SHA256 content address
    parent_id: str        # SHA256 of parent node ('0' * 64 if genesis)
    claim_summary: str    # BPE-aligned summary (< 64 chars)
    payload_hash: str     # SHA256 of mutated data

def core_calc_sha256(data: str) -> str:
    """Pre: valid utf-8 str -> Exec: sha256 -> Post: 64-char hex digest."""
    assert isinstance(data, str), "Fail-fast: data must be strictly typed str"
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

class GraphLedger:
    """
    DAG state ledger enforcing strict acyclycity and content-addressable SSOT.
    Zero-magic: all insertions verify invariants before modifying local index.
    """
    def __init__(self) -> None:
        self.nodes: Dict[str, StateNode] = {}
        self.genesis_id: str = "0" * 64

    def mut_append_node(self, parent_id: str, claim: str, payload_hash: str) -> StateNode:
        """
        Pre: parent_id exists (or is genesis) && claim non-empty
        Exec: compute node_id, verify DAG invariants, store node
        Post: StateNode appended to local dictionary || raise ValueError
        """
        if parent_id != self.genesis_id and parent_id not in self.nodes:
            raise ValueError(f"Fail-fast: parent_id {parent_id} not found in DAG ontology.")
        if not claim or len(claim) > 64:
            raise ValueError("Fail-fast: claim must be non-empty and <= 64 chars for BPE efficiency.")
        if len(payload_hash) != 64:
            raise ValueError("Fail-fast: payload_hash must be a strict 64-char SHA256 digest.")

        raw_content = f"{parent_id}:{claim}:{payload_hash}"
        node_id = core_calc_sha256(raw_content)

        if node_id in self.nodes:
            raise ValueError(f"Fail-fast: idempotency violation, node {node_id} already exists.")

        node = StateNode(
            node_id=node_id,
            parent_id=parent_id,
            claim_summary=claim,
            payload_hash=payload_hash
        )
        self.nodes[node_id] = node
        return node

    def core_get_path(self, head_id: str) -> List[StateNode]:
        """Pre: head_id in DAG -> Exec: trace parent_ids to genesis -> Post: ordered list of nodes."""
        if head_id not in self.nodes:
            raise ValueError(f"Fail-fast: head_id {head_id} missing from ledger.")
        
        path: List[StateNode] = []
        curr_id: str = head_id
        while curr_id != self.genesis_id:
            node = self.nodes[curr_id]
            path.append(node)
            curr_id = node.parent_id
        
        path.reverse()
        return path
