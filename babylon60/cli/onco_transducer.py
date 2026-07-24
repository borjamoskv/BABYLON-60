#!/usr/bin/env python3
# MOSKV-1 APEX: CLI ONCO TRANSDUCER (C5-REAL)
"""
Motor de CLI para transducción de datos transcriptómicos a modelos Booleanos.
Enfuerza la Regla Λ13 (Falsabilidad Empírica).
"""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

_ONCO_IMPORT_ERROR: Optional[BaseException]
try:
    import numpy as np
    import networkx as nx
    import pandas as pd
except ImportError as _exc:  # extra 'onco' no instalado
    np = None  # type: ignore[assignment]
    nx = None
    pd = None
    _ONCO_IMPORT_ERROR = _exc
else:
    _ONCO_IMPORT_ERROR = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [C5-REAL] %(levelname)s - %(message)s")
logger = logging.getLogger("OncoTransducer")


@dataclass(frozen=True)
class OncologySimulationResult:
    steps: int
    history: List[Dict[str, int]]
    initial_state: Dict[str, int]
    final_state: Dict[str, int]
    nodes: List[str]


class OncologyTransducer:
    """
    Orquestador C5-REAL para transducción y simulación de redes Booleanas oncológicas.
    """

    @classmethod
    def run_simulation(
        cls,
        initial_state: Dict[str, Any],
        steps: int = 30,
        graph: Optional[nx.DiGraph] = None,
        perturbed_nodes: Optional[Dict[str, Any]] = None,
    ) -> OncologySimulationResult:
        if graph is None:
            graph = nx.DiGraph()
            for k in initial_state.keys():
                graph.add_node(k)
                graph.add_edge(k, k)  # Auto-bucle para preservación basal si no se especifican aristas externas
            try:
                import babylon60.oncology_primitives as op_mod

                edges: Any = getattr(op_mod, "ONCOLOGY_PRIMITIVES_EDGES", [])
                for u, v in edges:
                    if u in initial_state and v in initial_state:
                        graph.add_edge(u, v)
            except (ImportError, AttributeError):
                pass

        raw_history, nodes = simulate_boolean_network(
            graph, initial_state, steps=steps, perturbed_nodes=perturbed_nodes, early_stop=False
        )
        history_dicts: List[Dict[str, int]] = []
        for vec in raw_history:
            history_dicts.append({nodes[i]: int(vec[i]) for i in range(len(nodes))})

        return OncologySimulationResult(
            steps=len(history_dicts) - 1,
            history=history_dicts,
            initial_state=history_dicts[0] if history_dicts else {str(k): int(v) for k, v in initial_state.items()},
            final_state=history_dicts[-1] if history_dicts else {str(k): int(v) for k, v in initial_state.items()},
            nodes=nodes,
        )


def construct_wgcna_graph(X: np.ndarray, gene_names: List[str], beta: int = 6, threshold: float = 0.15) -> nx.DiGraph:
    """Construye grafo empírico usando umbral WGCNA sobre correlación de Pearson."""
    logger.info("Calculando matriz de correlación de Pearson...")
    R = np.corrcoef(X, rowvar=False)
    S = np.abs(R)

    logger.info(f"Aplicando Soft-Thresholding (beta={beta}) y Hard Thresholding ({threshold})...")
    A = np.power(S, beta)
    A_bin = (A > threshold).astype(int)
    np.fill_diagonal(A_bin, 0)

    G = nx.from_numpy_array(A_bin, create_using=nx.DiGraph)
    G = nx.relabel_nodes(G, {i: gene_names[i] for i in range(len(gene_names))})
    return G


def get_structural_driver_nodes(G: nx.DiGraph) -> List[str]:
    """Extrae Driver Nodes mediante Maximum Bipartite Matching (Liu et al. 2011)."""
    B: nx.Graph = nx.Graph()
    out_nodes = [(n, "out") for n in G.nodes()]
    in_nodes = [(n, "in") for n in G.nodes()]
    B.add_nodes_from(out_nodes, bipartite=0)
    B.add_nodes_from(in_nodes, bipartite=1)

    for u, v in G.edges():
        B.add_edge((u, "out"), (v, "in"))

    matching = nx.bipartite.maximum_matching(B, top_nodes=out_nodes)
    matched_in_nodes = {k[0] for k, v in matching.items() if k[1] == "in"} | {
        v[0] for k, v in matching.items() if v[1] == "in"
    }

    return list(set(G.nodes()) - matched_in_nodes)


