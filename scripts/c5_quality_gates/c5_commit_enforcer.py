#!/usr/bin/env python3
"""
c5_commit_enforcer.py
=============================================================================
BABYLON-60 / C5-REAL — Validador Determinista de Proof of Work Semántico en Commits
Valida en silicio la gramática dual, el suelo de entropía de Shannon y la cota de ruido.
=============================================================================
"""

import sys
import re
import math
from collections import Counter
from pathlib import Path

# Formatos Canónicos Permitidos:
# 1. Axiomático C5: [AX-XX] DOMAIN: Description
AXIOMATIC_RE = re.compile(r"^\[AX-\d+\]\s+[A-Z0-9\-_]+:\s+.+$")

# 2. Conventional Commits con o sin scope: feat(scope): desc / feat: desc
CONVENTIONAL_RE = re.compile(
    r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)"
    r"(\([a-zA-Z0-9_\-\.\/]+\))?:\s+.+$"
)

def calculate_shannon_entropy(text: str) -> float:
    if not text:
        return 0.0
    counts = Counter(text)
    total = len(text)
    entropy = 0.0
    for count in counts.values():
        p = count / total
        entropy -= p * math.log2(p)
    return round(entropy, 4)

def validate_commit_msg(msg: str) -> tuple[bool, str]:
    lines = [l for l in msg.splitlines() if not l.startswith("#")]
    if not lines or not "".join(lines).strip():
        return False, "Mensaje de commit vacío o solo contiene comentarios."

    first_line = lines[0].strip()

    # 1. Longitud de primera línea
    if len(first_line) < 15:
        return False, f"Primera línea demasiado corta ({len(first_line)} chars < 15 chars). Falta densidad semántica."
    if len(first_line) > 100:
        return False, f"Primera línea demasiado larga ({len(first_line)} chars > 100 chars). Condensa el subject."

    # 2. Gramática Dual
    is_axiomatic = bool(AXIOMATIC_RE.match(first_line))
    is_conventional = bool(CONVENTIONAL_RE.match(first_line))

    if not (is_axiomatic or is_conventional):
        return False, (
            "Gramática inválida. El commit DEBE cumplir una de las dos formas canónicas:\n"
            "  1. Axiomática C5:      [AX-N] DOMINIO: Descripción causal\n"
            "  2. Conventional Commit: type(scope): Descripción causal\n"
            f"Mensaje evaluado: '{first_line}'"
        )

    # 3. Entropía de Shannon
    entropy = calculate_shannon_entropy(first_line)
    ENTROPY_FLOOR = 3.50
    if entropy < ENTROPY_FLOOR:
        return False, (
            f"Entropía semántica insuficiente ({entropy:.2f} bits/char < {ENTROPY_FLOOR} bits/char).\n"
            "El mensaje presenta baja variedad léxica o redundancia (Cheap Talk detectado)."
        )

    # 4. Prohibición de punto final en primera línea
    if first_line.endswith("."):
        return False, "El subject del commit no debe terminar con punto final ('.')."

    return True, f"Aprobado. Formato: {'AXIOMÁTICO' if is_axiomatic else 'CONVENTIONAL'} | H = {entropy:.2f} bits/char"

def main():
    if len(sys.argv) < 2:
        print("Uso: c5_commit_enforcer.py <ruta_commit_msg>")
        sys.exit(1)

    msg_file = Path(sys.argv[1])
    if not msg_file.exists():
        print(f"Error: No existe el archivo {msg_file}")
        sys.exit(1)

    raw_msg = msg_file.read_text(encoding="utf-8", errors="replace")
    valid, reason = validate_commit_msg(raw_msg)

    if not valid:
        print("\n" + "=" * 70)
        print("❌ [C5-GATE · COMMIT-MSG REJECTED] Fricción Epistémica Insuficiente")
        print("=" * 70)
        print(f"Motivo: {reason}")
        print("=" * 70 + "\n")
        sys.exit(1)

    print(f"✓ [C5-GATE · COMMIT-MSG PASSED] {reason}")
    sys.exit(0)

if __name__ == "__main__":
    main()
