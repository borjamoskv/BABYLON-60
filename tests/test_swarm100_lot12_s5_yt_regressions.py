"""C0103 regressions for the private youtube-analysis-pipeline skill script.

Split from test_swarm100_lot12_s5_regressions.py: these tests exercise
tools/skill_library/, which the public projection omits, so the projection
omits this module as well.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_yt():
    spec = importlib.util.spec_from_file_location(
        "lot12_yt", ROOT / "tools/skill_library/global/youtube-analysis-pipeline/scripts/yt_audit.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_c0103_url_and_directory_are_literal_arguments(tmp_path, monkeypatch):
    yt = load_yt()
    calls = []

    def record(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return SimpleNamespace(stdout="{}", stderr="", returncode=0)

    monkeypatch.setattr(yt.subprocess, "run", record)
    url = 'https://example.invalid/$(echo fixture);"data'
    target = tmp_path / 'literal $(echo fixture) " folder'
    yt.fetch_youtube_audit(url, str(target))
    assert len(calls) == 3
    assert all(isinstance(argv, list) and not opts.get("shell", False) for argv, opts in calls)
    assert all(argv[-2:] == ["--", url] for argv, _ in calls)


def test_c0103_real_process_does_not_interpret_shell(tmp_path):
    yt = load_yt()
    marker = tmp_path / "must-not-exist"
    argument = f'$(touch {marker}); "quoted"'
    result = yt.run_cmd([sys.executable, "-I", "-c", "import sys; print(sys.argv[1])", argument])
    assert result == argument
    assert not marker.exists()


def test_c0103_rejects_string_commands():
    with pytest.raises(TypeError):
        load_yt().run_cmd("echo must-not-run")
