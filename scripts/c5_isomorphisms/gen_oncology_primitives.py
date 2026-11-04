#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any

DISCLAIMER_ES = "AVISO. Esto es una ONTOLOGIA DE CONOCIMIENTO de biologia molecular del cancer y de sus dianas terapeuticas: los bloques fundamentales que la investigacion oncologica estudia y ataca. NO es una cura, NO es un protocolo de tratamiento y NO es consejo medico. Ninguna primitiva individual ni el conjunto 'curan el cancer'. El cancer no es una sola enfermedad sino mas de 200 enfermedades distintas; el diagnostico y el tratamiento son clinicos, individualizados y competencia de oncologos e investigadores. Cualquier decision medica debe tomarse con profesionales sanitarios."
DISCLAIMER_EN = "NOTICE. This is a KNOWLEDGE ONTOLOGY of cancer molecular biology and its therapeutic targets. It is NOT a cure, NOT a treatment protocol and NOT medical advice. No single primitive nor the whole set 'cures cancer'. Cancer is 200+ distinct diseases; diagnosis and treatment are clinical and individualized. Consult qualified healthcare professionals."
CATS = {
    "hallmark": ("Hallmarks del cancer", "meta"),
    "oncogene": ("Oncogenes", "molecular"),
    "suppressor": ("Genes supresores de tumores", "molecular"),
    "pathway": ("Vias de senalizacion", "pathway"),
    "cellcycle": ("Ciclo celular y checkpoints", "cellular"),
    "apoptosis": ("Apoptosis y muerte celular regulada", "cellular"),
    "ddr": ("Respuesta al dano y reparacion de ADN", "molecular"),
    "genome": ("Inestabilidad genomica y mutagenesis", "molecular"),
    "telomere": ("Telomeros, senescencia e inmortalidad", "cellular"),
    "angio": ("Angiogenesis", "cellular"),
    "metastasis": ("Invasion, EMT y metastasis", "cellular"),
    "metabolism": ("Metabolismo tumoral", "molecular"),
    "epigenetic": ("Epigenetica y cromatina", "molecular"),
    "tme": ("Microambiente tumoral (TME)", "tissue"),
    "immuno": ("Inmuno-oncologia y evasion inmune", "tissue"),
    "modality": ("Modalidades terapeuticas", "therapy"),
    "drug": ("Primitivas farmaco -> diana", "therapy"),
}
R_HW00 = "Hanahan & Weinberg, Cell 2000"
R_HW11 = "Hanahan & Weinberg, Cell 2011"
R_H22 = "Hanahan, Cancer Discov 2022 (New Dimensions)"
R_WBC = "Weinberg RA, The Biology of Cancer, 2nd ed. 2014"
R_VOG = "Vogelstein et al., Science 2013 (Cancer Genome Landscapes)"

_CATALOG_PATH = Path(__file__).resolve().parent / "oncology_primitives_catalog.json"
PRIMS: list[tuple[str, str, str, str, str, str]] = [
    tuple(item) for item in json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))
]

