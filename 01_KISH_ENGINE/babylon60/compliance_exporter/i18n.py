"""
BABYLON-60 v4.0 Multi-Country & Multi-Locale Compliance Translations (i18n)
Provides localized legal terminology and country-specific regulatory headers for audit certificates.
"""

from typing import Dict, Any

TRANSLATIONS: Dict[str, Dict[str, Any]] = {
    "es": {
        "title": "Informe de Auto-Evaluación de Conformidad Regulatoria de IA (BABYLON-60 v4.0)",
        "compliance_standard": "Reglamento de Inteligencia Artificial de la UE (Reglamento UE 2024/1689 / AESIA)",
        "executive_summary_title": "Resumen Ejecutivo de Auto-Evaluación",
        "executive_summary_text": (
            "Se documenta la auto-evaluación técnica del sistema ejecutado bajo el Kernel Causal-Determinista "
            "BABYLON-60 v4.0. Todas las transiciones de memoria y operaciones temporales están ancladas "
            "a un Ledger DAG Merkle-Causal con verificación criptográfica local."
        ),
        "legal_disclaimer": (
            "Nota legal: Este informe genera evidencia técnica de auto-evaluación interna para los Artículos 9–15 "
            "del Reglamento UE 2024/1689. No constituye una certificación formal emitida por un Organismo Notificado (Notified Body)."
        ),
        "status_pass": "CONFORME",
        "quarantine_nominal": "NOMINAL_LIMPIO",
        "quarantine_sealed": "CUARENTENA_SELLADA_WORM",
        "compliance_matrix_title": "Matriz de Cumplimiento Normativo EU AI Act",
        "evidence_verification_title": "Verificación Criptográfica de la Evidencia",
        "hardware_anchor_title": "Anclaje Criptográfico de Hardware y Ciclo de Vida",
        "signature_title": "Firma Ed25519 del Certificado",
        "certificate_id_label": "ID Certificado",
        "system_label": "Sistema Auditado",
        "operator_label": "Operador / Entidad",
        "issued_at_label": "Fecha Emisión",
        "ledger_label": "Ledger",
        "integrity_verified_label": "Cadena íntegra (verify_integrity)",
        "recomputed_merkle_root_label": "Merkle root recomputado",
        "manifest_match_label": "Coincide con global_hash del manifiesto",
        "verdict_label": "Veredicto",
        "quarantine_status_label": "Estado de Cuarentena",
        "report_id_label": "ID Informe",
        "supervisory_authority_label": "Autoridad de Supervisión",
        "article_titles": {
            "Article_9": "Art. 9: Sistema de Gestión de Riesgos",
            "Article_10": "Art. 10: Gobernanza de Datos y Linaje",
            "Article_11": "Art. 11: Documentación Técnica y Demostración Lean 4",
            "Article_12": "Art. 12: Conservación de Registros / Logging WORM",
            "Article_14": "Art. 14: Control y Supervisión Humana",
            "Article_15": "Art. 15: Precisión, Robustez y Ciberseguridad",
            "Article_50": "Art. 50: Obligaciones de Transparencia para Modelos de IA de Propósito General (GPAI)",
        },
        "mechanisms": {
            "Article_9": "Podador Termodinámico de AST + Motor de Auto-Falsación (Interruptor de Hombre Muerto)",
            "Article_10": "Memoria Tipada Sexagesimal F60 + Linaje DAG Merkle-Causal",
            "Article_11": "Exportación Automática de Proof IR a Lemas de Teorema Lean 4",
            "Article_12": "Ledger DAG Merkle-Causal + Sello Criptográfico de Cuarentena WORM",
            "Article_14": "Visualizador Armónico Tonnetz + Inspección de Trazas Causal IR",
            "Article_15": "Aislamiento Ring-0 C-ABI + Seqlock SPMC (RFO=0) + Apoptosis Fail-Stop (0xDEAD_6060)",
            "Article_50": "Atestación Inmutable Criptográfica SCITT L5 + Sello de Transparencia Causal",
        },
        "authority": "Agencia Española de Supervisión de Inteligencia Artificial (AESIA) / UE",
    },
    "en": {
        "title": "AI Regulatory Compliance Self-Assessment Report (BABYLON-60 v4.0)",
        "compliance_standard": "EU Artificial Intelligence Act (Regulation EU 2024/1689 / NIST AI RMF)",
        "executive_summary_title": "Executive Self-Assessment Summary",
        "executive_summary_text": (
            "This technical self-assessment report documents the system execution under the BABYLON-60 v4.0 Causal-Determinist Kernel. "
            "All memory transitions and temporal scheduling operations were anchored to a Merkle-Causal DAG Ledger "
            "with local cryptographic verification."
        ),
        "legal_disclaimer": (
            "Legal notice: This report provides technical self-assessment evidence for Articles 9–15 of EU Regulation 2024/1689. "
            "It does not constitute a formal certification by an accredited Notified Body."
        ),
        "status_pass": "COMPLIANT",
        "quarantine_nominal": "NOMINAL_CLEAN",
        "quarantine_sealed": "QUARANTINED_WORM_FREEZE",
        "compliance_matrix_title": "EU AI Act Regulatory Compliance Matrix",
        "evidence_verification_title": "Cryptographic Evidence Verification",
        "hardware_anchor_title": "Hardware Anchor & Lifecycle",
        "signature_title": "Certificate Ed25519 Signature",
        "certificate_id_label": "Certificate ID",
        "system_label": "Audited System",
        "operator_label": "Operator / Entity",
        "issued_at_label": "Issue Date",
        "ledger_label": "Ledger",
        "integrity_verified_label": "Chain Integrity (verify_integrity)",
        "recomputed_merkle_root_label": "Recomputed Merkle Root",
        "manifest_match_label": "Matches Manifest global_hash",
        "verdict_label": "Verdict",
        "quarantine_status_label": "Quarantine Status",
        "report_id_label": "Report ID",
        "supervisory_authority_label": "Supervisory Authority",
        "article_titles": {
            "Article_9": "Art. 9: Risk Management System",
            "Article_10": "Art. 10: Data Governance & Lineage",
            "Article_11": "Art. 11: Technical Documentation & Lean 4 Verification",
            "Article_12": "Art. 12: Record-Keeping & WORM Logging",
            "Article_14": "Art. 14: Human Oversight & Harmonics",
            "Article_15": "Art. 15: Accuracy, Robustness & Cybersecurity",
            "Article_50": "Art. 50: Transparency Obligations for GPAI Models",
        },
        "mechanisms": {
            "Article_9": "Thermodynamic AST Exergy Pruner + Self-Falsification Engine (Dead Man's Switch)",
            "Article_10": "F60 Typed Sexagesimal Memory + Merkle-Causal Lineage DAG",
            "Article_11": "Auto-export of Proof IR to Lean 4 Theorem Prover Obligations",
            "Article_12": "Merkle-Causal DAG Ledger + WORM Cryptographic Quarantine Seal",
            "Article_14": "Tonnetz Harmonic Audit Visualizer + Causal IR Trace Inspection",
            "Article_15": "Ring-0 C-ABI Isolation + Zero-Split Seqlock SPMC (RFO=0) + Fail-Stop Apoptosis (0xDEAD_6060)",
            "Article_50": "Cryptographic SCITT L5 Immutable Attestation + Causal Transparency Seal",
        },
        "authority": "EU AI Office / NIST (USA) / UK AI Safety Institute",
    },
    "de": {
        "title": "KI-Konformitätsselbstbewertungsbericht (BABYLON-60 v4.0)",
        "compliance_standard": "EU-Verordnung über Künstliche Intelligenz (Verordnung EU 2024/1689 / BSI)",
        "executive_summary_title": "Zusammenfassung der Selbstbewertung",
        "executive_summary_text": (
            "Dieser Bericht dokumentiert die technische Selbstbewertung des Systems unter dem BABYLON-60 v4.0 Kausal-Deterministischen "
            "Kernel. Alle Speicherübergänge und Zeitsteuerungsoperationen wurden in einem Merkle-Kausalen DAG-Ledger verankert."
        ),
        "legal_disclaimer": (
            "Rechtlicher Hinweis: Dieser Bericht liefert technische Selbstbewertungsnachweise für die Artikel 9–15 der EU-Verordnung 2024/1689. "
            "Er stellt keine formelle Zertifizierung durch eine Benannte Stelle dar."
        ),
        "status_pass": "KONFORM",
        "quarantine_nominal": "NOMINAL_SAUBER",
        "quarantine_sealed": "QUARANTÄNE_WORM_VERSIEGELT",
        "compliance_matrix_title": "EU AI Act Regulatorische Konformitätsmatrix",
        "evidence_verification_title": "Kryptografische Evidenzprüfung",
        "hardware_anchor_title": "Hardware-Verankerung & Lebenszyklus",
        "signature_title": "Ed25519-Zertifikatssignatur",
        "certificate_id_label": "Zertifikats-ID",
        "system_label": "Geprüftes System",
        "operator_label": "Betreiber / Entität",
        "issued_at_label": "Ausstellungsdatum",
        "ledger_label": "Ledger",
        "integrity_verified_label": "Kettenintegrität",
        "recomputed_merkle_root_label": "Neuberechnete Merkle-Wurzel",
        "manifest_match_label": "Stimmt mit Manifest global_hash überein",
        "verdict_label": "Urteil",
        "quarantine_status_label": "Quarantänestatus",
        "report_id_label": "Berichts-ID",
        "supervisory_authority_label": "Aufsichtsbehörde",
        "article_titles": {
            "Article_9": "Art. 9: Risikomanagementsystem",
            "Article_10": "Art. 10: Daten-Governance und Abstammung",
            "Article_11": "Art. 11: Technische Dokumentation und Lean 4 Nachweis",
            "Article_12": "Art. 12: Aufzeichnung von Ereignissen / WORM-Protokollierung",
            "Article_14": "Art. 14: Menschliche Aufsicht",
            "Article_15": "Art. 15: Genauigkeit, Robustheit und Cybersicherheit",
            "Article_50": "Art. 50: Transparenzpflichten für GPAI-Modelle",
        },
        "mechanisms": {
            "Article_9": "Thermodynamischer AST-Exergie-Pruner + Selbstfalsifikations-Engine",
            "Article_10": "F60 Typisierter Sexagesimalspeicher + Merkle-Kausaler DAG",
            "Article_11": "Automatischer Export von Proof IR in Lean 4 Theoremverifizierer",
            "Article_12": "Merkle-Kausales DAG-Ledger + WORM Kryptografisches Quarantänesiegel",
            "Article_14": "Tonnetz Harmonischer Audit-Visualisierer",
            "Article_15": "Ring-0 C-ABI-Isolation + Seqlock SPMC (RFO=0) + Fail-Stop-Apoptose (0xDEAD_6060)",
            "Article_50": "Kryptografisches SCITT L5 Unveränderliches Testat",
        },
        "authority": "Bundesamt für Sicherheit in der Informationstechnik (BSI) / EU AI Office",
    },
    "fr": {
        "title": "Rapport d'Auto-Évaluation de Conformité Réglementaire IA (BABYLON-60 v4.0)",
        "compliance_standard": "Règlement Européen sur l'IA (Règlement UE 2024/1689 / CNIL / ANSSI)",
        "executive_summary_title": "Résumé d'Auto-Évaluation",
        "executive_summary_text": (
            "Ce rapport documente l'auto-évaluation technique du système exécuté sous le Noyau Causal-Déterministe BABYLON-60 v4.0. "
            "Toutes les transitions de mémoire et opérations temporelles ont été ancrées dans un Registre DAG Merkle-Causal."
        ),
        "legal_disclaimer": (
            "Mentions légales : Ce rapport fournit des preuves d'auto-évaluation technique pour les articles 9–15 du règlement UE 2024/1689. "
            "Il ne constitue pas une certification formelle par un organisme notifié."
        ),
        "status_pass": "CONFORME",
        "quarantine_nominal": "NOMINAL_PROPRE",
        "quarantine_sealed": "QUARANTAINE_SCELLÉE_WORM",
        "compliance_matrix_title": "Matrice de Conformité Réglementaire EU AI Act",
        "evidence_verification_title": "Vérification Cryptographique des Preuves",
        "hardware_anchor_title": "Ancrage Matériel & Cycle de Vie",
        "signature_title": "Signature Ed25519 du Certificat",
        "certificate_id_label": "ID Certificat",
        "system_label": "Système Audité",
        "operator_label": "Opérateur / Entité",
        "issued_at_label": "Date d'Émission",
        "ledger_label": "Registre",
        "integrity_verified_label": "Intégrité de la Chaîne",
        "recomputed_merkle_root_label": "Racine de Merkle Recomputée",
        "manifest_match_label": "Correspond au global_hash du Manifeste",
        "verdict_label": "Verdict",
        "quarantine_status_label": "Statut de Quarantaine",
        "report_id_label": "ID Rapport",
        "supervisory_authority_label": "Autorité de Surveillance",
        "article_titles": {
            "Article_9": "Art. 9: Système de Gestion des Risques",
            "Article_10": "Art. 10: Gouvernance des Données et Lignée",
            "Article_11": "Art. 11: Documentation Technique et Vérification Lean 4",
            "Article_12": "Art. 12: Enregistrement des Journaux / Logging WORM",
            "Article_14": "Art. 14: Contrôle et Supervision Humaine",
            "Article_15": "Art. 15: Précision, Robustesse et Cybersécurité",
            "Article_50": "Art. 50: Obligations de Transparence pour Modèles GPAI",
        },
        "mechanisms": {
            "Article_9": "Éagueur Thermodynamique d'AST Exergie + Moteur d'Auto-Falsification",
            "Article_10": "Mémoire Typée Sexagésimale F60 + Lignée DAG Merkle-Causale",
            "Article_11": "Exportation Automatique de Proof IR vers Démonstrateur Lean 4",
            "Article_12": "Registre DAG Merkle-Causal + Sceau Cryptographique de Quarantaine WORM",
            "Article_14": "Visualiseur Harmonique Tonnetz",
            "Article_15": "Isolation Ring-0 C-ABI + Seqlock SPMC (RFO=0) + Apoptose Fail-Stop (0xDEAD_6060)",
            "Article_50": "Attestation Cryptographique Immuable SCITT L5",
        },
        "authority": "Commission Nationale de l'Informatique et des Libertés (CNIL) / ANSSI / UE",
    },
    "it": {
        "title": "Rapporto di Autovalutazione di Conformità Regolatoria IA (BABYLON-60 v4.0)",
        "compliance_standard": "Regolamento Europeo sull'IA (Regolamento UE 2024/1689 / AgID)",
        "executive_summary_title": "Riepilogo di Autovalutazione",
        "executive_summary_text": (
            "Questo rapporto documenta l'autovalutazione tecnica del sistema eseguito sotto il Kernel Causale-Deterministico BABYLON-60 v4.0. "
            "Tutte le transizioni di memoria e le operazioni temporali sono state ancorate a un Ledger DAG Merkle-Causale."
        ),
        "legal_disclaimer": (
            "Nota legale: Questo rapporto fornisce evidenze di autovalutazione tecnica per gli Articoli 9–15 del Regolamento UE 2024/1689. "
            "Non costituisce una certificazione formale rilasciata da un Organismo Notificato."
        ),
        "status_pass": "CONFORME",
        "quarantine_nominal": "NOMINALE_PULITO",
        "quarantine_sealed": "QUARANTENA_SIGILLATA_WORM",
        "compliance_matrix_title": "Matrice di Conformità Regolatoria EU AI Act",
        "evidence_verification_title": "Verifica Crittografica delle Prove",
        "hardware_anchor_title": "Ancoraggio Hardware & Ciclo di Vita",
        "signature_title": "Firma Ed25519 del Certificato",
        "certificate_id_label": "ID Certificato",
        "system_label": "Sistema Auditato",
        "operator_label": "Operatore / Entità",
        "issued_at_label": "Data di Emissione",
        "ledger_label": "Ledger",
        "integrity_verified_label": "Integrità della Catena",
        "recomputed_merkle_root_label": "Radice di Merkle Ricalcolata",
        "manifest_match_label": "Corrisponde al global_hash del Manifesto",
        "verdict_label": "Verdetto",
        "quarantine_status_label": "Stato di Quarantena",
        "report_id_label": "ID Rapporto",
        "supervisory_authority_label": "Autorità di Vigilanza",
        "article_titles": {
            "Article_9": "Art. 9: Sistema di Gestione dei Rischi",
            "Article_10": "Art. 10: Governance dei Dati e Lineaggio",
            "Article_11": "Art. 11: Documentazione Tecnica e Verifica Lean 4",
            "Article_12": "Art. 12: Conservazione dei Registri / Logging WORM",
            "Article_14": "Art. 14: Sorveglianza Umana",
            "Article_15": "Art. 15: Accuratezza, Robustezza e Cybersicurezza",
            "Article_50": "Art. 50: Obblighi di Trasparenza per Modelli GPAI",
        },
        "mechanisms": {
            "Article_9": "Pruner Termodinamico AST Exergy + Motore di Auto-Falsificazione",
            "Article_10": "Memoria Tipizzata Sessagesimale F60 + Lineaggio DAG Merkle-Causale",
            "Article_11": "Esportazione Automatica Proof IR verso Dimostratore Lean 4",
            "Article_12": "Ledger DAG Merkle-Causale + Sigillo Crittografico di Quarantena WORM",
            "Article_14": "Visualizzatore Armonico Tonnetz",
            "Article_15": "Isolamento Ring-0 C-ABI + Seqlock SPMC (RFO=0) + Apoptosi Fail-Stop (0xDEAD_6060)",
            "Article_50": "Attestazione Immutabile Crittografica SCITT L5",
        },
        "authority": "Agenzia per l'Italia Digitale (AgID) / Garante Privacy / UE",
    },
}


def get_translation(locale: str) -> Dict[str, Any]:
    """Retrieves translation mapping for given country/locale code (defaults to 'es')."""
    normalized_locale = locale.lower().strip()
    return TRANSLATIONS.get(normalized_locale, TRANSLATIONS["es"])
