import warnings
from typing import Any

import networkx as nx
import numpy as np

warnings.filterwarnings('ignore')

def get_structural_driver_nodes(G: nx.DiGraph) -> list[str]:
    B: nx.Graph = nx.Graph()
    out_nodes: list[tuple[str, str]] = [(str(n), 'out') for n in G.nodes()]
    in_nodes: list[tuple[str, str]] = [(str(n), 'in') for n in G.nodes()]
    B.add_nodes_from(out_nodes, bipartite=0)
    B.add_nodes_from(in_nodes, bipartite=1)
    for u, v in G.edges():
        B.add_edge((str(u), 'out'), (str(v), 'in'))
    matching = nx.bipartite.maximum_matching(B, top_nodes=out_nodes)
    matched_in_nodes = {k[0] for k, v in matching.items() if k[1] == 'in'} | {v[0] for k, v in matching.items() if v[1] == 'in'}
    return list(set(str(n) for n in G.nodes()) - matched_in_nodes)

def simulate_boolean_network(G: nx.DiGraph, initial_state: dict[str, int], steps: int=30, perturbed_nodes: dict[str, int] | None=None) -> tuple[list[Any], list[str]]:
    if perturbed_nodes is None:
        perturbed_nodes = {}
    current_state: dict[str, int] = initial_state.copy()
    nodes: list[str] = [str(n) for n in G.nodes()]
    A = nx.to_numpy_array(G, nodelist=list(G.nodes()))
    threshold: float = 0.5
    state_vector = np.array([current_state[n] for n in nodes])
    history: list[Any] = [state_vector]
    for _ in range(steps):
        inflow = A.T @ state_vector
        new_state_vector = (inflow >= threshold).astype(int)
        for p_node, val in perturbed_nodes.items():
            if p_node in nodes:
                idx = nodes.index(p_node)
                new_state_vector[idx] = val
        state_vector = new_state_vector
        history.append(state_vector)
        if np.array_equal(history[-1], history[-2]):
            break
    return (history, nodes)

def main() -> None:
    print('MOSKV-1 APEX: Iniciando Motor Empírico (WGCNA surrogate) y Aserción de Falsabilidad...')
    np.random.seed(42)
    N_SAMPLES = 200
    N_GENES = 50
    gene_names = [f'GEN_EMP_{i}' for i in range(N_GENES)]
    X_expr = np.random.normal(loc=5.0, scale=1.5, size=(N_SAMPLES, N_GENES))
    latent_factor = np.random.normal(loc=10.0, scale=3.0, size=(N_SAMPLES,))
    for i in range(5):
        X_expr[:, i] += latent_factor * 0.8 + np.random.normal(0, 0.5, N_SAMPLES)
    print(f'[DATA] Matriz de Expresión Empírica simulada: {X_expr.shape}')
    R = np.corrcoef(X_expr, rowvar=False)
    S = np.abs(R)
    beta = 6
    A = np.power(S, beta)
    threshold_bin = 0.15
    A_bin = (A > threshold_bin).astype(int)
    np.fill_diagonal(A_bin, 0)
    G_empirico = nx.from_numpy_array(A_bin, create_using=nx.DiGraph)
    G_empirico = nx.relabel_nodes(G_empirico, {i: gene_names[i] for i in range(N_GENES)})
    print(f'[GRAPH] Grafo Empírico Construido. Nodos: {G_empirico.number_of_nodes()}, Aristas: {G_empirico.number_of_edges()}')
    drivers_emp = get_structural_driver_nodes(G_empirico)
    print(f'[CONTROL] Driver Nodes detectados en matriz empírica: {len(drivers_emp)} nodos.')
    initial_state = {str(n): 1 for n in G_empirico.nodes()}
    hist_basal, _ = simulate_boolean_network(G_empirico, initial_state, steps=30)
    actividad_basal = np.sum(hist_basal[-1]) / N_GENES
    terapia_farmacos = {d: 0 for d in drivers_emp[:3]}
    hist_perturbado, _ = simulate_boolean_network(G_empirico, initial_state, steps=30, perturbed_nodes=terapia_farmacos)
    actividad_perturbada = np.sum(hist_perturbado[-1]) / N_GENES
    caida_atractor = float((actividad_basal - actividad_perturbada) * 100)
    print(f'\n[FALSABILIDAD] Caída del Atractor Tumoral (Exergía residual post-inhibición): {caida_atractor:.1f}%')
    UMBRAL_FALSACION = 40.0
    assert caida_atractor > UMBRAL_FALSACION, f'[ERROR C5-REAL] La intervención teórica solo alcanzó {caida_atractor:.1f}% de colapso. No supera el umbral crítico ({UMBRAL_FALSACION}%). Hipótesis REFUTADA. No derivar a ensayo In-Vitro.'
    print('[ÉXITO C5-REAL] Hipótesis topológica VALIDAD. La intervención supera el umbral termodinámico requerido para someterse a ensayo In-Vitro (CRISPR/Cas9).')
if __name__ == '__main__':
    main()