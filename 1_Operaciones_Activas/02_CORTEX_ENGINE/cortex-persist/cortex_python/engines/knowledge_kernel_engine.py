# C5-REAL EXERGY CERTIFIED
"""
C5-REAL Knowledge Kernel Engine (Omega 1 - Omega 12)
Transducer for Knowledge Fabric, Event Sourcing, Fractal Memory, and Causal Graph Simulation.
"""
from __future__ import annotations

import dataclasses
import datetime
import hashlib
import math
from typing import Any, Dict, List, Optional


@dataclasses.dataclass(frozen=True)
class KnowledgeNode:
    id: str
    node_type: str
    embedding: List[float]
    metadata: Dict[str, Any]


@dataclasses.dataclass(frozen=True)
class KnowledgeEdge:
    source: str
    target: str
    relation: str
    confidence: float


@dataclasses.dataclass(frozen=True)
class KnowledgeEvent:
    event_id: str
    timestamp: str
    actor: str
    action: str
    object_id: str
    confidence: float
    source: str


@dataclasses.dataclass(frozen=True)
class CausalClaim:
    claim_id: str
    proposition: str
    evidence: List[str]
    counter_evidence: List[str]
    confidence: float
    source: str
    temporal_evolution: List[str]


class CompressionPyramid:
    """
    Omega 8 Compression Engine: Ratios 100k -> 1 signal.
    Calculates Kolmogorov Exergy Density of Knowledge Networks.
    """

    RATIOS: Dict[str, int] = {
        "articles": 100000,
        "ideas": 20000,
        "concepts": 4000,
        "patterns": 900,
        "paradigms": 120,
        "structural_shifts": 12,
        "meta_trends": 3,
        "signal": 1,
    }

    @classmethod
    def compute_exergy_density(cls, raw_articles: int) -> Dict[str, int]:
        if raw_articles <= 0:
            return {k: 0 for k in cls.RATIOS}
        scale = raw_articles / float(cls.RATIOS["articles"])
        return {
            stage: max(1 if scale > 0 else 0, math.floor(ratio * scale))
            for stage, ratio in cls.RATIOS.items()
        }


