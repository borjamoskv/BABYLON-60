# C5-REAL EXERGY CERTIFIED
"""
CAM 2.0 Evolutionary Hypergraph.
Supports 1st-order causal edges (acyclic) and 2nd-order metadata feedback edges (cyclic adaptation).
Preserves dissenting branches during contradiction adjudication.
"""

from collections import defaultdict, deque
from cortex.cam.types import (
    AdjudicationRecord,
    EdgeOrder,
    EdgeType,
    EpistemicState,
    KGEdge,
    KGNode,
)


class CAM2Hypergraph:
    def __init__(self) -> None:
        self.nodes: dict[str, KGNode] = {}
        self.edges: list[KGEdge] = []
        self.causal_adj: dict[str, list[str]] = defaultdict(list)
        self.feedback_adj: dict[str, list[str]] = defaultdict(list)
        self.adjudications: list[AdjudicationRecord] = []
        self.lamport_clock: int = 0

    def add_node(self, node: KGNode) -> str:
        self.lamport_clock += 1
        node.lamport_t = self.lamport_clock
        self.nodes[node.id] = node
        return node.id

    def add_edge(
        self,
        edge_type: EdgeType,
        source_id: str,
        target_id: str,
        order: EdgeOrder = EdgeOrder.FIRST_ORDER_CAUSAL,
    ) -> None:
        if source_id not in self.nodes or target_id not in self.nodes:
            raise KeyError("Source or target node not found in Hypergraph")

        if order == EdgeOrder.FIRST_ORDER_CAUSAL:
            self.causal_adj[source_id].append(target_id)
            if self._has_causal_cycle():
                self.causal_adj[source_id].pop()
                raise RuntimeError("Undefined Behaviour Error: Cycle detected in 1st-order causal edges")
        else:
            self.feedback_adj[source_id].append(target_id)

        edge = KGEdge(
            edge_type=edge_type,
            source_id=source_id,
            target_id=target_id,
            order=order,
        )
        self.edges.append(edge)

    def _has_causal_cycle(self) -> bool:
        in_degree: dict[str, int] = {n: 0 for n in self.nodes}
        for u in self.causal_adj:
            for v in self.causal_adj[u]:
                in_degree[v] += 1

        queue = deque([n for n in self.nodes if in_degree[n] == 0])
        visited_count = 0

        while queue:
            curr = queue.popleft()
            visited_count += 1
            for nxt in self.causal_adj[curr]:
                in_degree[nxt] -= 1
                if in_degree[nxt] == 0:
                    queue.append(nxt)

        return visited_count != len(self.nodes)

    def adjudicate_conflict(
        self,
        claim_a_id: str,
        claim_b_id: str,
        winner_id: str,
        rationale: str,
    ) -> AdjudicationRecord:
        dissenting_id = claim_b_id if winner_id == claim_a_id else claim_a_id

        # Mark winner as VERIFIED, mark dissenter as REFUTED but preserve in graph
        self.nodes[winner_id].state = EpistemicState.VERIFIED
        self.nodes[dissenting_id].state = EpistemicState.REFUTED

        record = AdjudicationRecord(
            claim_a_id=claim_a_id,
            claim_b_id=claim_b_id,
            winning_claim_id=winner_id,
            dissenting_branch_id=dissenting_id,
            rationale=rationale,
        )
        self.adjudications.append(record)
        return record
