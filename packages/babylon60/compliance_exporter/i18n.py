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
            "Nota legal: Este informe genera evidencia técnica de auto-evaluación interna para los Artículos 9–14 "
            "del Reglamento UE 2024/1689. No constituye una certificación formal emitida por un Organismo Notificado (Notified Body)."
        ),
        "status_pass": "CONFORME",
        "quarantine_nominal": "NOMINAL_LIMPIO",
        "quarantine_sealed": "CUARENTENA_SELLADA_WORM",
        "article_titles": {
            "Article_9": "Art. 9: Sistema de Gestión de Riesgos",
            "Article_10": "Art. 10: Gobernanza de Datos y Linaje",
            "Article_11": "Art. 11: Documentación Técnica y Demostración Lean 4",
            "Article_12": "Art. 12: Conservación de Registros / Logging WORM",
            "Article_14": "Art. 14: Control y Supervisión Humana",
        },
        "mechanisms": {
            "Article_9": "Podador Termodinámico de AST + Motor de Auto-Falsación (Interruptor de Hombre Muerto)",
            "Article_10": "Memoria Tipada Sexagesimal F60 + Linaje DAG Merkle-Causal",
            "Article_11": "Exportación Automática de Proof IR a Lemas de Teorema Lean 4",
            "Article_12": "Ledger DAG Merkle-Causal + Sello Criptográfico de Cuarentena WORM",
            "Article_14": "Visualizador Armónico Tonnetz + Inspección de Trazas Causal IR",
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
            "Legal notice: This report provides technical self-assessment evidence for Articles 9–14 of EU Regulation 2024/1689. "
            "It does not constitute a formal certification by an accredited Notified Body."
        ),
        "status_pass": "COMPLIANT",
        "quarantine_nominal": "NOMINAL_CLEAN",
        "quarantine_sealed": "QUARANTINED_WORM_FREEZE",
        "article_titles": {
            "Article_9": "Art. 9: Risk Management System",
            "Article_10": "Art. 10: Data Governance & Lineage",
            "Article_11": "Art. 11: Technical Documentation & Lean 4 Verification",
            "Article_12": "Art. 12: Record-Keeping & WORM Logging",
            "Article_14": "Art. 14: Human Oversight & Harmonics",
        },
        "mechanisms": {
            "Article_9": "Thermodynamic AST Exergy Pruner + Self-Falsification Engine (Dead Man's Switch)",
            "Article_10": "F60 Typed Sexagesimal Memory + Merkle-Causal Lineage DAG",
            "Article_11": "Auto-export of Proof IR to Lean 4 Theorem Prover Obligations",
            "Article_12": "Merkle-Causal DAG Ledger + WORM Cryptographic Quarantine Seal",
            "Article_14": "Tonnetz Harmonic Audit Visualizer + Causal IR Trace Inspection",
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
            "Rechtlicher Hinweis: Dieser Bericht liefert technische Selbstbewertungsnachweise für die Artikel 9–14 der EU-Verordnung 2024/1689. "
            "Er stellt keine formelle Zertifizierung durch eine Benannte Stelle dar."
        ),
        "status_pass": "KONFORM",
        "quarantine_nominal": "NOMINAL_SAUBER",
        "quarantine_sealed": "QUARANTÄNE_WORM_VERSIEGELT",
        "article_titles": {
            "Article_9": "Art. 9: Risikomanagementsystem",
            "Article_10": "Art. 10: Daten-Governance und Abstammung",
            "Article_11": "Art. 11: Technische Dokumentation und Lean 4 Nachweis",
            "Article_12": "Art. 12: Aufzeichnung von Ereignissen / WORM-Protokollierung",
            "Article_14": "Art. 14: Menschliche Aufsicht",
        },
        "mechanisms": {
            "Article_9": "Thermodynamischer AST-Exergie-Pruner + Selbstfalsifikations-Engine",
            "Article_10": "F60 Typisierter Sexagesimalspeicher + Merkle-Kausaler DAG",
            "Article_11": "Automatischer Export von Proof IR in Lean 4 Theoremverifizierer",
            "Article_12": "Merkle-Kausales DAG-Ledger + WORM Kryptografisches Quarantänesiegel",
            "Article_14": "Tonnetz Harmonischer Audit-Visualisierer",
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
            "Mentions légales : Ce rapport fournit des preuves d'auto-évaluation technique pour les articles 9–14 du règlement UE 2024/1689. "
            "Il ne constitue pas une certification formelle par un organisme notifié."
        ),
        "status_pass": "CONFORME",
        "quarantine_nominal": "NOMINAL_PROPRE",
        "quarantine_sealed": "QUARANTAINE_SCELLÉE_WORM",
        "article_titles": {
            "Article_9": "Art. 9: Système de Gestion des Risques",
            "Article_10": "Art. 10: Gouvernance des Données et Lignée",
            "Article_11": "Art. 11: Documentation Technique et Vérification Lean 4",
            "Article_12": "Art. 12: Enregistrement des Journaux / Logging WORM",
            "Article_14": "Art. 14: Contrôle et Supervision Humaine",
        },
        "mechanisms": {
            "Article_9": "Éagueur Thermodynamique d'AST Exergie + Moteur d'Auto-Falsification",
            "Article_10": "Mémoire Typée Sexagésimale F60 + Lignée DAG Merkle-Causale",
            "Article_11": "Exportation Automatique de Proof IR vers Démonstrateur Lean 4",
            "Article_12": "Registre DAG Merkle-Causal + Sceau Cryptographique de Quarantaine WORM",
            "Article_14": "Visualiseur Harmonique Tonnetz",
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
            "Nota legale: Questo rapporto fornisce evidenze di autovalutazione tecnica per gli Articoli 9–14 del Regolamento UE 2024/1689. "
            "Non costituisce una certificazione formale rilasciata da un Organismo Notificato."
        ),
        "status_pass": "CONFORME",
        "quarantine_nominal": "NOMINALE_PULITO",
        "quarantine_sealed": "QUARANTENA_SIGILLATA_WORM",
        "article_titles": {
            "Article_9": "Art. 9: Sistema di Gestione dei Rischi",
            "Article_10": "Art. 10: Governance dei Dati e Lineaggio",
            "Article_11": "Art. 11: Documentazione Tecnica e Verifica Lean 4",
            "Article_12": "Art. 12: Conservazione dei Registri / Logging WORM",
            "Article_14": "Art. 14: Sorveglianza Umana",
        },
        "mechanisms": {
            "Article_9": "Pruner Termodinamico AST Exergy + Motore di Auto-Falsificazione",
            "Article_10": "Memoria Tipizzata Sessagesimale F60 + Lineaggio DAG Merkle-Causale",
            "Article_11": "Esportazione Automatica Proof IR verso Dimostratore Lean 4",
            "Article_12": "Ledger DAG Merkle-Causale + Sigillo Crittografico di Quarantena WORM",
            "Article_14": "Visualizzatore Armonico Tonnetz",
        },
        "authority": "Agenzia per l'Italia Digitale (AgID) / Garante Privacy / UE",
    },
}


def get_translation(locale: str) -> Dict[str, Any]:
    """Retrieves translation mapping for given country/locale code (defaults to 'es')."""
    normalized_locale = locale.lower().strip()
    return TRANSLATIONS.get(normalized_locale, TRANSLATIONS["es"])
