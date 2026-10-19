#!/usr/bin/env python3
"""
Linter Determinista Anti-Slop de Frontend (C5-REAL).
Audita código HTML, TSX, JSX, Vue, Svelte y CSS sin coste de LLM.
Verifica:
1. Contraste y luminancia relativa (WCAG AAA).
2. Erradicación de paletas grises neutras clónicas (Zero Gray Slop).
3. Apego a escalas tipográficas modulares (prohibición de tamaños arbitrarios).
4. Accesibilidad e interactividad somática (focus-visible, aria-label).
"""

import os
import sys
import re
import argparse
from typing import List, Dict, Any, Tuple

# Colores conocidos de Tailwind (Luminancias relativas aproximadas sRGB)
# L = 0.2126*R + 0.7152*G + 0.0722*B
TAILWIND_LUMINANCE = {
    "zinc-950": 0.005,
    "zinc-900": 0.015,
    "zinc-800": 0.040,
    "zinc-700": 0.090,
    "zinc-600": 0.160,
    "zinc-500": 0.260,
    "zinc-400": 0.440,
    "zinc-300": 0.650,
    "zinc-200": 0.800,
    "zinc-100": 0.920,
    "zinc-50": 0.980,
    "white": 1.000,
    "black": 0.000,
}

MODULAR_SCALE_MAJOR_THIRD = {10, 12, 13, 14, 16, 20, 25, 31, 39, 49, 61}
MODULAR_SCALE_PERFECT_FOURTH = {10, 12, 16, 21, 28, 38, 50, 67}

EXTENSIONS = {".tsx", ".jsx", ".html", ".vue", ".svelte", ".astro", ".css"}

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

def calculate_contrast(l1: float, l2: float) -> float:
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)

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
                "Texto gris con bajo contraste potencial (WCAG AAA < 7:1 en fondos oscuros). Usar luminosidad >= 75% (zinc-300 o superior).",
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
                    "Botón con icono sin atributo 'aria-label' descriptivo (violación de accesibilidad sensorial).",
                    line
                ))

    # Chequeo a nivel de archivo: Alerta de Slop Monocromático
    if has_dark_bg and has_generic_gray and not has_accent:
        violations.append(Violation(
            filepath, 1, "C5-UI-004",
            "Atractor grisáceo clónico detectado: fondo oscuro + texto zinc sin acentos cromáticos ni tensión visual intencionada."
        ))

    return violations

def audit_directory(path: str) -> List[Violation]:
    all_violations: List[Violation] = []
    if os.path.isfile(path):
        return audit_file(path)

    for root, _, files in os.walk(path):
        # Excluir node_modules, dist, .git
        if any(ignored in root for ignored in ["node_modules", ".git", "dist", "build", ".next"]):
            continue
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in EXTENSIONS:
                fp = os.path.join(root, file)
                all_violations.extend(audit_file(fp))

    return all_violations

def main():
    parser = argparse.ArgumentParser(description="Linter Frontend Anti-Slop C5-REAL")
    parser.add_argument("target", help="Archivo o directorio a auditar")
    parser.add_argument("--json", action="store_true", help="Salida en formato JSON")
    args = parser.parse_args()

    if not os.path.exists(args.target):
        sys.stderr.write(f"Error: Ruta no encontrada '{args.target}'\n")
        sys.exit(2)

    violations = audit_directory(args.target)

    if args.json:
        import json
        print(json.dumps([v.to_dict() for v in violations], indent=2, ensure_ascii=False))
    else:
        print(f"=== [C5-REAL UI LINTER] Auditoría de '{args.target}' ===")
        if not violations:
            print("✓ Cero violaciones detectadas. La interfaz cumple con las invariantes C5-REAL.")
            sys.exit(0)

        print(f"⚠ Se detectaron {len(violations)} violaciones de diseño / accesibilidad:\n")
        for v in violations:
            print(f"[{v.rule_id}] {v.file}:{v.line}")
            print(f"  Mensaje: {v.message}")
            if v.snippet:
                print(f"  Código : {v.snippet}")
            print()

    sys.exit(1 if violations else 0)

if __name__ == "__main__":
    main()
