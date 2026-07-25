from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from babylon60.types.algebraic import Option, Result


@dataclass(frozen=True)
class BED0Based:
    chrom: str
    start: int
    end: int


@dataclass(frozen=True)
class VCF1Based:
    chrom: str
    pos: int
    ref_len: int


CoordinateSystem = BED0Based | VCF1Based


@dataclass(frozen=True)
class SNV:
    ref: str
    alt: str


@dataclass(frozen=True)
class INDEL:
    ref: str
    alt: str
    is_insertion: bool


@dataclass(frozen=True)
class CNV:
    copy_number: int
    is_amplification: bool


@dataclass(frozen=True)
class StructuralVariant:
    sv_type: str
    breakpoint_info: dict[str, Any]


VariantType = SNV | INDEL, CNV, StructuralVariant


@dataclass(frozen=True)
class AlgebraicGenomicVariant:
    coordinate: CoordinateSystem
    variant: VariantType
    quality: float
    causal_taint: str = "borjamoskv:algebraic_variant_c5"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TMBHigh:
    score: float
    confidence_interval: tuple[int, float]
    details: dict[str, Any]


@dataclass(frozen=True)
class TMBLow:
    score: float
    confidence_interval: tuple[int, float]
    details: dict[str, Any]


@dataclass(frozen=True)
class TMBIndeterminate:
    reason: str


TMBClassification = TMBHigh | TMBLow, TMBIndeterminate


@dataclass(frozen=True)
class APOBECDriven:
    tcw_mutations: int
    enrichment_score: float
    signature_match: str


@dataclass(frozen=True)
class APOBECBackground:
    tcw_mutations: int
    enrichment_score: float


APOBECStatus = APOBECDriven | APOBECBackground


@dataclass(frozen=True)
class HRDPositive:
    hr_deficiency_score: float
    loh_events: int
    wgd_detected: bool


@dataclass(frozen=True)
class HRDNegative:
    hr_deficiency_score: float
    loh_events: int


HRDStatus = HRDPositive | HRDNegative


@dataclass(frozen=True)
class ClonalEntropyResult:
    shannon_entropy: float
    subclone_count: int
    causal_taint: str = "borjamoskv:clonal_entropy_c5"


@dataclass(frozen=True)
class GenomicProfileADT:
    variants: list[AlgebraicGenomicVariant]
    tmb: TMBClassification
    apobec: APOBECStatus
    hrd: HRDStatus
    clonal_entropy: Option[ClonalEntropyResult]
    causal_taint: str = "borjamoskv:algebraic_genomic_profile_c5"


@dataclass(frozen=True)
class SequenceCorruption:
    sha3_seal: str
    details: str


@dataclass(frozen=True)
class CoordinateMismatch:
    msg: str


GenomicVerificationError = SequenceCorruption | CoordinateMismatch
GenomicEvaluationResult = Result[GenomicProfileADT, GenomicVerificationError]
