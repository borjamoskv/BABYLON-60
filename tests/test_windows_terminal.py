"""Exercise the shipped archive on native Windows without importing its checkout."""

import asyncio
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

import pytest
from babylon60 import __version__

pytestmark = pytest.mark.skipif(
    sys.platform != "win32" or "BABYLON_WINDOWS_ARTIFACT" not in os.environ,
    reason="requires the source archive supplied by native Windows CI",
)


def environment(state: Path) -> dict[str, str]:
    env = os.environ.copy()
    for name in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV", "UV_PROJECT_ENVIRONMENT", "BABYLON60_SIGNING_SEED"):
        env.pop(name, None)
    env["BABYLON_HOME"] = str(state)
    env["BABYLON_CAUSAL_GATE_DB"] = str(state / "gate.db")
    env["UV_PYTHON"] = sys.executable
    # Redirected Windows streams can use legacy code pages; the product must emit UTF-8.
    env["PYTHONUTF8"] = "0"
    env["PYTHONIOENCODING"] = "cp1252"
    return env


def powershell() -> str:
    executable = shutil.which("pwsh") or shutil.which("powershell")
    assert executable is not None, "PowerShell is required for native installation"
    return executable


def install_command(root: Path, *args: str) -> list[str]:
    return [powershell(), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(root / "install.ps1"), *args]


@pytest.fixture(scope="module")
def release(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    artifact = Path(os.environ["BABYLON_WINDOWS_ARTIFACT"])
    metadata = json.loads((artifact / "source.json").read_text(encoding="utf-8"))
    assert metadata["bundle"] == f"Babylon60-v{__version__}-terminal-mcp.zip"
    checkout = Path(__file__).absolute().parents[1]
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=checkout, text=True).strip()
    assert metadata["commit"] == commit
    bundle = artifact / metadata["bundle"]
    assert hashlib.sha256(bundle.read_bytes()).hexdigest() == metadata["sha256"]
    outside = tmp_path_factory.mktemp("windows terminal outside")
    root = outside / "Babylon 60 Ω"
    with zipfile.ZipFile(bundle) as archive:
        assert "install.ps1" in archive.namelist()
        archive.extractall(root)
    assert not (root / ".git").exists()
    return root, outside


def test_powershell_dry_run_from_another_directory(release: tuple[Path, Path]) -> None:
    root, outside = release
    result = subprocess.run(
        install_command(root, "-DryRun"),
        cwd=outside,
        env=environment(outside / "state"),
        capture_output=True,
        encoding="utf-8",
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "BABYLON_TERMINAL_VERIFIED" in result.stdout
    assert str(root) in result.stdout
    assert "Scripts" in result.stdout and "babylon60-mcp.exe" in result.stdout


def test_powershell_rejects_dirty_checkout(release: tuple[Path, Path], tmp_path: Path) -> None:
    root, _ = release
    dirty = tmp_path / "dirty checkout"
    shutil.copytree(root, dirty, ignore=shutil.ignore_patterns(".venv"))
    subprocess.run(["git", "init", str(dirty)], check=True, capture_output=True)
    result = subprocess.run(
        install_command(dirty),
        cwd=tmp_path,
        env=environment(tmp_path / "state"),
        capture_output=True,
        encoding="utf-8",
        timeout=30,
    )
    assert result.returncode != 0
    assert "clean checkout" in result.stderr
    assert not (dirty / ".venv").exists()


def test_archive_installs_and_runs_cli_and_mcp(release: tuple[Path, Path]) -> None:
    root, outside = release
    env = environment(outside / "state")
    result = subprocess.run(
        install_command(root), cwd=outside, env=env, capture_output=True, encoding="utf-8", timeout=240
    )
    assert result.returncode == 0, result.stderr
    assert "CLI installed:" in result.stdout
    scripts = root / ".venv" / "Scripts"
    python = scripts / "python.exe"
    for args in (["--help"], ["--version"], ["presentation"]):
        cli = subprocess.run(
            [str(scripts / "babylon60.exe"), *args],
            cwd=outside,
            env=env,
            capture_output=True,
            encoding="utf-8",
            timeout=20,
        )
        assert cli.returncode == 0, cli.stderr
        assert cli.stdout.strip()
        if args == ["--version"]:
            assert cli.stdout.strip().split()[-1] == __version__
    isolation = subprocess.run(
        [
            str(python),
            "-I",
            "-c",
            "import babylon60, importlib.metadata, importlib.util, json; print(json.dumps(babylon60.__file__)); "
            "assert importlib.metadata.version('babylon60') == babylon60.__version__; "
            "assert importlib.util.find_spec('pytest') is None; "
            "assert importlib.util.find_spec('mcp') is None",
        ],
        cwd=outside,
        env=env,
        capture_output=True,
        encoding="utf-8",
        timeout=20,
    )
    assert isolation.returncode == 0, isolation.stderr
    assert str(root).casefold() in str(json.loads(isolation.stdout)).casefold()
    asyncio.run(asyncio.wait_for(check_mcp(scripts / "babylon60-mcp.exe", outside, env), timeout=40))


async def check_mcp(executable: Path, outside: Path, env: dict[str, str]) -> None:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.types import ReadResourceResult, TextResourceContents

    server = StdioServerParameters(
        command=str(executable),
        args=["--ledger", str(outside / "state" / "ledger.db")],
        cwd=str(outside),
        env=env,
    )
    async with stdio_client(server) as (reader, writer):
        async with ClientSession(reader, writer, read_timeout_seconds=15) as session:
            initialized = await session.initialize()
            assert initialized.protocol_version == "2024-11-05"
            assert initialized.server_info.name == "cortex-persist-bft"
            assert initialized.server_info.version == __version__
            assert "bft_query_ledger" in {tool.name for tool in (await session.list_tools()).tools}
            assert "babylon://presentation/guide" in {
                str(resource.uri) for resource in (await session.list_resources()).resources
            }
            guide = await session.read_resource("babylon://presentation/guide")
            assert isinstance(guide, ReadResourceResult)
            assert isinstance(guide.contents[0], TextResourceContents)
            assert "MOSKV-1" in guide.contents[0].text
            await session.send_ping()
