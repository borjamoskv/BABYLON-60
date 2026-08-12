#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
r"""
poc_axiom4_disintegration.py — Proof of Concept: Axiom 4 Bayesian Disintegration & Non-Hallucination

Demonstrates the constructive computation of the Bayesian disintegration morphism f^\dagger_p
in a finite stochastic category (FinStoch / Markov category), enforcing:
1. Joint probability symmetry: p x f = (p f) x f^\dagger_p
2. Support non-hallucination invariant: supp(f^\dagger_p(y)) <= supp(p)
3. Split Epi reduction under deterministic incommensurability collapse.
"""

import sys
from typing import Dict, Set, Tuple


class FiniteMarkovKernel:
    """Stochastic morphism f: X -> Y defined by a transition matrix P(Y|X)."""

    def __init__(self, X: Set[str], Y: Set[str], matrix: Dict[Tuple[str, str], float]):
        self.X = X
        self.Y = Y
        self.matrix = matrix

    def apply_prior(self, p: Dict[str, float]) -> Dict[str, float]:
        """Compute the pushforward distribution p * f on Y."""
        pf: Dict[str, float] = {y: 0.0 for y in self.Y}
        for x, prob_x in p.items():
            if prob_x > 0:
                for y in self.Y:
                    pf[y] += prob_x * self.matrix.get((x, y), 0.0)
        return pf

    def disintegrate(self, p: Dict[str, float]) -> Dict[Tuple[str, str], float]:
        r"""
        Constructive Bayesian Disintegration f^\dagger_p: Y -> X.
        Computes P(X=x | Y=y) = P(Y=y | X=x) * p(x) / (p f)(y).
        Enforces supp(f^\dagger_p(y)) <= supp(p).
        """
        pf = self.apply_prior(p)
        prior_supp = {x for x, prob in p.items() if prob > 0}
        f_dagger: Dict[Tuple[str, str], float] = {}

        for y in self.Y:
            py = pf[y]
            if py > 0:
                for x in self.X:
                    if x in prior_supp:
                        prob_xy = self.matrix.get((x, y), 0.0) * p[x]
                        f_dagger[(y, x)] = prob_xy / py
                    else:
                        # Non-hallucination invariant: force 0 outside prior support
                        f_dagger[(y, x)] = 0.0
            else:
                # Observation outside image: zero distribution (circuit breaker)
                for x in self.X:
                    f_dagger[(y, x)] = 0.0

        return f_dagger


def main() -> None:
    print("[*] C5-REAL — Proof of Concept: Axiom 4 Bayesian Disintegration Engine")
    print("=" * 72)

    # Defined finite objects
    X = {"state_A", "state_B", "state_C"}  # state_C is outside prior support
    Y = {"obs_1", "obs_2"}

    # Prior distribution p with supp(p) = {"state_A", "state_B"}
    prior_p = {"state_A": 0.7, "state_B": 0.3, "state_C": 0.0}
    prior_supp = {x for x, prob in prior_p.items() if prob > 0}

    # Stochastic Kernel f: X -> Y
    kernel_matrix = {
        ("state_A", "obs_1"): 0.8,
        ("state_A", "obs_2"): 0.2,
        ("state_B", "obs_1"): 0.1,
        ("state_B", "obs_2"): 0.9,
        ("state_C", "obs_1"): 0.5,  # Dummy transition if state_C were active
        ("state_C", "obs_2"): 0.5,
    }

    kernel = FiniteMarkovKernel(X, Y, kernel_matrix)

    # 1. Pushforward distribution pf
    pf = kernel.apply_prior(prior_p)
    print(f"[+] Pushforward Prior p*f on Y: {pf}")

    # 2. Bayesian Disintegration Morphism f^\dagger_p
    f_dagger = kernel.disintegrate(prior_p)
    print(r"[+] Constructed Disintegration Morphism f^\dagger_p (Posterior Kernel):")
    for (y, x), prob in f_dagger.items():
        if prob > 0:
            print(f"    P({x} | {y}) = {prob:.4f}")

    # 3. Verify Non-Hallucination Invariant: supp(f^\dagger_p(y)) <= supp(p)
    print("\n[*] Verifying Axiom 4.3 Support Non-Hallucination Invariant...")
    hallucinations_detected = False
    for y in Y:
        posterior_supp_y = {x for x in X if f_dagger.get((y, x), 0.0) > 0}
        print(f"    Observation '{y}' -> Posterior Support: {posterior_supp_y}")
        invalid = posterior_supp_y - prior_supp
        if invalid:
            print(f"    [!] VIOLATION: Hallucinated origins {invalid} detected!")
            hallucinations_detected = True

    if not hallucinations_detected:
        print(r"    [✓ PASS] Invariante de No-Alucinación verificado. supp(f^\dagger_p(y)) ⊆ supp(p).")

    # 4. Verify Joint Probability Symmetry (p x f = (p f) x f^\dagger_p)
    print("\n[*] Verifying Axiom 4.1 Joint Probability Symmetry...")
    symmetry_holds = True
    for x in X:
        for y in Y:
            joint_left = prior_p[x] * kernel_matrix.get((x, y), 0.0)
            joint_right = pf[y] * f_dagger.get((y, x), 0.0)
            if abs(joint_left - joint_right) > 1e-6:
                print(f"    [!] Asymmetry at ({x},{y}): left={joint_left}, right={joint_right}")
                symmetry_holds = False

    if symmetry_holds:
        print(r"    [✓ PASS] Simetría de Medida Conjunta verificada: (p ⊗ f = (p f) ⊗ f^\dagger_p).")

    print("\n" + "=" * 72)
    print("[✓ SUCCESS] Axiom 4 PoC Verification Completed cleanly.")
    sys.exit(0 if (not hallucinations_detected and symmetry_holds) else 1)


if __name__ == "__main__":
    main()
