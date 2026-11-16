"""Confined S3 regression/related tests. No network, operator HOME or global lock."""
import os
import socket
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
work = tempfile.TemporaryDirectory(prefix="b60-lot12-s3-related-")
os.environ["HOME"] = work.name
for name in ["BABYLON60_SIGNING_SEED", "CORTEX_VAULT_KEY", "KIMI_API_KEY", "MOONSHOT_API_KEY", "OPENROUTER_API_KEY"]:
    os.environ.pop(name, None)
sys.path.insert(0, str(ROOT / "01_KISH_ENGINE"))
sys.path.insert(0, str(ROOT / "02_EDIN_SWARMS"))
sys.modules["strike_rs"] = None

def blocked(*_args, **_kwargs):
    raise AssertionError("External network forbidden in S3 fixtures")

socket.getaddrinfo = blocked
original_connect = socket.socket.connect

def connect(self, *args, **kwargs):
    if self.family in (socket.AF_INET, socket.AF_INET6):
        return blocked()
    return original_connect(self, *args, **kwargs)

socket.socket.connect = connect
import dotenv
dotenv.load_dotenv = lambda *args, **kwargs: False
dotenv.dotenv_values = lambda *args, **kwargs: {}
tempfile.tempdir = work.name
os.chdir(work.name)
import pytest
raise SystemExit(pytest.main([
    str(ROOT / "tests/test_swarm100_lot12_s3_regressions.py"),
    str(ROOT / "tests/test_master_ledger_queue.py"),
    str(ROOT / "tests/test_swarm_kda_dag_scheduler.py"),
    str(ROOT / "tests/test_itera2_invariants.py") + "::test_master_ledger_queue_zombie_prevention",
    str(ROOT / "tests/test_itera2_invariants.py") + "::test_master_ledger_queue_durabilidad_full",
    "-q", "-o", "addopts=--tb=short",
]))
