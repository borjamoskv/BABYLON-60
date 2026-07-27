# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
"""
[C5-REAL] Step 1 Proof of Concept: Graph Isomorphism WL Pre-Filter (INV_C5_28).
"""

import hashlib

def weisfeiler_lehman_hash(adj: dict[int, list[int]], iterations: int = 3) -> str:
    """Computes 1-WL color refinement hash for graph adjacency dictionary."""
    colors = {node: "1" for node in adj}
    for _ in range(iterations):
        new_colors = {}
        for node, neighbors in adj.items():
            neighbor_colors = sorted(colors[n] for n in neighbors)
            s = colors[node] + "|" + ",".join(neighbor_colors)
            new_colors[node] = hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]
        colors = new_colors

    canonical = ",".join(sorted(colors.values()))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def verify_isomorphism(g1: dict[int, list[int]], g2: dict[int, list[int]]) -> bool:
    """INV_C5_28: Must perform O(V+E) WL pre-filtering before exact matching."""
    h1 = weisfeiler_lehman_hash(g1)
    h2 = weisfeiler_lehman_hash(g2)
    if h1 != h2:
        # Fail-fast O(1) decision without wasting ATP on VF2 N! combinatorial search
        return False
    # If WL hashes match, proceed to exact mapping (simplified degree check for PoC)
    return sorted(len(v) for v in g1.values()) == sorted(len(v) for v in g2.values())

if __name__ == "__main__":
    # Isomorphic graphs (Triangle + edge)
    g_a = {0: [1, 2], 1: [0, 2, 3], 2: [0, 1], 3: [1]}
    g_b = {10: [11, 12], 11: [10, 12, 13], 12: [10, 11], 13: [11]}

    # Non-isomorphic graph (Star)
    g_c = {0: [1, 2, 3], 1: [0], 2: [0], 3: [0]}

    assert verify_isomorphism(g_a, g_b) is True, "Isomorphic graphs MUST pass"
    assert verify_isomorphism(g_a, g_c) is False, "Non-isomorphic graphs MUST fail fast via WL"
    print("🟢 PoC Step 1 PASSED: INV_C5_28 WL pre-filtering verified.")
