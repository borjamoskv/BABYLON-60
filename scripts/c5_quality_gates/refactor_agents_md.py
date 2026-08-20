#!/usr/bin/env python3
"""
scripts/refactor_agents_md.py — Deterministic AGENTS.md & ENVIRONMENT.md Refactoring Engine

Refactoriza AGENTS.md con aserciones estrictas de conteo de patrones, backup automático,
fusión real de empirismo PxS, rescate de Sovereign Dual-License (INV_C5_17), purga de la
regla de comunicación cuñada y extracción de reglas locales a ENVIRONMENT.md.
"""

from __future__ import annotations
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

AGENTS_PATH = Path.home() / "10_PROJECTS/.agents/AGENTS.md"
BACKUP_PATH = Path.home() / "10_PROJECTS/.agents/AGENTS.md.bak"
ENV_PATH = Path.home() / "10_PROJECTS/.agents/ENVIRONMENT.md"


def extract_rule_block(content: str, rule_name: str) -> tuple[str, str]:
    """Extrae el bloque completo <RULE[rule_name]>...</RULE[rule_name]> y retorna (bloque, content_sin_bloque)."""
    pattern = rf"\n*<RULE\[{rule_name}\]>\n.*?\n</RULE\[{rule_name}\]>\n*"
    matches = re.findall(pattern, content, flags=re.DOTALL)
    assert len(matches) == 1, f"Fallo al aislar regla '{rule_name}': {len(matches)} coincidencias encontradas."
    block = matches[0].strip()
    new_content = re.sub(pattern, "\n\n", content, count=1, flags=re.DOTALL)
    return block, new_content


