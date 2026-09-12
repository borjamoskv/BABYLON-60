#!/usr/bin/env python3
"""
BABYLON-60 — Linter de Estética y Rigor de Documentación (C5-REAL)
Audita archivos Markdown en docs/ para verificar invariantes visuales:
- Insignias SVG (Shields.io) de estado y régimen.
- Alertas nativas de GitHub (> [!NOTE], > [!IMPORTANT], etc.).
- Sintaxis limpia de diagramas Mermaid y bloques de KaTeX.
- Alineación correcta de tablas GFM.
"""

import os
import sys
import re
import argparse

DOCS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs"))

REQUIRED_BADGE_PATTERN = r"img\.shields\.io/badge/"
UNCONVERTED_BLOCKQUOTE = r"^>\s*\*\*(Theorem|Teorema|Definition|Definición|Warning|Advertencia|Important|Importante)\*\*"

class AestheticLinter:
    def __init__(self, target_dir) -> None:
        self.target_dir = target_dir
        self.errors = []
        self.warnings = []

    def log_error(self, filepath, line_num, code, msg) -> None:
        rel_path = os.path.relpath(filepath, self.target_dir)
        self.errors.append(f"❌ [ERROR] [{code}] {rel_path}:{line_num} -> {msg}")

    def log_warning(self, filepath, line_num, code, msg) -> None:
        rel_path = os.path.relpath(filepath, self.target_dir)
        self.warnings.append(f"⚠️ [WARN]  [{code}] {rel_path}:{line_num} -> {msg}")

    def audit_file(self, filepath) -> None:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        content = "".join(lines)
        filename = os.path.basename(filepath)

        # Skip non-documentation or system metadata files
        if filename in ["skills.json", "CANARY_TOKENS.md"]:
            return

        # Rule 1: Header Badges Check
        if not re.search(REQUIRED_BADGE_PATTERN, content):
            self.log_warning(filepath, 1, "BADGE_MISSING", "El documento carece de insignias Shields.io de estado C5-REAL.")

        in_code_block = False
        in_mermaid_block = False
        mermaid_start_line = 0

        for idx, line in enumerate(lines, 1):
            stripped = line.strip()

            # Track code blocks
            if stripped.startswith("```"):
                if not in_code_block:
                    in_code_block = True
                    if stripped == "```mermaid":
                        in_mermaid_block = True
                        mermaid_start_line = idx
                else:
                    in_code_block = False
                    in_mermaid_block = False
                continue

            # Ignore lines inside code blocks (except Mermaid validation)
            if in_code_block and not in_mermaid_block:
                continue

            # Rule 2: Unconverted plain blockquotes
            if not in_code_block and re.match(UNCONVERTED_BLOCKQUOTE, stripped, re.IGNORECASE):
                self.log_error(filepath, idx, "PLAIN_BLOCKQUOTE", "Uso de cita en negrita plana en lugar de alerta nativa GFM (> [!NOTE], > [!IMPORTANT]).")

            # Rule 3: Malformed GFM Alert syntax
            if not in_code_block and stripped.startswith("> [!") and not re.match(r"^>\s*\[\!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]", stripped):
                self.log_error(filepath, idx, "BAD_ALERT_TAG", f"Etiqueta de alerta GFM inválida o malformada: '{stripped}'.")

            # Rule 4: Table Separator alignment
            if not in_code_block and "|" in stripped and stripped.startswith("|"):
                if re.match(r"^\|(\s*:?-+:?\s*\|)+$", stripped):
                    if not (":---" in stripped or "---:" in stripped or "---" in stripped):
                        self.log_warning(filepath, idx, "UNALIGNED_TABLE", "Separador de tabla Markdown sin sintaxis de alineación clara.")

        # Rule 5: Unclosed Mermaid Block
        if in_mermaid_block:
            self.log_error(filepath, mermaid_start_line, "UNCLOSED_MERMAID", "Bloque de diagrama Mermaid sin cerrar con ```.")

    def run(self) -> int:
        md_files = []
        for root, _, files in os.walk(self.target_dir):
            for file in files:
                if file.endswith(".md") and not file.startswith("."):
                    md_files.append(os.path.join(root, file))

        print(f"🔍 Auditando estética y rigor visual en {len(md_files)} archivos Markdown en {self.target_dir}...")
        for filepath in md_files:
            self.audit_file(filepath)

        print("\n" + "=" * 60)
        print("📊 RESUMEN DE AUDITORÍA VISUAL C5-REAL")
        print("=" * 60)

        if self.warnings:
            print(f"\n⚠️  ADVERTENCIAS DETECTADAS ({len(self.warnings)}):")
            for w in self.warnings[:15]:
                print(f"  {w}")
            if len(self.warnings) > 15:
                print(f"  ... y {len(self.warnings) - 15} advertencias adicionales.")

        if self.errors:
            print(f"\n❌ ERRORES CRÍTICOS DETECTADOS ({len(self.errors)}):")
            for e in self.errors:
                print(f"  {e}")
            print("\n❌ VERDICTO: AUDITORÍA FALLIDA — Corrija los errores de formato.")
            return 1
        else:
            print("\n✅ VERDICTO: AUDITORÍA COMPLETADA EXITOSAMENTE — 100% Conformidad Visual C5-REAL.")
            return 0

def main() -> None:
    parser = argparse.ArgumentParser(description="Linter de Estética y Rigor de Documentación C5-REAL")
    parser.add_argument("--dir", default=DOCS_DIR, help="Directorio objetivo de documentación")
    args = parser.parse_args()

    linter = AestheticLinter(args.dir)
    sys.exit(linter.run())

if __name__ == "__main__":
    main()
