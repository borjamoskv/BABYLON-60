"""CLI checks run in an isolated environment with fixture secrets only."""

import os
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).absolute().parents[2]
CLI = ROOT / "01_KISH_ENGINE/babylon60/cli/license_cli.py"


class LicenseCliTests(unittest.TestCase):
    def invoke(self, args: list[str], secret: str | None = None) -> subprocess.CompletedProcess[str]:
        environment = {"PATH": os.defpath, "PYTHONPATH": str(ROOT / "01_KISH_ENGINE")}
        if secret is not None:
            environment["BABYLON60_LICENSE_SALT"] = secret
        return subprocess.run(
            [sys.executable, str(CLI), *args], env=environment, capture_output=True, text=True, check=False
        )

    def test_generation_without_secret_refuses_without_issuing_key(self) -> None:
        result = self.invoke(["generate", "--owner", "isolated-fixture"])
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("GENERATED SUCCESSFULLY", result.stdout)

    def test_test_credential_is_never_a_commercial_licence(self) -> None:
        result = self.invoke(["verify", "--key", "b60_test_fixture"])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("INVALID", result.stdout)

    def test_new_fixture_uses_full_signature(self) -> None:
        signing_key = "isolated-cli-fixture-secret-2026-only"
        result = self.invoke(["generate", "--owner", "isolated-fixture"], signing_key)
        self.assertEqual(result.returncode, 0, result.stderr)
        match = re.search(r"^KEY: (.+)$", result.stdout, re.M)
        assert match is not None
        key = match[1]
        self.assertEqual(len(key.split(":")[-1]), 64)
        self.assertEqual(self.invoke(["verify", "--key", key], signing_key).returncode, 0)
