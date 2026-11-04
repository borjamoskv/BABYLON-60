"""Confined reproductions and regressions for five S5 findings."""

from __future__ import annotations

import importlib.util
from concurrent.futures import ThreadPoolExecutor
from itertools import permutations
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from babylon60.core import popperian_filter as popper
from babylon60.kernel.ns_z3_firewall import NavierStokesZ3Firewall
from babylon60.primitives import sandbox as sandbox_module
from babylon60.primitives.sandbox import ASTSandbox

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "02_EDIN_SWARMS"))
from agents_archi.clients import openrouter  # noqa: E402


def load_yt():
    spec = importlib.util.spec_from_file_location(
        "lot12_yt", ROOT / "tools/skill_library/global/youtube-analysis-pipeline/scripts/yt_audit.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_c0103_url_and_directory_are_literal_arguments(tmp_path, monkeypatch):
    yt = load_yt()
    calls = []

    def record(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return SimpleNamespace(stdout="{}", stderr="", returncode=0)

    monkeypatch.setattr(yt.subprocess, "run", record)
    url = 'https://example.invalid/$(echo fixture);"data'
    target = tmp_path / 'literal $(echo fixture) " folder'
    yt.fetch_youtube_audit(url, str(target))
    assert len(calls) == 3
    assert all(isinstance(argv, list) and not opts.get("shell", False) for argv, opts in calls)
    assert all(argv[-2:] == ["--", url] for argv, _ in calls)


def test_c0103_real_process_does_not_interpret_shell(tmp_path):
    yt = load_yt()
    marker = tmp_path / "must-not-exist"
    argument = f'$(touch {marker}); "quoted"'
    result = yt.run_cmd([sys.executable, "-I", "-c", "import sys; print(sys.argv[1])", argument])
    assert result == argument
    assert not marker.exists()


def test_c0103_rejects_string_commands():
    with pytest.raises(TypeError):
        load_yt().run_cmd("echo must-not-run")


def test_c0221_rejects_unexamined_suffix(monkeypatch):
    monkeypatch.setattr(popper, "MAX_PAYLOAD_BYTES", 160)
    monkeypatch.setattr(popper, "shannon_entropy", lambda text: 4.5)
    prefix = "https://example.invalid/evidence " + "bounded content " * 20
    result = popper.evaluate_payload(prefix + " revolutionary 100x")
    assert not result.passed
    assert result.reason == "PAYLOAD_TOO_LARGE"


def test_c0221_utf8_byte_limit(monkeypatch):
    monkeypatch.setattr(popper, "MAX_PAYLOAD_BYTES", 100)
    monkeypatch.setattr(popper, "shannon_entropy", lambda text: 4.5)
    assert not popper.evaluate_payload("é" * 60).passed


def test_c0221_exact_limit_and_invalid_unicode(monkeypatch):
    monkeypatch.setattr(popper, "MAX_PAYLOAD_BYTES", 80)
    monkeypatch.setattr(popper, "shannon_entropy", lambda text: 4.5)
    assert popper.evaluate_payload("x" * 80).passed
    assert popper.evaluate_payload("x" * 81).reason == "PAYLOAD_TOO_LARGE"
    assert popper.evaluate_payload("\ud800").reason == "INVALID_UTF8"


@pytest.mark.parametrize("mode", ["stdin", "file"])
def test_c0221_cli_does_not_hide_oversized_tail(tmp_path, mode):
    # Exercise the actual main entry with a lowered fixture limit and valid entropy.
    content = "https://example.invalid/ " + "abcdef " * 30
    path = tmp_path / "input.txt"
    path.write_text(content)
    script = ("from babylon60.core import popperian_filter as m; "
              "m.MAX_PAYLOAD_BYTES=120; m.shannon_entropy=lambda x:4.5; m.main()")
    argv = [sys.executable, "-c", script]
    if mode == "file":
        argv.append(str(path))
    result = subprocess.run(argv, input=content, capture_output=True, text=True, timeout=10)
    assert result.returncode == 2
    assert "PAYLOAD_TOO_LARGE" in result.stderr
    assert not result.stdout


def test_c0294_output_growth_is_rejected():
    sandbox = ASTSandbox(timeout_seconds=1)
    sandbox._max_output_bytes = 64
    result = sandbox.safe_exec("print('x' * 256)")
    assert not result.success
    assert len(result.stdout.encode()) <= 64


def test_c0294_unsupported_platform_never_executes(monkeypatch):
    monkeypatch.setattr(sandbox_module.sys, "platform", "unsupported-fixture")
    result = sandbox_module._execute_bounded({"code": "print('must-not-run')"})
    assert result["success"] is False
    assert result["error"].startswith("RESOURCE_LIMIT_UNAVAILABLE")
    assert "stdout" not in result


def fixture_worker(monkeypatch, code, *, output_bytes=64, result_bytes=1024):
    """Exercise output handling; resource API is a fixture, NOT a memory proof."""
    limits = {}
    backend = SimpleNamespace(RLIMIT_AS=9,
                              setrlimit=lambda key, value: limits.update({key: value}),
                              getrlimit=lambda key: limits[key])
    monkeypatch.setattr(sandbox_module.sys, "platform", "linux-fixture")
    monkeypatch.setitem(sys.modules, "resource", backend)
    return sandbox_module._execute_bounded({"code": code, "memory_bytes": 64 * 1024 * 1024,
                                           "output_bytes": output_bytes, "result_bytes": result_bytes})


def test_c0294_bounded_worker_print_effect_with_fixture_resource(monkeypatch):
    result = fixture_worker(monkeypatch, "print('á' * 16); print('x' * 40)")
    assert result["success"] is False
    assert result["error"] == "OUTPUT_LIMIT_EXCEEDED"
    assert result["stdout"] == "á" * 16 + "\n"
    assert len(result["stdout"].encode()) <= 64


def test_c0294_worker_positive_with_fixture_resource(monkeypatch):
    result = fixture_worker(monkeypatch, "result = sum(range(10)); print(result)")
    assert result == {"success": True, "output": {"result": 45}, "stdout": "45\n"}


def test_c0294_result_namespace_limit_with_fixture_resource(monkeypatch):
    result = fixture_worker(monkeypatch, "result = 'x' * 200", result_bytes=64)
    assert result["success"] is False
    assert result["error"] == "RESULT_LIMIT_EXCEEDED"


@pytest.mark.parametrize("field,value", [("max_memory_bytes", 1), ("max_output_bytes", 0),
                                        ("max_result_bytes", 2**30), ("timeout_seconds", True)])
def test_c0294_invalid_limits_rejected(field, value):
    with pytest.raises(ValueError):
        ASTSandbox(**{field: value})


def test_c0294_input_source_size_and_ast_rejected():
    sandbox = ASTSandbox()
    assert sandbox.safe_exec("x" * 65_537).error == "SOURCE_LIMIT_EXCEEDED"
    assert "Validation failed" in sandbox.safe_exec("import os").error


def test_c0294_memory_setup_failure_rejects_before_code(monkeypatch):
    def denied(*args):
        raise ValueError("fixture kernel rejects limit")

    monkeypatch.setattr(sandbox_module.sys, "platform", "linux-fixture")
    monkeypatch.setitem(sys.modules, "resource", SimpleNamespace(RLIMIT_AS=9, setrlimit=denied))
    result = sandbox_module._execute_bounded({"code": "print('must-not-run')", "memory_bytes": 64 * 1024 * 1024})
    assert result == {"success": False, "error": "RESOURCE_LIMIT_UNAVAILABLE"}


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="Real RLIMIT_AS execution requires Linux")
def test_c0294_real_linux_memory_output_and_timeout_bounds():
    sandbox = ASTSandbox(timeout_seconds=1, max_output_bytes=64)
    assert sandbox.safe_exec("result = sum(range(10))").output == {"result": 45}
    memory = sandbox.safe_exec("result = [0] * 10**10")
    assert not memory.success
    assert memory.error in {"MEMORY_LIMIT_EXCEEDED", "WORKER_FAILED_OR_RESOURCE_LIMIT"}
    output = sandbox.safe_exec("print('x' * 256)")
    assert not output.success and len(output.stdout.encode()) <= 64
    timeout = sandbox.safe_exec("while True: pass")
    assert not timeout.success and timeout.error == "EXECUTION_TIMEOUT"


def test_c0294_concurrent_calls_do_not_change_host_stdout():
    stdout_before = sys.stdout
    sandbox = ASTSandbox()
    for _warmup in range(3):
        sandbox.safe_exec("result = 1")
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(sandbox.safe_exec, ["result = 1"] * 12))
    assert sys.stdout is stdout_before
    assert all(r.output == {"result": 1} if r.success else r.error.startswith("RESOURCE_LIMIT_UNAVAILABLE")
               for r in results)


