#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
c5_preserve_logs.py - Unified CLI log harvesting, dual cryptographic hashing
(SHA256 / SHA3-256), and forensic Markdown catalog generation.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import shutil
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent

PROVIDERS = {
    "agent": {
        "name": "Agent Code",
        "source_dir": Path.home() / ".agent_persist" / "projects",
        "target_dir": REPO_ROOT / "cortex" / "legal_dossier" / "agent_code_local_logs",
        "index_file": "C5_CATALOGO_LOGS_LOCALES_AGENT_CODE.md",
        "prefix": "agent_local_log",
    },
    "claude": {
        "name": "Claude Code",
        "source_dir": Path.home() / ".claude" / "projects",
        "target_dir": REPO_ROOT / "cortex" / "legal_dossier" / "claude_code_local_logs",
        "index_file": "C5_CATALOGO_LOGS_LOCALES_CLAUDE_CODE.md",
        "prefix": "claude_local_log",
    },
}


def compute_hashes(filepath: Path) -> tuple[str, str]:
    sha256 = hashlib.sha256()
    sha3 = hashlib.sha3_256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
            sha3.update(chunk)
    return (sha256.hexdigest(), sha3.hexdigest())


def harvest_provider_logs(provider_key: str) -> None:
    if provider_key not in PROVIDERS:
        print(f"[-] Unknown provider key: {provider_key}")
        return

    cfg = PROVIDERS[provider_key]
    provider_name = cfg["name"]
    source_dir: Path = cfg["source_dir"]
    target_dir: Path = cfg["target_dir"]
    index_path = target_dir / cfg["index_file"]
    prefix = cfg["prefix"]

    print(f"[*] ULTRATHINK P0: Harvesting local {provider_name} CLI session logs from {source_dir}...")
    target_dir.mkdir(parents=True, exist_ok=True)
    if not source_dir.exists():
        print(f"[-] Source directory {source_dir} does not exist.")
        return

    jsonl_files = list(source_dir.rglob("*.jsonl"))
    print(f"[+] Found {len(jsonl_files)} local {provider_name} session logs.")
    if not jsonl_files:
        return

    catalog_entries = []
    for i, file_path in enumerate(sorted(jsonl_files), 1):
        rel_proj = file_path.parent.name
        dest_filename = f"{prefix}_{i:02d}_{rel_proj}_{file_path.name}"
        dest_path = target_dir / dest_filename

        shutil.copy2(file_path, dest_path)
        sha256_hash, sha3_hash = compute_hashes(dest_path)
        size_kb = dest_path.stat().st_size / 1024.0

        catalog_entries.append(
            {
                "id": f"LOG-LOCAL-#{i:02d}",
                "original_path": str(file_path),
                "dest_name": dest_filename,
                "size_kb": f"{size_kb:.2f} KB",
                "sha256": sha256_hash,
                "sha3": sha3_hash,
            }
        )

    md_lines = [
        f"# CATÁLOGO PERICIAL Y CUSTODIA DE LOGS LOCALES DE `{provider_name.upper()}`",
        "",
        "> **Documento de Custodia Forense e Identificación Criptográfica (`CORTEX-PERSIST`)**  ",
        "> **Titular de Propiedad Intelectual:** Don CORTEX Core Dev (`borjamoskv`)  ",
        f"> **Objeto:** Custodia física, sellado hash inmutable (`SHA256 / SHA3-256`) e indexación de los historiales locales y sesiones `.jsonl` ejecutados en silicio soberano Apple Silicon (`{source_dir}`). Acredita de forma incontestable el historial, el pensamiento y las trazas de análisis técnico de `{provider_name}` en local.",
        "",
        "---",
        "",
        "## 1. CUADRO RESUMEN DE SESIONES LOCALES EN DISCO (`Causal-Determinist`)",
        "",
        "| ID | Archivo de Log Preservado en Silicio | Tamaño | SHA256 (Hash de Integridad) | SHA3-256 (Attestation) | Ruta Original en Apple Silicon |",
        "| :---: | :--- | :---: | :--- | :--- | :--- |",
    ]

    for entry in catalog_entries:
        row = f"| **`{entry['id']}`** | `{entry['dest_name']}` | `{entry['size_kb']}` | `{entry['sha256']}` | `{entry['sha3']}` | `{entry['original_path']}` |"
        md_lines.append(row)

    md_lines.extend(
        [
            "",
            "---",
            "",
            "## 2. VALOR PROBATORIO Y FORENSE",
            "",
            "1. **Acreditación de Trazabilidad e Historial:** Estos registros demuestran empíricamente el trabajo, los *prompts*, las lecturas de archivo (`FileRead`) y el análisis arquitectónico ejecutados en silicio Apple Silicon antes del bloqueo, constituyendo una prueba de anterioridad fehaciente (*Prior Art*).",
            "2. **Inmutabilidad Criptográfica:** El sellado dual con funciones de hash (`SHA256` y `SHA3-256`) previene cualquier impugnación de manipulación posterior del texto logueado.",
            "",
            "---",
            "*Catálogo sellado por el autómata MOSKV-1 APEX / BABILONIA 60. Nivel de Certeza: Causal-Determinist.*",
            "",
        ]
    )

    with open(index_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"[+] Successfully harvested and indexed {len(catalog_entries)} local {provider_name} logs.")
    print(f"[+] Index created at: {index_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="C5 Unified Local Log Preservation Engine")
    parser.add_argument(
        "--provider",
        choices=["agent", "claude", "all"],
        default="all",
        help="Target provider logs to preserve (agent, claude, or all)",
    )
    args = parser.parse_args()

    if args.provider in ("agent", "all"):
        harvest_provider_logs("agent")
    if args.provider in ("claude", "all"):
        harvest_provider_logs("claude")


if __name__ == "__main__":
    main()
