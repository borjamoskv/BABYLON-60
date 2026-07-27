# C5-REAL EXERGY CERTIFIED
"""apex_trials.backtest — calibrate the deterministic score against public ground-truth.

For a cohort of completed trials we compute the predicted amendment-risk score
and the ACTUAL number of substantive protocol amendments (from the history
plane), then measure whether the score rank-orders reality: Spearman rank
correlation + a tier-stratified mean-amendment table. This is the C5-REAL
attestation that the model's ordering is earned, not asserted.

No third-party deps: Spearman is computed by hand (average-rank ties, Pearson
on ranks).

Author: Borja Moskv (borjamoskv). Reality level: C5-REAL.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .ctgov import CtGovClient, CtGovError, classify_history
from .features import extract_features
from .risk_engine import assess


@dataclass(frozen=True)
class BacktestRow:
    nct_id: str
    score: int
    tier: str
    actual_substantive: int
    n_versions: int
    title: str


@dataclass(frozen=True)
class BacktestReport:
    rows: tuple[BacktestRow, ...]
    spearman: float
    tier_means: dict[str, dict[str, float]]
    n: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "n": self.n,
            "spearman_score_vs_actual_amendments": round(self.spearman, 4),
            "tier_means": self.tier_means,
            "rows": [
                {
                    "nct_id": r.nct_id,
                    "score": r.score,
                    "tier": r.tier,
                    "actual_substantive": r.actual_substantive,
                    "n_versions": r.n_versions,
                    "title": r.title,
                }
                for r in self.rows
            ],
        }


def _average_ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0  # 1-based average rank for the tie group
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def _pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    if dx == 0 or dy == 0:
        return 0.0
    return float(num / (dx * dy))


def spearman(xs: list[float], ys: list[float]) -> float:
    return _pearson(_average_ranks(xs), _average_ranks(ys))


def run_backtest(
    client: CtGovClient,
    condition: str,
    n: int = 30,
    status: str = "COMPLETED",
) -> BacktestReport:
    studies = client.search(condition=condition, status=status, page_size=min(n * 2, 200))
    rows: list[BacktestRow] = []
    for study in studies:
        if len(rows) >= n:
            break
        ident = study.get("protocolSection", {}).get("identificationModule", {})
        nct = ident.get("nctId")
        if not nct:
            continue
        try:
            history = classify_history(nct, client.get_history(nct))
        except CtGovError:
            continue
        features = extract_features(study)
        assessment = assess(features)
        rows.append(
            BacktestRow(
                nct_id=nct,
                score=assessment.score,
                tier=assessment.tier,
                actual_substantive=history.n_substantive,
                n_versions=history.n_versions,
                title=features.brief_title[:60],
            )
        )

    scores = [float(r.score) for r in rows]
    actuals = [float(r.actual_substantive) for r in rows]
    rho = spearman(scores, actuals) if len(rows) >= 2 else 0.0

    tier_means: dict[str, dict[str, float]] = {}
    for tier in ("LOW", "MODERATE", "HIGH", "CRITICAL"):
        group = [r for r in rows if r.tier == tier]
        if group:
            tier_means[tier] = {
                "n": float(len(group)),
                "mean_actual_amendments": round(sum(r.actual_substantive for r in group) / len(group), 2),
                "mean_score": round(sum(r.score for r in group) / len(group), 1),
            }

    return BacktestReport(rows=tuple(rows), spearman=rho, tier_means=tier_means, n=len(rows))
