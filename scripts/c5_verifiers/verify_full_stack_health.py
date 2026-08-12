#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ FULL_STACK_HEALTH-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
Oracle Verifier for Full-Stack System Health across:
1. Causal Invariants & Monorepo Topology
2. Rust Kernel compilation & atomic Seqlock layout (cargo check)
3. React Web Frontend TypeScript & Vite build (npm run build)
4. EU AI Act Compliance & Hero Demo execution
"""

import os
import subprocess
import sys

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def run_step(step_name: str, cmd: list[str] | str, cwd: str, env: dict[str, str] | None = None) -> bool:
    print(f"\n[PASO] {step_name}...")
    try:
        current_env = os.environ.copy()
        if env:
            current_env.update(env)
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env=current_env,
            shell=isinstance(cmd, str),
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            print(f"  [OK] {step_name} ejecutado con éxito (código 0).")
            return True
        else:
            print(f"  [FAIL] {step_name} falló (código {result.returncode}).")
            if result.stdout:
                print(f"  --- stdout ---\n{result.stdout.strip()[:1000]}")
            if result.stderr:
                print(f"  --- stderr ---\n{result.stderr.strip()[:1000]}")
            return False
    except Exception as e:
        print(f"  [FAIL] Excepción al ejecutar {step_name}: {e}")
        return False


def verify_full_stack():
    print("========================================================================")
    print("  BABYLON-60 v4.0 Sovereign Hardened — AUDITORÍA DE SALUD FULL STACK")
    print("========================================================================")

    steps = [
        (
            "1. Invariantes de Causalidad & Monorepo",
            [sys.executable, "scripts/c5_verifiers/verify_causal_invariants.py"],
            repo_root,
            None,
        ),
        (
            "2. Rust Kernel Compilation (Cargo Check)",
            ["cargo", "check"],
            repo_root,
            None,
        ),
        (
            "3. Web Frontend Production Build (Vite/React)",
            ["npm", "run", "build"],
            os.path.join(repo_root, "web"),
            None,
        ),
        (
            "4. Demostración Hero Demo & Cumplimiento EU AI Act",
            [sys.executable, "scripts/c5_demos/run_hero_demo.py"],
            repo_root,
            {"PYTHONPATH": "."},
        ),
    ]

    all_passed = True
    for name, cmd, cwd, env in steps:
        if not run_step(name, cmd, cwd, env):
            all_passed = False
            break

    print("\n========================================================================")
    if all_passed:
        print("  ✅ AUDITORÍA DE SALUD FULL STACK EXITOSA — C5-REAL VERIFIED")
        print("  Todas las capas (Rust Kernel, Python, Web Frontend y Compliance) OK.")
    else:
        print("  ❌ AUDITORÍA DE SALUD FULL STACK FALLIDA — Requiere Remediación")
    print("========================================================================")

    return all_passed


if __name__ == "__main__":
    success = verify_full_stack()
    sys.exit(0 if success else 1)
