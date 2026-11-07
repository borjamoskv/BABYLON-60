# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Topological 1-WL Filters

import hashlib
from typing import Any, Dict, List, Set, Tuple


def compute_1wl_hash(nodes: List[str], edges: List[Tuple[str, str]], iterations: int = 3) -> str:
    """
    INV_C5_28: 1-Dimensional Weisfeiler-Lehman O(V+E) Graph Isomorphism Pre-Filter.
    Calculates a topological hash that guarantees causal determinism regardless of byte ordering.
    """
    if not nodes:
        return hashlib.sha3_256(b"").hexdigest()

    colors: Dict[str, str] = {node: "0" for node in nodes}
    adj: Dict[str, List[str]] = {node: [] for node in nodes}

    # Build undirected adjacency list
    for u, v in edges:
        if u in adj and v in adj:
            adj[u].append(v)
            adj[v].append(u)

    for _ in range(iterations):
        new_colors = {}
        for node in nodes:
            neighbor_colors = sorted([colors[nbr] for nbr in adj[node]])
            signature = f"{colors[node]}|" + ",".join(neighbor_colors)
            new_colors[node] = hashlib.sha256(signature.encode("utf-8")).hexdigest()[:16]
        colors = new_colors

    canonical = "|".join(sorted(colors.values()))
    return hashlib.sha3_256(canonical.encode("utf-8")).hexdigest()


def json_to_graph(json_data: Any) -> Tuple[List[str], List[Tuple[str, str]]]:
    """
    Parses a JSON object (dict/list) into a graph of (nodes, edges).
    Nodes are paths or stringified primitive values to capture structural relationships.
    Edges connect parent nodes to their nested children or values.
    """
    nodes: Set[str] = set()
    edges: Set[Tuple[str, str]] = set()

    def traverse(obj: Any, parent_id: str = "ROOT") -> None:
        nodes.add(parent_id)

        if isinstance(obj, dict):
            # Sort keys to ensure deterministic traversal if not building fully symmetric graphs
            # However, since 1-WL is permutation invariant, key order strictly doesn't matter for the hash,
            # but we need deterministic node identifiers to prevent accidental disjointing.
            for k, v in obj.items():
                child_id = f"{parent_id}.{k}"
                nodes.add(child_id)
                edges.add((parent_id, child_id))
                traverse(v, child_id)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                # For arrays, position might matter. If we want pure set semantics, we wouldn't use `i`.
                # For causal JSON arrays, order is often important, so we encode it in the node ID.
                child_id = f"{parent_id}[{i}]"
                nodes.add(child_id)
                edges.add((parent_id, child_id))
                traverse(v, child_id)
        else:
            # Primitive values (str, int, float, bool, None)
            val_id = f"{parent_id}->{str(obj)}"
            nodes.add(val_id)
            edges.add((parent_id, val_id))

    traverse(json_data)
    return list(nodes), list(edges)
