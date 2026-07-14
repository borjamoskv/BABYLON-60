"""Progressive Multiple Sequence Alignment (Needleman-Wunsch profile)."""

from __future__ import annotations

import numpy as np

from cortex.agents.phylo.phonetics import phonetic_distance

GAP = "-"
GAP_PEN = -1.0


def _sub_score(a: str, b: str) -> float:
    if a == GAP or b == GAP:
        return GAP_PEN
    return 2.0 - phonetic_distance(a, b)


def _col_score(column: list[str], seg: str) -> float:
    return sum(_sub_score(x, seg) if x != GAP else GAP_PEN for x in column) / len(column)


def align_seq_to_msa(msa_rows: list[list[str]], seq: list[str]) -> list[list[str]]:
    """Align a single sequence against an existing MSA via profile NW."""
    width = len(msa_rows[0]) if msa_rows else 0
    n = len(seq)
    cols = [[row[c] for row in msa_rows] for c in range(width)]
    neg = -1e9

    dp = np.full((width + 1, n + 1), neg)
    bt = np.zeros((width + 1, n + 1), dtype=np.int8)
    dp[0, 0] = 0.0
    for i in range(1, width + 1):
        dp[i, 0] = dp[i - 1, 0] + GAP_PEN
        bt[i, 0] = 1
    for j in range(1, n + 1):
        dp[0, j] = dp[0, j - 1] + GAP_PEN
        bt[0, j] = 2

    for i in range(1, width + 1):
        for j in range(1, n + 1):
            diag = dp[i - 1, j - 1] + _col_score(cols[i - 1], seq[j - 1])
            up = dp[i - 1, j] + GAP_PEN
            left = dp[i, j - 1] + GAP_PEN
            best = max(diag, up, left)
            dp[i, j] = best
            bt[i, j] = 0 if best == diag else (1 if best == up else 2)

    # traceback
    i, j = width, n
    new_cols: list[tuple[list[str] | None, str]] = []
    while i > 0 or j > 0:
        b = bt[i, j]
        if i > 0 and j > 0 and b == 0:
            new_cols.append((cols[i - 1], seq[j - 1]))
            i -= 1; j -= 1
        elif i > 0 and (j == 0 or b == 1):
            new_cols.append((cols[i - 1], GAP))
            i -= 1
        else:
            new_cols.append((None, seq[j - 1]))
            j -= 1
    new_cols.reverse()

    num_rows = len(msa_rows)
    out: list[list[str]] = [[] for _ in range(num_rows + 1)]
    for col, seg in new_cols:
        if col is None:
            for r in range(num_rows):
                out[r].append(GAP)
            out[num_rows].append(seg)
        else:
            for r in range(num_rows):
                out[r].append(col[r])
            out[num_rows].append(seg)
    return out


def build_msa(forms: list[tuple[str, list[str]]]) -> tuple[list[str], list[list[str]]]:
    """Progressive MSA ordered by descending sequence length."""
    order = sorted(range(len(forms)), key=lambda k: -len(forms[k][1]))
    langs = [forms[order[0]][0]]
    msa = [list(forms[order[0]][1])]
    for k in order[1:]:
        lang, seq = forms[k]
        msa = align_seq_to_msa(msa, list(seq))
        langs.append(lang)
    return langs, msa
