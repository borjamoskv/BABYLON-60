"""Lot 1: real source modules, synthetic credentials and temporary evidence."""

import importlib.util
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from babylon60.transducers.c5_mail_transducer import C5MailTransducer

ROOT = Path(__file__).absolute().parents[1]
TOKEN = "SYNTHETIC_LOT1_CREDENTIAL"


def load_source(path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("kind", ["empty_stderr", "token_stderr", "generic", "bad_response", "http_failure"])
def test_mail_never_returns_credential_or_command(monkeypatch, kind):
    def run(cmd, **kwargs):
        if kind in {"empty_stderr", "token_stderr"}:
            raise subprocess.CalledProcessError(7, cmd, stderr="" if kind == "empty_stderr" else TOKEN)
        if kind == "generic":
            raise RuntimeError(f"Authorization: Bearer {TOKEN}; argv={cmd!r}")
        if kind == "bad_response":
            return SimpleNamespace(stdout=TOKEN)
        return SimpleNamespace(stdout=json.dumps({"message": f"Authorization: Bearer {TOKEN}"}) + "\n403")

    monkeypatch.setattr(subprocess, "run", run)
    result = C5MailTransducer(TOKEN).dispatch(["fixture@example.invalid"], "fixture", "fixture")
    rendered = json.dumps(result)
    assert TOKEN not in rendered
    assert "Authorization" not in rendered
    assert "curl" not in rendered
    assert result["status"] in {"ERROR", "FAILED"}
    assert result["code"]


def test_mail_no_key_and_success_preserve_expected_results(monkeypatch):
    monkeypatch.setattr(C5MailTransducer, "_get_keychain_secret", staticmethod(lambda: ""))
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: pytest.fail("No key must not dispatch"))
    assert C5MailTransducer().dispatch([], "", "")["code"] == "NO_API_KEY"
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: SimpleNamespace(stdout='{"id":"fixture-id"}\n200'))
    assert C5MailTransducer(TOKEN).dispatch([], "", "") == {
        "status": "DELIVERED",
        "id": "fixture-id",
        "http_code": 200,
    }
