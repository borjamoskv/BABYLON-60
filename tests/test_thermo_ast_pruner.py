import ast

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


def test_anergia_purger_injects_sigkill(tmp_path) -> None:  # type: ignore
    source = """
try:
    x = 1 / 0
except (ValueError, TypeError, KeyError, RuntimeError, OSError, AssertionError):
    pass
"""
    tree = ast.parse(source)
    purger = AnergiaPurger()
    mutated = purger.visit(tree)
    code_out = ast.unparse(mutated)

    assert "signal.SIGKILL" in code_out
    assert "os.kill" in code_out
    assert "FAIL-FAST: General Exception intercepted." in code_out