def simulate_boolean_network(
    G: nx.DiGraph,
    initial_state: Dict[str, Any],
    steps: int = 30,
    perturbed_nodes: Optional[Dict[str, Any]] = None,
    early_stop: bool = True,
) -> Tuple[List[Any], List[Any]]:
    """Simula atractor de red Booleana sincrónica."""
    if perturbed_nodes is None:
        perturbed_nodes = {}

    current_state = initial_state.copy()
    nodes = list(G.nodes())
    A = nx.to_numpy_array(G, nodelist=nodes)
    threshold = 0.5

    state_vector = np.array([current_state[n] for n in nodes])
    history = [state_vector]

    for _ in range(steps):
        inflow = A.T @ state_vector
        new_state_vector = (inflow >= threshold).astype(int)

        for p_node, val in perturbed_nodes.items():
            if p_node in nodes:
                idx = nodes.index(p_node)
                new_state_vector[idx] = val

        state_vector = new_state_vector
        history.append(state_vector)

        if early_stop and np.array_equal(history[-1], history[-2]):
            break

    return history, nodes


def execute_pipeline(data_path: str | None = None, falsifiability_threshold: float = 40.0) -> None:
    """Ejecuta el pipeline C5-REAL completo."""
    if data_path:
        logger.info(f"Cargando matriz empírica desde: {data_path}")
        df = pd.read_csv(data_path, sep="\t", index_col=0)
        X = df.values.T  # (Samples x Genes)
        gene_names = df.index.tolist()
    else:
        logger.warning("No data_path provided. Generando Matriz Surrogate C5-REAL...")
        np.random.seed(42)
        N_SAMPLES, N_GENES = 200, 50
        gene_names = [f"GEN_EMP_{i}" for i in range(N_GENES)]
        X = np.random.normal(loc=5.0, scale=1.5, size=(N_SAMPLES, N_GENES))
        latent_factor = np.random.normal(loc=10.0, scale=3.0, size=(N_SAMPLES,))
        for i in range(5):
            X[:, i] += latent_factor * 0.8 + np.random.normal(0, 0.5, N_SAMPLES)

    G = construct_wgcna_graph(X, gene_names)
    logger.info(f"Topología extraída: {G.number_of_nodes()} Nodos, {G.number_of_edges()} Aristas.")

    if G.number_of_edges() == 0:
        logger.error("Grafo vacío. Ajustar umbrales o verificar varianza de matriz.")
        sys.exit(1)

    drivers = get_structural_driver_nodes(G)
    logger.info(f"Driver Nodes extraídos: {len(drivers)}")

    if not drivers:
        logger.warning("No se hallaron Driver Nodes (red completamente aislada).")
        sys.exit(0)

    initial_state = {n: 1 for n in G.nodes()}

    hist_basal, _ = simulate_boolean_network(G, initial_state)
    act_basal = np.sum(hist_basal[-1]) / len(G.nodes())
    logger.info(f"Atractor Basal: {act_basal * 100:.1f}% de actividad en steady-state.")

    top_k = min(3, len(drivers))
    terapia = {d: 0 for d in drivers[:top_k]}
    logger.info(f"Aplicando terapia in-silico sobre: {list(terapia.keys())}")

    hist_pert, _ = simulate_boolean_network(G, initial_state, perturbed_nodes=terapia)
    act_pert = np.sum(hist_pert[-1]) / len(G.nodes())
    logger.info(f"Atractor Perturbado: {act_pert * 100:.1f}% de actividad residual.")

    delta = (act_basal - act_pert) * 100
    logger.info(f"Impacto Termodinámico (Caída del Atractor): {delta:.1f}%")

    # C5-REAL ASSERTION
    assert delta > falsifiability_threshold, (
        f"FALSABILIDAD REFUTADA: El colapso del {delta:.1f}% es menor al umbral {falsifiability_threshold}%."
    )

    logger.info("VERIFICACIÓN C5-REAL EXITOSA. Hipótesis apta para In-Vitro.")


def main() -> None:
    if _ONCO_IMPORT_ERROR is not None:
        print(
            "🔴 [FATAL] cortex-onco requiere el extra 'onco' (numpy, networkx, pandas).\n"
            "    Instalar con: pip install cortex-persist[onco]\n"
            f"    Error subyacente: {_ONCO_IMPORT_ERROR}",
            file=sys.stderr,
        )
        sys.exit(1)

    parser = argparse.ArgumentParser(description="MOSKV-1 Onco Transducer CLI")
    parser.add_argument(
        "--data", type=str, help="Path a la matriz TSV (genes en filas, muestras en columnas).", default=None
    )
    parser.add_argument("--threshold", type=float, default=40.0, help="Umbral de colapso termodinámico (0-100).")
    args = parser.parse_args()

    try:
        execute_pipeline(args.data, args.threshold)
    except AssertionError as e:
        logger.error(str(e))
        sys.exit(1)
    except (OSError, ValueError, RuntimeError, MemoryError) as e:
        logger.error(f"Error estructural fatal: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