def test_c0486_explicit_free_target_is_checked_before_dispatch(monkeypatch):
    dispatched = []

    class Reply:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self):
            return json.dumps({"model": "fixture/paid", "choices": [{"message": {"content": "ok"}}]}).encode()

    def record(req, **kwargs):
        dispatched.append(req)
        return Reply()

    monkeypatch.setattr(openrouter.urllib.request, "urlopen", record)
    client = openrouter.OpenRouterClient(api_key="synthetic", enable_local_failover=False)
    result = client.query("inspect SharedManifest", model="fixture/secret:free", models=["fixture/paid"])
    assert not result["success"]
    assert not dispatched


@pytest.mark.parametrize("target,candidates", [("fixture/free:free", ["fixture/paid"]),
                                                ("fixture/paid", ["fixture/free:free"]),
                                                ("fixture/free:free", [])])
def test_c0486_every_transmitted_model_is_checked(monkeypatch, target, candidates):
    monkeypatch.setattr(openrouter.urllib.request, "urlopen", lambda *a, **k: pytest.fail("dispatch forbidden"))
    client = openrouter.OpenRouterClient(api_key="synthetic", enable_local_failover=False)
    result = client.query("ordinary sensitive source", context_paths=["proof/check.lean"],
                          model=target, models=candidates)
    assert not result["success"]
    assert "SOVEREIGN_IP_GUARD_TRIPPED" in result["error"]


