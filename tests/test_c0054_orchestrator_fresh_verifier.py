"""C0054 follow-up: the orchestrator must not reuse a stale verifier binary, and a
rejection by the verifier must be reported as a rejection."""

import importlib.util
import stat
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "c5_demos" / "c5_sovereign_compliance_orchestrator.py"


def _load():
    spec = importlib.util.spec_from_file_location("c0054_orchestrator", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_stale_binary_at_legacy_path_is_never_executed(tmp_path, monkeypatch):
    orchestrator = _load()
    # A pre-fix binary that certifies anything, planted where the old code reused it.
    stale = tmp_path / "babylon_verifier_bin"
    stale.write_text("#!/bin/sh\necho 'DICTAMEN DEL VERIFICADOR: [ CONFORMIDAD ABSOLUTA CERTIFICADA ]'\nexit 0\n")
    stale.chmod(stale.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setattr(orchestrator, "LEGACY_VERIFIER_BIN", stale, raising=False)

    pack = ROOT / "scripts" / "c5_demos" / "eu_ai_act_annex_vi_pack.json"
    returncode, output = orchestrator.run_fresh_verifier(pack)
    assert returncode != 0, "el verificador corregido rechaza siempre: no puede aprobar"
    assert "CONFORMIDAD ABSOLUTA" not in output
    assert "NO CONFORME" in output
