#!/usr/bin/env python3
"""
Terminal installer and retained local gateway compatibility tests.
Desktop/wizard distribution was retired; source bundle tests live in test_terminal_distribution.py.
"""

import os
import sys
import json
import time
import socket
import urllib.request
import subprocess
from pathlib import Path

REPO_ROOT = Path(os.environ.get("BABYLON_TEST_SOURCE", str(Path(__file__).absolute().parent.parent)))


def wait_for_port(port: int, timeout: float = 10.0) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return True
        except OSError:
            time.sleep(0.08)
    return False


def test_dry_run_install_sh() -> None:
    """Verifica el script universal install.sh con flag --dry-run."""
    install_sh = REPO_ROOT / "install.sh"
    assert install_sh.exists(), "install.sh debe existir"

    res = subprocess.run(["bash", str(install_sh), "--dry-run"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "BABYLON_TERMINAL_VERIFIED" in res.stdout


def test_babylon_launcher_check_only() -> None:
    """Verifica que el launcher responda telemetria JSON en --check-only."""
    launcher_py = REPO_ROOT / "scripts" / "babylon_launcher.py"
    assert launcher_py.exists(), "babylon_launcher.py debe existir"

    res = subprocess.run([sys.executable, str(launcher_py), "--check-only"], capture_output=True, text=True)
    assert res.returncode == 0

    data = json.loads(res.stdout)
    assert data["status"] == "ONLINE"
    assert data["cache_line_bytes"] == 64
    assert data["version"] == "60.4-SOVEREIGN"
    assert "architecture" in data
    assert "hardware_threads" in data


def test_babylon_launcher_test_port() -> None:
    """Verifica la deteccion no bloqueante de puerto."""
    launcher_py = REPO_ROOT / "scripts" / "babylon_launcher.py"
    res = subprocess.run([sys.executable, str(launcher_py), "--test-port"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "PORT_AVAILABLE:" in res.stdout


def test_babylon_launcher_http_serving() -> None:
    """Prueba de integracion: Levanta el launcher en puerto efimero y comprueba / y /api/status."""
    launcher_py = REPO_ROOT / "scripts" / "babylon_launcher.py"
    test_port = 6098

    proc = subprocess.Popen([sys.executable, str(launcher_py), "--port", str(test_port), "--no-browser"])
    try:
        assert wait_for_port(test_port), f"Puerto {test_port} no respondió a tiempo"

        # Test GET /api/status
        with urllib.request.urlopen(f"http://127.0.0.1:{test_port}/api/status", timeout=3) as response:
            assert response.status == 200
            payload = json.loads(response.read().decode("utf-8"))
            assert payload["status"] == "ONLINE"
            assert payload["exergy_target"] == 21000

    finally:
        proc.terminate()
        proc.wait(timeout=3)


def test_package_release_script(tmp_path: Path) -> None:
    """Verifica que scripts/package_release.sh construya un archivo ZIP valido en dist/."""
    script_path = REPO_ROOT / "scripts" / "package_release.sh"
    assert script_path.exists()

    res = subprocess.run(["bash", str(script_path), str(tmp_path)], capture_output=True, text=True)
    assert res.returncode == 0
    assert "terminal-mcp.zip" in res.stdout

    dist_dir = tmp_path
    zips = list(dist_dir.glob("*.zip"))
    assert len(zips) >= 1
    assert zips[0].stat().st_size > 50_000


def test_install_sh_https_clone() -> None:
    """Verifica que install.sh use HTTPS y no SSH para permitir clonado público anónimo."""
    install_sh = (REPO_ROOT / "install.sh").read_text(encoding="utf-8")
    assert "https://github.com/borjamoskv/BABYLON-60.git" in install_sh
    assert "git@github.com:borjamoskv/BABYLON-60.git" not in install_sh


def test_agents_detection_api() -> None:
    """Verifica que /api/agents/detect descubra agentes instalados con estructura canónica."""
    launcher_py = REPO_ROOT / "scripts" / "babylon_launcher.py"
    test_port = 6101

    proc = subprocess.Popen([sys.executable, str(launcher_py), "--port", str(test_port), "--no-browser"])
    try:
        assert wait_for_port(test_port), f"Puerto {test_port} no respondió a tiempo"
        with urllib.request.urlopen(f"http://127.0.0.1:{test_port}/api/agents/detect", timeout=3) as response:
            assert response.status == 200
            data = json.loads(response.read().decode("utf-8"))
            assert "claude" in data
            assert "antigravity" in data
            assert "terminal" in data
            assert data["terminal"]["detected"] is True
            assert "description" in data["claude"]
    finally:
        proc.terminate()
        proc.wait(timeout=3)


def test_touchid_trigger_api() -> None:
    """Verifica el endpoint /api/touchid/trigger en modo mock/simulado."""
    launcher_py = REPO_ROOT / "scripts" / "babylon_launcher.py"
    test_port = 6102

    proc = subprocess.Popen([sys.executable, str(launcher_py), "--port", str(test_port), "--no-browser"])
    try:
        assert wait_for_port(test_port), f"Puerto {test_port} no respondió a tiempo"
        post_data = json.dumps({"mock": True}).encode("utf-8")
        req = urllib.request.Request(
            f"http://127.0.0.1:{test_port}/api/touchid/trigger",
            data=post_data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=3) as response:
            assert response.status == 200
            res = json.loads(response.read().decode("utf-8"))
            assert res["success"] is True
            assert res["status"] == "SIMULATED"
            assert res["verified_in_hardware"] is False
            assert "operator_user" in res
            assert "causal_hash" in res
    finally:
        proc.terminate()
        proc.wait(timeout=3)
