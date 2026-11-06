"""Exercise the independent package and generators without a core checkout."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from babylon60_oncology.oncology_primitives import PRIMITIVES

EXPERIMENT_ROOT = Path(__file__).absolute().parents[1]


def relocated_generators(tmp_path: Path) -> Path:
    relocated = tmp_path / "standalone oncology"
    for directory in ("scripts", "data"):
        shutil.copytree(EXPERIMENT_ROOT / directory, relocated / directory)
    return relocated


def test_catalog_preserves_300_unique_records() -> None:
    assert len(PRIMITIVES) == 300
    assert len({record["id"] for record in PRIMITIVES}) == 300


def test_markdown_exporter_runs_outside_core_checkout(tmp_path: Path) -> None:
    relocated = relocated_generators(tmp_path)
    proc = subprocess.run(
        [sys.executable, str(relocated / "scripts/export_ontology.py")],
        cwd=tmp_path, capture_output=True, text=True, timeout=30,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    output = relocated / "generated"
    assert {path.name for path in output.iterdir()} == {"oncology_300.json", "OncologyOntology.lean"}
    catalog = json.loads((output / "oncology_300.json").read_text())
    assert catalog["total_primitives"] == len(catalog["primitives"]) == 300
    assert "within_limit : P.length ≤ 300" in (output / "OncologyOntology.lean").read_text()
    assert not (relocated / "01_KISH_ENGINE").exists()


def test_record_generator_writes_only_selected_output_directory(tmp_path: Path) -> None:
    relocated = relocated_generators(tmp_path)
    output = tmp_path / "chosen outputs"
    proc = subprocess.run(
        [sys.executable, str(relocated / "scripts/generate_primitives.py"), "--output-dir", str(output)],
        cwd=tmp_path, capture_output=True, text=True, timeout=30,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert {path.name for path in output.iterdir()} == {
        "oncology_primitives.py", "oncology_300_primitives.yaml", "ONCOLOGIA_300_PRIMITIVAS.md",
    }
    assert not (relocated / "babylon60").exists()
    assert not (relocated / "generated").exists()


def test_simulation_cli_help_works_from_external_directory(tmp_path: Path) -> None:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(EXPERIMENT_ROOT / "src")
    proc = subprocess.run(
        [sys.executable, "-m", "babylon60_oncology.onco_transducer", "--help"],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "--data" in proc.stdout
    assert "--threshold" in proc.stdout
    assert "Traceback" not in proc.stderr
