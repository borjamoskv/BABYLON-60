# MOSKV-1 APEX: NETWORK TOPOLOGY AND ALIGNMENT IN ONCOLOGY
# PATH: docs/isomorfismos_cancer.md

> **"Exact isomorphism (VF2) is mathematically pristine but biologically fragile. Intratumoral heterogeneity demands Probabilistic Isomorphisms and Soft Graph Matching via Latent Embeddings."**

---

## 1. LIMITATIONS OF EXACT ISOMORPHISM IN BIOLOGY
Biological noise (dropout in scRNA-seq, passenger mutations, metabolic compensation) means that two functionally identical tumors lack a strict graph isomorphism $G_1 \cong G_2$. 
Applying VF2 assumes deterministic graphs. To transduce oncological reality, we must transition from discrete matching to **matching in latent space**.

## 2. SOFT STRUCTURAL ALIGNMENT (SOFT MATCHING)
Instead of searching for a bijective edge mapping, we project the topology onto a low-dimensional manifold:

### A. Random Walk Embeddings (Node2Vec / DeepWalk)
- **Mechanism:** Biased random walks (parameters $p, q$) are run over the co-expression or PPI network.
- **Transduction:** Word2Vec (Skip-gram) is applied to the walks. Nodes (genes) with similar topological contexts end up close in Euclidean space $\mathbb{R}^d$.
- **Alignment:** To align Tumor A with Tumor B, their latent spaces are aligned (e.g. via Procrustes Analysis or Canonical Correlation Analysis, CCA) and genes are matched by computing Cosine Similarity.

### B. Graph Neural Networks (GNNs)
- Graph convolutional networks (GCN, GraphSAGE) can learn node representations that combine local topology with molecular features (e.g. differential expression levels).
- They allow prediction of response to perturbations (drugs) based on how the latent representation is altered.

## 3. MODULARITY AND CONTROL THEOREM
- **Communities (Leiden / Louvain):** Segment the graph into dense sub-modules (isolable biological processes).
- **Structural Control Theory:** In directed networks, the set of **Driver Nodes** is computed using Maximum Bipartite Matching. 
- **C5-REAL Friction:** The vulnerability (DepMap) of a Driver Node must be empirically cross-referenced; topological centrality does not guarantee *druggability* if the protein lacks allosteric pockets.

## 4. KINETIC ALIGNMENT PIPELINE
1. **Ingestion:** `scanpy` -> Adjacency matrix (WGCNA).
2. **Embedding:** Run Node2Vec over $G_A$ and $G_B$.
3. **Mapping:** Align spaces $\mathcal{H}_A$ and $\mathcal{H}_B$ (Orthogonal Procrustes).
4. **Matching:** Cosine Similarity Matrix $S_{ij} = \cos(e^{(A)}_i, e^{(B)}_j)$.
5. **Extraction:** Identify biologically functionally isomorphic modules despite mutational noise.
6. **Execution:** Compute topological centralities within the aligned sub-module to propose therapeutic combinations (LINCS).

---
*End of alignment manifesto.*
