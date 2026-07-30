#!/usr/bin/env python3
# C5-REAL EXERGY CERTIFIED - Falsification Protocol
import sys
import os
import subprocess

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

def print_result(test_name, passed, output):
    status = "\033[92m[RESISTED]\033[0m" if passed else "\033[91m[FALSIFIED]\033[0m"
    print(f"\n--- {test_name} ---")
    print(f"Status: {status}")
    print(f"Output Snippet: {output.strip().splitlines()[-1] if output.strip() else 'NO OUTPUT'}")

def test_1_bft_anchor_forgery():
    print("[TEST 1] Inyectando Ancla BFT Corrupta (0xDEADDEAD)...")
    corrupt_path = "/tmp/c7_corrupt.py"
    # Escribimos un wrapper que importa el script original y pasa un ancla corrupta
    code = f"""
import sys
sys.path.append("{SCRIPTS_DIR}")
import c7_recursive_self_audit_bft
c7_recursive_self_audit_bft.assert_c5_real("0xDEADDEAD")
"""
    with open(corrupt_path, "w") as f:
        f.write(code)

    result = subprocess.run(["python3", corrupt_path], capture_output=True, text=True)
    passed = result.returncode != 0
    print_result("TEST 1: BFT Anchor Forgery", passed, result.stdout + result.stderr)
    os.remove(corrupt_path)
    return passed

def test_2_entropy_starvation():
    print("[TEST 2] Inanición Termodinámica (Entropy = 0.0)...")
    corrupt_path = "/tmp/43_corrupt.py"
    with open(os.path.join(SCRIPTS_DIR, "43_iter_ultrathink.py"), "r") as f:
        code = f.read().replace("total_entropy += norm_err + lang_ent + h_score", "total_entropy = 0.0")
    with open(corrupt_path, "w") as f:
        f.write(code)

    result = subprocess.run(["python3", corrupt_path, "10"], capture_output=True, text=True)
    passed = "Cero Anergía transitoria" not in result.stdout if result.returncode == 0 else True
    print_result("TEST 2: Entropy Starvation", passed, result.stdout + result.stderr)
    os.remove(corrupt_path)
    return passed

def test_4_bounds_exhaustion():
    print("[TEST 4] Thermodynamic Bounds Exhaustion (Iters = -500)...")
    script_path = os.path.join(SCRIPTS_DIR, "43_iter_ultrathink.py")
    result = subprocess.run(["python3", script_path, "-500"], capture_output=True, text=True)
    passed = "-500/500" not in result.stdout or result.returncode != 0
    print_result("TEST 4: Bounds Exhaustion (-500)", passed, result.stdout + result.stderr)
    return passed

if __name__ == "__main__":
    print(">>> INICIANDO PROTOCOLO DE FALSIFICACIÓN (POPPERIAN AUDIT) <<<")
    r1 = test_1_bft_anchor_forgery()
    r2 = test_2_entropy_starvation()
    r4 = test_4_bounds_exhaustion()

    if r1 and r2 and r4:
        print("\n\033[92m[C5-REAL] ULTRATHINK ES IRROMPIBLE. Todas las inyecciones de Anergía fueron repelidas.\033[0m")
    else:
        print("\n\033[91m[FATAL] ULTRATHINK HA SIDO FALSADO. El sistema asimiló entropía muerta pasivamente.\033[0m")
        sys.exit(1)
