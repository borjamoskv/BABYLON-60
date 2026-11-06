"""Finite graph regressions and an independent permutation oracle, not a runtime proof."""

from collections import Counter
from itertools import combinations_with_replacement, permutations

import pytest

from scripts.c5_demos import poc_graph_isomorphism_wl as graph_wl
from scripts.c5_isomorphisms.c5_ultimate_causal_determinant import ThermodynamicVetoTransducer


def adjacency(edges, n):
    return {node: [target for source, target in edges if source == node] for node in range(n)}


def undirected(edges, n):
    return adjacency(list(edges) + [(v, u) for u, v in edges], n)


def relabel(graph, labels):
    names = dict(zip(graph, labels, strict=True))
    return {names[v]: [names[w] for w in reversed(neighbors)] for v, neighbors in reversed(list(graph.items()))}


def permutation_oracle(left, right):
    """Check every bijection directly, without WL, colors or implementation helpers."""
    if len(left) != len(right):
        return False
    left_nodes = tuple(left)
    for image in permutations(right):
        mapping = dict(zip(left_nodes, image, strict=True))
        if all(Counter(mapping[v] for v in left[u]) == Counter(right[mapping[u]]) for u in left_nodes):
            return True
    return False


def test_audited_dags_have_equal_wl_but_are_not_isomorphic():
    first = adjacency([(0, 4), (0, 5), (1, 5), (1, 6), (2, 6), (2, 7), (3, 7), (3, 4)], 8)
    second = adjacency([(0, 4), (0, 5), (1, 4), (1, 5), (2, 6), (2, 7), (3, 6), (3, 7)], 8)
    assert graph_wl.weisfeiler_lehman_hash(first) == graph_wl.weisfeiler_lehman_hash(second)
    assert graph_wl.verify_isomorphism(first, second) is False


def test_connected_regular_graphs_require_the_exact_check():
    prism = undirected([(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3), (0, 3), (1, 4), (2, 5)], 6)
    bipartite = undirected([(u, v) for u in range(3) for v in range(3, 6)], 6)
    assert graph_wl.weisfeiler_lehman_hash(prism) == graph_wl.weisfeiler_lehman_hash(bipartite)
    assert permutation_oracle(prism, bipartite) is False
    assert graph_wl.verify_isomorphism(prism, bipartite) is False


def test_all_three_node_simple_directed_graphs_match_independent_oracle():
    edges = [(u, v) for u in range(3) for v in range(3) if u != v]
    corpus = [adjacency([edge for bit, edge in enumerate(edges) if mask & (1 << bit)], 3) for mask in range(64)]
    for left, right in combinations_with_replacement(corpus, 2):
        assert graph_wl.verify_isomorphism(left, right) is permutation_oracle(left, right)


def test_four_node_multigraph_corpus_matches_independent_oracle():
    corpus = [
        adjacency([], 4),
        adjacency([(0, 0)], 4),
        adjacency([(0, 1), (0, 1), (1, 2)], 4),
        adjacency([(0, 1), (1, 0), (2, 3)], 4),
        adjacency([(0, 1), (1, 2), (2, 3), (3, 0)], 4),
        adjacency([(0, 1), (0, 2), (1, 3), (2, 3)], 4),
        adjacency([(0, 0), (0, 1), (1, 1), (1, 2), (2, 3), (3, 3)], 4),
    ]
    corpus += [relabel(graph, ["a", 7, ("node",), None]) for graph in corpus]
    for left, right in combinations_with_replacement(corpus, 2):
        assert graph_wl.verify_isomorphism(left, right) is permutation_oracle(left, right)


@pytest.mark.parametrize("rounds", [0, 1, 3, 10, 20])
def test_directed_hash_and_exact_check_ignore_node_and_neighbor_order(rounds):
    graph = {0: [0, 1, 1], 1: [2, 0], 2: [], 3: [2]}
    renamed = relabel(graph, ["mixed", 9, ("tuple",), None])
    assert graph_wl.weisfeiler_lehman_hash(graph, rounds) == graph_wl.weisfeiler_lehman_hash(renamed, rounds)
    assert graph_wl.verify_isomorphism(graph, renamed, rounds) is True


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ({0: [1, 2], 1: [], 2: []}, {0: [], 1: [0], 2: [0]}),
        ({0: [1, 1], 1: []}, {0: [1], 1: [0]}),
        ({0: [0], 1: []}, {0: [1], 1: []}),
    ],
)
def test_direction_multiplicity_and_self_loops_are_preserved(left, right):
    assert permutation_oracle(left, right) is False
    assert graph_wl.verify_isomorphism(left, right) is False


