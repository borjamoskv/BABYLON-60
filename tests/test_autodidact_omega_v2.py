# ============================================================================
# BABYLON-60 v5.0 Sovereign Hardened
# █ AUTODIDACT-Ω v2.0 TEST SUITE | DOMAIN: tests | STATE: C5-REAL
# ============================================================================
"""
Suite de Pruebas de Silicio para el Motor AUTODIDACT-Ω v2.0.
Verifica:
  1. Ingesta y parsing de literatura científica (Atom XML / arXiv y Local Corpus).
  2. Invariante B4: Propagación en cascada de contradicciones sobre el DAG de dependencias (ATMS).
  3. Integridad criptográfica determinista de Cristales Epistémicos (verify_crystal_integrity).
  4. Disyuntor Bayesiano y verificación de soporte en topología de enjambre.
"""

from pathlib import Path

import json
import pytest

from babylon60.autodidact import (
    ArxivFetcher,
    AutodidactOmegaEngine,
    CrystalCompiler,
    EvidenceSource,
    Justification,
    JustifiedStatement,
    LocalCorpusFetcher,
    Modality,
    Obligation,
    Statement,
    StatementStatus,
    verify,
)
from agents_archi.topologies.autodidact_topology import AutodidactSwarmTopology


MOCK_ARXIV_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title type="html">arXiv Query: search_query=all:quantum</title>
  <entry>
    <id>http://arxiv.org/abs/2606.04484v1</id>
    <published>2026-06-08T14:32:00Z</published>
    <title>AgentJet: A Distributed Swarm Training Framework</title>
    <summary>We introduce a decoupled architecture for training LLM swarms across clusters.</summary>
    <author><name>Alice Researcher</name></author>
    <author><name>Bob Scientist</name></author>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2610.12436v1</id>
    <published>2026-10-02T09:15:00Z</published>
    <title>Ecology of AI Agents: Population Threshold for Takeoff</title>
    <summary>We study the takeoff conditions and emergent dynamics in multi-agent ecosystems.</summary>
    <author><name>Carol Polymath</name></author>
  </entry>
