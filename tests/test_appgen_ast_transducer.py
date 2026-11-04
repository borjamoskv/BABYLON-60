"""
test_appgen_ast_transducer.py — Suite de Verificación para KISH AppGen AST Transducer
===================================================================================
Valida la extracción guiada por AST, la verificación sintáctica en silicio a coste
cero de tokens y la atestación determinista de código generado.
"""

from babylon60.transducers.appgen_ast_transducer import AppGenAstTransducer


def test_validate_syntax_python_valid_and_invalid() -> None:
    """Valida el análisis sintáctico de Python en silicio sin LLM."""
    valid_code = "def add(a: int, b: int) -> int:\n    return a + b\n"
    is_valid, err, line = AppGenAstTransducer.validate_syntax(valid_code, "python")
    assert is_valid is True
    assert err is None

    invalid_code = "def broken(a, b:\n    return a + b\n"
    is_valid, err, line = AppGenAstTransducer.validate_syntax(invalid_code, "python")
    assert is_valid is False
    assert err is not None
    assert line == 1


def test_validate_syntax_typescript_brace_balance() -> None:
    """Valida el balance de delimitadores en TypeScript/JSX."""
    valid_ts = "export function App() {\n  const [val, setVal] = useState(0);\n  return <div>{val}</div>;\n}\n"
    is_valid, err, line = AppGenAstTransducer.validate_syntax(valid_ts, "tsx")
    assert is_valid is True

    # Desbalance: falta llave de cierre
    invalid_ts = "export function App() {\n  const arr = [1, 2, 3;\n  return arr;\n}"
    is_valid, err, line = AppGenAstTransducer.validate_syntax(invalid_ts, "tsx")
    assert is_valid is False
    assert err is not None
    assert "Desbalance" in err or "sin cerrar" in err


def test_zero_token_feedback_loop() -> None:
    """Valida que el bucle de feedback opere a coste cero de tokens emitiendo restricciones."""
    good_code = "x = [i for i in range(10)]\n"
    res_good = AppGenAstTransducer.zero_token_feedback_loop(good_code, "python")
    assert res_good["status"] == "APPROVED"
    assert res_good["zero_token_cost"] is True
    assert res_good["constraint"] is None

    bad_code = "x = [i for i in range(10)\n"
    res_bad = AppGenAstTransducer.zero_token_feedback_loop(bad_code, "python")
    assert res_bad["status"] == "REJECTED"
    assert res_bad["zero_token_cost"] is True
    assert "CORRECT_SYNTAX" in res_bad["constraint"]


def test_extract_code_blocks_ast_with_sha256() -> None:
    """Valida la extracción estructurada de bloques de código y sus huellas SHA-256."""
    raw_markdown = """
Aquí tienes los archivos generados:

```python src/math.py
def multiply(x, y):
    return x * y
```

```tsx src/Button.tsx
export const Button = () => <button>Click</button>;
```
"""
    extracted = AppGenAstTransducer.extract_code_blocks_ast(raw_markdown)
    assert len(extracted) == 2
    assert extracted[0]["path"] == "src/math.py"
    assert extracted[0]["is_valid"] is True
    assert len(extracted[0]["sha256"]) == 64

    assert extracted[1]["path"] == "src/Button.tsx"
    assert extracted[1]["is_valid"] is True


def test_scitt_codebase_digest_deterministic() -> None:
    """Valida que el compound digest de SCITT sea reproducible e invariable al orden de entrada."""
    files = [{"path": "b.py", "sha256": "hash_b"}, {"path": "a.py", "sha256": "hash_a"}]
    digest1 = AppGenAstTransducer.compute_scitt_codebase_digest(files)
    digest2 = AppGenAstTransducer.compute_scitt_codebase_digest(list(reversed(files)))
    assert digest1 == digest2
    assert len(digest1) == 64
