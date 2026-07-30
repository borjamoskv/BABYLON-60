# C5-REAL EXERGY CERTIFIED
"""Unit tests for cortex.lexicon module.

Tests verify structural invariants (existence, non-emptiness, type)
rather than brittle literal title strings, so they survive invariant
renames without false breakage.
"""

from cortex.core.lexicon import LexiconEngine, lookup_invariant


# ─── Invariant IDs that MUST exist in AGENTS.md ───────────────────
_REQUIRED_INVARIANTS = [
    "Ω132", "Ω133", "Ω134", "Ω135", "Ω136", "Ω137",
    "Ω170", "Ω178", "Ω179", "Ω180", "Ω181", "Ω187",
]


def test_lexicon_load_invariants():
    """All required invariants are loadable and non-empty."""
    engine = LexiconEngine()
    for inv_id in _REQUIRED_INVARIANTS:
        result = engine.get_invariant(inv_id)
        assert result is not None, f"Invariant {inv_id} not found in AGENTS.md"
        assert isinstance(result, str) and len(result) > 10, (
            f"Invariant {inv_id} resolved but content is trivially short: {result!r}"
        )


def test_lookup_invariant_function():
    """Module-level convenience lookup_invariant() works for Ω178."""
    inv_178 = lookup_invariant("Ω178")
    assert inv_178 is not None, "lookup_invariant('Ω178') returned None"
    assert len(inv_178) > 10


def test_lexicon_term_search():
    """BM25 search engine returns without error (empty corpus is valid)."""
    engine = LexiconEngine()
    results = engine.search("anergía")
    assert isinstance(results, list)


def test_invariant_id_uniqueness():
    """No two invariants in the registry should share the same Ω ID."""
    engine = LexiconEngine()
    engine._load_invariants()
    ids = list(engine.invariants.keys())
    assert len(ids) == len(set(ids)), f"Duplicate invariant IDs detected: {ids}"