GENOME_MECHANICS: dict[str, dict[str, Any]] = {
    "ONC-143": {
        "coordinate_hygiene": "BED_0based_vs_VCF_1based",
        "seg_threshold": "log2_cnv_delta > 0.3",
        "hrd_cin_score_cut": 42.0,
        "synthetic_lethality_target": "PARP1/ATR",
        "chromosomal_imbalance_index": "fraction_genome_altered > 0.2",
    },
    "ONC-144": {
        "mmr_genes": ["MLH1", "MSH2", "MSH6", "PMS2"],
        "bat25_bat26_threshold": ">= 2 unstable mononucleotide loci",
        "immunotherapy_biomarker": "pembrolizumab_agnostic_approval",
        "hypermutability_rate": "> 100 mutations per genome",
    },
    "ONC-145": {
        "chromosomal_imbalance_index": "fraction_genome_altered > 0.2",
        "gene_dosage_leverage": "proteotoxic_stress_dependency",
        "target_pathway": "SAC_bub1b_mps1",
        "mitotic_spindle_checkpoint": "active_surveillance",
    },
    "ONC-146": {
        "calculation": "somatic_snv_indel_count / target_region_mb",
        "tmb_high_threshold_per_mb": 10.0,
        "target_region_default_mb": 38.0,
        "biomarker_clinical_utility": "anti_pd1_response_prediction",
    },
    "ONC-147": {
        "sbs_catalog_version": "COSMIC_v3.4",
        "deconstruct_sigs_metric": "cosine_similarity >= 0.85",
        "etiology_mapping": {
            "SBS1": "5mC_deamination",
            "SBS2_SBS13": "APOBEC_cytidine_deaminase",
            "SBS3": "HRD_BRCAness",
            "SBS4": "tobacco_PAH",
            "SBS7": "UV_pyrimidine_dimers",
        },
    },
    "ONC-148": {
        "motif_context": "TCW -> TTW / TGW (W = A or T)",
        "enrichment_ratio_cut": 2.0,
        "cosmic_signatures": ["SBS2", "SBS13"],
        "driver_neoantigen_leverage": "high_immunogenicity_clusters",
    },
    "ONC-149": {
        "genomic_hallmark": "localized_shattering_and_re_ligation",
        "copy_number_oscillations": "2_to_3_states_in_dense_cluster",
        "oncogene_amplification_link": ["MYC", "MDM2", "CDK4", "EGFR"],
        "repair_mechanism": "NHEJ_MMEJ_catastrophe",
    },
    "ONC-150": {
        "definition": "localized_hypermutation_rain",
        "intermutational_distance_bp": "<= 1000",
        "associated_enzyme": "APOBEC3A_APOBEC3B",
        "strand_coordination": "processive_deamination_on_ssDNA",
    },
    "ONC-151": {
        "ploidy_state": "tetraploid_or_near_tetraploid_transition",
        "buffer_capacity": "tolerates_deleterious_chromosomal_losses",
        "prognostic_impact": "high_relapse_risk_and_multidrug_resistance",
    },
    "ONC-152": {
        "mechanism": "biallelic_inactivation_knudson_2nd_hit",
        "hrd_loh_score": "number_of_subchromosomal_LOH_regions > 15Mb",
        "diagnostic_panel": "SNP_array_or_WGS_b_allele_frequency_shift",
    },
    "ONC-153": {
        "origin_firing_aberration": "premature_S_phase_entry_fork_stalling",
        "checkpoint_dependency": ["ATR", "CHK1", "WEE1"],
        "biomarker": "RPA_ssDNA_accumulation_and_gamma_H2AX",
    },
    "ONC-154": {
        "topology": "circular_amplicon_lacking_centromere",
        "copy_number_leverage": "up_to_100x_oncogene_amplification",
        "chromatin_state": "highly_accessible_super_enhancer_hub",
        "segregation_dynamics": "non_mendelian_random_segregation_under_drug_selection",
    },
}


def build_records() -> list[dict[str, Any]]:
    recs: list[dict[str, Any]] = []
    for i, (name, cat, role, desc, therapy, ref) in enumerate(PRIMS, start=1):
        label, layer = CATS[cat]
        rec: dict[str, Any] = {
            "id": f"ONC-{i:03d}",
            "name": name,
            "category": cat,
            "category_label": label,
            "layer": layer,
            "role": role,
            "description": desc,
            "therapeutic_relevance": therapy,
            "reference": ref,
            "confidence": "C5-established",
        }
        if rec["id"] in GENOME_MECHANICS:
            rec["genomic_mechanics"] = GENOME_MECHANICS[rec["id"]]
        recs.append(rec)
    return recs


