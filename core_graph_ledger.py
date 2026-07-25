import time
from dataclasses import asdict, dataclass
from typing import List
from proof_kernel.canonicalizer import hash_evidence
from proof_kernel.crdt import CRDTMap

@dataclass(frozen=True)
class StateNode:
    node_id: str
    parent_id: str
    claim_summary: str
    payload_hash: str

class GraphLedger:

    def __init__(self) -> None:
        self.crdt = CRDTMap()
        self.genesis_id: str = '0' * 64

    def _clock(self) -> int:
        return int(time.time() * 1000000)

    def mut_append_node(self, parent_id: str, claim: str, payload_hash: str) -> StateNode:
        if parent_id != self.genesis_id and self.crdt.get(parent_id) is None:
            raise ValueError(f'Fail-fast: parent_id {parent_id} not found in DAG ontology.')
        if not claim or len(claim) > 64:
            raise ValueError('Fail-fast: claim must be non-empty and <= 64 chars for BPE efficiency.')
        if len(payload_hash) != 64:
            raise ValueError('Fail-fast: payload_hash must be a strict 64-char SHA256 digest.')
        raw_content = {'parent_id': parent_id, 'claim': claim, 'payload_hash': payload_hash}
        node_id = hash_evidence(raw_content)
        if self.crdt.get(node_id) is not None:
            raise ValueError(f'Fail-fast: idempotency violation, node {node_id} already exists.')
        node = StateNode(node_id=node_id, parent_id=parent_id, claim_summary=claim, payload_hash=payload_hash)
        self.crdt.set(node_id, asdict(node), self._clock())
        return node

    def core_get_path(self, head_id: str) -> List[StateNode]:
        if self.crdt.get(head_id) is None:
            raise ValueError(f'Fail-fast: head_id {head_id} missing from ledger.')
        path: List[StateNode] = []
        curr_id: str = head_id
        while curr_id != self.genesis_id:
            node_data = self.crdt.get(curr_id)
            node = StateNode(**node_data)
            path.append(node)
            curr_id = node.parent_id
        path.reverse()
        return path