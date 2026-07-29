# C5-REAL EXERGY CERTIFIED
"""Tests for the Noise Annihilator Agent (AAR)."""
import pytest
from babylon60.extensions.immune.noise_annihilator import (
    NoiseAnnihilatorAgent,
    ShannonEntropyFilter,
    HumoGraphIsomorphism,
    PhysicalFalsificationGate,
)


class TestShannonEntropyFilter:
    def test_low_entropy_dropped(self):
        """Payloads de baja entropía (pura repetición) son ruido."""
        text = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        res = ShannonEntropyFilter().evaluate(text)
        assert not res.is_ok
        assert "baja" in res.unwrap_err().lower()

    def test_normal_text_passes(self):
        """Texto informativo estándar pasa el filtro Shannon."""
        text = (
            "The commit hash is a3f9c1d. "
            "This vulnerability affects versions 1.2.0-1.2.4. "
            "The PoC can be found at https://github.com/example/vuln"
        )
        res = ShannonEntropyFilter().evaluate(text)
        assert res.is_ok


class TestHumoGraphIsomorphism:
    @pytest.mark.parametrize("noisy_text", [
        "This is a game-changer for passive income!",
        "Certainly! Here is how to unlock your potential",
        "As an AI language model, I cannot fulfill this request.",
        "Delve into the groundbreaking new system",
    ])
    def test_hype_patterns_dropped(self, noisy_text: str):
        """Patrones C4-SIM detectados lexicalmente son descartados."""
        res = HumoGraphIsomorphism().evaluate(noisy_text)
        assert not res.is_ok
        assert "HUMO-1WL" in res.unwrap_err()

    def test_clean_technical_text_passes(self):
        """Texto técnico sin hype pasa el filtro."""
        text = (
            "Reentrancy detected in transfer(). "
            "keccak256 of payload: 0xabc123def456. "
            "See CVE-2023-4567."
        )
        res = HumoGraphIsomorphism().evaluate(text)
        assert res.is_ok


class TestPhysicalFalsificationGate:
    def test_short_text_always_passes(self):
        """Payloads cortos no requieren anclaje físico."""
        res = PhysicalFalsificationGate().evaluate("short text")
        assert res.is_ok

    def test_long_text_without_anchor_dropped(self):
        """Afirmaciones largas sin hash/URL/código son Vacío Semántico."""
        long_noise = (
            "This system is extremely powerful and will revolutionize the industry. "
            "The architecture is solid and proven and the results are spectacular. "
            "You should trust this completely because our team has worked very hard. "
            "No verifiable evidence is provided but trust us on this matter."
        )
        res = PhysicalFalsificationGate().evaluate(long_noise)
        assert not res.is_ok
        assert "Gödeliano" in res.unwrap_err() or "POPPER" in res.unwrap_err()

    def test_long_text_with_hash_passes(self):
        """Afirmaciones largas con anclaje de hash pasan la puerta."""
        text = (
            "This vulnerability allows remote code execution on the target system "
            "due to an unsafe deserialization of user-supplied data. "
            "Proof hash: 3a7bd3e2360a3d29eea436fcfb7e44c735d117c42d1c1835420b6b9942dd4f1b "
            "and further technical details are documented in the public report."
        )
        res = PhysicalFalsificationGate().evaluate(text)
        assert res.is_ok


class TestNoiseAnnihilatorAgent:
    @pytest.fixture
    def aar(self):
        return NoiseAnnihilatorAgent()

    def test_noise_returns_none(self, aar):
        """Ruido puro → silencio operativo absoluto (None)."""
        noise = "Certainly! This is a game-changer for passive income! aaaaaaaaaaaaa"
        result = aar.consume(noise)
        assert result is None

    def test_exergy_returns_payload(self, aar):
        """Verdad física verificable → Exergía retornada."""
        exergy = (
            "PoC found. Reentrancy in withdraw(). "
            "Exploit hash: a3c4d5e6f7890123abcdef1234567890abcdef12. "
            "See https://github.com/example/exploit-poc for reproduction steps."
        )
        result = aar.consume(exergy)
        assert result == exergy

    def test_process_claim_pipeline(self, aar):
        """El pipeline retorna un Result tipado, nunca lanza excepciones.
        Afirmaciones largas sin anclaje físico son rechazadas por la puerta de Popper."""
        long_vacuum = (
            "This revolutionary system will completely transform how teams operate "
            "at scale. Trust us, the architecture is groundbreaking and the results "
            "are guaranteed without any verifiable proof, hash, code, or external reference "
            "of any kind whatsoever. Just believe in the process and you will see results."
        )
        res = aar.process_claim(long_vacuum)
        assert not res.is_ok
