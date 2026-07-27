# [C5-REAL] Exergy-Maximized
"""Tests for LandauerGuard."""

import pytest
from babylon60.guards.landauer_guard import LandauerGuard
from babylon60.security.types import GuardViolation


def test_landauer_guard_empty():
    assert LandauerGuard.validate("") is False


def test_landauer_guard_too_large():
    # max bytes is 256
    large_text = "A" * 300
    assert LandauerGuard.validate(large_text) is False


def test_landauer_guard_low_entropy():
    # Repeating pattern has very low entropy
    low_entropy = "A" * 100
    # Must be under 256 bytes but also > 3.5 entropy
    assert LandauerGuard.validate(low_entropy) is False


def test_landauer_guard_valid():
    # A highly entropic string.
    high_entropy_text = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()"
    assert LandauerGuard.validate(high_entropy_text) is True


def test_landauer_enforce_sacred_pass():
    high_entropy_text = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()"
    metadata = {"fact_type": "axiom"}
    # Should not raise
    LandauerGuard.enforce(high_entropy_text, metadata)


def test_landauer_enforce_sacred_fail():
    low_entropy_text = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    metadata = {"tags": ["sacred"]}
    with pytest.raises(GuardViolation, match="Axiom rejected \\(Ω₄\\)"):
        LandauerGuard.enforce(low_entropy_text, metadata)


def test_landauer_enforce_non_sacred():
    low_entropy_text = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    metadata = {"fact_type": "regular"}
    # Should not raise because it's not sacred
    LandauerGuard.enforce(low_entropy_text, metadata)
