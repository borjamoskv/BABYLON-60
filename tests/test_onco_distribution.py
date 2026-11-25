"""The distributed CLI must not advertise excluded oncology experiments."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest

from scripts.guards.verify_windows_migrations import MigrationEvidence


ROOT = Path(__file__).absolute().parents[1]


@pytest.fixture
def migration_evidence(request, tmp_path):
    case = request.node.callspec.params["previous_install"]
    directory = Path(os.environ.get("BABYLON_MIGRATION_EVIDENCE", str(tmp_path / "evidence")))
    return MigrationEvidence(directory / f"{case}.json", case, request.node.nodeid)


def _installed_oncology_state(python, cwd, env, evidence, phase):
    code = (
        "import importlib.util,importlib.metadata,json; "
        "d=importlib.metadata.distribution('babylon60'); "
        "print(json.dumps({'modules':{n:importlib.util.find_spec(n) is not None for n in "
        "['babylon60.oncology_primitives','babylon60.genomics','babylon60.cli.onco_transducer']},"
        "'entry_points':[e.name for e in d.entry_points if e.name=='babylon60-onco'],"
        "'editable':json.loads(d.read_text('direct_url.json') or '{}').get('dir_info',{}).get('editable',False),"
        "'version':d.version}))"
    )
    probe = evidence.run(
        phase, [str(python), "-I", "-c", code], cwd=cwd, env=env, capture_output=True, encoding="utf-8", timeout=15
    )
    assert probe.returncode == 0, probe.stderr
    return json.loads(probe.stdout)


@pytest.mark.parametrize("command", [None, "onco", "boolean-sim"])
def test_cli_has_no_oncology_commands(command):
    env = dict(os.environ, PYTHONPATH=str(ROOT / "01_KISH_ENGINE"))
    args = ["--help"] if command is None else [command]
    result = subprocess.run(
        [sys.executable, "-m", "babylon60.cli.main_dispatcher", *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        encoding="utf-8",
        timeout=15,
    )
    if command is None:
        assert result.returncode == 0, result.stderr
        assert "onco" not in result.stdout
        assert "boolean-sim" not in result.stdout
    else:
        assert result.returncode == 2, result.stderr
        assert "invalid choice" in result.stderr
        assert "Traceback" not in result.stderr


def test_release_zip_excludes_oncology_experiments(tmp_path):
    result = subprocess.run(
        ["bash", str(ROOT / "scripts/package_release.sh"), str(tmp_path)],
        cwd=ROOT,
        capture_output=True,
        encoding="utf-8",
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    with zipfile.ZipFile(result.stdout.strip()) as bundle:
        names = bundle.namelist()
    assert "01_KISH_ENGINE/babylon60/oncology_primitives.py" not in names
    assert "01_KISH_ENGINE/babylon60/cli/onco_transducer.py" not in names
    assert not any(name.startswith("01_KISH_ENGINE/babylon60/genomics/") for name in names)
    assert not any(name.startswith(("experiments/oncology/", "examples/remotion/")) for name in names)
    assert "01_KISH_ENGINE/babylon60/cli/main_dispatcher.py" in names


def test_wheel_excludes_oncology_experiments_and_cli(tmp_path):
    result = subprocess.run(
        ["uv", "build", "--wheel", "--out-dir", str(tmp_path / "wheel")],
        cwd=ROOT,
        capture_output=True,
        encoding="utf-8",
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    wheels = list((tmp_path / "wheel").glob("*.whl"))
    assert len(wheels) == 1
    extracted = tmp_path / "installed"
    with zipfile.ZipFile(wheels[0]) as wheel:
        names = wheel.namelist()
        assert "babylon60/oncology_primitives.py" not in names
        assert "babylon60/cli/onco_transducer.py" not in names
        assert not any(name.startswith("babylon60/genomics/") for name in names)
        assert not any(
            name.startswith(("babylon60_oncology/", "experiments/oncology/", "examples/remotion/")) for name in names
        )
        metadata_name = next(name for name in names if name.endswith(".dist-info/METADATA"))
        assert "Provides-Extra: onco\n" not in wheel.read(metadata_name).decode()
        entry_points = next(name for name in names if name.endswith(".dist-info/entry_points.txt"))
        assert "babylon60-onco" not in wheel.read(entry_points).decode()
        wheel.extractall(extracted)

    # -I ignores checkout paths and PYTHONPATH; imports come from the wheel.
    code = (
        "import runpy, sys; sys.path.insert(0, sys.argv.pop(1)); "
        "runpy.run_module('babylon60.cli.main_dispatcher', run_name='__main__')"
    )
    for args in (["--help"], ["onco"], ["boolean-sim"]):
        run = subprocess.run(
            [sys.executable, "-I", "-c", code, str(extracted), *args],
            cwd=tmp_path,
            capture_output=True,
            encoding="utf-8",
            timeout=15,
        )
        assert run.returncode == (0 if args == ["--help"] else 2), run.stderr
        assert "Traceback" not in run.stderr
        if args == ["--help"]:
            assert "onco" not in run.stdout
            assert "boolean-sim" not in run.stdout
        else:
            assert "invalid choice" in run.stderr


def test_core_sdist_excludes_independent_domains(tmp_path):
    result = subprocess.run(
        ["uv", "build", "--sdist", "--out-dir", str(tmp_path)],
        cwd=ROOT,
        capture_output=True,
        encoding="utf-8",
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    archives = list(tmp_path.glob("*.tar.gz"))
    assert len(archives) == 1
    with tarfile.open(archives[0]) as archive:
        names = archive.getnames()
    assert any(name.endswith("/01_KISH_ENGINE/babylon60/cli/main_dispatcher.py") for name in names)
    assert not any("/experiments/oncology/" in name or "/examples/remotion/" in name for name in names)


def _seed_legacy_oncology(checkout):
    """Retired module names are fixtures for uninstall migration, not a model."""
    modules = {
        "oncology_primitives.py": "LEGACY_MIGRATION_FIXTURE = True\n",
        "genomics/__init__.py": "LEGACY_MIGRATION_FIXTURE = True\n",
        "cli/onco_transducer.py": ("def main():\n    print('legacy oncology migration fixture')\n"),
    }
    for name, source in modules.items():
        path = checkout / "01_KISH_ENGINE/babylon60" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")


@pytest.mark.skipif(
    os.environ.get("BABYLON_TEST_INSTALL_BUNDLE") != "1",
    reason="release integration: installs locked dependencies into a disposable environment",
)
@pytest.mark.parametrize("previous_install", ["none", "editable", "wheel", "source-wheel"])
def test_source_installer_respects_wheel_exclusions(tmp_path, previous_install, migration_evidence):
    evidence = migration_evidence
    checkout = tmp_path / "source checkout"
    checkout.mkdir()
    for name in (
        "install.sh",
        "install.ps1",
        "pyproject.toml",
        "uv.lock",
        "README.md",
        "LICENSE",
        "docs/skills.json",
        "docs/skills-lock.json",
    ):
        destination = checkout / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, destination)
    for name in ("01_KISH_ENGINE/babylon60", "02_EDIN_SWARMS/agents_archi", ".agents/skills"):
        shutil.copytree(ROOT / name, checkout / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    # Current source contains no retired experimental modules in the core.
    assert not (checkout / "01_KISH_ENGINE/babylon60/oncology_primitives.py").exists()
    assert not (checkout / "01_KISH_ENGINE/babylon60/cli/onco_transducer.py").exists()
    assert not (checkout / "01_KISH_ENGINE/babylon60/genomics").exists()
    lock_before = (checkout / "uv.lock").read_bytes()
    env = os.environ.copy()
    for name in ("PYTHONPATH", "VIRTUAL_ENV", "UV_PROJECT_ENVIRONMENT", "UV_PROJECT", "UV_NO_EDITABLE"):
        env.pop(name, None)
    env["UV_PYTHON"] = sys.executable
    if sys.platform == "win32":
        powershell = shutil.which("pwsh") or shutil.which("powershell")
        assert powershell is not None, "PowerShell is required for native Windows migrations"
        installer_command = [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(checkout / "install.ps1"),
        ]
        scripts = checkout / ".venv/Scripts"
        suffix = ".exe"
    else:
        installer_command = ["bash", str(checkout / "install.sh")]
        scripts = checkout / ".venv/bin"
        suffix = ""
    python = scripts / f"python{suffix}"
    cli = scripts / f"babylon60{suffix}"
    old_command = scripts / f"babylon60-onco{suffix}"
    evidence.observe("installer_sha256", hashlib.sha256(Path(installer_command[-1]).read_bytes()).hexdigest())
    previous_version = None
    if previous_install != "none":
        _seed_legacy_oncology(checkout)
        project = checkout / "pyproject.toml"
        current_project = project.read_text(encoding="utf-8")
        # Restore legacy packaging; dependencies and version stay fixed.
        legacy_project = current_project.replace(
            "[project.scripts]\n",
            '[project.scripts]\nbabylon60-onco = "babylon60.cli.onco_transducer:main"\n',
            1,
        )
        assert legacy_project != current_project
        if previous_install in ("wheel", "source-wheel"):
            for path in (
                "01_KISH_ENGINE/babylon60/oncology_primitives.py",
                "01_KISH_ENGINE/babylon60/genomics",
                "01_KISH_ENGINE/babylon60/cli/onco_transducer.py",
            ):
                exclusion = f'  "{path}",\n'
                assert exclusion in legacy_project
                legacy_project = legacy_project.replace(exclusion, "", 1)
        project.write_text(legacy_project, encoding="utf-8")
        if previous_install == "wheel":
            build = evidence.run(
                "legacy-build",
                ["uv", "build", "--wheel", "--out-dir", str(tmp_path / "legacy-wheel")],
                cwd=checkout,
                env=env,
                capture_output=True,
                encoding="utf-8",
                timeout=60,
            )
            assert build.returncode == 0, build.stderr
            wheels = list((tmp_path / "legacy-wheel").glob("*.whl"))
            assert len(wheels) == 1
            dependencies = evidence.run(
                "legacy-dependencies",
                ["uv", "sync", "--locked", "--no-dev", "--no-install-project"],
                cwd=checkout,
                env=env,
                capture_output=True,
                encoding="utf-8",
                timeout=60,
            )
            assert dependencies.returncode == 0, dependencies.stderr
            legacy_command = ["uv", "pip", "install", "--python", str(python), "--no-deps", str(wheels[0])]
        else:
            legacy_command = ["uv", "sync", "--locked", "--no-dev"]
            if previous_install == "source-wheel":
                legacy_command.append("--no-editable")
        legacy = evidence.run(
            "legacy-install",
            legacy_command,
            cwd=checkout,
            env=env,
            capture_output=True,
            encoding="utf-8",
            timeout=60,
        )
        assert legacy.returncode == 0, legacy.stderr
        state = _installed_oncology_state(python, tmp_path, env, evidence, "probe-before")
        evidence.observe("before", {**state, "old_command_exists": old_command.is_file()})
        assert state["editable"] is (previous_install == "editable")
        assert all(state["modules"].values())
        assert state["entry_points"] == ["babylon60-onco"]
        assert old_command.is_file() and os.access(old_command, os.X_OK)
        previous_version = state["version"]
        project.write_text(current_project, encoding="utf-8")
    for number in range(1, 3 if previous_install != "none" else 2):
        install = evidence.run(
            f"install-{number}",
            installer_command,
            cwd=tmp_path,
            env=env,
            capture_output=True,
            encoding="utf-8",
            timeout=60,
        )
        assert install.returncode == 0, install.stderr
        assert (checkout / "uv.lock").read_bytes() == lock_before
        state = _installed_oncology_state(python, tmp_path, env, evidence, f"probe-after-{number}")
        evidence.observe(
            f"after-{number}",
            {
                **state,
                "old_command_exists": os.path.lexists(old_command),
                "lock_unchanged": (checkout / "uv.lock").read_bytes() == lock_before,
            },
        )
        assert state["modules"] == {
            "babylon60.oncology_primitives": False,
            "babylon60.genomics": False,
            "babylon60.cli.onco_transducer": False,
        }
        assert state["editable"] is False
        assert state["entry_points"] == []
        assert not old_command.exists()
        if previous_version is not None:
            assert state["version"] == previous_version
    for args in (["--help"], ["onco"], ["boolean-sim"]):
        run = evidence.run(
            "cli-" + ("help" if args == ["--help"] else args[0]),
            [str(cli), *args],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            encoding="utf-8",
            timeout=15,
        )
        assert run.returncode == (0 if args == ["--help"] else 2), run.stderr
        assert "Traceback" not in run.stderr
        if args == ["--help"]:
            assert "onco" not in run.stdout
            assert "boolean-sim" not in run.stdout
        else:
            assert "invalid choice" in run.stderr
    evidence.finish()
