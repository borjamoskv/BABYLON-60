"""Round 2 browser-forensics cases split from test_swarm100_round2_regressions.py.

They load tools/skill_library sources, which the public projection excludes.
"""

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).absolute().parents[1]


def load_script(path):
    spec = importlib.util.spec_from_file_location("round2_script", ROOT / path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(
    params=[
        "tools/skill_library/global/c5-browser-forensics-and-extension-triage/scripts/browser_forensics.py",
        "tools/skill_library/global/c5-secops-infra-devtools/references/modules/c5-browser-forensics-and-extension-triage/scripts/browser_forensics.py",
    ]
)
def browser(tmp_path, monkeypatch, request):
    module = load_script(request.param)
    profile = tmp_path / "Chrome" / "Default"
    (profile / "Extensions").mkdir(parents=True)
    monkeypatch.setattr(module, "CHROME_BASE", str(profile.parent))
    return module, profile


@pytest.mark.parametrize("kind", ["relative", "absolute", "invalid", "symlink"])
def test_v11_purge_confines_deletion(browser, tmp_path, kind):
    module, profile = browser
    victim = profile / "victim"
    victim.mkdir()
    sentinel = victim / "sentinel"
    sentinel.write_text("preserve")
    ext_id = {"relative": "../victim", "absolute": str(victim), "invalid": ".", "symlink": "a" * 32}[kind]
    if kind == "symlink":
        (profile / "Extensions").rmdir()
        (profile / "Extensions").symlink_to(victim, target_is_directory=True)
        (victim / ext_id).mkdir()
        (victim / ext_id / "child").write_text("preserve")
    with pytest.raises((ValueError, OSError)):
        module.cmd_purge(SimpleNamespace(id=ext_id))
    assert sentinel.read_text() == "preserve"
    if kind == "symlink":
        assert (victim / ext_id / "child").exists()


def test_v11_valid_extension_purge(browser):
    module, profile = browser
    ext_id = "a" * 32
    target = profile / "Extensions" / ext_id
    target.mkdir()
    (target / "manifest.json").write_text("{}")
    prefs = profile / "Secure Preferences"
    prefs.write_text(json.dumps({"extensions": {"settings": {ext_id: {}, "b" * 32: {"keep": True}}}}))
    standard = profile / "Preferences"
    standard.write_text(json.dumps({"extensions": {"install_signature": {"ids": [ext_id, "b" * 32]}}}))
    module.cmd_purge(SimpleNamespace(id=ext_id))
    assert not target.exists()
    assert json.loads(prefs.read_text())["extensions"]["settings"] == {"b" * 32: {"keep": True}}
    assert json.loads(standard.read_text())["extensions"]["install_signature"]["ids"] == ["b" * 32]
    assert len(list(profile.glob("*.c5_bak-*"))) == 2


@pytest.mark.parametrize("target_name", ["extension", "preferences", "profile"])
def test_v11_rejects_symlink_targets(browser, tmp_path, target_name):
    module, profile = browser
    ext_id = "a" * 32
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "sentinel"
    sentinel.write_text("preserve")
    if target_name == "extension":
        (profile / "Extensions" / ext_id).symlink_to(outside, target_is_directory=True)
    elif target_name == "preferences":
        (profile / "Preferences").symlink_to(sentinel)
    else:
        (profile / "Extensions").rmdir()
        profile.rmdir()
        profile.symlink_to(outside, target_is_directory=True)
    with pytest.raises((ValueError, OSError)):
        module.cmd_purge(SimpleNamespace(id=ext_id))
    assert sentinel.read_text() == "preserve"
