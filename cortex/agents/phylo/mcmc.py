"""MCMC inference with Simulated Annealing for branch length optimization."""

from __future__ import annotations

import math

import numpy as np

from cortex.agents.phylo.alignment import GAP
from cortex.agents.phylo.model import (
    TreeNode,
    SubstitutionModel,
    felsenstein_partial,
)


def tree_log_likelihood(
    tree: TreeNode,
    msas: dict[str, tuple[list[str], list[list[str]]]],
    model: SubstitutionModel,
) -> float:
    """Total log-likelihood of all cognate MSAs under the tree."""
    ll = 0.0
    for _concept, (langs, msa) in msas.items():
        width = len(msa[0])
        ncol = len(langs)
        for c in range(width):
            column = {langs[r]: msa[r][c] for r in range(ncol) if msa[r][c] != GAP}
            root_partial = felsenstein_partial(tree, column, model)
            prob = float(np.sum(model.pi * root_partial))
            ll += math.log(prob) if prob > 0 else -1e9
    return ll


def tree_prior(node: TreeNode, rate: float = 10.0) -> float:
    """Exponential prior on branch lengths (conjugate regularizer)."""
    if node[0] == "L":
        return math.log(rate) - rate * node[2]
    p = (math.log(rate) - rate * node[1]) if node[1] > 0 else 0.0
    return p + sum(tree_prior(k, rate) for k in node[2])


def _mutate_tree(node: TreeNode, step: float = 0.1) -> TreeNode:
    """Gaussian perturbation of all branch lengths."""
    if node[0] == "L":
        return ("L", node[1], max(0.01, node[2] + np.random.normal(0, step)))
    return (
        "I",
        max(0.00, node[1] + np.random.normal(0, step)),
        [_mutate_tree(k, step) for k in node[2]],
    )


def run_mcmc(
    start_tree: TreeNode,
    msas: dict[str, tuple[list[str], list[list[str]]]],
    model: SubstitutionModel,
    *,
    iters: int = 500,
    t_start: float = 5.0,
    t_end: float = 0.01,
) -> TreeNode:
    """Metropolis-Hastings with geometric annealing schedule."""
    curr_tree = start_tree
    curr_ll = tree_log_likelihood(curr_tree, msas, model)
    curr_prior = tree_prior(curr_tree)
    curr_post = curr_ll + curr_prior

    best_tree = curr_tree
    best_post = curr_post
    print(f"[C5-REAL] MCMC Inicio: LogPosterior = {curr_post:.2f} "
          f"(LL: {curr_ll:.2f}, Prior: {curr_prior:.2f})")

    for i in range(iters):
        temp = t_start * (t_end / t_start) ** (i / (iters - 1)) if iters > 1 else t_end
        new_tree = _mutate_tree(curr_tree)
        new_ll = tree_log_likelihood(new_tree, msas, model)
        new_prior = tree_prior(new_tree)
        new_post = new_ll + new_prior

        diff = new_post - curr_post
        if diff > 0 or (diff / temp > -20 and math.log(np.random.uniform(0, 1)) < diff / temp):
            curr_tree = new_tree
            curr_post = new_post
            if curr_post > best_post:
                best_post = curr_post
                best_tree = curr_tree

        if (i + 1) % 100 == 0:
            print(f"  MCMC Iter {i+1}/{iters} [T={temp:.3f}]: "
                  f"LogPost = {curr_post:.2f} (Best: {best_post:.2f})")

    return best_tree
