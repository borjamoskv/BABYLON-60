"""Independent confined controls for the five S5 remediations."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import random
import sys

import pytest

from babylon60.core import popperian_filter as popper
from babylon60.kernel.ns_z3_firewall import NavierStokesZ3Firewall
from babylon60.primitives import sandbox

ROOT = Path(__file__).absolute().parents[5]
sys.path.insert(0, str(ROOT / "02_EDIN_SWARMS"))
from agents_archi.clients import openrouter  # noqa: E402


def yt_module():
    file = ROOT / "tools/skill_library/global/youtube-analysis-pipeline/scripts/yt_audit.py"
    spec = importlib.util.spec_from_file_location("independent_yt_audit", file)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("url_kind", ["shell", "leading_option"])
def test_yt_real_fixture_executable_preserves_arguments(tmp_path, monkeypatch, url_kind):
    executable = tmp_path / "bin" / "yt-dlp"
    executable.parent.mkdir()
    log = tmp_path / "arguments.jsonl"
    marker = tmp_path / "escaped"
    executable.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "with open(os.environ['FIXTURE_ARGV_LOG'], 'a') as out:\n"
        "    out.write(json.dumps(sys.argv[1:]) + '\\n')\n"
        "if '--dump-json' in sys.argv:\n"
        "    print(json.dumps({'title': 'fixture', 'duration': 1}))\n"
    )
    executable.chmod(0o700)
    monkeypatch.setenv("PATH", str(executable.parent) + os.pathsep + os.defpath)
    monkeypatch.setenv("FIXTURE_ARGV_LOG", str(log))
    url = f'https://fixture.invalid/a; touch {marker}; $(touch {marker})\n"quoted"'
    if url_kind == "leading_option":
        url = f"--exec=touch {marker}"
    output = tmp_path / f'--output; $(touch {marker}) "folder"'
    metadata, subtitles = yt_module().fetch_youtube_audit(url, str(output))
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    assert len(calls) == 3
    assert all(argv[-2:] == ["--", url] for argv in calls)
    assert calls[1][calls[1].index("-o") + 1] == str(output / "transcript.%(ext)s")
    assert metadata["title"] == "fixture" and subtitles == []
    assert json.loads((output / "metadata.json").read_text())["duration"] == 1
    assert not marker.exists()


def test_filter_checks_real_full_default_limit():
    prefix = "https://fixture.invalid/source "
    repeat = "abcdefghijklmnopqrstuvwxyz0123456789 "
    payload = (prefix + repeat * (popper.MAX_PAYLOAD_BYTES // len(repeat) + 1))[:popper.MAX_PAYLOAD_BYTES]
    assert len(payload.encode()) == popper.MAX_PAYLOAD_BYTES
    accepted = popper.evaluate_payload(payload)
    assert accepted.passed and accepted.truncated is False
    rejected = popper.evaluate_payload(payload + "\nrevolutionary 100x")
    assert not rejected.passed and rejected.reason == "PAYLOAD_TOO_LARGE"
    assert rejected.truncated is False


def test_filter_multibyte_boundary_without_entropy_stub(monkeypatch):
    prefix = "https://fixture.invalid/ "
    payload = prefix + "abcdefghijklmnopqrstuvwxyz0123456789áé " * 8
    size = len(payload.encode())
    monkeypatch.setattr(popper, "MAX_PAYLOAD_BYTES", size)
    assert popper.evaluate_payload(payload).passed
    assert popper.evaluate_payload(payload + "é").reason == "PAYLOAD_TOO_LARGE"
    assert popper.evaluate_payload("\udfff").reason == "INVALID_UTF8"


@pytest.mark.parametrize("code", ["result = 19", "result = 1 / 0", "while True: pass"])
def test_sandbox_actual_child_rejects_unavailable_platform(code):
    if sys.platform.startswith("linux"):
        pytest.skip("This control demonstrates fail-closed behavior on unsupported host")
    result = sandbox.ASTSandbox(timeout_seconds=2).safe_exec(code)
    assert result.success is False
    assert result.output == {} and result.stdout == ""
    assert result.error and result.error.startswith("RESOURCE_LIMIT_UNAVAILABLE")


def test_output_component_enforces_utf8_bytes_without_resource_mock():
    output = sandbox._BoundedText(9)
    assert output.write("éééé") == 4
    assert output.write("\n") == 1
    with pytest.raises(sandbox._OutputLimitError):
        output.write("x")
    assert output.getvalue() == "éééé\n"
    assert len(output.getvalue().encode()) == 9


@pytest.mark.parametrize("target,candidates", [
    ("openrouter/free", ["fixture/full-model"]),
    ("  Fixture/ModeL:FREE  ", ["fixture/full-model"]),
    ("fixture/full-model", ["openrouter/free"]),
])
def test_sensitive_dispatch_veto_covers_both_model_fields(monkeypatch, target, candidates):
    calls = []
    monkeypatch.setenv("OPENROUTER_API_KEY", "synthetic-test-only")
    monkeypatch.setattr(openrouter.urllib.request, "urlopen", lambda *a, **k: calls.append((a, k)))
    client = openrouter.OpenRouterClient(enable_local_failover=False)
    result = client.query("audit", context_paths=["proof/kernel.lean"], model=target, models=candidates)
    assert not result["success"] and "SOVEREIGN_IP_GUARD_TRIPPED" in result["error"]
    assert calls == []
    assert client.quota.work_used == 0


def test_sensitive_dispatch_local_fallback_receives_no_free_model(monkeypatch):
    calls = []
    client = openrouter.OpenRouterClient(api_key="synthetic", enable_local_failover=True)
    monkeypatch.setattr(openrouter.urllib.request, "urlopen", lambda *a, **k: pytest.fail("remote dispatch"))
    monkeypatch.setattr(client, "query_local", lambda **kwargs: calls.append(kwargs) or {"success": True, "fixture": True})
    result = client.query("SharedManifest", model="fixture/model:free", models=["fixture/full-model"])
    assert result["success"] and len(calls) == 1
    assert calls[0]["strict_model_floor"] is True
    assert calls[0]["fallback_reason"] == "sovereign_ip_guard_tripped"
    assert "model" not in calls[0]


def test_valid_paid_model_is_still_dispatched_as_declared(monkeypatch):
    calls = []

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({"model": "fixture/full-model", "choices": [{"message": {"content": "fixture"}}]}).encode()

    def transport(request, **kwargs):
        calls.append(json.loads(request.data))
        return Response()

    monkeypatch.setattr(openrouter.urllib.request, "urlopen", transport)
    client = openrouter.OpenRouterClient(api_key="synthetic", enable_local_failover=False)
    result = client.query("SharedManifest", model="fixture/full-model", models=["fixture/full-model-2"])
    assert result["success"] and result["content"] == "fixture"
    assert calls[0]["model"] == "fixture/full-model"
    assert calls[0]["models"] == ["fixture/full-model-2"]


def gram(rows):
    return [[sum(row[i] * row[j] for row in rows) for j in range(3)] for i in range(3)]


def matrix_status(matrix):
    # lambda=0 and S=-M, so the checked residual is exactly M.
    certificate = NavierStokesZ3Firewall(timeout_ms=5000).verify_strain_sos_bound(
        -matrix[0][0], -matrix[1][1], -matrix[2][2],
        -matrix[0][1], -matrix[0][2], -matrix[1][2], 0,
    )
    return certificate.status


def test_psd_random_gram_witnesses_and_indefinite_negative_witnesses():
    rng = random.Random(20261030)
    for _ in range(40):
        rows = [[rng.randint(-5, 5) for _ in range(3)] for _ in range(rng.randint(1, 3))]
        assert matrix_status(gram(rows)) == "VALID_PROOF"
        p, q, r = rng.randint(1, 7), rng.randint(-7, 7), rng.randint(-7, 7)
        v = [p, q, r]
        residual = gram([[q, -p, 0], [r, 0, -p]])
        indefinite = [[residual[i][j] - v[i] * v[j] for j in range(3)] for i in range(3)]
        # A*v=0, so v^T(M)v = -(v^T*v)^2 <0 is an independent witness.
        witness = sum(v[i] * indefinite[i][j] * v[j] for i in range(3) for j in range(3))
        assert witness < 0
        assert matrix_status(indefinite) == "FALSIFIED_UNSAT"


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf"), True, 1e101])
def test_psd_rejects_invalid_bounded_numeric_domain(value):
    with pytest.raises(ValueError):
        NavierStokesZ3Firewall().verify_strain_sos_bound(0, 0, value, 0, 0, 0, 0)


def test_psd_extreme_exact_scales_and_singular_boundary():
    assert matrix_status([[0, 0, 0], [0, 1e-300, 0], [0, 0, 1e100]]) == "VALID_PROOF"
    assert matrix_status([[0, 0, 0], [0, -1e-300, 0], [0, 0, 1e100]]) == "FALSIFIED_UNSAT"