def main() -> int:
    parser = argparse.ArgumentParser(description="AGENTS.md & ENVIRONMENT.md Refactoring Engine")
    parser.add_argument("--json", action="store_true", help="Emit JSON output for M2M ergonomics")
    parser.add_argument("--dry-run", action="store_true", help="Simulate changes without writing to disk")
    args = parser.parse_args()

    if not AGENTS_PATH.exists():
        err_msg = f"Archivo no encontrado: {AGENTS_PATH}"
        if args.json:
            print(json.dumps({"status": "ERROR", "error": err_msg}))
        else:
            print(f"[-] {err_msg}", file=sys.stderr)
        return 1

    content = AGENTS_PATH.read_text(encoding="utf-8")
    initial_rule_tags = len(re.findall(r"<RULE\[", content))

    # 1. Crear backup atómico
    if not args.dry_run:
        shutil.copy2(AGENTS_PATH, BACKUP_PATH)

    # 2. Rescatar bullets de sovereign_exergy_nomenclature antes de borrarla
    exergy_nom_block, content = extract_rule_block(content, "sovereign_exergy_nomenclature")
    
    # Extraer bullets relevantes: Sovereign Dual-License y Documentación Grado Militar/Financiero
    dual_license_bullet = "- **Sovereign Dual-License (INV_C5_17):** Toda mención a licencias debe referirse a la estructura *Sovereign Dual-License*: \"SOVEREIGN TIER\" (Gratis para uso individual) y \"ENTERPRISE TIER\" (Requiere `BABYLON60_LICENSE_KEY`), protegiendo el ecosistema contra recolección de datos (Anti-Harvesting) e IAs parásitas."
    military_doc_bullet = "- **Documentación Grado Militar/Financiero:** Especificaciones, manifiestos y scripts de despliegue (`deploy.sh`) deben estar redactados en inglés riguroso formal, sin coloquialismos, manteniendo la estética *Industrial Noir 2026 / C5-REAL*."

    # Inyectar estos bullets en english_naming_toponymy_standard
    toponymy_pattern = r"(<RULE\[english_naming_toponymy_standard\]>.*?)(</RULE\[english_naming_toponymy_standard\]>)"
    matches = re.findall(toponymy_pattern, content, flags=re.DOTALL)
    assert len(matches) == 1, "Fallo al localizar <RULE[english_naming_toponymy_standard]>"
    
    replacement_toponymy = rf"\1{dual_license_bullet}\n{military_doc_bullet}\n\2"
    content = re.sub(toponymy_pattern, replacement_toponymy, content, count=1, flags=re.DOTALL)

    # 3. Fusionar thermodynamic_empiricism_invariant dentro de ultrathink_master_protocol
    empiricism_block, content = extract_rule_block(content, "thermodynamic_empiricism_invariant")
    
    empiricism_bullets = (
        "- **Orquestación $P \\times S$ Controlada & Auditoría `ru_nivcsw`:** Al ejecutar barridos de concurrencia sobre repositorios o tareas paralelas, desduplicar parejas $P \\times S$ con `dict.fromkeys`, aplicar acotamiento `--limit` y registrar los cambios de contexto involuntarios (`ru_nivcsw` vía `resource.getrusage()`) para detectar el acantilado de saturación del scheduler y prevenir el *thrashing* de memoria unificada en Apple Silicon ($P \\approx \\text{Cores físicos}, S \\approx 1\\dots2$).\n"
        "- **Prioridad Axiomática de Determinismo (Ledger-First):** En cargas críticas (hashes, auditorías C5, firmas SCITT), el throughput bruto es inferior en jerarquía al determinismo estricto. La concurrencia DEBE ser modelada como un mapeo inmutable (índices estables de chunks + *Merkle-combine*) garantizando cero entropía de output."
    )

    ultrathink_pattern = r"(<RULE\[ultrathink_master_protocol\]>.*?)(-\s*\*\*Orquestación P \\times S Controlada:\*\*.*?\n)(.*?)(</RULE\[ultrathink_master_protocol\]>)"
    matches = re.findall(ultrathink_pattern, content, flags=re.DOTALL)
    assert len(matches) == 1, "Fallo al localizar la regla ultrathink_master_protocol para fusión"
    
    content = re.sub(ultrathink_pattern, rf"\1{empiricism_bullets}\n\3\4", content, count=1, flags=re.DOTALL)

    # 4. Eliminar exergy_communication_cunado_closure (purga de anergía)
    cunado_block, content = extract_rule_block(content, "exergy_communication_cunado_closure")

    # 5. Extraer reglas locales de entorno a ENVIRONMENT.md
    local_rules = [
        "whatsapp_ipc_baileys_robustness",
        "naroa_twin_domains_deploy_protocol",
        "ide_git_freeze_invariant",
        "c5_real_web_toolchain_homogeneity",
    ]

    extracted_env_blocks = []
    for rule_name in local_rules:
        block, content = extract_rule_block(content, rule_name)
        extracted_env_blocks.append(block)

    # Escribir ENVIRONMENT.md con el encabezado C5-REAL
    env_header = (
        "# C5-REAL ENVIRONMENT RULES (Local Host Infrastructure & Environment Invariants)\n\n"
        "> Las siguientes reglas corresponden exclusivamente a la infraestructura local, rutas fijadas\n"
        "> y configuraciones de entorno específicas del host actual.\n\n"
    )
    env_body = env_header + "\n\n".join(extracted_env_blocks) + "\n"

    # Clean multi-newlines in content
    content = re.sub(r"\n{3,}", "\n\n", content).strip() + "\n"

    final_rule_tags = len(re.findall(r"<RULE\[", content))
    extracted_tags_count = len(extracted_env_blocks)
    deleted_tags_count = 3  # thermodynamic_empiricism, exergy_communication_cunado_closure, sovereign_exergy_nomenclature

    # Verificación de invariante de etiquetas
    assert final_rule_tags == initial_rule_tags - extracted_tags_count - deleted_tags_count, (
        f"Invariante de etiquetas violado: iniciales={initial_rule_tags}, finales={final_rule_tags}, "
        f"extraídas={extracted_tags_count}, eliminadas={deleted_tags_count}"
    )

    if not args.dry_run:
        AGENTS_PATH.write_text(content, encoding="utf-8")
        ENV_PATH.write_text(env_body, encoding="utf-8")

    result_data = {
        "status": "SUCCESS",
        "backup_created": str(BACKUP_PATH),
        "initial_rules_count": initial_rule_tags,
        "final_rules_count": final_rule_tags,
        "extracted_to_environment": extracted_tags_count,
        "purged_rules": deleted_tags_count,
        "environment_file": str(ENV_PATH),
        "dry_run": args.dry_run,
    }

    if args.json:
        print(json.dumps(result_data, indent=2))
    else:
        print("=" * 72)
        print("█ REFACTORIZACIÓN ATÓMICA DE AGENTS.md Y ENVIRONMENT.md COMPLETADA")
        print("=" * 72)
        print(f"  ✓ Backup creado            : {BACKUP_PATH}")
        print(f"  ✓ Reglas iniciales en AGENTS: {initial_rule_tags}")
        print(f"  ✓ Reglas finales en AGENTS  : {final_rule_tags}")
        print(f"  ✓ Extraídas a ENVIRONMENT  : {extracted_tags_count} (Rutas locales/Zone IDs)")
        print(f"  ✓ Purgadas/Fusionadas       : {deleted_tags_count} (Empirismo, Cuñado, Nomenclatura)")
        print(f"  ✓ Invariante de Etiquetas  : VERIFICADO (0 Huérfanos)")
        print(f"  ✓ Archivo Creado           : {ENV_PATH}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
