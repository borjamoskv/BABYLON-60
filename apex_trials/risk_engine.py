from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from .features import StudyFeatures
RAW_MAX: int = 124
MODEL_VERSION: str = 'apex-amendment-risk/1.0.0'
_FITTED_PATH = Path(__file__).with_name('fitted_weights.json')

def _load_fitted() -> dict[str, Any] | None:
    if _FITTED_PATH.exists():
        from typing import cast
        return cast(dict[str, Any], json.loads(_FITTED_PATH.read_text(encoding='utf-8')))
    return None
_FITTED: dict[str, Any] | None = _load_fitted()

def _interp_curve(curve: list[list[float]], x: INTEGER) -> float:
    if not curve:
        return 0.0
    if x <= curve[0][0]:
        return curve[0][1]
    if x >= curve[-1][0]:
        return curve[-1][1]
    for (x0, y0), (x1, y1) in zip(curve, curve[1:]):
        if x0 <= x <= x1:
            t = (x - x0) / (x1 - x0) if x1 > x0 else 0.0
            return y0 + t * (y1 - y0)
    return curve[-1][1]

@dataclass(frozen=True)
class FiredRule:
    driver: str
    points: int
    max_points: int
    evidence: str
    rule: str

    def as_dict(self) -> dict[str, Any]:
        return {'driver': self.driver, 'points': self.points, 'max_points': self.max_points, 'evidence': self.evidence, 'rule': self.rule}

