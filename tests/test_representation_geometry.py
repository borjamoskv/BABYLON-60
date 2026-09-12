#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ TEST_REPRESENTATION_GEOMETRY | C5-REAL (arXiv:2609.08692v1 Verification)
# ============================================================================

import numpy as np
import pytest
from babylon60.core.representation_geometry import (
    compute_rankme,
    compute_pc1_explained_variance,
    compute_isoscore,
    compute_zca_whitening,
    compute_m_knn_overlap,
    compute_whitened_cka,
)


def test_isotropic_vs_anisotropic_geometry() -> None:
    """Falsates that isotropic representations exhibit higher RankMe and IsoScore."""
    np.random.seed(42)
    N, d = 500, 32

    # 1. Isotropic space (similar to SSM/Mamba residual stream)
    X_iso = np.random.randn(N, d)

    # 2. Anisotropic space (similar to Transformer residual stream dominated by PC1)
    X_aniso = np.random.randn(N, d)
    X_aniso[:, 0] *= 50.0  # Massive variance concentration along PC1

    rankme_iso = compute_rankme(X_iso)
    rankme_aniso = compute_rankme(X_aniso)

    isoscore_iso = compute_isoscore(X_iso)
    isoscore_aniso = compute_isoscore(X_aniso)

    pc1_iso = compute_pc1_explained_variance(X_iso)
    pc1_aniso = compute_pc1_explained_variance(X_aniso)

    # Verification: Isotropic must have higher RankMe and IsoScore, lower PC1 variance
    assert rankme_iso > rankme_aniso
    assert isoscore_iso > isoscore_aniso
    assert pc1_aniso > 0.80  # Over 80% variance captured by PC1
    assert pc1_iso < 0.20


def test_zca_whitening_eradicates_anisotropy() -> None:
    """Verifies that ZCA whitening restores covariance identity on anisotropic features."""
    np.random.seed(42)
    N, d = 400, 16

    X_skewed = np.random.randn(N, d)
    X_skewed[:, 0] *= 30.0
    X_skewed[:, 1] *= 10.0

    X_white = compute_zca_whitening(X_skewed)

    # After ZCA whitening, the covariance matrix must be approximately identity
    cov_white = np.cov(X_white, rowvar=False)
    np.testing.assert_allclose(cov_white, np.eye(d), atol=0.15)

    # IsoScore of whitened data must be close to 1.0
    assert compute_isoscore(X_white) > 0.90


def test_m_knn_structural_neighborhood_alignment() -> None:
    """Tests that mutual-kNN captures local neighborhood topologies invariant to orthogonal rotations."""
    np.random.seed(42)
    N, d = 200, 16
    k = 5

    X = np.random.randn(N, d)

    # Self-overlap must be 1.0
    self_overlap = compute_m_knn_overlap(X, X, k=k)
    assert pytest.approx(self_overlap, abs=1e-5) == 1.0

    # Orthogonal rotation (random unitary matrix)
    Q, _ = np.linalg.qr(np.random.randn(d, d))
    X_rotated = X @ Q

    # An orthogonal rotation strictly preserves Euclidean and cosine distances
    rotated_overlap = compute_m_knn_overlap(X, X_rotated, k=k)
    assert pytest.approx(rotated_overlap, abs=1e-5) == 1.0

    # Random unrelated space should have near-zero overlap
    Y_unrelated = np.random.randn(N, d)
    unrelated_overlap = compute_m_knn_overlap(X, Y_unrelated, k=k)
    assert unrelated_overlap < 0.15


def test_whitened_cka_metric() -> None:
    """Verifies that Whitened CKA yields 1.0 for identical representations."""
    np.random.seed(42)
    N, d = 100, 8

    X = np.random.randn(N, d)
    cka_identical = compute_whitened_cka(X, X)
    assert pytest.approx(cka_identical, abs=1e-3) == 1.0
