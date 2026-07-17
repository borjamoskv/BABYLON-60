"""
C5-REAL Verification Suite for `babylon60.genomics`.
Tests coordinate hygiene (BED vs VCF), FASTA validation, quantitative calculations (TMB, APOBEC, HRD, ecDNA),
and transduction directly into the 300-primitive Boolean network state matrix.
"""

import pytest
import networkx as nx
from babylon60.genomics import (
    GenomicVariantRecord,
    TMBResult,
    APOBECEnrichmentResult,
    LOHHRDResult,
    ECDNAAmpliconResult,
    GenomeCoordinateHygiene,
    FASTASequenceValidator,
    GenomicEvaluationEngine,
    GenomicStateTransducer,
)
from babylon60.cli.onco_transducer import simulate_boolean_network


def test_coordinate_hygiene_bed_vcf_conversions() -> None:
    """Test 0-based half-open (BED) vs 1-based closed (VCF) exact coordinate conversions."""
    chrom, start_1b, end_1b = GenomeCoordinateHygiene.bed_to_vcf("1", 100, 105)
    assert chrom == "chr1"
    assert start_1b == 101
    assert end_1b == 105

    chrom2, start_0b, end_0b = GenomeCoordinateHygiene.vcf_to_bed("ChrX", 101, ref_len=5)
    assert chrom2 == "chrX"
    assert start_0b == 100
    assert end_0b == 105

    with pytest.raises(ValueError):
        GenomeCoordinateHygiene.bed_to_vcf("chr1", 100, 100)  # Invalid interval start >= end


def test_fasta_sequence_validation_and_crypto_hash() -> None:
    """Test FASTA sequence validation, GC content calculation, and SHA3-256 seal generation."""
    seq = "ACGTACGTACGT"
    val = FASTASequenceValidator.validate_sequence("seq_001", seq, quality_scores="IIIIIIIIIIII")
    assert val["is_valid"] is True
    assert val["length"] == 12
    assert val["gc_content"] == 0.5
    assert len(val["sha3_256"]) == 64  # SHA3-256 hexdigest length
    assert val["causal_taint"] == "borjamoskv:fasta_validator_c5"

    with pytest.raises(ValueError):
        FASTASequenceValidator.validate_sequence("seq_bad", "ACGTZZZ")  # Invalid character Z


def test_tmb_evaluation_engine() -> None:
    """Test quantitative TMB calculation across target footprint."""
    variants = [
        GenomicVariantRecord(
            chrom="chr1",
            pos_0based=1000 + i,
            pos_1based=1001 + i,
            ref_allele="A",
            alt_allele="G",
            variant_type="SNV",
            quality=40.0,
            metadata={"gene": "TP53" if i == 0 else "GENE_X"}
        )
        for i in range(400)  # 400 mutations over 38 Mb = ~10.52 mut/Mb (TMB-High)
    ]
    res: TMBResult = GenomicEvaluationEngine.evaluate_tmb(variants, target_region_mb=38.0)
    assert res.total_mutations == 400
    assert res.status == "TMB-High"
    assert res.tmb_score > 10.0
    assert res.confidence_interval[0] < res.tmb_score < res.confidence_interval[1]


def test_apobec_enrichment_engine() -> None:
    """Test APOBEC motif enrichment (TCW -> TTW / TGW) scoring."""
    variants = [
        GenomicVariantRecord(
            chrom="chr1",
            pos_0based=2000 + i,
            pos_1based=2001 + i,
            ref_allele="C",
            alt_allele="T",
            variant_type="SNV",
            quality=35.0,
            metadata={"trinucleotide_context": "TCA"}  # TCW motif
        )
        for i in range(10)
    ] + [
        GenomicVariantRecord(
            chrom="chr2",
            pos_0based=3000 + i,
            pos_1based=3001 + i,
            ref_allele="A",
            alt_allele="G",
            variant_type="SNV",
            quality=35.0,
            metadata={"trinucleotide_context": "AAA"}
        )
        for i in range(5)
    ]
    res: APOBECEnrichmentResult = GenomicEvaluationEngine.evaluate_apobec_enrichment(variants)
    assert res.tcw_mutations == 10
    assert res.total_snvs == 15
    assert res.is_apobec_driven is True
    assert res.signature_match == "COSMIC_SBS2_SBS13"


