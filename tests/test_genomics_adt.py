"""
C5-REAL Algebraic Data Type and Clonal Entropy tests.
Verifies the strict invariants of Genomic Profile ADTs, Monadic Results, and Shannon entropy (Ω31).
"""

import pytest
from babylon60.types.algebraic import (
    Ok, Err, Result, AlgebraicCardinality, make_illegal_states_unrepresentable
)
from babylon60.genomics.adt import (
    VCF1Based, CoordinateSystem,
    SNV, AlgebraicGenomicVariant
)
from babylon60.genomics.engine import GenomicEvaluationEngine

def test_algebraic_cardinality():
    """Verify combinatorial cardinality bounds."""
    # Coordinate system: |BED| + |VCF|
    assert AlgebraicCardinality.sum_type_cardinality(1, 1) == 2
    # Product: Boolean state per gene (2 ^ N)
    assert AlgebraicCardinality.exponential_type_cardinality(domain_cardinality=3, codomain_cardinality=2) == 8

def test_result_monad():
    """Verify Monadic Result bindings."""
    success: Result[int, str] = Ok(42)
    failure: Result[int, str] = Err("C5-FAIL")
    
    assert isinstance(success, Ok)
    assert success.value == 42
    assert isinstance(failure, Err)
    assert failure.error == "C5-FAIL"

def test_genomic_adts():
    """Verify algebraic construction of genomic primitives makes illegal states unrepresentable."""
    coord: CoordinateSystem = VCF1Based(chrom="chr1", pos=12345, ref_len=1)
    var = SNV(ref="A", alt="T")
    
    # Strictly constructed variant
    alg_var = AlgebraicGenomicVariant(
        coordinate=coord,
        variant=var,
        quality=99.9
    )
    assert isinstance(alg_var.coordinate, VCF1Based)
    assert isinstance(alg_var.variant, SNV)

def test_clonal_entropy_omega31():
    """Verify Rule Ω31 Shannon entropy computation on subclonal structures."""
    # 3 subclones with normalized distribution [0.5, 0.25, 0.25]
    res = GenomicEvaluationEngine.evaluate_clonal_entropy([0.5, 0.25, 0.25])
    assert res.subclone_count == 3
    # S = -(0.5*ln(0.5) + 0.25*ln(0.25) + 0.25*ln(0.25)) = 1.0397
    assert res.shannon_entropy == 1.0397
    
    # Single clone (S = 0)
    res2 = GenomicEvaluationEngine.evaluate_clonal_entropy([1.0])
    assert res2.subclone_count == 1
    assert res2.shannon_entropy == 0.0

def test_clonal_entropy_empty_and_invalid():
    """Verify robustness of clonal entropy under edge cases."""
    # Empty subclone array
    res = GenomicEvaluationEngine.evaluate_clonal_entropy([])
    assert res.subclone_count == 0
    assert res.shannon_entropy == 0.0
    
    # Zeroes and negatives are filtered
    res2 = GenomicEvaluationEngine.evaluate_clonal_entropy([1.0, 0.0, -0.5])
    assert res2.subclone_count == 1
    assert res2.shannon_entropy == 0.0
    
    with pytest.raises(TypeError):
        GenomicEvaluationEngine.evaluate_clonal_entropy("illegal_type")  # type: ignore

def test_make_illegal_states_unrepresentable():
    """Verify unreachable match branches fail appropriately."""
    with pytest.raises(RuntimeError) as exc:
        make_illegal_states_unrepresentable("Some Rogue State")
    assert "Reached unreachable algebraic state" in str(exc.value)
