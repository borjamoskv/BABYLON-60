"""Phonetic feature vectors and distance kernel."""

from __future__ import annotations

import math

# Consonante: ('C', place, manner, voice) ; Vocal: ('V', height, back, round)
FEATURES: dict[str, tuple[str, int, int, int]] = {
    "p": ("C", 0, 0, 0), "b": ("C", 0, 0, 1),
    "f": ("C", 0, 1, 0), "v": ("C", 0, 1, 1),
    "m": ("C", 0, 3, 1), "w": ("C", 0, 6, 1),
    "t": ("C", 1, 0, 0), "d": ("C", 1, 0, 1),
    "s": ("C", 1, 1, 0), "z": ("C", 1, 1, 1),
    "n": ("C", 1, 3, 1), "l": ("C", 1, 4, 1),
    "r": ("C", 1, 5, 1),
    "S": ("C", 2, 1, 0), "Z": ("C", 2, 1, 1),
    "C": ("C", 2, 2, 0), "G": ("C", 2, 2, 1),
    "J": ("C", 3, 3, 1), "L": ("C", 3, 4, 1),
    "j": ("C", 3, 6, 1),
    "k": ("C", 4, 0, 0), "g": ("C", 4, 0, 1),
    "h": ("C", 5, 1, 0),
    "a": ("V", 2, 1, 0), "e": ("V", 1, 0, 0),
    "i": ("V", 0, 0, 0), "o": ("V", 1, 2, 1),
    "u": ("V", 0, 2, 1), "y": ("V", 0, 0, 1),
}


def phonetic_distance(a: str, b: str) -> float:
    """Distancia fonética ~[0, 3] entre dos segmentos (no gaps)."""
    if a == b:
        return 0.0
    fa, fb = FEATURES[a], FEATURES[b]
    if fa[0] != fb[0]:
        return 3.0
    if fa[0] == "C":
        return (
            min(abs(fa[1] - fb[1]), 3) / 3.0
            + 1.5 * (0 if fa[2] == fb[2] else 1)
            + 0.5 * abs(fa[3] - fb[3])
        )
    return (
        abs(fa[1] - fb[1]) / 2.0
        + abs(fa[2] - fb[2]) / 2.0
        + 0.5 * abs(fa[3] - fb[3])
    )


def exchangeability(a: str, b: str, lam: float = 1.4) -> float:
    """Markov exchangeability kernel: exp(-λ · d(a,b))."""
    return math.exp(-lam * phonetic_distance(a, b))
