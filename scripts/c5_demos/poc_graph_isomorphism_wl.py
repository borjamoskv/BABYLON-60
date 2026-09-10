#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ WEISFEILER-LEHMAN GRAPH ISOMORPHISM | C5-REAL (INV_C5_28)
# ============================================================================
"""
Proof of Concept: 1-Weisfeiler-Lehman Graph Isomorphism Pre-Filter.
Enforces O(V+E) rejection of non-isomorphic topologies before expensive
bijective verification.
"""

import hashlib
from typing import Dict, List, Any


def _hash_tokens(*tokens: str) -> str:
    hasher = hashlib.sha256()
    for token in tokens:
        hasher.update(token.encode("utf-8"))
    return hasher.hexdigest()


def weisfeiler_lehman_hash(adj_list: Dict[Any, List[Any]], max_iterations: int = 3) -> str:
    """
    Computes the 1-WL canonical color multiset hash for an adjacency list.
    Nodes can have arbitrary hashable IDs.
    """
    if not adj_list:
        return "WL1_EMPTY"

    # Initial color based on degree (INV_C5_28)
    colors: Dict[Any, str] = {
        node: f"deg:{len(neighbors)}"
        for node, neighbors in adj_list.items()
    }

    iters = min(max_iterations, 10)
    for _ in range(iters):
        next_colors: Dict[Any, str] = {}
        for node, neighbors in adj_list.items():
            nbr_colors = [colors[nbr] for nbr in neighbors if nbr in colors]
            nbr_colors.sort()
            next_colors[node] = _hash_tokens(colors[node], *nbr_colors)
        colors = next_colors

    # Global multiset hash over canonical sorted colors
    all_colors = sorted(colors.values())
    return _hash_tokens(*all_colors)


def verify_isomorphism(g1: Dict[Any, List[Any]], g2: Dict[Any, List[Any]], max_iterations: int = 3) -> bool:
    """
    Pre-filters graph isomorphism via 1-WL hash comparison in O(V+E) time,
    followed by degree multiset equivalence check.
    """
    if len(g1) != len(g2):
        return False

    if not g1 and not g2:
        return True

    # 1-WL Pre-filter (INV_C5_28)
    wl1 = weisfeiler_lehman_hash(g1, max_iterations=max_iterations)
    wl2 = weisfeiler_lehman_hash(g2, max_iterations=max_iterations)
    if wl1 != wl2:
        return False

    # Degree sequence equality check
    deg1 = sorted(len(v) for v in g1.values())
    deg2 = sorted(len(v) for v in g2.values())
    if deg1 != deg2:
        return False

    return True


if __name__ == "__main__":
    g_a = {0: [1, 2], 1: [0, 2, 3], 2: [0, 1], 3: [1]}
    g_b = {10: [11, 12], 11: [10, 12, 13], 12: [10, 11], 13: [11]}
    g_c = {0: [1, 2, 3], 1: [0], 2: [0], 3: [0]}

    print("WL(g_a):", weisfeiler_lehman_hash(g_a))
    print("WL(g_b):", weisfeiler_lehman_hash(g_b))
    print("WL(g_c):", weisfeiler_lehman_hash(g_c))
    print("Isomorphic(g_a, g_b):", verify_isomorphism(g_a, g_b))
    print("Isomorphic(g_a, g_c):", verify_isomorphism(g_a, g_c))
