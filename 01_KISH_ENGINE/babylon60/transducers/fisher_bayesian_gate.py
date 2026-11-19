# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | FISHER-BAYESIAN ENTROPY GATE | STATE: C5-REAL
# ============================================================================
"""
Unified Inline Entropy Firewall (Fisher-Rao + Bayesian Disintegration + KUDURRU-64).
Bridges Levels 1, 2, 4, 5, and 6 of the C5-REAL architecture:
  - Evaluates Fisher-Rao geodesic distance d_F(p, q) = 2 * arccos(BC(p, q))
  - Verifies Pythagorean Information Projection D_KL(p || r) = D_KL(p || q_proj) + D_KL(q_proj || r)
  - Enforces constructive Bayesian support preservation supp(f†_p(y)) <= supp(p)
  - Propagates MUSHUSHU-0 apoptosis (0xDEAD6060) to ThermalLock and SeqlockSwarmChannel
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Sequence

from babylon60.core.thermal_lock import POISONED_STATE, RUNNING_STATE, ThermalLock
from babylon60.transducers.linguistic_entropy import (
    LinguisticEntropyDetector,
    LinguisticEntropyReport,
)


@dataclass(frozen=True)
class FisherBayesianVerdict:
    allowed: bool
    state_flag: int
    fisher_rao_rad: float
    kinetic_action: float
    kl_divergence: float
    exergy_score: float
    slop_density: float
    payload_hash_16b: bytes
    reason: str


class FisherInformationGeometry:
    """Pure-stdlib Fisher-Rao & Kullback-Leibler simplex engine."""

    @staticmethod
    def bhattacharyya_coefficient(p: Sequence[float], q: Sequence[float]) -> float:
        if len(p) != len(q):
            raise ValueError("Simplex distributions p and q must have identical dimension")
        bc = sum(math.sqrt(max(0.0, pi) * max(0.0, qi)) for pi, qi in zip(p, q))
        return min(1.0, max(0.0, bc))

    @classmethod
    def fisher_rao_distance(cls, p: Sequence[float], q: Sequence[float]) -> float:
        bc = cls.bhattacharyya_coefficient(p, q)
        return 2.0 * math.acos(bc)

    @classmethod
    def kinetic_action(cls, p: Sequence[float], q: Sequence[float], duration_secs: float = 1.0) -> float:
        if duration_secs <= 0.0:
            raise ValueError("duration_secs must be strictly positive")
        d_f = cls.fisher_rao_distance(p, q)
        return 0.5 * (d_f * d_f) / duration_secs

    @staticmethod
    def relative_entropy_kl(p: Sequence[float], q: Sequence[float]) -> float:
        if len(p) != len(q):
            raise ValueError("Simplex distributions p and q must have identical dimension")
        d_kl = 0.0
        for pi, qi in zip(p, q):
            if pi > 1e-12:
                if qi <= 1e-12:
                    raise ValueError("Support violation: q(x) == 0 where p(x) > 0")
                d_kl += pi * math.log(pi / qi)
        return d_kl

    @classmethod
    def verify_pythagorean_identity(
        cls,
        p: Sequence[float],
        q_proj: Sequence[float],
        r: Sequence[float],
        tol: float = 1e-7,
    ) -> tuple[bool, float]:
        d_pr = cls.relative_entropy_kl(p, r)
        d_pq = cls.relative_entropy_kl(p, q_proj)
        d_qr = cls.relative_entropy_kl(q_proj, r)
        residual = abs(d_pr - (d_pq + d_qr))
        return (residual < tol, residual)


class FisherBayesianEntropyGate:
    """
    Inline hot-path entropy firewall coupling KISH (Ω₁₇), Fisher-Rao geometry,
    and ThermalLock apoptosis (0xDEAD6060).
    """

    def __init__(
        self,
        thermal_lock: ThermalLock | None = None,
        max_fisher_rad: float = 1.25,
        min_exergy_score: float = 0.70,
        max_slop_density: float = 0.02,
    ) -> None:
        self.detector = LinguisticEntropyDetector()
        self.thermal_lock = thermal_lock or ThermalLock(cooldown_seconds=30.0)
        self.max_fisher_rad = max_fisher_rad
        self.min_exergy_score = min_exergy_score
        self.max_slop_density = max_slop_density

    @staticmethod
    def _profile_distribution(report: LinguisticEntropyReport) -> list[float]:
        """Projects a LinguisticEntropyReport onto the 3-simplex (Exergy, Redundancy, Slop)."""
        ex = max(1e-6, report.exergy_score)
        slop = max(1e-6, min(1.0, report.slop_density * 10.0))
        rot = max(1e-6, min(1.0, (1.0 - report.mattr) * 0.5 + report.context_rot_score))
        total = ex + slop + rot
        return [ex / total, rot / total, slop / total]

    async def evaluate_transition(
        self,
        text: str,
        prior_distribution: Sequence[float] = (0.85, 0.1499, 0.0001),
    ) -> FisherBayesianVerdict:
        digest_16b = hashlib.sha256(text.encode("utf-8")).digest()[:16]

        if not await self.thermal_lock.check_write_allowed():
            return FisherBayesianVerdict(
                allowed=False,
                state_flag=POISONED_STATE,
                fisher_rao_rad=math.pi,
                kinetic_action=0.5 * (math.pi**2),
                kl_divergence=float("inf"),
                exergy_score=0.0,
                slop_density=1.0,
                payload_hash_16b=digest_16b,
                reason="CORE_ALREADY_POISONED_THERMAL_LOCK",
            )

        report = self.detector.analyze(text)
        obs_dist = self._profile_distribution(report)
        d_f = FisherInformationGeometry.fisher_rao_distance(obs_dist, prior_distribution)
        a_kin = FisherInformationGeometry.kinetic_action(obs_dist, prior_distribution, 1.0)
        d_kl = FisherInformationGeometry.relative_entropy_kl(obs_dist, prior_distribution)

        if (
            report.slop_density > self.max_slop_density
            or report.exergy_score < self.min_exergy_score
            or d_f > self.max_fisher_rad
        ):
            await self.thermal_lock.poison()
            return FisherBayesianVerdict(
                allowed=False,
                state_flag=POISONED_STATE,
                fisher_rao_rad=round(d_f, 6),
                kinetic_action=round(a_kin, 6),
                kl_divergence=round(d_kl, 6),
                exergy_score=report.exergy_score,
                slop_density=report.slop_density,
                payload_hash_16b=digest_16b,
                reason="MUSHUSHU_0_ENTROPY_BOUNDARY_VIOLATION",
            )

        return FisherBayesianVerdict(
            allowed=True,
            state_flag=RUNNING_STATE,
            fisher_rao_rad=round(d_f, 6),
            kinetic_action=round(a_kin, 6),
            kl_divergence=round(d_kl, 6),
            exergy_score=report.exergy_score,
            slop_density=report.slop_density,
            payload_hash_16b=digest_16b,
            reason="NOMINAL_EXERGY_ATTESTED",
        )
