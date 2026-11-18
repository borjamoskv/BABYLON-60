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

REPO_ROOT = Path(__file__).absolute().parents[2]

# Canonical allowed root directories
CANONICAL_ROOT_DIRS = {
    ".agents", ".audit", ".babylon60", ".cargo", ".cortex", ".git", ".github",
    ".hypothesis", ".licenses", ".pytest_cache", ".vscode",
    "00_ABZU_KERNEL", "01_KISH_ENGINE", "02_EDIN_SWARMS",
    "L1_sink", "__pycache__", "apps", "artifact_bundle_v3", "assets",
    "attestation_bundle_v1", "attestation_bundle_v2", "babylonmail",
    "compliance_reports", "config", "contracts", "crates", "data", "deploy", "dist",
    "docs", "evidence", "examples", "experiments", "keys", "ledger", "logs", "ontology",
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
                except OSError:
                    continue
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


EXTRINSIC_FORBIDDEN_PATHS = (
    "tools/flstudio",
    "tools/mac_prompt",
    "apps/gflow-studio",
    "apps/mandato",
    "assets/voice_samples",
    "docs/04_audit/campaigns",
    "tools/skill_library/codex_overrides",
)

EXTRINSIC_FORBIDDEN_SKILLS = frozenset({
    "flstudio-mcp-production",
    "djstudio-mcp",
    "suno-bracket-tagging",
    "soulseek-p2p-audio-acquisition",
    "f5tts-voice-cloning-sota",
    "c5-spatial-audio-architect",
    "c5-rubin-acoustic-linter",
    "c5-media-platform-epistemology",
    "c5-audiovisual-acreativo-sota",
    "c5-audiovisual-acreativo-sota-project",
    "audiovisual-sota",
    "youtube-remotion-sota",
    "remotion-audio-reactive-video",
    "pika-generative-video-pipeline",
    "gflow-browser-cinema-sovereign",
    "c5-video-quality-audit",
    "c5-neural-face-swap-cuadrilla",
    "c5-poster-and-sign-craft",
    "youtube-analysis-pipeline",
    "c5-solar-thermodynamic-architecture",
    "somatic-ble-transduction",
    "c5-somatic-panic-deescalation",
    "c5-2e-neuropharmacological-sovereignty",
    "c5-wetware-divergente",
    "c5-wetware-and-venture-ops",
    "c5-wetware-and-venture-ops-project",
    "c5-spaced-repetition-architect",
    "biographical-thermo",
    "adaptive-cron",
    "c5-venture-pitch-architect",
    "c5-weighted-decision-matrix",
    "c5-codebase-valuation-audit",
    "c5-epistemic-dissemination-engine",
    "c5-tamkarum-60",
    "c5-real-legaltech-analysis",
    "whatsapp-nexus-protocol",
    "safari-browser-agent",
    "c5-socint-extraction-suite",
    "c5-browser-forensics-and-extension-triage",
    "c5-sovereign-identity-hardening",
    "cloudflare-mcp-usage",
    "github-architect",
    "github-api-rate-limit-optimization",
    "homebrew-ecosystem-management",
    "jujutsu-vcs-management",
    "macos-lulu-firewall-diagnostics",
    "vscode-git-packed-refs-diagnostics",
    "electron-mac-bundle-collision-diagnostics",
    "electron-asar-forensic-audit",
    "ghidra-ida-binary-audit",
    "webkit-memory-audit",
    "c5-sre-postmortem-architect",
    "c5-secops-infra-devtools",
})


def check_extrinsic_domain_isolation() -> List[Tuple[str, str]]:
    """Reject re-entry of extracted D1-D4 personal/media skills or local creative repos."""
    import json

    violations: List[Tuple[str, str]] = []
    for rel in EXTRINSIC_FORBIDDEN_PATHS:
        target = REPO_ROOT / rel
        if target.exists():
            violations.append((str(target), f"Superficie extrínseca re-inyectada en BABYLON-60: '{rel}'"))

    for base_rel in ("tools/skill_library/global", "tools/skill_library/workspace", ".agents/skills"):
        base = REPO_ROOT / base_rel
        if not base.is_dir():
            continue
        for child in sorted(base.iterdir()):
            if child.is_dir() and child.name in EXTRINSIC_FORBIDDEN_SKILLS:
                violations.append((str(child), f"Skill extrínseco D1-D4 presente en '{base_rel}': '{child.name}'"))

    skills_json = REPO_ROOT / "docs" / "skills.json"
    if skills_json.is_file():
        try:
            entries = json.loads(skills_json.read_text(encoding="utf-8")).get("entries", [])
            for entry in entries:
                name = entry.get("name")
                if name in EXTRINSIC_FORBIDDEN_SKILLS:
                    violations.append((str(skills_json), f"Skill extrínseco '{name}' registrado en docs/skills.json"))
        except (OSError, ValueError):
            pass
    return violations


def run_all_audits() -> int:
    print("=" * 78)
    print("█ [C5-REAL] AUDITORÍA DETERMINISTA DE FUGA DE DOMINIO (DOMAIN BLEED)")
    print("=" * 78)

    all_violations: List[Tuple[str, str]] = []

    print("[1/6] Verificando confinamiento de directorios de anillos...")
    v = check_directory_confinement()
    all_violations.extend(v)
    print(f"      Estado: {'PASS (0 hallazgos)' if not v else f'FAIL ({len(v)} violaciones)'}")

    print("[2/6] Verificando confinamiento comercial (Zero Invoices / Zero CIF)...")
    v = check_commercial_confinement()
    all_violations.extend(v)
    print(f"      Estado: {'PASS (0 hallazgos)' if not v else f'FAIL ({len(v)} violaciones)'}")

    print("[3/6] Verificando confinamiento de activos de audio (Zero Bloat)...")
    v = check_audio_bloat_confinement()
    all_violations.extend(v)
    print(f"      Estado: {'PASS (0 hallazgos)' if not v else f'FAIL ({len(v)} violaciones)'}")

    print("[4/6] Verificando confinamiento de bases de datos SQLite...")
    v = check_database_confinement()
    all_violations.extend(v)
    print(f"      Estado: {'PASS (0 hallazgos)' if not v else f'FAIL ({len(v)} violaciones)'}")

    print("[5/6] Verificando pureza de las 14 Leyes Ontológicas (O1-O14)...")
    v = check_ontological_laws_confinement()
    all_violations.extend(v)
    print(f"      Estado: {'PASS (0 hallazgos)' if not v else f'FAIL ({len(v)} violaciones)'}")

    print("[6/6] Verificando aislamiento de skills y apps extrínsecas (D1-D4)...")
    v = check_extrinsic_domain_isolation()
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
