"""Run M0 regression checks with a disposable HOME and blocked TCP/DNS."""

import hashlib
import json
import os
from pathlib import Path
import socket
import sys
import tempfile

HERE = Path(__file__).absolute().parent
ROOT = HERE.parents[4]
SOURCE = ROOT / "01_KISH_ENGINE/babylon60/verifier/standalone_verify.py"
TEST = "tests/test_swarm100_lot12_m0_regressions.py"


def blocked(*args, **kwargs):
    raise AssertionError("network forbidden in confined M0 fixtures")


def main():
    mode = sys.argv[1]
    with tempfile.TemporaryDirectory(prefix="lot12-m0-home-") as home:
        os.environ["HOME"] = home
        os.environ["BABYLON60_SIGNING_SEED"] = "00" * 32
        for name in ("CORTEX_VAULT_KEY", "KIMI_API_KEY", "MOONSHOT_API_KEY", "OPENROUTER_API_KEY"):
            os.environ.pop(name, None)
        import dotenv
        dotenv.load_dotenv = lambda *args, **kwargs: False
        dotenv.dotenv_values = lambda *args, **kwargs: {}
        sys.modules["strike_rs"] = None
        original = socket.socket.connect
        original_ex = socket.socket.connect_ex

        def connect(self, *args, **kwargs):
            if self.family in (socket.AF_INET, socket.AF_INET6):
                return blocked()
            return original(self, *args, **kwargs)

        def connect_ex(self, *args, **kwargs):
            if self.family in (socket.AF_INET, socket.AF_INET6):
                return blocked()
            return original_ex(self, *args, **kwargs)

        socket.socket.connect = connect
        socket.socket.connect_ex = connect_ex
        socket.getaddrinfo = blocked
        import pytest
        args = [TEST] if mode in {"before", "after"} else [
            TEST,
            "tests/test_m0_evidence_pack_acceptance.py",
            "tests/test_standalone_verifier.py",
            "tests/test_compliance_exporter.py",
            "tests/test_swarm100_round2_regressions.py",
        ]
        args += ["-q", "-rs", "-o", "addopts=--tb=short"]
        code = pytest.main(args)
        result = {
            "command": ["uv", "run", "--locked", "--no-sync", "python", str(Path(__file__).relative_to(ROOT)), mode],
            "pytest_args": args,
            "exit_code": int(code),
            "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            "test_sha256": hashlib.sha256((ROOT / TEST).read_bytes()).hexdigest(),
            "scope": "Disposable HOME, synthetic Ed25519 keys and SQLite pack data; TCP/DNS blocked; no operator identities/hardware/services.",
        }
        (HERE / f"{mode}-check.json").write_text(json.dumps(result, indent=2) + "\n")
        return code


if __name__ == "__main__":
    raise SystemExit(main())
