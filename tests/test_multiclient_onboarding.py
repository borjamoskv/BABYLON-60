"""End-to-end onboarding, BLAKE3 ownership, symlink rejection, and doctor tests for claude, cursor, and gemini."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from babylon60 import onboarding


def _configure_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, client: str) -> tuple[Path, Path, Path, Path]:
    data_home = tmp_path / "babylon_state"
    monkeypatch.setenv("BABYLON_HOME", str(data_home))
    if client == "claude":
        home = tmp_path / "claude_home"
        mcp_path = home / ".claude.json"
        profile_path = home / "CLAUDE.md"
        monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(home))
    elif client == "cursor":
        home = tmp_path / "cursor_home"
        mcp_path = home / "mcp.json"
        profile_path = home / "rules" / "babylon60.mdc"
        monkeypatch.setenv("CURSOR_HOME", str(home))
    else:
        home = tmp_path / "gemini_home"
        mcp_path = home / "settings.json"
        profile_path = home / "GEMINI.md"
        monkeypatch.setenv("GEMINI_CLI_HOME", str(home))
    return home, data_home, profile_path, mcp_path


@pytest.mark.parametrize("client", ["claude", "cursor", "gemini"])
def test_multiclient_lifecycle_dry_run_setup_doctor_idempotent_remove(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    client: str,
) -> None:
    home, data_home, profile_path, mcp_path = _configure_env(monkeypatch, tmp_path, client)
    home.mkdir(parents=True)

    # Seed foreign MCP server and foreign preferences to prove zero clobbering
    mcp_path.write_text(
        json.dumps({"otherTopKey": 42, "mcpServers": {"foreign_mcp": {"command": "echo"}}}),
        encoding="utf-8",
    )
    if client != "cursor":
        profile_path.write_text("# Preferencias previas del operador\nNo borrar.\n", encoding="utf-8")

    dry = onboarding.setup_client(client, dry_run=True)
    assert dry["ok"] is True
    assert dry["status"] == "dry_run"
    assert not (data_home / "integrations" / f"{client}.json").exists()

    installed = onboarding.setup_client(client)
    assert installed["ok"] is True, installed
    assert installed["status"] == "configured"
    assert profile_path.is_file()
    assert "MOSKV-1" in profile_path.read_text(encoding="utf-8")

    mcp_doc = json.loads(mcp_path.read_text(encoding="utf-8"))
    assert mcp_doc["otherTopKey"] == 42
    assert mcp_doc["mcpServers"]["foreign_mcp"] == {"command": "echo"}
    assert "babylon60" in mcp_doc["mcpServers"]
    if client == "gemini":
        assert mcp_doc["mcpServers"]["babylon60"]["trust"] is False
    if client == "claude":
        assert mcp_doc["mcpServers"]["babylon60"]["type"] == "stdio"

    # Idempotent second install
    repeated = onboarding.setup_client(client)
    assert repeated["ok"] is True
    assert repeated["status"] == "configured"

    # Doctor checks real isolated MCP handshake + babylon_exergy_transduce advertisement
    doc_report = onboarding.doctor_client(client)
    assert doc_report["ok"] is True, doc_report
    assert doc_report["status"] == "connected"
    checks = doc_report["checks"]
    assert isinstance(checks, dict)
    assert checks["configuration"] == "OK"
    assert checks["mcp"] == "OK"
    assert checks["contract"] == "OK"
    assert checks["behavior"] == "NO_VERIFICADO"
    probe = doc_report["probe"]
    assert isinstance(probe, dict)
    assert probe["exergy_transducer"] is True

    # Non-destructive removal preserves foreign MCP server and prior user text
    removed = onboarding.setup_client(client, remove=True)
    assert removed["ok"] is True
    assert removed["status"] == "removed"
    mcp_after = json.loads(mcp_path.read_text(encoding="utf-8"))
    assert "babylon60" not in mcp_after["mcpServers"]
    assert mcp_after["mcpServers"]["foreign_mcp"] == {"command": "echo"}
    if client == "cursor":
        assert not profile_path.exists()
    else:
        assert profile_path.read_text(encoding="utf-8") == "# Preferencias previas del operador\nNo borrar.\n"

    not_conf = onboarding.setup_client(client, remove=True)
    assert not_conf["ok"] is True
    assert not_conf["status"] == "not_configured"


@pytest.mark.parametrize("client", ["claude", "cursor", "gemini"])
def test_multiclient_refuses_symlink_and_external_tampering(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    client: str,
) -> None:
    home, _, profile_path, mcp_path = _configure_env(monkeypatch, tmp_path, client)
    home.mkdir(parents=True)
    profile_path.parent.mkdir(parents=True, exist_ok=True)

    target = tmp_path / "secret.txt"
    target.write_text("do not touch", encoding="utf-8")
    mcp_path.symlink_to(target)

    symlink_attempt = onboarding.setup_client(client)
    assert symlink_attempt["ok"] is False
    err_msg = str(symlink_attempt["message"]).lower()
    assert any(k in err_msg for k in ("symlink", "symbolic link", "no se puede leer con seguridad"))
    assert target.read_text(encoding="utf-8") == "do not touch"
    mcp_path.unlink()

    assert onboarding.setup_client(client)["ok"] is True
    # External modification of managed MCP entry blocks blind removal
    doc = json.loads(mcp_path.read_text(encoding="utf-8"))
    doc["mcpServers"]["babylon60"]["command"] = "/usr/bin/false"
    mcp_path.write_text(json.dumps(doc), encoding="utf-8")

    tampered_remove = onboarding.setup_client(client, remove=True)
    assert tampered_remove["ok"] is False
    assert "modificado" in str(tampered_remove["message"]).lower()
