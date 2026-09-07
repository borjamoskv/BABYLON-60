# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
from babylon60.transducers.linguistic_entropy import (
    LinguisticEntropyDetector,
    LinguisticEntropyReport,
)


def test_linguistic_entropy_detector_short_text():
    detector = LinguisticEntropyDetector()
    text = "BABYLON-60 kernel operates deterministically in Ring-0 memory space."
    report = detector.analyze(text)
    assert isinstance(report, LinguisticEntropyReport)
    assert report.word_count > 0
    assert report.context_rot_score == 0.0
    assert report.exergy_score > 0.0


def test_linguistic_entropy_detector_long_text_context_rot():
    detector = LinguisticEntropyDetector()
    # Generar texto largo (> 300 palabras) para activar _context_rot
    base_paragraph = (
        "Thermodynamic exergy governs information preservation across Markov blankets. "
        "Fisher information metric defines geodesic trajectories in statistical manifolds. "
        "Deterministic finite state transducers ensure verifiable consensus without slop. "
    )
    long_text = base_paragraph * 20
    report = detector.analyze(long_text)
    assert isinstance(report, LinguisticEntropyReport)
    assert report.word_count >= 200
    assert 0.0 <= report.context_rot_score <= 1.0
    assert report.exergy_score <= 100.0


def test_context_rot_static_call():
    detector = LinguisticEntropyDetector()
    text = "sample word " * 250
    rot = detector._context_rot(text, window_size=50)
    assert 0.0 <= rot <= 1.0
