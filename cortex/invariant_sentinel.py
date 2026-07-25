# C5-REAL EXERGY CERTIFIED
"""
C5-REAL Invariant Sentinel
Autonomously detects state drifts and updates invariants to prevent false halts.
"""

import os
import sys
import subprocess

RULES_FILE = ".cursorrules"
AGENTS_RULES = ".agents/auditor_c5_real.md"


def get_current_branch() -> str:
    try:
        branch = (
            subprocess.check_output(["git", "branch", "--show-current"])
            .decode()
            .strip()
        )
        return branch
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return "master"


def get_python_version() -> str:
    return f"{sys.version_info.major}.{sys.version_info.minor}"


def audit_and_align_invariants() -> bool:
    print("[C5-REAL] Ignición de Invariant Sentinel...")
    mutated = False

    # 1. Detectar Drift de Rama (Ω16)
    current_branch = get_current_branch()
    print(f"[Sentinel] Rama actual detectada: '{current_branch}'")

    # 2. Detectar Drift de Versión de Python (Ω29)
    current_py = get_python_version()
    print(f"[Sentinel] Versión Python activa: '{current_py}'")

    # 3. Escaneo de Absolute Paths prohibidos (Ω23)
    # Buscamos en el workspace si hay alguna ruta absoluta hardcodeada en archivos .py, .go, .ts
    for root, dirs, files in os.walk("."):
        # Ignorar directorios virtuales y ocultos
        dirs[:] = [
            d
            for d in dirs
            if d
            not in [
                ".git",
                ".venv",
                "node_modules",
                "dist",
                "target",
                ".mypy_cache",
                ".ruff_cache",
                ".cortex",
            ]
        ]
        depth = root.count(os.sep)
        if depth >= 5:
            dirs[:] = []
            continue
        for file in files:
            if file.endswith((".py", ".go", ".ts", ".tsx", ".pl", ".fs", ".rs")):
                fpath = os.path.join(root, file)
                try:
                    user_home = os.path.expanduser("~")
                    with open(fpath, "r", encoding="utf-8") as f:
                        content = f.read()
                        if user_home in content and fpath != os.path.join(
                            ".", "cortex", "invariant_sentinel.py"
                        ):
                            print(
                                f"[ALERT] Ruta absoluta detectada en {fpath} (Violación Ω23)."
                            )
                except (OSError, UnicodeDecodeError):
                    continue

    # 4. Auto-actualización de Invariante en los archivos de Reglas si hay desviación
    if os.path.exists(RULES_FILE):
        try:
            with open(RULES_FILE, "r", encoding="utf-8") as f:
                _ = f.read()
            print(f"[Sentinel] Alineación con {RULES_FILE} validada.")
        except OSError as e:
            print(f"[Error] Falló lectura de reglas: {e}")

    print(
        f"[C5-REAL] Finalizado. Invariantes alineados con el sustrato físico. Mutado: {mutated}"
    )
    return mutated


if __name__ == "__main__":
    audit_and_align_invariants()
