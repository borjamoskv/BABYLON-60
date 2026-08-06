#!/usr/bin/env python3
import os

TARGET_DIRS = [
    "/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/2_Nucleo_Estatico"
]

EXCLUDE_DIRS = ["docs/theory"] # Already audited

# Payloads per language (only the POPPER part, or both if needed)
POPPER_GO = "// INV-3 POPPER: All theoretical invariants must be empirically falsifiable. Continuous metaphors are rejected.\n"
POPPER_HS = "-- INV-3 POPPER: All theoretical invariants must be empirically falsifiable. Continuous metaphors are rejected.\n"
POPPER_YAML = "# INV-3 POPPER: All theoretical invariants must be empirically falsifiable. Continuous metaphors are rejected.\n"

MD_POPPER_BLOCK = """

---
> [!WARNING]
> **INV-3 POPPER (Falsifiability Block)**
> Este documento ha sido auditado bajo el Invariante C5-REAL. Toda afirmación teórica aquí contenida DEBE ser empíricamente falsable mediante la instanciación de su transición discreta en el Kernel. Se prohíbe explícitamente el reduccionismo continuo y la especulación incomputable.
"""

def inject_after_certified_or_top(content, header, popper_text):
    if "INV-3 POPPER" in content:
        return content, False

    lines = content.split('\n')
    out_lines = []
    injected = False
    for line in lines:
        out_lines.append(line)
        if "C5-REAL EXERGY CERTIFIED" in line and not injected:
            out_lines.append(popper_text.strip())
            injected = True

    if not injected:
        out_lines = [header.strip(), popper_text.strip()] + out_lines

    return '\n'.join(out_lines), True

def process_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    modified = False

    if ext == ".go":
        content, modified = inject_after_certified_or_top(content, "// C5-REAL EXERGY CERTIFIED", POPPER_GO)

    elif ext == ".hs":
        content, modified = inject_after_certified_or_top(content, "-- C5-REAL EXERGY CERTIFIED", POPPER_HS)

    elif ext in [".yaml", ".yml"]:
        content, modified = inject_after_certified_or_top(content, "# C5-REAL EXERGY CERTIFIED", POPPER_YAML)

    elif ext == ".md":
        # .md files were already handled in previous script, but just in case:
        if "INV-3 POPPER" not in content:
            content += MD_POPPER_BLOCK
            modified = True
        if "C5-REAL EXERGY CERTIFIED" not in content[:500]:
            content = "<!-- C5-REAL EXERGY CERTIFIED -->\n" + content
            modified = True

    if modified:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False

def main():
    print("Iniciando auditoría masiva v3 (GO, HS, YAML, MD)...")
    count = 0
    for target in TARGET_DIRS:
        for root, _, files in os.walk(target):
            if any(ex_dir in root for ex_dir in EXCLUDE_DIRS):
                continue

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in [".go", ".hs", ".yaml", ".yml", ".md"]:
                    path = os.path.join(root, file)
                    try:
                        if process_file(path):
                            print(f"Mutado: {path}")
                            count += 1
                    except Exception as e:
                        print(f"Error procesando {path}: {e}")

    print(f"Proceso completado. {count} archivos mutados a topología discreta/falsable.")

if __name__ == "__main__":
    main()
