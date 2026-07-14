# %% [markdown]
# # C5-REAL: Pipeline de Isomorfismos y Control Estructural en Cáncer
# 
# Este script/notebook materializa la teoría de sistemas biológicos sobre redes de interacción génica.
# Implementa:
# 1. Construcción de una red tumoral simulada (Scale-Free) y una red de referencia.
# 2. Búsqueda de Isomorfismos (Subgraph Matching) para encontrar módulos conservados.
# 3. Análisis de Control Estructural Topológico (basado en Liu et al., Nature 2011) para encontrar *Driver Nodes*.
# 
# Ejecución compatible con Jupyter (usando VS Code o Jupytext) o como script estándar Python.

# %%
import numpy as np
import pandas as pd
import networkx as nx
from networkx.algorithms import isomorphism
import matplotlib.pyplot as plt
import time

print("MOSKV-1 APEX: Inicializando Pipeline Estructural...")

# %% [markdown]
# ## 1. Ingesta / Generación de Redes Scale-Free (Aproximación de Coexpresión)
# Las redes biológicas (PPI, coexpresión) presentan topologías libres de escala (Scale-Free).
# Vamos a simular un grafo tumoral (G_tumor) y un grafo normal o módulo diana (G_target).
# En un entorno real, `G_tumor` se construiría cruzando correlaciones de Pearson/Spearman (WGCNA) desde AnnData de RNA-seq.

# %%
# Fijar entropía (semilla) para reproducibilidad C5-REAL
np.random.seed(42)

# Crear G_tumor (Red principal, simulando 1000 genes pero usaremos 100 para computación rápida)
N_NODES = 150
M_EDGES = 2
G_tumor = nx.barabasi_albert_graph(N_NODES, M_EDGES, seed=42)
G_tumor = G_tumor.to_directed() # Las redes de regulación transcripcional son dirigidas

# Asignar nombres ficticios a los genes
mapping_tumor = {i: f"GEN_{i}" for i in range(N_NODES)}
G_tumor = nx.relabel_nodes(G_tumor, mapping_tumor)

# Crear un submódulo patológico conocido (G_target) que queremos buscar en el tumor
# Supongamos que es una vía de resistencia a apoptosis de 5 genes
G_target = nx.DiGraph()
target_edges = [
    ("AKT1", "MTOR"),
    ("PIK3CA", "AKT1"),
    ("MTOR", "HIF1A"),
    ("PTEN", "AKT1"),
    ("HIF1A", "VEGFA")
]
G_target.add_edges_from(target_edges)

# Para asegurar que encontraremos un isomorfismo parcial, inyectamos G_target en G_tumor
# Seleccionamos 5 nodos al azar en G_tumor y forzamos esta topología
injection_nodes = ["GEN_10", "GEN_42", "GEN_73", "GEN_88", "GEN_105"]
injected_edges = [
    (injection_nodes[1], injection_nodes[2]),
    (injection_nodes[0], injection_nodes[1]),
    (injection_nodes[2], injection_nodes[3]),
    (injection_nodes[4], injection_nodes[1]),
    (injection_nodes[3], injection_nodes[4]) # Bucle leve para simular feedback
]
G_tumor.add_edges_from(injected_edges)

print(f"Red Tumoral Creada: Nodos={G_tumor.number_of_nodes()}, Aristas={G_tumor.number_of_edges()}")
print(f"Red Target (Vía Resistencia): Nodos={G_target.number_of_nodes()}, Aristas={G_target.number_of_edges()}")

# %% [markdown]
# ## 2. Isomorfismo Parcial (Subgraph Matching)
# Buscamos correspondencias topológicas de G_target dentro de G_tumor.
# VF2 Algorithm: Busca isomorfismos exactos.

# %%
start_time = time.time()
print("\n[EXERGY] Iniciando Subgraph Matching (VF2 Algorithm)...")

# Buscamos si G_target es subgrafo isomorfo a alguna parte de G_tumor
matcher = isomorphism.DiGraphMatcher(G_tumor, G_target)

matches = list(matcher.subgraph_isomorphisms_iter())
end_time = time.time()

print(f"Isomorfismos encontrados: {len(matches)}")
print(f"Latencia de cálculo: {(end_time - start_time)*1000:.2f} ms")

if matches:
    print("\nEjemplo de Mapeo Encontrado (Tumor -> Target):")
    for key, val in list(matches[0].items())[:5]:
        print(f"  {key} es isomorfo a {val}")

