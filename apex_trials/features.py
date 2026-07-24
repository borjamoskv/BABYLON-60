"""apex_trials.features — deterministic complexity feature extraction.

Every field here is a pure function of the protocol record: given the same
study JSON, the same StudyFeatures is produced, with no wall-clock or random
input. These are the features known at *protocol design time* — so the score
built on them is genuinely predictive for a brand-new protocol, not a
post-hoc description.

Author: Borja Moskv (borjamoskv). Reality level: C5-REAL.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Any

_NUMBERED = re.compile(r"^\s*(\d+)\s*[.)]\s+\S")
_BULLET = re.compile(r"^\s*[-*•]\s+\S")

_ONCOLOGY_TERMS = (
    "cancer",
    "carcinoma",
    "tumor",
    "tumour",
    "oncolog",
    "neoplasm",
    "leukemia",
    "leukaemia",
    "lymphoma",
    "melanoma",
    "sarcoma",
    "myeloma",
    "glioma",
    "metasta",
)
_RARE_TERMS = (
    "rare",
    "orphan",
    "cystic fibrosis",
    "duchenne",
    "amyloidosis",
    "hemophilia",
    "haemophilia",
    "gaucher",
    "pompe",
    "huntington",
    "als ",
    "sma ",
    "spinal muscular",
)


@dataclass(frozen=True)
class StudyFeatures:
    nct_id: str
    brief_title: str
    phase: str
    study_type: str
    n_eligibility_criteria: int
    n_inclusion: int
    n_exclusion: int
    n_primary_endpoints: int
    n_secondary_endpoints: int
    n_arms: int
    enrollment: int
    n_sites: int
    n_countries: int
    allocation: str
    intervention_model: str
    masking: str
    is_oncology: bool
    is_rare_disease: bool
    therapeutic_area: str
    has_dmc: bool = False
    is_fda_regulated: bool = False
    brief_summary_words: int = 0
    n_conditions: int = 1
    n_interventions: int = 1
    enrollment_velocity: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _count_criteria(text: str) -> tuple[int, int, int]:
    """Count inclusion/exclusion criteria from the free-text block, deterministically.

    Splits on the 'exclusion' header; within each section counts numbered or
    bulleted items. Falls back to non-empty lines when no markers are present.
    """
    if not text:
        return 0, 0, 0
    lower = text.lower()
    idx = lower.find("exclusion")
    inclusion_block = text[:idx] if idx != -1 else text
    exclusion_block = text[idx:] if idx != -1 else ""

    def count_block(block: str) -> int:
        lines = block.splitlines()
        numbered = sum(1 for ln in lines if _NUMBERED.match(ln))
        if numbered:
            return numbered
        bulleted = sum(1 for ln in lines if _BULLET.match(ln))
        if bulleted:
            return bulleted
        return sum(1 for ln in lines if len(ln.strip()) > 12 and "criteria" not in ln.lower())

    n_inc = count_block(inclusion_block)
    n_exc = count_block(exclusion_block) if exclusion_block else 0
    return n_inc, n_exc, n_inc + n_exc


def _therapeutic_area(conditions: list[str]) -> tuple[bool, bool, str]:
    joined = " ; ".join(conditions).lower()
    is_onc = any(t in joined for t in _ONCOLOGY_TERMS)
    is_rare = any(t in joined for t in _RARE_TERMS)
    if is_onc:
        area = "Oncology"
    elif is_rare:
        area = "Rare disease"
    elif conditions:
        area = conditions[0][:40]
    else:
        area = "Unspecified"
    return is_onc, is_rare, area


def _max_phase(phases: list[str]) -> str:
    order = ["EARLY_PHASE1", "PHASE1", "PHASE2", "PHASE3", "PHASE4"]
    present = [p for p in phases if p in order]
    if not present:
        return phases[0] if phases else "NA"
    return max(present, key=order.index)


def _parse_date_to_months(date_str: str | None) -> float | None:
    if not date_str:
        return None
    parts = date_str.split("-")
    try:
        year = int(parts[0])
        month = int(parts[1]) if len(parts) > 1 else 1
        return year * 12.0 + month
    except (ValueError, IndexError):
        return None


def _calculate_duration_months(start_str: str | None, completion_str: str | None) -> float | None:
    start_m = _parse_date_to_months(start_str)
    comp_m = _parse_date_to_months(completion_str)
    if start_m is not None and comp_m is not None:
        diff = comp_m - start_m
        return max(1.0, diff)
    return None


def extract_features(study: dict[str, Any]) -> StudyFeatures:
    ps = study.get("protocolSection", {})
    ident = ps.get("identificationModule", {})
    design = ps.get("designModule", {})
    elig = ps.get("eligibilityModule", {})
    outcomes = ps.get("outcomesModule", {})
    arms_mod = ps.get("armsInterventionsModule", {})
    cond_mod = ps.get("conditionsModule", {})
    loc_mod = ps.get("contactsLocationsModule", {})
    oversight_mod = ps.get("oversightModule", {})
    desc_mod = ps.get("descriptionModule", {})
    design_info = design.get("designInfo", {})

    n_inc, n_exc, n_total = _count_criteria(elig.get("eligibilityCriteria", ""))

    locations = loc_mod.get("locations", [])
    countries = sorted({loc.get("country", "?") for loc in locations if loc.get("country")})

    conditions = cond_mod.get("conditions", [])
    is_onc, is_rare, area = _therapeutic_area(conditions)

    enrollment_info = design.get("enrollmentInfo", {})

    has_dmc = bool(oversight_mod.get("oversightHasDmc", False))
    is_fda = bool(oversight_mod.get("isFdaRegulatedDrug", False) or oversight_mod.get("isFdaRegulatedDevice", False))
    brief_summary = str(desc_mod.get("briefSummary", ""))
    summary_words = len(re.findall(r"\w+", brief_summary))
    n_interventions = len(arms_mod.get("interventions", []))

    status_mod = ps.get("statusModule", {})
    start_str = status_mod.get("startDateStruct", {}).get("date")
    comp_str = status_mod.get("completionDateStruct", {}).get("date")
    if not comp_str:
        comp_str = status_mod.get("primaryCompletionDateStruct", {}).get("date")
    duration = _calculate_duration_months(start_str, comp_str) or 24.0

    enrollment_val = int(enrollment_info.get("count", 0) or 0)
    sites_val = len(locations)
    velocity = enrollment_val / (max(1, sites_val) * duration) if enrollment_val > 0 else 0.0

    return StudyFeatures(
        nct_id=ident.get("nctId", "?"),
        brief_title=ident.get("briefTitle", ""),
        phase=_max_phase(design.get("phases", [])),
        study_type=design.get("studyType", "?"),
        n_eligibility_criteria=n_total,
        n_inclusion=n_inc,
        n_exclusion=n_exc,
        n_primary_endpoints=len(outcomes.get("primaryOutcomes", [])),
        n_secondary_endpoints=len(outcomes.get("secondaryOutcomes", [])),
        n_arms=len(arms_mod.get("armGroups", [])),
        enrollment=enrollment_val,
        n_sites=sites_val,
        n_countries=len(countries),
        allocation=design_info.get("allocation", "NA"),
        intervention_model=design_info.get("interventionModel", "NA"),
        masking=design_info.get("maskingInfo", {}).get("masking", "NA"),
        is_oncology=is_onc,
        is_rare_disease=is_rare,
        therapeutic_area=area,
        has_dmc=has_dmc,
        is_fda_regulated=is_fda,
        brief_summary_words=summary_words,
        n_conditions=max(1, len(conditions)),
        n_interventions=max(1, n_interventions),
        enrollment_velocity=velocity,
    )
