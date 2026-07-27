import pytest
from babylon60.core.membrane import (
    EpistemicMembrane,
    EpistemicState,
    Z3Guard,
    Z3_AVAILABLE,
    Z3ASTCompiler,
)
import ast
import time
import json


def test_epistemic_state_enum():
    assert EpistemicState.CONFIRMED.value == "confirmed"
    assert EpistemicState.REJECTED.value == "rejected"
    assert EpistemicState.UNKNOWN.value == "unknown"


def test_epistemic_membrane_initialization():
    guard = Z3Guard()
    membrane = EpistemicMembrane(z3_guard=guard)
    assert membrane.token_budget == 1000
    assert membrane.entropy_used == 0


def test_membrane_entropy_delta_estimation():
    guard = Z3Guard()
    membrane = EpistemicMembrane(z3_guard=guard)
    payload = {"key": "value"}
    delta = membrane._estimate_entropy_delta(payload)
    expected_delta = len(json.dumps(payload, ensure_ascii=False)) / 100.0
    assert delta == expected_delta


def test_membrane_causal_anchor():
    guard = Z3Guard()
    membrane = EpistemicMembrane(z3_guard=guard)

    # Con anchor provisto
    metadata = {"causal_anchor": "sim:12345"}
    assert membrane._get_causal_anchor(metadata) == "sim:12345"

    # Sin anchor (fallback)
    fallback = membrane._get_causal_anchor({})
    assert fallback.startswith("sim:")


def test_membrane_high_frequency_entropy_violation():
    guard = Z3Guard()
    membrane = EpistemicMembrane(z3_guard=guard)

    # Forzar que el tiempo sea casi idéntico
    membrane.last_write_time = time.time()

    # Payload grande para generar entropía > 5
    large_payload = {"data": "x" * 600}

    event = membrane.check(key="test", value=large_payload)

    assert event.state == EpistemicState.REJECTED
    assert event.confidence == 0.99
    assert event.z3_trace == {"reason": "High frequency entropy violation"}


def test_membrane_c5_real_reality_level():
    guard = Z3Guard()
    membrane = EpistemicMembrane(z3_guard=guard)

    # Para evitar rechazo por alta frecuencia
    membrane.last_write_time = 0

    event = membrane.check(
        key="test", value={"valid": True}, metadata={"causal_anchor": "C5-REAL:hash"}
    )

    assert event.reality_level == "C5-REAL"


def test_membrane_solver_silent_when_no_guards():
    guard = Z3Guard()
    membrane = EpistemicMembrane(z3_guard=guard)
    membrane.last_write_time = 0

    event = membrane.check(key="test", value={"valid": True}, guards=None)
    assert event.state == EpistemicState.SOLVER_SILENT


@pytest.mark.skipif(not Z3_AVAILABLE, reason="z3-solver no está instalado")
def test_z3_guard_initialization():
    guard = Z3Guard()
    assert guard.enabled is True
    assert "pricing_policy" in guard.presets


@pytest.mark.skipif(not Z3_AVAILABLE, reason="z3-solver no está instalado")
def test_z3_guard_bind_context():
    guard = Z3Guard()
    guard.bind_context({"price": 100.5, "confidence": 90, "is_valid": True})
    assert "price" in guard.variables
    assert "confidence" in guard.variables
    assert "is_valid" in guard.variables


@pytest.mark.skipif(not Z3_AVAILABLE, reason="z3-solver no está instalado")
def test_z3_guard_check_satisfied():
    guard = Z3Guard()
    # Pasa las constraints por defecto
    result = guard.check(value={"price": 50, "confidence": 50})
    assert result["status"] == "satisfied"
    assert result["satisfied"] is True


@pytest.mark.skipif(not Z3_AVAILABLE, reason="z3-solver no está instalado")
def test_z3_guard_check_violated():
    guard = Z3Guard()
    # Viola confidence <= 100
    result = guard.check(value={"price": 50, "confidence": 150})
    assert result["status"] == "violated"
    assert result["satisfied"] is False
    assert "unsat_core" in result


@pytest.mark.skipif(not Z3_AVAILABLE, reason="z3-solver no está instalado")
def test_z3_ast_compiler():
    from z3 import Real

    variables = {}
    compiler = Z3ASTCompiler(variables)

    # x + 5
    node = ast.parse("x + 5", mode="eval")
    z3_expr = compiler.compile_expr(node)
    assert "x" in variables

    # Validamos que se puede agregar al solver
    guard = Z3Guard()
    guard.add_constraint("ast_test", z3_expr > 10)
    guard.bind_context({"x": 10})
    res = guard.check()
    assert res["status"] == "satisfied"


@pytest.mark.skipif(not Z3_AVAILABLE, reason="z3-solver no está instalado")
def test_membrane_with_guards():
    guard = Z3Guard()
    membrane = EpistemicMembrane(z3_guard=guard)
    membrane.last_write_time = 0

    event = membrane.check(
        key="test", value={"price": 50, "confidence": 50}, guards=["confidence_range"]
    )

    assert event.state == EpistemicState.CONFIRMED
    assert event.confidence == 0.95


@pytest.mark.skipif(not Z3_AVAILABLE, reason="z3-solver no está instalado")
def test_membrane_with_failing_guards():
    guard = Z3Guard()
    membrane = EpistemicMembrane(z3_guard=guard)
    membrane.last_write_time = 0

    event = membrane.check(
        key="test",
        value={"price": -50, "confidence": 50},  # price_nonneg fail
        guards=["price_nonneg"],
    )

    assert event.state == EpistemicState.REJECTED
