# [C5-REAL] Exergy-Maximized
"""Tests for AntiLimerenceGuard."""

import pytest
from babylon60.guards.anti_limerence import AntiLimerenceGuard, _jaccard_similarity


def test_jaccard_similarity():
    text1 = "hello world"
    text2 = "world hello"
    assert _jaccard_similarity(text1, text2) == 1.0

    text3 = "hello there"
    # union: hello, world, there (3), intersection: hello (1) -> 1/3 = 0.333
    assert abs(_jaccard_similarity(text1, text3) - (1.0 / 3.0)) < 1e-6

    # empty texts
    assert _jaccard_similarity("", "text") == 0.0


def test_anti_limerence_guard_empty():
    guard = AntiLimerenceGuard()
    # Empty content should return True
    assert guard.check_iteration("") is True


def test_anti_limerence_guard_pass():
    guard = AntiLimerenceGuard()
    assert guard.check_iteration("This is the first message.") is True
    assert (
        guard.check_iteration("This is a completely different message with new concepts.") is True
    )


def test_anti_limerence_guard_trigger():
    guard = AntiLimerenceGuard(similarity_threshold=0.8, max_identical=2)
    assert guard.check_iteration("The quick brown fox jumps over the lazy dog.") is True

    # Second identical (triggers warning, returns True but identical count is 1)
    assert guard.check_iteration("The quick brown fox jumps over the lazy dog.") is True

    # Third identical (identical count reaches 2, raises RuntimeError)
    with pytest.raises(RuntimeError, match="Anti-Limerence Triggered"):
        guard.check_iteration("The quick brown fox jumps over the lazy dog.")


def test_anti_limerence_guard_reset():
    guard = AntiLimerenceGuard(max_identical=1)
    assert guard.check_iteration("Repeat me") is True
    guard.reset()
    # Should not raise because history was cleared
    assert guard.check_iteration("Repeat me") is True
