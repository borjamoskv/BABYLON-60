import pytest
from babylon60.bft.lexicon import BFTLexicon, LEXICON_NAMESPACE
import uuid

def test_lexicon_hashing_determinism() -> None:
    lexicon = BFTLexicon()
    # Test UUIDv5 determinism
    h1 = lexicon.get_concept_hash("ACTION")
    h2 = lexicon.get_concept_hash("ACTION")
    assert h1 == h2
    assert h1 == str(uuid.uuid5(LEXICON_NAMESPACE, "ACTION"))

def test_lexicon_resolution() -> None:
    lexicon = BFTLexicon()
    # We know ACTION is seeded in cortex_lexicon.db
    h1 = lexicon.get_concept_hash("ACTION")
    name = lexicon.resolve_hash(h1)
    assert name == "ACTION"
    
def test_lexicon_trace_edges() -> None:
    lexicon = BFTLexicon()
    h1 = lexicon.get_concept_hash("ACTION")
    edges = lexicon.trace_edges(h1)
    
    # Action MUTATES Entity, and MAXIMIZES Exergy based on initial seed
    # Verify the structure holds
    assert len(edges) >= 2
    types = [rel for rel, _ in edges]
    assert "MUTATES" in types
    assert "MAXIMIZES" in types
