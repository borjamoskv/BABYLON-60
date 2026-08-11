#!/usr/bin/env python3
"""Ω-16 — verify_p0_rotation: certificador del estado opsec del linaje.

ITERA-1 / OPSEC-Ω TASKFORCE-16 · Agente Ω-16 (Rotation-Verifier, v2).
Reimplementa el verificador del PR muerto #551 contra el linaje NUEVO.

Verifica el LADO REPOSITORIO:
  1. Los paths expuestos no existen en el working tree.
  2. Los paths expuestos no aparecen en TODA la historia git (--all).
  3. .gitignore contiene los patrones de hardening P0.
  4. .gitleaks.toml existe y declara las reglas P0.
  5. .pre-commit-config.yaml existe (capa 0).

Exit 0 = lado repo verde · Exit 1 = fallo (detalle en stdout).
Stdlib only. Python 3.10+.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

EXPOSED_PATHS = [".cortex/master_key.hex", ".cortex/solana_keypair.json", "20_VAULT"]
REQUIRED_GITIGNORE = [".cortex/", "20_VAULT/", "*keypair*.json", "*.pem"]
REQUIRED_GITLEAKS = ["cortex-master-key-hex", "solana-keypair-json"]


def sh(*args: str) -> str:
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, check=False
    ).stdout


def main() -> int:
    failures: list[str] = []
    print("█ OPSEC-Ω VERIFIER — Ω-16 (ITERA-1)")

    for p in EXPOSED_PATHS:
        if Path(p).exists():
            failures.append(f"TREE: {p} existe en el working tree")
        else:
            print(f"  ✓ tree: {p} ausente")

    for p in EXPOSED_PATHS:
        out = sh("log", "--all", "--oneline", "--", p).strip()
        if out:
            failures.append(f"HISTORY: {p} en {len(out.splitlines())} commit(s)")
        else:
            print(f"  ✓ history: {p} sin rastro en --all")

    gi = Path(".gitignore")
    if not gi.exists():
        failures.append("GITIGNORE: no existe")
    else:
        body = gi.read_text(encoding="utf-8", errors="replace")
        for pat in REQUIRED_GITIGNORE:
            if pat in body:
                print(f"  ✓ gitignore: '{pat}'")
            else:
                failures.append(f"GITIGNORE: falta '{pat}'")

    gl = Path(".gitleaks.toml")
    if not gl.exists():
        failures.append("GITLEAKS: no existe .gitleaks.toml")
    else:
        body = gl.read_text(encoding="utf-8", errors="replace")
        for rule in REQUIRED_GITLEAKS:
            if rule in body:
                print(f"  ✓ gitleaks: '{rule}'")
            else:
                failures.append(f"GITLEAKS: falta '{rule}'")

    if Path(".pre-commit-config.yaml").exists():
        print("  ✓ pre-commit: capa 0 presente")
    else:
        failures.append("PRE-COMMIT: falta .pre-commit-config.yaml")

    if failures:
        print()
        for f in failures:
            print(f"  ✗ FAIL: {f}")
        print(f"\n█ VEREDICTO: {len(failures)} fallo(s) — opsec incompleto")
        return 1
    print("\n█ VEREDICTO: lado repositorio VERDE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
