"""
C5-REAL Genomics Transducer Package (`babylon60.genomics`).
Provides quantitative biomarker evaluation (TMB, APOBEC, HRD, ecDNA), coordinate hygiene,
sequence validation, and state transduction into the 300-primitive oncological Boolean network.
"""

from .engine import GenomicEvaluationEngine
from .hygiene import (
    FASTASequenceValidator,
    GenomeCoordinateHygiene,
)
from .models import (
    APOBECEnrichmentResult,
    ECDNAAmpliconResult,
    GenomicVariantRecord,
    LOHHRDResult,
    TMBResult,
)
from .transducer import GenomicStateTransducer

__all__ = [
    "GenomicVariantRecord",
    "TMBResult",
    "APOBECEnrichmentResult",
    "LOHHRDResult",
    "ECDNAAmpliconResult",
    "GenomeCoordinateHygiene",
    "FASTASequenceValidator",
    "GenomicEvaluationEngine",
    "GenomicStateTransducer",
]
