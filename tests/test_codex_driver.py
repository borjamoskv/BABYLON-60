"""Codex JSONL completion must agree with both process and turn outcomes."""

import json
import subprocess

import pytest

from babylon60.adapters.codex.codex_driver import CodexDriver


@pytest.fixture
def invoke(tmp_path, monkeypatch):
    cli = tmp_path / "codex"
    cli.touch()
    driver = CodexDriver(cli_path=cli, codex_home=tmp_path / "codex-state")

    def run(events, *, returncode=0, stderr=""):
        stdout = "\n".join(json.dumps(event) for event in events)
        monkeypatch.setattr(
            subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args, returncode, stdout, stderr)
        )
        return driver.ask("Local fixture; no inference")

    return run


def partial_events():
    return [
        {"type": "thread.started", "thread_id": "fixture-thread"},
        {"type": "turn.started"},
        {"type": "item.completed", "item": {"type": "agent_message", "text": "Partial answer"}},
    ]


def test_completed_turn_with_zero_exit_succeeds(invoke):
    usage = {"input_tokens": 3, "output_tokens": 2}
    result = invoke([*partial_events(), {"type": "turn.completed", "usage": usage}])
    assert result["success"] is True
    assert result["text"] == "Partial answer"
    assert result["thread_id"] == "fixture-thread"
    assert result["usage"] == usage
    assert result["events_count"] == 4


@pytest.mark.parametrize("completed", [False, True])
def test_nonzero_exit_cannot_be_hidden_by_partial_text(invoke, completed):
    events = partial_events()
    if completed:
        events.append({"type": "turn.completed", "usage": {"output_tokens": 2}})
    result = invoke(events, returncode=1, stderr="CLI process failed")
    assert result["success"] is False
    assert result["returncode"] == 1
    assert result["error"] == "CLI process failed"
    assert result["text"] == "Partial answer"
    assert result["thread_id"] == "fixture-thread"


@pytest.mark.parametrize(
    ("failure", "message"),
    [
        ({"type": "turn.failed", "error": {"message": "Turn exhausted its retries"}}, "Turn exhausted its retries"),
        ({"type": "error", "message": "Stream disconnected"}, "Stream disconnected"),
        ({"type": "turn.failed"}, "Codex turn failed"),
    ],
)
@pytest.mark.parametrize("completed", [False, True])
def test_terminal_error_is_failure_even_with_zero_exit(invoke, failure, message, completed):
    events = partial_events()
    if completed:
        events.append({"type": "turn.completed", "usage": {"output_tokens": 2}})
    result = invoke([*events, failure], stderr="less specific stderr")
    assert result["success"] is False
    assert result["returncode"] == 0
    assert result["error"] == message
    assert result["text"] == "Partial answer"
    assert result["thread_id"] == "fixture-thread"
    assert result["events_count"] == len(events) + 1


@pytest.mark.parametrize(
    "events",
    [
        [],
        partial_events(),
        [*partial_events(), {"type": "turn.completed"}, {"type": "turn.started"}],
    ],
)
def test_missing_final_completion_is_not_success(invoke, events):
    result = invoke(events)
    assert result["success"] is False
    assert result["returncode"] == 0
    assert "turn.completed" in result["error"]


def test_error_message_survives_nonzero_exit_without_output(invoke):
    result = invoke([{"type": "error", "message": "Authentication failed"}], returncode=1, stderr="stderr fallback")
    assert result["success"] is False
    assert result["error"] == "Authentication failed"
    assert result["returncode"] == 1
