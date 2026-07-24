import math
from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy.linalg import expm

GOLD: dict[str, str] = {
    "key": "k l a v e",
    "night": "n o k t e",
    "eight": "o k t o",
    "milk": "l a k t e",
    "to_do": "f a k e r e",
    "fire": "f o k u",
    "hundred": "k e n t u",
    "moon": "l u n a",
    "sea": "m a r e",
    "flower": "f l o r e",
    "to_sing": "k a n t a r e",
    "dog": "k a n e",
    "to_have": "h a b e r e",
    "water": "a k w a",
    "to_die": "m o r i r e",
    "name": "n o m e n",
    "new": "n o v u",
    "to_love": "a m a r e",
}
DATA: dict[str, dict[str, str]] = {
    "key": {"es": "L a v e", "pt": "S a v e", "fr": "k l e", "it": "k j a v e", "ro": "k e j e", "sc": "k r a e"},
    "night": {"es": "n o C e", "pt": "n o j t e", "fr": "n w i", "it": "n o t e", "ro": "n o a p t e", "sc": "n o t e"},
    "eight": {"es": "o C o", "pt": "o j t o", "fr": "w i t", "it": "o t o", "ro": "o p t", "sc": "o t o"},
    "milk": {"es": "l e C e", "pt": "l e j t e", "fr": "l e", "it": "l a t e", "ro": "l a p t e", "sc": "l a t e"},
    "to_do": {"es": "a s e r", "pt": "f a z e r", "fr": "f e r", "it": "f a r e", "ro": "f a C e"},
    "fire": {"es": "f w e g o", "pt": "f o g o", "it": "f w o k o", "ro": "f o k", "sc": "f o g u"},
    "hundred": {"es": "s j e n", "fr": "s a n", "it": "C e n t o", "ro": "s u t e"},
    "moon": {"es": "l u n a", "pt": "l u a", "fr": "l y n", "it": "l u n a", "ro": "l u n a", "sc": "l u n a"},
    "sea": {"es": "m a r", "pt": "m a r", "fr": "m e r", "it": "m a r e", "ro": "m a r e", "sc": "m a r e"},
    "flower": {"es": "f l o r", "pt": "f l o r", "it": "f j o r e", "ro": "f l o a r e"},
    "to_sing": {"es": "k a n t a r", "pt": "k a n t a r", "fr": "S a n t e", "it": "k a n t a r e", "ro": "k a n t a"},
    "dog": {
        "es": "k a n",
        "fr": "S j e e n" if False else "S j e n",
        "it": "k a n e",
        "ro": "k a i n e",
        "sc": "k a n e",
    },
    "to_have": {"es": "a b e r", "pt": "a v e r", "fr": "a v w a r", "it": "a v e r e", "ro": "a v e a"},
    "water": {"es": "a g w a", "pt": "a g w a", "it": "a k w a", "ro": "a p e", "sc": "a b a"},
    "to_die": {"es": "m o r i r", "pt": "m o r e r", "fr": "m u r i r", "it": "m o r i r e", "ro": "m u r i"},
    "name": {"es": "n o m b r e", "pt": "n o m e", "fr": "n o n", "it": "n o m e", "ro": "n u m e"},
    "new": {"es": "n w e v o", "pt": "n o v o", "it": "n w o v o", "ro": "n o u", "sc": "n o b u"},
    "to_love": {"es": "a m a r", "pt": "a m a r", "fr": "e m e", "it": "a m a r e", "ro": "a m a"},
}
GAP: str = "-"
FEAT: dict[str, tuple[str, int, int, int]] = {
    "p": ("C", 0, 0, 0),
    "b": ("C", 0, 0, 1),
    "f": ("C", 0, 1, 0),
    "v": ("C", 0, 1, 1),
    "m": ("C", 0, 3, 1),
    "w": ("C", 0, 6, 1),
    "t": ("C", 1, 0, 0),
    "d": ("C", 1, 0, 1),
    "s": ("C", 1, 1, 0),
    "z": ("C", 1, 1, 1),
    "n": ("C", 1, 3, 1),
    "l": ("C", 1, 4, 1),
    "r": ("C", 1, 5, 1),
    "S": ("C", 2, 1, 0),
    "Z": ("C", 2, 1, 1),
    "C": ("C", 2, 2, 0),
    "G": ("C", 2, 2, 1),
    "J": ("C", 3, 3, 1),
    "L": ("C", 3, 4, 1),
    "j": ("C", 3, 6, 1),
    "k": ("C", 4, 0, 0),
    "g": ("C", 4, 0, 1),
    "h": ("C", 5, 1, 0),
    "a": ("V", 2, 1, 0),
    "e": ("V", 1, 0, 0),
    "i": ("V", 0, 0, 0),
    "o": ("V", 1, 2, 1),
    "u": ("V", 0, 2, 1),
    "y": ("V", 0, 0, 1),
}