</feed>
"""


def test_arxiv_fetcher_parse_atom_xml() -> None:
    """Valida el parsing nativo sin dependencias de respuestas Atom XML de arXiv."""
    fetcher = ArxivFetcher()
    results = fetcher.parse_atom_xml(MOCK_ARXIV_XML)

    assert len(results) == 2
    assert results[0].source == EvidenceSource.ARXIV_PAPER
    assert isinstance(results[0].raw_payload, dict)
    assert isinstance(results[1].raw_payload, dict)
    assert results[0].digest_sha256 is not None
    assert results[0].raw_payload["title"] == "AgentJet: A Distributed Swarm Training Framework"
    assert results[0].raw_payload["arxiv_id"] == "http://arxiv.org/abs/2606.04484v1"
    assert "Alice Researcher" in results[0].raw_payload["authors"]
    assert len(results[0].digest_sha256) == 64

    assert results[1].raw_payload["title"] == "Ecology of AI Agents: Population Threshold for Takeoff"
    assert "Carol Polymath" in results[1].raw_payload["authors"]


def test_local_corpus_fetcher() -> None:
    """Valida el escaneo de evidencias locales en papers/."""
    fetcher = LocalCorpusFetcher(base_dir="papers")
    evidences = fetcher.scan_corpus()
    # No debe arrojar excepciones independientemente de qué archivos residan en papers/
    assert isinstance(evidences, list)


def test_atms_nogood_cascade_propagation_b4() -> None:
    """
    Valida la Invariante Constitucional B4:
    Falsify(c) => Review(Dependents(c)).
    La refutación de una premisa base debe propagar el estatus DISCREDITED
    y agregar a nogoods a todas las conclusiones derivadas dependientes.
    """
    engine = AutodidactOmegaEngine()

    # Premisa 1: Hipótesis vulnerable
    p1 = engine.assert_hypothesis(
        content="Sustrato cuántico superconductor a 300K",
        modality=Modality.EPISTEMIC,
        obligations=[Obligation.PROVENANCE, Obligation.REPRODUCIBILITY, Obligation.CONTRADICTION],
    )
    # Premisa 2: Hipótesis auxiliar
    p2 = engine.assert_hypothesis(
        content="La resistencia óhmica observada es cero",
        modality=Modality.EPISTEMIC,
        obligations=[Obligation.PROVENANCE, Obligation.REPRODUCIBILITY, Obligation.CONTRADICTION],
    )

    # Teorema derivado 1: Depende de p1 y p2
    t1 = engine.derive_theorem(
        premises=[p1, p2],
        goal_content="Computabilidad sin disipación Joule en temperatura ambiente",
        goal_modality=Modality.EPISTEMIC,
        goal_obligations=[Obligation.PROVENANCE, Obligation.CONTRADICTION],
    )
    initial_t1_status = t1.status
    assert initial_t1_status == StatementStatus.CANONICAL
    assert verify(t1, nogoods=engine.falsifier.nogoods) is True

    # Teorema derivado 2: Depende de t1 (dependencia indirecta en cascada)
    t2 = engine.derive_theorem(
        premises=[t1],
        goal_content="Viabilidad de red superconductora global sin refrigeración",
        goal_modality=Modality.EPISTEMIC,
        goal_obligations=[Obligation.PROVENANCE, Obligation.CONTRADICTION],
    )
    initial_t2_status = t2.status
    assert initial_t2_status == StatementStatus.CANONICAL
    assert verify(t2, nogoods=engine.falsifier.nogoods) is True

    # Comprobar aristas en el DAG
    p1_hash = p1.statement_hash
    t1_hash = t1.statement_hash
    t2_hash = t2.statement_hash
    assert p1_hash is not None
    assert t1_hash is not None
    assert t2_hash is not None
    assert t1_hash in engine.dependencies_dag[p1_hash]
    assert t2_hash in engine.dependencies_dag[t1_hash]

    # Ahora ejecutamos falsación empírica sobre la premisa p1
    # Test canario: medición de resistencia arrojando fallo
    verdict = engine.falsify_hypothesis(
        statement=p1.statement,
        test_fn=lambda: 12.5,  # Resistencia distinta de cero
        expected_output=0.0,
    )
    assert verdict.falsified is True
    assert p1.status == StatementStatus.FALSIFIED

    # INVARIANTE B4: t1 y t2 deben haber colapsado a DISCREDITED
    assert t1.status == StatementStatus.DISCREDITED
    assert t2.status == StatementStatus.DISCREDITED

    # Sus hashes deben estar registrados en nogoods
    assert t1_hash in engine.falsifier.nogoods
    assert t2_hash in engine.falsifier.nogoods

    # verify() debe fallar para t1 y t2 debido a Obligation.CONTRADICTION
    assert verify(t1, nogoods=engine.falsifier.nogoods) is False
    assert verify(t2, nogoods=engine.falsifier.nogoods) is False

    st = engine.status()
    assert st["discredited_statements"] >= 2
    assert st["falsified_nogoods"] >= 3


def test_crystal_export_and_cryptographic_verification() -> None:
    """Valida la exportación a JSON canónico y la verificación criptográfica bit a bit."""
    engine = AutodidactOmegaEngine()
    engine.assert_hypothesis("Claim A", Modality.EPISTEMIC, obligations=[])
    engine.assert_hypothesis("Claim B", Modality.EPISTEMIC, obligations=[])

    crystal = engine.compile_crystal(
        topic="Consistencia de Silicio",
        thesis="Validación determinista de invariantes.",
    )

    compiler = CrystalCompiler()
    json_str = compiler.export_json(crystal)
    assert len(json_str) > 0

    # 1. Verificación exitosa del cristal íntegro
    is_valid, msg = compiler.verify_crystal_integrity(json_str)
    assert is_valid is True
    assert "INTEGRITY_VERIFIED" in msg

    # 2. Detección de manipulación (tampering)
    crystal_dict = json.loads(json_str)
    # Alterar el hash de un statement
    crystal_dict["statements"][0]["statement_hash"] = (
        "STMT:deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
    )

    is_valid_tampered, msg_tampered = compiler.verify_crystal_integrity(crystal_dict)
    assert is_valid_tampered is False
    assert "MERKLE_MISMATCH" in msg_tampered


@pytest.mark.asyncio
async def test_bayesian_disintegration_in_swarm_topology() -> None:
    """Valida la ejecución del ciclo de enjambre con el disyuntor Bayesiano activo."""
    topology = AutodidactSwarmTopology(concurrency_limit=2)

    initial_claims = [
        {"content": "Axioma de Shannon sobre el canal", "modality": "epistemic", "confidence": 1.0},
        {"content": "Anomalía estocástica imposible", "modality": "epistemic", "confidence": 0.5},
    ]

    # Refutar la anomalía estocástica para disparar la inspección bayesiana de soporte
    verifiers = {
        "Anomalía estocástica imposible": lambda: False,
        "Axioma de Shannon sobre el canal": lambda: True,
    }

    crystal = await topology.execute_research_cycle(
        topic="Protocolo de Disyuntor Bayesiano MUSHUSHU-0",
        initial_claims=initial_claims,
        empirical_verifiers=verifiers,
    )

    assert crystal is not None
    assert len(crystal.merkle_root) == 64
    falsified = [f for f in crystal.falsification_verdicts if f.falsified]
    assert len(falsified) == 1
    assert falsified[0].claim == "Anomalía estocástica imposible"


try:
    import strike_rs as strike_rs

    HAS_STRIKE_RS = True
except ImportError:
    HAS_STRIKE_RS = False


@pytest.mark.skipif(not HAS_STRIKE_RS, reason="strike_rs rust extension is not built in this environment")
def test_native_strike_rs_acceleration(tmp_path: Path) -> None:
    """Valida la aceleración nativa de silicio con strike_rs en AutodidactOmegaEngine."""
    import strike_rs as strike_rs
    from babylon60.autodidact import HumeViolationError, derive

    # 1. Hasher nativo de statements
    native_hash = strike_rs.py_hash_statement("Velocidad de la luz es c", "epistemic")
    assert native_hash.startswith("STMT:")
    assert len(native_hash) == 69  # "STMT:" + 64 hex chars

    # 2. Guillotina de Hume nativa
    assert strike_rs.py_enforce_hume_guillotine(True, "deontic") is True
    with pytest.raises(RuntimeError, match="Hume's Guillotine Breach"):
        strike_rs.py_enforce_hume_guillotine(False, "deontic")

    # 3. Integración en derive()
    p_epi = JustifiedStatement(
        statement=Statement(content="La entropía siempre aumenta", modality=Modality.EPISTEMIC),
        justification=Justification(kind="Observation"),
    )
    goal_deo = Statement(content="Debes conservar la energía", modality=Modality.DEONTIC)
    with pytest.raises(HumeViolationError, match="Hume's Guillotine Breach"):
        derive([p_epi], goal_deo)

    # 4. Engine con puente CortexKernel activo
    db_file = str(tmp_path / "test_autodidact_native.db")
    engine = AutodidactOmegaEngine(db_path=db_file)
    assert engine.cortex_kernel is not None
    status = engine.status()
    assert status["native_cortex_bridge"] is True
    assert status["native_hume_guillotine"] is True
    assert status["native_statement_hasher"] is True

    # 5. Aserción con verificación formal Harrop en silicio
    js = engine.assert_hypothesis(
        content="Información de Fisher es invariante",
        modality=Modality.EPISTEMIC,
        obligations=[Obligation.PROVENANCE, Obligation.REPRODUCIBILITY],
        justification_kind="FormalProof",
    )
    assert js.status == StatementStatus.STABILIZED
