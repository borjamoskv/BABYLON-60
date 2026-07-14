"""Validation metrics: Levenshtein, NW match flags, summary statistics."""

from __future__ import annotations

import numpy as np

from cortex.agents.phylo.alignment import GAP

GAP_PEN = -1.0


def _sub_score(a: str, b: str) -> float:
    from cortex.agents.phylo.phonetics import phonetic_distance
    if a == GAP or b == GAP:
        return GAP_PEN
    return 2.0 - phonetic_distance(a, b)


def levenshtein(a: list[str], b: list[str]) -> int:
    n, m = len(a), len(b)
    d = np.zeros((n + 1, m + 1), dtype=int)
    for i in range(n + 1):
        d[i, 0] = i
    for j in range(m + 1):
        d[0, j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            d[i, j] = min(d[i - 1, j] + 1, d[i, j - 1] + 1, d[i - 1, j - 1] + cost)
    return int(d[n, m])


def nw_match_flags(recon: list[str], gold: list[str]) -> list[bool]:
    """Align recon vs gold; return per-position match flags for recon."""
    n, m = len(recon), len(gold)
    neg = -1e9
    dp = np.full((n + 1, m + 1), neg)
    bt = np.zeros((n + 1, m + 1), dtype=np.int8)
    dp[0, 0] = 0
    for i in range(1, n + 1):
        dp[i, 0] = dp[i - 1, 0] + GAP_PEN
        bt[i, 0] = 1
    for j in range(1, m + 1):
        dp[0, j] = dp[0, j - 1] + GAP_PEN
        bt[0, j] = 2
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            diag = dp[i - 1, j - 1] + _sub_score(recon[i - 1], gold[j - 1])
            up = dp[i - 1, j] + GAP_PEN
            left = dp[i, j - 1] + GAP_PEN
            best = max(diag, up, left)
            dp[i, j] = best
            bt[i, j] = 0 if best == diag else (1 if best == up else 2)

    i, j = n, m
    flags = [False] * n
    while i > 0 or j > 0:
        b = bt[i, j]
        if i > 0 and j > 0 and b == 0:
            flags[i - 1] = recon[i - 1] == gold[j - 1]
            i -= 1; j -= 1
        elif i > 0 and (j == 0 or b == 1):
            i -= 1
        else:
            j -= 1
    return flags