def test_loh_hrd_and_ecdna_engine() -> None:
    """Test HRD scoring and ecDNA transcriptional leverage calculations."""
    hrd: LOHHRDResult = GenomicEvaluationEngine.evaluate_loh_hrd(loh_events=16, total_regions=30, wgd_detected=True)
    assert hrd.wgd_detected is True
    assert hrd.status == "HRD-Positive"
    assert hrd.hr_deficiency_score >= 42.0

    ecdna: ECDNAAmpliconResult = GenomicEvaluationEngine.evaluate_ecdna_amplicon(
        amplicon_id="AMP_MYC_01",
        oncogenes=["MYC", "PVT1"],
        copy_number=25,
        circular_confirmed=True,
        rna_fold_change=150.0
    )
    assert ecdna.amplicon_id == "AMP_MYC_01"
    assert "MYC" in ecdna.oncogenes
    assert ecdna.circular_topology_confirmed is True
    assert ecdna.transcriptional_leverage > 6.0


def test_genomic_transducer_integration_with_oncology_transducer() -> None:
    """Verify that multi-scale genomic profiles transduce into exact primitive activations and execute cleanly in OncologyTransducer."""
    variants = [
        GenomicVariantRecord("chr17", 7673766, 7673767, "C", "T", "SNV", 45.0, metadata={"gene": "TP53"}),
        GenomicVariantRecord("chr17", 43044294, 43044295, "G", "A", "SNV", 45.0, metadata={"gene": "BRCA1"}),
        GenomicVariantRecord("chr7", 55242464, 55242465, "T", "G", "SNV", 50.0, metadata={"gene": "EGFR"}),
    ] + [
        GenomicVariantRecord("chr1", 10000 + i, 10001 + i, "C", "T", "SNV", 35.0, metadata={"trinucleotide_context": "TCA"})
        for i in range(400)
    ]

    profile = GenomicStateTransducer.transduce_full_profile(
        variants=variants,
        loh_events=20,
        total_regions=35,
        wgd_detected=True,
        ecdna_records=[{
            "amplicon_id": "AMP_MYC_CIRC",
            "oncogenes": ["MYC"],
            "copy_number": 30,
            "circular_confirmed": True,
            "rna_fold_change": 200.0
        }]
    )

    state_matrix = profile["state_matrix"]
    assert state_matrix.get("ONC-046") == 1  # TP53 primitive
    assert state_matrix.get("ONC-151") == 1  # BRCA1 primitive
    assert state_matrix.get("ONC-017") == 1  # EGFR primitive
    assert state_matrix.get("ONC-019") == 1  # MYC primitive (from ecDNA)
    assert state_matrix.get("ONC-146") == 1  # TMB-High node
    assert state_matrix.get("ONC-148") == 1  # APOBEC signature node
    assert state_matrix.get("ONC-143") == 1  # HRD node
    assert state_matrix.get("ONC-154") == 1  # ecDNA amplification node

    # Verify execution inside Boolean network simulation (`simulate_boolean_network`)
    G = nx.DiGraph()
    # Create directed edges among activated oncogenic/suppressor nodes to model causal propagation
    G.add_edges_from([
        ("ONC-046", "ONC-143"),  # TP53 loss promotes HRD / DDR instability
        ("ONC-143", "ONC-146"),  # HRD promotes TMB-High
        ("ONC-017", "ONC-019"),  # EGFR kinase signaling drives MYC transcription
        ("ONC-154", "ONC-019")   # ecDNA amplicon reinforces MYC activation
    ])

    history, nodes = simulate_boolean_network(G, state_matrix, steps=3)
    assert len(history) >= 2
    assert "ONC-046" in nodes
    # Ensure initial state vector preserved node activations
    assert history[0][nodes.index("ONC-046")] == 1
    assert history[0][nodes.index("ONC-019")] == 1
