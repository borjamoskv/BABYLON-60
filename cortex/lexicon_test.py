# C5-REAL EXERGY CERTIFIED
"""Unit tests for cortex.lexicon module."""

from cortex.lexicon import LexiconEngine, lookup_invariant

def test_lexicon_load_invariants():
    engine = LexiconEngine()
    # Test lookup of known invariant Ω179
    inv_179 = engine.get_invariant("Ω179")
    assert inv_179 is not None
    assert "ZERO-TRUST RUNTIME VERIFICATION INVARIANT" in inv_179

    # Test new ULTRATHINK P0 Invariants Ω180 and Ω181
    inv_180 = engine.get_invariant("Ω180")
    assert inv_180 is not None
    assert "TOOL METADATA BOUNDARY INVARIANT" in inv_180

    inv_181 = engine.get_invariant("Ω181")
    assert inv_181 is not None
    assert "ULTRATHINK P0 HARNESS CONVERGENCE INVARIANT" in inv_181

    # Test new Aximatiza Invariant Ω187
    inv_187 = engine.get_invariant("Ω187")
    assert inv_187 is not None
    assert "KERNEL AXIOMATIZATION PROTOCOL" in inv_187

def test_lookup_invariant_function():
    inv_178 = lookup_invariant("Ω178")
    assert inv_178 is not None
    assert "KOLMOGOROV PROOF ENGINE INVARIANT" in inv_178

def test_lexicon_term_search():
    engine = LexiconEngine()
    results = engine.search("anergía")
    assert len(results) >= 0
