# [C5-REAL] Exergy-Maximized
"""Security utilities for CORTEX."""

import math


def calculate_shannon_entropy(content: str) -> float:
    """Calculate Shannon entropy of content (character-level).

    High entropy (>4.5) suggests encoded/encrypted payloads.
    """
    if not content:
        return 0.0
    freq: dict[str, int] = {}
    for ch in content:
        freq[ch] = freq.get(ch, 0) + 1
    length = len(content)
    return -sum((c / length) * math.log2(c / length) for c in freq.values() if c > 0)


def calculate_lexical_entropy(content: str) -> float:
    """Calculate Shannon entropy of words in content (word-level)."""
    import re

    if not content:
        return 0.0
    words = re.findall(r"\w+", content.lower())
    if not words:
        return 0.0
    freq: dict[str, int] = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    total = len(words)
    return -sum((c / total) * math.log2(c / total) for c in freq.values() if c > 0)


def calculate_distribution_entropy(counts: dict, total: int = 0) -> float:
    """Calculate Shannon entropy of a generic distribution/histogram."""
    if not counts:
        return 0.0
    if total <= 0:
        total = sum(counts.values())
    if total <= 0:
        return 0.0
    return -sum((c / total) * math.log2(c / total) for c in counts.values() if c > 0)


def calculate_entropy_from_probabilities(probs: list[float]) -> float:
    """Calculate Shannon entropy directly from a list of probabilities."""
    return -sum(p * math.log2(p) for p in probs if p > 0)
