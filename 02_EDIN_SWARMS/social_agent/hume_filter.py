#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 Sovereign Hardened
# █ HUME GUILLOTINE LINTER (LAHAMU-60) | DOMAIN: social.gates | STATE: C5-REAL
# ============================================================================
"""
Hume Guillotine & Shannon Density Linter.
Audits social media copy before any external dispatch.
Enforces fail-closed rejection of marketing fluff, hype adjectives, and ungrounded claims.
"""

from dataclasses import dataclass
import math
import re
from typing import Dict, List, Optional, Set, Tuple


PROHIBITED_HYPE_ROOTS: List[str] = [
    r"revolucionari[oa]s?",
    r"incre[ií]bles?",
    r"el mejor",
    r"la mejor",
    r"los mejores",
    r"las mejores",
    r"disruptiv[oa]s?",
    r"game[- ]?changers?",
    r"m[aá]gic[oa]s?",
    r"secret[oa]s?",
    r"infalibles?",
    r"hype",
    r"viral(?:es)?",
    r"definitiv[oa]s?",
    r"nunca antes vist[oa]s?",
    r"10x developer",
    r"ninja developer",
    r"gur[uú]s?",
    r"f[aá]cil dinero",
    r"sin esfuerzo",
]


@dataclass(frozen=True)
class HumeAuditResult:
    """Rigid verification result from Hume Guillotine."""

    is_valid: bool
    shannon_entropy: float
    violations: List[str]
    char_count: int
    word_count: int


class HumeGuillotine:
    """
    Enforces epistemic rigor on social copy:
    1. Veto to emotional manipulation and hype adjectives (Popperian verification).
    2. Minimum Shannon information entropy constraint (H >= 3.5 bits/char).
    3. Platform character length constraints.
    """

    MIN_SHANNON_ENTROPY: float = 3.5
    MAX_INSTAGRAM_CAPTION_LEN: int = 2200
    MAX_X_TWEET_LEN: int = 280
    MAX_LINKEDIN_POST_LEN: int = 3000

    @classmethod
    def compute_shannon_entropy(cls, text: str) -> float:
        """Computes the Shannon information entropy of the text in bits/char."""
        if not text:
            return 0.0
        length = len(text)
        freqs: Dict[str, int] = {}
        for char in text:
            freqs[char] = freqs.get(char, 0) + 1

        entropy = 0.0
        for count in freqs.values():
            p = count / length
            entropy -= p * math.log2(p)
        return round(entropy, 3)

    @classmethod
    def audit_text(
        cls,
        text: str,
        platform: str = "instagram",
        require_min_entropy: bool = True,
    ) -> HumeAuditResult:
        """
        Audits text against Hume Guillotine invariants.
        Returns HumeAuditResult with pass/fail and detailed violations.
        """
        violations: List[str] = []
        text_lower = text.lower()

        # 1. Prohibited words check
        for root_pattern in PROHIBITED_HYPE_ROOTS:
            pattern = rf"\b{root_pattern}\b"
            match = re.search(pattern, text_lower)
            if match:
                violations.append(f"Término proscrito detectado: '{match.group(0)}' (viola invariante anti-hype).")

        # 2. Length check by platform
        char_count = len(text)
        word_count = len(text.split())

        platform_clean = platform.lower()
        if platform_clean == "instagram" and char_count > cls.MAX_INSTAGRAM_CAPTION_LEN:
            violations.append(
                f"Longitud de caption en Instagram ({char_count}) supera el límite de {cls.MAX_INSTAGRAM_CAPTION_LEN}."
            )
        elif platform_clean in ("x", "twitter") and char_count > cls.MAX_X_TWEET_LEN:
            violations.append(
                f"Longitud de tweet en X ({char_count}) supera el límite de {cls.MAX_X_TWEET_LEN}."
            )
        elif platform_clean == "linkedin" and char_count > cls.MAX_LINKEDIN_POST_LEN:
            violations.append(
                f"Longitud de post en LinkedIn ({char_count}) supera el límite de {cls.MAX_LINKEDIN_POST_LEN}."
            )

        # 3. Information entropy check
        entropy = cls.compute_shannon_entropy(text)
        if require_min_entropy and char_count > 40 and entropy < cls.MIN_SHANNON_ENTROPY:
            violations.append(
                f"Densidad de Shannon insuficiente ({entropy} < {cls.MIN_SHANNON_ENTROPY} bits/char). Texto repetitivo o de baja información."
            )

        return HumeAuditResult(
            is_valid=len(violations) == 0,
            shannon_entropy=entropy,
            violations=violations,
            char_count=char_count,
            word_count=word_count,
        )