class KnowledgeKernelEngine:
    """
    Omega 12 Knowledge Kernel.
    Event-Sourced Append-Only Ledger with fractal abstraction and causal graph synthesis.
    """

    def __init__(self) -> None:
        self._nodes: Dict[str, KnowledgeNode] = {}
        self._edges: List[KnowledgeEdge] = []
        self._events: List[KnowledgeEvent] = []
        self._claims: Dict[str, CausalClaim] = {}

    def append_event(
        self,
        actor: str,
        action: str,
        object_id: str,
        confidence: float,
        source: str,
        timestamp: Optional[str] = None,
    ) -> KnowledgeEvent:
        ts = timestamp or datetime.datetime.now(datetime.timezone.utc).isoformat()
        raw_payload = f"{actor}:{action}:{object_id}:{ts}:{source}".encode("utf-8")
        event_id = hashlib.sha3_256(raw_payload).hexdigest()

        evt = KnowledgeEvent(
            event_id=event_id,
            timestamp=ts,
            actor=actor,
            action=action,
            object_id=object_id,
            confidence=max(0.0, min(1.0, confidence)),
            source=source,
        )
        self._events.append(evt)
        return evt

    def compute_pagerank(self, damping_factor: float = 0.85, max_iterations: int = 100, tolerance: float = 1.0e-6) -> Dict[str, float]:
        """
        Calculates topological centrality (PageRank) over the Causal Graph.
        Iterative convergence (META_ITER compliant).
        """
        num_nodes = len(self._nodes)
        if num_nodes == 0:
            return {}

        pr = {node_id: 1.0 / num_nodes for node_id in self._nodes}
        out_degree = {node_id: 0 for node_id in self._nodes}

        for edge in self._edges:
            if edge.source in out_degree:
                out_degree[edge.source] += 1

        for _ in range(max_iterations):
            prev_pr = pr.copy()
            diff = 0.0

            # Distribute PageRank
            for node_id in self._nodes:
                pr[node_id] = (1.0 - damping_factor) / num_nodes

            for edge in self._edges:
                if edge.source in prev_pr and out_degree[edge.source] > 0 and edge.target in pr:
                    pr[edge.target] += damping_factor * (prev_pr[edge.source] / out_degree[edge.source])

            for node_id in self._nodes:
                diff += abs(pr[node_id] - prev_pr.get(node_id, 0.0))

            if diff < tolerance:
                break

        return pr

    def compute_affinity_score(self, target_node_id: str) -> Dict[str, float]:
        """
        Calculates latent semantic affinity against a target node (e.g. @telmodinamico).
        """
        if target_node_id not in self._nodes:
            raise KeyError(f"Target node {target_node_id} not in graph")

        target_emb = self._nodes[target_node_id].embedding
        if not target_emb:
            return {}

        affinities = {}
        target_mag = math.sqrt(sum(a * a for a in target_emb))

        if target_mag == 0.0:
            return {n_id: 0.0 for n_id in self._nodes}

        for node_id, node in self._nodes.items():
            if node_id == target_node_id:
                continue
            emb = node.embedding
            if not emb or len(emb) != len(target_emb):
                continue

            dot = sum(a * b for a, b in zip(emb, target_emb))
            mag = math.sqrt(sum(a * a for a in emb))
            aff = dot / (mag * target_mag) if mag > 0 else 0.0
            affinities[node_id] = aff

        return affinities

    def register_node(
        self,
        node_id: str,
        node_type: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> KnowledgeNode:
        node = KnowledgeNode(
            id=node_id,
            node_type=node_type,
            embedding=embedding,
            metadata=metadata or {},
        )
        self._nodes[node_id] = node
        return node

    def add_edge(
        self, source: str, target: str, relation: str, confidence: float
    ) -> KnowledgeEdge:
        edge = KnowledgeEdge(
            source=source,
            target=target,
            relation=relation,
            confidence=max(0.0, min(1.0, confidence)),
        )
        self._edges.append(edge)
        return edge

    def register_claim(
        self,
        proposition: str,
        source: str,
        evidence: List[str],
        counter_evidence: Optional[List[str]] = None,
    ) -> CausalClaim:
        raw_payload = f"{proposition}:{source}".encode("utf-8")
        claim_id = hashlib.sha3_256(raw_payload).hexdigest()
        c_ev = counter_evidence or []

        pos_weight = float(len(evidence))
        neg_weight = float(len(c_ev))
        total = pos_weight + neg_weight
        confidence = pos_weight / total if total > 0.0 else 0.5

        claim = CausalClaim(
            claim_id=claim_id,
            proposition=proposition,
            evidence=evidence,
            counter_evidence=c_ev,
            confidence=confidence,
            source=source,
            temporal_evolution=[e.event_id for e in self._events],
        )
        self._claims[claim_id] = claim
        return claim

    def simulate_counterfactual(
        self, target_node_id: str, perturbation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Omega 9 Counterfactual Simulation Engine.
        Simulates network structural shift upon node mutation.
        """
        if target_node_id not in self._nodes:
            raise KeyError(f"Node {target_node_id} not present in graph topology")

        impacted_edges = [
            e for e in self._edges if e.source == target_node_id or e.target == target_node_id
        ]
        impacted_neighbors = list(
            {e.target if e.source == target_node_id else e.source for e in impacted_edges}
        )

        return {
            "target": target_node_id,
            "perturbation": perturbation,
            "impacted_edges_count": len(impacted_edges),
            "affected_neighbors": impacted_neighbors,
            "cascade_factor": len(impacted_neighbors) * 1.414,
        }

    def generate_hypotheses(self) -> List[Dict[str, Any]]:
        """
        Omega 6 Hypothesis Engine.
        Detects topological convergence between unlinked actors / nodes in semantic vector space.
        """
        hypotheses: List[Dict[str, Any]] = []
        node_ids = list(self._nodes.keys())
        for i in range(len(node_ids)):
            for j in range(i + 1, len(node_ids)):
                id1, id2 = node_ids[i], node_ids[j]
                n1, n2 = self._nodes[id1], self._nodes[id2]

                # Check if edge already exists
                has_edge = any(
                    (e.source == id1 and e.target == id2) or (e.source == id2 and e.target == id1)
                    for e in self._edges
                )
                if not has_edge and n1.embedding and n2.embedding and len(n1.embedding) == len(n2.embedding):
                    dot = sum(a * b for a, b in zip(n1.embedding, n2.embedding))
                    mag1 = math.sqrt(sum(a * a for a in n1.embedding))
                    mag2 = math.sqrt(sum(b * b for b in n2.embedding))
                    sim = dot / (mag1 * mag2) if mag1 > 0 and mag2 > 0 else 0.0

                    if sim > 0.8:
                        hypotheses.append({
                            "node_a": id1,
                            "node_b": id2,
                            "similarity": sim,
                            "hypothesis": f"Nodes {id1} and {id2} converge on latent vector space (sim={sim:.3f}) without explicit link."
                        })
        return hypotheses

    def detect_innovation_shift(
        self, baseline_embedding: List[float], new_embedding: List[float], threshold: float = 0.15
    ) -> Dict[str, Any]:
        """
        Omega 7 Innovation Detection Engine.
        Tracks vector displacement across global semantic space to signal emergent paradigm shifts.
        """
        if len(baseline_embedding) != len(new_embedding) or not baseline_embedding:
            return {"shift_detected": False, "displacement": 0.0, "reason": "Dimensionality mismatch"}

        diff_sq = sum((b - n) ** 2 for b, n in zip(baseline_embedding, new_embedding))
        displacement = math.sqrt(diff_sq)
        shift_detected = displacement >= threshold

        return {
            "shift_detected": shift_detected,
            "displacement": displacement,
            "threshold": threshold,
            "signal": "EMERGENT_PARADIGM_SHIFT" if shift_detected else "STABLE_LATENT_GEOMETRY",
        }

    def get_fractal_memory_hierarchy(self, node_id: str) -> Dict[str, Any]:
        """
        Omega 5 Fractal Memory Engine.
        Generates 7 tiers of memory representation for a given knowledge primitive.
        """
        if node_id not in self._nodes:
            raise KeyError(f"Node {node_id} not found")

        node = self._nodes[node_id]
        return {
            "node_id": node_id,
            "levels": {
                "1_raw": str(node.metadata),
                "2_parsed": {"type": node.node_type, "id": node.id},
                "3_embedded": node.embedding,
                "4_summarized": f"Node[{node.node_type}] - {node.id}",
                "5_concept_graph": [e.target for e in self._edges if e.source == node_id],
                "6_claim_graph": [c.claim_id for c in self._claims.values() if node_id in c.evidence],
                "7_prediction_graph": self.simulate_counterfactual(node_id, {"query": "abduction"}),
            }
        }

    def export_telemetry(self) -> Dict[str, Any]:
        return {
            "reality_level": "C5-REAL",
            "nodes_count": len(self._nodes),
            "edges_count": len(self._edges),
            "events_count": len(self._events),
            "claims_count": len(self._claims),
            "compression_status": CompressionPyramid.compute_exergy_density(len(self._events)),
        }

