from __future__ import annotations

import pytest

from scripts.c5_cli.markov_bridge import (
    MarkovLexicalBridge,
    classify_pos,
    main,
)


def test_classify_pos_only_nouns_and_verbs() -> None:
    # Verbos válidos
    assert classify_pos("transformar") == "VERB"
    assert classify_pos("ejecuta") == "VERB"
    assert classify_pos("calculando") == "VERB"
    assert classify_pos("verificar") == "VERB"

    # Sustantivos válidos
    assert classify_pos("sistema") == "NOUN"
    assert classify_pos("memoria") == "NOUN"
    assert classify_pos("física") == "NOUN"
    assert classify_pos("operador") == "NOUN"

    # Clases cerradas, adverbios y adjetivos deben ser rechazados (None)
    for rejected in (
        "el",
        "para",
        "mediante",
        "aunque",
        "rápidamente",
        "siempre",
        "muy",
        "posible",
        "necesario",
        "grande",
        "maravilloso",
        "operativo",
    ):
        assert classify_pos(rejected) is None, f"{rejected} no debería admitirse"


def test_find_bridge_direct_two_step_markov() -> None:
    engine = MarkovLexicalBridge(window_size=2, decay=0.8)
    engine.ingest_text(
        "El operador compila código rápidamente. "
        "El operador compila código siempre. "
        "El código genera binarios posibles. "
        "El código genera binarios grandes."
    )
    res = engine.find_bridge("operador", "binarios")
    # Entre 'operador' y 'binarios', el puente de máxima verosimilitud es 'código' o 'compila'/'genera'
    assert res.origin == "operador"
    assert res.target == "binarios"
    assert res.bridge in {"código", "compila", "genera"}
    assert classify_pos(res.bridge) in {"NOUN", "VERB"}
    assert res.joint_score > 0.0


def test_find_bridge_multihop_geodesic() -> None:
    engine = MarkovLexicalBridge(window_size=1, decay=1.0)
    engine.ingest_text("energía alimenta motor.\n\nmotor impulsa rueda.\n\nrueda mueve vehículo.")
    res = engine.find_bridge("energía", "vehículo")
    assert res.origin == "energía"
    assert res.bridge == "alimenta"
    assert res.full_path == (
        "energía",
        "alimenta",
        "motor",
        "impulsa",
        "rueda",
        "mueve",
        "vehículo",
    )


def test_rejects_non_noun_verb_input() -> None:
    engine = MarkovLexicalBridge()
    engine.ingest_text("sistema ejecuta cálculo mediante memoria")
    try:
        engine.find_bridge("mediante", "memoria")
        raise AssertionError("Debió rechazar una preposición")
    except ValueError as exc:
        assert "solo se admiten sustantivos y verbos" in str(exc)


def test_cli_single_and_pair_execution(capsys: pytest.CaptureFixture[str]) -> None:
    rc1 = main(["sistema", "memoria"])
    out1 = capsys.readouterr().out
    assert rc1 == 0
    assert "IMPRESCINDIBLE (w*):" in out1
    assert "Flujo=" in out1

    rc2 = main(["transformar"])
    out2 = capsys.readouterr().out
    assert rc2 == 0
    assert "IMPRESCINDIBLE (w*):" in out2

    rc3 = main(["sistema", "memoria", "--rag"])
    out3 = capsys.readouterr().out
    assert rc3 == 0
    assert "EVIDENCIA RECUPERADA (GraphRAG Local Cero-Embeddings)" in out3

    rc4 = main(["sistema", "memoria", "--json"])
    out4 = capsys.readouterr().out
    assert rc4 == 0
    assert '"origin": "sistema"' in out4
    assert '"bridge":' in out4
    assert '"bottleneck_ratio":' in out4


def test_graph_rag_retrieval_chunks() -> None:
    engine = MarkovLexicalBridge(window_size=2, decay=0.9)
    engine.ingest_text(
        "El núcleo protege la memoria crítica.\n\nLa memoria registra eventos causales.",
        source_path="/test/kernel.md",
    )
    rag = engine.graph_rag("núcleo", "eventos")
    assert rag.bridge_result.origin == "núcleo"
    assert rag.bridge_result.target == "eventos"
    assert rag.bridge_result.bridge == "memoria"
    # Debe haber recuperado los dos bloques de evidencia causal
    assert len(rag.leg_1_chunks) >= 1
    assert rag.leg_1_chunks[0].source == "/test/kernel.md"
    assert "núcleo protege la memoria" in rag.leg_1_chunks[0].snippet
    assert len(rag.leg_2_chunks) >= 1
    assert "memoria registra eventos" in rag.leg_2_chunks[0].snippet


def test_markdown_code_fence_stripping_and_stem_resolution() -> None:
    engine = MarkovLexicalBridge(window_size=2, decay=0.9)
    engine.ingest_text("```rust\nfn wip_noise() { let foo = bar; }\n```\n\nEl operador consolida la memoria soberana.")
    assert "wip" not in engine.unigram_counts
    # Consulta usando flexiones ('consolidar', 'memorias') que se resuelven por raíz morfológica
    assert engine.resolve_word("memorias") == "memoria"
    assert engine.resolve_word("consolidar") == "consolida"
    res = engine.find_bridge("operador", "memorias")
    assert res.bridge == "consolida"
