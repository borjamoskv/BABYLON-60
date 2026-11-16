"""Reproduce confined S2 identity verification without operator keys or services."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[5]
EVIDENCE = Path(__file__).resolve().parent
SOURCES = [
    "01_KISH_ENGINE/babylon60/crypto/identity.py",
    "01_KISH_ENGINE/babylon60/crypto/keys.py",
    "scripts/c5_l1_ledger/seal_bounty_aeon.py",
]
TEST = "tests/test_swarm100_lot12_s2_identity_regressions.py"
CONFINED = r'''
import os, socket, sys, tempfile
temporary = tempfile.TemporaryDirectory(prefix="lot12-s2-identity-")
os.environ["HOME"] = temporary.name
os.environ["CORTEX_DB_PATH"] = temporary.name + "/state"
os.environ["CORTEX_TESTING"] = "1"
os.environ["BABYLON60_SIGNING_SEED"] = "00" * 32
for key in ["CORTEX_VAULT_KEY", "BABYLON_AEON_TRUSTED_PUBLIC_KEY_B64", "KIMI_API_KEY", "MOONSHOT_API_KEY", "OPENROUTER_API_KEY"]:
    os.environ.pop(key, None)
import dotenv
dotenv.load_dotenv = lambda *a, **k: False
dotenv.dotenv_values = lambda *a, **k: {}
connect_original = socket.socket.connect
connect_ex_original = socket.socket.connect_ex
def blocked(*a, **k):
    raise AssertionError("network forbidden in identity fixtures")
def connect(self, *a, **k):
    if self.family in (socket.AF_INET, socket.AF_INET6): return blocked()
    return connect_original(self, *a, **k)
def connect_ex(self, *a, **k):
    if self.family in (socket.AF_INET, socket.AF_INET6): return blocked()
    return connect_ex_original(self, *a, **k)
socket.socket.connect = connect
socket.socket.connect_ex = connect_ex
socket.getaddrinfo = blocked
import pytest
raise SystemExit(pytest.main(sys.argv[1:]))
'''


def main() -> int:
    commands = {
        "related-tests": [
            "uv", "run", "--locked", "--no-sync", "python", "-c", CONFINED, TEST,
            "tests/test_crypto_canonical.py",
            "tests/test_bounty_aeon_sealer.py::test_conformal_merkle_tree_inclusion_and_falsification",
            "-q", "-o", "addopts=--tb=short",
        ],
        "ruff": ["uv", "run", "--locked", "--no-sync", "ruff", "check", *SOURCES, TEST],
        "mypy": [
            "uv", "run", "--locked", "--no-sync", "mypy", "--follow-imports=silent",
            "--check-untyped-defs", *SOURCES,
        ],
        "diff-check": ["git", "diff", "--check", "--", *SOURCES, TEST],
    }
    results = {}
    for name, command in commands.items():
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=180)
        output = result.stdout + result.stderr
        (EVIDENCE / f"{name}.log").write_text(output)
        results[name] = {
            "command": command, "exit_code": result.returncode,
            "log_sha256": hashlib.sha256(output.encode()).hexdigest(),
        }
        print(name, result.returncode, output[-1000:])
    (EVIDENCE / "checks.json").write_text(json.dumps(results, indent=2) + "\n")
    return int(any(result["exit_code"] for result in results.values()))


if __name__ == "__main__":
    raise SystemExit(main())
