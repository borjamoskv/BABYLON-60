"""First-use installer checks run in disposable source bundles with fake tools."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(os.environ.get("BABYLON_TEST_SOURCE", str(Path(__file__).absolute().parents[1])))
REQUIRED = (
    "pyproject.toml",
    "uv.lock",
    "01_KISH_ENGINE/babylon60/cli/main_dispatcher.py",
    "01_KISH_ENGINE/babylon60/mcp/cortex_mcp_server.py",
    "01_KISH_ENGINE/babylon60/presentation.md",
)


@pytest.fixture
def installer(tmp_path):
    root = tmp_path / "source bundle Ω with spaces"
    root.mkdir()
    for filename in ("install.sh", "install.ps1"):
        shutil.copyfile(ROOT / filename, root / filename)
    for filename in REQUIRED:
        target = root / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("fixture", encoding="utf-8")
    tools = tmp_path / "stub tools"
    tools.mkdir()
    state = tmp_path / "state"
    state.mkdir()
    env = os.environ.copy()
    env.update(
        PATH=str(tools) + os.pathsep + env.get("PATH", ""),
        HOME=str(tmp_path / "home"),
        CODEX_HOME=str(tmp_path / "codex home"),
        BABYLON_HOME=str(tmp_path / "babylon home"),
        STUB_LOG=str(state / "calls.jsonl"),
        STUB_SETUP_STATE=str(state / "setup.json"),
    )
    cli = """import json, os, sys
from pathlib import Path
with open(os.environ['STUB_LOG'], 'a', encoding='utf-8') as stream:
    stream.write(json.dumps(['cli', *sys.argv[1:]]) + '\\n')
if sys.argv[1:] == ['--help']:
    print('Babylon CLI help')
elif sys.argv[1:] == ['setup', '--client', 'codex']:
    status = int(os.environ.get('STUB_SETUP_EXIT', '0'))
    if status:
        print('Codex executable not found; install Codex and rerun setup.', file=sys.stderr)
        raise SystemExit(status)
    Path(os.environ['STUB_SETUP_STATE']).write_text('activated', encoding='utf-8')
    print('Codex configured; application not evaluated.')
else:
    raise SystemExit(2)
"""
    server = """import json
print(json.dumps({'jsonrpc': '2.0', 'id': 1, 'result': {'serverInfo': {'name': 'isolated-test-server'}}}))
"""
    uv_source = f"""#!{sys.executable}
import json, os, sys
from pathlib import Path
with open(os.environ['STUB_LOG'], 'a', encoding='utf-8') as stream:
    stream.write(json.dumps(['uv', *sys.argv[1:]]) + '\\n')
status = int(os.environ.get('STUB_UV_EXIT', '0'))
if status:
    raise SystemExit(status)
print('uv install notice')
if not os.environ.get('STUB_MISSING_EXECUTABLES'):
    binaries = Path.cwd() / '.venv' / 'bin'
    binaries.mkdir(parents=True, exist_ok=True)
    for name, content in [('babylon60', {cli!r}), ('babylon60-mcp', {server!r})]:
        target = binaries / name
        target.write_text('#!' + sys.executable + '\\n' + content, encoding='utf-8')
        target.chmod(0o755)
