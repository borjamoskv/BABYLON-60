#!/usr/bin/env python3
"""Directed multigraph isomorphism: an incomplete WL filter plus exact search.

Node IDs are arbitrary hashable names, not semantic labels. Every vertex must be
an adjacency key; repeated neighbors represent parallel arcs and self-loops are
allowed. Hash profile v2 changes the old digest bytes; persisted v1 commitments
must retain their original verifier. No linear-time isomorphism claim is made.
"""

from collections import Counter
import hashlib
from typing import Any, Dict, List

WL_HASH_PROFILE = "b60-wl-directed-multigraph-v2"
DEFAULT_MAX_SEARCH_STATES = 100_000


class IsomorphismSearchLimitExceeded(RuntimeError):
    """Exact search exhausted its candidate-extension budget without a verdict."""


def _hash_tokens(*tokens: str) -> str:
    """Length-frame UTF-8 tokens so distinct token boundaries remain distinct."""
    hasher = hashlib.sha256()
    for token in tokens:
        encoded = token.encode("utf-8")
        hasher.update(len(encoded).to_bytes(8, "big"))
        hasher.update(encoded)
    return hasher.hexdigest()


def _round_count(max_iterations: int) -> int:
    if type(max_iterations) is not int or max_iterations < 0:
        raise ValueError("max_iterations must be a nonnegative integer")
    return min(max_iterations, 10)


def _validated_graph(adj_list: Dict[Any, List[Any]]) -> Dict[Any, Counter]:
    if not isinstance(adj_list, dict):
        raise ValueError("a graph must be an adjacency dictionary")
    graph: Dict[Any, Counter] = {}
    for node, neighbors in adj_list.items():
        if not isinstance(neighbors, (list, tuple)):
            raise ValueError("each adjacency value must be a list or tuple")
        counts: Counter = Counter()
        for neighbor in neighbors:
            try:
                exists = neighbor in adj_list
            except TypeError as error:
                raise ValueError("neighbor IDs must be hashable") from error
            if not exists:
                raise ValueError("every referenced vertex must be an adjacency key")
            counts[neighbor] += 1
        graph[node] = counts
    return graph


def _refine_colors(graph: Dict[Any, Counter], rounds: int) -> Dict[Any, str]:
    incoming: Dict[Any, Counter] = {node: Counter() for node in graph}
    for node, neighbors in graph.items():
        for neighbor, count in neighbors.items():
            incoming[neighbor][node] += count
    colors = {
        node: _hash_tokens(str(sum(incoming[node].values())), str(sum(neighbors.values())), str(neighbors[node]))
        for node, neighbors in graph.items()
    }
    for _ in range(rounds):
        # Read only the prior round, including incoming direction and multiplicity.
        colors = {
            node: _hash_tokens(
                colors[node],
                "in",
                *sorted(colors[neighbor] for neighbor in incoming[node].elements()),
                "out",
                *sorted(colors[neighbor] for neighbor in neighbors.elements()),
            )
            for node, neighbors in graph.items()
        }
    return colors


def weisfeiler_lehman_hash(adj_list: Dict[Any, List[Any]], max_iterations: int = 3) -> str:
    """Return a versioned isomorphism-invariant filter, not a canonical form.

    At most ten simultaneous rounds are used. Equal digests do not prove
    isomorphism; input processing, hashing and sorting all contribute to cost.
    """
    rounds = _round_count(max_iterations)
    graph = _validated_graph(adj_list)
    colors = _refine_colors(graph, rounds)
    return "WL1_V2:" + _hash_tokens(WL_HASH_PROFILE, str(rounds), *sorted(colors.values()))


def verify_isomorphism(
    g1: Dict[Any, List[Any]],
    g2: Dict[Any, List[Any]],
    max_iterations: int = 3,
    *,
    max_search_states: int = DEFAULT_MAX_SEARCH_STATES,
) -> bool:
    """Decide exact directed multigraph isomorphism if search completes.

    A positive result requires a bijection preserving every arc multiplicity,
    direction and self-loop. Worst-case search is exponential. Malformed inputs
    raise ValueError; budget exhaustion raises IsomorphismSearchLimitExceeded,
    never a guessed boolean. The budget counts attempted candidate extensions,
    not elapsed time, total preprocessing work or a production resource bound.
    """
    rounds = _round_count(max_iterations)
    if type(max_search_states) is not int or max_search_states <= 0:
        raise ValueError("max_search_states must be a positive integer")
    # Validate both inputs even when a size or digest comparison would reject.
    first = _validated_graph(g1)
    second = _validated_graph(g2)
    if len(first) != len(second):
        return False
    if not first:
        return True
    left_colors = _refine_colors(first, rounds)
    right_colors = _refine_colors(second, rounds)
    if sorted(left_colors.values()) != sorted(right_colors.values()):
        return False
    candidates = {
        node: [other for other in second if right_colors[other] == color]
        for node, color in left_colors.items()
    }
    order = sorted(first, key=lambda node: (len(candidates[node]), -sum(first[node].values())))
    mapping: Dict[Any, Any] = {}
    used = set()
    next_candidate = [0] * len(order)
    depth = 0
    states = 0
    # Iterative backtracking avoids a recursion-depth failure on larger inputs.
    while depth >= 0:
        if depth == len(order):
            return True
        node = order[depth]
        advanced = False
        choices = candidates[node]
        while next_candidate[depth] < len(choices):
            other = choices[next_candidate[depth]]
            next_candidate[depth] += 1
            if other in used:
                continue
            states += 1
            if states > max_search_states:
                raise IsomorphismSearchLimitExceeded("exact isomorphism search budget exhausted")
            if first[node][node] != second[other][other]:
                continue
            if any(
                first[node][mapped] != second[other][image]
                or first[mapped][node] != second[image][other]
                for mapped, image in mapping.items()
            ):
                continue
            mapping[node] = other
            used.add(other)
            depth += 1
            if depth < len(order):
                next_candidate[depth] = 0
            advanced = True
            break
        if not advanced:
            next_candidate[depth] = 0
            depth -= 1
            if depth >= 0:
                used.remove(mapping.pop(order[depth]))
    return False


if __name__ == "__main__":
    g_a = {0: [1, 2], 1: [0, 2, 3], 2: [0, 1], 3: [1]}
    g_b = {10: [11, 12], 11: [10, 12, 13], 12: [10, 11], 13: [11]}
    g_c = {0: [1, 2, 3], 1: [0], 2: [0], 3: [0]}
    print("WL filter(g_a):", weisfeiler_lehman_hash(g_a))
    print("WL filter(g_b):", weisfeiler_lehman_hash(g_b))
    print("WL filter(g_c):", weisfeiler_lehman_hash(g_c))
    print("Exact isomorphism(g_a, g_b):", verify_isomorphism(g_a, g_b))
    print("Exact isomorphism(g_a, g_c):", verify_isomorphism(g_a, g_c))
