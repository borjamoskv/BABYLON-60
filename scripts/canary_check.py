#!/usr/bin/env python3
"""Ω-12 — canary_check: verifica que los señuelos canary siguen en el árbol.

ITERA-1 / OPSEC-Ω TASKFORCE-16 · Agente Ω-12 (Canary-Guard).

Los canary tokens (credenciales falsas plantadas) son un *honeypot*:
si alguien (o algo) usa una credencial canary, la alerta del proveedor
(canarytokens.org / AWS / GitHub) delata la intrusión. Este guard hace
dos cosas:

  1. Avisa si un fichero de credencial local que DEBERÍA existir fuera
     del repo aparece DENTRO del árbol (fuga inminente).
  2. Falla el commit/push si un patrón canary declarado en
     `docs/CANARY_TOKENS.md` ha desaparecido del índice (posible purga
     accidental o maliciosa del señuelo).

Exit 0 = OK · Exit 1 = canary perdido o fuga detectada.
Stdlib only. Python 3.10+.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# Ficheros que NUNCA deben estar trackeados (si aparecen → fuga)
FORBIDDEN_TRACKED = [
    ".cortex/master_key.hex",
    ".cortex/solana_keypair.json",
    "20_VAULT",
    ".env",
    ".env.local",
    ".env.production",
]

# Patrones canary esperados en el índice (se declararán al plantarlos).
# Mientras docs/CANARY_TOKENS.md no exista, el guard pasa en modo "idle".
CANARY_MANIFEST = Path("docs/CANARY_TOKENS.md")


def _tracked_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files"], capture_output=True, text=True, check=False
    ).stdout
    return [ln for ln in out.splitlines() if ln]


def main() -> int:
    failures: list[str] = []
    tracked = _tracked_files()

    # 1. Fuga inminente
    for bad in FORBIDDEN_TRACKED:
        if any(f == bad or f.startswith(bad.rstrip("/") + "/") for f in tracked):
            failures.append(f"LEAK: '{bad}' está trackeado en el índice")

    # 2. Canaries declarados pero ausentes
    if CANARY_MANIFEST.exists():
        body = CANARY_MANIFEST.read_text(encoding="utf-8", errors="replace")
        declared = re.findall(r"canary_path:\s*(\S+)", body)
        for path in declared:
            if path not in tracked and not Path(path).exists():
                failures.append(f"CANARY LOST: '{path}' declarado pero ausente")
    else:
        print("[Ω-12] idle: docs/CANARY_TOKENS.md no existe (canaries no plantados aún)")

    if failures:
        for f in failures:
            print(f"[Ω-12 FAIL] {f}", file=sys.stderr)
        return 1
    print("[Ω-12 OK] sin fugas; canaries íntegros (o idle)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
