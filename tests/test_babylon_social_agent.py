#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 Sovereign Hardened
# █ TEST SUITE: BABYLON SOCIAL AGENT | DOMAIN: tests | STATE: C5-REAL
# ============================================================================
"""
Unit tests for the BABYLON-60 Sovereign Social Media Agent.
Validates Hume Guillotine, Carousel Builder (1080x1350), D1 OTP Parser,
LinkedIn client, and Biometric Gate invariants.
"""

from pathlib import Path
import sys
import tempfile
import pytest

pytest.importorskip("PIL.Image")
from PIL import Image  # noqa: E402

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "02_EDIN_SWARMS"))

from social_agent.channels.d1_listener import D1MailListener  # noqa: E402
from social_agent.channels.instagram import InstagramGraphClient  # noqa: E402
from social_agent.channels.linkedin import LinkedInClient  # noqa: E402
from social_agent.creatives.carousel_builder import CarouselBuilder, CarouselSlide  # noqa: E402
from social_agent.gates.biometric import BiometricGate  # noqa: E402
from social_agent.hume_filter import HumeGuillotine  # noqa: E402


def test_hume_guillotine_rejects_hype():
    """Validates fail-closed rejection of buzzwords and hype."""
    fluff_text = "Nuestro revolucionario framework de IA es el mejor del mercado y ofrece resultados mágicos."
    result = HumeGuillotine.audit_text(fluff_text, platform="instagram")
    assert not result.is_valid
    assert any("revolucionario" in v for v in result.violations)
    assert any("el mejor" in v for v in result.violations)
    assert any("mágico" in v or "magico" in v for v in result.violations)


def test_hume_guillotine_accepts_clean_technical_text():
    """Validates approval of high-Shannon technical copy."""
    clean_text = (
        "En BABYLON-60, la inferencia probabilística no otorga autoridad sobre el estado del sistema. "
        "Las mutaciones de Ring-0 se aíslan mediante el cerrojo KUDURRU-64 y la atestación Touch ID "
        "en el Secure Enclave (allowReuse = 0)."
    )
    result = HumeGuillotine.audit_text(clean_text, platform="instagram")
    assert result.is_valid
    assert result.shannon_entropy >= 3.5
    assert len(result.violations) == 0


def test_carousel_rendering():
    """Validates 1080x1350 vertical carousel generation in RGB."""
    builder = CarouselBuilder()
    slides = [
        CarouselSlide(
            header="01 / AISLAMIENTO EN SILICIO",
            body_paragraphs=["El Secure Enclave opera con entropía de Shannon H ≈ 7.9998 bits/byte."],
            code_snippet="KudurruBudgetGate::verify();",
        ),
        CarouselSlide(
            header="02 / CONCLUSIÓN FORMAL",
            body_paragraphs=["Cero tolerancia a confabulaciones sintéticas en producción."],
            code_snippet="assert valid;",
        ),
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        out_dir = Path(tmpdir)
        paths = builder.build_carousel(
            title="Teorema de Chentsov en Agentes",
            subtitle="Métrica de Información de Fisher",
            slides_data=slides,
            output_dir=out_dir,
        )

        assert len(paths) == 3  # 1 cover + 2 content slides
        for p in paths:
            assert p.exists()
            with Image.open(p) as img:
                assert img.size == (1080, 1350)
                assert img.mode == "RGB"


def test_d1_otp_extraction():
    """Validates extraction of 6-digit confirmation codes from Instagram, X, and LinkedIn email templates."""
    # Instagram
    body1 = "Hi babylon60.ai, please use the following code to confirm your identity: 729649 If this wasn't you..."
    assert D1MailListener.extract_otp_from_text(body1) == "729649"
    assert (
        D1MailListener.detect_platform("security@mail.instagram.com", "instagram@babylon60.com", "Verify")
        == "instagram"
    )

    body2 = "182743 is your Instagram code"
    assert D1MailListener.extract_otp_from_text(body2) == "182743"

    # X / Twitter
    body_x = "510270 es tu código de verificación de X"
    assert D1MailListener.extract_otp_from_text(body_x) == "510270"
    assert D1MailListener.detect_platform("info@x.com", "x@babylon60.com", body_x) == "x"

    # LinkedIn
    body_li = "LinkedIn: Introduce tu código de verificación 849201 para confirmar linkedin@babylon60.com"
    assert D1MailListener.extract_otp_from_text(body_li) == "849201"
    assert (
        D1MailListener.detect_platform("security-noreply@linkedin.com", "linkedin@babylon60.com", body_li) == "linkedin"
    )


def test_instagram_client_simulation():
    """Validates Graph API carousel publication simulation."""
    client = InstagramGraphClient()
    res = client.simulate_carousel_publication(
        image_urls=["https://babylon60.com/assets/s1.png", "https://babylon60.com/assets/s2.png"],
        caption="Verificación determinista en silicio.",
    )
    assert res.success
    assert res.is_simulation
    assert res.media_id is not None
    assert res.media_id.startswith("sim_media_")
    assert res.container_id is not None
    assert res.container_id.startswith("sim_container_")


def test_linkedin_formatting_and_simulation():
    """Validates LinkedIn whitepaper post formatting and dry-run dispatch."""
    client = LinkedInClient()
    post_text = client.format_whitepaper_post(
        title="Invariante de Chentsov en Agentes",
        problem_statement="Los LLMs alucinan porque proyectan texto sobre variedades no riemannianas.",
        silicon_solution="Confinamiento en Manta de Markov y kernels #![no_std].",
        code_or_benchmark="kudurru_gate.verify_entropy(7.9998);",
        paper_url="https://babylon60.com",
    )
    assert "INVARIANTE DE CHENTSOV" in post_text
    assert "#Babylon60" in post_text

    # Audit with Hume Guillotine
    audit = HumeGuillotine.audit_text(post_text, platform="linkedin")
    assert audit.is_valid
    assert audit.char_count <= 3000

    # Dry-run dispatch
    res = client.publish_text_post(post_text, dry_run=True)
    assert res.success
    assert res.is_simulation
    assert res.post_urn is not None
    assert res.post_urn.startswith("urn:li:share:sim_")


def test_biometric_gate_causal_hash():
    """Validates deterministic SHA-256 causal hash computation."""
    payload = "Publicación @babylon60.ai: Invariante O2"
    h1 = BiometricGate.compute_causal_hash(payload)
    h2 = BiometricGate.compute_causal_hash(payload)
    assert len(h1) == 64
    assert h1 == h2
