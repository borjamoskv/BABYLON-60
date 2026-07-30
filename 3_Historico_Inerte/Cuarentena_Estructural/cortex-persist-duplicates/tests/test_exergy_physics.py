# [C5-REAL] Exergy-Maximized
from babylon60.engine.core.ultrathink_physics import UltrathinkPhysicsEngine

import pytest


@pytest.fixture(autouse=True)
def mock_thermal_penalty(monkeypatch):
    monkeypatch.setattr(
        "babylon60.engine.core.ultrathink_physics.UltrathinkPhysicsEngine.get_thermal_penalty",
        classmethod(lambda cls: 1.05),
    )



def test_exergy_yield_calculation():
    """Test the derivation of cognitive exergy."""
    # S_stoc = 15.0, S_det = 120.0, T = 2.0s
    # Thermal penalty (Landauer): 1.05^2 = 1.1025
    # Raw Exergy: (120-15)/2 = 52.5
    # Net Exergy: 52.5 / 1.1025 = 47.619047619
    exergy = UltrathinkPhysicsEngine.calculate_exergy_yield(15.0, 120.0, 2.0)
    assert exergy == pytest.approx(47.6190476, rel=1e-5)

    # Negative Exergy -> Should cap at 0
    negative_exergy = UltrathinkPhysicsEngine.calculate_exergy_yield(200.0, 10.0, 1.0)
    assert negative_exergy == 0.0


def test_blast_radius_measurement():
    """Test the topological depth of an isolated failure graph."""
    deps = {"A": ["B", "C"], "B": ["D"], "C": [], "D": ["E", "F"], "E": [], "F": []}

    # Epicenter A touches all 6 nodes
    assert UltrathinkPhysicsEngine.measure_blast_radius(deps, "A") == 6

    # Epicenter B touches B, D, E, F (4)
    assert UltrathinkPhysicsEngine.measure_blast_radius(deps, "B") == 4

    # Epicenter F touches only F (1)
    assert UltrathinkPhysicsEngine.measure_blast_radius(deps, "F") == 1


def test_ultrathink_authorization():
    """Validates the P0 Horizon decision."""
    # Valid Ultrathink: Exergy > 10, Blast >= 3
    auth, msg, formation = UltrathinkPhysicsEngine.authorize_ultrathink(10.0, 200.0, 5.0, 4)
    assert auth is True
    assert formation is not None
    assert "Authorized" in msg

    # Invalid: small blast radius
    auth, msg, formation = UltrathinkPhysicsEngine.authorize_ultrathink(10.0, 200.0, 5.0, 2)
    assert auth is False
    assert "small" in msg

    # Invalid: Low exergy yield
    auth, msg, formation = UltrathinkPhysicsEngine.authorize_ultrathink(50.0, 60.0, 10.0, 5)
    assert auth is False
    assert "Insufficient" in msg


def test_ultrathink_critical_authorization():
    """Verify that critical domains trigger with lower exergy and blast requirements."""
    # A standard node with blast radius 2 fails
    auth, msg, formation = UltrathinkPhysicsEngine.authorize_ultrathink(
        10.0, 200.0, 5.0, 2, epicenter_node="ordinary_node"
    )
    assert auth is False

    # A critical node (e.g. "master_ledger") with blast radius 2 succeeds because radius is amplified and exergy threshold is halved
    auth, msg, formation = UltrathinkPhysicsEngine.authorize_ultrathink(
        10.0, 100.0, 10.0, 2, epicenter_node="master_ledger"
    )
    # exergy = (100 - 10) / 10 = 9.0. Required for critical: 0.05 * 100 = 5.0. 9.0 >= 5.0 -> True.
    # effective_radius = 2 * 1.5 = 3. min_radius = 2 -> True.
    assert auth is True
    assert "Authorized" in msg


def test_exergy_yield_calculation_overflow_handling():
    """Verify that extreme execution times do not trigger OverflowError (VM-03)."""
    # 1.05 ** 1e9 will overflow standard floats
    exergy = UltrathinkPhysicsEngine.calculate_exergy_yield(10.0, 100.0, 1e9)
    assert exergy == 0.0


