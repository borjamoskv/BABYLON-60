import pytest

np = pytest.importorskip("numpy")
nx = pytest.importorskip("networkx")
pytest.importorskip("pandas")
from babylon60.cli.onco_transducer import (  # noqa: E402
    construct_wgcna_graph,
    get_structural_driver_nodes,
    simulate_boolean_network,
)


def test_exergy_extraction() -> None:
    G = nx.DiGraph()
    G.add_edges_from([("A", "B"), ("B", "C")])
    drivers = get_structural_driver_nodes(G)
    assert "A" in drivers
    assert len(drivers) == 1


def test_entropy_injection() -> None:
    G = nx.DiGraph()
    G.add_edges_from([("A", "B"), ("B", "C")])
    initial = {"A": 1, "B": 1, "C": 1}
    history_force, _ = simulate_boolean_network(G, initial, steps=10, perturbed_nodes={"A": 1})
    assert np.sum(history_force[-1]) == 3.0
    history_knock, _ = simulate_boolean_network(G, initial, steps=10, perturbed_nodes={"A": 0})
    assert np.sum(history_knock[-1]) == 0.0


def test_onco_transducer_initialization() -> None:
    X = np.array([[1.0, 1.0, 0.5], [2.0, 2.0, 0.1], [3.0, 3.0, 0.9], [4.0, 4.0, 0.2], [5.0, 5.0, 0.8]])
    G = construct_wgcna_graph(X, gene_names=["G0", "G1", "G2"], beta=1, threshold=0.9)
    assert G.has_edge("G0", "G1")
    assert G.has_edge("G1", "G0")
    assert not G.has_edge("G0", "G2")
