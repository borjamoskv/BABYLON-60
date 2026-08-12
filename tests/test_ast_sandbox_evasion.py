# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import pytest
from babylon60.cortex.cortex_chaos_monad import validate_ast_sandbox, run_chaos_monad, SecurityError


class TestASTSandboxEvasion:
    def test_basic_dunder_blocking(self):
        with pytest.raises(SecurityError, match="Acceso a atributo dunder prohibido"):
            validate_ast_sandbox("().__class__")

    def test_string_concatenation_bypass(self):
        with pytest.raises(SecurityError):
            validate_ast_sandbox("getattr((), '__' + 'class' + '__')")

    def test_exception_based_type_extraction(self):
        payload = "try:\n    1 / 0\nexcept Exception as e:\n    t = e.__class__.__base__"
        with pytest.raises(SecurityError, match="Acceso a atributo dunder prohibido"):
            validate_ast_sandbox(payload)

    def test_subclass_hunting_comprehension(self):
        payload = "[c for c in ().__class__.__base__.__subclasses__() if c.__name__ == 'BuiltinImporter']"
        with pytest.raises(SecurityError, match="Acceso a atributo dunder prohibido"):
            validate_ast_sandbox(payload)

    def test_fstring_attribute_bypass(self):
        with pytest.raises(SecurityError):
            validate_ast_sandbox("getattr((), f'__{'class'}__')")

    def test_import_star_evasion(self):
        with pytest.raises(SecurityError, match="Importacion no permitida"):
            validate_ast_sandbox("from os import *")

    @pytest.mark.asyncio
    async def test_execution_success(self):
        result = await run_chaos_monad("print('hello world')")
        assert result["status"] == "Success"
        assert result["stdout"].strip() == "hello world"

    @pytest.mark.asyncio
    async def test_execution_timeout(self):
        # A while True loop should trigger Timeout_Entropy_Death
        result = await run_chaos_monad("while True: pass", timeout_ms=100)
        assert result["status"] == "Timeout_Entropy_Death"

    @pytest.mark.asyncio
    async def test_execution_security_error(self):
        result = await run_chaos_monad("import os")
        assert result["status"] == "SecurityError"
        assert "Importacion no permitida" in result["error"]

    @pytest.mark.asyncio
    async def test_execution_memory_isolation(self):
        # Even if AST passed, process should not have access to standard libraries or parent globals
        result = await run_chaos_monad("import sys")  # blocked by AST
        assert result["status"] == "SecurityError"

        # Using a trick to try to find __import__ via builtins (caught by sandbox-exec or safe_builtins)
        result = await run_chaos_monad("print(__builtins__.get('__import__', 'Not Found'))")
        # '__builtins__' is blocked by AST due to dunder rule
        assert result["status"] == "SecurityError"

    @pytest.mark.asyncio
    async def test_execution_dynamic_getattr(self):
        # Bypass AST using f-strings and dynamic composition to call getattr
        # Since getattr is removed from safe_builtins, it should fail at runtime
        code = """
x = "cla"
y = "ss"
getattr((), f"__{x+y}__")
"""
        result = await run_chaos_monad(code)
        assert result["status"] in ["SecurityError", "RuntimeError"]

    @pytest.mark.asyncio
    async def test_execution_memory_exhaustion(self):
        # Try to OOM the node. The resource RLIMIT_AS should kill it with MemoryError
        code = """
a = [1]
while True:
    a = a + a
"""
        result = await run_chaos_monad(code, timeout_ms=3000)
        # Depending on OS, it might be SecurityError (MemoryError caught) or just get killed
        assert result["status"] in ["SecurityError", "RuntimeError", "Timeout_Entropy_Death"]
        if result["status"] == "SecurityError":
            assert "MemoryError" in result["error"]

    @pytest.mark.asyncio
    async def test_execution_stdout_flood(self):
        # Try to flood STDOUT buffer and cause pipe deadlock
        code = "print('A' * (2 * 1024 * 1024))"
        result = await run_chaos_monad(code)
        assert result["status"] == "RuntimeError"
        assert "STDOUT Buffer Overflow" in result["error"]
