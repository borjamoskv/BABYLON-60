"""CLI wiring preserves JSON streams and distinguishes preview from removal."""

from __future__ import annotations

import json
import sys

import pytest

from babylon60.cli import main_dispatcher


@pytest.mark.parametrize("subcommand", ["setup", "doctor"])
@pytest.mark.parametrize("ok", [True, False])
def test_first_use_cli_json_has_no_banner(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], subcommand: str, ok: bool
) -> None:
    from babylon60 import onboarding

    calls: list[dict[str, bool]] = []
    result: dict[str, object] = {
        "ok": ok,
        "status": "ready" if ok else "conflict",
        "message": "Resultado de la comprobación",
        "next_step": "Abre una conversación nueva.",
    }

    def setup(*, dry_run: bool, remove: bool) -> dict[str, object]:
        calls.append({"dry_run": dry_run, "remove": remove})
        return result

    monkeypatch.setattr(onboarding, "setup_codex", setup)
    monkeypatch.setattr(onboarding, "doctor_codex", lambda: result)
    argv = ["babylon60", subcommand, "--client", "codex", "--json"]
    if subcommand == "setup":
        argv.extend(["--dry-run", "--remove"])
    monkeypatch.setattr(sys, "argv", argv)
    with pytest.raises(SystemExit) as stopped:
        main_dispatcher.main()
    assert stopped.value.code == (0 if ok else 1)
    output = capsys.readouterr()
    assert output.err == ""
    assert json.loads(output.out) == result
    assert calls == ([{"dry_run": True, "remove": True}] if subcommand == "setup" else [])


@pytest.mark.parametrize("subcommand", ["setup", "doctor"])
def test_first_use_cli_requires_explicit_client(monkeypatch: pytest.MonkeyPatch, subcommand: str) -> None:
    monkeypatch.setattr(sys, "argv", ["babylon60", subcommand])
    with pytest.raises(SystemExit) as stopped:
        main_dispatcher.main()
    assert stopped.value.code == 2
