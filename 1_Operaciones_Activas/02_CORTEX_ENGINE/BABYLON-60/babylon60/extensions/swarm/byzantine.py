# C5-REAL EXERGY CERTIFIED
# [C5-REAL] Exergy-Maximized
"""
Byzantine Consensus (LEGION-Ω)
Byzantine Fault Tolerance / Zero-Trust Mathematics: Axiom 4.
"""

import json
import math
from typing import Any, TypeVar

from babylon60.crypto.hash_registry import cortex_hash

T = TypeVar("T")


class ByzantineNode:
    def __init__(self, node_id: str, reputation: float = 1.0):
        self.node_id = node_id
        self.reputation = reputation


class ByzantineConsensus:
    """
    Implements Zero-Trust consensus for multi-model / multi-agent swarms.
    Operates under the absolute premise that peripheral nodes hallucinate or lie.
    """

    def __init__(self, tolerance_threshold: float = 0.67):
        # By default, a 2/3 majority weighted by reputation is required.
        self.tolerance_threshold = tolerance_threshold
        self.nodes: dict[str, ByzantineNode] = {}
        # [C5-REAL] Exergy Cache: Previene Thermal Runaway O(N^2) en evaluación continua de cuórum.
        self._hash_cache: dict[str, str] = {}

    def register_node(self, node_id: str, initial_reputation: float = 1.0) -> None:
        self.nodes[node_id] = ByzantineNode(node_id, initial_reputation)

    @staticmethod
    def _normalize_proposal(proposal: Any) -> str:
        """Normalize proposal content using AST unparsing for code structures to achieve semantic consensus."""
        import ast

        if isinstance(proposal, str):
            try:
                tree = ast.parse(proposal)
                return ast.unparse(tree)
            except SyntaxError:
                pass
        try:
            return json.dumps(proposal, sort_keys=True, default=str)
        except (TypeError, ValueError):
            return str(proposal)

    def _get_proposal_hash_sync(self, proposal: Any) -> str:
        """
        O(1) Memoized Hashing.
        Evita el colapso O(N^2) de AST Parses cuando el orquestador evalúa
        el cuórum bizantino tras cada respuesta de agente en LEGION_10K.
        """
        raw_str = str(proposal)
        if raw_str in self._hash_cache:
            return self._hash_cache[raw_str]

        normalized = self._normalize_proposal(proposal)
        h = cortex_hash(normalized.encode())
        self._hash_cache[raw_str] = h
        return h

    def _hash_proposal(self, proposal: Any) -> str:
        """Compatibility alias for legacy tests."""
        return self._get_proposal_hash_sync(proposal)

    async def _batch_hash_proposals(self, proposals: dict[str, Any]) -> dict[str, str]:
        """
        Calcula hashes asincrónicamente pero usando memoización estricta sincrónica.
        Destruye el ThreadPoolExecutor bottleneck de asyncio.to_thread x 10,000.
        """
        # La evaluación es mayoritariamente O(1) por caché, liberando el event loop.
        return {
            nid: self._get_proposal_hash_sync(prop)
            for nid, prop in proposals.items()
            if nid in self.nodes
        }

    async def execute_consensus(self, proposals: dict[str, T]) -> T | None:
        """
        Takes proposals from multiple nodes. Validates them via reputation-weighted
        thresholding. Returns the absolute truth or None if BFT consensus fails.
        """
        if not proposals:
            return None

        vote_tally: dict[str, float] = {}
        hash_to_proposal: dict[str, T] = {}
        total_reputation = 0.0

        # [C5-REAL] Batch hash con Memoización (Ω₂: Erradicación de latencia en loops de as_completed)
        node_hashes = await self._batch_hash_proposals(proposals)

        for node_id, proposal_hash in node_hashes.items():
            rep = self.nodes[node_id].reputation
            total_reputation += rep
            vote_tally[proposal_hash] = vote_tally.get(proposal_hash, 0.0) + rep
            hash_to_proposal[proposal_hash] = proposals[node_id]

        if math.isclose(total_reputation, 0.0, abs_tol=1e-9):
            return None

        # Find winning proposal
        winning_hash = max(vote_tally.keys(), key=lambda k: vote_tally[k])
        winning_weight = vote_tally[winning_hash]

        # Check against Byzantine tolerance threshold
        ratio = winning_weight / total_reputation
        if ratio > self.tolerance_threshold or math.isclose(
            ratio, self.tolerance_threshold, rel_tol=1e-9
        ):
            # Consensus achieved
            self._update_reputations(winning_hash, proposals, node_hashes)
            return hash_to_proposal[winning_hash]

        # Consensus failed (Shattered Trust)
        return None

    def _update_reputations(
        self, winning_hash: str, proposals: dict[str, T], node_hashes: dict[str, str]
    ) -> None:
        """
        Zero-trust reputation slashing. Nodes that hallucinated or Byzantine-lied
        lose reputation. Nodes that proposed the truth gain.
        (Ahora O(1) usando los hashes previamente calculados).
        """
        for node_id, _ in proposals.items():
            if node_id not in self.nodes:
                continue

            proposal_hash = node_hashes.get(node_id)
            if proposal_hash == winning_hash:
                # Reward
                self.nodes[node_id].reputation = min(1.0, self.nodes[node_id].reputation * 1.05)
            else:
                # Slash
                self.nodes[node_id].reputation *= 0.8
