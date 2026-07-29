from unittest.mock import patch, MagicMock
from scripts.pre_push_ledger_guard import verify_exergy, verify_invariants, main

def test_verify_exergy_pass():
    with patch("scripts.pre_push_ledger_guard.run_exergy_optimizer", return_value=True):
        assert verify_exergy() is True

def test_verify_exergy_fail():
    with patch("scripts.pre_push_ledger_guard.run_exergy_optimizer", return_value=False):
        assert verify_exergy() is False

def test_verify_invariants_pass():
    mock_res = MagicMock()
    mock_res.returncode = 0
    with patch("subprocess.run", return_value=mock_res):
        assert verify_invariants() is True

def test_verify_invariants_fail():
    mock_res = MagicMock()
    mock_res.returncode = 1
    mock_res.stdout = "Failed"
    mock_res.stderr = "Error"
    with patch("subprocess.run", return_value=mock_res):
        assert verify_invariants() is False

def test_verify_symlink_depth_pass():
    mock_res = MagicMock()
    mock_res.returncode = 0
    with patch("subprocess.run", return_value=mock_res):
        from scripts.pre_push_ledger_guard import verify_symlink_depth
        assert verify_symlink_depth() is True

def test_verify_symlink_depth_fail():
    mock_res = MagicMock()
    mock_res.returncode = 1
    mock_res.stdout = "Failed"
    mock_res.stderr = "Error"
    with patch("subprocess.run", return_value=mock_res):
        from scripts.pre_push_ledger_guard import verify_symlink_depth
        assert verify_symlink_depth() is False

def test_main_success():
    with patch("scripts.pre_push_ledger_guard.verify_exergy", return_value=True), \
         patch("scripts.pre_push_ledger_guard.verify_invariants", return_value=True), \
         patch("scripts.pre_push_ledger_guard.verify_symlink_depth", return_value=True):
        assert main() == 0

def test_main_exergy_fail():
    with patch("scripts.pre_push_ledger_guard.verify_exergy", return_value=False):
        assert main() == 1

