#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v5.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | DOMAIN BLEED AUDITOR
# ============================================================================
"""Domain Bleed Invariant Guard (INV_C5_DOMAIN_BLEED).

Audits the repository for domain boundary breaches across four vectors:
1. Ring & Directory Confinement: No unclassified root directories or domain splits.
2. Commercial & Societary Confinement: Zero invoices, billing, or corporate VAT files.
3. Audio Bloat Confinement: Zero heavy binary audio files (.mp3, .m4a, .wav > 500KB).
4. Database Confinement: Zero orphan SQLite databases in unauthorized root paths.
5. Ontological Purity: Enforces O1-O14 in schema and source declarations.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]

# Canonical allowed root directories
CANONICAL_ROOT_DIRS = {
    ".agents", ".audit", ".babylon60", ".cargo", ".cortex", ".git", ".github",
    ".hypothesis", ".licenses", ".pytest_cache", ".vscode",
    "00_ABZU_KERNEL", "01_KISH_ENGINE", "02_EDIN_SWARMS",
    "L1_sink", "__pycache__", "apps", "artifact_bundle_v3", "assets",
    "attestation_bundle_v1", "attestation_bundle_v2", "babylonmail",
    "compliance_reports", "contracts", "crates", "data", "deploy", "dist",
    "docs", "examples", "experiments", "keys", "ledger", "logs", "ontology",
    "papers", "proof", "reports", "scratch", "scripts", "site", "src", "target",
    "tests", "tools", "ui", "Babylon60.app"
}

FORBIDDEN_ROOT_DIRS = {"04_GO_STUDIO", "03_STUDIO", "cortex"}


def check_directory_confinement() -> List[Tuple[str, str]]:
    violations = []
    for item in os.listdir(REPO_ROOT):
        p = REPO_ROOT / item
        if p.is_dir():
            if item in FORBIDDEN_ROOT_DIRS:
                violations.append((str(p), f"Directorio prohibido / desalineado en raíz: '{item}'"))
            elif item not in CANONICAL_ROOT_DIRS and not item.startswith("."):
                violations.append((str(p), f"Directorio no clasificado en raíz: '{item}'"))
    return violations


def check_commercial_confinement() -> List[Tuple[str, str]]:
    violations = []
    forbidden_outreach_scripts = {
        "generate_outreach_payloads.py",
        "index_leads_sqlite.py",
        "swarm_generate_10000_leads.py",
        "sovereign_dispatcher.py",
    }
    for root, _, files in os.walk(REPO_ROOT):
        # Skip git and target
        if "/.git" in root or "/target" in root:
            continue
        for f in files:
            p = Path(root) / f
            if f in forbidden_outreach_scripts:
                violations.append((str(p), f"Script de prospección/outreach no confinado en 20_VAULT: '{f}'"))
            # Check for invoice naming
            if "invoice" in f.lower() and f.endswith((".txt", ".json", ".pdf", ".md")):
                violations.append((str(p), f"Archivo de facturación mercantil detectado: '{f}'"))
            # Check for real CIF/VAT patterns in text files
            if f.endswith((".txt", ".json", ".md")) and "license_template" not in f:
                try:
                    content = p.read_text(encoding="utf-8", errors="ignore")
                    if re.search(r"Tax\s*/\s*VAT\s*ID:\s*ES[A-Z0-9]{8}", content):
                        violations.append((str(p), f"Número CIF/VAT real de cliente en código: '{f}'"))
                except Exception:
                    pass
    return violations


def check_audio_bloat_confinement() -> List[Tuple[str, str]]:
    violations = []
    forbidden_audio_exts = {".mp3", ".m4a"}
    for root, _, files in os.walk(REPO_ROOT):
        if "/.git" in root or "/target" in root:
            continue
        for f in files:
            p = Path(root) / f
            ext = p.suffix.lower()
            if ext in forbidden_audio_exts:
                violations.append((str(p), f"Audio binario de producción detectado en repositorio de código: '{f}'"))
            elif ext == ".wav":
                size = p.stat().st_size
                if size > 500 * 1024:  # > 500 KB
                    violations.append((str(p), f"Audio WAV pesado (>500KB) detectado: '{f}' ({size} bytes)"))
    return violations


def check_database_confinement() -> List[Tuple[str, str]]:
    violations = []
    allowed_db_paths = {
        REPO_ROOT / "data" / "cortex_memory.db",
        REPO_ROOT / "data" / "mail_ledger.db",
        REPO_ROOT / ".cortex" / "causal_gate.db",
    }
    for root, _, files in os.walk(REPO_ROOT):
        if any(skip in root for skip in ("/.git", "/target", "/.audit", "/.mypy_cache", "/.ruff_cache", "/.venv")):
            continue
        for f in files:
            if f.endswith((".db", ".sqlite")):
                p = Path(root) / f
                if p not in allowed_db_paths and not str(p).startswith(str(REPO_ROOT / "scratch")):
                    violations.append((str(p), f"Base de datos SQLite huérfana / no confinada: '{f}' en '{root}'"))
    return violations


def check_ontological_laws_confinement() -> List[Tuple[str, str]]:
    violations = []
    # Check src/ontology.rs contains O1 through O14
    ontology_rs = REPO_ROOT / "src" / "ontology.rs"
    if ontology_rs.exists():
        content = ontology_rs.read_text(encoding="utf-8")
        for i in range(1, 15):
            law_pat = f"O{i}"
            if law_pat not in content:
                violations.append((str(ontology_rs), f"Ley ontológica '{law_pat}' no declarada en src/ontology.rs"))

    # Check ontology/v1/schema.json contains O1 through O14
    schema_json = REPO_ROOT / "ontology" / "v1" / "schema.json"
    if schema_json.exists():
        content = schema_json.read_text(encoding="utf-8")
        for i in range(1, 15):
            law_pat = f"O{i}_"
            if law_pat not in content:
                violations.append((str(schema_json), f"Ley ontológica '{law_pat}' ausente en schema.json"))
    return violations


def run_all_audits() -> int:
    print("=" * 78)
    print("█ [C5-REAL] AUDITORÍA DETERMINISTA DE FUGA DE DOMINIO (DOMAIN BLEED)")
    print("=" * 78)

    all_violations: List[Tuple[str, str]] = []

    print("[1/5] Verificando confinamiento de directorios de anillos...")
    v = check_directory_confinement()
    all_violations.extend(v)
    print(f"      Estado: {'PASS (0 hallazgos)' if not v else f'FAIL ({len(v)} violaciones)'}")

    print("[2/5] Verificando confinamiento comercial (Zero Invoices / Zero CIF)...")
    v = check_commercial_confinement()
    all_violations.extend(v)
    print(f"      Estado: {'PASS (0 hallazgos)' if not v else f'FAIL ({len(v)} violaciones)'}")

    print("[3/5] Verificando confinamiento de activos de audio (Zero Bloat)...")
    v = check_audio_bloat_confinement()
    all_violations.extend(v)
    print(f"      Estado: {'PASS (0 hallazgos)' if not v else f'FAIL ({len(v)} violaciones)'}")

    print("[4/5] Verificando confinamiento de bases de datos SQLite...")
    v = check_database_confinement()
    all_violations.extend(v)
    print(f"      Estado: {'PASS (0 hallazgos)' if not v else f'FAIL ({len(v)} violaciones)'}")

    print("[5/5] Verificando pureza de las 14 Leyes Ontológicas (O1-O14)...")
    v = check_ontological_laws_confinement()
    all_violations.extend(v)
    print(f"      Estado: {'PASS (0 hallazgos)' if not v else f'FAIL ({len(v)} violaciones)'}")

    print("-" * 78)
    if all_violations:
        print(f"❌ FALLO DE AUDITORÍA: Se detectaron {len(all_violations)} anomalías de Fuga de Dominio:")
        for path, desc in all_violations:
            print(f"   • {desc}")
            print(f"     Ruta: {path}")
        return 1

    print("✅ PASS: DOMINIOS ESTRICTAMENTE AISLADOS (Cero Bleed en Silicio).")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(run_all_audits())