@pytest.mark.parametrize("malformed", [None, [], {0: [1]}, {0: None}, {0: "node"}, {0: [[0]]}])
def test_malformed_graphs_raise_before_size_or_hash_early_return(malformed):
    with pytest.raises(ValueError):
        graph_wl.weisfeiler_lehman_hash(malformed)
    with pytest.raises(ValueError):
        graph_wl.verify_isomorphism(malformed, {})
    with pytest.raises(ValueError):
        graph_wl.verify_isomorphism({}, malformed)


@pytest.mark.parametrize("rounds", [-1, 1.5, True])
def test_invalid_refinement_limits_are_explicit_errors(rounds):
    with pytest.raises(ValueError):
        graph_wl.weisfeiler_lehman_hash({}, rounds)
    with pytest.raises(ValueError):
        graph_wl.verify_isomorphism({}, {}, rounds)


def test_length_framing_does_not_merge_distinct_token_sequences():
    assert graph_wl._hash_tokens("ab", "c") != graph_wl._hash_tokens("a", "bc")
    assert graph_wl._hash_tokens("") != graph_wl._hash_tokens()


def test_search_budget_exhaustion_is_an_error_not_a_boolean_verdict():
    left = {0: [1], 1: []}
    right = {"a": ["b"], "b": []}
    with pytest.raises(graph_wl.IsomorphismSearchLimitExceeded):
        graph_wl.verify_isomorphism(left, right, max_search_states=1)


def test_budget_exhaustion_does_not_report_a_nonisomorphism_verdict():
    prism = undirected([(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3), (0, 3), (1, 4), (2, 5)], 6)
    bipartite = undirected([(u, v) for u in range(3) for v in range(3, 6)], 6)
    with pytest.raises(graph_wl.IsomorphismSearchLimitExceeded):
        graph_wl.verify_isomorphism(prism, bipartite, max_search_states=1)


@pytest.mark.parametrize("budget", [0, -1, 1.5, True])
def test_invalid_search_budget_is_an_explicit_error(budget):
    with pytest.raises(ValueError):
        graph_wl.verify_isomorphism({}, {}, max_search_states=budget)


def test_undirected_hash_uses_simultaneous_colors_for_every_node_order():
    edges = [("a", "b"), ("b", "c")]
    hashes = {ThermodynamicVetoTransducer.compute_1wl_hash(list(order), edges) for order in permutations("abc")}
    assert len(hashes) == 1


def test_undirected_hash_ignores_edge_order_orientation_and_node_names():
    hash_graph = ThermodynamicVetoTransducer.compute_1wl_hash
    expected = hash_graph(["a", "b", "c"], [("a", "b"), ("a", "b"), ("b", "c"), ("c", "c")])
    assert expected == hash_graph(["z", "x", "y"], [("z", "z"), ("z", "y"), ("y", "x"), ("x", "y")])
    assert expected == hash_graph(["c", "a", "b"], [("c", "c"), ("c", "b"), ("b", "a"), ("a", "b")])


@pytest.mark.parametrize(
    ("nodes", "edges"),
    [
        (["a", "a"], []),
        (["a"], [("a", "missing")]),
        (["a"], [("a",)]),
        (["a"], [("a", "a", "a")]),
        ([[]], []),
        (["a"], [("a", [])]),
        (None, []),
        ("a", []),
        (["a"], None),
        (["a"], ""),
    ],
)
def test_undirected_hash_rejects_duplicate_nodes_and_malformed_edges(nodes, edges):
    with pytest.raises(ValueError):
        ThermodynamicVetoTransducer.compute_1wl_hash(nodes, edges)


def test_empty_graph_and_isolated_vertices_have_explicit_semantics():
    assert graph_wl.verify_isomorphism({}, {}) is True
    assert graph_wl.verify_isomorphism({0: []}, {}) is False
    assert graph_wl.verify_isomorphism({0: [], 1: []}, {"a": [], "b": []}) is True
