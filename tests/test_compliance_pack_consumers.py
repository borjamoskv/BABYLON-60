"""Exercise report consumers without starting servers or issuing signed licenses."""

import ast
import datetime
import io
import json
import os
import time
import urllib.parse
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest


REPO_ROOT = Path(__file__).absolute().parent.parent


def _load_functions(relative_path: str, names: tuple[str, ...], namespace: dict[str, Any]) -> dict[str, Any]:
    """Compile real consumer bodies without module-level startup side effects."""
    source = REPO_ROOT / relative_path
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    selected = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name in names}
    assert set(selected) == set(names)
    module = ast.Module(
        body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)]
        + [selected[name] for name in names],
        type_ignores=[],
    )
    exec(compile(ast.fix_missing_locations(module), str(source), "exec"), namespace)
    return namespace


def _write_candidate_and_stale_pack(root: Path) -> tuple[Path, dict[str, Any]]:
    path = root / "reports" / "eu_ai_act_compliance_pack.json"
    path.parent.mkdir()
    report = {"report_type": "SOURCE_CLAIMS_EXPORT", "result": "NOT_EVALUATED"}
    path.write_text(json.dumps(report), encoding="utf-8")
    stale = root / "compliance_reports" / path.name
    stale.parent.mkdir()
    stale.write_text('{"stale": true}', encoding="utf-8")
    return path, report


def test_launcher_reads_reports_pack_instead_of_stale_legacy_copy(tmp_path: Path) -> None:
    _, expected = _write_candidate_and_stale_pack(tmp_path)
    namespace = _load_functions(
        "scripts/babylon_launcher.py", ("do_GET",), {"REPO_ROOT": tmp_path, "json": json, "urllib": urllib}
    )
    responses: list[int] = []
    headers: dict[str, str] = {}
    output = io.BytesIO()
    handler = SimpleNamespace(
        path="/api/compliance/pack",
        send_response=responses.append,
        send_header=lambda name, value: headers.__setitem__(name, value),
        end_headers=lambda: None,
        wfile=output,
    )
    namespace["do_GET"](handler)
    assert responses == [200]
    assert headers["Content-Type"] == "application/json; charset=utf-8"
    assert json.loads(output.getvalue()) == expected


def test_onboarding_links_reports_pack_without_issuing_a_license(tmp_path: Path) -> None:
    pack_path, expected = _write_candidate_and_stale_pack(tmp_path)
    namespace = _load_functions(
        "scripts/zero_touch_onboarding_daemon.py",
        ("_sanitize_field", "process_zero_touch_pilot_order"),
        {
            "REPO_ROOT": tmp_path,
            "time": time,
            "datetime": datetime,
            "json": json,
            "os": os,
            "generate_license_certificate": lambda *_: (
                {"license_id": "UNSIGNED_FIXTURE", "cryptographic_seal": {"digest": "unsigned-fixture"}},
                "unsigned-fixture",
            ),
            "generate_proforma_invoice": lambda *_: ("UNSIGNED_FIXTURE", "Unsigned invoice fixture"),
            "DEFAULT_SETTLEMENT_IBAN": "",
            "DEFAULT_SETTLEMENT_BIC": "",
        },
    )
    receipt = namespace["process_zero_touch_pilot_order"]({}, out_dir=tmp_path / "unsigned-fixtures")
    sample_path = Path(receipt["delivery_bundle"]["compliance_pack_sample"])
    assert sample_path == pack_path
    assert json.loads(sample_path.read_text(encoding="utf-8")) == expected


@pytest.mark.parametrize("case", ["historical_derivative", "version_only", "absent", "corrupt"])
def test_a216_cannot_verify_seal_from_presence_or_historical_metadata(tmp_path: Path, case: str) -> None:
    manifest = tmp_path / "deploy" / "manifests" / "manifest_v4.2.0_sealed.json"
    manifest.parent.mkdir(parents=True)
    if case == "historical_derivative":
        manifest.write_bytes((REPO_ROOT / "deploy/manifests/manifest_v4.2.0_sealed.json").read_bytes())
    elif case == "version_only":
        manifest.write_text('{"version": "4.2.0"}', encoding="utf-8")
    elif case == "corrupt":
        manifest.write_text('{"version":', encoding="utf-8")
    namespace = _load_functions(
        "scripts/c5_edin/f13_233_specialist_audit_matrix.py",
        ("evaluate_specialist",),
        {"ROOT_DIR": str(tmp_path), "os": os, "json": json, "time": time, "SpecialistResult": SimpleNamespace},
    )
    result = namespace["evaluate_specialist"](
        {"id": "A216", "cluster": "isolated-test", "name": "Manifest Sealed JSON", "category": "test"}
    )
    assert result.passed is False
    assert "sellado y verificado" not in result.details
    if case != "corrupt":
        assert result.details.startswith("NO_VERIFICADO:")
    if case == "historical_derivative":
        assert "sin nuevo sello" in result.details
