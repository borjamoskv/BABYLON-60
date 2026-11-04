#!/usr/bin/env python3
"""Partial lexical frontend checks. No DOM, computed CSS or WCAG certification."""

import os
import sys
import re
import argparse
from typing import List, Dict, Any

MODULAR_SCALE_MAJOR_THIRD = {10, 12, 13, 14, 16, 20, 25, 31, 39, 49, 61}
MODULAR_SCALE_PERFECT_FOURTH = {10, 12, 16, 21, 28, 38, 50, 67}

EXTENSIONS = {".tsx", ".jsx", ".html", ".vue", ".svelte", ".astro", ".css"}
EXCLUDED_DIRS = {"node_modules", ".git", "dist", "build", ".next"}
UNVERIFIED = ["rendered_contrast", "accessible_names", "focus_states", "css_cascade"]

class Violation:
    def __init__(self, file: str, line: int, rule_id: str, message: str, snippet: str = ""):
        self.file = file
        self.line = line
        self.rule_id = rule_id
        self.message = message
        self.snippet = snippet.strip()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file": self.file,
            "line": self.line,
            "rule": self.rule_id,
            "message": self.message,
            "snippet": self.snippet
        }

def audit_file(filepath: str) -> List[Violation]:
    violations: List[Violation] = []
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    has_dark_bg = False
    has_accent = False
    has_generic_gray = False

    for idx, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()

        # Detección de fondo oscuro genérico
        if re.search(r'bg-(zinc|neutral|stone|gray|slate)-(900|950)', line):
            has_dark_bg = True

        # Detección de acento cromático
        if re.search(r'(text|bg|border)-(emerald|cyan|indigo|amber|rose|teal|violet|blue|orange|red)-(400|500|600)', line):
            has_accent = True

        # Invariante 1 & 2: Texto gris oscuro sobre fondo oscuro (Contraste deficiente)
        if re.search(r'text-(zinc|gray|neutral|slate)-(500|600)', line):
            has_generic_gray = True
            violations.append(Violation(
                filepath, idx, "C5-UI-001",
                "Clase gris detectada: revisar contraste con los estilos y fondo renderizados; no se ha medido el ratio.",
                line
            ))

        # Invariante 3: Tamaños arbitrarios de fuente desalineados de la escala modular
        arbitrary_font = re.findall(r'text-\[(\d+)px\]', line)
        for px_str in arbitrary_font:
            px = int(px_str)
            if px not in MODULAR_SCALE_MAJOR_THIRD and px not in MODULAR_SCALE_PERFECT_FOURTH:
                violations.append(Violation(
                    filepath, idx, "C5-UI-002",
                    f"Tamaño arbitrario de fuente text-[{px}px] rompe la escala modular armónica. Alinear a razón 1.25 o 1.333.",
                    line
                ))

        # Invariante 5: Botón solo con icono sin aria-label
        if "<button" in line and "aria-label" not in line:
            # Comprobar si las siguientes 3 líneas tienen <svg> y cierran sin texto
            chunk = "".join(lines[idx-1:min(len(lines), idx+4)])
            if "<svg" in chunk and not re.search(r'<button[^>]*>[^<]*[a-zA-Z0-9]+', chunk):
                violations.append(Violation(
                    filepath, idx, "C5-UI-003",
                    "Posible botón con icono sin aria-label: comprobar su nombre accesible en el DOM renderizado.",
                    line
                ))

    # Chequeo a nivel de archivo: Alerta de Slop Monocromático
    if has_dark_bg and has_generic_gray and not has_accent:
        violations.append(Violation(
            filepath, 1, "C5-UI-004",
            "Atractor grisáceo clónico detectado: fondo oscuro + texto zinc sin acentos cromáticos ni tensión visual intencionada."
        ))

    return violations

def collect_files(path: str) -> List[str]:
    if os.path.isfile(path):
        return [path] if os.path.splitext(path)[1].lower() in EXTENSIONS else []
    candidates: List[str] = []
    for root, dirs, files in os.walk(path):
        dirs[:] = sorted(name for name in dirs if name not in EXCLUDED_DIRS)
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in EXTENSIONS:
                candidates.append(os.path.join(root, file))
    return sorted(candidates)


def audit_directory(path: str) -> List[Violation]:
    return [v for filepath in collect_files(path) for v in audit_file(filepath)]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", help="Archivo o directorio a auditar")
    parser.add_argument("--json", action="store_true", help="Salida en formato JSON")
    args = parser.parse_args()

    if not os.path.exists(args.target):
        sys.stderr.write(f"Error: Ruta no encontrada '{args.target}'\n")
        sys.exit(2)

    files = collect_files(args.target)
    violations = [v for filepath in files for v in audit_file(filepath)]
    status = "findings" if violations else "no_lexical_findings" if files else "no_files"

    if args.json:
        import json
        print(json.dumps({
            "schema_version": 2,
            "status": status,
            "scope": "lexical_patterns_only",
            "conformance": "not_verified",
            "files_scanned": len(files),
            "excluded_directories": sorted(EXCLUDED_DIRS),
            "unverified": UNVERIFIED,
            "findings": [v.to_dict() for v in violations],
        }, indent=2, ensure_ascii=False))
    else:
        print(f"Comprobación léxica parcial: {len(files)} archivos en '{args.target}'")
        print("Conformidad WCAG: NO_VERIFICADO. Contraste renderizado, nombres accesibles, foco y cascada CSS no evaluados.")
        if not violations:
            print("Sin hallazgos en los patrones comprobados." if files else "No se encontraron archivos compatibles.")
        else:
            print(f"Se detectaron {len(violations)} indicios para revisión contextual:\n")
        for v in violations:
            print(f"[{v.rule_id}] {v.file}:{v.line}")
            print(f"  Mensaje: {v.message}")
            if v.snippet:
                print(f"  Código : {v.snippet}")
            print()

    sys.exit(2 if not files else 1 if violations else 0)

if __name__ == "__main__":
    main()
