# [C5-REAL] Byzantine Fault Tolerance with Diversity Multiplier
# Author: borjamoskv
# Estilo: Sin comillas simples (exclusivo comillas dobles)

from __future__ import annotations
from dataclasses import dataclass

@dataclass
class AgentMetadata:
    agent_id: str
    reputation: float
    model_family: str  # e.g., "claude", "llama", "qwen"
    architecture_id: str  # e.g., "anthropic-moe", "meta-dense", "alibaba-dense"

class DiversityConsensusManager:
    """
    Implements WBFT consensus with a structural diversity multiplier.
    Prevents Sybil attacks from clustered/destilled model variants.
    """
    def __init__(self) -> None:
        self.agents: dict[str, AgentMetadata] = {}

    def register_agent(self, agent_id: str, reputation: float, model_family: str, architecture_id: str) -> None:
        self.agents[agent_id] = AgentMetadata(
            agent_id=agent_id,
            reputation=reputation,
            model_family=model_family,
            architecture_id=architecture_id
        )

    def calculate_distance(self, agent_a: AgentMetadata, agent_b: AgentMetadata) -> float:
        """
        Determines architectural and family distances between two agent engines.
        Returns a score in [0.1, 1.0].
        """
        if agent_a.agent_id == agent_b.agent_id:
            return 0.0
        
        distance = 0.2
        if agent_a.model_family != agent_b.model_family:
            distance += 0.4
        if agent_a.architecture_id != agent_b.architecture_id:
            distance += 0.4
        return max(0.1, min(1.0, distance))

    def compute_consensus(self, votes: dict[str, int]) -> tuple[bool, float, dict[str, float]]:
        """
        Processes votes cast by agent nodes (+1 to verify, -1 to dispute).
        Returns:
            - consensus_reached: boolean indicating if quorum threshold is met
            - final_score: normalized consensus score [-1.0, 1.0]
            - adjusted_weights: details of the weight calculations for debugging
        """
        if not votes:
            return False, 0.0, {}

        # 1. Calculate diversity coefficients per voting node
        diversity_coefficients: dict[str, float] = {}
        for voter_id in votes:
            if voter_id not in self.agents:
                # Untracked/unknown voter gets minimum base coefficient
                diversity_coefficients[voter_id] = 0.1
                continue
            
            voter_meta = self.agents[voter_id]
            
            # Find average distance to all other active voters in this epoch
            other_distances = []
            for peer_id in votes:
                if peer_id == voter_id:
                    continue
                if peer_id in self.agents:
                    dist = self.calculate_distance(voter_meta, self.agents[peer_id])
                    other_distances.append(dist)
            
            # Diversity coefficient is the mean distance to peers
            if other_distances:
                diversity_coefficients[voter_id] = sum(other_distances) / len(other_distances)
            else:
                diversity_coefficients[voter_id] = 1.0

        # 2. Compute diversity-adjusted weights
        adjusted_weights: dict[str, float] = {}
        total_weight = 0.0
        for voter_id, vote in votes.items():
            rep = self.agents[voter_id].reputation if voter_id in self.agents else 0.1
            coeff = diversity_coefficients[voter_id]
            
            # Adjusted weight: reputation * diversity coefficient
            weight = rep * coeff
            adjusted_weights[voter_id] = weight
            total_weight += weight

        if total_weight <= 0.0:
            return False, 0.0, adjusted_weights

        # 3. Aggregate weighted votes
        weighted_sum = 0.0
        for voter_id, vote in votes.items():
            weighted_sum += vote * adjusted_weights[voter_id]

        normalized_score = weighted_sum / total_weight

        # Consensus Quorum is met if the absolute normalized score is >= 2/3 (Byzantine boundary)
        consensus_reached = abs(normalized_score) >= (2.0 / 3.0)
        return consensus_reached, normalized_score, adjusted_weights
