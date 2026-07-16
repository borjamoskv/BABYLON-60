"""Markov substitution model + Felsenstein pruning on a phylogenetic tree."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from scipy.linalg import expm

from cortex.agents.phylo.phonetics import phonetic_distance
from cortex.agents.phylo.alignment import GAP

# -- Tree node constructors --------------------------------------------------
TreeNode = tuple[Any, ...]  # ("L", name, length) | ("I", length, children)


def leaf(name: str, length: float) -> TreeNode:
    return ("L", name, length)


def internal(length: float, kids: list[TreeNode]) -> TreeNode:  # noqa: E743
    return ("I", length, kids)


def branch_length(node: TreeNode) -> float:
    return node[2] if node[0] == "L" else node[1]


# -- Default Romance tree (prior initial values) -----------------------------
DEFAULT_TREE: TreeNode = internal(
    0.0,
    [
        leaf("sc", 0.35),
        leaf("ro", 0.85),
        internal(
            0.15,
            [
                leaf("it", 0.45),
                internal(
                    0.15,
                    [
                        leaf("fr", 0.95),
                        internal(0.15, [leaf("es", 0.50), leaf("pt", 0.50)]),
                    ],
                ),
            ],
        ),
    ],
)


# -- Substitution model (Q matrix + transition probability cache) -------------
LAMBDA = 1.4
GAP_EXCH = 0.05


def build_rate_matrix(
    states: list[str], pi: np.ndarray
) -> tuple[np.ndarray, dict[str, int]]:
    """Build normalized Q matrix from phonetic exchangeabilities."""
    num_s = len(states)
    idx = {s: i for i, s in enumerate(states)}
    raw = np.zeros((num_s, num_s))
    for a in states:
        for b in states:
            if a == b:
                continue
            if a == GAP or b == GAP:
                raw[idx[a], idx[b]] = GAP_EXCH
            else:
                raw[idx[a], idx[b]] = math.exp(-LAMBDA * phonetic_distance(a, b))

    q_mat = np.zeros((num_s, num_s))
    for i in range(num_s):
        for j in range(num_s):
            if i != j:
                q_mat[i, j] = raw[i, j] * pi[j]
        q_mat[i, i] = -np.sum(q_mat[i, :])

    scale = -np.sum(pi * np.diag(q_mat))
    return q_mat / scale, idx


class SubstitutionModel:
    """CTMC substitution model with memoized P(t) = expm(Qt)."""

    __slots__ = ("states", "pi", "q_mat", "idx", "_cache")

    def __init__(
        self,
        states: list[str],
        pi: np.ndarray,
        q_mat: np.ndarray,
        idx: dict[str, int],
    ) -> None:
        self.states = states
        self.pi = pi
        self.q_mat = q_mat
        self.idx = idx
        self._cache: dict[float, np.ndarray] = {}

    def transition_prob(self, t: float) -> np.ndarray:
        key = round(t, 6)
        if key not in self._cache:
            self._cache[key] = expm(self.q_mat * t)
        return self._cache[key]


# -- Felsenstein pruning ------------------------------------------------------
def felsenstein_partial(
    node: TreeNode, column: dict[str, str], model: SubstitutionModel
) -> np.ndarray:
    """Conditional likelihood vector at `node`."""
    num_s = len(model.states)
    if node[0] == "L":
        _, name, _ = node
        seg = column.get(name)
        if seg is None:
            return np.ones(num_s)
        vec = np.zeros(num_s)
        vec[model.idx[seg]] = 1.0
        return vec

    _, _, kids = node
    result = np.ones(num_s)
    for child in kids:
        child_partial = felsenstein_partial(child, column, model)
        result *= model.transition_prob(branch_length(child)).dot(child_partial)
    return result


def reconstruct_column(
    tree: TreeNode, column: dict[str, str], model: SubstitutionModel
) -> tuple[str, float, np.ndarray]:
    """MAP reconstruction + posterior entropy for one MSA column."""
    root_partial = felsenstein_partial(tree, column, model)
    posterior = model.pi * root_partial
    total = posterior.sum()
    posterior = posterior / total if total > 0 else np.ones(len(posterior)) / len(posterior)
    entropy = -sum(p * math.log2(p) for p in posterior if p > 0)
    best_idx = int(np.argmax(posterior))
    return model.states[best_idx], entropy, posterior
