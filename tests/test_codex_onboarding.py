"""Isolated CLI doubles exercise onboarding without touching the user's Codex."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import IO, cast

import pytest

from babylon60 import onboarding
from babylon60.experience import load_mcp_instructions, load_presentation_guide


_CLI = r"""
import json, os, sys
from pathlib import Path
home = Path(os.environ["CODEX_HOME"])
home.mkdir(parents=True, exist_ok=True)
state_path = home / "double-mcp.json"
calls_path = home / "double-calls.jsonl"
arguments = sys.argv[1:]
with calls_path.open("a", encoding="utf-8") as stream:
    stream.write(json.dumps(arguments) + "\n")
servers = json.loads(state_path.read_text()) if state_path.exists() else {"foreign": {"untouched": True}}
if os.environ.get("DOUBLE_BROKEN_CONFIG"):
    print("Error reading TOML: token TOP_SECRET", file=sys.stderr)
    sys.exit(2)
action, name = arguments[1:3]
if action == "get":
    if name not in servers:
        print("Error: No MCP server named '" + name + "' found.", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(servers[name]))
elif action == "add":
    if os.environ.get("DOUBLE_FAIL_ADD"):
        sys.exit(3)
    split = arguments.index("--")
    environment = {}
    index = 3
    while index < split:
        assert arguments[index] == "--env"
        key, value = arguments[index + 1].split("=", 1)
        environment[key] = value
        index += 2
    servers[name] = {"name": name, "enabled": True, "transport": {
        "type": "stdio", "command": arguments[split + 1], "args": arguments[split + 2:],
        "env": environment, "env_vars": [], "cwd": None}}
    state_path.write_text(json.dumps(servers), encoding="utf-8")
    if os.environ.get("DOUBLE_FAIL_AFTER_ADD"):
        sys.exit(4)
elif action == "remove":
    servers.pop(name, None)
    state_path.write_text(json.dumps(servers), encoding="utf-8")
else:
    sys.exit(9)
