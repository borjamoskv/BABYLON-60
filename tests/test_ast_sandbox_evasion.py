"""
Unit Tests for AST Sandbox Evasion Guard — MOSKV-1 APEX
Verifies prevention of introspection, dunder exploitation, subclass hunting, f-string traps, and unauthorized imports.
"""

import pytest

from babylon60.guards.ast_sandbox import SecurityError, validate_ast_sandbox


class TestASTSandboxEvasion:

    def test_basic_dunder_blocking(self) -> None:
        with pytest.raises(SecurityError, match="Acceso a atributo dunder prohibido"):
            validate_ast_sandbox("().__class__")

    def test_string_concatenation_bypass(self) -> None:
        with pytest.raises(SecurityError):
            validate_ast_sandbox("getattr((), '__' + 'class' + '__')")

    def test_exception_based_type_extraction(self) -> None:
        payload = (
            "try:\n"
            "    1 / 0\n"
            "except (ValueError, TypeError, KeyError, RuntimeError, OSError, AssertionError) as e:\n"
            "    t = e.__class__.__base__"
        )
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

    def test_prohibited_function_globals(self) -> None:
        with pytest.raises(SecurityError, match="Llamada a función de introspección prohibida: globals"):
            validate_ast_sandbox("x = globals()")

    def test_prohibited_function_eval(self) -> None:
        with pytest.raises(SecurityError, match="Llamada a función de introspección prohibida: eval"):
            validate_ast_sandbox("eval('1 + 1')")

    def test_fstring_dunder_traversal(self) -> None:
        with pytest.raises(SecurityError, match="Acceso a atributo dunder"):
            validate_ast_sandbox("f'{x.__class__}'")

    def test_safe_arithmetic_passes(self) -> None:
        assert validate_ast_sandbox("a = 10 + 20\nb = a * 2") is True