"""
    stub = tools / "uv"
    stub.write_text(uv_source, encoding="utf-8")
    stub.chmod(0o755)
    return root, tmp_path, env


def run_installer(fixture, *args):
    root, outside, env = fixture
    return subprocess.run(
        ["bash", str(root / "install.sh"), *args],
        cwd=outside,
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )


def calls(env):
    log = Path(env["STUB_LOG"])
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []


@pytest.mark.skipif(sys.platform == "win32", reason="requires Bash; PowerShell archive integration runs on Windows")
def test_client_installs_then_activates_from_unicode_bundle_outside_checkout(installer):
    root, _, env = installer
    result = run_installer(installer, "--client", "codex")
    assert result.returncode == 0, result.stderr
    assert calls(env) == [
        ["uv", "sync", "--locked", "--no-dev", "--no-editable"],
        ["cli", "setup", "--client", "codex"],
    ]
    assert Path(env["STUB_SETUP_STATE"]).read_text(encoding="utf-8") == "activated"
    assert "CLI installed:" in result.stdout and str(root) in result.stdout
    assert "new Codex conversation" in result.stdout
    assert "not yet evaluated" in result.stdout
    assert "Babylon CLI help" not in result.stdout


@pytest.mark.skipif(sys.platform == "win32", reason="requires Bash")
def test_repeated_client_install_repeats_only_the_requested_install_and_setup(installer):
    for _ in range(2):
        result = run_installer(installer, "--client", "codex")
        assert result.returncode == 0, result.stderr
    assert calls(installer[2]) == 2 * [
        ["uv", "sync", "--locked", "--no-dev", "--no-editable"],
        ["cli", "setup", "--client", "codex"],
    ]


@pytest.mark.skipif(sys.platform == "win32", reason="requires Bash")
def test_dry_run_describes_install_and_setup_without_installed_package(installer):
    root, _, env = installer
    result = run_installer(installer, "--client", "codex", "--dry-run")
    assert result.returncode == 0, result.stderr
    assert "Install: uv sync --locked --no-dev --no-editable" in result.stdout
    assert "setup --client codex --dry-run" in result.stdout
    assert "not executed" in result.stdout
    assert "BABYLON_TERMINAL_VERIFIED" in result.stdout
    assert not (root / ".venv").exists()
    assert not Path(env["CODEX_HOME"]).exists()
    assert not Path(env["STUB_SETUP_STATE"]).exists()
    assert calls(env) == []


@pytest.mark.skipif(sys.platform == "win32", reason="requires Bash")
@pytest.mark.parametrize("args", [("--client",), ("--client", "other"), ("--unknown",)])
def test_invalid_options_do_not_install(installer, args):
    result = run_installer(installer, *args)
    assert result.returncode == 2
    assert result.stderr.strip()
    assert calls(installer[2]) == []


@pytest.mark.skipif(sys.platform == "win32", reason="requires Bash")
@pytest.mark.parametrize("dry_run", [(), ("--dry-run",)])
def test_client_and_stdio_mode_are_rejected_before_install(installer, dry_run):
    result = run_installer(installer, "--mcp", "--client", "codex", *dry_run)
    assert result.returncode == 2
    assert "cannot be combined" in result.stderr
    assert result.stdout == ""
    assert calls(installer[2]) == []


@pytest.mark.skipif(sys.platform == "win32", reason="requires Bash")
def test_default_install_reports_activation_command_and_preserves_globals(installer):
    _, _, env = installer
    result = run_installer(installer)
    assert result.returncode == 0, result.stderr
    assert calls(env) == [["uv", "sync", "--locked", "--no-dev", "--no-editable"], ["cli", "--help"]]
    assert "CLI installed:" in result.stdout
    assert "Codex integration: not activated." in result.stdout
    assert "Next step:" in result.stdout and "setup --client codex" in result.stdout
    assert not Path(env["CODEX_HOME"]).exists()
    assert not Path(env["STUB_SETUP_STATE"]).exists()


@pytest.mark.skipif(sys.platform == "win32", reason="requires Bash")
def test_setup_failure_propagates_without_reporting_activation_success(installer):
    _, _, env = installer
    env["STUB_SETUP_EXIT"] = "7"
    result = run_installer(installer, "--client", "codex")
    assert result.returncode == 7
    assert "Codex executable not found" in result.stderr
    assert "CLI installed:" not in result.stdout
    assert "new Codex conversation" not in result.stdout
    assert not Path(env["STUB_SETUP_STATE"]).exists()


@pytest.mark.skipif(sys.platform == "win32", reason="requires Bash")
def test_install_failure_does_not_attempt_setup(installer):
    _, _, env = installer
    env["STUB_UV_EXIT"] = "9"
    result = run_installer(installer, "--client", "codex")
    assert result.returncode == 9
    assert calls(env) == [["uv", "sync", "--locked", "--no-dev", "--no-editable"]]


@pytest.mark.skipif(sys.platform == "win32", reason="requires Bash")
def test_missing_executables_does_not_attempt_setup(installer):
    _, _, env = installer
    env["STUB_MISSING_EXECUTABLES"] = "1"
    result = run_installer(installer, "--client", "codex")
    assert result.returncode == 1
    assert "did not create" in result.stderr
    assert calls(env) == [["uv", "sync", "--locked", "--no-dev", "--no-editable"]]


@pytest.mark.skipif(sys.platform == "win32", reason="requires Bash")
def test_stdio_output_contains_only_server_jsonrpc(installer):
    result = run_installer(installer, "--mcp")
    assert result.returncode == 0, result.stderr
    messages = [json.loads(line) for line in result.stdout.splitlines()]
    assert messages == [{"jsonrpc": "2.0", "id": 1, "result": {"serverInfo": {"name": "isolated-test-server"}}}]
    assert "uv install notice" in result.stderr


@pytest.mark.skipif(sys.platform == "win32", reason="requires Bash")
def test_dirty_checkout_rejected_before_dependency_changes(installer):
    root, _, env = installer
    subprocess.run(["git", "init", str(root)], check=True, capture_output=True)
    result = run_installer(installer, "--client", "codex")
    assert result.returncode == 1
    assert "clean checkout" in result.stderr
    assert not (root / ".venv").exists()
    assert calls(env) == []


def test_powershell_client_dry_run_and_failure_contract_is_distributed():
    """Static coverage complements native Windows runtime archive CI."""
    script = (ROOT / "install.ps1").read_text(encoding="utf-8")
    assert '[ValidateSet("codex")]' in script
    assert "if ($Mcp -and $Client)" in script
    assert "setup --client codex --dry-run" in script
    assert "& $cli setup --client $Client" in script
    assert "if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }" in script
    assert "ForEach-Object { [Console]::Error.WriteLine($_) }" in script


@pytest.mark.skipif(
    shutil.which("pwsh") is None and shutil.which("powershell") is None,
    reason="PowerShell is unavailable; native Windows CI exercises the source archive",
)
@pytest.mark.parametrize(
    ("args", "success", "message"),
    [
        (["-DryRun", "-Client", "codex"], True, "setup --client codex --dry-run"),
        (["-DryRun", "-Mcp", "-Client", "codex"], False, "cannot be combined"),
        (["-Client", "other"], False, "codex"),
    ],
)
def test_powershell_argument_and_dry_run_paths_without_installation(installer, args, success, message):
    root, outside, env = installer
    executable = shutil.which("pwsh") or shutil.which("powershell")
    assert executable is not None
    result = subprocess.run(
        [executable, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(root / "install.ps1"), *args],
        cwd=outside,
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert (result.returncode == 0) == success, result.stderr
    assert message in result.stdout + result.stderr
    assert not (root / ".venv").exists()
    assert not Path(env["CODEX_HOME"]).exists()
    assert calls(env) == []
