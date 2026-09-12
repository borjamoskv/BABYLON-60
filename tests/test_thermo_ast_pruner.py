# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import ast
from pathlib import Path
from babylon60.core.thermo_ast_pruner import AnergiaPurger


def test_anergia_purger_removes_constants() -> None:
    source = """
def example():
    "Docstring that should be pruned"
    x = 10
    return x
"""
    tree = ast.parse(source)
    purger = AnergiaPurger()
    mutated = purger.visit(tree)
    code_out = ast.unparse(mutated)

    assert "Docstring that should be pruned" not in code_out
    assert "x = 10" in code_out


def test_anergia_purger_injects_sigkill(tmp_path: Path) -> None:
    source = """
try:
    x = 1 / 0
except Exception as e:
    logging.error(f'Traza Epistémica Perdida: {e}')
"""
    tree = ast.parse(source)
    purger = AnergiaPurger()
    mutated = purger.visit(tree)
    code_out = ast.unparse(mutated)

    assert "signal.SIGKILL" in code_out
    assert "os.kill" in code_out
    assert "FAIL-FAST: General Exception intercepted." in code_out
