"""
C5-REAL Algebraic Data Type and Clonal Entropy tests.
Verifies the strict invariants of Genomic Profile ADTs, Monadic Results, and Shannon entropy (Ω31).
"""

import pytest

from babylon60.genomics.adt import SNV, AlgebraicGenomicVariant, CoordinateSystem, VCF1Based
from babylon60.genomics.engine import GenomicEvaluationEngine
from babylon60.types.algebraic import AlgebraicCardinality, Err, Ok, Result, make_illegal_states_unrepresentable


def test_algebraic_cardinality() -> None:
    """Verify combinatorial cardinality bounds."""
    assert AlgebraicCardinality.sum_type_cardinality(1, 1) == 2
    assert AlgebraicCardinality.exponential_type_cardinality(domain_cardinality=3, codomain_cardinality=2) == 8


def test_result_monad() -> None:
    """Verify Monadic Result bindings."""
    success: Result[int, str] = Ok(42)
    failure: Result[int, str] = Err("C5-FAIL")

    assert isinstance(success, Ok)
    assert success.value == 42
    assert isinstance(failure, Err)
    assert failure.error == "C5-FAIL"


def test_genomic_adts() -> None:
    """Verify algebraic construction of genomic primitives makes illegal states unrepresentable."""
    coord: CoordinateSystem = VCF1Based(chrom="chr1", pos=12345, ref_len=1)
    var = SNV(ref="A", alt="T")

    alg_var = AlgebraicGenomicVariant(coordinate=coord, variant=var, quality=99.9)
    assert isinstance(alg_var.coordinate, VCF1Based)
    assert isinstance(alg_var.variant, SNV)


def test_clonal_entropy_omega31() -> None:
    """Verify Rule Ω31 Shannon entropy computation on subclonal structures."""
    res = GenomicEvaluationEngine.evaluate_clonal_entropy([0.5, 0.25, 0.25])
    assert res.subclone_count == 3
    assert res.shannon_entropy == 1.0397

    res2 = GenomicEvaluationEngine.evaluate_clonal_entropy([1.0])
    assert res2.subclone_count == 1
    assert res2.shannon_entropy == 0.0


def test_clonal_entropy_empty_and_invalid() -> None:
    """Verify robustness of clonal entropy under edge cases."""
    res = GenomicEvaluationEngine.evaluate_clonal_entropy([])
    assert res.subclone_count == 0
    assert res.shannon_entropy == 0.0

    res2 = GenomicEvaluationEngine.evaluate_clonal_entropy([1.0, 0.0, -0.5])
    assert res2.subclone_count == 1
    assert res2.shannon_entropy == 0.0

    with pytest.raises(TypeError):
        GenomicEvaluationEngine.evaluate_clonal_entropy("illegal_type")  # type: ignore


def test_make_illegal_states_unrepresentable() -> None:
    """Verify unreachable match branches fail appropriately."""
    with pytest.raises(RuntimeError) as exc:
        make_illegal_states_unrepresentable("Some Rogue State")  # type: ignore
    assert "Reached unreachable algebraic state" in str(exc.value)
