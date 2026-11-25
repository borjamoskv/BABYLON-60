r"""
bayesian_disintegration.py — Desintegración Bayesiana y Disyuntor Nulo para Swarms
==================================================================================
Implementa el Nivel 6 de la arquitectura C5-REAL:
  - Morfismos finitos de Markov f: X -> Y
  - Desintegración Bayesiana constructiva f^\dagger_p: Y -> X
  - Cota estricta de no-alucinación: supp(f^\dagger_p(y)) <= supp(p)
  - Simetría de probabilidad conjunta: p x f = (p f) x f^\dagger_p
  - Token de Apoptosis MUSHUSHU-0: 0xDEAD_6060
"""

from typing import Dict, Set, Tuple

POISON_TOKEN = 0xDEAD_6060


class HallucinatedOriginError(Exception):
    """Disparado cuando la inferencia intenta deducir un origen fuera del soporte a priori."""

    pass


class JointAsymmetryError(Exception):
    r"""Disparado si la simetría conjunta p x f != (pf) x f^\dagger_p se rompe por deriva estocástica."""

    pass


class FiniteMarkovKernel:
    """Morfismo estocástico f: X -> Y definido por una matriz condicional P(Y | X)."""

    def __init__(self, x_states: Set[str], y_states: Set[str], matrix: Dict[Tuple[str, str], float]):
        self.x_states = set(x_states)
        self.y_states = set(y_states)
        self.matrix = matrix

    def apply_prior(self, p: Dict[str, float]) -> Dict[str, float]:
        """Calcula el empuje hacia adelante (pushforward) p * f sobre el espacio observable Y."""
        pf = {y: 0.0 for y in self.y_states}
        for x, prob_x in p.items():
            if prob_x > 0.0:
                for y in self.y_states:
                    trans = self.matrix.get((x, y), 0.0)
                    pf[y] += prob_x * trans
        return pf

    def disintegrate(self, p: Dict[str, float], tolerance: float = 1e-9) -> Dict[Tuple[str, str], float]:
        """Calcula el operador dual constructivo f^dagger_p: Y -> X.
        P(X=x | Y=y) = P(Y=y | X=x) * p(x) / (p f)(y).
        Garantiza que supp(f^dagger_p(y)) <= supp(p).
        """
        pf = self.apply_prior(p)
        prior_supp = {x for x, prob in p.items() if prob > 0.0}
        dual_matrix: Dict[Tuple[str, str], float] = {}

        for y in self.y_states:
            prob_y = pf[y]
            if prob_y <= 0.0:
                # Si el estado y no es observable bajo el prior, la distribución dual es nula
                for x in self.x_states:
                    dual_matrix[(y, x)] = 0.0
                continue

            for x in self.x_states:
                trans = self.matrix.get((x, y), 0.0)
                prob_x = p.get(x, 0.0)

                # Regla de Bayes constructiva
                cond_p = (trans * prob_x) / prob_y

                # Verificación de soporte estricto (Axioma 4.3):
                if cond_p > tolerance and x not in prior_supp:
                    raise HallucinatedOriginError(
                        f"Alucinación Detectada: Estado {x} deducido sin soporte a priori (p({x}) = 0)"
                    )

                dual_matrix[(y, x)] = cond_p

        # Verificación de simetría de probabilidad conjunta: p(x) * f(y|x) == pf(y) * f^\dagger(x|y)
        for x in self.x_states:
            prob_x = p.get(x, 0.0)
            for y in self.y_states:
                lhs = prob_x * self.matrix.get((x, y), 0.0)
                rhs = pf[y] * dual_matrix.get((y, x), 0.0)
                if abs(lhs - rhs) > 1e-6:
                    raise JointAsymmetryError(f"Asimetría Conjunta en ({x}, {y}): |{lhs} - {rhs}| > tol")

        return dual_matrix


class SwarmBayesianCircuitBreaker:
    """Disyuntor nulo de inferencia estocástica con cerrojo de veneno MUSHUSHU-0."""

    def __init__(self, kernel: FiniteMarkovKernel, prior: Dict[str, float]):
        self.kernel = kernel
        self.prior = prior
        self.poisoned = False

    def verify_observation_step(self, observable_y: str) -> Dict[str, float]:
        """Si la observación es termodinámicamente imposible o alucinatoria, dispara el disyuntor."""
        if self.poisoned:
            raise RuntimeError(f"CIRCUITO ENVENENADO (0x{POISON_TOKEN:X}): Swarm en estado POISONED")

        pf = self.kernel.apply_prior(self.prior)
        if pf.get(observable_y, 0.0) <= 0.0:
            # Observación físicamente incompatible con el prior -> Apoptosis MUSHUSHU-0
            self.poisoned = True
            raise HallucinatedOriginError(
                f"Observación Imposible '{observable_y}': Disyuntor disparado -> Apoptosis MUSHUSHU-0"
            )

        dual = self.kernel.disintegrate(self.prior)
        return {x: dual.get((observable_y, x), 0.0) for x in self.kernel.x_states}