def test_c0486_sensitive_paid_target_and_candidates_preserved(monkeypatch):
    dispatched = []

    class Reply:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self):
            return json.dumps({"model": "fixture/paid-target", "choices": [{"message": {"content": "fixture"}}]}).encode()

    def record(req, **kwargs):
        dispatched.append(json.loads(req.data))
        return Reply()

    monkeypatch.setattr(openrouter.urllib.request, "urlopen", record)
    client = openrouter.OpenRouterClient(api_key="synthetic", enable_local_failover=False)
    result = client.query("inspect SharedManifest", model="fixture/paid-target", models=["fixture/paid-fallback"])
    assert result["success"]
    assert dispatched[0]["model"] == "fixture/paid-target"
    assert dispatched[0]["models"] == ["fixture/paid-fallback"]


def test_c0486_blocked_target_uses_strict_local_failover(monkeypatch):
    routes = []
    monkeypatch.setattr(openrouter.urllib.request, "urlopen", lambda *a, **k: pytest.fail("remote dispatch forbidden"))
    client = openrouter.OpenRouterClient(api_key="synthetic", enable_local_failover=True)

    def local(**kwargs):
        routes.append(kwargs)
        return {"success": True, "fixture": "local"}

    monkeypatch.setattr(client, "query_local", local)
    result = client.query("inspect SharedManifest", model="fixture/free:free", models=["fixture/paid"])
    assert result["fixture"] == "local"
    assert len(routes) == 1 and routes[0]["strict_model_floor"] is True


@pytest.mark.parametrize("diagonal", [(0.0, 1.0, 1.0), (0.0, 1.0, -1.0)])
def test_c0113_rejects_zero_leading_minor_indefinite_matrix(diagonal):
    fw = NavierStokesZ3Firewall(timeout_ms=5000)
    result = fw.verify_strain_sos_bound(*diagonal, 0.0, 0.0, 0.0, lambda_max=0.0)
    assert result.status == "FALSIFIED_UNSAT"


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -float("inf")])
def test_c0113_nonfinite_inputs_are_rejected(bad):
    fw = NavierStokesZ3Firewall(timeout_ms=5000)
    with pytest.raises(ValueError):
        fw.verify_strain_sos_bound(bad, 0.0, 0.0, 0.0, 0.0, 0.0, lambda_max=0.0)


@pytest.mark.parametrize("diagonal", [(0.0, 0.0, 0.0), (-1.0, 0.0, -1.0), (-1e-40, -1e-40, 0.0)])
def test_c0113_singular_psd_is_accepted(diagonal):
    fw = NavierStokesZ3Firewall(timeout_ms=5000)
    result = fw.verify_strain_sos_bound(*diagonal, 0.0, 0.0, 0.0, lambda_max=0.0)
    assert result.status == "VALID_PROOF"


def test_c0113_negative_nonleading_minor_is_rejected():
    # All diagonals nonnegative; yz principal minor is negative with x row zero.
    fw = NavierStokesZ3Firewall(timeout_ms=5000)
    result = fw.verify_strain_sos_bound(0.0, -1.0, -1.0, 0.0, 0.0, 2.0, lambda_max=0.0)
    assert result.status == "FALSIFIED_UNSAT"


def test_c0113_exact_small_negative_and_range_rejected():
    fw = NavierStokesZ3Firewall(timeout_ms=5000)
    assert fw.verify_strain_sos_bound(0.0, 1e-40, 0.0, 0.0, 0.0, 0.0, lambda_max=0.0).status == "FALSIFIED_UNSAT"
    with pytest.raises(ValueError):
        fw.verify_strain_sos_bound(1e101, 0.0, 0.0, 0.0, 0.0, 0.0, lambda_max=0.0)


def test_c0113_permuted_counterexamples_after_warmup():
    fw = NavierStokesZ3Firewall(timeout_ms=5000)
    for _ in range(3):
        assert fw.verify_strain_sos_bound(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, lambda_max=0.0).status == "VALID_PROOF"
    for _ in range(10):
        for diagonal in permutations((0.0, 1.0, -1.0)):
            assert fw.verify_strain_sos_bound(*diagonal, 0.0, 0.0, 0.0, lambda_max=0.0).status == "FALSIFIED_UNSAT"