def phon_dist(a: str, b: str) -> float:
    if a == b:
        return 0.0
    fa, fb = (FEAT[a], FEAT[b])
    if fa[0] != fb[0]:
        return 3.0
    if fa[0] == "C":
        return 1.0 * min(abs(fa[1] - fb[1]), 3) / 3.0 + 1.5 * (0 if fa[2] == fb[2] else 1) + 0.5 * abs(fa[3] - fb[3])
    else:
        return 1.0 * abs(fa[1] - fb[1]) / 2.0 + 1.0 * abs(fa[2] - fb[2]) / 2.0 + 0.5 * abs(fa[3] - fb[3])


GAP_PEN: float = -1.0


def sub_score(a: str, b: str) -> float:
    if a == GAP or b == GAP:
        return GAP_PEN
    return 2.0 - phon_dist(a, b)


def col_score(column: list[str], seg: str) -> float:
    vals = [sub_score(x, seg) if x != GAP else GAP_PEN for x in column]
    return float(sum(vals) / len(vals))


def align_seq_to_msa(msa_rows: list[list[str]], seq: list[str]) -> list[list[str]]:
    W = len(msa_rows[0]) if msa_rows else 0
    n = len(seq)
    cols = [[row[c] for row in msa_rows] for c in range(W)]
    NEG = -1000000000.0
    dp: NDArray[np.float64] = np.full((W + 1, n + 1), NEG)
    bt: NDArray[np.intp] = np.zeros((W + 1, n + 1), dtype=int)
    dp[0, 0] = 0.0
    for i in range(1, W + 1):
        dp[i, 0] = dp[i - 1, 0] + GAP_PEN
        bt[i, 0] = 1
    for j in range(1, n + 1):
        dp[0, j] = dp[0, j - 1] + GAP_PEN
        bt[0, j] = 2
    for i in range(1, W + 1):
        for j in range(1, n + 1):
            diag = float(dp[i - 1, j - 1]) + col_score(cols[i - 1], seq[j - 1])
            up = float(dp[i - 1, j]) + GAP_PEN
            left = float(dp[i, j - 1]) + GAP_PEN
            best = max(diag, up, left)
            dp[i, j] = best
            bt[i, j] = 0 if best == diag else 1 if best == up else 2
    i, j = (W, n)
    new_cols: list[tuple[list[str] | None, str]] = []
    while i > 0 or j > 0:
        b = int(bt[i, j])
        if i > 0 and j > 0 and (b == 0):
            new_cols.append((cols[i - 1], seq[j - 1]))
            i -= 1
            j -= 1
        elif i > 0 and (j == 0 or b == 1):
            new_cols.append((cols[i - 1], GAP))
            i -= 1
        else:
            new_cols.append((None, seq[j - 1]))
            j -= 1
    new_cols.reverse()
    R = len(msa_rows)
    out: list[list[str]] = [[] for _ in range(R + 1)]
    for col, seg in new_cols:
        if col is None:
            for r in range(R):
                out[r].append(GAP)
            out[R].append(seg)
        else:
            for r in range(R):
                out[r].append(col[r])
            out[R].append(seg)
    return out


def build_msa(forms: list[tuple[str, list[str]]]) -> tuple[list[str], list[list[str]]]:
    order = sorted(range(len(forms)), key=lambda k: -len(forms[k][1]))
    langs = [forms[order[0]][0]]
    msa = [list(forms[order[0]][1])]
    for k in order[1:]:
        lang, seq = forms[k]
        msa = align_seq_to_msa(msa, list(seq))
        langs.append(lang)
    return (langs, msa)


TreeNode = tuple[str, ...]


def L(name: str, length: float) -> TreeNode:
    return ("L", name, str(length))


def I(length: float, kids: list[TreeNode]) -> TreeNode:  # noqa: E743
    return ("I", str(length), *[str(id(k)) for k in kids])


TREE: tuple[str, ...] = (
    "I",
    "0.0",
    "L",
    "sc",
    "0.35",
    "L",
    "ro",
    "0.85",
    "I",
    "0.15",
    "L",
    "it",
    "0.45",
    "I",
    "0.15",
    "L",
    "fr",
    "0.95",
    "I",
    "0.15",
    "L",
    "es",
    "0.5",
    "L",
    "pt",
    "0.5",
)

_TREE: Any = (
    "I",
    0.0,
    [
        ("L", "sc", 0.35),
        ("L", "ro", 0.85),
        (
            "I",
            0.15,
            [("L", "it", 0.45), ("I", 0.15, [("L", "fr", 0.95), ("I", 0.15, [("L", "es", 0.5), ("L", "pt", 0.5)])])],
        ),
    ],
)
TREE = _TREE


