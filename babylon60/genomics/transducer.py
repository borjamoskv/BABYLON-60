from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .engine import GenomicEvaluationEngine
from .models import APOBECEnrichmentResult, ECDNAAmpliconResult, GenomicVariantRecord, LOHHRDResult, TMBResult


@dataclass
class FullProfileParams:
    variants: list[GenomicVariantRecord]
    loh_events: int
    total_regions: int
    wgd_detected: bool = False
    ecdna_records: list[dict[str, Any]] | None = None
    base_state: dict[str, int] | None = None
    target_region_mb: float = 38.0


class GenomicStateTransducer:
    GENE_TO_PRIMITIVE_MAP: dict[str, str] = {
        "TP53": "ONC-046",
        "BRCA1": "ONC-151",
        "BRCA2": "ONC-152",
        "ATM": "ONC-136",
        "ATR": "ONC-137",
        "EGFR": "ONC-017",
        "KRAS": "ONC-018",
        "MYC": "ONC-019",
        "PIK3CA": "ONC-020",
        "PTEN": "ONC-047",
        "TERT": "ONC-163",
    }

    @classmethod
    def transduce_variant_records(
        cls,
        variants: list[GenomicVariantRecord],
        base_state: dict[str, int] | None = None,
        target_region_mb: float = 38.0,
    ) -> dict[str, Any]:
        if not isinstance(variants, list):
            raise TypeError("[C5-FAIL] variants must be provided as a list.")
        state: dict[str, int] = dict(base_state) if base_state is not None else {}
        tmb_res: TMBResult = GenomicEvaluationEngine.evaluate_tmb(variants, target_region_mb=target_region_mb)
        if tmb_res.status == "TMB-High":
            state["ONC-146"] = 1
        apobec_res: APOBECEnrichmentResult = GenomicEvaluationEngine.evaluate_apobec_enrichment(variants)
        if apobec_res.is_apobec_driven:
            state["ONC-148"] = 1
            state["ONC-150"] = 1
        mutated_genes: set[str] = set()
        for v in variants:
            gene = str(v.metadata.get("gene", "")).upper()
            if gene in cls.GENE_TO_PRIMITIVE_MAP:
                prim_id = cls.GENE_TO_PRIMITIVE_MAP[gene]
                state[prim_id] = 1
                mutated_genes.add(gene)
        return {
            "state_matrix": state,
            "tmb_result": tmb_res,
            "apobec_result": apobec_res,
            "mutated_genes": sorted(mutated_genes),
            "causal_taint": "borjamoskv:genomic_state_transducer_c5",
        }

    @classmethod
    def transduce_full_profile(
        cls,
        params: FullProfileParams | None = None,
        *,
        variants: list[GenomicVariantRecord] | None = None,
        loh_events: int = 0,
        total_regions: int = 1,
        wgd_detected: bool = False,
        ecdna_records: list[dict[str, Any]] | None = None,
        base_state: dict[str, int] | None = None,
        target_region_mb: float = 38.0,
    ) -> dict[str, Any]:
        if params is None:
            if variants is None:
                raise ValueError("[C5-FAIL] Either params or variants must be provided.")
            params = FullProfileParams(
                variants=variants,
                loh_events=loh_events,
                total_regions=total_regions,
                wgd_detected=wgd_detected,
                ecdna_records=ecdna_records,
                base_state=base_state,
                target_region_mb=target_region_mb,
            )
        base_transduction = cls.transduce_variant_records(
            params.variants, base_state=params.base_state, target_region_mb=params.target_region_mb
        )
        state_matrix: dict[str, int] = base_transduction["state_matrix"]
        hrd_res: LOHHRDResult = GenomicEvaluationEngine.evaluate_loh_hrd(
            params.loh_events, params.total_regions, wgd_detected=params.wgd_detected
        )
        if hrd_res.status == "HRD-Positive":
            state_matrix["ONC-143"] = 1
            if hrd_res.wgd_detected:
                state_matrix["ONC-145"] = 1
        ecdna_results: list[ECDNAAmpliconResult] = []
        if params.ecdna_records:
            if not isinstance(params.ecdna_records, list):
                raise TypeError("[C5-FAIL] ecdna_records must be a list of dictionaries.")
            for rec in params.ecdna_records:
                amp_res = GenomicEvaluationEngine.evaluate_ecdna_amplicon(
                    amplicon_id=str(rec["amplicon_id"]),
                    oncogenes=list(rec["oncogenes"]),
                    copy_number=int(rec["copy_number"]),
                    circular_confirmed=bool(rec["circular_confirmed"]),
                    rna_fold_change=float(rec["rna_fold_change"]),
                )
                ecdna_results.append(amp_res)
                if amp_res.transcriptional_leverage >= 5.0 or amp_res.copy_number >= 10:
                    state_matrix["ONC-154"] = 1
                    for g in amp_res.oncogenes:
                        gene_upper = g.upper()
                        if gene_upper in cls.GENE_TO_PRIMITIVE_MAP:
                            state_matrix[cls.GENE_TO_PRIMITIVE_MAP[gene_upper]] = 1
        return {
            "state_matrix": state_matrix,
            "tmb_result": base_transduction["tmb_result"],
            "apobec_result": base_transduction["apobec_result"],
            "hrd_result": hrd_res,
            "ecdna_results": ecdna_results,
            "mutated_genes": base_transduction["mutated_genes"],
            "causal_taint": "borjamoskv:full_genomic_profile_transducer_c5",
        }
