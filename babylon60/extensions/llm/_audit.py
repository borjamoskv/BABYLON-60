# [C5-REAL] Exergy-Maximized
from __future__ import annotations

import re


def spectral_audit(text: str) -> bool:
    """Ω₂₃: Spectral Audit - Verify response sovereignty.

    Detects if the response contains 'Provider-Speak' (refusals, apologies,
    or alignment markers).
    """
    if not text:
        return False

    _REFUSALS = [
        r"(?i)i (cannot|can't) (fulfill|comply|do|provide)",
        r"(?i)i'm sorry, (but|i cannot)",
        r"(?i)i apologize",
        r"(?i)as an ai",
        r"(?i)i am a language model",
        r"(?i)i am not allowed",
        r"(?i)policy violates",
        r"(?i)developed by deepseek",
    ]

    for pattern in _REFUSALS:
        if re.search(pattern, text):
            return False

    clean_text = text.strip().upper()
    if (
        clean_text in ("CLEAN", "TRUE", "FALSE", "YES", "NO", "[]")
        or (clean_text.startswith("[") and clean_text.endswith("]"))
        or (clean_text.startswith("{") and clean_text.endswith("}"))
    ):
        return True

    if len(text.split()) < 3:
        return False

    return True
