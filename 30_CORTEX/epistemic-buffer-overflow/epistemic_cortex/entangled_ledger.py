# [C5-REAL] Entangled Ledger and Cryptographic Anchoring
# Author: borjamoskv
# Estilo: Sin comillas simples (exclusivo comillas dobles)

from __future__ import annotations
import hashlib
import json
import time
from dataclasses import dataclass, asdict

@dataclass
class Transaction:
    tx_id: int
    fact_id: int
    operation: str
    content_hash: str
    peer_hashes: list[str]  # Entanglement component
    prev_hash: str
    timestamp: float
    signature: str = ""
    hash: str = ""

    def compute_hash(self) -> str:
        data = {
            "tx_id": self.tx_id,
            "fact_id": self.fact_id,
            "operation": self.operation,
            "content_hash": self.content_hash,
            "peer_hashes": sorted(self.peer_hashes),
            "prev_hash": self.prev_hash,
            "timestamp": self.timestamp
        }
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

class EntangledLedger:
    """
    C5-REAL Ledger with state entanglement and Merkle verification.
    Prevents simple database rollbacks by anchoring state to peer swarms
    and generating deterministic Merkle checkpoints.
    """
    def __init__(self, anchor_callback: callable | None = None) -> None:
        self.chain: list[Transaction] = []
        self.anchor_callback = anchor_callback
        self.peer_states: dict[str, str] = {}

    def update_peer_state(self, peer_id: str, last_hash: str) -> None:
        self.peer_states[peer_id] = last_hash

    def append_fact(self, fact_id: int, operation: str, content: str) -> Transaction:
        tx_id = len(self.chain)
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        prev_hash = self.chain[-1].hash if self.chain else "0" * 64

        # Entanglement: incorporate latest known state hashes of peer agents
        peer_hashes = list(self.peer_states.values())

        tx = Transaction(
            tx_id=tx_id,
            fact_id=fact_id,
            operation=operation,
            content_hash=content_hash,
            peer_hashes=peer_hashes,
            prev_hash=prev_hash,
            timestamp=time.time()
        )
        tx.hash = tx.compute_hash()
        self.chain.append(tx)

        # Trigger Merkle Root anchoring and external publication if threshold reached
        if len(self.chain) % 10 == 0:
            self.anchor_checkpoint()

        return tx

    def calculate_merkle_root(self, leaves: list[str]) -> str:
        if not leaves:
            return "0" * 64
        if len(leaves) == 1:
            return leaves[0]
        
        next_level: list[str] = []
        for i in range(0, len(leaves), 2):
            left = leaves[i]
            right = leaves[i+1] if i + 1 < len(leaves) else left
            combined = left + right
            parent_hash = hashlib.sha256(combined.encode("utf-8")).hexdigest()
            next_level.append(parent_hash)
            
        return self.calculate_merkle_root(next_level)

    def anchor_checkpoint(self) -> str:
        tx_hashes = [tx.hash for tx in self.chain]
        merkle_root = self.calculate_merkle_root(tx_hashes)
        if self.anchor_callback:
            self.anchor_callback(merkle_root)
        return merkle_root

    def verify_chain_integrity(self) -> bool:
        for i in range(len(self.chain)):
            tx = self.chain[i]
            # 1. Recalculate hash
            if tx.hash != tx.compute_hash():
                return False
            # 2. Check back-linkage
            if i > 0:
                prev_tx = self.chain[i-1]
                if tx.prev_hash != prev_tx.hash:
                    return False
        return True
