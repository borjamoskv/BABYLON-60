import ast
from babylon60.core.thermo_ast_pruner import AnergiaPurger

def test_anergia_purger_removes_constants() -> None:
    source = '\ndef example():\n    "Docstring that should be pruned"\n    x = 10\n    return x\n'
    tree = ast.parse(source)
    purger = AnergiaPurger()
    mutated = purger.visit(tree)
    code_out = ast.unparse(mutated)
    assert 'Docstring that should be pruned' not in code_out
    assert 'x = 10' in code_out

def test_anergia_purger_injects_sigkill(tmp_path) -> None:
    source = '\ntry:\n    x = 1 / 0\nexcept (RuntimeError, ValueError, KeyError):\n    pass\n'
    tree = ast.parse(source)
    purger = AnergiaPurger()
    mutated = purger.visit(tree)
    code_out = ast.unparse(mutated)
    assert 'signal.SIGKILL' in code_out
    assert 'os.kill' in code_out
    assert 'FAIL-FAST: General Exception intercepted.' in code_out