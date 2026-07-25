from __future__ import annotations
import math
from .adt import ClonalEntropyResult
from .models import APOBECEnrichmentResult, ECDNAAmpliconResult, GenomicVariantRecord, LOHHRDResult, TMBResult

class GenomicEvaluationEngine:

    @staticmethod
    def evaluate_clonal_entropy(allele_frequencies: list[float]) -> ClonalEntropyResult:
        if not isinstance(allele_frequencies, list):
            raise TypeError('[C5-FAIL] Allele frequencies must be a list.')
        valid_afs = [f for f in allele_frequencies if isinstance(f, (int, float)) and f > 0.0]
        if not valid_afs:
            return ClonalEntropyResult(shannon_entropy=0.0, subclone_count=0)
        total_freq = sum(valid_afs)
        normalized_probs = [f / total_freq for f in valid_afs]
        entropy = -sum((p * math.log(p) for p in normalized_probs))
        return ClonalEntropyResult(shannon_entropy=round(entropy, 4), subclone_count=len(valid_afs))

    @staticmethod
    def evaluate_tmb(variants: list[GenomicVariantRecord], target_region_mb: float=38.0) -> TMBResult:
        if not isinstance(target_region_mb, (int, float)) or target_region_mb <= 0.0:
            raise ValueError(f'[C5-FAIL] Target region size must be positive, got: {target_region_mb}')
        if not isinstance(variants, list):
            raise TypeError('[C5-FAIL] Variants must be provided as a list.')
        coding_muts = [v for v in variants if v.variant_type in ('SNV', 'INDEL') and v.quality >= 30.0]
        total_muts = len(coding_muts)
        tmb_score = float(total_muts) / float(target_region_mb)
        status = 'TMB-High' if tmb_score >= 10.0 else 'TMB-Low'
        std_err = math.sqrt(float(total_muts)) / float(target_region_mb) if total_muts > 0 else 0.0
        ci_low = max(0.0, tmb_score - 1.96 * std_err)
        ci_high = tmb_score + 1.96 * std_err
        return TMBResult(total_mutations=total_muts, target_region_mb=float(target_region_mb), tmb_score=round(tmb_score, 4), status=status, confidence_interval=(round(ci_low, 4), round(ci_high, 4)), causal_taint='borjamoskv:tmb_evaluator_c5', details={'snv_count': sum((1 for v in coding_muts if v.variant_type == 'SNV')), 'indel_count': sum((1 for v in coding_muts if v.variant_type == 'INDEL'))})

    @staticmethod
    def evaluate_apobec_enrichment(variants: list[GenomicVariantRecord], trinucleotide_context: dict[str, str] | None=None) -> APOBECEnrichmentResult:
        if not isinstance(variants, list):
            raise TypeError('[C5-FAIL] Variants must be provided as a list.')
        snvs = [v for v in variants if v.variant_type == 'SNV']
        total_snvs = len(snvs)
        if total_snvs == 0:
            return APOBECEnrichmentResult(tcw_mutations=0, total_snvs=0, enrichment_score=0.0, is_apobec_driven=False, signature_match='NONE', causal_taint='borjamoskv:apobec_evaluator_c5', details={'reason': 'No somatic SNVs present in cohort'})
        tcw_muts = 0
        for idx, v in enumerate(snvs):
            var_key = f'{v.chrom}:{v.pos_1based}'
            motif = ''
            if trinucleotide_context and var_key in trinucleotide_context:
                motif = trinucleotide_context[var_key].upper()
            elif 'trinucleotide_context' in v.metadata:
                motif = str(v.metadata['trinucleotide_context']).upper()
            else:
                if v.ref_allele == 'C' and v.alt_allele in ('T', 'G') or (v.ref_allele == 'G' and v.alt_allele in ('A', 'C')):
                    if v.metadata.get('apobec_motif', False):
                        tcw_muts += 1
                continue
            if len(motif) == 3 and motif[1] == 'C' and (motif[2] in ('A', 'T')):
                if v.ref_allele == 'C' and v.alt_allele in ('T', 'G'):
                    tcw_muts += 1
            elif len(motif) == 3 and motif[1] == 'G' and (motif[0] in ('A', 'T')):
                if v.ref_allele == 'G' and v.alt_allele in ('A', 'C'):
                    tcw_muts += 1
        observed_fraction = float(tcw_muts) / float(total_snvs)
        enrichment_score = observed_fraction / 0.16 if total_snvs >= 5 else 0.0
        is_driven = enrichment_score >= 2.0 and tcw_muts >= 3
        return APOBECEnrichmentResult(tcw_mutations=tcw_muts, total_snvs=total_snvs, enrichment_score=round(enrichment_score, 4), is_apobec_driven=is_driven, signature_match='COSMIC_SBS2_SBS13' if is_driven else 'BACKGROUND', causal_taint='borjamoskv:apobec_evaluator_c5', details={'observed_tcw_fraction': round(observed_fraction, 4), 'expected_baseline': 0.16})

    @staticmethod
    def evaluate_loh_hrd(loh_events: int, total_regions: int, wgd_detected: bool=False) -> LOHHRDResult:
        if not isinstance(loh_events, int) or not isinstance(total_regions, int):
            raise TypeError('[C5-FAIL] LOH events and total regions must be integers.')
        if loh_events < 0 or total_regions <= 0 or loh_events > total_regions:
            raise ValueError(f'[C5-FAIL] Invalid LOH regions: loh_events={loh_events}, total_regions={total_regions}')
        loh_fraction = float(loh_events) / float(total_regions)
        hrd_score = float(loh_events) * 2.8 + (10.0 if wgd_detected else 0.0)
        status = 'HRD-Positive' if hrd_score >= 42.0 or loh_events >= 15 else 'HRD-Negative'
        return LOHHRDResult(loh_events=loh_events, total_regions=total_regions, hr_deficiency_score=round(hrd_score, 2), wgd_detected=bool(wgd_detected), status=status, causal_taint='borjamoskv:loh_hrd_evaluator_c5', details={'loh_fraction': round(loh_fraction, 4), 'wgd_penalty_applied': 10.0 if wgd_detected else 0.0})

    @staticmethod
    def evaluate_ecdna_amplicon(amplicon_id: str, oncogenes: list[str], copy_number: int, circular_confirmed: bool, rna_fold_change: float) -> ECDNAAmpliconResult:
        if not amplicon_id or not isinstance(amplicon_id, str):
            raise ValueError('[C5-FAIL] Amplicon ID must be a non-empty string.')
        if not isinstance(oncogenes, list) or not all((isinstance(g, str) for g in oncogenes)):
            raise TypeError('[C5-FAIL] Oncogenes must be a list of strings.')
        if not isinstance(copy_number, int) or copy_number < 1:
            raise ValueError(f'[C5-FAIL] Copy number must be >= 1, got: {copy_number}')
        if not isinstance(rna_fold_change, (int, float)) or rna_fold_change < 0.0:
            raise ValueError(f'[C5-FAIL] RNA fold change must be non-negative, got: {rna_fold_change}')
        leverage = float(rna_fold_change) / float(copy_number) if copy_number > 1 else float(rna_fold_change)
        if circular_confirmed:
            leverage *= 1.35
        return ECDNAAmpliconResult(amplicon_id=amplicon_id, oncogenes=list(oncogenes), copy_number=copy_number, circular_topology_confirmed=bool(circular_confirmed), transcriptional_leverage=round(leverage, 4), causal_taint='borjamoskv:ecdna_evaluator_c5', details={'raw_fold_change': float(rna_fold_change), 'circular_enhancer_boost': 1.35 if circular_confirmed else 1.0})