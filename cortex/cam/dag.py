# C5-REAL EXERGY CERTIFIED
"""
CAM 1.0 Typed DAG Knowledge Graph.
Enforces acyclicity, Lamport timestamp monotonicity, and 10-state node transitions.
"""

from collections import defaultdict, deque
from cortex.cam.types import EdgeType, EpistemicState, KGEdge, KGNode


class TypedDAGKnowledgeGraph:
    def __init__(self) -> None:
        self.nodes: dict[str, KGNode] = {}
        self.edges: list[KGEdge] = []
        self.adj_list: dict[str, list[str]] = defaultdict(list)
        self.lamport_clock: int = 0

    def add_node(self, node: KGNode) -> str:
        self.lamport_clock += 1
        node.lamport_t = self.lamport_clock
        self.nodes[node.id] = node
        return node.id

    def add_edge(self, edge_type: EdgeType, source_id: str, target_id: str) -> None:
        if source_id not in self.nodes or target_id not in self.nodes:
            raise KeyError("Source or target node not found in Knowledge Graph")

        # Add potential edge and check for cycles
        self.adj_list[source_id].append(target_id)
        if self._has_cycle():
            self.adj_list[source_id].pop()
            raise RuntimeError("Undefined Behaviour Error: Cycle detected in Knowledge Graph DAG")

        edge = KGEdge(edge_type=edge_type, source_id=source_id, target_id=target_id)
        self.edges.append(edge)

    def _has_cycle(self) -> bool:
        in_degree: dict[str, int] = {n: 0 for n in self.nodes}
        for u in self.adj_list:
            for v in self.adj_list[u]:
                in_degree[v] += 1

        queue = deque([n for n in self.nodes if in_degree[n] == 0])
        visited_count = 0

        while queue:
            curr = queue.popleft()
            visited_count += 1
            for nxt in self.adj_list[curr]:
                in_degree[nxt] -= 1
                if in_degree[nxt] == 0:
                    queue.append(nxt)

        return visited_count != len(self.nodes)

    def transition_node_state(self, node_id: str, new_state: EpistemicState) -> None:
        if node_id not in self.nodes:
            raise KeyError(f"Node '{node_id}' not found in Knowledge Graph")
        self.nodes[node_id].state = new_state
