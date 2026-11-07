"""Mathematical scalability evaluators for concurrency, queueing, and structural elasticity.

Implements the canonical equations referenced in
``docs/06_theory/c5_thermodynamic_invariants_compendium.md`` (Section 6):

1. Gunther's Universal Scalability Law (USL):
   ``U(N) = N / (1 + sigma * (N - 1) + kappa * N * (N - 1))``
2. Amdahl's Law (``kappa = 0``) and Gustafson-Barsis scaled speedup.
3. Kingman's VUT queueing waiting-time approximation and Little's Law.
4. Discrete and differential logarithmic scale elasticities for ``J(N)``.
5. Chinchilla neural compute-optimal loss scaling law.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class USLFitResult:
    """Least-squares parameter fit for Gunther's Universal Scalability Law."""

    sigma: float
    kappa: float
    r_squared: float
    peak_n: float | None
    amdahl_ceiling: float | None


def _validate_finite(name: str, value: float) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{name} must be a finite real number, got {value!r}")


def usl_capacity(n: float, sigma: float, kappa: float) -> float:
    """Evaluate Gunther's Universal Scalability Law capacity ratio U(N).

    Formula:
        U(N) = N / (1 + sigma * (N - 1) + kappa * N * (N - 1))

    Args:
        n: Concurrency level or node/agent count (must be >= 1).
        sigma: Contention / serial fraction coefficient in [0, 1].
        kappa: Coherency / pairwise crosstalk coefficient (>= 0).

    Returns:
        Normalized relative capacity U(N) >= 0.
    """
    _validate_finite("n", n)
    _validate_finite("sigma", sigma)
    _validate_finite("kappa", kappa)
    if n < 1.0:
        raise ValueError(f"n must be >= 1.0, got {n}")
    if not (0.0 <= sigma <= 1.0):
        raise ValueError(f"sigma must be in [0.0, 1.0], got {sigma}")
    if kappa < 0.0:
        raise ValueError(f"kappa must be >= 0.0, got {kappa}")

    denom = 1.0 + sigma * (n - 1.0) + kappa * n * (n - 1.0)
    if denom <= 0.0:
        raise ValueError(f"Non-positive USL denominator: {denom}")
    return n / denom


def amdahl_speedup(n: float, sigma: float) -> float:
    """Evaluate Amdahl's Law speedup S(N) = N / (1 + sigma * (N - 1))."""
    return usl_capacity(n=n, sigma=sigma, kappa=0.0)


def gustafson_speedup(n: float, sigma: float) -> float:
    """Evaluate Gustafson-Barsis scaled speedup S_G(N) = N - sigma * (N - 1)."""
    _validate_finite("n", n)
    _validate_finite("sigma", sigma)
    if n < 1.0:
        raise ValueError(f"n must be >= 1.0, got {n}")
    if not (0.0 <= sigma <= 1.0):
        raise ValueError(f"sigma must be in [0.0, 1.0], got {sigma}")
    return n - sigma * (n - 1.0)


def usl_peak_concurrency(sigma: float, kappa: float) -> float | None:
    """Return the critical concurrency N* = sqrt((1 - sigma) / kappa) where U(N) peaks.

    Returns ``None`` when ``kappa == 0`` (monotonic Amdahl regime without retrograde collapse).
    """
    _validate_finite("sigma", sigma)
    _validate_finite("kappa", kappa)
    if not (0.0 <= sigma <= 1.0):
        raise ValueError(f"sigma must be in [0.0, 1.0], got {sigma}")
    if kappa < 0.0:
        raise ValueError(f"kappa must be >= 0.0, got {kappa}")
    if kappa == 0.0:
        return None
    return math.sqrt((1.0 - sigma) / kappa)


def fit_usl_parameters(samples: Sequence[tuple[float, float]]) -> USLFitResult:
    """Estimate (sigma, kappa) from empirical (N, throughput) pairs via linearized least squares.

    Uses Gunther's algebraic transformation:
        y_i = (N_i / U(N_i)) - 1 = sigma * (N_i - 1) + kappa * N_i * (N_i - 1)

    If a sample with N=1 is present, all throughputs are normalized by X(1);
    otherwise samples are treated as already normalized U(N).
    """
    if len(samples) < 2:
        raise ValueError("At least 2 (N, throughput) samples are required to fit USL")

    baseline = 1.0
    for n_val, x_val in samples:
        _validate_finite("n", n_val)
        _validate_finite("throughput", x_val)
        if n_val < 1.0:
            raise ValueError(f"Sample concurrency N must be >= 1.0, got {n_val}")
        if x_val <= 0.0:
            raise ValueError(f"Sample throughput must be > 0.0, got {x_val}")
        if math.isclose(n_val, 1.0, rel_tol=1e-9, abs_tol=1e-9):
            baseline = x_val

    u_vec: list[float] = []
    v_vec: list[float] = []
    y_vec: list[float] = []

    for n_val, x_val in samples:
        if math.isclose(n_val, 1.0, rel_tol=1e-9, abs_tol=1e-9):
            continue
        norm_u = x_val / baseline
        u_i = n_val - 1.0
        v_i = n_val * (n_val - 1.0)
        y_i = (n_val / norm_u) - 1.0
        u_vec.append(u_i)
        v_vec.append(v_i)
        y_vec.append(y_i)

    if len(u_vec) < 2:
        raise ValueError("At least 2 distinct samples with N > 1 are required to fit (sigma, kappa)")

    suu = sum(u * u for u in u_vec)
    suv = sum(u * v for u, v in zip(u_vec, v_vec, strict=True))
    svv = sum(v * v for v in v_vec)
    suy = sum(u * y for u, y in zip(u_vec, y_vec, strict=True))
    svy = sum(v * y for v, y in zip(v_vec, y_vec, strict=True))

    det = suu * svv - suv * suv
    if abs(det) <= 1e-15:
        raise ValueError("Collinear concurrency levels; provide distinct N values")

    raw_sigma = (suy * svv - svy * suv) / det
    raw_kappa = (suu * svy - suv * suy) / det

    sigma = min(1.0, max(0.0, raw_sigma))
    kappa = max(0.0, raw_kappa)

    # If clamping altered one parameter, re-optimize the unconstrained partner cleanly
    if raw_sigma < 0.0 and svv > 0.0:
        sigma = 0.0
        kappa = max(0.0, svy / svv)
    elif raw_kappa < 0.0 and suu > 0.0:
        kappa = 0.0
        sigma = min(1.0, max(0.0, suy / suu))

    y_mean = sum(y_vec) / len(y_vec)
    ss_tot = sum((y - y_mean) ** 2 for y in y_vec)
    ss_res = sum((y - (sigma * u + kappa * v)) ** 2 for u, v, y in zip(u_vec, v_vec, y_vec, strict=True))
    r_squared = 1.0 if ss_tot <= 1e-15 else max(0.0, 1.0 - (ss_res / ss_tot))

    return USLFitResult(
        sigma=sigma,
        kappa=kappa,
        r_squared=r_squared,
        peak_n=usl_peak_concurrency(sigma, kappa),
        amdahl_ceiling=(1.0 / sigma) if sigma > 0.0 else None,
    )


