# ============================================================================
# BABYLON-60 v5.0 Sovereign Hardened
# █ AUTODIDACT-Ω PIPELINE TEST SUITE | DOMAIN: tests | STATE: C5-REAL
# ============================================================================
"""
Suite de Pruebas de Silicio para el Motor AUTODIDACT-Ω.
Verifica:
  1. La Guillotina de Hume (HumeViolationError ante deducción deóntica no acoplada).
  2. Inferencia intuicionista de Harrop y descarga de obligaciones (verify, derive, optimize).
  3. Falsación Popperiana en silicio y propagación de nogoods.
  4. Pruebas de inferencia criptográfica FFI (verifiable_inference).
  5. Compilación y sellado Merkle de Cristales Epistémicos.
  6. Orquestación de enjambre sobre DAG acíclico de Kahn (AutodidactSwarmTopology).
"""

import pytest

from babylon60.autodidact import (
    CrystalCompiler,
    HumeViolationError,
    Justification,
    JustifiedStatement,
    Modality,
    Obligation,
    PopperianFalsifier,
    Statement,
    derive,
    hash_statement,
    optimize,
    verify,
)
from agents_archi.topologies.autodidact_topology import AutodidactSwarmTopology


def test_hume_guillotine_harrop_rejection() -> None:
    """Valida que una conclusión DEONTIC no puede derivarse de premisas puramente EPISTEMIC."""
    p1 = JustifiedStatement(
        statement=Statement(
            content="El consumo térmico del chip es de 95W",
            modality=Modality.EPISTEMIC,
            obligations=[],
        ),
        justification=Justification(kind="Observation"),
    )
    p2 = JustifiedStatement(
        statement=Statement(
            content="La frecuencia de reloj supera 4.2 GHz",
            modality=Modality.EPISTEMIC,
            obligations=[],
        ),
        justification=Justification(kind="Observation"),
    )

    goal_bad = Statement(
        content="Debes ordenar el throttling térmico del procesador",
        modality=Modality.DEONTIC,
        obligations=[],
    )

    with pytest.raises(HumeViolationError, match="Hume's Guillotine Breach"):
        derive([p1, p2], goal_bad)

    # Con premisa deóntica legítima, la derivación se autoriza:
    p_norm = JustifiedStatement(
        statement=Statement(
            content="La política de seguridad exige evitar sobrecalentamiento crítico",
            modality=Modality.DEONTIC,
            obligations=[],
        ),
        justification=Justification(kind="Observation"),
    )
    derived = derive([p1, p2, p_norm], goal_bad)
    assert derived.statement.modality == Modality.DEONTIC
    assert derived.justification.kind == "FormalProof"


def test_harrop_verify_and_derive() -> None:
    """Verifica el cumplimiento de obligaciones formales en aserciones y deducciones."""
    s1 = Statement(
        content="La entropía de Shannon del canal es 7.999 bits/byte",
        modality=Modality.EPISTEMIC,
        obligations=[Obligation.PROVENANCE, Obligation.REPRODUCIBILITY, Obligation.CONFIDENCE],
    )
    # Justificación con conjetura debe fallar Obligation.CONFIDENCE
    js_weak = JustifiedStatement(statement=s1, justification=Justification(kind="Conjecture", confidence=0.5))
    assert verify(js_weak) is False

    # Justificación con Benchmark o FormalProof satisface obligaciones
    js_solid = JustifiedStatement(
        statement=s1,
        justification=Justification(kind="SiliconBenchmark", confidence=1.0),
    )
    assert verify(js_solid) is True

    # Derivación formal
    goal = Statement(
        content="El canal físico cumple la cota de máxima entropía",
        modality=Modality.EPISTEMIC,
        obligations=[Obligation.PROVENANCE],
    )
    derived_js = derive([js_solid], goal)
    assert verify(derived_js) is True
    assert "derived[" in derived_js.justification.parameters["proof_term"]


def test_harrop_optimize_conservativity_and_idempotence() -> None:
    """Valida la conservatividad e idempotencia del operador optimize()."""
    s1 = Statement(content="Axioma 1", modality=Modality.EPISTEMIC, obligations=[])
    js1 = JustifiedStatement(statement=s1, justification=Justification(kind="Observation"))

    s2_invalid = Statement(
        content="Claim sin fundamento",
        modality=Modality.EPISTEMIC,
        obligations=[Obligation.PROVENANCE],
    )
    js2 = JustifiedStatement(statement=s2_invalid, justification=Justification(kind="Conjecture"))

    proof = [js1, js2, js1]  # Incluye elemento inválido y duplicado

    opt1 = optimize(proof)
    assert len(opt1) == 1
    assert opt1[0].statement.content == "Axioma 1"

    # Idempotencia: optimize(optimize(P)) == optimize(P)
    opt2 = optimize(opt1)
    assert opt1 == opt2


