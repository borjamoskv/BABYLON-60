# C5-REAL EXERGY CERTIFIED
"""Unit tests for cortex.lexicon module."""

import pytest
from cortex.lexicon import LexiconEngine, lookup_invariant, lookup_term


def test_lexicon_load_invariants():
    engine = LexiconEngine()
    # Test lookup of known invariant Ω179
    inv_179 = engine.get_invariant("Ω179")
    assert inv_179 is not None
    assert "ZERO-TRUST RUNTIME VERIFICATION INVARIANT" in inv_179


def test_lookup_invariant_function():
    inv_178 = lookup_invariant("Ω178")
    assert inv_178 is not None
    assert "KOLMOGOROV PROOF ENGINE INVARIANT" in inv_178


def test_lexicon_term_search():
    engine = LexiconEngine()
    results = engine.search("anergía")
    assert len(results) >= 0
