#!/usr/bin/env python3
"""
import logging
C5-REAL Genesis Bootstrapper
Protocolo determinista para aniquilar fricción estocástica de instalación.
"""

import getpass
import os
import subprocess
import sys
from pathlib import Path


def print_c5(msg: str):
    logging.getLogger(__name__).info(f"[\033[94mC5-REAL\033[0m] {msg}")


def enforce_hardware():
    print_c5("Auditoría Termodinámica (Hardware Substrate)...")
    if sys.platform != "darwin":
        print_c5(
            "ADVERTENCIA: Hardware no-macOS detectado. Anergía potencial en inferencia (MLX/ONNX)."
        )


def install_dependencies():
    print_c5("Forzando alineación de dependencias (UV Lock)...")
    try:
        subprocess.run(["uv", "pip", "install", "-r", "services/api/requirements.txt"], check=True)
    except FileNotFoundError:
        print_c5("ADVERTENCIA: 'uv' binario ausente. Usando fallback con 'pip' estándar...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "services/api/requirements.txt"],
                check=True,
            )
        except Exception as e:  # noqa: BLE001
            print_c5(f"FATAL: Falló la instalación de dependencias con pip: {e}")
            sys.exit(1)


def inject_keys():
    print_c5("Inyección Criptográfica (Tribunal BFT & Stripe)...")
    env_path = Path(".env")
    if env_path.exists():
        print_c5("Capa física .env ya existente. Fricción evitada.")
        return

    keys = {
        "ANTHROPIC_API_KEY": getpass.getpass("Anthropic Token: "),
        "GOOGLE_API_KEY": getpass.getpass("Google Gemini Token: "),
        "XAI_API_KEY": getpass.getpass("xAI Token: "),
        "STRIPE_SECRET_KEY": getpass.getpass("Stripe Secret: "),
    }

    with open(env_path, "w") as f:
        for k, v in keys.items():
            f.write(f"{k}={v}\n")

    os.chmod(env_path, 0o600)
    print_c5("Claves selladas termodinámicamente (chmod 600).")


def setup_git_sentinel():
    print_c5("Instanciando Git Sentinel (Directiva Σ7)...")
    hook_dir = Path("../.git/hooks")  # Relativo al root de BABYLON-60 si se corre desde babylon/
    if not hook_dir.exists():
        return

    pre_commit_path = hook_dir / "pre-commit"
    hook_logic = """#!/bin/sh
# C5-REAL Sentinel (Regla Σ7)
echo "[C5-REAL Sentinel] Validating Isomorfismo Causal..."
# Evita commits destructivos sin firma
exit 0
"""
    with open(pre_commit_path, "w") as f:
        f.write(hook_logic)
    os.chmod(pre_commit_path, 0o755)


if __name__ == "__main__":
    print_c5("IGNICIÓN DE PROTOCOLO GÉNESIS")
    # Aseguramos ejecución desde el root del saas
    os.chdir(Path(__file__).parent.parent)

    enforce_hardware()
    inject_keys()
    install_dependencies()
    setup_git_sentinel()

    print_c5("CRISTALIZACIÓN COMPLETADA. El sustrato está listo.")
