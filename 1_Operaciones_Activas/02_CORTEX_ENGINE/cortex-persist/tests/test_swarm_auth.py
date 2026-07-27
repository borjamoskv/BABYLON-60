import pytest
import asyncio
import json
from unittest.mock import patch, MagicMock
from pathlib import Path
from babylon60.swarm.auth import ByzantineAuthLayer, AUTH_DIR

def test_is_command_safe():
    assert ByzantineAuthLayer.is_command_safe("ls -la") is True
    assert ByzantineAuthLayer.is_command_safe("pwd") is True
    assert ByzantineAuthLayer.is_command_safe("cat file.txt") is True
    assert ByzantineAuthLayer.is_command_safe("rm -rf /") is False
    assert ByzantineAuthLayer.is_command_safe("ls | grep text") is False
    assert ByzantineAuthLayer.is_command_safe("echo test > file.txt") is False

@pytest.mark.asyncio
async def test_acquire_lock_zenith():
    result = await ByzantineAuthLayer.acquire_lock("OS_COMMAND", {"command": "rm file"}, zenith_score=1.0)
    assert result is True

@pytest.mark.asyncio
async def test_acquire_lock_safe_command():
    result = await ByzantineAuthLayer.acquire_lock("OS_COMMAND", {"command": "ls -la"}, zenith_score=0.5)
    assert result is True

@pytest.mark.asyncio
async def test_acquire_lock_missing_file():
    # If the file gets deleted while waiting, it should return False
    with patch("asyncio.sleep", new_callable=pytest.MonkeyPatch) as mock_sleep:
        async def mock_sleep_func(delay):
            pass
        mock_sleep = mock_sleep_func

        with patch("babylon60.swarm.auth.asyncio.sleep", new=mock_sleep_func):
            with patch("pathlib.Path.exists", return_value=False):
                result = await ByzantineAuthLayer.acquire_lock("OS_COMMAND", {"command": "rm foo"}, zenith_score=0.5)
                assert result is False

@pytest.mark.asyncio
async def test_acquire_lock_approved(tmp_path):
    with patch("babylon60.swarm.auth.AUTH_DIR", tmp_path):
        async def mock_sleep_func(delay):
            # Simulate approval during sleep
            for file in tmp_path.glob("*.json"):
                data = json.loads(file.read_text())
                data["status"] = "APPROVED"
                file.write_text(json.dumps(data))

        with patch("babylon60.swarm.auth.asyncio.sleep", new=mock_sleep_func):
            result = await ByzantineAuthLayer.acquire_lock("OS_COMMAND", {"command": "rm foo"}, zenith_score=0.5)
            assert result is True
            # Check file was deleted
            assert list(tmp_path.glob("*.json")) == []

@pytest.mark.asyncio
async def test_acquire_lock_rejected(tmp_path):
    with patch("babylon60.swarm.auth.AUTH_DIR", tmp_path):
        async def mock_sleep_func(delay):
            for file in tmp_path.glob("*.json"):
                data = json.loads(file.read_text())
                data["status"] = "DENIED"
                file.write_text(json.dumps(data))

        with patch("babylon60.swarm.auth.asyncio.sleep", new=mock_sleep_func):
            result = await ByzantineAuthLayer.acquire_lock("DB_DROP", {"table": "users"}, zenith_score=0.5)
            assert result is False
            assert list(tmp_path.glob("*.json")) == []

@pytest.mark.asyncio
async def test_acquire_lock_timeout(tmp_path):
    with patch("babylon60.swarm.auth.AUTH_DIR", tmp_path):
        async def mock_sleep_func(delay):
            pass # Do not approve or deny, just let it loop 30 times

        with patch("babylon60.swarm.auth.asyncio.sleep", new=mock_sleep_func):
            result = await ByzantineAuthLayer.acquire_lock("DANGEROUS_ACTION", {"key": "val"}, zenith_score=0.5)
            assert result is False
            assert list(tmp_path.glob("*.json")) == []
