"""C0381 follow-up: the EU AI Act exporter must see quarantine exports in their new
exclusive directories (artifact_bundle_v3/quarantine/<hash>-NNNN/manifest.json)."""

import json

from babylon60.compliance_exporter.eu_ai_act import EUAIActComplianceExporter


def _write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_quarantine_export_dir_wins_over_standard_manifest(tmp_path):
    bundle = tmp_path / "artifact_bundle_v3"
    _write(bundle / "manifest.json", {"version": "2.0", "global_hash": "ok"})
    _write(
        bundle / "quarantine" / "abc-0000" / "manifest.json", {"status": "INTERPRETER_STOPPED", "global_hash": "abc"}
    )
    manifest = EUAIActComplianceExporter(str(bundle)).load_manifest()
    assert manifest["_is_quarantine"] is True
    assert manifest["status"] == "INTERPRETER_STOPPED"


def test_legacy_quarantine_manifest_still_recognised(tmp_path):
    bundle = tmp_path / "artifact_bundle_v3"
    _write(bundle / "quarantine" / "manifest.json", {"status": "INTERPRETER_STOPPED"})
    assert EUAIActComplianceExporter(str(bundle)).load_manifest()["_is_quarantine"] is True


def test_standard_manifest_without_quarantine_is_not_quarantine(tmp_path):
    bundle = tmp_path / "artifact_bundle_v3"
    _write(bundle / "manifest.json", {"version": "2.0"})
    (bundle / "quarantine").mkdir()
    assert EUAIActComplianceExporter(str(bundle)).load_manifest()["_is_quarantine"] is False
