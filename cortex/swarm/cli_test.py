"""
Unit tests for C5-REAL Sovereign Swarm CLI (cortex/swarm/cli.py).
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from cortex.swarm.cli import main

def test_swarm_cli_kill_unkill(capsys: pytest.CaptureFixture[str]) -> None:
    lock_file = "kill_switch.lock"
    if os.path.exists(lock_file):
        os.remove(lock_file)
        
    try:
        # Test kill
        test_args_kill = ["cortex/swarm/cli.py", "kill"]
        with patch.object(sys, "argv", test_args_kill):
            main()
        assert os.path.exists(lock_file)
        captured = capsys.readouterr()
        assert "Kill Switch activado" in captured.out

        # Test unkill
        test_args_unkill = ["cortex/swarm/cli.py", "unkill"]
        with patch.object(sys, "argv", test_args_unkill):
            main()
        assert not os.path.exists(lock_file)
        captured = capsys.readouterr()
        assert "Kill Switch desactivado" in captured.out
    finally:
        if os.path.exists(lock_file):
            os.remove(lock_file)

def test_swarm_cli_unkill_inactive(capsys: pytest.CaptureFixture[str]) -> None:
    lock_file = "kill_switch.lock"
    if os.path.exists(lock_file):
        os.remove(lock_file)

    test_args_unkill = ["cortex/swarm/cli.py", "unkill"]
    with patch.object(sys, "argv", test_args_unkill):
        main()
    captured = capsys.readouterr()
    assert "no estaba activo" in captured.out

@patch("cortex.swarm.cli.run_fsm_cycle")
def test_swarm_cli_run(mock_run_fsm: MagicMock) -> None:
    test_args = ["cortex/swarm/cli.py", "run"]
    with patch.object(sys, "argv", test_args):
        main()
    mock_run_fsm.assert_called_once()

@patch("cortex.swarm.cli.ArchitectAgent")
def test_swarm_cli_audit(mock_agent_cls: MagicMock) -> None:
    mock_instance = MagicMock()
    mock_agent_cls.return_value = mock_instance
    test_args = ["cortex/swarm/cli.py", "audit", "--threshold", "15"]
    with patch.object(sys, "argv", test_args):
        main()
    mock_agent_cls.assert_called_once()
    mock_instance.trigger_refactoring.assert_called_once_with(threshold=15)
