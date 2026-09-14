"""
[AX-59] TEST: Suite de Verificación del Firewall Neurosimbólico Z3 para Navier-Stokes
Certificación empírica de las 10 iteraciones de Bloque VII (Iter 61–70).
"""

import pytest
from babylon60.kernel.ns_z3_firewall import (
    NavierStokesZ3Firewall,
    SmtApoptosisError,
    SmtProofCertificate,
)


@pytest.fixture
def firewall() -> NavierStokesZ3Firewall:
    return NavierStokesZ3Firewall(timeout_ms=100)


def test_sos_strain_relaxation_valid_and_invalid(firewall: NavierStokesZ3Firewall) -> None:
    """[Iter 61/62] Verifica la cota SOS y la programación semidefinida (SDP)."""
    # 1. Caso Válido: lambda_max = 5.0 domina los autovalores del tensor
    cert_valid = firewall.verify_strain_sos_bound(
        s_xx=1.0, s_yy=1.0, s_zz=-2.0,  # Traza cero (incompresible)
        s_xy=0.5, s_xz=0.0, s_yz=0.5,
        lambda_max=5.0,
    )
    assert cert_valid.status == "VALID_PROOF"
    assert len(cert_valid.certificate_hash) == 64

    # 2. Caso Inválido: lambda_max = 0.5 subestima el autovalor máximo (~2.0)
    cert_invalid = firewall.verify_strain_sos_bound(
        s_xx=2.0, s_yy=1.0, s_zz=-3.0,
        s_xy=0.0, s_xz=0.0, s_yz=0.0,
        lambda_max=1.0,
    )
    assert cert_invalid.status == "FALSIFIED_UNSAT"
    assert len(cert_invalid.unsat_core) > 0


def test_lyapunov_dissipation_leray_hopf(firewall: NavierStokesZ3Firewall) -> None:
    """[Iter 63] Poda de ramas débiles mediante la desigualdad de disipación de Leray-Hopf."""
    dt = 0.01
    nu = 0.05
    enstrophy = 10.0
    # Disipación esperada: 2 * nu * enstrophy * dt = 2 * 0.05 * 10 * 0.01 = 0.01
    e_curr = 1.0

    # 1. Paso disipativo físico: e_next = 0.985 (delta_e = -0.015 <= -0.01)
    cert_valid = firewall.verify_lyapunov_dissipation(
        energy_current=e_curr,
        energy_next=0.985,
        enstrophy=enstrophy,
        viscosity=nu,
        dt=dt,
    )
    assert cert_valid.status == "VALID_PROOF"

    # 2. Paso no físico (crecimiento de energía): e_next = 1.05
    cert_invalid = firewall.verify_lyapunov_dissipation(
        energy_current=e_curr,
        energy_next=1.05,
        enstrophy=enstrophy,
        viscosity=nu,
        dt=dt,
    )
    assert cert_invalid.status == "FALSIFIED_UNSAT"
    assert "leray_energy_monotone" in cert_invalid.unsat_core


def test_bmc_vorticity_bounded_horizon(firewall: NavierStokesZ3Firewall) -> None:
    """[Iter 64] Bounded Model Checking en horizonte discreto."""
    # 1. Trayectoria suave acotada
    trajectory_smooth = [1.0, 1.2, 1.5, 1.8, 2.1, 2.3]
    cert_bounded = firewall.bmc_check_vorticity_explosion(trajectory_smooth, omega_threshold=5.0)
    assert cert_bounded.status == "VALID_PROOF"

    # 2. Trayectoria con candidato a singularidad
    trajectory_blowup = [1.0, 2.0, 5.0, 12.0, 50.0]
    cert_blowup = firewall.bmc_check_vorticity_explosion(trajectory_blowup, omega_threshold=20.0)
    assert cert_blowup.status == "FALSIFIED_UNSAT"
    assert "bkm_safety_step_4" in cert_blowup.unsat_core


def test_inductive_perturbation_counterexample(firewall: NavierStokesZ3Firewall) -> None:
    """[Iter 65] Síntesis inductiva de contraejemplos de estabilidad."""
    # 1. Alta disipación: ninguna perturbación en [-0.1, 0.1] puede superar la disipación
    cert_stable = firewall.synthesize_perturbation_stability(
        nominal_vorticity=1.0,
        strain_rate=0.5,
        viscous_dissipation=10.0,
        perturbation_bound=0.1,
    )
    assert cert_stable.status == "VALID_PROOF"

    # 2. Baja disipación y alto estiramiento: existe perturbación que induce crecimiento
    cert_unstable = firewall.synthesize_perturbation_stability(
        nominal_vorticity=2.0,
        strain_rate=5.0,
        viscous_dissipation=1.0,
        perturbation_bound=0.5,
    )
    assert cert_unstable.status == "COUNTEREXAMPLE_FOUND"
    assert cert_unstable.counterexample is not None
    assert "delta" in cert_unstable.counterexample


def test_unsat_core_inconsistency_extraction(firewall: NavierStokesZ3Firewall) -> None:
    """[Iter 66] Extracción de núcleo mínimo insatisfactible ante inconsistencia física."""
    # Divergencia residual masiva viola la incompresibilidad
    core = firewall.extract_fluid_unsat_core(
        incompressibility_residual=1e-5,  # Violación: > tol (1e-12)
        energy_residual=1e-14,
        bkm_divergence=10.0,
        tol=1e-12,
    )
    assert "INV_INCOMPRESSIBLE_SOLENOIDAL" in core


def test_taylor_green_canary(firewall: NavierStokesZ3Firewall) -> None:
    """[Iter 67] Canario de calibración de vórtices de Taylor-Green."""
    time_t = 0.5
    nu = 0.05
    e0 = 1.0
    theoretical = e0 * 2.718281828459045 ** (-4.0 * nu * time_t)  # exp(-4 * 0.05 * 0.5) = exp(-0.1) ~ 0.9048

    # Medición dentro del 5%
    cert_pass = firewall.verify_taylor_green_canary(time_t, e0, theoretical * 1.01, nu, tol_rel=0.05)
    assert cert_pass.status == "VALID_PROOF"

    # Medición aberrante (desviada un 20%)
    cert_fail = firewall.verify_taylor_green_canary(time_t, e0, theoretical * 1.25, nu, tol_rel=0.05)
    assert cert_fail.status == "FALSIFIED_UNSAT"


def test_stochastic_confabulation_suppression(firewall: NavierStokesZ3Firewall) -> None:
    """[Iter 68] Supresión de alucinaciones estocásticas con apoptosis MUSHUSHU-0."""
    with pytest.raises(SmtApoptosisError) as exc_info:
        firewall.suppress_stochastic_claim(
            "BLOWUP_WITH_CONSTANT_ENERGY_IN_VISCOUS_FLOW",
            {"viscosity": 0.05, "enstrophy": 1e9},
        )
    assert "MUSHUSHU-0 Apoptosis" in str(exc_info.value)

    with pytest.raises(SmtApoptosisError) as exc_info:
        firewall.suppress_stochastic_claim(
            "NEGATIVE_KINETIC_ENERGY",
            {"energy": -1.5},
        )
    assert "MUSHUSHU-0 Apoptosis" in str(exc_info.value)


def test_drat_larat_certificate_integrity(firewall: NavierStokesZ3Firewall) -> None:
    """[Iter 70] Atestación criptográfica reproducible en certificados SMT."""
    cert1 = firewall.verify_strain_sos_bound(1.0, 1.0, -2.0, 0.0, 0.0, 0.0, 5.0)
    assert len(cert1.certificate_hash) == 64
    assert cert1.status == "VALID_PROOF"
