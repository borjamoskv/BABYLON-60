"""
Unit tests for FISR Subadditivity Theorem Verifier
===================================================
Kernel: MOSKV-1 APEX
State: Executable C5-REAL Test Suite for Baseline v18.1
"""

import pytest
from cortex.subadditivity_verifier import CertificateCategoryP, Morphism, Certificate


def test_subadditivity_sequential():
    cat = CertificateCategoryP(delta_circ=0.5, delta_tensor=1.0)
    alpha = Morphism("alpha", "A", "B")
    beta = Morphism("beta", "B", "C")

    # Add certificates to fibers
    cat.add_certificate(Certificate("c1_1", alpha, 3.0))
    cat.add_certificate(Certificate("c1_2", alpha, 2.0))  # mu(alpha) = 2.0

    cat.add_certificate(Certificate("c2_1", beta, 4.0))   # mu(beta) = 4.0

    ok, lhs, rhs = cat.verify_sequential_subadditivity(alpha, beta)
    assert ok is True
    assert lhs == 6.5  # 2.0 + 4.0 + 0.5
    assert rhs == 6.5


def test_subadditivity_monoidal():
    cat = CertificateCategoryP(delta_circ=0.2, delta_tensor=0.8)
    alpha = Morphism("alpha", "X", "Y")
    beta = Morphism("beta", "W", "Z")

    cat.add_certificate(Certificate("c_alpha", alpha, 5.0))
    cat.add_certificate(Certificate("c_beta", beta, 10.0))

    ok, lhs, rhs = cat.verify_monoidal_subadditivity(alpha, beta)
    assert ok is True
    assert lhs == 15.8  # 5.0 + 10.0 + 0.8
    assert rhs == 15.8


def test_unbounded_cost_subadditivity():
    cat = CertificateCategoryP()
    alpha = Morphism("alpha", "A", "B")
    beta = Morphism("beta", "B", "C")

    # alpha has no certificates -> mu(alpha) = inf
    ok, lhs, rhs = cat.verify_sequential_subadditivity(alpha, beta)
    assert ok is True
    assert lhs == float('inf')
    assert rhs == float('inf')
