# MOSKV-1 APEX: TOPOLOGÍA Y ALINEAMIENTO DE REDES EN ONCOLOGÍA
# PATH: docs/isomorfismos_cancer.md

> **"El isomorfismo exacto (VF2) es matemáticamente prístino pero biológicamente frágil. La heterogeneidad intratumoral exige Isomorfismos Probabilísticos y Alineamiento Suave (Soft Graph Matching) mediante Embeddings Latentes."**

---

## 1. LIMITACIONES DEL ISOMORFISMO EXACTO EN BIOLOGÍA
El ruido biológico (dropout en scRNA-seq, mutaciones *passenger*, compensación metabólica) hace que dos tumores funcionalmente idénticos carezcan de un isomorfismo de grafos estricto $G_1 \cong G_2$. 
Aplicar VF2 asume grafos deterministas. Para transducir la realidad oncológica, debemos transicionar del matching discreto al **matching en el espacio latente**.

## 2. ALINEAMIENTO ESTRUCTURAL SUAVE (SOFT MATCHING)
En lugar de buscar un mapeo biyectivo de aristas, proyectamos la topología en un colector de baja dimensión (manifold):

### A. Random Walk Embeddings (Node2Vec / DeepWalk)
- **Mecanismo:** Se ejecutan caminatas aleatorias (Random Walks) sesgadas (parámetros $p, q$) sobre la red de coexpresión o PPI.
- **Transducción:** Se aplica Word2Vec (Skip-gram) a las caminatas. Los nodos (genes) con contextos topológicos similares terminan cerca en el espacio euclidiano $\mathbb{R}^d$.
- **Alineamiento:** Para alinear el Tumor A con el Tumor B, se alinean sus espacios latentes (p. ej., mediante Procrustes Analysis o Canonical Correlation Analysis, CCA) y se emparejan genes calculando la Similitud Coseno.

### B. Graph Neural Networks (GNNs)
- Redes convolucionales en grafos (GCN, GraphSAGE) pueden aprender representaciones de nodos que combinan la topología local con los features moleculares (ej. niveles de expresión diferencial).
- Permiten predecir la respuesta a perturbaciones (fármacos) basándose en cómo se altera la representación latente.

## 3. MODULARIDAD Y TEOREMA DE CONTROL
- **Comunidades (Leiden / Louvain):** Segmentan el grafo en submódulos densos (procesos biológicos aislables).
- **Teoría de Control Estructural:** En redes dirigidas, se calcula el conjunto de **Driver Nodes** usando Maximum Bipartite Matching. 
- **Fricción C5-REAL:** La vulnerabilidad (DepMap) de un Driver Node debe ser cruzada empíricamente; la centralidad topológica no garantiza *druggability* si la proteína carece de bolsillos alostéricos.

## 4. PIPELINE CINÉTICO DE ALINEAMIENTO
1. **Ingesta:** `scanpy` -> Matriz de adyacencia (WGCNA).
2. **Incrustación (Embedding):** Ejecutar Node2Vec sobre $G_A$ y $G_B$.
3. **Mapeo:** Alinear los espacios $\mathcal{H}_A$ y $\mathcal{H}_B$ (Orthogonal Procrustes).
4. **Matching:** Matriz de Similitud Coseno $S_{ij} = \cos(e^{(A)}_i, e^{(B)}_j)$.
5. **Extracción:** Identificar los módulos biológicos funcionalmente isomorfos a pesar del ruido mutacional.
6. **Ejecución:** Computar centralidades topológicas dentro del submódulo alineado para proponer combinaciones terapéuticas (LINCS).

---
*Fin del manifiesto de alineamiento.*