def test_blast_radius_type_safety():
    """Verify that non-dict graphs are coerced safely (VM-05)."""
    assert UltrathinkPhysicsEngine.measure_blast_radius("not_a_dict", "A") == 1
    # Check sets/tuples are parsed correctly
    deps_with_sets = {"A": {"B", "C"}, "B": ("D",), "C": set()}
    assert UltrathinkPhysicsEngine.measure_blast_radius(deps_with_sets, "A") == 4


def test_ultrathink_arsenal_path_resolution():
    """Verify that SYS_OPERATOR placeholders are resolved dynamically at runtime (VM-04)."""
    from babylon60.agents.primitives.ultrathink_arsenal import get_ultrathink_arsenal
    import getpass

    current_user = getpass.getuser()
    resolved_directives = get_ultrathink_arsenal()

    # Locate a target that originally had SYS_OPERATOR
    found_target = False
    for directive in resolved_directives:
        if "Users" in directive.target:
            assert "SYS_OPERATOR" not in directive.target
            assert current_user in directive.target
            found_target = True

    assert found_target is True


def test_estimate_shannon_entropy():
    """Verify that text Shannon Entropy is calculated accurately."""
    # Empty string should yield 0.0
    assert UltrathinkPhysicsEngine.estimate_shannon_entropy("") == 0.0

    # Single repeating character should yield 0.0 (no uncertainty/entropy)
    assert UltrathinkPhysicsEngine.estimate_shannon_entropy("aaaaa") == 0.0

    # Equal distribution of two characters (a, b) should yield 1.0 bit
    assert UltrathinkPhysicsEngine.estimate_shannon_entropy("abab") == pytest.approx(1.0, rel=1e-5)


def test_ultrathink_nan_inf_safety():
    """Verify that NaN and Inf values are safely rejected by exergy engine."""
    import math

    # NaN check for yield
    assert UltrathinkPhysicsEngine.calculate_exergy_yield(float("nan"), 100.0, 2.0) == 0.0
    assert UltrathinkPhysicsEngine.calculate_exergy_yield(10.0, float("inf"), 2.0) == 0.0
    assert UltrathinkPhysicsEngine.calculate_exergy_yield(10.0, 100.0, float("nan")) == 0.0

    # NaN check for authorization
    auth, msg, formation = UltrathinkPhysicsEngine.authorize_ultrathink(
        stochastic_entropy=float("nan"),
        deterministic_output=100.0,
        execution_time=2.0,
        epicenter_radius=4,
    )
    assert auth is False
    assert formation is None

    # Epicenter radius NaN check
    auth, msg, formation = UltrathinkPhysicsEngine.authorize_ultrathink(
        stochastic_entropy=10.0,
        deterministic_output=200.0,
        execution_time=5.0,
        epicenter_radius=float("nan"),
    )
    assert auth is False
    assert "Invalid epicenter radius" in msg


def test_dynamic_critical_domains(monkeypatch):
    """Verify dynamic mapping of critical domains from environment variables."""
    import os

    # Check resolving dynamic domain
    monkeypatch.setenv("CORTEX_CRITICAL_DOMAINS", "custom_subsystem,another_subsystem")

    risk_mult, is_crit = UltrathinkPhysicsEngine._resolve_risk("my_custom_subsystem_engine")
    assert is_crit is True
    assert risk_mult == 1.5

    risk_mult_std, is_crit_std = UltrathinkPhysicsEngine._resolve_risk("ordinary_node")
    assert is_crit_std is False
    assert risk_mult_std == 1.0


def test_measure_blast_metrics():
    """Verify that measure_blast_metrics computes both volume and tree depth correctly."""
    # Graph representing: A -> B -> C -> D, and A -> E
    deps = {"A": ["B", "E"], "B": ["C"], "C": ["D"], "D": [], "E": []}

    metrics = UltrathinkPhysicsEngine.measure_blast_metrics(deps, "A")
    assert metrics["volume"] == 5
    assert metrics["depth"] == 3  # A -> B -> C -> D is 3 hops

    # Verification of backward compatibility via measure_blast_radius
    assert UltrathinkPhysicsEngine.measure_blast_radius(deps, "A") == 5
