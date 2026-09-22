#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
Oracle Verifier for Agent Ontological Value (V_A).
Checks:
1. ADT Primitives in babylon60.types.algebraic
2. Zero existence gap for primary modules
3. Disk anergy footprint check (< 500 MB target anergy threshold)
"""

import os
import sys
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
kish_dir = os.path.join(repo_root, "01_KISH_ENGINE")
if kish_dir not in sys.path:
    sys.path.insert(0, kish_dir)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

def verify_va() -> bool:
    print("=== ORÁCULO DE VERIFICACIÓN: VALOR ONTOLÓGICO PARA EL AGENTE (V_A) ===")
    
    # Check 1: ADTs
    try:
        import babylon60.types as t
        res = t.Ok(42).map(lambda x: x * 2)
        assert res.unwrap() == 84
        opt = t.Some("exergy").map(lambda s: s.upper())
        assert opt.unwrap() == "EXERGY"
        assert t.Nothing().is_none()
        print("  [OK] Pilar 1: Tipos Algebraicos Primordiales (Result/Option ADT) Operativos.")
    except Exception as e:
        print(f"  [FAIL] Pilar 1: ADT failure: {e}")
        return False
        
    # Check 2: Existence Gap check for local modules
    required_paths = [
        os.path.join(repo_root, "01_KISH_ENGINE", "babylon60"),
        os.path.join(repo_root, "scripts"),
        os.path.join(repo_root, "crates"),
    ]
    for p in required_paths:
        if not os.path.exists(p):
            print(f"  [FAIL] Pilar 2: Módulo esencial '{os.path.basename(p)}' no encontrado en {p}.")
            return False
    print("  [OK] Pilar 2: Anclaje de Existencia de Módulos Locales Verificado.")


    # Check 3: Anergy Check
    target_path = "target"
    if os.path.exists(target_path):
        sz_mb = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(target_path) for f in fs) / (1024*1024)
        if sz_mb > 500:
            print(f"  [WARN] Pilar 3: Anergía en target/ excede umbral ({sz_mb:.2f} MB > 500 MB). Recomienda cargo clean.")
        else:
            print(f"  [OK] Pilar 3: Anergía física en disco bajo control ({sz_mb:.2f} MB).")
    else:
        print("  [OK] Pilar 3: target/ inerte/limpio (0 MB de anergía).")

    print("\n✅ V_A VERIFICADO: El sistema ofrece Valor Ontológico Pleno para el Agente Computacional.")
    return True

if __name__ == "__main__":
    success = verify_va()
    sys.exit(0 if success else 1)