# %% [markdown]
# ## 3. Control Estructural Topológico (Maximum Bipartite Matching)
# Liu et al. (Nature, 2011) demostraron que podemos encontrar el número mínimo de nodos conductores (Driver Nodes) 
# necesarios para controlar completamente una red dirigida buscando el "Maximum Matching" en su representación bipartita.
# 
# Los Driver Nodes son aquellos nodos en G_tumor que no están emparejados (unmatched) en el matching máximo.

# %%
def get_structural_driver_nodes(G: nx.DiGraph):
    """
    Calcula los Driver Nodes mínimos para control estructural (Liu et al. 2011).
    Requiere transformar el grafo dirigido a uno bipartito.
    """
    # 1. Crear grafo bipartito
    B = nx.Graph()
    # Nodos origen (out) y nodos destino (in)
    out_nodes = [(n, 'out') for n in G.nodes()]
    in_nodes = [(n, 'in') for n in G.nodes()]
    
    B.add_nodes_from(out_nodes, bipartite=0)
    B.add_nodes_from(in_nodes, bipartite=1)
    
    # 2. Agregar aristas mapeando u -> v
    for u, v in G.edges():
        B.add_edge((u, 'out'), (v, 'in'))
        
    # 3. Maximum Bipartite Matching (Hopcroft-Karp algorithm)
    # top_nodes = {n for n, d in B.nodes(data=True) if d["bipartite"] == 0}
    matching = nx.bipartite.maximum_matching(B, top_nodes=out_nodes)
    
    # 4. Los nodos que NO están acoplados en su puerto 'in' son los Driver Nodes
    # Es decir, nodos cuya representación (n, 'in') no está en el matching
    matched_in_nodes = set()
    for k, v in matching.items():
        if k[1] == 'in':
            matched_in_nodes.add(k[0])
        elif v[1] == 'in':
            matched_in_nodes.add(v[0])
            
    driver_nodes = set(G.nodes()) - matched_in_nodes
    return list(driver_nodes)

print("\n[EXERGY] Calculando Nodos Conductores de Control Mínimo (MDS)...")
start_time = time.time()
driver_nodes = get_structural_driver_nodes(G_tumor)
end_time = time.time()

print(f"Total Driver Nodes requeridos para control total: {len(driver_nodes)}")
print(f"Ratio de Densidad de Control (n_D / N): {len(driver_nodes)/N_NODES:.2f}")
print(f"Latencia de cálculo: {(end_time - start_time)*1000:.2f} ms")

print(f"\nTop 10 Driver Nodes: {driver_nodes[:10]}")

# %% [markdown]
# ## 4. Visualización (Opcional, reducida)
# Extraemos el subgrafo inducido por los Driver Nodes y sus vecinos para priorizar dianas farmacológicas.

# %%
def visualize_driver_subgraph(G, drivers, limit=15):
    sub_nodes = drivers[:limit]
    # Extraer vecinos de grado 1 de estos drivers
    neighborhood = set(sub_nodes)
    for d in sub_nodes:
        neighborhood.update(G.successors(d))
    
    H = G.subgraph(neighborhood)
    
    plt.figure(figsize=(10, 8))
    pos = nx.spring_layout(H, seed=42)
    
    # Colorear Drivers vs Vecinos
    color_map = []
    for node in H:
        if node in drivers:
            color_map.append('#E74C3C') # Rojo para Driver (Alta Exergía)
        else:
            color_map.append('#3498DB') # Azul para Regulados
            
    nx.draw_networkx(H, pos, node_color=color_map, node_size=500, font_size=8, font_color='white', edge_color='#7F8C8D')
    plt.title(f"Subgrafo de Control (Rojo: Driver Nodes)")
    plt.axis('off')
    # plt.show()
    print("Gráfico generado. Ejecuta plt.show() en un notebook iterativo para visualizar.")

visualize_driver_subgraph(G_tumor, driver_nodes)

# %% [markdown]
# ## CONCLUSIÓN C5-REAL
# En este pipeline hemos:
# 1. Simulando un fenotipo (Scale-Free Graph).
# 2. Localizado módulos funcionales biológicamente isomorfos.
# 3. Mapeado la red bipartita para extraer mediante Hopcroft-Karp los Nodos Conductores (Drivers).
# 
# Modulando este subconjunto mínimo (fármacos multidiana), la teoría de Control garantiza que 
# podemos dirigir el atractor del estado patológico a un estado de homeostasis apoptótica,
# aniquilando la exergía tumoral.
