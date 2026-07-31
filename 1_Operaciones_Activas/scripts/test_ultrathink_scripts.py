# C5-REAL EXERGY CERTIFIED
import pytest
import subprocess
import os

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

def test_script_43_iter_ultrathink():
    # Test that 43_iter_ultrathink can run without crashing and outputs C5-REAL
    script_path = os.path.join(SCRIPTS_DIR, "43_iter_ultrathink.py")
    result = subprocess.run(["python3", script_path, "10"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Hiper-Colapso MCTS finalizado" in result.stdout
    assert "Cero Anergía transitoria" in result.stdout

def test_script_58_thermodynamic_wallpaper():
    script_path = os.path.join(SCRIPTS_DIR, "58_thermodynamic_wallpaper_ultrathink.py")
    result = subprocess.run(["python3", script_path], capture_output=True, text=True)
    assert result.returncode == 0
    assert "[C5-REAL] Thermodynamic Entropy Extracted" in result.stdout

def test_script_c7_audit():
    script_path = os.path.join(SCRIPTS_DIR, "c7_recursive_self_audit_bft.py")
    result = subprocess.run(["python3", script_path], capture_output=True, text=True)
    assert result.returncode == 0
    assert "0xDEADBEEF" in result.stdout

def test_script_59_deep_research_engine():
    script_path = os.path.join(SCRIPTS_DIR, "59_autodidact_omega_deep_research_engine.py")
    result = subprocess.run(["python3", script_path], capture_output=True, text=True)
    assert result.returncode == 0
    assert "AUTODIDACT-Ω V4.0 DEEP RESEARCH" in result.stdout
    assert "ZERO ANERGY" in result.stdout

