#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ REPRESENTATION_GEOMETRY | C5-REAL (arXiv:2609.08692v1 / Belouche et al.)
# ============================================================================
# Multi-Scale Latent Geometry: RankMe, IsoScore, ZCA-Whitening & m-KNN

from typing import cast
import numpy as np


def compute_rankme(X: np.ndarray, eps: float = 1e-12) -> float:
    """
    Computes RankMe: the effective dimensionality of representations
    defined as the exponential of the Shannon entropy of normalized singular values.

    Reference: Garrido et al. (2022) / Belouche et al. (2026, arXiv:2609.08692v1)
    """
    if X.ndim != 2 or X.shape[0] == 0 or X.shape[1] == 0:
        return 0.0

    # Center matrix before SVD
    X_c = X - np.mean(X, axis=0, keepdims=True)
    singular_values = np.linalg.svd(X_c, compute_uv=False)

    total = np.sum(singular_values)
    if total <= eps:
        return 0.0

    p = singular_values / total
    # Filter out zero probabilities
    p = p[p > eps]
    entropy = -np.sum(p * np.log(p))
    return float(np.exp(entropy))


def compute_pc1_explained_variance(X: np.ndarray) -> float:
    """
    Calculates the proportion of variance explained by the first principal component (PC1).
    High values indicate representation collapse into a narrow cone (anisotropy).
    """
    if X.ndim != 2 or X.shape[0] < 2 or X.shape[1] == 0:
        return 0.0

    X_c = X - np.mean(X, axis=0, keepdims=True)
    cov = np.cov(X_c, rowvar=False)

    if cov.ndim == 0:
        return 1.0

    eigenvalues = np.linalg.eigvalsh(cov)
    eigenvalues = np.maximum(eigenvalues, 0.0)
    total_var = np.sum(eigenvalues)

    if total_var <= 1e-12:
        return 0.0

    return float(np.max(eigenvalues) / total_var)


def compute_isoscore(X: np.ndarray) -> float:
    """
    Quantifies the degree of isotropy of latent space representations.
    Measures the normalized distance between the normalized eigenvalue distribution
    and the uniform distribution.

    Score 1.0 = Perfectly isotropic (equal variance in all directions).
    Score 0.0 = Degenerated / anisotropic (collapsed into a 1D subspace).
    """
    if X.ndim != 2 or X.shape[0] < 2 or X.shape[1] < 2:
        return 0.0

    X_c = X - np.mean(X, axis=0, keepdims=True)
    cov = np.cov(X_c, rowvar=False)

    if cov.ndim == 0:
        return 0.0

    d = X.shape[1]
    eigenvalues = np.linalg.eigvalsh(cov)
    eigenvalues = np.maximum(eigenvalues, 0.0)
    total_var = np.sum(eigenvalues)

    if total_var <= 1e-12:
        return 0.0

    p = eigenvalues / total_var
    uniform = 1.0 / d
    # Normalized Euclidean distance to uniform vector
    dist_sq = np.sum((p - uniform) ** 2)
    max_dist_sq = (1.0 - uniform) ** 2 + (d - 1) * (uniform**2)

    if max_dist_sq <= 1e-12:
        return 1.0

    score = 1.0 - np.sqrt(dist_sq / max_dist_sq)
    return float(np.clip(score, 0.0, 1.0))


def compute_zca_whitening(X: np.ndarray, eps: float = 1e-5) -> np.ndarray:
    """
    Applies Zero-Phase Component Analysis (ZCA) whitening.
    Transforms representation space such that the global covariance becomes the identity matrix,
    removing anisotropic artifacts while minimizing Euclidean distance to original features.

    Formula: X_white = (X - mu) * Sigma^(-1/2)
    Reference: Section 5.1 of Belouche et al. (2026, arXiv:2609.08692v1)
    """
    if X.ndim != 2 or X.shape[0] < 2:
        return X.copy()

    X_c = X - np.mean(X, axis=0, keepdims=True)
    cov = np.cov(X_c, rowvar=False)

    # Eigendecomposition of covariance matrix
    eigvals, eigvecs = np.linalg.eigh(cov)
    # Inverse square root with numerical damping
    inv_sqrt_eigvals = 1.0 / np.sqrt(np.maximum(eigvals, eps))

    # ZCA transform matrix: W = V * diag(1 / sqrt(lambda)) * V^T
    zca_matrix = eigvecs @ np.diag(inv_sqrt_eigvals) @ eigvecs.T
    return cast(np.ndarray, X_c @ zca_matrix)


def compute_m_knn_overlap(X: np.ndarray, Y: np.ndarray, k: int = 10) -> float:
    """
    Computes Mutual k-Nearest Neighbors (m-KNN) overlap between two representation spaces.
    Measures structural equivalence of local token neighborhoods, invariant to global linear
    transformations or anisotropic scaling.

    Reference: Section 5.2 of Belouche et al. (2026, arXiv:2609.08692v1)
    """
    if X.shape[0] != Y.shape[0] or X.shape[0] <= k or k <= 0:
        return 0.0

    n = X.shape[0]

    # Normalize vectors for cosine similarity computation
    norm_X = np.linalg.norm(X, axis=1, keepdims=True)
    norm_Y = np.linalg.norm(Y, axis=1, keepdims=True)
    X_n = X / np.maximum(norm_X, 1e-12)
    Y_n = Y / np.maximum(norm_Y, 1e-12)

    # Compute cosine similarity matrices
    sim_X = X_n @ X_n.T
    sim_Y = Y_n @ Y_n.T

    # Set self-similarity to -infinity to exclude self from nearest neighbors
    np.fill_diagonal(sim_X, -np.inf)
    np.fill_diagonal(sim_Y, -np.inf)

    # Top-k indices for each token
    top_k_X = np.argpartition(-sim_X, k, axis=1)[:, :k]
    top_k_Y = np.argpartition(-sim_Y, k, axis=1)[:, :k]

    total_overlap = 0
    for i in range(n):
        set_x = set(top_k_X[i])
        set_y = set(top_k_Y[i])
        total_overlap += len(set_x.intersection(set_y))

    return float(total_overlap / (n * k))


def compute_whitened_cka(X: np.ndarray, Y: np.ndarray) -> float:
    """
    Computes Linear Centered Kernel Alignment (CKA) between globally ZCA-whitened representations.
    Permits unbiased structural alignment comparison between anisotropic and isotropic models.
    """
    X_w = compute_zca_whitening(X)
    Y_w = compute_zca_whitening(Y)

    # Compute Gram matrices
    K = X_w @ X_w.T
    L = Y_w @ Y_w.T

    # Center Gram matrices
    n = K.shape[0]
    H = np.eye(n) - np.ones((n, n)) / n
    K_c = H @ K @ H
    L_c = H @ L @ H

    # Hilbert-Schmidt Independence Criterion (HSIC)
    hsic_kl = np.sum(K_c * L_c)
    hsic_kk = np.sum(K_c * K_c)
    hsic_ll = np.sum(L_c * L_c)

    denominator = np.sqrt(np.maximum(hsic_kk * hsic_ll, 1e-12))
    return float(np.clip(hsic_kl / denominator, 0.0, 1.0))