def q(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def write_if_changed(path: str, content: str) -> None:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            if f.read() == content:
                return
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _format_genomic_mechanics(genomic_mechanics: dict[str, Any]) -> list[str]:
    lines = ["      genomic_mechanics:"]
    for k_mech, v_mech in genomic_mechanics.items():
        if isinstance(v_mech, dict):
            lines.append(f"        {k_mech}:")
            for sub_k, sub_v in v_mech.items():
                val_str = repr(sub_v) if not isinstance(sub_v, str) else q(sub_v)
                lines.append(f"          {sub_k}: {val_str}")
        elif isinstance(v_mech, list):
            lines.append(f"        {k_mech}:")
            for item in v_mech:
                val_str = repr(item) if not isinstance(item, str) else q(item)
                lines.append(f"          - {val_str}")
        else:
            val_str = repr(v_mech) if not isinstance(v_mech, str) else q(v_mech)
            lines.append(f"        {k_mech}: {val_str}")
    return lines


def emit_yaml(recs: list[dict[str, Any]], path: str) -> None:
    lines = []
    lines.append("# CORTEX / BABYLON-60 :: Oncology Molecular Primitives Ontology")
    lines.append(f"# count: {len(recs)} | source of truth: scripts/gen_oncology_primitives.py")
    lines.append("# authorship (AKA): Borja Moskv (borjamoskv)")
    lines.append("---")
    lines.append(f"disclaimer_es: {q(DISCLAIMER_ES)}")
    lines.append(f"disclaimer_en: {q(DISCLAIMER_EN)}")
    lines.append("ontology:")
    lines.append("  name: oncology_300_primitives")
    lines.append("  version: 1.0.0")
    lines.append(f"  count: {len(recs)}")
    lines.append("  confidence_scale: C5-established")
    lines.append("  categories:")
    for k, (label, layer) in CATS.items():
        n = sum((1 for r in recs if r["category"] == k))
        lines.append(f"    - key: {k}")
        lines.append(f"      label: {q(label)}")
        lines.append(f"      layer: {layer}")
        lines.append(f"      count: {n}")
    lines.append("  primitives:")
    for r in recs:
        lines.append(f"    - id: {r['id']}")
        lines.append(f"      name: {q(r['name'])}")
        lines.append(f"      category: {r['category']}")
        lines.append(f"      layer: {r['layer']}")
        lines.append(f"      role: {r['role']}")
        lines.append(f"      description: {q(r['description'])}")
        lines.append(f"      therapeutic_relevance: {q(r['therapeutic_relevance'])}")
        lines.append(f"      reference: {q(r['reference'])}")
        lines.append(f"      confidence: {r['confidence']}")
        if "genomic_mechanics" in r:
            lines.extend(_format_genomic_mechanics(r["genomic_mechanics"]))
    write_if_changed(path, "\n".join(lines) + "\n")


def emit_python(recs: list[dict[str, Any]], path: str) -> None:
    header = (
        '#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n"""\nCORTEX / BABYLON-60 :: oncology_primitives\nModulo de datos: 300 primitivas de biologia molecular del cancer y dianas terapeuticas.\n\nGENERADO por scripts/gen_oncology_primitives.py -- NO editar a mano.\nAutoria artistica/arquitectonica (AKA): Borja Moskv (borjamoskv).\n\n%s\n"""\nfrom __future__ import annotations\nfrom typing import Optional, Any\n\nDISCLAIMER = %r\n\nCATEGORIES: dict[str, dict[str, str]] = %r\n\nPRIMITIVES: list[dict[str, Any]] = [\n'
        % (DISCLAIMER_ES, DISCLAIMER_ES, {k: {"label": v[0], "layer": v[1]} for k, v in CATS.items()})
    )
    body: list[str] = []
    for r in recs:
        body.append("    " + repr(r) + ",")
    footer = '\n]\n\nassert len(PRIMITIVES) == 300, "La ontologia debe contener exactamente 300 primitivas"\n\n_BY_ID: dict[str, dict[str, Any]] = {str(p["id"]): p for p in PRIMITIVES}\n\n\ndef get(primitive_id: str) -> Optional[dict[str, Any]]:\n    """Devuelve la primitiva por id (p.ej. \'ONC-001\') o None."""\n    return _BY_ID.get(primitive_id)\n\n\ndef by_category(category: str) -> list[dict[str, Any]]:\n    """Todas las primitivas de una categoria (clave de CATEGORIES)."""\n    return [p for p in PRIMITIVES if p["category"] == category]\n\n\ndef by_role(role: str) -> list[dict[str, Any]]:\n    """Filtra por rol: process, oncogene, suppressor, target, biomarker, modality, mechanism, drug-target."""\n    return [p for p in PRIMITIVES if p["role"] == role]\n\n\ndef search(term: str) -> list[dict[str, Any]]:\n    """Busqueda de subcadena (case-insensitive) en nombre y descripcion."""\n    t = term.lower()\n    return [p for p in PRIMITIVES if t in str(p["name"]).lower() or t in str(p["description"]).lower()]\n\n\ndef counts() -> dict[str, int]:\n    """Conteo por categoria."""\n    out: dict[str, int] = {}\n    for p in PRIMITIVES:\n        cat_key = str(p["category"])\n        out[cat_key] = out.get(cat_key, 0) + 1\n    return out\n\n\nif __name__ == "__main__":\n    print(DISCLAIMER)\n    print()\n    print(f"Total primitivas: {len(PRIMITIVES)}")\n    for k, n in counts().items():\n        print(f"  {k:12s} {n:3d}  {CATEGORIES[k][\'label\']}")\n'
    write_if_changed(path, header + "\n".join(body) + footer)


def emit_markdown(recs: list[dict[str, Any]], path: str) -> None:
    role_es: dict[str, str] = {
        "process": "proceso",
        "oncogene": "oncogen",
        "suppressor": "supresor",
        "target": "diana",
        "biomarker": "biomarcador",
        "modality": "modalidad",
        "mechanism": "mecanismo",
        "drug-target": "farmaco->diana",
    }
    L: list[str] = []
    L.append("# 300 Primitivas de Oncologia Molecular")
    L.append(
        "### Ontologia CORTEX / BABYLON-60 -- bloques fundamentales que la investigacion del cancer estudia y ataca"
    )
    L.append("")
    L.append(
        "*Generado deterministicamente | 300 primitivas | escala de confianza C5-established | fuente unica: `scripts/gen_oncology_primitives.py`*"
    )
    L.append("")
    L.append("> **AVISO IMPORTANTE.** " + DISCLAIMER_ES)
    L.append("")
    L.append("> *NOTICE.* " + DISCLAIMER_EN)
    L.append("")
    L.append("Autoria artistica/arquitectonica del sustrato (AKA): **Borja Moskv** (`borjamoskv`).")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## Indice de categorias")
    L.append("")
    L.append("| # | Categoria | Capa | Primitivas |")
    L.append("| :--- | :--- | :--- | :---: |")
    for idx, (k, (label, layer)) in enumerate(CATS.items(), start=1):
        n = sum((1 for r in recs if r["category"] == k))
        anchor = label.lower().replace(" ", "-").replace("(", "").replace(")", "").replace("/", "").replace(",", "")
        L.append(f"| {idx} | [{label}](#{anchor}) | {layer} | {n} |")
    L.append(f"| | **TOTAL** | | **{len(recs)}** |")
    L.append("")
    L.append("---")
    L.append("")
    for k, (label, layer) in CATS.items():
        cat_recs = [r for r in recs if r["category"] == k]
        anchor = label.lower().replace(" ", "-").replace("(", "").replace(")", "").replace("/", "").replace(",", "")
        L.append(f"## {label}")
        L.append(f'<a id="{anchor}"></a>')
        L.append(f"*Capa: {layer} | {len(cat_recs)} primitivas*")
        L.append("")
        L.append("| ID | Primitiva | Rol | Mecanismo | Relevancia terapeutica | Referencia |")
        L.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
        for r in cat_recs:
            L.append(
                f"| `{r['id']}` | **{r['name']}** | {role_es.get(r['role'], r['role'])} | {r['description']} | {r['therapeutic_relevance']} | {r['reference']} |"
            )
        L.append("")
    L.append("---")
    L.append("")
    L.append("## Nota metodologica")
    L.append("")
    L.append(
        "Las primitivas cubren desde los *hallmarks* de Hanahan & Weinberg (Cell 2000, 2011; Cancer Discovery 2022) hasta pares farmaco->diana con evidencia clinica registrada. Las referencias citan articulos o revisiones canonicas; los mecanismos reflejan conocimiento establecido a la fecha de generacion. Esto es material educativo y de modelado ontologico: **no sustituye juicio clinico ni investigacion primaria.**"
    )
    L.append("")
    write_if_changed(path, "\n".join(L) + "\n")


def main() -> None:
    root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    recs = build_records()
    assert len(recs) == 300, f"Se esperaban 300 primitivas, hay {len(recs)}"
    ids = [r["id"] for r in recs]
    assert len(set(ids)) == len(ids), "IDs duplicados detectados"
    yaml_path = os.path.join(root, "cortex", "ontologies", "oncology_300_primitives.yaml")
    py_path = os.path.join(root, "babylon60", "oncology_primitives.py")
    md_path = os.path.join(root, "docs", "ONCOLOGIA_300_PRIMITIVAS.md")
    for p in (yaml_path, py_path, md_path):
        os.makedirs(os.path.dirname(p), exist_ok=True)
    emit_yaml(recs, yaml_path)
    emit_python(recs, py_path)
    emit_markdown(recs, md_path)
    from collections import Counter

    c = Counter((r["category"] for r in recs))
    print(f"OK -> {len(recs)} primitivas, IDs unicos, 3 formatos emitidos.")
    for k in CATS:
        print(f"  {k:12s} {c[k]:3d}")


if __name__ == "__main__":
    main()
