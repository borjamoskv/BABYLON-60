"""
C5-REAL Genomic Algebraic Data Types (ADTs).
Replaces string-typed genomic models with rigorous Sum and Product Types.
Makes genomic illegal states (e.g., TMB-High without score) physically unrepresentable.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Union, Any
from babylon60.types.algebraic import Result, Option

# 1. Coordinate System Sum Type (|Coord| = |BED| + |VCF|)
@dataclass(frozen=True)
class BED0Based:
    """0-based half-open interval [start, end)"""
    chrom: str
    start: int
    end: int

@dataclass(frozen=True)
class VCF1Based:
    """1-based closed interval [pos, pos + ref_len - 1]"""
    chrom: str
    pos: int
    ref_len: int

CoordinateSystem = Union[BED0Based, VCF1Based]

# 2. Variant Type Sum Type
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
    sv_type: str  # e.g., "BND", "INV"
    breakpoint_info: dict[str, Any]

VariantType = Union[SNV, INDEL, CNV, StructuralVariant]

# 3. Product Type for an exact Variant Record
@dataclass(frozen=True)
class AlgebraicGenomicVariant:
    coordinate: CoordinateSystem
    variant: VariantType
    quality: float
    causal_taint: str = "borjamoskv:algebraic_variant_c5"
    metadata: dict[str, Any] = field(default_factory=dict)

# 4. TMB Sum Type
@dataclass(frozen=True)
class TMBHigh:
    score: float
    confidence_interval: tuple[float, float]
    details: dict[str, Any]

@dataclass(frozen=True)
class TMBLow:
    score: float
    confidence_interval: tuple[float, float]
    details: dict[str, Any]

@dataclass(frozen=True)
class TMBIndeterminate:
    reason: str

TMBClassification = Union[TMBHigh, TMBLow, TMBIndeterminate]

# 5. APOBEC Sum Type
@dataclass(frozen=True)
class APOBECDriven:
    tcw_mutations: int
    enrichment_score: float
    signature_match: str

@dataclass(frozen=True)
class APOBECBackground:
    tcw_mutations: int
    enrichment_score: float

APOBECStatus = Union[APOBECDriven, APOBECBackground]

# 6. HRD Sum Type
@dataclass(frozen=True)
class HRDPositive:
    hr_deficiency_score: float
    loh_events: int
    wgd_detected: bool

@dataclass(frozen=True)
class HRDNegative:
    hr_deficiency_score: float
    loh_events: int

HRDStatus = Union[HRDPositive, HRDNegative]

# 7. Clonal Entropy Product Type (Rule Ω31)
@dataclass(frozen=True)
class ClonalEntropyResult:
    shannon_entropy: float  # S = -sum(p_i * ln(p_i))
    subclone_count: int
    causal_taint: str = "borjamoskv:clonal_entropy_c5"

# 8. Full Algebraic Profile
@dataclass(frozen=True)
class GenomicProfileADT:
    variants: list[AlgebraicGenomicVariant]
    tmb: TMBClassification
    apobec: APOBECStatus
    hrd: HRDStatus
    clonal_entropy: Option[ClonalEntropyResult]
    causal_taint: str = "borjamoskv:algebraic_genomic_profile_c5"

# 9. Errors
@dataclass(frozen=True)
class SequenceCorruption:
    sha3_seal: str
    details: str

@dataclass(frozen=True)
class CoordinateMismatch:
    msg: str

GenomicVerificationError = Union[SequenceCorruption, CoordinateMismatch]
GenomicEvaluationResult = Result[GenomicProfileADT, GenomicVerificationError]
