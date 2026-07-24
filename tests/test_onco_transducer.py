import pytest

# [C5-REAL] Optional-dependency gate: onco stack (numpy/networkx/pandas) is an
np = pytest.importorskip("numpy")
nx = pytest.importorskip("networkx")
pytest.importorskip("pandas")

from babylon60.cli.onco_transducer import (  # noqa: E402
    construct_wgcna_graph,
    get_structural_driver_nodes,
    simulate_boolean_network,
)


def test_exergy_extraction() -> None:
    """
    Prueba que el control estructural funcione perfectamente.
    En una cadena A -> B -> C, el único nodo incontrolado es A (no tiene 'in').
    Por lo tanto, 'A' debe ser el driver node.
    """
    G = nx.DiGraph()
    G.add_edges_from([("A", "B"), ("B", "C")])
    drivers = get_structural_driver_nodes(G)
    assert "A" in drivers
    assert len(drivers) == 1


def test_entropy_injection() -> None:
    """
    Prueba que inhibir un nodo upstream en un pipeline Booleano apaga los downstream.
    G: A -> B -> C
    Umbral es 0.5. Si A = 0, B recibe 0 -> se apaga. C recibe 0 -> se apaga.
    """
    G = nx.DiGraph()
    G.add_edges_from([("A", "B"), ("B", "C")])

    initial = {"A": 1, "B": 1, "C": 1}


    history_force, _ = simulate_boolean_network(G, initial, steps=10, perturbed_nodes={"A": 1})
    assert np.sum(history_force[-1]) == 3.0  # Todos en 1

    history_knock, _ = simulate_boolean_network(G, initial, steps=10, perturbed_nodes={"A": 0})
    assert np.sum(history_knock[-1]) == 0.0  # Todos caen a 0 (Colapso total)


def test_onco_transducer_initialization() -> None:
    """
    Prueba de integración matemática de umbrales.
    Si proveemos dos genes perfectamente correlacionados, deben formar una arista.
    Si proveemos dos sin correlación, no deben.
    """
    X = np.array([[1.0, 1.0, 0.5], [2.0, 2.0, 0.1], [3.0, 3.0, 0.9], [4.0, 4.0, 0.2], [5.0, 5.0, 0.8]])
    G = construct_wgcna_graph(X, gene_names=["G0", "G1", "G2"], beta=1, threshold=0.9)
    assert G.has_edge("G0", "G1")
    assert G.has_edge("G1", "G0")
    assert not G.has_edge("G0", "G2")
