# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ DISCRETE_CURVATURE | C5-REAL Tensor Demolition (Triple Rigor)
# ============================================================================

import numpy as np
import networkx as nx
from typing import Dict, Tuple, Any

def compute_effective_resistance(G: nx.Graph) -> float:
    """
    Computes the total effective resistance of the graph via the Moore-Penrose 
    pseudoinverse of the graph Laplacian.
    This replaces the ill-posed 'ghost pressure' scalar.
    """
    if G.number_of_nodes() < 2:
        return 0.0
    
    L = nx.laplacian_matrix(G.to_undirected()).toarray()
    L_pinv = np.linalg.pinv(L)
    
    # Total effective resistance = N * Trace(L_pinv)
    R_eff = G.number_of_nodes() * np.trace(L_pinv)
    return float(R_eff)

def compute_forman_ricci_curvature(G: nx.Graph) -> Dict[Tuple[Any, Any], float]:
    """
    Computes the Discrete Forman-Ricci Curvature for each edge in the graph.
    Formula: F(e) = 4 - d(u) - d(v) + 3 * #triangles(e)
    Highly negative curvature indicates structural bottlenecks (real technical debt).
    """
    curvature_map = {}
    for u, v in G.edges():
        d_u = G.degree(u)
        d_v = G.degree(v)
        
        common_neighbors = 0
        if G.is_directed():
            u_succ = set(G.successors(u)) | set(G.predecessors(u))
            v_succ = set(G.successors(v)) | set(G.predecessors(v))
            common_neighbors = len(u_succ.intersection(v_succ))
        else:
            common_neighbors = len(list(nx.common_neighbors(G, u, v)))
            
        f_e = 4 - d_u - d_v + 3 * common_neighbors
        curvature_map[(u, v)] = float(f_e)
        
    return curvature_map

def compute_sheaf_obstruction_h1(G: nx.Graph) -> float:
    """
    H^1 Sheaf Cohomology Obstruction (Approximation).
    Measures the impossibility of gluing local states into a global colimit.
    We approximate it via the spectral gap of the normalized Laplacian.
    """
    if G.number_of_nodes() < 2:
        return 0.0
    
    L_norm = nx.normalized_laplacian_matrix(G.to_undirected()).toarray()
    eigenvalues = np.linalg.eigvals(L_norm).real
    eigenvalues.sort()
    
    # The algebraic connectivity (Fiedler value, lambda_2) serves as a proxy.
    lambda_2 = eigenvalues[1] if len(eigenvalues) > 1 else 0.0
    obstruction = np.exp(-lambda_2)
    return float(obstruction)

def get_structural_debt_triple(G: nx.Graph) -> Dict[str, float]:
    """
    Calculates the Fable 5 Máx C5-REAL 'Triple of Rigor'.
    """
    R_eff = compute_effective_resistance(G)
    
    curvatures = compute_forman_ricci_curvature(G)
    min_curvature = min(curvatures.values()) if curvatures else 0.0
    avg_curvature = sum(curvatures.values()) / len(curvatures) if curvatures else 0.0
    
    obstruction = compute_sheaf_obstruction_h1(G)
    
    return {
        "effective_resistance": R_eff,
        "min_forman_ricci_curvature": min_curvature,
        "avg_forman_ricci_curvature": avg_curvature,
        "h1_sheaf_obstruction": obstruction
    }
