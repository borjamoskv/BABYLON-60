import ast
import pytest


class SecurityError(Exception):
    pass


def validate_ast_sandbox(source_code: str) -> bool:
    try:
        tree = ast.parse(source_code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                if isinstance(node.attr, str) and node.attr.startswith("__") and node.attr.endswith("__"):
                    raise SecurityError(f"Acceso a atributo dunder prohibido: {node.attr}")
            if isinstance(node, ast.Name) and node.id in (
                "getattr",
                "setattr",
                "eval",
                "exec",
                "compile",
                "__import__",
            ):
                raise SecurityError(f"Llamada a función de introspección prohibida: {node.id}")
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                raise SecurityError("Importación no permitida en entorno sandboxed")
        return True
    except SecurityError:
        raise
    except SyntaxError as e:
        raise SecurityError(f"Syntax error (safe): {e}")


class TestASTSandboxEvasion:
    def test_basic_dunder_blocking(self) -> None:
        with pytest.raises(SecurityError, match="Acceso a atributo dunder prohibido"):
            validate_ast_sandbox("().__class__")

    def test_string_concatenation_bypass(self) -> None:
        with pytest.raises(SecurityError):
            validate_ast_sandbox("getattr((), '__' + 'class' + '__')")

    def test_exception_based_type_extraction(self) -> None:
        payload = "try:\n    1 / 0\nexcept Exception as e:\n    t = e.__class__.__base__"
        with pytest.raises(SecurityError, match="Acceso a atributo dunder prohibido"):
            validate_ast_sandbox(payload)

    def test_subclass_hunting_comprehension(self) -> None:
        payload = "[c for c in ().__class__.__base__.__subclasses__() if c.__name__ == 'BuiltinImporter']"
        with pytest.raises(SecurityError, match="Acceso a atributo dunder prohibido"):
            validate_ast_sandbox(payload)

    def test_fstring_attribute_bypass(self) -> None:
        with pytest.raises(SecurityError):
            validate_ast_sandbox("getattr((), f'__{'class'}__')")

    def test_import_star_evasion(self) -> None:
        with pytest.raises(SecurityError, match="Importación no permitida"):
            validate_ast_sandbox("from os import *")

    def test_lambda_and_exec_bypass(self) -> None:
        with pytest.raises(SecurityError):
            validate_ast_sandbox("(lambda: __import__('os').system('id'))()")
