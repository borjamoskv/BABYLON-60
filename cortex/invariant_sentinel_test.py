"""
Tests for cortex/invariant_sentinel.py
Achieves >90% coverage for Invariant Sentinel module.
"""

import os
import sys
import unittest
import subprocess
from typing import Any
from unittest.mock import patch, mock_open, MagicMock

from cortex.invariant_sentinel import (
    get_current_branch,
    get_python_version,
    audit_and_align_invariants,
    RULES_FILE,
)


class TestInvariantSentinel(unittest.TestCase):
    @patch("subprocess.check_output")
    def test_get_current_branch_success(self, mock_check_output: MagicMock) -> None:
        mock_check_output.return_value = b"feature/bft-fix\n"
        branch = get_current_branch()
        self.assertEqual(branch, "feature/bft-fix")

    @patch("subprocess.check_output")
    def test_get_current_branch_called_process_error(
        self, mock_check_output: MagicMock
    ) -> None:
        mock_check_output.side_effect = subprocess.CalledProcessError(1, ["git"])
        branch = get_current_branch()
        self.assertEqual(branch, "master")

    @patch("subprocess.check_output")
    def test_get_current_branch_file_not_found_error(
        self, mock_check_output: MagicMock
    ) -> None:
        mock_check_output.side_effect = FileNotFoundError()
        branch = get_current_branch()
        self.assertEqual(branch, "master")

    @patch("subprocess.check_output")
    def test_get_current_branch_os_error(self, mock_check_output: MagicMock) -> None:
        mock_check_output.side_effect = OSError()
        branch = get_current_branch()
        self.assertEqual(branch, "master")

    def test_get_python_version(self) -> None:
        expected = f"{sys.version_info.major}.{sys.version_info.minor}"
        self.assertEqual(get_python_version(), expected)

    def test_audit_and_align_invariants_full_run(self) -> None:
        # Run audit on current workspace to test standard execution path
        result = audit_and_align_invariants()
        self.assertIsInstance(result, bool)

    @patch("os.walk")
    @patch("os.path.exists")
    def test_audit_and_align_invariants_mocked_walk_and_rules(
        self, mock_exists: MagicMock, mock_walk: MagicMock
    ) -> None:
        user_home = os.path.expanduser("~")
        
        # Setup mock directory walk:
        # Level 0: root containing ignored dirs and normal files
        # Level 5: deep directory to hit depth >= 5 prune condition
        mock_walk.return_value = [
            (".", [".git", ".venv", "subfolder"], ["clean.py", "tainted.py", "unreadable.py", "binary.py"]),
            ("./subfolder", ["deep_sub"], ["sub.ts"]),
            ("./1/2/3/4/5", ["too_deep"], ["deep.py"]),
        ]
        
        def mock_exists_side_effect(path: str) -> bool:
            if path == RULES_FILE:
                return True
            return False

        mock_exists.side_effect = mock_exists_side_effect

        def custom_open(file: Any, mode: str = "r", encoding: Any = None, **kwargs: Any) -> Any:
            if "tainted.py" in str(file):
                return mock_open(read_data=f"# Tainted with {user_home}")()
            elif "unreadable.py" in str(file):
                raise OSError("Disk error")
            elif "binary.py" in str(file):
                raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")
            elif file == RULES_FILE:
                return mock_open(read_data="rules content")()
            return mock_open(read_data="# clean code")()

        with patch("builtins.open", side_effect=custom_open):
            result = audit_and_align_invariants()
            self.assertFalse(result)

    @patch("os.path.exists")
    def test_audit_and_align_invariants_rules_file_os_error(
        self, mock_exists: MagicMock
    ) -> None:
        mock_exists.return_value = True

        def custom_open(file: Any, mode: str = "r", encoding: Any = None, **kwargs: Any) -> Any:
            if file == RULES_FILE:
                raise OSError("Permission denied")
            return mock_open(read_data="")()

        with patch("builtins.open", side_effect=custom_open):
            result = audit_and_align_invariants()
            self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
