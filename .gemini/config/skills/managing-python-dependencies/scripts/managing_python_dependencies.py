#!/usr/bin/env python3
"""
C5-REAL: Python Dependency Manager Detector & Executor.
Scans project root for dependency manager signals and executes
the appropriate install/setup command deterministically.

Author: borjamoskv
Version: v3.0.0

Usage:
  python managing_python_dependencies.py [project_root]           # Detect only
  python managing_python_dependencies.py [project_root] --install pkg  # Install package
  python managing_python_dependencies.py [project_root] --setup   # Run full setup
  python managing_python_dependencies.py [project_root] --check   # Verify coherence
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:
        tomllib = None  # type: ignore[assignment]


# Detection hierarchy (priority order)
MANAGERS: list[dict[str, str | list[str] | None]] = [
    {
        "name": "uv",
        "signals": ["uv.lock"],
        "toml_key": "tool.uv",
        "install": "uv add",
        "setup": "uv sync",
        "lock": "uv.lock",
        "check": "uv pip check",
    },
    {
        "name": "poetry",
        "signals": [],
        "toml_key": "tool.poetry",
        "install": "poetry add",
        "setup": "poetry install",
        "lock": "poetry.lock",
        "check": "poetry check",
    },
    {
        "name": "pdm",
        "signals": ["pdm.lock"],
        "toml_key": "tool.pdm",
        "install": "pdm add",
        "setup": "pdm install",
        "lock": "pdm.lock",
        "check": "pdm run pip check",
    },
    {
        "name": "pipenv",
        "signals": ["Pipfile"],
        "toml_key": None,
        "install": "pipenv install",
        "setup": "pipenv install",
        "lock": "Pipfile.lock",
        "check": "pipenv check",
    },
    {
        "name": "conda",
        "signals": ["environment.yml"],
        "toml_key": None,
        "install": "conda install",
        "setup": "conda env create -f environment.yml",
        "lock": "conda-lock.yml",
        "check": None,
    },
    {
        "name": "pip",
        "signals": ["pyproject.toml"],
        "toml_key": None,
        "install": ".venv/bin/pip install",
        "setup": '.venv/bin/pip install -e ".[all]"',
        "lock": "requirements.txt",
        "check": ".venv/bin/pip check",
    },
    {
        "name": "pip-requirements",
        "signals": ["requirements.txt"],
        "toml_key": None,
        "install": ".venv/bin/pip install",
        "setup": ".venv/bin/pip install -r requirements.txt",
        "lock": "requirements.txt",
        "check": ".venv/bin/pip check",
    },
]


def _parse_toml(path: Path) -> dict:
    """Parse pyproject.toml using tomllib (3.11+) or tomli fallback."""
    if tomllib is None:
        return {}
    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except Exception:
        return {}


def _has_toml_key(data: dict, dotted_key: str) -> bool:
    """Check nested dict for a dotted key like 'tool.uv'."""
    keys = dotted_key.split(".")
    current = data
    for k in keys:
        if not isinstance(current, dict) or k not in current:
            return False
        current = current[k]
    return True


def _get_requires_python(data: dict) -> str | None:
    """Extract requires-python from parsed pyproject.toml."""
    project = data.get("project", {})
    return project.get("requires-python")


def check_python_version(project_root: Path) -> bool:
    """Verify active interpreter satisfies requires-python constraint."""
    pyproject = project_root / "pyproject.toml"
    if not pyproject.exists():
        return True

    data = _parse_toml(pyproject)
    requires = _get_requires_python(data)
    if not requires:
        return True

    # Parse simple constraints: >=3.10, >=3.10,<4
    import re
    version = f"{sys.version_info.major}.{sys.version_info.minor}"
    version_tuple = (sys.version_info.major, sys.version_info.minor)

    # Extract minimum version from >=X.Y pattern
    match = re.search(r">=\s*(\d+)\.(\d+)", requires)
    if match:
        min_ver = (int(match.group(1)), int(match.group(2)))
        if version_tuple < min_ver:
            print(
                f"[P0 ABORT] Python {version} does not satisfy "
                f"requires-python: {requires}"
            )
            return False

    # Extract maximum version from <X.Y pattern
    match = re.search(r"<\s*(\d+)\.(\d+)", requires)
    if match:
        max_ver = (int(match.group(1)), int(match.group(2)))
        if version_tuple >= max_ver:
            print(
                f"[P0 ABORT] Python {version} exceeds upper bound in "
                f"requires-python: {requires}"
            )
            return False

    print(f"[C5-REAL] Python {version} satisfies requires-python: {requires}")
    return True


def detect_manager(project_root: Path) -> dict | None:
    """Detect the dependency manager by scanning for signal files."""
    pyproject = project_root / "pyproject.toml"
    toml_data: dict = {}
    if pyproject.exists():
        toml_data = _parse_toml(pyproject)

    for manager in MANAGERS:
        # Check pyproject.toml keys via proper TOML parsing
        toml_key = manager.get("toml_key")
        if toml_key and toml_data and _has_toml_key(toml_data, toml_key):
            return manager
        # Check signal files
        signals = manager.get("signals", [])
        if isinstance(signals, list):
            for signal_file in signals:
                if (project_root / signal_file).exists():
                    return manager

    return None


def ensure_venv(project_root: Path) -> Path:
    """Create .venv if it does not exist (fallback protocol). Returns venv path."""
    venv_path = project_root / ".venv"
    if not venv_path.exists():
        print(f"[C5-REAL] Creating isolated venv at {venv_path}")
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True,
        )
    return venv_path


def verify_installation(project_root: Path, manager: dict) -> bool:
    """Run the appropriate check command for the detected manager."""
    check_cmd = manager.get("check")
    if not check_cmd or not isinstance(check_cmd, str):
        print(f"[WARN] No verification command for {manager['name']}")
        return True

    manager_name = manager["name"]

    # For pip-based managers, verify .venv exists first
    if manager_name in ("pip", "pip-requirements"):
        pip_path = project_root / ".venv" / "bin" / "pip"
        if not pip_path.exists():
            print("  Venv status : MISSING (run: python3 -m venv .venv)")
            return False

    result = subprocess.run(
        check_cmd.split(),
        capture_output=True,
        text=True,
        cwd=str(project_root),
    )
    if result.returncode != 0:
        print(f"[P0 ABORT] {check_cmd} failed:")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return False

    print(f"[C5-REAL] {check_cmd}: No broken dependencies.")
    return True


def execute_install(project_root: Path, manager: dict, package: str) -> bool:
    """Execute the install command for the given package."""
    install_cmd = manager.get("install")
    if not install_cmd or not isinstance(install_cmd, str):
        print(f"[ERROR] No install command for {manager['name']}")
        return False

    # For pip-based, ensure venv exists
    if manager["name"] in ("pip", "pip-requirements"):
        ensure_venv(project_root)

    cmd = f"{install_cmd} {package}"
    print(f"[C5-REAL] Executing: {cmd}")
    result = subprocess.run(
        cmd.split(),
        cwd=str(project_root),
    )
    return result.returncode == 0


def execute_setup(project_root: Path, manager: dict) -> bool:
    """Execute the setup command for the project."""
    setup_cmd = manager.get("setup")
    if not setup_cmd or not isinstance(setup_cmd, str):
        print(f"[ERROR] No setup command for {manager['name']}")
        return False

    # For pip-based, ensure venv exists
    if manager["name"] in ("pip", "pip-requirements"):
        ensure_venv(project_root)

    print(f"[C5-REAL] Executing: {setup_cmd}")
    result = subprocess.run(
        setup_cmd.split(),
        cwd=str(project_root),
    )
    return result.returncode == 0


def main() -> int:
    """Detect manager and report or execute commands. Returns exit code."""
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]

    project_root = Path(args[0]).resolve() if args else Path.cwd()

    print(f"[C5-REAL] Scanning: {project_root}")

    # Python version gate
    if not check_python_version(project_root):
        return 1

    manager = detect_manager(project_root)

    if manager is None:
        print("[WARN] No dependency manager detected. Activating Fallback Protocol.")
        if "--install" in flags:
            idx = flags.index("--install")
            # Package name follows --install in original argv
            pkg_candidates = [
                a for a in sys.argv[sys.argv.index("--install") + 1:]
                if not a.startswith("--")
            ]
            if pkg_candidates:
                venv = ensure_venv(project_root)
                pip_path = venv / "bin" / "pip"
                cmd = [str(pip_path), "install", pkg_candidates[0]]
                print(f"[C5-REAL] Executing: {' '.join(cmd)}")
                result = subprocess.run(cmd, cwd=str(project_root))
                if result.returncode != 0:
                    return 1
                # Freeze
                subprocess.run(
                    [str(pip_path), "freeze"],
                    stdout=open(project_root / "requirements.txt", "w"),
                    cwd=str(project_root),
                )
                return 0
        print("  -> python3 -m venv .venv")
        print("  -> .venv/bin/pip install <package>")
        print("  -> .venv/bin/pip freeze > requirements.txt")
        return 0

    print(f"[C5-REAL] Detected manager: {manager['name']}")
    print(f"  Install cmd : {manager['install']} <pkg>")
    print(f"  Setup cmd   : {manager['setup']}")
    print(f"  Lock file   : {manager['lock']}")

    # Check lock file existence
    lock_file = manager.get("lock", "")
    if isinstance(lock_file, str) and lock_file:
        lock_path = project_root / lock_file
        if lock_path.exists():
            print(f"  Lock status : EXISTS ({lock_path.stat().st_size} bytes)")
        else:
            print("  Lock status : MISSING (run setup command to generate)")

    # Handle --install
    if "--install" in flags:
        pkg_candidates = [
            a for a in sys.argv[sys.argv.index("--install") + 1:]
            if not a.startswith("--")
        ]
        if pkg_candidates:
            if not execute_install(project_root, manager, pkg_candidates[0]):
                return 1
            return 0
        print("[ERROR] --install requires a package name")
        return 1

    # Handle --setup
    if "--setup" in flags:
        if not execute_setup(project_root, manager):
            return 1
        return 0

    # Handle --check or default verification
    if "--check" in flags:
        if not verify_installation(project_root, manager):
            return 1
        return 0

    # Default: report only + verify
    if not verify_installation(project_root, manager):
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
