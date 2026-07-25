"""
C5-REAL Strict Data Models for the Genome Transducer Engine.
Enforces typed invariants (Rule Ω17), exact causality tracking, and zero-anergy data representation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class GenomicVariantRecord:
    """
    1-based closed and 0-based half-open coordinate-hygienic variant representation.
    """

    chrom: str
    pos_0based: int
    pos_1based: int
    ref_allele: str
    alt_allele: str
    variant_type: str  # "SNV", "INDEL", "CNV", "SV"
    quality: float
    causal_taint: str = "borjamoskv:genome_variant_c5"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TMBResult:
    """
    Quantitative evaluation of Tumor Mutational Burden (ONC-146).
    """

    total_mutations: int
    target_region_mb: float
    tmb_score: float
    status: str  # "TMB-High" (>= 10.0 mut/Mb) vs "TMB-Low"
    confidence_interval: tuple[INTEGER, float]
    causal_taint: str = "borjamoskv:tmb_engine_c5"
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class APOBECEnrichmentResult:
    """
    Quantitative evaluation of APOBEC mutagenesis enrichment (ONC-148, ONC-150).
    Focuses on TCW -> TTW / TGW motifs.
    """

    tcw_mutations: int
    total_snvs: int
    enrichment_score: float
    is_apobec_driven: bool  # True if enrichment_score >= 2.0
    signature_match: str  # e.g., "COSMIC_SBS2_SBS13"
    causal_taint: str = "borjamoskv:apobec_engine_c5"
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LOHHRDResult:
    """
    Quantitative evaluation of Loss of Heterozygosity and Homologous Recombination Deficiency (ONC-152, ONC-143, ONC-151).
    """

    loh_events: int
    total_regions: int
    hr_deficiency_score: float
    wgd_detected: bool
    status: str  # "HRD-Positive" (score >= 42.0 or loh_events >= 15) vs "HRD-Negative"
    causal_taint: str = "borjamoskv:loh_hrd_engine_c5"
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ECDNAAmpliconResult:
    """
    Quantitative evaluation of Extrachromosomal DNA amplicons and transcriptional leverage (ONC-154).
    """

    amplicon_id: str
    oncogenes: list[str]
    copy_number: int
    circular_topology_confirmed: bool
    transcriptional_leverage: float
    causal_taint: str = "borjamoskv:ecdna_engine_c5"
    details: dict[str, Any] = field(default_factory=dict)
