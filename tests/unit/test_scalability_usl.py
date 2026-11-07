"""Unit tests for mathematical scalability evaluators (USL, Amdahl, Gustafson, Kingman, C5 elasticity)."""

from __future__ import annotations

import math

import pytest

from babylon60.metrics import (
    amdahl_speedup,
    chinchilla_loss,
    composite_j_elasticity,
    discrete_log_elasticity,
    fit_usl_parameters,
    gustafson_speedup,
    kingman_waiting_time,
    littles_law_concurrency,
    usl_capacity,
    usl_peak_concurrency,
)


def test_usl_reduces_to_amdahl_and_asymptote() -> None:
    sigma = 0.05  # 5% serial fraction -> ceiling = 20x
    for n in (1, 2, 4, 8, 16, 64, 256):
        assert math.isclose(
            usl_capacity(n, sigma=sigma, kappa=0.0),
            amdahl_speedup(n, sigma=sigma),
            rel_tol=1e-12,
        )
    # Asymptotic limit as N -> infinity is 1 / sigma = 20.0
    assert math.isclose(amdahl_speedup(1_000_000, sigma=sigma), 1.0 / sigma, rel_tol=1e-4)
    assert usl_peak_concurrency(sigma=sigma, kappa=0.0) is None


def test_usl_retrograde_peak_and_collapse() -> None:
    sigma = 0.04
    kappa = 0.0015  # N* = sqrt((1 - 0.04) / 0.0015) = sqrt(640) ~ 25.298
    peak_n = usl_peak_concurrency(sigma=sigma, kappa=kappa)
    assert peak_n is not None
    assert math.isclose(peak_n, math.sqrt(640.0), rel_tol=1e-12)

    u_peak = usl_capacity(peak_n, sigma=sigma, kappa=kappa)
    u_before = usl_capacity(peak_n - 3.0, sigma=sigma, kappa=kappa)
    u_after = usl_capacity(peak_n + 3.0, sigma=sigma, kappa=kappa)
    assert u_peak > u_before
    assert u_peak > u_after


def test_gustafson_linear_scaled_speedup() -> None:
    assert math.isclose(gustafson_speedup(1, sigma=0.1), 1.0)
    assert math.isclose(gustafson_speedup(10, sigma=0.1), 10.0 - 0.9)


def test_fit_usl_parameters_recovers_exact_synthetic_curve() -> None:
    true_sigma = 0.05
    true_kappa = 0.002
    base_throughput = 150.0
    samples = [
        (float(n), base_throughput * usl_capacity(float(n), true_sigma, true_kappa)) for n in (1, 2, 4, 8, 16, 32, 64)
    ]
    fit = fit_usl_parameters(samples)
    assert math.isclose(fit.sigma, true_sigma, rel_tol=1e-9, abs_tol=1e-9)
    assert math.isclose(fit.kappa, true_kappa, rel_tol=1e-9, abs_tol=1e-9)
    assert math.isclose(fit.r_squared, 1.0, rel_tol=1e-9, abs_tol=1e-9)
    assert fit.peak_n is not None
    assert math.isclose(fit.peak_n, math.sqrt((1.0 - true_sigma) / true_kappa), rel_tol=1e-9)
    assert fit.amdahl_ceiling is not None
    assert math.isclose(fit.amdahl_ceiling, 20.0, rel_tol=1e-9)


def test_kingman_waiting_time_and_littles_law() -> None:
    # Deterministic zero-jitter service and arrival (ca^2 = cs^2 = 0) yields 0 queue wait
    assert kingman_waiting_time(rho=0.95, ca_sq=0.0, cs_sq=0.0, tau_s=10.0) == 0.0

    # M/M/1 queue (ca^2 = cs^2 = 1) at rho = 0.8 -> E[W_q] = 4 * tau_s
    wq_80 = kingman_waiting_time(rho=0.8, ca_sq=1.0, cs_sq=1.0, tau_s=5.0)
    wq_95 = kingman_waiting_time(rho=0.95, ca_sq=1.0, cs_sq=1.0, tau_s=5.0)
    assert math.isclose(wq_80, 20.0, rel_tol=1e-12)
    assert wq_95 > wq_80
    assert math.isclose(littles_law_concurrency(arrival_rate=10.0, residence_time=2.5), 25.0)


def test_discrete_and_composite_log_elasticity() -> None:
    # Quadratic growth J(N) = N^2 -> log elasticity is exactly 2.0
    assert math.isclose(discrete_log_elasticity(2.0, 4.0, 8.0, 64.0), 2.0, rel_tol=1e-12)

    net = composite_j_elasticity(
        e_cap=0.9,
        e_v=1.1,
        e_f=0.05,
        e_c=0.4,
        e_k=0.3,
        e_r=0.1,
    )
    assert math.isclose(net, 1.25, rel_tol=1e-12)


def test_chinchilla_loss_monotone_in_scale() -> None:
    loss_small = chinchilla_loss(params=1e9, tokens=20e9)
    loss_large = chinchilla_loss(params=10e9, tokens=200e9)
    assert loss_large < loss_small
    assert loss_large > 1.69


@pytest.mark.parametrize(
    ("fn", "kwargs"),
    [
        (usl_capacity, {"n": 0.5, "sigma": 0.1, "kappa": 0.01}),
        (usl_capacity, {"n": 2.0, "sigma": -0.1, "kappa": 0.01}),
        (usl_capacity, {"n": 2.0, "sigma": 0.1, "kappa": -0.01}),
        (kingman_waiting_time, {"rho": 1.0, "ca_sq": 1.0, "cs_sq": 1.0, "tau_s": 1.0}),
        (discrete_log_elasticity, {"n1": 4.0, "j1": 10.0, "n2": 4.0, "j2": 20.0}),
    ],
)
def test_domain_validation_rejects_invalid_inputs(fn: object, kwargs: dict[str, float]) -> None:
    with pytest.raises(ValueError):
        fn(**kwargs)  # type: ignore[operator]
