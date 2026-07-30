# [C5-REAL] Exergy-Maximized
import pytest
from decimal import Decimal
from babylon60.engine.causal.reality_ledger import RealityLedger, BeliefNode


def test_add_belief_and_topological_sort():
    ledger = RealityLedger()
    ledger.add_belief("A", Decimal("10.0"), False)
    ledger.add_belief("B", Decimal("5.0"), True, ["A"])
    ledger.add_belief("C", Decimal("2.0"), False, ["A", "B"])

    sort = ledger.topological_sort()
    assert sort == ["A", "B", "C"]


def test_cycle_detection():
    ledger = RealityLedger()
    ledger.add_belief("A", Decimal("10.0"), False)
    ledger.add_belief("B", Decimal("5.0"), False, ["A"])
    # Force a cycle manually since add_belief verifies parents exist before adding
    ledger.nodes["A"].parents.add("B")
    ledger.nodes["B"].children.add("A")

    with pytest.raises(ValueError, match="Cycle detected"):
        ledger.topological_sort()


def test_cumulative_exergy():
    ledger = RealityLedger()
    ledger.add_belief("A", Decimal("10.0"), False)
    ledger.add_belief("B", Decimal("5.0"), True, ["A"])  # Diamond: 5 * 1.5 = 7.5

    cum = ledger.calculate_cumulative_exergy()
    assert cum["A"] == Decimal("10.0")
    # B cumulative = 7.5 + (10 * 0.9) = 16.5
    assert cum["B"] == Decimal("16.5")


def test_invalidate_belief_cascade():
    ledger = RealityLedger()
    ledger.add_belief("A", Decimal("10.0"), False)
    ledger.add_belief("B", Decimal("5.0"), False, ["A"])
    ledger.add_belief("C", Decimal("2.0"), False, ["B"])

    invalidated = ledger.invalidate_belief("A")
    assert set(invalidated) == {"A", "B", "C"}
    assert ledger.nodes["A"].is_invalidated
    assert ledger.nodes["A"].exergy == Decimal("0.0")
    assert ledger.nodes["C"].is_invalidated

    cum = ledger.calculate_cumulative_exergy()
    assert cum["A"] == Decimal("0.0")
    assert cum["B"] == Decimal("0.0")
    assert cum["C"] == Decimal("0.0")


def test_verifier_pass():
    ledger = RealityLedger()
    ledger.add_belief("A", Decimal("10.0"), False)
    ledger.add_belief("B", Decimal("5.0"), True, ["A"])

    results = ledger.verifier_pass()
    assert results["A"] is True
    assert results["B"] is True

    ledger.invalidate_belief("B")
    # Now B is diamond but exergy is 0 -> dead branch warning -> False
    results2 = ledger.verifier_pass()
    assert results2["A"] is True
    assert results2["B"] is False
