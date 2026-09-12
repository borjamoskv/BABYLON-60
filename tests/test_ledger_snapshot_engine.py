# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import json
from pathlib import Path
import sqlite3
from unittest.mock import patch
from scripts.c5_l1_ledger.ledger_snapshot_engine import compute_sha256, create_snapshot, main, AUTHOR


def test_author_identity() -> None:
    assert "Telmo Dinámico de Moskv" in AUTHOR
    assert "borjamoskv" in AUTHOR


def test_compute_sha256(tmp_path: Path) -> None:
    f = tmp_path / "sample.txt"
    f.write_text("Causal-Determinist-ledger-data")
    digest = compute_sha256(f)
    assert isinstance(digest, str)
    assert len(digest) == 64


def test_create_snapshot(tmp_path: Path) -> None:
    db_file = tmp_path / "cortex.db"
    conn = sqlite3.connect(db_file)
    conn.execute("CREATE TABLE test (id INT)")
    conn.commit()
    conn.close()

    snap_dir = tmp_path / "audit" / "snapshots"
    with (
        patch("scripts.c5_l1_ledger.ledger_snapshot_engine.DB_PATH", db_file),
        patch("scripts.c5_l1_ledger.ledger_snapshot_engine.SNAPSHOT_DIR", snap_dir),
    ):
        manifest_path = create_snapshot()
        assert manifest_path.exists()
        with open(manifest_path) as mf:
            data = json.load(mf)
            assert data["author"] == AUTHOR
            assert "sha256" in data
            assert (snap_dir / data["snapshot_file"]).exists()


def test_main_success(tmp_path: Path) -> None:
    snap_dir = tmp_path / "audit" / "snapshots"
    db_file = tmp_path / "cortex.db"
    sqlite3.connect(db_file).close()

    async def mock_record(manifest_path: Path) -> None:
        pass

    with (
        patch("scripts.c5_l1_ledger.ledger_snapshot_engine.DB_PATH", db_file),
        patch("scripts.c5_l1_ledger.ledger_snapshot_engine.SNAPSHOT_DIR", snap_dir),
        patch("scripts.c5_l1_ledger.ledger_snapshot_engine.record_snapshot_event", side_effect=mock_record),
    ):
        assert main() == 0