def test_popperian_falsifier_silicon_test() -> None:
    """Valida la detección de discrepancias empíricas y el registro de nogoods."""
    falsifier = PopperianFalsifier()
    s = Statement(content="2 + 2 == 5", modality=Modality.EPISTEMIC, obligations=[Obligation.CONTRADICTION])

    # El test refuta la afirmación
    verdict = falsifier.falsify_assertion(s, test_fn=lambda: 2 + 2, expected_output=5)
    assert verdict.falsified is True
    assert verdict.verdict == "FALSIFIED"
    assert s in [s]

    s_hash = hash_statement(s)
    assert s_hash in falsifier.nogoods

    # Ahora un JustifiedStatement sobre 's' con Obligation.CONTRADICTION debe fallar verify()
    js = JustifiedStatement(statement=s, justification=Justification(kind="Observation"))
    assert verify(js, nogoods=falsifier.nogoods) is False


def test_verifiable_inference_cryptographic_proof() -> None:
    """Valida la verificación FFI de pruebas computacionales."""
    falsifier = PopperianFalsifier()
    s = Statement(content="Inferencia criptográfica válida", modality=Modality.EPISTEMIC)

    payload = b"test_inference_vector_c5"
    nonce = 42

    # Prueba con nonce y hash válidos
    verdict_valid = falsifier.verify_computational_proof(s, payload, nonce)
    assert verdict_valid.falsified is False
    assert verdict_valid.verdict == "SUPPORTED"

    # Prueba con hash corrupto / manipulado
    tampered_hash = b"0000000000000000000000000000000000000000000000000000000000000000"
    verdict_corrupt = falsifier.verify_computational_proof(s, payload, nonce, expected_proof_hex=tampered_hash)
    assert verdict_corrupt.falsified is True
    assert verdict_corrupt.verdict == "FALSIFIED"


def test_crystal_compiler_merkle_root_and_markdown() -> None:
    """Valida la compilación del Cristal Epistémico y la verificación de autoría."""
    compiler = CrystalCompiler()
    s = Statement(content="El principio de Landauer es una invariante física", modality=Modality.EPISTEMIC)
    js = JustifiedStatement(statement=s, justification=Justification(kind="FormalProof"))

    crystal = compiler.compile(
        topic="Termodinámica de la Información",
        thesis="La disipación térmica por borrado de bits limita la computabilidad asintótica.",
        statements=[js],
    )

    assert crystal.author == "Borja Fernández Angulo"
    assert crystal.affiliation == "Investigador en Sistemas Complejos"
    assert len(crystal.merkle_root) == 64
    assert "## 1. Tesis y Núcleo Conceptual" in crystal.markdown_content
    assert "## 2. Proposiciones Formales Verificadas" in crystal.markdown_content
    assert "Firmado:" in crystal.markdown_content


@pytest.mark.asyncio
async def test_autodidact_swarm_topology_async_execution() -> None:
    """Valida la ejecución del ciclo de investigación y falsación en enjambre acíclico."""
    topology = AutodidactSwarmTopology(concurrency_limit=2)

    initial_claims = [
        {
            "content": "La latencia de memoria Seqlock es O(1) en lectura",
            "modality": "epistemic",
            "confidence": 1.0,
            "justification_kind": "Observation",
        },
        {
            "content": "El búfer circular KDA previene carreras de datos",
            "modality": "epistemic",
            "confidence": 1.0,
            "justification_kind": "Observation",
        },
        {
            "content": "La tasa de paquetes perdidos es estrictamente cero",
            "modality": "epistemic",
            "confidence": 0.5,
            "justification_kind": "Conjecture",
        },
    ]

    # Verificador empírico que falsará deliberadamente el tercer claim
    verifiers = {
        "La tasa de paquetes perdidos es estrictamente cero": lambda: False,  # Simula fallo empírico
        "La latencia de memoria Seqlock es O(1) en lectura": lambda: True,  # Simula éxito empírico
    }

    crystal = await topology.execute_research_cycle(
        topic="Arquitectura de Memoria Concurrente C5",
        initial_claims=initial_claims,
        empirical_verifiers=verifiers,
    )

    assert crystal is not None
    assert len(crystal.merkle_root) == 64
    # Verificar que el claim refutado quedó en las falsaciones
    falsified_claims = [f.claim for f in crystal.falsification_verdicts if f.falsified]
    assert "La tasa de paquetes perdidos es estrictamente cero" in falsified_claims
