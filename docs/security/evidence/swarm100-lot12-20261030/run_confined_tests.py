"""Run targeted regressions with synthetic HOME/keys and TCP/DNS blocked."""
from __future__ import annotations

import os
import socket
import sys
import tempfile
from pathlib import Path


def main() -> int:
    root = Path(__file__).absolute().parents[4]
    sys.path.insert(0, str(root / "01_KISH_ENGINE"))
    with tempfile.TemporaryDirectory(prefix="babylon-lot12-home-") as home:
        # macOS may spell its temporary root through /var -> /private/var.
        # Canonicalize only this owned fixture, never a production root.
        home = os.path.realpath(home)
        os.environ["HOME"] = home
        os.environ["BABYLON_HOME"] = str(Path(home) / ".babylon60")
        os.environ["TMPDIR"] = home
        tempfile.tempdir = None
        for key in (
            "CORTEX_VAULT_KEY", "KIMI_API_KEY", "MOONSHOT_API_KEY",
            "OPENROUTER_API_KEY", "MOONSHOT_API_URL", "OPENROUTER_API_URL",
            "MOONSHOT_MODEL", "OPENROUTER_MODEL", "BABYLON_AEON_TRUSTED_PUBLIC_KEY_B64",
        ):
            os.environ.pop(key, None)
        os.environ["BABYLON60_SIGNING_SEED"] = "00" * 32
        import dotenv
        dotenv.load_dotenv = lambda *a, **k: False
        dotenv.dotenv_values = lambda *a, **k: {}
        sys.modules["strike_rs"] = None

        def blocked(*args, **kwargs):
            raise AssertionError("TCP/DNS forbidden in confined regression suite")

        original_connect = socket.socket.connect
        original_connect_ex = socket.socket.connect_ex

        def connect(self, *args, **kwargs):
            if self.family in (socket.AF_INET, socket.AF_INET6):
                return blocked()
            return original_connect(self, *args, **kwargs)

        def connect_ex(self, *args, **kwargs):
            if self.family in (socket.AF_INET, socket.AF_INET6):
                return blocked()
            return original_connect_ex(self, *args, **kwargs)

        socket.socket.connect = connect
        socket.socket.connect_ex = connect_ex
        socket.getaddrinfo = blocked
        import pytest
        return pytest.main(sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
