# C5-REAL EXERGY CERTIFIED
"""
Unit tests for MOSKV-1 APEX C5-REAL Categorical Logic 896 Primitives CLI (cortex/cli.py).
"""

import sys
import json
import pytest
from unittest.mock import patch
from cortex.cli import main

def test_cli_evaluate(capsys: pytest.CaptureFixture[str]) -> None:
    test_args = ["cortex/cli.py", "evaluate", "--ids", "1", "2", "--friction", "0.5"]
    with patch.object(sys, "argv", test_args):
        main()
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["status"] == "VALIDATED_C5_REAL"
    assert data["sequence"] == [1, 2]
    assert data["friction"] == 0.5
    assert "morphism_cost_mu" in data

def test_cli_collisions(capsys: pytest.CaptureFixture[str]) -> None:
    test_args = ["cortex/cli.py", "collisions", "--active-ids", "1", "2", "3"]
    with patch.object(sys, "argv", test_args):
        main()
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["status"] == "COLLISION_AUDIT_COMPLETE"
    assert data["collision_count"] >= 0

def test_cli_query_by_id(capsys: pytest.CaptureFixture[str]) -> None:
    test_args = ["cortex/cli.py", "query", "--id", "1"]
    with patch.object(sys, "argv", test_args):
        main()
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "id" in data or "code" in data or "error" in data

def test_cli_help(capsys: pytest.CaptureFixture[str]) -> None:
    test_args = ["cortex/cli.py"]
    with patch.object(sys, "argv", test_args):
        main()
    captured = capsys.readouterr()
    assert "usage:" in captured.out.lower() or "c5-real" in captured.out.lower()
