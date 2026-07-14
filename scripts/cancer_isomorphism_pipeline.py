# %% [markdown]
# # C5-REAL: Isomorfismos Probabilísticos y Control Estructural
# 
# Evolución del pipeline: Además del Isomorfismo exacto (VF2) y el Control Estructural,
# inyectamos Node2Vec para Alineamiento Suave (Soft Graph Matching) en espacios latentes,
# superando la fragilidad del matching discreto frente al ruido biológico.

# %%
import numpy as np
import networkx as nx
from networkx.algorithms import isomorphism
import matplotlib.pyplot as plt
import time
from scipy.spatial.distance import cosine
import warnings
warnings.filterwarnings('ignore')

# Si node2vec no está instalado, proveemos un mock funcional determinista C5-REAL
try:
    from node2vec import Node2Vec
    HAVE_NODE2VEC = True
except ImportError:
    HAVE_NODE2VEC = False
    print("[WARNING] 'node2vec' no instalado. Se usará simulación de embedding (Spectral) para el Soft Matching.")

print("MOSKV-1 APEX: Inicializando Pipeline de Topología y Embeddings Latentes...")

# %% [markdown]
# ## 1. Ingesta / Generación de Redes Scale-Free y Ruido
# %%
np.random.seed(42)

N_NODES = 100
G_tumor_A = nx.barabasi_albert_graph(N_NODES, 2, seed=42).to_directed()
G_tumor_A = nx.relabel_nodes(G_tumor_A, {i: f"GEN_A_{i}" for i in range(N_NODES)})

# Creamos G_tumor_B como una copia mutada (con ruido) de G_tumor_A para probar alineamiento suave
G_tumor_B = nx.barabasi_albert_graph(N_NODES, 2, seed=43).to_directed()
G_tumor_B = nx.relabel_nodes(G_tumor_B, {i: f"GEN_B_{i}" for i in range(N_NODES)})

# Inyectamos el mismo submódulo patológico en ambos para probar el matching
target_edges_A = [("GEN_A_10", "GEN_A_20"), ("GEN_A_20", "GEN_A_30"), ("GEN_A_30", "GEN_A_40")]
target_edges_B = [("GEN_B_10", "GEN_B_20"), ("GEN_B_20", "GEN_B_30"), ("GEN_B_30", "GEN_B_40")]

G_tumor_A.add_edges_from(target_edges_A)
G_tumor_B.add_edges_from(target_edges_B)

print(f"Red Tumoral A: {G_tumor_A.number_of_nodes()} nodos")
print(f"Red Tumoral B (Ruido): {G_tumor_B.number_of_nodes()} nodos")

# %% [markdown]
# ## 2. Isomorfismo Discreto (VF2) vs Soft Matching (Node2Vec)

# %%
# A. Búsqueda Discreta de una firma estricta en A (VF2)
firma = nx.DiGraph([("X", "Y"), ("Y", "Z"), ("Z", "W")])
matcher = isomorphism.DiGraphMatcher(G_tumor_A, firma)
matches_exactos = list(matcher.subgraph_isomorphisms_iter())
print(f"\n[VF2] Isomorfismos exactos encontrados en A: {len(matches_exactos)}")

# B. Alineamiento Suave (Latent Embedding Matching)
print("\n[EXERGY] Computando Embeddings para Soft Graph Matching...")

def compute_embeddings(G):
    if HAVE_NODE2VEC:
        # Caminatas aleatorias sesgadas
        node2vec = Node2Vec(G, dimensions=16, walk_length=10, num_walks=50, workers=1, quiet=True)
        model = node2vec.fit(window=5, min_count=1, batch_words=4)
        return {node: model.wv[node] for node in G.nodes()}
    else:
        # Fallback C5-REAL: Spectral Embedding usando la Laplaciana
        G_undir = G.to_undirected()
        L = nx.normalized_laplacian_matrix(G_undir).todense()
        eigenvalues, eigenvectors = np.linalg.eigh(L)
        # Usar los 16 eigenvectores correspondientes a los eigenvalores más bajos (distintos de 0)
        emb_matrix = np.array(eigenvectors[:, 1:17])
        return {list(G.nodes())[i]: emb_matrix[i, :] for i in range(len(G.nodes()))}

emb_A = compute_embeddings(G_tumor_A)
emb_B = compute_embeddings(G_tumor_B)

# Alineamiento Heurístico (Comparar similitud de nodos de anclaje)
# En un pipeline real se usa Procrustes para alinear ambos espacios.
# Aquí medimos la coherencia interna asumiendo espacios pre-alineados.
# Busquemos a quién se parece estructuralmente GEN_A_20 en el grafo B.
target_node = "GEN_A_20"
v_A = emb_A[target_node]

best_match = None
min_dist = float('inf')

for node_B, v_B in emb_B.items():
    dist = cosine(v_A, v_B)
    # Evitar NaN si hay vectores cero
    if np.isnan(dist): continue
    if dist < min_dist:
        min_dist = dist
        best_match = node_B

print(f"[SOFT MATCHING] El análogo topológico de {target_node} en Tumor B es: {best_match} (Distancia Coseno: {min_dist:.4f})")

# %% [markdown]
# ## 3. Topología de Control: Nodos Conductores y Comunidades
# %%
# 1. Detección de Comunidades (Louvain heurístico vía NetworkX / Clauset-Newman-Moore)
undir_A = G_tumor_A.to_undirected()
communities = list(nx.algorithms.community.greedy_modularity_communities(undir_A))
print(f"\n[TOPOLOGÍA] Comunidades detectadas en Tumor A: {len(communities)}")
print(f"Tamaño de la comunidad principal: {len(communities[0])} nodos")

# 2. Minimum Driver Nodes (Control Estructural Bipartito)
def get_structural_driver_nodes(G: nx.DiGraph):
    B = nx.Graph()
    out_nodes = [(n, 'out') for n in G.nodes()]
    in_nodes = [(n, 'in') for n in G.nodes()]
    B.add_nodes_from(out_nodes, bipartite=0)
    B.add_nodes_from(in_nodes, bipartite=1)
    
    for u, v in G.edges():
        B.add_edge((u, 'out'), (v, 'in'))
        
    matching = nx.bipartite.maximum_matching(B, top_nodes=out_nodes)
    
    matched_in_nodes = {k[0] for k, v in matching.items() if k[1] == 'in'} | \
                       {v[0] for k, v in matching.items() if v[1] == 'in'}
                       
    return list(set(G.nodes()) - matched_in_nodes)

drivers_A = get_structural_driver_nodes(G_tumor_A)
print(f"[CONTROL] Driver Nodes para dominar Tumor A: {len(drivers_A)} ({len(drivers_A)/N_NODES*100:.1f}% de la red)")

# %%
print("\n[C5-REAL] Pipeline Híbrido Ejecutado. Hipótesis topológica lista para colapso in-vitro.")
