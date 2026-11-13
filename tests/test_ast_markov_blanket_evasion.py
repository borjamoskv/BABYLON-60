# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import pytest
import sys
from babylon60.cortex import cortex_chaos_monad as chaos
from babylon60.cortex.cortex_chaos_monad import validate_ast_markov_blanket, run_chaos_monad, SecurityError


class TestASTMarkovBlanketEvasion:
    def test_basic_dunder_blocking(self) -> None:
        with pytest.raises(SecurityError, match="Acceso a atributo dunder prohibido"):
            validate_ast_markov_blanket("().__class__")

    def test_string_concatenation_bypass(self) -> None:
        with pytest.raises(SecurityError):
            validate_ast_markov_blanket("getattr((), '__' + 'class' + '__')")

    def test_exception_based_type_extraction(self) -> None:
        payload = "try:\n    1 / 0\nexcept Exception as e:\n    t = e.__class__.__base__"
        with pytest.raises(SecurityError, match="Acceso a atributo dunder prohibido"):
            validate_ast_markov_blanket(payload)

    def test_subclass_hunting_comprehension(self) -> None:
        payload = "[c for c in ().__class__.__base__.__subclasses__() if c.__name__ == 'BuiltinImporter']"
        with pytest.raises(SecurityError, match="Acceso a atributo dunder prohibido"):
            validate_ast_markov_blanket(payload)

    def test_fstring_attribute_bypass(self) -> None:
        with pytest.raises(SecurityError):
            validate_ast_markov_blanket("getattr((), f'__{'class'}__')")

    def test_import_star_evasion(self) -> None:
        with pytest.raises(SecurityError, match="Importacion no permitida"):
            validate_ast_markov_blanket("from os import *")

    @pytest.mark.asyncio
    async def test_execution_success(self) -> None:
        result = await run_chaos_monad("print('hello world')")
        if sys.platform != "darwin":
            assert result["status"] == "SecurityError"
            assert "confinement" in result["error"]
            return
        assert result["status"] == "Success"
        assert result["stdout"].strip() == "hello world"

    @pytest.mark.asyncio
    async def test_execution_timeout(self) -> None:
        # A while True loop should trigger Timeout_Entropy_Death
        result = await run_chaos_monad("while True: pass", timeout_ms=100)
        if sys.platform != "darwin":
            assert result["status"] == "SecurityError"
            assert "confinement" in result["error"]
            return
        assert result["status"] == "Timeout_Entropy_Death"

    @pytest.mark.asyncio
    async def test_execution_security_error(self) -> None:
        result = await run_chaos_monad("import os")
        assert result["status"] == "SecurityError"
        assert "Importacion no permitida" in result["error"]

    @pytest.mark.asyncio
    async def test_execution_memory_isolation(self) -> None:
        # Even if AST passed, process should not have access to standard libraries or parent globals
        result = await run_chaos_monad("import sys")  # blocked by AST
        assert result["status"] == "SecurityError"

        # Using a trick to try to find __import__ via builtins (caught by sandbox-exec or safe_builtins)
        result = await run_chaos_monad("print(__builtins__.get('__import__', 'Not Found'))")
        # '__builtins__' is blocked by AST due to dunder rule
        assert result["status"] == "SecurityError"

    @pytest.mark.asyncio
    async def test_execution_dynamic_getattr(self) -> None:
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
    async def test_execution_memory_exhaustion(self, monkeypatch: pytest.MonkeyPatch, record_property) -> None:
        # Finite retained payload: 320 MiB, even if the supervisor regresses.
        # Fill real pages and retain them long enough for the parent's RSS sample.
        code = """
chunks = []
for i in range(80):
    chunks.append(b'X' * (4 * 1024 * 1024))
while True: pass
"""
        samples: list[int] = []
        resident_bytes = chaos._resident_bytes

        def observed_rss(pid: int) -> int:
            observed = resident_bytes(pid)
            samples.append(observed)
            return observed

        monkeypatch.setattr(chaos, "_resident_bytes", observed_rss)
        result = await run_chaos_monad(code, timeout_ms=3000)
        if sys.platform != "darwin":
            assert result["status"] == "SecurityError"
            assert "confinement" in result["error"]
            return
        assert result["status"] == "SecurityError"
        assert result["error"] == "MemoryError: Execution resident memory exceeds 256 MiB cutoff"
        assert result["stdout"] == "" and result["scitt_receipt"] == {}
        assert samples and max(samples) > chaos._MAX_RESIDENT_BYTES
        assert max(samples) < 500 * 1024 * 1024
        record_property("retained_payload_limit_bytes", 320 * 1024 * 1024)
        record_property("sampled_peak_rss_bytes", max(samples))

    @pytest.mark.asyncio
    async def test_execution_stdout_flood(self) -> None:
        # Try to flood STDOUT buffer and cause pipe deadlock
        code = "print('A' * (2 * 1024 * 1024))"
        result = await run_chaos_monad(code)
        if sys.platform != "darwin":
            assert result["status"] == "SecurityError"
            assert "confinement" in result["error"]
            return
        assert result["status"] == "RuntimeError"
        assert "STDOUT Buffer Overflow" in result["error"]
