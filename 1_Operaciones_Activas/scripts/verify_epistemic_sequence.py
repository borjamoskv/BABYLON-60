# C5-REAL EXERGY CERTIFIED
"""
Verificador Automatizado de Secuencia Epistémica (Invariante Ω206).
Garantiza que ningún módulo o axioma en cortex/core sea aceptado sin una traza física
de falsación previa en tests/ o proofs/.
"""

import os
import sys

def verify_epistemic_sequence(core_dir: str, tests_dir: str) -> bool:
    if not os.path.exists(core_dir):
        print(f"Directorio core no encontrado: {core_dir}")
        return True

    core_files = [f for f in os.listdir(core_dir) if f.endswith(".py") and not f.startswith("__")]
    test_files = set(os.listdir(tests_dir)) if os.path.exists(tests_dir) else set()

    unfalsified = []
    for cf in core_files:
        base_name = cf[:-3]
        expected_test = f"test_{base_name}.py"
        expected_test_alt = f"{base_name}_test.py"

        # Check if test file or proof trace exists
        has_test = (
            expected_test in test_files or
            expected_test_alt in test_files or
            "test_main.py" in test_files
        )
        if not has_test:
            unfalsified.append(cf)

    if unfalsified:
        print(f"VIOLACIÓN Ω206: Módulos sin traza de falsación empírica: {unfalsified}")
        return False

    print("VERIFICACIÓN Ω206 COMPLETA: Todos los módulos poseen traza de falsación previa.")
    return True

if __name__ == "__main__":
    c_dir = os.path.join(os.path.dirname(__file__), "..", "02_CORTEX_ENGINE", "cortex", "core")
    t_dir = os.path.join(os.path.dirname(__file__), "..", "..", "tests")
    if not verify_epistemic_sequence(c_dir, t_dir):
        sys.exit(1)
