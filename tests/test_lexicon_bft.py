import uuid

from babylon60.bft.lexicon import LEXICON_NAMESPACE, BFTLexicon


def test_lexicon_hashing_determinism() -> None:
    lexicon = BFTLexicon()
    h1 = lexicon.get_concept_hash("ACTION")
    h2 = lexicon.get_concept_hash("ACTION")
    assert h1 == h2
    assert h1 == str(uuid.uuid5(LEXICON_NAMESPACE, "ACTION"))


def test_lexicon_resolution() -> None:
    lexicon = BFTLexicon()
    h1 = lexicon.get_concept_hash("ACTION")
    name = lexicon.resolve_hash(h1)
    assert name == "ACTION"


def test_lexicon_trace_edges() -> None:
    lexicon = BFTLexicon()
    h1 = lexicon.get_concept_hash("ACTION")
    edges = lexicon.trace_edges(h1)
    assert len(edges) >= 2
    types = [rel for rel, _ in edges]
    assert "MUTATES" in types
    assert "MAXIMIZES" in types
