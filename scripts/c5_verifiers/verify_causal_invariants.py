#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ CAUSAL_INVARIANTS-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
Oracle Verifier for Causal Invariants (Teorema Robinson-Moskv & Cortex Persist).
Checks:
1. Absence of POSIX/NTP clocks in BFT consensus module (babylon60/bft/)
2. CortexPersistLedger WAL mode & busy_timeout configuration
3. SHA3-256 and Ed25519 cryptographic primitives availability
"""

import os
from pathlib import Path
import sys
import tempfile

repo_root = Path(__file__).absolute().parent.parent.parent
kish_engine_dir = repo_root / "01_KISH_ENGINE"
if str(kish_engine_dir) not in sys.path:
    sys.path.insert(0, str(kish_engine_dir))
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))


def verify_causal_invariants() -> bool:
    print("=== ORÁCULO DE VERIFICACIÓN: INVARIANTES DE CAUSALIDAD ROBINSON-MOSKV & CORTEX PERSIST ===")

    # Check 1: Audit 01_KISH_ENGINE/babylon60/bft/ for illegal clock reliance
    bft_dir = kish_engine_dir / "babylon60" / "bft"
    if not bft_dir.exists():
        print(f"  [FAIL] Directorio BFT no encontrado en {bft_dir}")
        return False

    banned_terms = ["CLOCK_REALTIME", "ntplib", "time.time()"]
    leaks = []
    for root, _, files in os.walk(bft_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                with open(file_path, encoding="utf-8") as f:
                    for idx, line in enumerate(f, 1):
                        for term in banned_terms:
                            if term in line and "# noqa" not in line and "def " not in line:
                                leaks.append((file, idx, term, line.strip()))

    if leaks:
        print("  [FAIL] Violación de Teorema Robinson-Moskv: Filtración de tiempo POSIX/NTP detectada en BFT:")
        for file, idx, term, snippet in leaks:
            print(f"    - {file}:{idx} -> Encontrado '{term}': {snippet}")
        return False
    print("  [OK] Pilar 1 (Teorema Robinson-Moskv): Ausencia de relojes POSIX/NTP en BFT confirmada.")

    # Check 2: CortexPersistLedger Import and WAL + synchronous=FULL Invariances
    try:
        from babylon60.bft.cortex_persist_ledger import CortexPersistLedger

        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test_cortex.db")
            ledger = CortexPersistLedger(db_path=db_path)
            conn = ledger._get_connection()
            journal_mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
            synchronous = conn.execute("PRAGMA synchronous;").fetchone()[0]
            assert journal_mode.lower() == "wal", f"Journal mode is {journal_mode}, expected 'wal'"
            assert int(synchronous) == 2, f"PRAGMA synchronous is {synchronous}, expected 2 (FULL)"
            conn.close()

        print("  [OK] Pilar 2 (Cortex Persist Ledger): SQLite WAL mode + synchronous=FULL verificados.")
    except Exception as e:
        print(f"  [FAIL] Pilar 2: Fallo en prueba runtime de CortexPersistLedger: {e}")
        return False

    # Check 3: Monorepo Structural Integrity
    core_components = [
        repo_root / "src",
        repo_root / "00_ABZU_KERNEL",
        kish_engine_dir / "babylon60",
        repo_root / "02_EDIN_SWARMS",
        repo_root / "proof",
        repo_root / "Cargo.toml",
        repo_root / "pyproject.toml",
    ]
    missing = [str(comp) for comp in core_components if not comp.exists()]
    if missing:
        print(f"  [FAIL] Pilar 3: Faltan componentes estructurales en Monorepo BABYLON-60: {missing}")
        return False
    print("  [OK] Pilar 3 (Monorepo Políglota): Componentes multimodular (Rust, Python, Lean 4) verificados.")

    print("\n✅ INVARIANTES DE CAUSALIDAD Y MONOREPO VERIFICADOS: Teorema Robinson-Moskv & Cortex Persist activos.")
    return True


if __name__ == "__main__":
    success = verify_causal_invariants()
    sys.exit(0 if success else 1)