"""


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    home = tmp_path / "Códex perfil con espacios"
    data = tmp_path / "Babilón datos con espacios"
    home.mkdir()
    cli = tmp_path / "codex_double.py"
    cli.write_text(_CLI, encoding="utf-8")
    monkeypatch.setenv("CODEX_HOME", str(home))
    monkeypatch.setenv("BABYLON_HOME", str(data))
    monkeypatch.setattr(shutil, "which", lambda name: sys.executable)
    real_run = subprocess.run

    def invoke(
        command: list[str],
        *,
        env: dict[str, str],
        cwd: Path,
        capture_output: bool,
        timeout: int,
        check: bool,
    ) -> subprocess.CompletedProcess[bytes]:
        assert isinstance(command, list)
        if len(command) > 1 and command[1] == "mcp":
            command = [command[0], str(cli), *command[1:]]
        return real_run(command, env=env, cwd=cwd, capture_output=capture_output, timeout=timeout, check=check)

    monkeypatch.setattr(subprocess, "run", invoke)
    return home, data


def _object(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return cast(dict[str, object], value)


def _servers(home: Path) -> dict[str, dict[str, object]]:
    servers = _object(json.loads((home / "double-mcp.json").read_text()))
    return {name: _object(value) for name, value in servers.items()}


def _calls(home: Path) -> list[list[str]]:
    return [json.loads(line) for line in (home / "double-calls.jsonl").read_text().splitlines()]


def _seed(home: Path, transport: dict[str, object]) -> None:
    value = dict(transport)
    enabled = value.pop("enabled", True)
    (home / "double-mcp.json").write_text(
        json.dumps({"foreign": {"untouched": True}, "babylon60": {"enabled": enabled, "transport": value}})
    )


def test_setup_idempotent_and_remove_preserve_foreign_bytes(client: tuple[Path, Path]) -> None:
    home, data = client
    preferences = b"# Mis preferencias\r\nPreserva el espa\xc3\xb1ol.\r\n"
    agents = home / "AGENTS.md"
    agents.write_bytes(preferences)
    assert onboarding.setup_codex()["ok"] is True
    installed = agents.read_bytes()
    state = (data / "integrations/codex.json").read_bytes()
    assert installed.startswith(preferences)
    assert installed.count(onboarding._START) == 1
    assert len(installed) - len(preferences) <= 2000
    server = _servers(home)["babylon60"]
    assert isinstance(server, dict)
    transport = _object(server["transport"])
    assert Path(str(transport["command"])).is_absolute()
    assert transport["args"] == ["-m", "babylon60.mcp.cortex_mcp_server", "--ledger", str(data / "mcp_ledger.db")]
    assert _object(transport["env"])["BABYLON_CAUSAL_GATE_DB"] == str(data / "causal_gate.db")
    assert onboarding.setup_codex()["ok"] is True
    assert agents.read_bytes() == installed
    assert (data / "integrations/codex.json").read_bytes() == state
    assert sum(call[1] == "add" for call in _calls(home)) == 1
    data.joinpath("mcp_ledger.db").write_bytes(b"user ledger")
    assert onboarding.setup_codex(remove=True)["status"] == "removed"
    assert agents.read_bytes() == preferences
    assert _servers(home) == {"foreign": {"untouched": True}}
    assert (data / "mcp_ledger.db").read_bytes() == b"user ledger"
    assert onboarding.setup_codex(remove=True)["status"] == "not_configured"


def test_dry_run_has_no_managed_writes_or_cli_mutations(client: tuple[Path, Path]) -> None:
    home, data = client
    agents = home / "AGENTS.md"
    agents.write_bytes(b"Personal\n")
    result = onboarding.setup_codex(dry_run=True)
    assert result["status"] == "dry_run"
    assert result["steps"]
    assert agents.read_bytes() == b"Personal\n"
    assert not data.exists()
    assert not (home / "double-mcp.json").exists()
    assert all(call[1] == "get" for call in _calls(home))


def test_new_codex_home_can_be_previewed_then_initialized(client: tuple[Path, Path]) -> None:
    home, data = client
    home.rmdir()
    assert onboarding.setup_codex(dry_run=True)["status"] == "dry_run"
    assert not home.exists()
    assert not data.exists()
    assert onboarding.setup_codex()["ok"] is True
    assert "babylon60" in _servers(home)


def test_effective_override_is_migrated_without_duplicate(client: tuple[Path, Path]) -> None:
    home, _ = client
    normal = home / "AGENTS.md"
    normal.write_bytes(b"Original\r\n")
    override = home / "AGENTS.override.md"
    override.write_bytes(b" \n")
    assert onboarding.setup_codex()["ok"] is True
    assert onboarding._START in normal.read_bytes()
    override.write_bytes(b"Override privado\r\n")
    assert onboarding.doctor_codex()["ok"] is False
    assert onboarding.setup_codex()["ok"] is True
    assert normal.read_bytes() == b"Original\r\n"
    assert override.read_bytes().count(onboarding._START) == 1
    assert onboarding.setup_codex(remove=True)["ok"] is True
    assert override.read_bytes() == b"Override privado\r\n"


def test_homonymous_foreign_mcp_conflicts_without_changes(client: tuple[Path, Path]) -> None:
    home, data = client
    _seed(home, {"type": "stdio", "command": "/foreign/python", "args": ["other"], "env": {}})
    original = (home / "double-mcp.json").read_bytes()
    result = onboarding.setup_codex()
    assert result["ok"] is False
    assert "otra configuración" in str(result["message"])
    assert (home / "double-mcp.json").read_bytes() == original
    assert not (home / "AGENTS.md").exists()
    assert not data.exists()


def test_existing_identical_registration_is_reused_without_claiming_it(client: tuple[Path, Path]) -> None:
    home, data = client
    _seed(home, onboarding._transport(data))
    assert onboarding.setup_codex()["ok"] is True
    assert onboarding.setup_codex(remove=True)["ok"] is True
    assert "babylon60" in _servers(home)
    assert all(call[1] == "get" for call in _calls(home))


def test_missing_cli_and_broken_config_are_actionable_and_do_not_leak(
    client: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    home, data = client
    monkeypatch.setenv("DOUBLE_BROKEN_CONFIG", "1")
    result = onboarding.setup_codex()
    assert result["ok"] is False
    assert "TOP_SECRET" not in json.dumps(result)
    assert "codex mcp get" in str(result["message"])
    monkeypatch.setattr(shutil, "which", lambda name: None)
    result = onboarding.setup_codex()
    assert "Instálalo" in str(result["message"])
    assert not data.exists()
    assert not (home / "AGENTS.md").exists()


@pytest.mark.parametrize("after_add", [False, True])
def test_partial_registration_failure_rolls_back_only_owned_changes(
    client: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch, after_add: bool
) -> None:
    home, data = client
    (home / "AGENTS.md").write_bytes(b"User original\r\n")
    monkeypatch.setenv("DOUBLE_FAIL_AFTER_ADD" if after_add else "DOUBLE_FAIL_ADD", "1")
    result = onboarding.setup_codex()
    assert result["ok"] is False
    assert result["rollback"] == []
    assert (home / "AGENTS.md").read_bytes() == b"User original\r\n"
    assert not (data / "integrations/codex.json").exists()
    if (home / "double-mcp.json").exists():
        assert _servers(home) == {"foreign": {"untouched": True}}


def test_state_failure_reverts_registration_and_preferences(
    client: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    home, data = client
    original_replace = onboarding._replace

    def fail_state(before: onboarding._File, content: bytes | None) -> onboarding._File:
        if before.path.name == "codex.json":
            raise OSError("state write failed")
        return original_replace(before, content)

    monkeypatch.setattr(onboarding, "_replace", fail_state)
    result = onboarding.setup_codex()
    assert result["ok"] is False
    assert not (home / "AGENTS.md").exists()
    assert _servers(home) == {"foreign": {"untouched": True}}
    assert not (data / "integrations/codex.json").exists()


def test_rollback_preserves_external_instruction_edit(
    client: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    home, _ = client
    original_add = onboarding._add

    def interrupted_add(executable: str, codex_home: Path, transport: dict[str, object]) -> None:
        (home / "AGENTS.md").write_bytes(b"Concurrent edit\n")
        monkeypatch.setenv("DOUBLE_FAIL_ADD", "1")
        original_add(executable, codex_home, transport)

    monkeypatch.setattr(onboarding, "_add", interrupted_add)
    result = onboarding.setup_codex()
    assert result["status"] == "rollback_incomplete"
    assert (home / "AGENTS.md").read_bytes() == b"Concurrent edit\n"


def test_atomic_replace_detects_changes_before_replace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "AGENTS.md"
    target.write_bytes(b"before")
    before = onboarding._read(target)
    real_unchanged = onboarding._unchanged
    count = 0

    def concurrent(file: onboarding._File) -> bool:
        nonlocal count
        count += 1
        if count == 2:
            target.write_bytes(b"other writer")
        return real_unchanged(file)

    monkeypatch.setattr(onboarding, "_unchanged", concurrent)
    with pytest.raises(onboarding._IntegrationError, match="concurrente"):
        onboarding._replace(before, b"ours")
    assert target.read_bytes() == b"other writer"
    assert not list(tmp_path.glob(".babylon60-*"))


@pytest.mark.parametrize("link_kind", ["symbolic", "hard"])
def test_instruction_links_are_rejected(client: tuple[Path, Path], tmp_path: Path, link_kind: str) -> None:
    home, data = client
    target = tmp_path / "foreign.md"
    target.write_bytes(b"foreign")
    link = home / "AGENTS.md"
    try:
        if link_kind == "symbolic":
            link.symlink_to(target)
        else:
            os.link(target, link)
    except OSError:
        pytest.skip("filesystem does not permit creating this link")
    result = onboarding.setup_codex()
    assert result["ok"] is False
    assert target.read_bytes() == b"foreign"
    assert not data.exists()


def test_linked_codex_config_is_not_rewritten(client: tuple[Path, Path], tmp_path: Path) -> None:
    home, data = client
    foreign = tmp_path / "foreign-config.toml"
    foreign.write_bytes(b"external config\n")
    try:
        (home / "config.toml").symlink_to(foreign)
    except OSError:
        pytest.skip("filesystem does not permit creating a symbolic link")
    assert onboarding.setup_codex()["ok"] is False
    assert foreign.read_bytes() == b"external config\n"
    assert not data.exists()


def test_modified_managed_block_and_registration_are_preserved(client: tuple[Path, Path]) -> None:
    home, _ = client
    assert onboarding.setup_codex()["ok"] is True
    target = home / "AGENTS.md"
    edited = target.read_bytes().replace(b"MOSKV-1", b"MOSKV-modified")
    assert edited != target.read_bytes()
    target.write_bytes(edited)
    assert onboarding.setup_codex(remove=True)["ok"] is False
    assert target.read_bytes() == edited
    servers = _servers(home)
    _object(servers["babylon60"]["transport"])["command"] = "/external/change"
    (home / "double-mcp.json").write_text(json.dumps(servers))
    result = onboarding.setup_codex(remove=True)
    assert result["ok"] is False
    assert _object(_servers(home)["babylon60"]["transport"])["command"] == "/external/change"


def test_external_tool_filters_and_timeouts_are_not_removed(client: tuple[Path, Path]) -> None:
    home, _ = client
    assert onboarding.setup_codex()["ok"] is True
    servers = _servers(home)
    servers["babylon60"]["disabled_tools"] = ["memory_store"]
    servers["babylon60"]["tool_timeout_sec"] = 321
    (home / "double-mcp.json").write_text(json.dumps(servers))
    result = onboarding.setup_codex(remove=True)
    assert result["ok"] is False
    assert _servers(home) == servers
    assert onboarding._START in (home / "AGENTS.md").read_bytes()


def test_unexposed_config_changes_are_guarded_without_rebasing(client: tuple[Path, Path]) -> None:
    home, data = client
    config = home / "config.toml"
    config.write_text("# original config\n")
    assert onboarding.setup_codex()["ok"] is True
    state_path = data / "integrations/codex.json"
    original_state = state_path.read_bytes()
    config.write_text('# changed outside Babylon\n[mcp_servers.babylon60]\nrequired = true\napi_key = "keep-private"\n')
    # Codex's get may omit required and approval options; reruns cannot claim them.
    assert onboarding.setup_codex()["ok"] is True
    assert state_path.read_bytes() == original_state
    result = onboarding.setup_codex(remove=True)
    assert result["ok"] is False
    assert "config.toml cambió" in str(result["message"])
    assert "required = true" in config.read_text()
    assert "keep-private" not in state_path.read_text()
    assert "keep-private" not in json.dumps(result)
    assert "babylon60" in _servers(home)


def test_external_config_edit_before_mutation_is_preserved(
    client: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    home, _ = client
    config = home / "config.toml"
    config.write_bytes(b"before\n")
    replace = onboarding._replace

    def concurrent(before: onboarding._File, content: bytes | None) -> onboarding._File:
        after = replace(before, content)
        if before.path.name == "AGENTS.md" and content:
            config.write_bytes(b"external config change\n")
        return after

    monkeypatch.setattr(onboarding, "_replace", concurrent)
    result = onboarding.setup_codex()
    assert result["ok"] is False
    assert config.read_bytes() == b"external config change\n"
    assert not (home / "AGENTS.md").exists()
    assert all(call[1] == "get" for call in _calls(home))


def test_concurrent_override_activation_does_not_report_configured(
    client: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    home, data = client
    add = onboarding._add

    def activate(executable: str, codex_home: Path, transport: dict[str, object]) -> None:
        add(executable, codex_home, transport)
        (home / "AGENTS.override.md").write_bytes(b"external override\n")

    monkeypatch.setattr(onboarding, "_add", activate)
    result = onboarding.setup_codex()
    assert result["ok"] is False
    assert "efectivo cambió" in str(result["message"])
    assert (home / "AGENTS.override.md").read_bytes() == b"external override\n"
    assert not (home / "AGENTS.md").exists()
    assert "babylon60" not in _servers(home)
    assert not (data / "integrations/codex.json").exists()


def test_effective_override_does_not_read_inactive_symlink(client: tuple[Path, Path], tmp_path: Path) -> None:
    home, _ = client
    foreign = tmp_path / "dotfiles-agents.md"
    foreign.write_bytes(b"foreign instructions\n")
    try:
        (home / "AGENTS.md").symlink_to(foreign)
    except OSError:
        pytest.skip("filesystem does not permit creating a symbolic link")
    override = home / "AGENTS.override.md"
    override.write_bytes(b"active override\n")
    assert onboarding.setup_codex()["ok"] is True
    assert onboarding._START in override.read_bytes()
    assert foreign.read_bytes() == b"foreign instructions\n"


def test_unknown_markers_and_corrupt_state_do_not_overwrite(client: tuple[Path, Path]) -> None:
    home, data = client
    target = home / "AGENTS.md"
    target.write_bytes(onboarding._START + b"\nforeign Babylon block\n" + onboarding._END)
    assert onboarding.setup_codex()["ok"] is False
    state = data / "integrations/codex.json"
    state.parent.mkdir(parents=True)
    state.write_bytes(b"{broken")
    assert onboarding.setup_codex()["ok"] is False
    assert state.read_bytes() == b"{broken"


def test_multiple_codex_homes_keep_separate_ownership(
    client: tuple[Path, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first, data = client
    assert onboarding.setup_codex()["ok"] is True
    second = tmp_path / "another Codex"
    second.mkdir()
    monkeypatch.setenv("CODEX_HOME", str(second))
    assert onboarding.setup_codex()["ok"] is True
    assert onboarding.setup_codex(remove=True)["ok"] is True
    assert "babylon60" in _servers(first)
    assert onboarding._START in (first / "AGENTS.md").read_bytes()
    state = json.loads((data / "integrations/codex.json").read_text())
    assert set(state["clients"]) == {str(first)}


def test_doctor_keeps_behavior_unverified_and_uses_expected_executable(
    client: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    _, data = client
    assert onboarding.setup_codex()["ok"] is True
    ledger = data / "mcp_ledger.db"
    ledger.write_bytes(b"production data")
    observed: list[dict[str, object]] = []

    def isolated(transport: dict[str, object]) -> dict[str, object]:
        observed.append(transport)
        return {"isolated": True, "tools": 1}

    monkeypatch.setattr(onboarding, "_probe", isolated)
    report = onboarding.doctor_codex()
    assert report["ok"] is True
    assert report["checks"] == {
        "configuration": "OK",
        "executable": "OK",
        "mcp": "OK",
        "contract": "OK",
        "behavior": "NO_VERIFICADO",
    }
    assert observed == [onboarding._transport(data)]
    assert ledger.read_bytes() == b"production data"


@pytest.mark.parametrize(
    ("overrides", "expected_error"),
    [
        pytest.param({}, None, id="valid"),
        pytest.param(
            {"initialize": {"result": {"protocolVersion": "unsupported"}}},
            "versión MCP",
            id="unsupported-protocol",
        ),
        pytest.param(
            {"initialize": {"result": {"protocolVersion": None}}},
            "versión MCP",
            id="missing-protocol",
        ),
        pytest.param({"initialize": {"id": True}}, "identificador", id="boolean-id"),
        pytest.param({"tools/list": {"id": 2.0}}, "identificador", id="floating-id"),
        pytest.param({"tools/list": {"result": {"tools": [None]}}}, "herramientas", id="null-tool"),
        pytest.param({"tools/list": {"result": {"tools": [{}]}}}, "herramientas", id="unnamed-tool"),
        pytest.param({"tools/list": {"result": {"tools": [{"name": ""}]}}}, "herramientas", id="empty-tool-name"),
        pytest.param({"tools/list": {"result": {"tools": [{"name": "   "}]}}}, "herramientas", id="blank-tool-name"),
        pytest.param({"tools/list": {"result": {"tools": [{"name": 42}]}}}, "herramientas", id="numeric-tool-name"),
    ],
)
def test_probe_uses_protocol_sequence_and_temporary_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    overrides: dict[str, object],
    expected_error: str | None,
) -> None:
    """A tiny protocol peer checks initialized before tools and temporary writes."""
    script = tmp_path / "peer.py"
    audit = tmp_path / "probe-audit.json"
    script.write_text(
        "import json, os, sys\nfrom pathlib import Path\n"
        f"expected_instructions = {load_mcp_instructions()!r}\n"
        f"expected_guide = {load_presentation_guide()!r}\n"
        f"overrides = {overrides!r}\n"
        "args = sys.argv[1:]\n"
        f"Path({str(audit)!r}).write_text(json.dumps({{'cwd': os.getcwd(), 'home': os.environ['BABYLON_HOME'], 'gate': os.environ['BABYLON_CAUSAL_GATE_DB'], 'ledger': args[args.index('--ledger') + 1], 'pythonpath': os.environ.get('PYTHONPATH')}}))\n"
        "initialized = False\n"
        "for line in sys.stdin:\n"
        " request = json.loads(line)\n method = request['method']\n"
        " if method == 'initialize': result = {'protocolVersion': '2024-11-05', 'instructions': expected_instructions, 'serverInfo': {'name': 'test-peer'}}\n"
        " elif method == 'notifications/initialized': initialized = True; continue\n"
        " elif method == 'tools/list':\n  assert initialized\n  result = {'tools': [{'name': 'read'}]}\n"
        " elif method == 'resources/read': result = {'contents': [{'uri': request['params']['uri'], 'text': expected_guide}]}\n"
        " response = {'jsonrpc': '2.0', 'id': request['id'], 'result': result}\n"
        " for key, value in overrides.get(method, {}).items():\n"
        "  if key == 'result':\n"
        "   for field, replacement in value.items():\n"
        "    if replacement is None: result.pop(field, None)\n"
        "    else: result[field] = replacement\n"
        "  else: response[key] = value\n"
        " print(json.dumps({'jsonrpc': '2.0', 'method': 'notifications/progress'}), flush=True)\n"
        " print(json.dumps(response), flush=True)\n",
        encoding="utf-8",
    )
    real_popen = subprocess.Popen
    peers: list[subprocess.Popen[bytes]] = []

    def peer(
        command: list[str],
        *,
        stdin: int,
        stdout: int,
        stderr: IO[bytes],
        cwd: Path,
        env: dict[str, str],
    ) -> subprocess.Popen[bytes]:
        assert command[1:3] == ["-m", "babylon60.mcp.cortex_mcp_server"]
        process = real_popen(
            [command[0], str(script), *command[3:]],
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            cwd=cwd,
            env=env,
        )
        peers.append(process)
        return process

    monkeypatch.setattr(subprocess, "Popen", peer)
    monkeypatch.setenv("PYTHONPATH", "must-not-propagate")
    transport = onboarding._transport(tmp_path / "productive")
    if expected_error is None:
        details = onboarding._probe(transport)
        assert details["isolated"] is True
        assert details["protocol"] == "2024-11-05"
        assert details["tools"] == 1
    else:
        with pytest.raises(onboarding._IntegrationError, match=expected_error):
            onboarding._probe(transport)
    assert len(peers) == 1 and peers[0].poll() is not None
    observation = json.loads(audit.read_text())
    assert observation["pythonpath"] is None
    directory = Path(observation["ledger"]).parent
    assert directory.name == Path(observation["cwd"]).name
    for name in ("home", "gate", "ledger"):
        assert Path(observation[name]).is_relative_to(directory)
    assert not directory.exists()
    assert not (tmp_path / "productive").exists()


def test_probe_rejects_notification_flood_and_reaps_peer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    script = tmp_path / "flood_peer.py"
    script.write_text(
        "import json, sys\n"
        "sys.stdin.readline()\n"
        "for index in range(256):\n"
        " print(json.dumps({'jsonrpc': '2.0', 'method': 'notifications/progress'}), flush=True)\n"
        "sys.stdin.read()\n",
        encoding="utf-8",
    )
    real_popen = subprocess.Popen
    peers: list[subprocess.Popen[bytes]] = []
    directories: list[Path] = []

    def peer(
        command: list[str],
        *,
        stdin: int,
        stdout: int,
        stderr: IO[bytes],
        cwd: Path,
        env: dict[str, str],
    ) -> subprocess.Popen[bytes]:
        process = real_popen(
            [command[0], str(script)],
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            cwd=cwd,
            env=env,
        )
        peers.append(process)
        directories.append(cwd)
        return process

    monkeypatch.setattr(subprocess, "Popen", peer)
    with pytest.raises(onboarding._IntegrationError, match="no devolvió la respuesta esperada"):
        onboarding._probe(onboarding._transport(tmp_path / "productive"))
    assert len(peers) == 1 and peers[0].poll() is not None
    assert not directories[0].exists()
    assert not (tmp_path / "productive").exists()


def test_windows_cmd_discovery_does_not_require_shell(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        shutil, "which", lambda name: r"C:\Program Files\Codex\codex.cmd" if name == "codex.cmd" else None
    )
    assert onboarding._codex().endswith("codex.cmd")


def test_windows_npm_shim_is_called_directly_through_node(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    base = tmp_path / "Program Files with & Unicode ñ"
    script = base / "node_modules/@openai/codex/bin/codex.js"
    script.parent.mkdir(parents=True)
    script.write_text("// official entry point")
    node = base / "node.exe"
    node.write_bytes(b"node fixture")
    monkeypatch.setattr(sys, "platform", "win32")
    assert onboarding._codex_prefix(str(base / "codex.cmd")) == [str(node), str(script)]


def test_unknown_windows_batch_shim_fails_with_actionable_message(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(shutil, "which", lambda name: None)
    with pytest.raises(onboarding._IntegrationError, match="CLI oficial"):
        onboarding._codex_prefix(str(tmp_path / "codex.cmd"))
