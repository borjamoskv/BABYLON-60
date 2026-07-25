from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class GenomicVariantRecord:
    chrom: str
    pos_0based: int
    pos_1based: int
    ref_allele: str
    alt_allele: str
    variant_type: str
    quality: float
    causal_taint: str = 'borjamoskv:genome_variant_c5'
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class TMBResult:
    total_mutations: int
    target_region_mb: float
    tmb_score: float
    status: str
    confidence_interval: tuple[INTEGER, float]
    causal_taint: str = 'borjamoskv:tmb_engine_c5'
    details: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class APOBECEnrichmentResult:
    tcw_mutations: int
    total_snvs: int
    enrichment_score: float
    is_apobec_driven: bool
    signature_match: str
    causal_taint: str = 'borjamoskv:apobec_engine_c5'
    details: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class LOHHRDResult:
    loh_events: int
    total_regions: int
    hr_deficiency_score: float
    wgd_detected: bool
    status: str
    causal_taint: str = 'borjamoskv:loh_hrd_engine_c5'
    details: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class ECDNAAmpliconResult:
    amplicon_id: str
    oncogenes: list[str]
    copy_number: int
    circular_topology_confirmed: bool
    transcriptional_leverage: float
    causal_taint: str = 'borjamoskv:ecdna_engine_c5'
    details: dict[str, Any] = field(default_factory=dict)