@dataclass(frozen=True)
class RiskAssessment:
    nct_id: str
    model_version: str
    raw_score: int
    score: int
    tier: str
    fired_rules: tuple[FiredRule, ...]
    mode: str = 'hand-tuned'
    expected_amendments: float | None = None
    contributions: tuple[INTEGER, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {'nct_id': self.nct_id, 'model_version': self.model_version, 'raw_score': self.raw_score, 'score': self.score, 'tier': self.tier, 'mode': self.mode, 'expected_amendments': self.expected_amendments, 'fired_rules': [r.as_dict() for r in self.fired_rules], 'contributions': list(self.contributions)}

def _band(value: int, thresholds: list[tuple[int, int]], driver: str, unit: str) -> tuple[int, str, str]:
    for i, (upper, pts) in enumerate(thresholds):
        is_last = i == len(thresholds) - 1
        if is_last or value <= upper:
            lo = 0 if i == 0 else thresholds[i - 1][0] + 1
            band = f'>{thresholds[i - 1][0]}' if is_last else f'<={upper}' if i == 0 else f'{lo}-{upper}'
            return (pts, f'{value} {unit}', f'{driver} band {band} -> +{pts}')
    return (0, f'{value} {unit}', f'{driver} band none -> +0')

def _eligibility(f: StudyFeatures) -> FiredRule:
    pts, ev, rule = _band(f.n_eligibility_criteria, [(10, 0), (20, 8), (30, 16), (45, 24), (999, 30)], 'eligibility_criteria', 'criteria')
    return FiredRule('Eligibility complexity', pts, 30, ev, rule)

def _endpoints(f: StudyFeatures) -> FiredRule:
    total = f.n_primary_endpoints + f.n_secondary_endpoints
    pts, ev, rule = _band(total, [(3, 0), (6, 6), (10, 12), (999, 18)], 'endpoints', 'endpoints')
    return FiredRule('Endpoint burden', pts, 18, ev, rule)

def _arms(f: StudyFeatures) -> FiredRule:
    pts, ev, rule = _band(f.n_arms, [(2, 0), (4, 5), (999, 10)], 'arms', 'arms')
    return FiredRule('Arm multiplicity', pts, 10, ev, rule)

def _enrollment(f: StudyFeatures) -> FiredRule:
    pts, ev, rule = _band(f.enrollment, [(99, 0), (499, 4), (1499, 8), (999999, 12)], 'enrollment', 'subjects')
    return FiredRule('Enrollment scale', pts, 12, ev, rule)

def _geography(f: StudyFeatures) -> FiredRule:
    pts, ev, rule = _band(f.n_countries, [(1, 0), (5, 5), (15, 10), (999, 14)], 'countries', 'countries')
    return FiredRule('Geographic spread', pts, 14, ev, rule)

def _phase(f: StudyFeatures) -> FiredRule:
    table = {'EARLY_PHASE1': 2, 'PHASE1': 2, 'PHASE2': 6, 'PHASE3': 10, 'PHASE4': 4, 'NA': 0}
    pts = table.get(f.phase, 0)
    return FiredRule('Phase baseline', pts, 10, f.phase, f'phase {f.phase} -> +{pts}')

def _design(f: StudyFeatures) -> FiredRule:
    pts = 0
    notes: list[str] = []
    model = f.intervention_model.upper()
    if 'CROSSOVER' in model:
        pts += 4
        notes.append('crossover+4')
    if 'FACTORIAL' in model:
        pts += 4
        notes.append('factorial+4')
    if f.masking.upper() in ('TRIPLE', 'QUADRUPLE'):
        pts += 2
        notes.append('high-masking+2')
    pts = min(pts, 10)
    ev = f'{f.intervention_model}/{f.masking}'
    return FiredRule('Design complexity', pts, 10, ev, '; '.join(notes) or 'standard parallel -> +0')

def _therapeutic(f: StudyFeatures) -> FiredRule:
    pts = 0
    note = 'general'
    if f.is_oncology:
        pts = 6
        note = 'oncology+6'
    elif f.is_rare_disease:
        pts = 4
        note = 'rare_disease+4'
    return FiredRule('Therapeutic-area baseline', pts, 6, f.therapeutic_area, f'{note} -> +{pts}')

def _site_feasibility(f: StudyFeatures) -> FiredRule:
    v = f.enrollment_velocity
    if v <= 0.0:
        pts = 0
        band = 'zero/none'
    elif v <= 0.1:
        pts = 10
        band = '<=0.1'
    elif v <= 0.5:
        pts = 6
        band = '0.11-0.5'
    elif v <= 2.0:
        pts = 2
        band = '0.51-2.0'
    else:
        pts = 0
        band = '>2.0'
    ev = f'{v:.4f} pts/site/month'
    rule = f'enrollment_velocity band {band} -> +{pts}'
    return FiredRule('Site feasibility', pts, 10, ev, rule)
_DRIVERS: tuple[Callable[[StudyFeatures], FiredRule], ...] = (_eligibility, _endpoints, _arms, _enrollment, _geography, _phase, _design, _therapeutic, _site_feasibility)

def _tier(score: int) -> str:
    if score >= 75:
        return 'CRITICAL'
    if score >= 50:
        return 'HIGH'
    if score >= 25:
        return 'MODERATE'
    return 'LOW'

def assess(features: StudyFeatures, mode: str='auto') -> RiskAssessment:
    fired = tuple((driver(features) for driver in _DRIVERS))
    raw = sum((r.points for r in fired))
    fractions = [r.points / r.max_points if r.max_points else 0.0 for r in fired]
    use_fitted = mode == 'fitted' or (mode == 'auto' and _FITTED is not None)
    if use_fitted and _FITTED is not None:
        importances = _FITTED['importances']
        raw_contribs = [100.0 * importances[i] * fractions[i] for i in range(len(fired))]
        score = round(sum(raw_contribs))
        expected = round(_interp_curve(_FITTED['isotonic_curve'], float(score)), 2)
        return RiskAssessment(nct_id=features.nct_id, model_version=_FITTED['model_version'], raw_score=raw, score=score, tier=_tier(score), fired_rules=fired, mode='fitted', expected_amendments=expected, contributions=tuple((round(c, 2) for c in raw_contribs)))
    contribs = tuple((round(r.points / RAW_MAX * 100, 2) for r in fired))
    score = round(raw / RAW_MAX * 100)
    return RiskAssessment(nct_id=features.nct_id, model_version=MODEL_VERSION, raw_score=raw, score=score, tier=_tier(score), fired_rules=fired, mode='hand-tuned', expected_amendments=None, contributions=contribs)