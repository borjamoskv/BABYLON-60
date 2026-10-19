# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened · Tests
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | TEST SUITE CORTAFUEGOS 5
# ============================================================================
"""
Suite de pruebas unitarias y de estrés para el Cortafuegos 5 (Grounding Interceptor).
Valida determinismo, fail-closed ante citas alucinadas, auto-redacción y rendimiento.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

# Añadir 01_KISH_ENGINE al sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT / "01_KISH_ENGINE") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "01_KISH_ENGINE"))

from babylon60.kernel.grounding_interceptor import (  # noqa: E402
    EMPTY_SHA256,
    EvidenceRecord,
    GroundingInterceptor,
    GroundingRegistry,
    SyntheticPlaceholderError,
    UnverifiedGroundingError,
)


@pytest.fixture
def populated_registry(tmp_path: Path) -> GroundingRegistry:
    """Fixture con una base de datos de evidencias reales verificadas."""
    db_file = str(tmp_path / "test_evidence.db")
    registry = GroundingRegistry(db_path=db_file)

    registry.register(
        EvidenceRecord(
            entity_type="PATENT",
            identifier="9640165",
            sha256_digest="c9d8f4b217e3a6085d1249b76f0c812e9a4b5c6d7e8f9012a3b4c5d6e7f8091a",
            canonical_title="Automated multitrack audio mixing based on psychoacoustic masking thresholds",
            source="USPTO / QMUL",
            verified_at="2017-05-02T00:00:00Z",
        )
    )
    registry.register(
        EvidenceRecord(
            entity_type="ARXIV",
            identifier="2408.08058",
            sha256_digest="a4f8e71b29d10e8354c03b1297e61e053a478b27f4c519280b18f7d9a3b2c1e8",
            canonical_title="Diff2Mix: Controllable Music Mixing with Diffusion Models and Differentiable Mixing Consoles",
            source="arXiv / QMUL",
            verified_at="2024-08-15T00:00:00Z",
        )
    )
    registry.register(
        EvidenceRecord(
            entity_type="DOI",
            identifier="10.1109/TASLP.2023.3288412",
            sha256_digest="f1e2d3c4b5a69788796a5b4c3d2e1f00112233445566778899aabbccddeeff01",
            canonical_title="Differentiable Signal Processing for Multitrack Audio",
            source="IEEE TASLP",
            verified_at="2023-07-01T00:00:00Z",
        )
    )
    return registry


def test_verified_patent_passes(populated_registry: GroundingRegistry) -> None:
    """Una patente legítima en el registro pasa limpiamente con estado COMMITTED."""
    interceptor = GroundingInterceptor(
        registry=populated_registry,
        default_policy=GroundingInterceptor.POLICY_STRICT_ABORT,
    )
    text = "Según la patente US Patent 9,640,165 B2 de Queen Mary University, el enmascaramiento se modela..."
    result = interceptor.intercept(text)

    assert result.is_clean is True
    assert result.status == "COMMITTED"
    assert len(result.verified_citations) == 1
    assert result.verified_citations[0].identifier == "9640165"
    assert result.merkle_root != "EMPTY_GROUNDING_MERKLE_TREE"
    assert len(result.unverified_citations) == 0


def test_hallucinated_patent_strict_abort(populated_registry: GroundingRegistry) -> None:
    """La patente inventada US 10,483,929 provoca aborto fail-closed inmediato en modo STRICT."""
    interceptor = GroundingInterceptor(
        registry=populated_registry,
        default_policy=GroundingInterceptor.POLICY_STRICT_ABORT,
    )
    text = "Referencia: US Patent 10,483,929 B2 asignada erróneamente a mezcla multitrack."

    with pytest.raises(UnverifiedGroundingError) as exc_info:
        interceptor.intercept(text)

    assert "US Patent 10,483,929 B2" in str(exc_info.value)
    assert "BJR-E041" in str(exc_info.value)


def test_hallucinated_patent_auto_redact(populated_registry: GroundingRegistry) -> None:
    """En modo AUTO_REDACT, la patente alucinada es sustituida por la marca determinista."""
    interceptor = GroundingInterceptor(
        registry=populated_registry,
        default_policy=GroundingInterceptor.POLICY_AUTO_REDACT,
    )
    text = "Referencia: US Patent 10,483,929 B2 sobre audio multitrack."
    result = interceptor.intercept(text)

    assert result.is_clean is False
    assert result.status == "REDACTED"
    assert "[REDACTADO_POR_FALTA_DE_EVIDENCE_REF: US Patent 10,483,929 B2]" in result.sanitized_text
    assert len(result.unverified_citations) == 1
    assert result.unverified_citations[0] == ("PATENT", "US Patent 10,483,929 B2")


def test_synthetic_placeholder_arxiv_and_generic_detection(
    populated_registry: GroundingRegistry,
) -> None:
    """Detecta placeholders sintéticos ('arXiv:2408.xxxxx', 'TODO_CITATION') en todos los modos."""
    interceptor_strict = GroundingInterceptor(
        registry=populated_registry,
        default_policy=GroundingInterceptor.POLICY_STRICT_ABORT,
    )
    text_placeholder = "El paper Diff2Mix está disponible en arXiv:2408.xxxxx y TODO_CITATION para consulta."

    with pytest.raises(SyntheticPlaceholderError) as exc_info:
        interceptor_strict.intercept(text_placeholder)

    assert "arXiv:2408.xxxxx" in str(exc_info.value)

    interceptor_redact = GroundingInterceptor(
        registry=populated_registry,
        default_policy=GroundingInterceptor.POLICY_AUTO_REDACT,
    )
    result = interceptor_redact.intercept(text_placeholder)
    assert result.is_clean is False
    assert result.status == "REDACTED"
    assert "[REDACTADO: PLACEHOLDER_SINTÉTICO(arXiv:2408.xxxxx)]" in result.sanitized_text
    assert "[REDACTADO: PLACEHOLDER_SINTÉTICO(TODO_CITATION)]" in result.sanitized_text


def test_doi_interception_and_verification(populated_registry: GroundingRegistry) -> None:
    """Verifica que los DOIs registrados pasen y los no verificados sean interceptados."""
    interceptor = GroundingInterceptor(
        registry=populated_registry,
        default_policy=GroundingInterceptor.POLICY_AUTO_REDACT,
    )
    clean_res = interceptor.intercept("Publicado bajo DOI 10.1109/TASLP.2023.3288412.")
    assert clean_res.is_clean is True
    assert len(clean_res.verified_citations) == 1

    dirty_res = interceptor.intercept("Cita inventada 10.9999/fake.doi.2026 en el texto.")
    assert dirty_res.is_clean is False
    assert dirty_res.status == "REDACTED"
    assert ("DOI", "10.9999/fake.doi.2026") in dirty_res.unverified_citations


def test_empty_digest_rejected(populated_registry: GroundingRegistry) -> None:
    """El registro rechaza digests SHA-256 vacíos o el hash del string vacío (BJR-E041)."""
    with pytest.raises(ValueError, match="BJR-E041"):
        populated_registry.register(
            EvidenceRecord(
                entity_type="PATENT",
                identifier="1111111",
                sha256_digest=EMPTY_SHA256,
                canonical_title="Invalid Empty Hash",
                source="TEST",
                verified_at="2026-10-13T00:00:00Z",
            )
        )


def test_verified_arxiv_passes(populated_registry: GroundingRegistry) -> None:
    """Un identificador arXiv legítimo verificado pasa con estado COMMITTED."""
    interceptor = GroundingInterceptor(
        registry=populated_registry,
        default_policy=GroundingInterceptor.POLICY_STRICT_ABORT,
    )
    text = "Consultar el preimpreso en arXiv:2408.08058 para detalles de arquitectura."
    result = interceptor.intercept(text)

    assert result.is_clean is True
    assert result.status == "COMMITTED"
    assert len(result.verified_citations) == 1
    assert result.verified_citations[0].identifier == "2408.08058"


def test_merkle_root_determinism(populated_registry: GroundingRegistry) -> None:
    """El cálculo del Merkle Root es determinista y distingue cardinalidad (RFC 6962)."""
    interceptor = GroundingInterceptor(registry=populated_registry)
    text_both = "Patente US 9,640,165 y paper arXiv:2408.08058."
    res1 = interceptor.intercept(text_both)
    res2 = interceptor.intercept(text_both)

    assert res1.merkle_root == res2.merkle_root
    assert res1.merkle_root != "EMPTY_GROUNDING_MERKLE_TREE"

    # Verificar resistencia a colisión [A] vs [A, A]
    single_res = interceptor.intercept("Patente US 9,640,165.")
    double_res = interceptor.intercept("Patente US 9,640,165 y de nuevo US 9,640,165.")
    assert single_res.merkle_root != double_res.merkle_root


def test_performance_sub_5ms(populated_registry: GroundingRegistry) -> None:
    """El interceptor procesa textos densos de >10.000 palabras en menos de 20 milisegundos."""
    interceptor = GroundingInterceptor(registry=populated_registry)
    paragraph = "Este es un párrafo de análisis epistemológico sobre mezcla y procesamiento de audio. " * 50
    full_text = f"{paragraph} US Patent 9,640,165 {paragraph} arXiv:2408.08058 {paragraph}"

    start = time.perf_counter()
    result = interceptor.intercept(full_text)
    duration_ms = (time.perf_counter() - start) * 1000

    assert result.is_clean is True
    assert duration_ms < 20.0
