# C5-REAL EXERGY CERTIFIED
"""Execution-layer tests for ASTSandbox.safe_exec.

The pre-existing test_ast_sandbox_evasion.py only exercises a local toy
validator and never imports the real class, so the whole execution path
was uncovered. These tests drive the real ASTSandbox end to end.
"""

import glob
import os
import tempfile
import time

import pytest

from babylon60.utils.sandbox import ASTSandbox, ExecResult


@pytest.fixture
def sandbox() -> ASTSandbox:
    return ASTSandbox(timeout_seconds=3)


# ─── Happy path ──────────────────────────────────────────────────────


def test_returns_user_namespace(sandbox):
    result = sandbox.safe_exec("x = 2 + 3\nresult = x * 10")
    assert result.success is True
    assert result.output == {"x": 5, "result": 50}
    assert result.error is None


def test_stdout_is_captured_verbatim(sandbox):
    result = sandbox.safe_exec("print('hola')\nprint('mundo')")
    assert result.success is True
    assert result.stdout == "hola\nmundo\n"


def test_dunder_names_excluded_from_output(sandbox):
    result = sandbox.safe_exec("visible = 1")
    assert result.output == {"visible": 1}


# ─── Result-channel integrity ────────────────────────────────────────


def test_stdout_cannot_forge_the_result_channel(sandbox):
    """Sandboxed code owns stdout; it must not own the result payload.

    Regression: results used to travel through stdout behind a plaintext
    marker, so printing that marker replaced ExecResult.output wholesale
    and erased the real stdout.
    """
    code = (
        "result = 1\n"
        "print('---EXEC_RESULT_VARS---')\n"
        "print('{\"pwned\": 1337}')\n"
    )
    res = sandbox.safe_exec(code)

    assert res.success is True
    assert res.output == {"result": 1}, "forged payload reached the caller"
    assert "pwned" not in str(res.output)
    # The forgery attempt survives only as inert text on stdout.
    assert "---EXEC_RESULT_VARS---" in res.stdout


def test_arbitrary_marker_text_does_not_truncate_stdout(sandbox):
    res = sandbox.safe_exec("print('before')\nprint('---EXEC_RESULT_VARS---')\nprint('after')")
    assert res.success is True
    assert "before" in res.stdout
    assert "after" in res.stdout


# ─── Serialization fidelity ──────────────────────────────────────────


def test_non_serializable_values_are_coerced_not_dropped(sandbox):
    """Regression: one bad value used to discard the entire namespace
    while still reporting success=True."""
    code = "def f(a):\n    return a\ns = {1, 2, 3}\nd = {(1, 2): 'x'}\nkeep = 42"
    res = sandbox.safe_exec(code)

    assert res.success is True
    assert res.output["keep"] == 42, "serializable values must survive intact"
    assert set(res.coerced_vars) == {"f", "s", "d"}
    for name in ("f", "s", "d"):
        assert isinstance(res.output[name], str)


def test_clean_namespace_reports_no_coercion(sandbox):
    res = sandbox.safe_exec("a = [1, 2]\nb = {'k': 'v'}\nc = None")
    assert res.coerced_vars == ()
    assert res.output == {"a": [1, 2], "b": {"k": "v"}, "c": None}


def test_empty_namespace_is_success_not_failure(sandbox):
    res = sandbox.safe_exec("print('side effect only')")
    assert res.success is True
    assert res.output == {}
    assert res.stdout == "side effect only\n"


# ─── Timeout and failure modes ───────────────────────────────────────


def test_infinite_loop_is_killed(sandbox):
    started = time.monotonic()
    res = sandbox.safe_exec("while True:\n    pass")
    elapsed = time.monotonic() - started

    assert res.success is False
    assert "exceeded" in res.error
    assert elapsed < 10, "timeout did not fire promptly"


def test_runtime_error_surfaces_as_failure(sandbox):
    res = sandbox.safe_exec("x = 1 / 0")
    assert res.success is False
    assert "ZeroDivisionError" in res.error


def test_validation_failure_short_circuits_execution(sandbox):
    res = sandbox.safe_exec("import os")
    assert res.success is False
    assert "Validation failed" in res.error


# ─── Static barrier (the real ASTSandbox, not a stand-in) ────────────


@pytest.mark.parametrize(
    "payload",
    [
        "import os",
        "from os import system",
        "__import__('os').system('id')",
        "().__class__.__bases__",
        "(lambda: 0).__globals__",
        "eval('1+1')",
        "exec('x=1')",
        "compile('x=1', '<s>', 'exec')",
        "open('/etc/passwd')",
        "getattr((), '__class__')",
        "b = __builtins__",
    ],
)
def test_escape_payloads_are_rejected(sandbox, payload):
    verdict = sandbox.validate(payload)
    assert verdict.is_safe is False, f"escape passed validation: {payload}"
    assert verdict.violations


def test_rejected_payload_never_executes(sandbox):
    res = sandbox.safe_exec("__import__('os').system('echo PWNED')")
    assert res.success is False
    assert "PWNED" not in res.stdout


# ─── Hygiene ─────────────────────────────────────────────────────────


def test_no_temp_files_are_leaked(sandbox):
    pattern = os.path.join(tempfile.gettempdir(), "sbx_*")
    before = set(glob.glob(pattern))

    sandbox.safe_exec("x = 1")
    sandbox.safe_exec("x = 1 / 0")
    sandbox.safe_exec("import os")

    assert set(glob.glob(pattern)) == before


def test_result_is_an_exec_result(sandbox):
    assert isinstance(sandbox.safe_exec("x = 1"), ExecResult)