def kingman_waiting_time(rho: float, ca_sq: float, cs_sq: float, tau_s: float) -> float:
    """Compute expected queue waiting time E[W_q] via Kingman's VUT equation for G/G/1.

    Formula:
        E[W_q] = (rho / (1 - rho)) * ((ca_sq + cs_sq) / 2) * tau_s
    """
    _validate_finite("rho", rho)
    _validate_finite("ca_sq", ca_sq)
    _validate_finite("cs_sq", cs_sq)
    _validate_finite("tau_s", tau_s)
    if not (0.0 <= rho < 1.0):
        raise ValueError(f"Utilization rho must be in [0.0, 1.0), got {rho}")
    if ca_sq < 0.0 or cs_sq < 0.0:
        raise ValueError("Squared coefficients of variation ca_sq and cs_sq must be >= 0.0")
    if tau_s <= 0.0:
        raise ValueError(f"Mean service time tau_s must be > 0.0, got {tau_s}")

    return (rho / (1.0 - rho)) * ((ca_sq + cs_sq) / 2.0) * tau_s


def littles_law_concurrency(arrival_rate: float, residence_time: float) -> float:
    """Compute mean system concurrency L = lambda * W via Little's Law."""
    _validate_finite("arrival_rate", arrival_rate)
    _validate_finite("residence_time", residence_time)
    if arrival_rate < 0.0 or residence_time < 0.0:
        raise ValueError("arrival_rate and residence_time must be >= 0.0")
    return arrival_rate * residence_time


def discrete_log_elasticity(n1: float, j1: float, n2: float, j2: float) -> float:
    """Compute discrete logarithmic scale elasticity d(ln J)/d(ln N) between two positive scales."""
    for name, val in (("n1", n1), ("j1", j1), ("n2", n2), ("j2", j2)):
        _validate_finite(name, val)
        if val <= 0.0:
            raise ValueError(f"{name} must be > 0.0, got {val}")
    if math.isclose(n1, n2, rel_tol=1e-12, abs_tol=1e-12):
        raise ValueError("n1 and n2 must be distinct positive scales")
    return math.log(j2 / j1) / math.log(n2 / n1)


def composite_j_elasticity(
    e_cap: float,
    e_v: float,
    e_f: float,
    e_c: float,
    e_k: float,
    e_r: float,
) -> float:
    """Compute net scale elasticity of J(N) = (Cap * V * F) / (C * K * R).

    Formula (c5_thermodynamic_invariants_compendium.md, Section 6):
        d(ln J)/d(ln N) = e_Cap + e_V + e_F - e_C - e_K - e_R
    """
    for name, val in (
        ("e_cap", e_cap),
        ("e_v", e_v),
        ("e_f", e_f),
        ("e_c", e_c),
        ("e_k", e_k),
        ("e_r", e_r),
    ):
        _validate_finite(name, val)
    return (e_cap + e_v + e_f) - (e_c + e_k + e_r)


def chinchilla_loss(
    params: float,
    tokens: float,
    *,
    irreducible_e: float = 1.69,
    a: float = 406.4,
    alpha: float = 0.34,
    b: float = 410.7,
    beta: float = 0.28,
) -> float:
    """Evaluate Hoffmann et al. (2022) Chinchilla parametric neural scaling loss L(P, D)."""
    for name, val in (
        ("params", params),
        ("tokens", tokens),
        ("irreducible_e", irreducible_e),
        ("a", a),
        ("alpha", alpha),
        ("b", b),
        ("beta", beta),
    ):
        _validate_finite(name, val)
    if params <= 0.0 or tokens <= 0.0:
        raise ValueError("params and tokens must be > 0.0")
    if irreducible_e < 0.0 or a < 0.0 or alpha <= 0.0 or b < 0.0 or beta <= 0.0:
        raise ValueError("Scaling law constants must be non-negative with positive exponents")
    return irreducible_e + a / (params**alpha) + b / (tokens**beta)
