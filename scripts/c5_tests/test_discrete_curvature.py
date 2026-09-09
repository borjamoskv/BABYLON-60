#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import networkx as nx
from babylon60.core.discrete_curvature import get_structural_debt_triple

def test_topologies():
    print("--- PRUEBA C5-REAL: TRIPLE DEL RIGOR ---")
    
    # 1. Grafo Estrella (alta centralización, cuello de botella)
    G_star = nx.star_graph(5, create_using=nx.DiGraph)
    triple_star = get_structural_debt_triple(G_star)
    print("\n[Grafo Estrella (Bottleneck)]")
    print(f"Resistencia Efectiva: {triple_star['effective_resistance']:.4f}")
    print(f"Curvatura Forman (Mínima): {triple_star['min_forman_ricci_curvature']:.4f}")
    print(f"Obstrucción H1: {triple_star['h1_sheaf_obstruction']:.4f}")

    # 2. Grafo Línea (Flujo secuencial)
    G_line = nx.path_graph(5, create_using=nx.DiGraph)
    triple_line = get_structural_debt_triple(G_line)
    print("\n[Grafo Línea (Secuencial)]")
    print(f"Resistencia Efectiva: {triple_line['effective_resistance']:.4f}")
    print(f"Curvatura Forman (Mínima): {triple_line['min_forman_ricci_curvature']:.4f}")
    print(f"Obstrucción H1: {triple_line['h1_sheaf_obstruction']:.4f}")

    # 3. Grafo Completo (Redundancia absoluta, baja deuda estructural)
    G_complete = nx.complete_graph(5, create_using=nx.DiGraph)
    triple_complete = get_structural_debt_triple(G_complete)
    print("\n[Grafo Completo (Alta Redundancia)]")
    print(f"Resistencia Efectiva: {triple_complete['effective_resistance']:.4f}")
    print(f"Curvatura Forman (Mínima): {triple_complete['min_forman_ricci_curvature']:.4f}")
    print(f"Obstrucción H1: {triple_complete['h1_sheaf_obstruction']:.4f}")

if __name__ == "__main__":
    test_topologies()