def node_len(node: tuple[str, ...]) -> float:
    return float(node[2]) if node[0] == "L" else float(node[1])


LAMBDA: float = 1.4
GAP_EXCH: float = 0.05


def build_Q(states: list[str], pi: NDArray[np.float64]) -> tuple[NDArray[np.float64], dict[str, int]]:
    S = len(states)
    idx: dict[str, int] = {s: i for i, s in enumerate(states)}
    R: NDArray[np.float64] = np.zeros((S, S))
    for a in states:
        for b in states:
            if a == b:
                continue
            if a == GAP or b == GAP:
                R[idx[a], idx[b]] = GAP_EXCH
            else:
                R[idx[a], idx[b]] = math.exp(-LAMBDA * phon_dist(a, b))
    Q: NDArray[np.float64] = np.zeros((S, S))
    for i in range(S):
        for j in range(S):
            if i != j:
                Q[i, j] = R[i, j] * pi[j]
        Q[i, i] = -float(np.sum(Q[i, :]))
    scale = -float(np.sum(pi * np.diag(Q)))
    return (Q / scale, idx)


class Model:
    def __init__(self, states: list[str], pi: NDArray[np.float64], Q: NDArray[np.float64], idx: dict[str, int]) -> None:
        self.states: list[str] = states
        self.pi: NDArray[np.float64] = pi
        self.Q: NDArray[np.float64] = Q
        self.idx: dict[str, int] = idx
        self._P: dict[float, NDArray[np.float64]] = {}

    def P(self, t: float) -> NDArray[np.float64]:
        key = round(t, 6)
        if key not in self._P:
            self._P[key] = expm(self.Q * t)
        return self._P[key]


def partial(node: tuple[str, ...], column: dict[str, str], model: Model) -> NDArray[np.float64]:
    S = len(model.states)
    if node[0] == "L":
        name: str = str(node[1])
        seg = column.get(name)
        v: NDArray[np.float64] = np.ones(S)
        if seg is not None:
            v = np.zeros(S)
            v[model.idx[seg]] = 1.0
        return v
    kids: list[tuple[str, ...]] = node[2]  # type: ignore[assignment]
    Ln: NDArray[np.float64] = np.ones(S)
    for ch in kids:
        Lc = partial(ch, column, model)
        Ln *= model.P(node_len(ch)).dot(Lc)
    return Ln


def reconstruct_column(column: dict[str, str], model: Model) -> tuple[str, float, NDArray[np.float64]]:
    Lroot = partial(TREE, column, model)
    post: NDArray[np.float64] = model.pi * Lroot
    tot = float(post.sum())
    post = post / tot if tot > 0 else np.ones(len(post)) / len(post)
    ent = -float(np.sum(np.array([p * math.log2(p) for p in post if p > 0])))
    top = int(np.argmax(post))
    return (model.states[top], ent, post)


def levenshtein(a: list[str], b: list[str]) -> int:
    n, m = (len(a), len(b))
    d: NDArray[np.float64] = np.zeros((n + 1, m + 1))
    for i in range(n + 1):
        d[i, 0] = i
    for j in range(m + 1):
        d[0, j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            d[i, j] = min(
                float(d[i - 1, j]) + 1,
                float(d[i, j - 1]) + 1,
                float(d[i - 1, j - 1]) + (0 if a[i - 1] == b[j - 1] else 1),
            )
    return int(d[n, m])


def nw_match_flags(recon: list[str], gold: list[str]) -> list[bool]:
    n, m = (len(recon), len(gold))
    NEG = -1000000000.0
    dp: NDArray[np.float64] = np.full((n + 1, m + 1), NEG)
    bt: NDArray[np.intp] = np.zeros((n + 1, m + 1), dtype=int)
    dp[0, 0] = 0
    for i in range(1, n + 1):
        dp[i, 0] = dp[i - 1, 0] + GAP_PEN
        bt[i, 0] = 1
    for j in range(1, m + 1):
        dp[0, j] = dp[0, j - 1] + GAP_PEN
        bt[0, j] = 2
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            diag = float(dp[i - 1, j - 1]) + sub_score(recon[i - 1], gold[j - 1])
            up = float(dp[i - 1, j]) + GAP_PEN
            left = float(dp[i, j - 1]) + GAP_PEN
            best = max(diag, up, left)
            dp[i, j] = best
            bt[i, j] = 0 if best == diag else 1 if best == up else 2
    i, j = (n, m)
    flags = [False] * n
    while i > 0 or j > 0:
        b = int(bt[i, j])
        if i > 0 and j > 0 and (b == 0):
            flags[i - 1] = recon[i - 1] == gold[j - 1]
            i -= 1
            j -= 1
        elif i > 0 and (j == 0 or b == 1):
            i -= 1
        else:
            j -= 1
    return flags
