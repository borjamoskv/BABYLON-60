"""
test_swarm_bayesian_omega0.py — Suite de Verificación Nivel 5 (Ω₀ / Hume) y Nivel 6 (Bayes)
========================================================================================
Valida la Guillotina de Hume, la simetría conjunta en desintegración Bayesiana,
la preservación estricta de soporte y el disyuntor nulo de apoptosis MUSHUSHU-0.
"""

import pytest

from agents_archi.protocols.aof import AOFValidator, Proposition, Modality
from agents_archi.protocols.attestation import AttestationEnvelope
from agents_archi.protocols.bayesian_disintegration import (
    FiniteMarkovKernel,
    SwarmBayesianCircuitBreaker,
    HallucinatedOriginError,
)


def test_hume_guillotine_enforcement() -> None:
    """Valida que una conclusión DEONTIC no puede derivarse de premisas puramente EPISTEMIC."""
    p1 = Proposition(statement="La carga de CPU del cluster es 98%", modality=Modality.EPISTEMIC)
    p2 = Proposition(statement="El tiempo de respuesta es 450ms", modality=Modality.EPISTEMIC)
    conclusion_bad = Proposition(statement="Debes throttler los agentes inmediatamente", modality=Modality.DEONTIC)

    with pytest.raises(ValueError, match="Hume's Guillotine Breach"):
        AOFValidator.enforce_humes_guillotine([p1, p2], conclusion_bad)

    # Si se inyecta una premisa normativa legítima, pasa el filtro:
    p_norm = Proposition(statement="La política exige mitigar sobrecargas térmicas", modality=Modality.DEONTIC)
    assert AOFValidator.enforce_humes_guillotine([p1, p2, p_norm], conclusion_bad) is True


def test_bayesian_disintegration_constructive_symmetry() -> None:
    r"""Valida la simetría conjunta estricta p x f = (pf) x f^\dagger_p en un morfismo 2x2."""
    x_states = {"H0", "H1"}
    y_states = {"E0", "E1"}

    # Matriz P(Y | X)
    matrix = {
        ("H0", "E0"): 0.8,
        ("H0", "E1"): 0.2,
        ("H1", "E0"): 0.1,
        ("H1", "E1"): 0.9,
    }
    kernel = FiniteMarkovKernel(x_states, y_states, matrix)
    prior = {"H0": 0.6, "H1": 0.4}

    dual = kernel.disintegrate(prior)

    # Calcular pushforward pf:
    # pf(E0) = 0.6 * 0.8 + 0.4 * 0.1 = 0.48 + 0.04 = 0.52
    # P(H0 | E0) = (0.8 * 0.6) / 0.52 = 0.48 / 0.52 = 0.9230769
    assert abs(dual[("E0", "H0")] - (0.48 / 0.52)) < 1e-6
    # P(H1 | E0) = (0.1 * 0.4) / 0.52 = 0.04 / 0.52 = 0.0769230
    assert abs(dual[("E0", "H1")] - (0.04 / 0.52)) < 1e-6


def test_bayesian_non_hallucination_support_bound() -> None:
    r"""Valida que supp(f^\dagger_p(y)) <= supp(p) (Invariante anti-confabulación)."""
    x_states = {"RealOrigin", "PhantomOrigin"}
    y_states = {"Signal"}

    matrix = {
        ("RealOrigin", "Signal"): 1.0,
        ("PhantomOrigin", "Signal"): 1.0,
    }
    kernel = FiniteMarkovKernel(x_states, y_states, matrix)
    # PhantomOrigin tiene probabilidad cero en el prior
    prior = {"RealOrigin": 1.0, "PhantomOrigin": 0.0}

    dual = kernel.disintegrate(prior)

    # El origen fantasma debe tener exactamente 0.0 en la probabilidad posterior
    assert dual[("Signal", "PhantomOrigin")] == 0.0
    assert dual[("Signal", "RealOrigin")] == 1.0


def test_circuit_breaker_mushushu0_poison_on_hallucination() -> None:
    """Valida la activación del disyuntor nulo ante observaciones imposibles."""
    x_states = {"StateA"}
    y_states = {"ObsValid", "ObsImpossible"}

    matrix = {
        ("StateA", "ObsValid"): 1.0,
        ("StateA", "ObsImpossible"): 0.0,
    }
    kernel = FiniteMarkovKernel(x_states, y_states, matrix)
    prior = {"StateA": 1.0}

    breaker = SwarmBayesianCircuitBreaker(kernel, prior)

    # Observación válida
    post = breaker.verify_observation_step("ObsValid")
    assert post["StateA"] == 1.0

    # Observación imposible: dispara disyuntor y envenena
    with pytest.raises(HallucinatedOriginError, match="Apoptosis MUSHUSHU-0"):
        breaker.verify_observation_step("ObsImpossible")

    assert breaker.poisoned is True
    # Llamadas subsecuentes fallan inmediatamente
    with pytest.raises(RuntimeError, match="CIRCUITO ENVENENADO"):
        breaker.verify_observation_step("ObsValid")


def test_attestation_envelope_rfc9942() -> None:
    """Valida la creación y verificación de un AttestationEnvelope SCITT."""
    env = AttestationEnvelope.create(
        sender_id="agent_ring2_42",
        recipient_id="kernel_ring0",
        payload={"action": "commit_transition", "delta": "0x6060"},
        signing_key="test_dummy_key_00",
    )
    assert env.sender_id == "agent_ring2_42"
    assert env.verify(expected_key="test_dummy_key_00") is True

    # Mutación de payload detectada:
    env.payload["delta"] = "0xTAMPERED"
    assert env.verify(expected_key="test_dummy_key_00") is False
